"""
Paragraph Layer API Routes (Layer 3)
段落层API路由（第3层）

Endpoints:
- POST /step3-0/identify - Step 3.0: Paragraph Identification & Segmentation
- POST /role - Step 3.1: Paragraph Role Detection
- POST /coherence - Step 3.2: Paragraph Internal Coherence
- POST /anchor - Step 3.3: Anchor Density Analysis
- POST /sentence-length - Step 3.4: Sentence Length Distribution
- POST /step3-5/transition - Step 3.5: Paragraph Transition Analysis
- POST /analyze - Combined paragraph analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import time

from src.api.routes.analysis.schemas import (
    ParagraphAnalysisRequest,
    ParagraphAnalysisResponse,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
    IssueSeverity,
)
from src.core.analyzer.layers import ParagraphOrchestrator, LayerContext
from src.core.preprocessor.segmenter import SentenceSegmenter, ContentType

# Import LLM handlers for Layer 3 substeps
# 导入 Layer 3 子步骤的 LLM handler
from src.api.routes.substeps.layer3.step3_0_handler import Step3_0Handler
from src.api.routes.substeps.layer3.step3_1_handler import Step3_1Handler
from src.api.routes.substeps.layer3.step3_2_handler import Step3_2Handler
from src.api.routes.substeps.layer3.step3_3_handler import Step3_3Handler
from src.api.routes.substeps.layer3.step3_4_handler import Step3_4Handler
from src.api.routes.substeps.layer3.step3_5_handler import Step3_5Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handlers for Layer 3 substeps
# 初始化 Layer 3 子步骤的 LLM handler
step3_0_handler = Step3_0Handler()
step3_1_handler = Step3_1Handler()
step3_2_handler = Step3_2Handler()
step3_3_handler = Step3_3Handler()
step3_4_handler = Step3_4Handler()
step3_5_handler = Step3_5Handler()

# Reusable segmenter instance
# 可重用的分句器实例
_segmenter = SentenceSegmenter()


# =============================================================================
# Step 3.0: Paragraph Identification & Segmentation
# 步骤 3.0：段落识别与分割
# =============================================================================

class ParagraphIdentificationRequest(BaseModel):
    """Request for paragraph identification"""
    text: str = Field(..., min_length=1, description="Full document text")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    section_context: Optional[Dict[str, Any]] = Field(default=None, description="Context from Layer 4")


class ParagraphMeta(BaseModel):
    """Metadata for a single paragraph"""
    index: int
    word_count: int
    sentence_count: int
    char_count: int
    preview: str
    section_index: Optional[int] = None
    content_type: str = "body"  # body, transition, etc.


class ParagraphIdentificationResponse(BaseModel):
    """Response for paragraph identification"""
    paragraphs: List[str]
    paragraph_count: int
    paragraph_section_map: List[int]
    paragraph_metadata: List[ParagraphMeta]
    filtered_count: int
    total_word_count: int
    risk_level: str = "low"
    recommendations: List[str] = []
    recommendations_zh: List[str] = []
    processing_time_ms: int


@router.post("/step3-0/identify", response_model=ParagraphIdentificationResponse)
async def identify_paragraphs(request: ParagraphIdentificationRequest):
    """
    Step 3.0: Paragraph Identification & Segmentation (LLM-based)
    步骤 3.0：段落识别与分割（基于LLM）

    This is the foundational step for Layer 3 (Paragraph Level Analysis).
    Uses LLM to identify paragraph boundaries and filter non-body content.
    使用LLM识别段落边界并过滤非正文内容。
    """
    start_time = time.time()

    try:
        document_text = request.text
        if not document_text:
            return ParagraphIdentificationResponse(
                paragraphs=[],
                paragraph_count=0,
                paragraph_section_map=[],
                paragraph_metadata=[],
                filtered_count=0,
                total_word_count=0,
                risk_level="low",
                recommendations=[],
                recommendations_zh=[],
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        # Call LLM handler for analysis
        # 调用LLM handler进行分析
        logger.info("Calling Step3_0Handler for LLM-based paragraph identification")
        result = await step3_0_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer3-step3-0",
            use_cache=True
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        paragraphs = []
        paragraph_metadata = []

        for para_data in result.get("paragraphs", []):
            if para_data.get("is_body", True):
                preview = para_data.get("preview", "")
                paragraphs.append(preview)
                paragraph_metadata.append(ParagraphMeta(
                    index=para_data.get("index", len(paragraph_metadata)),
                    word_count=para_data.get("word_count", 0),
                    sentence_count=para_data.get("sentence_count", 0),
                    char_count=len(preview),
                    preview=preview[:100] + "..." if len(preview) > 100 else preview,
                    section_index=0,
                    content_type="body"
                ))

        paragraph_section_map = [m.section_index or 0 for m in paragraph_metadata]
        total_word_count = sum(m.word_count for m in paragraph_metadata)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ParagraphIdentificationResponse(
            paragraphs=paragraphs,
            paragraph_count=result.get("paragraph_count", len(paragraphs)),
            paragraph_section_map=paragraph_section_map,
            paragraph_metadata=paragraph_metadata,
            filtered_count=result.get("filtered_count", 0),
            total_word_count=total_word_count,
            risk_level=result.get("risk_level", "low"),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        logger.error(f"Paragraph identification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _split_text_to_paragraphs(text: str) -> list:
    """
    Split text into paragraphs, filtering out non-paragraph content
    将文本分割为段落，过滤掉非段落内容（标题、表头、keywords等）

    Uses SentenceSegmenter to detect and filter:
    - Section headers (Abstract, Introduction, etc.)
    - Table/Figure captions
    - Keywords lines
    - Metadata (author info, affiliations)
    - Short fragments
    """
    # First split into raw paragraphs
    # 首先分割为原始段落
    raw_paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(raw_paragraphs) <= 1:
        raw_paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    # Filter paragraphs using segmenter
    # 使用分句器过滤段落
    filtered_paragraphs = []
    for para in raw_paragraphs:
        # Segment the paragraph to detect content types
        # 分割段落以检测内容类型
        sentences = _segmenter.segment(para)

        # Check if this paragraph should be processed
        # 检查这个段落是否应该被处理
        if not sentences:
            continue

        # If the first sentence is not processable (header, keywords, etc.), skip the paragraph
        # 如果第一个句子不可处理（标题、关键词等），跳过该段落
        first_sent = sentences[0]
        if not first_sent.should_process:
            continue

        # Count processable sentences
        # 统计可处理的句子数量
        processable = [s for s in sentences if s.should_process]
        if not processable:
            continue

        # Reconstruct paragraph from processable sentences only
        # 仅从可处理的句子重建段落
        if len(processable) == len(sentences):
            # All sentences are processable, use original
            # 所有句子都可处理，使用原文
            filtered_paragraphs.append(para)
        else:
            # Some sentences filtered, rebuild
            # 部分句子被过滤，重建
            filtered_text = ' '.join(s.text for s in processable)
            if filtered_text.strip():
                filtered_paragraphs.append(filtered_text)

    return filtered_paragraphs


def _get_paragraphs(request: ParagraphAnalysisRequest) -> list:
    """Extract paragraphs from request (either from text or paragraphs field)"""
    if request.paragraphs:
        return request.paragraphs
    elif request.text:
        return _split_text_to_paragraphs(request.text)
    else:
        return []


def _convert_issue(issue) -> DetectionIssue:
    """Convert internal issue to API schema"""
    return DetectionIssue(
        type=issue.type,
        description=issue.description,
        description_zh=issue.description_zh,
        severity=IssueSeverity(issue.severity.value),
        layer=LayerLevel.PARAGRAPH,
        position=issue.position,
        suggestion=issue.suggestion,
        suggestion_zh=issue.suggestion_zh,
        details=issue.details,
    )


@router.post("/role", response_model=ParagraphAnalysisResponse)
async def analyze_paragraph_roles(request: ParagraphAnalysisRequest):
    """
    Step 3.1: Paragraph Role Detection (LLM-based)
    步骤 3.1：段落角色识别（基于LLM）

    Classifies each paragraph's function using LLM.
    使用LLM分类每个段落的功能。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return ParagraphAnalysisResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=[],
                recommendations_zh=[],
                details={},
                processing_time_ms=int((time.time() - start_time) * 1000),
                paragraph_roles=[],
                coherence_scores=[],
                anchor_densities=[],
                sentence_length_cvs=[],
                low_burstiness_paragraphs=[],
            )

        # Call LLM handler for analysis
        # 调用LLM handler进行分析
        logger.info("Calling Step3_1Handler for LLM-based paragraph role detection")
        result = await step3_1_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer3-step3-1",
            use_cache=True
        )

        # Convert issues
        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "role_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.PARAGRAPH,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract paragraph roles
        paragraph_roles = [pr.get("role", "body") for pr in result.get("paragraph_roles", [])]

        return ParagraphAnalysisResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            details={"role_distribution": result.get("role_distribution", {}), "uniformity_score": result.get("uniformity_score", 0)},
            processing_time_ms=processing_time_ms,
            paragraph_roles=paragraph_roles,
            coherence_scores=[],
            anchor_densities=[],
            sentence_length_cvs=[],
            low_burstiness_paragraphs=[],
        )

    except Exception as e:
        logger.error(f"Paragraph role analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coherence", response_model=ParagraphAnalysisResponse)
