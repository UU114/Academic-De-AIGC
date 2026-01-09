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

logger = logging.getLogger(__name__)
router = APIRouter()

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
    Step 3.0: Paragraph Identification & Segmentation
    步骤 3.0：段落识别与分割

    This is the foundational step for Layer 3 (Paragraph Level Analysis).
    Receives section context from Layer 4 and identifies paragraph boundaries.

    功能：
    - 正确识别段落边界
    - 过滤非正文内容（标题、关键词、表头等）
    - 将段落映射到Section
    - 提取段落元数据
    """
    start_time = time.time()

    try:
        # Split text into paragraphs with filtering
        # 分割文本为段落并过滤
        raw_paragraphs = [p.strip() for p in request.text.split('\n\n') if p.strip()]
        if len(raw_paragraphs) <= 1:
            raw_paragraphs = [p.strip() for p in request.text.split('\n') if p.strip()]

        filtered_paragraphs = []
        paragraph_metadata = []
        filtered_count = 0

        for i, para in enumerate(raw_paragraphs):
            # Segment the paragraph to detect content types
            # 分割段落以检测内容类型
            sentences = _segmenter.segment(para)

            if not sentences:
                filtered_count += 1
                continue

            # If the first sentence is not processable, skip
            # 如果第一个句子不可处理，跳过
            first_sent = sentences[0]
            if not first_sent.should_process:
                filtered_count += 1
                continue

            # Count processable sentences
            # 统计可处理的句子数量
            processable = [s for s in sentences if s.should_process]
            if not processable:
                filtered_count += 1
                continue

            # Use original or rebuild
            # 使用原文或重建
            if len(processable) == len(sentences):
                filtered_paragraphs.append(para)
            else:
                filtered_text = ' '.join(s.text for s in processable)
                if filtered_text.strip():
                    filtered_paragraphs.append(filtered_text)
                else:
                    filtered_count += 1
                    continue

            # Calculate metadata
            # 计算元数据
            para_text = filtered_paragraphs[-1]
            word_count = len(para_text.split())
            preview = para_text[:100] + "..." if len(para_text) > 100 else para_text

            # Determine section index from context
            # 从上下文确定Section索引
            section_index = 0
            if request.section_context and "sections" in request.section_context:
                sections = request.section_context["sections"]
                para_idx = len(filtered_paragraphs) - 1
                for sec in sections:
                    start = sec.get("startParagraphIdx", sec.get("start_paragraph_idx", 0))
                    end = sec.get("endParagraphIdx", sec.get("end_paragraph_idx", 0))
                    if start <= para_idx <= end:
                        section_index = sec.get("index", 0)
                        break

            paragraph_metadata.append(ParagraphMeta(
                index=len(filtered_paragraphs) - 1,
                word_count=word_count,
                sentence_count=len(processable),
                char_count=len(para_text),
                preview=preview,
                section_index=section_index,
                content_type="body",
            ))

        # Build section map
        # 构建Section映射
        paragraph_section_map = [m.section_index or 0 for m in paragraph_metadata]

        # Calculate total word count
        # 计算总词数
        total_word_count = sum(m.word_count for m in paragraph_metadata)

        # Generate recommendations
        # 生成建议
        recommendations = []
        recommendations_zh = []

        if len(filtered_paragraphs) < 3:
            recommendations.append("Document has very few paragraphs. Consider adding more content structure.")
            recommendations_zh.append("文档段落较少，建议添加更多内容结构。")

        if filtered_count > len(filtered_paragraphs):
            recommendations.append(f"Filtered {filtered_count} non-body paragraphs (headers, keywords, etc.).")
            recommendations_zh.append(f"已过滤{filtered_count}个非正文段落（标题、关键词等）。")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ParagraphIdentificationResponse(
            paragraphs=filtered_paragraphs,
            paragraph_count=len(filtered_paragraphs),
            paragraph_section_map=paragraph_section_map,
            paragraph_metadata=paragraph_metadata,
            filtered_count=filtered_count,
            total_word_count=total_word_count,
            risk_level="low",
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
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
    Step 3.1: Paragraph Role Detection
    步骤 3.1：段落角色识别

    Classifies each paragraph's function:
    - Introduction, background, methodology, results, discussion, conclusion
    - Transition paragraphs
    - Detects role distribution anomalies
    """
    start_time = time.time()

    try:
        orchestrator = ParagraphOrchestrator()

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles,
            sections=request.section_context.get("sections") if request.section_context else None,
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract role-specific details
        role_details = result.details.get("roles", {})

        return ParagraphAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "role" in i.type or "homogeneous" in i.type or "transition" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=role_details,
            processing_time_ms=processing_time_ms,
            paragraph_roles=result.updated_context.paragraph_roles or [],
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
    Step 3.2: Paragraph Internal Coherence
    步骤 3.2：段落内部连贯性

    Analyzes sentence relationships within paragraphs:
    - Subject diversity
    - Logic structure
    - Connector density
    - Overall coherence score
    """
    start_time = time.time()

    try:
        orchestrator = ParagraphOrchestrator()

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles,
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract coherence-specific details
        coherence_details = result.details.get("coherence", {})

        return ParagraphAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "coherence" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=coherence_details,
            processing_time_ms=processing_time_ms,
            paragraph_roles=result.updated_context.paragraph_roles or [],
            coherence_scores=result.updated_context.paragraph_coherence or [],
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
    Step 3.3: Anchor Density Analysis
    步骤 3.3：锚点密度分析

    Analyzes evidence density in paragraphs:
    - 13 anchor types (citations, numbers, proper nouns, etc.)
    - Calculates anchors per 100 words
    - Flags high hallucination risk (<5 anchors/100 words)
    """
    start_time = time.time()

    try:
        orchestrator = ParagraphOrchestrator()

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles,
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract anchor-specific details
        anchor_details = result.details.get("anchor_density", {})

        return ParagraphAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "anchor" in i.type or "density" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=anchor_details,
            processing_time_ms=processing_time_ms,
            paragraph_roles=result.updated_context.paragraph_roles or [],
            coherence_scores=[],
            anchor_densities=result.updated_context.paragraph_anchor_density or [],
            sentence_length_cvs=[],
            low_burstiness_paragraphs=[],
        )

    except Exception as e:
        logger.error(f"Anchor density analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sentence-length", response_model=ParagraphAnalysisResponse)
