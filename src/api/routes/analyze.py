"""
============================================
DEPRECATED: Legacy Text Analysis API Routes
已废弃：旧版文本分析API路由
============================================

This module uses the OLD API structure and is superseded by:
- New 5-Layer Analysis API: /api/v1/analysis/*
- Located at: src/api/routes/analysis/

Frontend should use:
- analysisApi.ts instead of api.ts for analysis

DO NOT DELETE - kept for backward compatibility
请勿删除 - 保留用于向后兼容
============================================

Text analysis API routes
文本分析API路由
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.db.database import get_db
from src.db.models import Document, Sentence
from src.api.schemas import (
    AnalyzeRequest,
    SentenceAnalysis,
    RiskLevel,
    FingerprintMatch,
    IssueDetail,
    DetectorView
)
from src.core.preprocessor.segmenter import SentenceSegmenter
from src.core.preprocessor.term_locker import TermLocker
from src.core.analyzer.fingerprint import FingerprintDetector
from src.core.analyzer.scorer import RiskScorer

router = APIRouter()


@router.post("/", response_model=List[SentenceAnalysis])
async def analyze_text(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze text for AIGC characteristics
    分析文本的AIGC特征
    """
    # Initialize components
    # 初始化组件
    segmenter = SentenceSegmenter()
    term_locker = TermLocker()
    fingerprint_detector = FingerprintDetector()
    risk_scorer = RiskScorer()

    # Segment text into sentences
    # 将文本分割为句子
    sentences = segmenter.segment(request.text)

    results = []
    for idx, sentence in enumerate(sentences):
        # Identify locked terms
        # 识别锁定术语
        locked_terms = term_locker.identify_terms(sentence.text)

        # Detect fingerprint words
        # 检测指纹词
        fingerprints = fingerprint_detector.detect(sentence.text)

        # Calculate risk score (CAASS v2.0)
        # 计算风险分数（CAASS v2.0）
        analysis = risk_scorer.analyze(
            sentence.text,
            fingerprints=fingerprints,
            include_turnitin=request.include_turnitin,
            include_gptzero=request.include_gptzero,
            tone_level=4  # Default to standard academic level
        )

        # Build response
        # 构建响应
        result = SentenceAnalysis(
            index=idx,
            text=sentence.text,
            risk_score=analysis.risk_score,
            risk_level=RiskLevel(analysis.risk_level),
            ppl=analysis.ppl,
            ppl_risk=RiskLevel(analysis.ppl_risk),
            fingerprints=[
                FingerprintMatch(
                    word=fp.word,
                    position=fp.position,
                    risk_weight=fp.risk_weight,
                    category=fp.category,
                    replacements=fp.replacements
                ) for fp in fingerprints
            ],
            fingerprint_density=analysis.fingerprint_density,
            issues=[
                IssueDetail(
                    type=issue.type,
                    description=issue.description,
                    description_zh=issue.description_zh,
                    severity=RiskLevel(issue.severity),
                    position=issue.position,
                    word=issue.word
                ) for issue in analysis.issues
            ],
            turnitin_view=DetectorView(
                detector="turnitin",
                risk_score=analysis.turnitin_score,
                key_issues=analysis.turnitin_issues,
                key_issues_zh=analysis.turnitin_issues_zh
            ) if request.include_turnitin else None,
            gptzero_view=DetectorView(
                detector="gptzero",
                risk_score=analysis.gptzero_score,
                key_issues=analysis.gptzero_issues,
                key_issues_zh=analysis.gptzero_issues_zh
            ) if request.include_gptzero else None,
            locked_terms=[t.term for t in locked_terms]
        )
        results.append(result)

    return results


@router.post("/document/{document_id}")
async def analyze_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    include_turnitin: bool = True,
    include_gptzero: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Start document analysis (background task)
    启动文档分析（后台任务）
    """
    # Get document
    # 获取文档
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update status
    # 更新状态
    doc.status = "analyzing"
    await db.commit()

    # Add background task
    # 添加后台任务
    background_tasks.add_task(
        _analyze_document_task,
        document_id,
        include_turnitin,
        include_gptzero
    )

    return {"status": "analyzing", "document_id": document_id}


@router.get("/{analysis_id}/status")
async def get_analysis_status(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get analysis status
    获取分析状态
    """
    result = await db.execute(
        select(Document).where(Document.id == analysis_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Count processed sentences
    # 统计已处理的句子
    sentences_result = await db.execute(
        select(Sentence).where(Sentence.document_id == analysis_id)
    )
    sentences = sentences_result.scalars().all()

    return {
        "status": doc.status,
        "total_sentences": len(sentences),
        "analyzed": len([s for s in sentences if s.risk_score is not None])
    }


@router.get("/{analysis_id}/result", response_model=List[SentenceAnalysis])
async def get_analysis_result(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get analysis results
    获取分析结果
    """
    result = await db.execute(
        select(Sentence)
        .where(Sentence.document_id == analysis_id)
        .order_by(Sentence.index)
    )
    sentences = result.scalars().all()

    if not sentences:
        raise HTTPException(status_code=404, detail="No analysis results found")

    return [
        SentenceAnalysis(
            index=s.index,
            text=s.original_text,
            risk_score=s.risk_score or 0,
            risk_level=RiskLevel(s.risk_level or "low"),
            ppl=s.analysis_json.get("ppl", 0) if s.analysis_json else 0,
            ppl_risk=RiskLevel(s.analysis_json.get("ppl_risk", "low") if s.analysis_json else "low"),
            fingerprints=[],
            fingerprint_density=0,
            issues=[],
            locked_terms=s.locked_terms_json or []
        ) for s in sentences
    ]


async def _analyze_document_task(
    document_id: str,
    include_turnitin: bool,
    include_gptzero: bool
):
    """
    Background task for document analysis (DEPRECATED)
    文档分析的后台任务（已弃用）

    NOTE: This endpoint is not actively used. The main analysis flow uses:
    - ThreeLevelFlow -> structureApi.analyzeStep1_1/Step1_2
    - flowApi.start -> Intervention page

    This endpoint was designed for async background analysis with Turnitin/GPTZero
    integration, but was never implemented. Consider removing if not needed.

    注意：此端点未被积极使用。主要分析流程使用：
    - ThreeLevelFlow -> structureApi.analyzeStep1_1/Step1_2
    - flowApi.start -> Intervention 页面

    此端点原设计用于异步后台分析和 Turnitin/GPTZero 集成，
    但从未实现。如不需要请考虑移除。
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(
        f"_analyze_document_task called but not implemented. "
        f"document_id={document_id}, turnitin={include_turnitin}, gptzero={include_gptzero}"
    )
    # TODO: Implement or remove this deprecated endpoint
    # TODO: 实现或移除此已弃用的端点