async def analyze_paragraph_coherence(request: ParagraphAnalysisRequest):
    """
    Step 3.2: Paragraph Internal Coherence (LLM-based)
    步骤 3.2：段落内部连贯性（基于LLM）

    Analyzes sentence relationships within paragraphs using LLM.
    使用LLM分析段落内部句子关系。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return ParagraphAnalysisResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=[],
                recommendations_zh=[],
                details={},
                processing_time_ms=int((time.time() - start_time) * 1000),
                paragraph_roles=[],
                coherence_scores=[],
                anchor_densities=[],
                sentence_length_cvs=[],
                low_burstiness_paragraphs=[],
            )

        # Call LLM handler for analysis
        # 调用LLM handler进行分析
        logger.info("Calling Step3_2Handler for LLM-based paragraph coherence analysis")
        result = await step3_2_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer3-step3-2",
            use_cache=True
        )

        # Convert issues
        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "coherence_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.PARAGRAPH,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract coherence scores
        coherence_scores = [pc.get("coherence_score", 0) for pc in result.get("paragraph_coherence", [])]

        return ParagraphAnalysisResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            details=result.get("details", {}),
            processing_time_ms=processing_time_ms,
            paragraph_roles=[],
            coherence_scores=coherence_scores,
            anchor_densities=[],
            sentence_length_cvs=[],
            low_burstiness_paragraphs=[],
        )

    except Exception as e:
        logger.error(f"Paragraph coherence analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anchor", response_model=ParagraphAnalysisResponse)
async def analyze_anchor_density(request: ParagraphAnalysisRequest):
    """
    Step 3.3: Anchor Density Analysis (LLM-based)
    步骤 3.3：锚点密度分析（基于LLM）

    Analyzes evidence density in paragraphs using LLM.
    使用LLM分析段落中的证据密度。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return ParagraphAnalysisResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=[],
                recommendations_zh=[],
                details={},
                processing_time_ms=int((time.time() - start_time) * 1000),
                paragraph_roles=[],
                coherence_scores=[],
                anchor_densities=[],
                sentence_length_cvs=[],
                low_burstiness_paragraphs=[],
            )

        # Call LLM handler for analysis
        # 调用LLM handler进行分析
        logger.info("Calling Step3_3Handler for LLM-based anchor density analysis")
        result = await step3_3_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer3-step3-3",
            use_cache=False  # Temporarily disable cache for debugging
        )

        # Debug log: Print LLM result keys and structure
        # 调试日志：打印LLM返回结果的键和结构
        logger.info(f"LLM result keys: {list(result.keys())}")
        logger.info(f"LLM result risk_score: {result.get('risk_score')}")
        logger.info(f"LLM result overall_density: {result.get('overall_density')}")
        logger.info(f"LLM result paragraph_densities count: {len(result.get('paragraph_densities', []))}")
        logger.info(f"LLM result high_risk_paragraphs: {result.get('high_risk_paragraphs')}")
        logger.info(f"LLM result recommendations: {result.get('recommendations')}")

        # Convert issues
        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "anchor_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.PARAGRAPH,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract paragraph densities from LLM result
        # LLM returns "paragraph_densities" field with anchor info
        # LLM 返回 "paragraph_densities" 字段包含锚点信息
        paragraph_densities = result.get("paragraph_densities", [])
        anchor_densities = [pa.get("density", 0) for pa in paragraph_densities]

        # Build paragraph details for frontend
        # 构建前端需要的段落详情
        paragraph_details = []
        for pd in paragraph_densities:
            paragraph_details.append({
                "index": pd.get("paragraph_index", 0),
                "role": "body",  # Default role, can be enhanced later
                "coherenceScore": 0,  # Not analyzed in this step
                "anchorCount": pd.get("anchor_count", 0),
                "sentenceLengthCv": 0,  # Not analyzed in this step
                "issues": [],
                "wordCount": pd.get("word_count", 0),
                "density": pd.get("density", 0),
                "hasHallucinationRisk": pd.get("has_hallucination_risk", False),
                "riskLevel": pd.get("risk_level", "low"),
                "anchorTypes": pd.get("anchor_types", {})
            })

        # Calculate overall anchor density
        # 计算整体锚点密度
        overall_density = result.get("overall_density", 0.0)
        high_risk_paragraphs = result.get("high_risk_paragraphs", [])

        return ParagraphAnalysisResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            details={
                "overall_density": overall_density,
                "high_risk_paragraphs": high_risk_paragraphs,
                "anchor_type_distribution": result.get("anchor_type_distribution", {}),
                "document_hallucination_risk": result.get("document_hallucination_risk", "low"),
                "paragraph_details": paragraph_details
            },
            processing_time_ms=processing_time_ms,
            paragraph_roles=[],
            coherence_scores=[],
            anchor_densities=anchor_densities,
            anchor_density=overall_density,
            paragraph_count=len(paragraph_densities),
            paragraph_details=paragraph_details,
            sentence_length_cvs=[],
            low_burstiness_paragraphs=[],
        )

    except Exception as e:
        logger.error(f"Anchor density analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sentence-length", response_model=ParagraphAnalysisResponse)