async def analyze_sentence_length_distribution(request: ParagraphAnalysisRequest):
    """
    Step 3.4: Sentence Length Distribution
    步骤 3.4：段内句子长度分布

    Analyzes sentence length variation within each paragraph:
    - Calculates within-paragraph length CV (coefficient of variation)
    - Detects monotonous length patterns (AI pattern)
    - Flags paragraphs with low burstiness
    """
    start_time = time.time()

    try:
        orchestrator = ParagraphOrchestrator()

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles,
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract sentence length-specific details
        length_details = result.details.get("sentence_lengths", {})
        low_burst_paras = length_details.get("low_burstiness_paragraphs", [])

        return ParagraphAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "length" in i.type or "burstiness" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=length_details,
            processing_time_ms=processing_time_ms,
            paragraph_roles=result.updated_context.paragraph_roles or [],
            coherence_scores=[],
            anchor_densities=[],
            sentence_length_cvs=[p.get("cv", 0) for p in low_burst_paras] if low_burst_paras else [],
            low_burstiness_paragraphs=[p.get("index", 0) for p in low_burst_paras] if low_burst_paras else [],
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
        low_burst_paras = length_details.get("low_burstiness_paragraphs", [])

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
            sentence_length_cvs=[p.get("cv", 0) for p in low_burst_paras] if low_burst_paras else [],
            low_burstiness_paragraphs=[p.get("index", 0) for p in low_burst_paras] if low_burst_paras else [],
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
    Step 3.5: Paragraph Transition Analysis
    步骤 3.5：段落间过渡分析

    Analyzes transitions between adjacent paragraphs:
    - Detects explicit connectors at paragraph openings
    - Calculates semantic echo scores (keyword overlap)
    - Identifies formulaic opener patterns
    - Provides transition quality assessment

    功能：
    - 检测段首显性连接词
    - 计算语义回声分数（关键词重叠）
    - 识别公式化开头模式
    - 提供过渡质量评估
    """
    start_time = time.time()

    try:
        # Get paragraphs
        # 获取段落
        if request.paragraphs:
            paragraphs = request.paragraphs
        elif request.text:
            paragraphs = _split_text_to_paragraphs(request.text)
        else:
            raise HTTPException(status_code=400, detail="Either text or paragraphs must be provided")

        if len(paragraphs) < 2:
            return ParagraphTransitionResponse(
                risk_score=0,
                risk_level="low",
                total_transitions=0,
                explicit_connector_count=0,
                explicit_ratio=0.0,
                avg_semantic_echo=0.0,
                formulaic_opener_count=0,
                transitions=[],
                recommendations=["Document has fewer than 2 paragraphs, no transitions to analyze."],
                recommendations_zh=["文档段落少于2个，无法进行过渡分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        transitions = []
        explicit_count = 0
        formulaic_count = 0
        echo_scores = []

        # Compile formulaic patterns
        # 编译公式化模式
        formulaic_patterns = [re.compile(p, re.IGNORECASE) for p in FORMULAIC_OPENERS]

        # Flatten all connectors
        # 展平所有连接词
        all_connectors = []
        for category, words in EXPLICIT_CONNECTORS.items():
            all_connectors.extend(words)

        for i in range(len(paragraphs) - 1):
            para_a = paragraphs[i]
            para_b = paragraphs[i + 1]

            # Get opening of paragraph B (first ~50 words)
            # 获取段落B的开头（前50词左右）
            opener_words = para_b.split()[:50]
            opener_text = ' '.join(opener_words[:15]) + "..." if len(opener_words) > 15 else ' '.join(opener_words)
            opener_lower = para_b.lower()

            # Check for explicit connectors
            # 检查显性连接词
            found_connectors = []
            for conn in all_connectors:
                if opener_lower.startswith(conn) or opener_lower.startswith(conn + ","):
                    found_connectors.append(conn)
            has_explicit = len(found_connectors) > 0
            if has_explicit:
                explicit_count += 1

            # Check for formulaic openers
            # 检查公式化开头
            opener_pattern = ""
            is_formulaic = False
            for pattern in formulaic_patterns:
                match = pattern.match(para_b)
                if match:
                    is_formulaic = True
                    opener_pattern = match.group(0)
                    break
            if is_formulaic:
                formulaic_count += 1

            # Calculate semantic echo (simple keyword overlap)
            # 计算语义回声（简单关键词重叠）
            para_a_words = set(w.lower() for w in para_a.split() if len(w) > 4)
            para_b_words = set(w.lower() for w in para_b.split() if len(w) > 4)
            common_words = para_a_words & para_b_words
            echoed_keywords = list(common_words)[:5]  # Top 5 echoed keywords

            if len(para_a_words) > 0:
                echo_score = len(common_words) / len(para_a_words)
            else:
                echo_score = 0.0
            echo_scores.append(echo_score)

            # Determine transition quality
            # 确定过渡质量
            if has_explicit or is_formulaic:
                quality = "formulaic"
                risk = 60
            elif echo_score > 0.1:
                quality = "smooth"
                risk = 20
            else:
                quality = "abrupt"
                risk = 40

            transitions.append(ParagraphTransitionInfo(
                from_paragraph=i,
                to_paragraph=i + 1,
                has_explicit_connector=has_explicit,
                connector_words=found_connectors,
                semantic_echo_score=round(echo_score, 3),
                echoed_keywords=echoed_keywords,
                transition_quality=quality,
                opener_text=opener_text,
                opener_pattern=opener_pattern,
                is_formulaic_opener=is_formulaic,
                risk_score=risk,
            ))

        # Calculate overall metrics
        # 计算整体指标
        total_transitions = len(transitions)
        explicit_ratio = explicit_count / total_transitions if total_transitions > 0 else 0.0
        avg_echo = sum(echo_scores) / len(echo_scores) if echo_scores else 0.0

        # Calculate overall risk score
        # 计算整体风险分数
        if explicit_ratio > 0.5:
            risk_score = 70
            risk_level = "high"
        elif explicit_ratio > 0.3 or formulaic_count > 2:
            risk_score = 50
            risk_level = "medium"
        else:
            risk_score = 25
            risk_level = "low"

        # Generate recommendations
        # 生成建议
        recommendations = []
        recommendations_zh = []
        issues = []

        if explicit_ratio > 0.3:
            recommendations.append(f"High explicit connector ratio ({explicit_ratio:.1%}). Consider using semantic echoes instead of explicit connectors like 'Furthermore', 'Moreover'.")
            recommendations_zh.append(f"显性连接词比例较高 ({explicit_ratio:.1%})。建议用语义回声代替'Furthermore'、'Moreover'等显性连接词。")
            issues.append({
                "type": "high_explicit_ratio",
                "description": f"Explicit connector ratio is {explicit_ratio:.1%}",
                "description_zh": f"显性连接词比例为 {explicit_ratio:.1%}",
                "severity": "medium",
            })

        if formulaic_count > 2:
            recommendations.append(f"Found {formulaic_count} formulaic openers. Vary your paragraph openings for more natural flow.")
            recommendations_zh.append(f"发现{formulaic_count}个公式化开头。建议变化段落开头以获得更自然的行文。")
            issues.append({
                "type": "formulaic_openers",
                "description": f"Found {formulaic_count} formulaic paragraph openers",
                "description_zh": f"发现 {formulaic_count} 个公式化段落开头",
                "severity": "medium",
            })

        if avg_echo < 0.05:
            recommendations.append("Low semantic echo between paragraphs. Consider linking paragraphs by referencing key concepts from the previous paragraph.")
            recommendations_zh.append("段落间语义回声较低。建议通过引用上一段的关键概念来连接段落。")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ParagraphTransitionResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            total_transitions=total_transitions,
            explicit_connector_count=explicit_count,
            explicit_ratio=round(explicit_ratio, 3),
            avg_semantic_echo=round(avg_echo, 3),
            formulaic_opener_count=formulaic_count,
            transitions=transitions,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        logger.error(f"Paragraph transition analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
