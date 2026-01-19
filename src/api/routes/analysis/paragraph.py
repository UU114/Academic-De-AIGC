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
    Step 3.0: Paragraph Identification & Segmentation (LLM-based with pre-calculated statistics)
    步骤 3.0：段落识别与分割（基于LLM，使用预计算统计数据）

    This is the foundational step for Layer 3 (Paragraph Level Analysis).
    Pre-calculates paragraph statistics and passes to LLM for analysis.
    使用预计算统计数据并传递给LLM进行分析。
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

        # STEP 1: Pre-calculate paragraph statistics from text
        # 步骤1：从文本预计算段落统计数据
        raw_paragraphs = _split_text_to_paragraphs(document_text)
        paragraph_count = len(raw_paragraphs)
        total_word_count = sum(len(p.split()) for p in raw_paragraphs)

        # Calculate per-paragraph statistics
        # 计算每个段落的统计数据
        para_stats = []
        for i, para in enumerate(raw_paragraphs):
            sentences = _segmenter.segment(para)
            para_stats.append({
                "index": i,
                "word_count": len(para.split()),
                "sentence_count": len(sentences) if sentences else 1,
                "char_count": len(para),
                "preview": para[:100] + "..." if len(para) > 100 else para
            })

        # Build pre-calculated statistics JSON
        # 构建预计算统计数据JSON
        import json
        parsed_statistics = {
            "paragraph_count": paragraph_count,
            "total_word_count": total_word_count,
            "paragraph_details": para_stats[:20],  # Limit for prompt size
            "avg_paragraph_words": round(total_word_count / paragraph_count, 1) if paragraph_count > 0 else 0
        }
        parsed_statistics_str = json.dumps(parsed_statistics, indent=2, ensure_ascii=False)

        logger.info(f"Step 3.0: Pre-calculated {paragraph_count} paragraphs, {total_word_count} words")

        # STEP 2: Pass pre-calculated statistics to LLM
        # 步骤2：将预计算统计数据传递给LLM
        logger.info("Calling Step3_0Handler for LLM-based paragraph identification")
        result = await step3_0_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step3-0",
            use_cache=True,
            parsed_statistics=parsed_statistics_str
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
            step_name="step3-1",
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
            step_name="step3-2",
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
    Step 3.3: Anchor Density Analysis (LLM-based with pre-calculated statistics)
    步骤 3.3：锚点密度分析（基于LLM，使用预计算统计数据）

    Pre-calculates anchor counts and density, then passes to LLM for analysis.
    预计算锚点数量和密度，然后传递给LLM进行分析。
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

        # STEP 1: Pre-calculate anchor statistics from text
        # 步骤1：从文本预计算锚点统计数据
        import re
        import json

        paragraphs = _split_text_to_paragraphs(document_text)

        # Anchor detection patterns
        # 锚点检测模式
        anchor_patterns = {
            "numbers": r'\b\d+(?:\.\d+)?%?\b|\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b',
            "dates": r'\b(?:19|20)\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\b',
            "citations": r'\[\d+\]|\(\w+(?:\s+et\s+al\.?)?,?\s*(?:19|20)\d{2}\)|\(\d{4}\)',
            "names": r'\b(?:Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.)\s+[A-Z][a-z]+|\b[A-Z][a-z]+\s+(?:University|Institute|Lab)\b'
        }

        para_anchor_stats = []
        total_anchors = 0
        total_words = 0
        high_risk_paragraphs = []

        for i, para in enumerate(paragraphs):
            word_count = len(para.split())
            total_words += word_count

            anchor_counts = {}
            for anchor_type, pattern in anchor_patterns.items():
                matches = re.findall(pattern, para)
                anchor_counts[anchor_type] = len(matches)

            total_anchor_count = sum(anchor_counts.values())
            total_anchors += total_anchor_count
            density = round((total_anchor_count / word_count) * 100, 2) if word_count > 0 else 0

            has_risk = total_anchor_count == 0 or density < 1.0  # Less than 1 anchor per 100 words
            if has_risk:
                high_risk_paragraphs.append(i)

            para_anchor_stats.append({
                "paragraph_index": i,
                "word_count": word_count,
                "anchor_count": total_anchor_count,
                "density": density,
                "has_hallucination_risk": has_risk,
                "anchor_types": anchor_counts
            })

        overall_density = round((total_anchors / total_words) * 100, 2) if total_words > 0 else 0

        # Build pre-calculated statistics JSON
        # 构建预计算统计数据JSON
        parsed_statistics = {
            "paragraph_count": len(paragraphs),
            "total_words": total_words,
            "total_anchors": total_anchors,
            "overall_density": overall_density,
            "high_risk_count": len(high_risk_paragraphs),
            "high_risk_paragraphs": high_risk_paragraphs[:10],  # Limit for prompt
            "paragraph_anchor_stats": para_anchor_stats[:15]  # Limit for prompt
        }
        parsed_statistics_str = json.dumps(parsed_statistics, indent=2, ensure_ascii=False)

        logger.info(f"Step 3.3: Pre-calculated overall_density={overall_density}, high_risk={len(high_risk_paragraphs)}")

        # STEP 2: Pass pre-calculated statistics to LLM
        # 步骤2：将预计算统计数据传递给LLM
        logger.info("Calling Step3_3Handler for LLM-based anchor density analysis")
        result = await step3_3_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step3-3",
            use_cache=True,
            parsed_statistics=parsed_statistics_str,
            overall_density=overall_density
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

        # STEP 3: Use PRE-CALCULATED statistics (not LLM's)
        # 步骤3：使用预计算的统计数据（不是LLM的）

        # Aggregate anchor type distribution from pre-calculated data
        # 从预计算数据汇总锚点类型分布
        aggregated_anchor_types = {
            "numbers": 0,
            "dates": 0,
            "citations": 0,
            "names": 0
        }
        for ps in para_anchor_stats:
            for anchor_type, count in ps["anchor_types"].items():
                if anchor_type in aggregated_anchor_types:
                    aggregated_anchor_types[anchor_type] += count

        # Build paragraph details from pre-calculated data
        # 从预计算数据构建段落详情
        paragraph_details = []
        anchor_densities_list = []
        for i, ps in enumerate(para_anchor_stats):
            # Get first 3 words of paragraph for preview
            # 获取段落前3个单词作为预览
            para_text = paragraphs[i] if i < len(paragraphs) else ""
            words = para_text.split()[:5]  # First 5 words
            preview = " ".join(words)
            if len(words) < len(para_text.split()):
                preview += "..."

            paragraph_details.append({
                "index": ps["paragraph_index"],
                "role": "body",
                "preview": preview,  # Add paragraph preview
                "coherenceScore": 0,
                "anchorCount": ps["anchor_count"],
                "sentenceLengthCv": 0,
                "issues": [],
                "wordCount": ps["word_count"],
                "density": ps["density"],
                "hasHallucinationRisk": ps["has_hallucination_risk"],
                "riskLevel": "high" if ps["has_hallucination_risk"] else "low",
                "anchorTypes": ps["anchor_types"]
            })
            anchor_densities_list.append(ps["density"])

        return ParagraphAnalysisResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            details={
                "overall_density": overall_density,  # Use pre-calculated value
                "high_risk_paragraphs": high_risk_paragraphs,  # Use pre-calculated value
                "anchor_type_distribution": aggregated_anchor_types,  # Use PRE-CALCULATED, not LLM
                "document_hallucination_risk": result.get("document_hallucination_risk", "low"),
                "paragraph_details": paragraph_details
            },
            processing_time_ms=processing_time_ms,
            paragraph_roles=[],
            coherence_scores=[],
            anchor_densities=anchor_densities_list,  # Use pre-calculated value
            anchor_density=overall_density,  # Use pre-calculated value
            paragraph_count=len(para_anchor_stats),  # Use pre-calculated value
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
    Step 3.4: Sentence Length Distribution (LLM-based with pre-calculated statistics)
    步骤 3.4：段内句子长度分布（基于LLM，使用预计算统计数据）

    Pre-calculates sentence length CV and burstiness, then passes to LLM for analysis.
    预计算句子长度CV和突发性，然后传递给LLM进行分析。
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

        # STEP 1: Pre-calculate sentence length statistics from text
        # 步骤1：从文本预计算句子长度统计数据
        import statistics as stat_module
        import json

        paragraphs = _split_text_to_paragraphs(document_text)

        para_length_stats = []
        low_burstiness_paragraphs = []
        all_cvs = []

        for i, para in enumerate(paragraphs):
            sentences = _segmenter.segment(para)
            # Extract text from Sentence objects and calculate word counts
            # 从Sentence对象中提取文本并计算词数
            sentence_lengths = [len(s.text.split()) for s in sentences] if sentences else []

            if len(sentence_lengths) >= 2:
                mean_len = stat_module.mean(sentence_lengths)
                stdev_len = stat_module.stdev(sentence_lengths)
                cv = round(stdev_len / mean_len, 3) if mean_len > 0 else 0
            else:
                mean_len = sentence_lengths[0] if sentence_lengths else 0
                stdev_len = 0
                cv = 0

            all_cvs.append(cv)

            # Burstiness: variance in consecutive sentence length differences
            # 突发性：连续句子长度差异的方差
            burstiness = 0
            if len(sentence_lengths) >= 3:
                diffs = [abs(sentence_lengths[j+1] - sentence_lengths[j]) for j in range(len(sentence_lengths)-1)]
                burstiness = round(stat_module.stdev(diffs) / stat_module.mean(diffs), 2) if stat_module.mean(diffs) > 0 else 0

            has_short = any(l < 10 for l in sentence_lengths)
            has_long = any(l > 40 for l in sentence_lengths)

            # Low burstiness = uniform sentence lengths (AI-like)
            if cv < 0.3:
                low_burstiness_paragraphs.append(i)

            para_length_stats.append({
                "paragraph_index": i,
                "sentence_count": len(sentences) if sentences else 0,
                "sentence_lengths": sentence_lengths[:10],  # Limit for prompt
                "mean_length": round(mean_len, 1),
                "std_length": round(stdev_len, 1),
                "cv": cv,
                "burstiness": burstiness,
                "has_short_sentence": has_short,
                "has_long_sentence": has_long,
                "rhythm_score": round(burstiness * 0.5 + (0.5 if has_short and has_long else 0), 2)
            })

        overall_cv = round(stat_module.mean(all_cvs), 3) if all_cvs else 0

        # Build pre-calculated statistics JSON
        # 构建预计算统计数据JSON
        parsed_statistics = {
            "paragraph_count": len(paragraphs),
            "overall_cv": overall_cv,
            "cv_evaluation": "AI-like (too uniform)" if overall_cv < 0.3 else ("Borderline" if overall_cv < 0.4 else "Human-like (good variation)"),
            "low_burstiness_count": len(low_burstiness_paragraphs),
            "low_burstiness_paragraphs": low_burstiness_paragraphs[:10],
            "paragraph_length_stats": para_length_stats[:15]
        }
        parsed_statistics_str = json.dumps(parsed_statistics, indent=2, ensure_ascii=False)

        logger.info(f"Step 3.4: Pre-calculated overall_cv={overall_cv}, low_burstiness={len(low_burstiness_paragraphs)}")

        # STEP 2: Pass pre-calculated statistics to LLM
        # 步骤2：将预计算统计数据传递给LLM
        logger.info("Calling Step3_4Handler for LLM-based sentence length distribution analysis")
        result = await step3_4_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step3-4",
            use_cache=True,
            parsed_statistics=parsed_statistics_str,
            overall_cv=overall_cv
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

        # STEP 3: Use PRE-CALCULATED statistics (not LLM's)
        # 步骤3：使用预计算的统计数据（不是LLM的）

        # Build paragraph_details from pre-calculated data
        # 从预计算数据构建段落详情
        def _get_preview(text: str, max_words: int = 8) -> str:
            """Get first few words as preview / 获取前几个单词作为预览"""
            words = text.split()
            if len(words) <= max_words:
                return text.strip()
            return " ".join(words[:max_words]) + "..."

        paragraph_details = []
        for pl in para_length_stats:
            para_idx = pl["paragraph_index"]
            # Get preview from original paragraph text
            # 从原始段落文本获取预览
            preview = _get_preview(paragraphs[para_idx]) if para_idx < len(paragraphs) else ""
            paragraph_details.append({
                "index": para_idx,
                "sentenceCount": pl["sentence_count"],
                "meanLength": pl["mean_length"],
                "sentenceLengthCv": pl["cv"],
                "burstiness": pl["burstiness"],
                "hasShortSentence": pl["has_short_sentence"],
                "hasLongSentence": pl["has_long_sentence"],
                "rhythmScore": pl["rhythm_score"],
                "preview": preview,
            })

        # Build a map of paragraph_index -> cv for quick lookup
        # 构建段落索引到CV值的映射
        cv_map = {pl["paragraph_index"]: pl["cv"] for pl in para_length_stats}

        # Get CVs for low burstiness paragraphs
        # 获取低突发性段落的CV值
        sentence_length_cvs = [cv_map.get(idx, 0) for idx in low_burstiness_paragraphs] if low_burstiness_paragraphs else []

        # Build details with sentence_length_analysis for frontend
        # 构建包含句长分析的详情供前端使用
        details = result.get("details", {})
        details["sentenceLengthAnalysis"] = {
            "meanCv": overall_cv,  # Use pre-calculated value
            "paragraphCount": len(para_length_stats),  # Use pre-calculated value
            "lowCvCount": len(low_burstiness_paragraphs),  # Use pre-calculated value
        }

        logger.info(f"Sentence length analysis result: overall_cv={overall_cv}, paragraphs={len(para_length_stats)}, low_cv_paras={len(low_burstiness_paragraphs)}")

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
            low_burstiness_paragraphs=low_burstiness_paragraphs,  # Use pre-calculated value
            paragraph_count=len(para_length_stats),  # Use pre-calculated value
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
    Step 3.5: Paragraph Transition Analysis (LLM-based with pre-calculated statistics)
    步骤 3.5：段落间过渡分析（基于LLM，使用预计算统计数据）

    Pre-calculates explicit connector counts, then passes to LLM for semantic analysis.
    预计算显性连接词数量，然后传递给LLM进行语义分析。
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

        # STEP 1: Pre-calculate transition statistics from text
        # 步骤1：从文本预计算过渡统计数据
        import json

        paragraphs = _split_text_to_paragraphs(document_text)
        paragraph_count = len(paragraphs)
        total_transitions = max(0, paragraph_count - 1)

        # Detect explicit connectors at paragraph starts
        # 检测段落开头的显性连接词
        all_connectors = []
        for cat, words in EXPLICIT_CONNECTORS.items():
            all_connectors.extend(words)

        explicit_connector_details = []
        explicit_count = 0
        formulaic_count = 0

        for i, para in enumerate(paragraphs):
            para_lower = para.lower().strip()
            first_words = para_lower.split()[:5]  # Check first 5 words

            # Check for explicit connectors
            has_explicit = False
            found_connectors = []
            for word in first_words:
                word_clean = word.strip(',.;:')
                if word_clean in all_connectors:
                    has_explicit = True
                    found_connectors.append(word_clean)

            if has_explicit:
                explicit_count += 1
                explicit_connector_details.append({
                    "paragraph_index": i,
                    "connectors": found_connectors
                })

            # Check for formulaic openers
            is_formulaic = False
            for pattern in FORMULAIC_OPENERS:
                if re.match(pattern, para_lower, re.IGNORECASE):
                    is_formulaic = True
                    formulaic_count += 1
                    break

        explicit_ratio = round(explicit_count / total_transitions, 3) if total_transitions > 0 else 0

        # Build pre-calculated statistics JSON
        # 构建预计算统计数据JSON
        parsed_statistics = {
            "paragraph_count": paragraph_count,
            "total_transitions": total_transitions,
            "explicit_connector_count": explicit_count,
            "explicit_ratio": explicit_ratio,
            "formulaic_opener_count": formulaic_count,
            "is_high_explicit": explicit_ratio > 0.3,
            "evaluation": "AI-like (too many explicit connectors)" if explicit_ratio > 0.3 else "Human-like (natural transitions)",
            "explicit_connector_details": explicit_connector_details[:10]
        }
        parsed_statistics_str = json.dumps(parsed_statistics, indent=2, ensure_ascii=False)

        logger.info(f"Step 3.5: Pre-calculated explicit_ratio={explicit_ratio}, formulaic={formulaic_count}")

        # STEP 2: Pass pre-calculated statistics to LLM
        # 步骤2：将预计算统计数据传递给LLM
        logger.info("Calling Step3_5Handler for LLM-based paragraph transition analysis")
        result = await step3_5_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step3-5",
            use_cache=True,
            parsed_statistics=parsed_statistics_str,
            explicit_ratio=explicit_ratio
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

        # STEP 3: Return PRE-CALCULATED statistics (not LLM's)
        # 步骤3：返回预计算的统计数据（不是LLM的）
        return ParagraphTransitionResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=result.get("risk_level", "low"),
            total_transitions=total_transitions,  # Use pre-calculated value
            explicit_connector_count=explicit_count,  # Use pre-calculated value
            explicit_ratio=explicit_ratio,  # Use pre-calculated value
            avg_semantic_echo=result.get("avg_semantic_echo", 0.0),
            formulaic_opener_count=formulaic_count,  # Use pre-calculated value
            transitions=transitions,
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        logger.error(f"Paragraph transition analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