async def analyze_sentence_length_distribution(request: ParagraphAnalysisRequest):
    """
    Step 3.4: Sentence Length Distribution (LLM-based)
    步骤 3.4：段内句子长度分布（基于LLM）

    Analyzes sentence length variation within each paragraph using LLM.
    使用LLM分析每个段落内句子长度变化。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return ParagraphAnalysisResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=[],
                recommendations_zh=[],
                details={},
                processing_time_ms=int((time.time() - start_time) * 1000),
                paragraph_roles=[],
                coherence_scores=[],
                anchor_densities=[],
                sentence_length_cvs=[],
                low_burstiness_paragraphs=[],
            )

        # Call LLM handler for analysis
        # 调用LLM handler进行分析
        logger.info("Calling Step3_4Handler for LLM-based sentence length distribution analysis")
        result = await step3_4_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer3-step3-4",
            use_cache=True
        )

        # Convert issues
        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "length_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.PARAGRAPH,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract sentence length CVs and low burstiness paragraphs
        # low_burstiness_paragraphs is a list of paragraph indices (integers), not dicts
        # 低突发性段落是段落索引的整数列表，而不是字典
        low_burst_paras = result.get("low_burstiness_paragraphs", [])
        paragraph_lengths = result.get("paragraph_lengths", [])
        overall_cv = result.get("overall_cv", 0)

        # Build paragraph_details with sentence length CV for frontend
        # 构建包含句长CV的段落详情供前端使用
        paragraph_details = []
        for pl in paragraph_lengths:
            paragraph_details.append({
                "index": pl.get("paragraph_index", 0),
                "sentenceCount": pl.get("sentence_count", 0),
                "meanLength": pl.get("mean_length", 0),
                "sentenceLengthCv": pl.get("cv", 0),
                "burstiness": pl.get("burstiness", 0),
                "hasShortSentence": pl.get("has_short_sentence", False),
                "hasLongSentence": pl.get("has_long_sentence", False),
                "rhythmScore": pl.get("rhythm_score", 0),
            })

        # Build a map of paragraph_index -> cv for quick lookup
        # 构建段落索引到CV值的映射
        cv_map = {pl.get("paragraph_index", i): pl.get("cv", 0) for i, pl in enumerate(paragraph_lengths)}

        # Get CVs for low burstiness paragraphs
        # 获取低突发性段落的CV值
        sentence_length_cvs = [cv_map.get(idx, 0) for idx in low_burst_paras] if low_burst_paras else []

        # Build details with sentence_length_analysis for frontend
        # 构建包含句长分析的详情供前端使用
        details = result.get("details", {})
        details["sentenceLengthAnalysis"] = {
            "meanCv": overall_cv,
            "paragraphCount": len(paragraph_lengths),
            "lowCvCount": len(low_burst_paras),
        }

        logger.info(f"Sentence length analysis result: overall_cv={overall_cv}, paragraphs={len(paragraph_lengths)}, low_cv_paras={len(low_burst_paras)}")

        return ParagraphAnalysisResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            details=details,
            processing_time_ms=processing_time_ms,
            paragraph_roles=[],
            coherence_scores=[],
            anchor_densities=[],
            sentence_length_cvs=sentence_length_cvs,
            low_burstiness_paragraphs=low_burst_paras,  # Already a list of integers
            paragraph_count=len(paragraph_lengths),
            paragraph_details=paragraph_details,
        )

    except Exception as e:
        logger.error(f"Sentence length analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=ParagraphAnalysisResponse)
async def analyze_paragraph(request: ParagraphAnalysisRequest):
    """
    Combined Paragraph Analysis (Layer 3)
    综合段落分析（第3层）

    Runs all paragraph-level analysis steps:
    - Step 3.1: Paragraph Role Detection
    - Step 3.2: Paragraph Internal Coherence
    - Step 3.3: Anchor Density Analysis
    - Step 3.4: Sentence Length Distribution

    Returns complete paragraph-level analysis results with context
    for passing to lower layers (sentence layer).
    """
    start_time = time.time()

    try:
        orchestrator = ParagraphOrchestrator()

        # Get filtered paragraphs (headers, keywords, etc. removed)
        # 获取过滤后的段落（已移除标题、关键词等）
        filtered_paragraphs = _get_paragraphs(request)

        # Create context with paragraphs and optional section context
        context = LayerContext(
            paragraphs=filtered_paragraphs,
            paragraph_roles=request.paragraph_roles,
            sections=request.section_context.get("sections") if request.section_context else None,
        )

        # Run full analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract all details
        length_details = result.details.get("sentence_lengths", {})
        # low_burstiness_paragraphs is a list of paragraph indices (integers)
        # 低突发性段落是段落索引的整数列表
        low_burst_paras = length_details.get("low_burstiness_paragraphs", [])
        paragraph_lengths = length_details.get("paragraph_lengths", [])

        # Build a map of paragraph_index -> cv for quick lookup
        # 构建段落索引到CV值的映射
        cv_map = {pl.get("paragraph_index", i): pl.get("cv", 0) for i, pl in enumerate(paragraph_lengths)}

        # Get CVs for low burstiness paragraphs
        # 获取低突发性段落的CV值
        sentence_length_cvs = [cv_map.get(idx, 0) for idx in low_burst_paras] if low_burst_paras else []

        return ParagraphAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=result.details,
            processing_time_ms=processing_time_ms,
            paragraphs=filtered_paragraphs,  # Return filtered paragraphs 返回过滤后的段落
            paragraph_roles=result.updated_context.paragraph_roles or [],
            coherence_scores=result.updated_context.paragraph_coherence or [],
            anchor_densities=result.updated_context.paragraph_anchor_density or [],
            sentence_length_cvs=sentence_length_cvs,
            low_burstiness_paragraphs=low_burst_paras,  # Already a list of integers
        )

    except Exception as e:
        logger.error(f"Paragraph analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context")
async def get_paragraph_context(request: ParagraphAnalysisRequest):
    """
    Get paragraph context for passing to sentence layer
    获取段落上下文以传递给句子层

    Returns the updated LayerContext that can be used
    to initialize sentence-level analysis with paragraph context.

    **IMPORTANT**: This context is critical for sentence layer analysis.
    句子层分析需要这个上下文信息。
    """
    try:
        orchestrator = ParagraphOrchestrator()

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles,
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Return the updated context as dict for sentence layer
        return {
            "paragraphs": result.updated_context.paragraphs,
            "paragraph_roles": result.updated_context.paragraph_roles,
            "paragraph_coherence": result.updated_context.paragraph_coherence,
            "paragraph_anchor_density": result.updated_context.paragraph_anchor_density,
            "paragraph_sentence_lengths": result.updated_context.paragraph_sentence_lengths,
        }

    except Exception as e:
        logger.error(f"Paragraph context extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Step 3.5: Paragraph Transition Analysis
# 步骤 3.5：段落间过渡分析
# =============================================================================

class ParagraphTransitionInfo(BaseModel):
    """Transition info between two paragraphs"""
    from_paragraph: int
    to_paragraph: int
    has_explicit_connector: bool
    connector_words: List[str] = []
    semantic_echo_score: float
    echoed_keywords: List[str] = []
    transition_quality: str  # smooth/abrupt/formulaic
    opener_text: str
    opener_pattern: str = ""
    is_formulaic_opener: bool = False
    risk_score: int


class ParagraphTransitionRequest(BaseModel):
    """Request for paragraph transition analysis"""
    text: Optional[str] = Field(default=None, description="Full document text")
    paragraphs: Optional[List[str]] = Field(default=None, description="Pre-split paragraphs")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    section_context: Optional[Dict[str, Any]] = Field(default=None, description="Context from Layer 4")


class ParagraphTransitionResponse(BaseModel):
    """Response for paragraph transition analysis"""
    risk_score: int
    risk_level: str
    total_transitions: int
    explicit_connector_count: int
    explicit_ratio: float
    avg_semantic_echo: float
    formulaic_opener_count: int
    transitions: List[ParagraphTransitionInfo]
    issues: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    recommendations_zh: List[str] = []
    processing_time_ms: int


# Explicit connector patterns for paragraph transitions
# 段落过渡的显性连接词模式
EXPLICIT_CONNECTORS = {
    "additive": ["furthermore", "moreover", "additionally", "also", "in addition", "besides"],
    "causal": ["therefore", "thus", "hence", "consequently", "as a result"],
    "contrastive": ["however", "nevertheless", "nonetheless", "yet", "on the other hand"],
    "sequential": ["firstly", "secondly", "thirdly", "finally", "next", "then"],
}

# Formulaic opener patterns
# 公式化开头模式
FORMULAIC_OPENERS = [
    r"^(It is|This is) (important|essential|crucial|worth noting)",
    r"^(Furthermore|Moreover|Additionally|In addition),",
    r"^(However|Nevertheless|Nonetheless),",
    r"^(As (mentioned|discussed|noted) (above|earlier|previously))",
    r"^(In (this|the) (section|paragraph|part)),",
]

import re


@router.post("/step3-5/transition", response_model=ParagraphTransitionResponse)
async def analyze_paragraph_transitions(request: ParagraphTransitionRequest):
    """
    Step 3.5: Paragraph Transition Analysis (LLM-based)
    步骤 3.5：段落间过渡分析（基于LLM）

    Analyzes transitions between adjacent paragraphs using LLM.
    使用LLM分析相邻段落之间的过渡。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return ParagraphTransitionResponse(
                risk_score=0,
                risk_level="low",
                total_transitions=0,
                explicit_connector_count=0,
                explicit_ratio=0.0,
                avg_semantic_echo=0.0,
                formulaic_opener_count=0,
                transitions=[],
                recommendations=["Document is empty, no transitions to analyze."],
                recommendations_zh=["文档为空，无法进行过渡分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        # Call LLM handler for analysis
        # 调用LLM handler进行分析
        logger.info("Calling Step3_5Handler for LLM-based paragraph transition analysis")
        result = await step3_5_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer3-step3-5",
            use_cache=True
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        transitions: List[ParagraphTransitionInfo] = []
        for trans_data in result.get("transitions", []):
            transitions.append(ParagraphTransitionInfo(
                from_paragraph=trans_data.get("from_paragraph", 0),
                to_paragraph=trans_data.get("to_paragraph", 0),
                has_explicit_connector=trans_data.get("has_explicit_connector", False),
                connector_words=trans_data.get("connector_words", []),
                semantic_echo_score=trans_data.get("semantic_echo_score", 0.0),
                echoed_keywords=trans_data.get("echoed_keywords", []),
                transition_quality=trans_data.get("transition_quality", "smooth"),
                opener_text=trans_data.get("opener_text", ""),
                opener_pattern=trans_data.get("opener_pattern", ""),
                is_formulaic_opener=trans_data.get("is_formulaic_opener", False),
                risk_score=trans_data.get("risk_score", 0),
            ))

        # Convert issues
        issues = []
        for issue_data in result.get("issues", []):
            issues.append({
                "type": issue_data.get("type", "transition_issue"),
                "description": issue_data.get("description", ""),
                "description_zh": issue_data.get("description_zh", ""),
                "severity": issue_data.get("severity", "medium"),
            })

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ParagraphTransitionResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=result.get("risk_level", "low"),
            total_transitions=len(transitions),
            explicit_connector_count=result.get("explicit_connector_count", 0),
            explicit_ratio=result.get("explicit_ratio", 0.0),
            avg_semantic_echo=result.get("avg_semantic_echo", 0.0),
            formulaic_opener_count=result.get("formulaic_opener_count", 0),
            transitions=transitions,
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        logger.error(f"Paragraph transition analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
