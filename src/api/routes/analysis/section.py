"""
Section Layer API Routes (Layer 4)
章节层API路由（第4层）

Sub-step Endpoints:
- POST /step2-0/identify - Step 2.0: Section Identification
- POST /step2-1/order - Step 2.1: Section Order & Structure
- POST /step2-2/length - Step 2.2: Section Length Distribution
- POST /step2-3/similarity - Step 2.3: Internal Structure Similarity (NEW)
- POST /step2-4/transition - Step 2.4: Section Transition
- POST /step2-5/logic - Step 2.5: Inter-Section Logic

Legacy Endpoints:
- POST /logic - Step 2.1: Section Logic Flow (legacy)
- POST /transition - Step 2.2: Section Transitions (legacy)
- POST /length - Step 2.3: Section Length Distribution (legacy)
- POST /analyze - Combined section analysis
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any, List, Tuple
import logging
import time
import re
import statistics
from collections import Counter

from src.api.routes.analysis.schemas import (
    SectionAnalysisRequest,
    SectionAnalysisResponse,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
    IssueSeverity,
    # Step 2.0 schemas
    SectionIdentificationRequest,
    SectionIdentificationResponse,
    SectionInfo,
    # Step 2.1 schemas
    SectionOrderRequest,
    SectionOrderResponse,
    SectionOrderAnalysis,
    # Step 2.2 schemas
    SectionLengthRequest,
    SectionLengthResponse,
    SectionLengthInfo,
    # Step 2.3 schemas
    InternalStructureSimilarityRequest,
    InternalStructureSimilarityResponse,
    SectionInternalStructure,
    ParagraphFunctionInfo,
    StructureSimilarityPair,
    # Step 2.4 schemas
    SectionTransitionRequest,
    SectionTransitionResponse,
    SectionTransitionInfo,
    # Step 2.5 schemas
    InterSectionLogicRequest,
    InterSectionLogicResponse,
    ArgumentChainNode,
    RedundancyInfo,
    ProgressionPatternInfo,
)
from src.core.analyzer.layers import SectionAnalyzer, LayerContext
from src.core.preprocessor.segmenter import SentenceSegmenter, ContentType

logger = logging.getLogger(__name__)
router = APIRouter()

# Reusable segmenter instance
# 可重用的分句器实例
_segmenter = SentenceSegmenter()


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


def _get_paragraphs(request: SectionAnalysisRequest) -> list:
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
        layer=LayerLevel.SECTION,
        position=issue.position,
        suggestion=issue.suggestion,
        suggestion_zh=issue.suggestion_zh,
        details=issue.details,
    )


@router.post("/logic", response_model=SectionAnalysisResponse)
async def analyze_section_logic(request: SectionAnalysisRequest):
    """
    Step 2.1: Section Logic Flow
    步骤 2.1：章节逻辑?

    Analyzes logical relationships between sections:
    - Check section sequence rationality
    - Detect structural anomalies
    - Compare against expected academic structure
    """
    start_time = time.time()

    try:
        analyzer = SectionAnalyzer()
        paragraphs = _get_paragraphs(request)

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=paragraphs,
            document_structure=request.document_context or {},
        )

        # Run analysis
        result = await analyzer.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract logic-specific details
        logic_details = result.details.get("logic_flow", {})
        sections = result.details.get("sections", [])

        # Transform section details for frontend
        section_details = _transform_section_details(sections)

        return SectionAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if i.type.startswith(("predictable", "missing"))],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=logic_details,
            processing_time_ms=processing_time_ms,
            section_details=section_details,
            section_count=len(sections),
            logic_flow_score=0,
            transition_quality=0,
            logic_flow=logic_details,
            transitions=[],
            length_distribution=None,
        )

    except Exception as e:
        logger.error(f"Section logic analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transition", response_model=SectionAnalysisResponse)
async def analyze_section_transitions(request: SectionAnalysisRequest):
    """
    Step 2.2: Section Transitions
    步骤 2.2：章节衔?

    Analyzes transition quality between sections:
    - Detect abrupt topic changes
    - Evaluate cross-section coherence
    - Check for AI-like explicit transitions
    """
    start_time = time.time()

    try:
        analyzer = SectionAnalyzer()
        paragraphs = _get_paragraphs(request)

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=paragraphs,
            document_structure=request.document_context or {},
        )

        # Run analysis
        result = await analyzer.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract transition-specific details
        transitions = result.details.get("transitions", {})
        sections = result.details.get("sections", [])

        # Transform section details for frontend
        section_details = _transform_section_details(sections)

        return SectionAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "transition" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=transitions,
            processing_time_ms=processing_time_ms,
            section_details=section_details,
            section_count=len(sections),
            logic_flow_score=0,
            transition_quality=transitions.get("explicit_transition_count", 0),
            logic_flow=None,
            transitions=result.updated_context.section_transitions or [],
            length_distribution=None,
        )

    except Exception as e:
        logger.error(f"Section transition analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/length", response_model=SectionAnalysisResponse)
async def analyze_section_length(request: SectionAnalysisRequest):
    """
    Step 2.3: Section Length Distribution
    步骤 2.3：章节长度分?

    Analyzes length balance across sections:
    - Detect abnormal length patterns
    - Calculate length CV (coefficient of variation)
    - Identify very short or long sections
    """
    start_time = time.time()

    try:
        analyzer = SectionAnalyzer()
        paragraphs = _get_paragraphs(request)

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=paragraphs,
            document_structure=request.document_context or {},
        )

        # Run analysis
        result = await analyzer.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract length-specific details
        length_details = result.details.get("length_distribution", {})
        sections = result.details.get("sections", [])

        # Transform section details for frontend
        section_details = _transform_section_details(sections)

        return SectionAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "length" in i.type or "short" in i.type or "long" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=length_details,
            processing_time_ms=processing_time_ms,
            section_details=section_details,
            section_count=len(sections),
            logic_flow_score=0,
            transition_quality=0,
            logic_flow=None,
            transitions=[],
            length_distribution=_transform_length_distribution(length_details),
        )

    except Exception as e:
        logger.error(f"Section length analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _transform_length_distribution(length_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform length distribution data to frontend-expected format.
    将长度分布数据转换为前端期望的格式?

    Backend returns: mean_length, stdev_length, length_cv
    Frontend expects: mean, stdDev, cv, isUniform
    """
    if not length_details:
        return None

    cv = length_details.get("length_cv", 0)
    return {
        "mean": length_details.get("mean_length", 0),
        "stdDev": length_details.get("stdev_length", 0),
        "cv": cv,
        "isUniform": cv < 0.3 if cv else False,  # CV < 0.3 is considered uniform (AI-like)
    }


def _transform_section_details(sections: list) -> list:
    """
    Transform section details to include expected frontend fields.
    转换章节详情以包含前端期望的字段?
    """
    transformed = []
    for idx, section in enumerate(sections):
        transformed.append({
            "index": idx,
            "role": section.get("role", "unknown"),
            "wordCount": section.get("word_count", 0),
            "transitionScore": section.get("transition_score", 0),
            "issues": section.get("issues", []),
        })
    return transformed


@router.post("/analyze", response_model=SectionAnalysisResponse)
async def analyze_section(request: SectionAnalysisRequest):
    """
    Combined Section Analysis (Layer 4)
    综合章节分析（第4层）

    Runs all section-level analysis steps:
    - Step 2.1: Section Logic Flow
    - Step 2.2: Section Transitions
    - Step 2.3: Section Length Distribution

    Returns complete section-level analysis results with context
    for passing to lower layers.
    """
    start_time = time.time()

    try:
        analyzer = SectionAnalyzer()
        paragraphs = _get_paragraphs(request)

        # Create context with paragraphs and optional document context
        context = LayerContext(
            paragraphs=paragraphs,
            document_structure=request.document_context or {},
        )

        # Run full analysis
        result = await analyzer.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract all details
        sections = result.details.get("sections", [])
        logic_flow = result.details.get("logic_flow", {})
        transitions_detail = result.details.get("transitions", {})
        length_distribution = result.details.get("length_distribution", {})

        # Transform section details for frontend
        section_details = _transform_section_details(sections)

        # Debug log to check section_details
        logger.info(f"Section analysis - sections count: {len(sections)}, section_details: {section_details[:2] if section_details else 'empty'}")

        # Calculate scores for frontend display
        logic_flow_score = int(logic_flow.get("order_match_score", 0) * 100) if logic_flow else 0
        transition_quality = transitions_detail.get("explicit_transition_count", 0)

        return SectionAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=result.details,
            processing_time_ms=processing_time_ms,
            section_details=section_details,
            section_count=len(sections),
            logic_flow_score=logic_flow_score,
            transition_quality=transition_quality,
            logic_flow=logic_flow,
            transitions=result.updated_context.section_transitions or [],
            length_distribution=_transform_length_distribution(length_distribution),
        )

    except Exception as e:
        logger.error(f"Section analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context")
async def get_section_context(request: SectionAnalysisRequest):
    """
    Get section context for passing to lower layers
    获取章节上下文以传递给下层

    Returns the updated LayerContext that can be used
    to initialize lower layer analysis.
    """
    try:
        analyzer = SectionAnalyzer()
        paragraphs = _get_paragraphs(request)

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=paragraphs,
            document_structure=request.document_context or {},
        )

        # Run analysis
        result = await analyzer.analyze(context)

        # Return the updated context as dict
        return {
            "sections": result.updated_context.sections,
            "section_boundaries": result.updated_context.section_boundaries,
            "section_transitions": result.updated_context.section_transitions,
        }

    except Exception as e:
        logger.error(f"Section context extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Layer 4 Sub-step API Routes (Step 2.0 - 2.5)
# 第4层子步骤API路由（步骤 2.0 - 2.5）
# =============================================================================

# Section role patterns for detection
# 章节角色检测模式
SECTION_ROLE_PATTERNS = {
    "introduction": [
        r"\bintroduction\b", r"\bbackground\b", r"\boverview\b",
        r"\bthis (paper|study|research|work)\b", r"\bwe (present|propose|introduce)\b"
    ],
    "literature_review": [
        r"\bliterature\s+review\b", r"\brelated\s+work\b", r"\bprior\s+(work|research)\b",
        r"\bprevious\s+studies\b", r"\bstate\s+of\s+the\s+art\b"
    ],
    "methodology": [
        r"\bmethodology\b", r"\bmethods?\b", r"\bapproach\b", r"\bprocedure\b",
        r"\bexperimental\s+design\b", r"\bdata\s+collection\b"
    ],
    "results": [
        r"\bresults?\b", r"\bfindings?\b", r"\bobservation\b",
        r"\b(we|our)\s+(found|observed|noted)\b", r"\bthe\s+data\s+show\b"
    ],
    "discussion": [
        r"\bdiscussion\b", r"\bimplications?\b", r"\binterpreting\b",
        r"\bthese\s+(results|findings)\s+(suggest|indicate|demonstrate)\b"
    ],
    "conclusion": [
        r"\bconclusion\b", r"\bsummary\b", r"\bin\s+conclusion\b",
        r"\bfuture\s+(work|research|directions?)\b", r"\blimitations?\b"
    ],
}

# Paragraph function patterns
# 段落功能模式
PARAGRAPH_FUNCTION_PATTERNS = {
    "topic_sentence": [
        r"^this\s+(section|paper|study)\s+", r"^in\s+this\s+(section|paper)\s+",
        r"^the\s+(main|primary|key)\s+", r"^we\s+(argue|propose|suggest|examine)\s+"
    ],
    "evidence": [
        r"\baccording\s+to\b", r"\bresearch\s+shows\b", r"\bstudies\s+(indicate|show|demonstrate)\b",
        r"\bdata\s+from\b", r"\bthe\s+results\s+(show|indicate)\b", r"\d+%", r"\bp\s*[<>=]"
    ],
    "analysis": [
        r"\bthis\s+(suggests|indicates|demonstrates)\b", r"\bcan\s+be\s+(explained|understood)\b",
        r"\bthe\s+reason\s+for\b", r"\bone\s+possible\s+explanation\b"
    ],
    "example": [
        r"\bfor\s+(example|instance)\b", r"\bsuch\s+as\b", r"\bto\s+illustrate\b",
        r"\bconsider\s+the\s+case\b", r"\ba\s+good\s+example\b"
    ],
    "transition": [
        r"^(however|moreover|furthermore|additionally|in\s+addition)\b",
        r"^on\s+the\s+other\s+hand\b", r"^in\s+contrast\b"
    ],
    "mini_conclusion": [
        r"\bin\s+summary\b", r"\bto\s+summarize\b", r"\boverall\b",
        r"\btherefore\b", r"\bthus\b", r"\bconsequently\b"
    ],
}

# Transition word patterns by strength
# 按强度分类的过渡词模式
TRANSITION_WORD_PATTERNS = {
    "strong": [
        r"\bhaving\s+established\b", r"\bbuilding\s+on\b", r"\bgiven\s+the\b",
        r"\bwith\s+this\s+(understanding|foundation)\b", r"\bbased\s+on\b",
        r"\bas\s+demonstrated\s+above\b", r"\bas\s+mentioned\s+earlier\b"
    ],
    "moderate": [
        r"^\s*(now|next)\b", r"^turning\s+to\b", r"^moving\s+to\b",
        r"^(first|second|third|finally)\b", r"^in\s+the\s+following\s+section\b"
    ],
    "weak": [
        r"^(however|moreover|furthermore|additionally)\b", r"^in\s+addition\b",
        r"^consequently\b", r"^therefore\b"
    ],
}

# Argument markers
# 论点标记
ARGUMENT_MARKERS = [
    r"\bwe\s+argue\s+that\b", r"\bour\s+claim\s+is\b", r"\bthe\s+(main|key)\s+point\b",
    r"\bit\s+is\s+important\s+to\s+note\b", r"\bsignificantly\b", r"\bcrucially\b",
    r"\bthe\s+evidence\s+suggests\b", r"\bthis\s+demonstrates\b"
]


def _get_paragraphs_from_request(request) -> List[str]:
    """
    Extract paragraphs from various request types
    从各种请求类型中提取段落
    """
    if hasattr(request, 'paragraphs') and request.paragraphs:
        return request.paragraphs
    elif hasattr(request, 'text') and request.text:
        return _split_text_to_paragraphs(request.text)
    else:
        return []


def _detect_paragraph_role(para: str) -> Tuple[str, float]:
    """
    Detect the role of a paragraph based on content patterns
    根据内容模式检测段落的角色

    Returns: (role, confidence)
    """
    para_lower = para.lower()
    matches = {}

    for role, patterns in SECTION_ROLE_PATTERNS.items():
        match_count = 0
        for pattern in patterns:
            if re.search(pattern, para_lower):
                match_count += 1
        if match_count > 0:
            matches[role] = match_count

    if not matches:
        return ("body", 0.5)

    best_role = max(matches, key=matches.get)
    confidence = min(1.0, matches[best_role] / 3)  # Scale to 0-1

    return (best_role, confidence)


def _detect_paragraph_function(para: str, position: str = "middle") -> Tuple[str, float]:
    """
    Detect the function of a paragraph within a section
    检测段落在章节内的功能

    Args:
        para: Paragraph text
        position: "first", "last", or "middle"

    Returns: (function, confidence)
    """
    para_lower = para.lower()

    # Check for specific function patterns
    for func, patterns in PARAGRAPH_FUNCTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, para_lower):
                return (func, 0.8)

    # Position-based heuristics
    if position == "first":
        return ("topic_sentence", 0.6)
    elif position == "last":
        return ("mini_conclusion", 0.5)
    else:
        # Check for evidence indicators
        if re.search(r'\d+', para):  # Contains numbers
            return ("evidence", 0.5)
        return ("elaboration", 0.4)


def _calculate_sequence_similarity(seq1: List[str], seq2: List[str]) -> float:
    """
    Calculate similarity between two function sequences using edit distance
    使用编辑距离计算两个功能序列之间的相似性

    Returns: Similarity percentage (0-100)
    """
    if not seq1 or not seq2:
        return 0.0

    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i-1] == seq2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    edit_distance = dp[m][n]
    max_len = max(m, n)
    similarity = (1 - edit_distance / max_len) * 100 if max_len > 0 else 0

    return round(similarity, 1)


def _extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    Extract important keywords from text
    从文本中提取重要关键词
    """
    # Remove common stopwords
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "and", "but", "or",
        "nor", "for", "yet", "so", "as", "if", "of", "at", "by", "from", "up",
        "down", "in", "out", "on", "off", "over", "under", "to", "into", "onto",
        "this", "that", "these", "those", "it", "its", "their", "our", "we",
        "they", "them", "which", "what", "who", "whom", "with", "about"
    }

    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    word_counts = Counter(w for w in words if w not in stopwords)

    return [w for w, _ in word_counts.most_common(top_n)]


# -----------------------------------------------------------------------------
# Step 2.0: Section Identification / 步骤 2.0：章节识别
# -----------------------------------------------------------------------------

@router.post("/step2-0/identify", response_model=SectionIdentificationResponse)
async def identify_sections(request: SectionIdentificationRequest):
    """
    Step 2.0: Section Identification
    步骤 2.0：章节识别与角色标注

    Detects section boundaries and assigns roles to each section.
    检测章节边界并为每个章节分配角色。
    """
    start_time = time.time()

    try:
        paragraphs = _get_paragraphs_from_request(request)

        if not paragraphs:
            return SectionIdentificationResponse(
                section_count=0,
                sections=[],
                total_paragraphs=0,
                total_words=0,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Detect sections and roles
        # 检测章节和角色
        sections: List[SectionInfo] = []
        current_role = None
        current_start = 0
        role_distribution: Dict[str, int] = {}

        for idx, para in enumerate(paragraphs):
            detected_role, confidence = _detect_paragraph_role(para)

            # Check for section boundary (role change)
            # 检查章节边界（角色变化）
            if detected_role != current_role and detected_role != "body":
                # Save previous section if exists
                if current_role is not None and idx > current_start:
                    section_paras = paragraphs[current_start:idx]
                    word_count = sum(len(p.split()) for p in section_paras)
                    char_count = sum(len(p) for p in section_paras)

                    sections.append(SectionInfo(
                        index=len(sections),
                        role=current_role,
                        role_confidence=0.7,
                        start_paragraph_idx=current_start,
                        end_paragraph_idx=idx,
                        paragraph_count=idx - current_start,
                        word_count=word_count,
                        char_count=char_count,
                        preview=section_paras[0][:150] if section_paras else ""
                    ))

                    role_distribution[current_role] = role_distribution.get(current_role, 0) + 1

                current_role = detected_role
                current_start = idx
            elif current_role is None:
                current_role = detected_role
                current_start = idx

        # Add final section
        # 添加最后一个章节
        if current_role is not None:
            section_paras = paragraphs[current_start:]
            word_count = sum(len(p.split()) for p in section_paras)
            char_count = sum(len(p) for p in section_paras)

            sections.append(SectionInfo(
                index=len(sections),
                role=current_role,
                role_confidence=0.7,
                start_paragraph_idx=current_start,
                end_paragraph_idx=len(paragraphs),
                paragraph_count=len(paragraphs) - current_start,
                word_count=word_count,
                char_count=char_count,
                preview=section_paras[0][:150] if section_paras else ""
            ))

            role_distribution[current_role] = role_distribution.get(current_role, 0) + 1

        # If no sections detected, treat as single body section
        # 如果未检测到章节，视为单一正文章节
        if not sections:
            total_words = sum(len(p.split()) for p in paragraphs)
            total_chars = sum(len(p) for p in paragraphs)

            sections.append(SectionInfo(
                index=0,
                role="body",
                role_confidence=0.5,
                start_paragraph_idx=0,
                end_paragraph_idx=len(paragraphs),
                paragraph_count=len(paragraphs),
                word_count=total_words,
                char_count=total_chars,
                preview=paragraphs[0][:150] if paragraphs else ""
            ))
            role_distribution["body"] = 1

        total_words = sum(s.word_count for s in sections)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SectionIdentificationResponse(
            section_count=len(sections),
            sections=sections,
            total_paragraphs=len(paragraphs),
            total_words=total_words,
            role_distribution=role_distribution,
            recommendations=[],
            recommendations_zh=[],
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Section identification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Step 2.1: Section Order & Structure / 步骤 2.1：章节顺序与结构
# -----------------------------------------------------------------------------

@router.post("/step2-1/order", response_model=SectionOrderResponse)
async def analyze_section_order(request: SectionOrderRequest):
    """
    Step 2.1: Section Order & Structure Analysis
    步骤 2.1：章节顺序与结构分析

    Analyzes section order, detects missing sections, and evaluates function purity.
    分析章节顺序，检测缺失章节，评估功能纯度。
    """
    start_time = time.time()

    try:
        # Get or detect sections
        # 获取或检测章节
        if request.sections:
            sections = request.sections
        else:
            paragraphs = _get_paragraphs_from_request(request)
            # Use Step 2.0 logic to detect sections
            id_response = await identify_sections(SectionIdentificationRequest(
                paragraphs=paragraphs
            ))
            sections = [s.model_dump() for s in id_response.sections]

        if not sections:
            return SectionOrderResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                order_analysis=SectionOrderAnalysis(),
                issues=[],
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Expected academic order
        # 预期的学术顺序
        expected_order = ["introduction", "literature_review", "methodology", "results", "discussion", "conclusion"]
        detected_order = [s.get("role", "unknown") for s in sections]

        # Calculate order match score
        # 计算顺序匹配分数
        filtered_detected = [r for r in detected_order if r in expected_order]
        order_match_score = 0.0

        if filtered_detected:
            matches = 0
            last_idx = -1
            for role in filtered_detected:
                exp_idx = expected_order.index(role) if role in expected_order else -1
                if exp_idx > last_idx:
                    matches += 1
                    last_idx = exp_idx
            order_match_score = matches / len(filtered_detected)

        is_predictable = order_match_score >= 0.8

        # Detect missing critical sections
        # 检测缺失的关键章节
        missing_sections = []
        for critical in ["introduction", "methodology", "conclusion"]:
            if critical not in detected_order:
                missing_sections.append(critical)

        # Analyze function fusion (single purpose vs multi-purpose)
        # 分析功能融合度
        fusion_score = 1.0  # Assume perfect purity initially
        multi_function_sections = []

        # Issues and recommendations
        # 问题和建议
        issues: List[DetectionIssue] = []
        recommendations = []
        recommendations_zh = []

        if is_predictable:
            issues.append(DetectionIssue(
                type="predictable_section_order",
                description="Section order follows a highly predictable academic template",
                description_zh="章节顺序遵循高度可预测的学术模板",
                severity=IssueSeverity.MEDIUM,
                layer=LayerLevel.SECTION,
                suggestion="Consider non-linear narrative or integrated discussions",
                suggestion_zh="考虑非线性叙事或整合式讨论"
            ))
            recommendations.append("Add digressions or combine related sections")
            recommendations_zh.append("添加旁白或合并相关章节")

        # Calculate risk score
        # 计算风险分数
        risk_score = int(order_match_score * 60)  # Up to 60 points for predictability
        if not missing_sections:
            risk_score += 20  # Additional points for having all sections
        risk_level = RiskLevel.HIGH if risk_score >= 60 else (RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SectionOrderResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            order_analysis=SectionOrderAnalysis(
                detected_order=detected_order,
                expected_order=expected_order,
                order_match_score=order_match_score,
                is_predictable=is_predictable,
                missing_sections=missing_sections,
                unexpected_sections=[],
                fusion_score=fusion_score,
                multi_function_sections=multi_function_sections
            ),
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Section order analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Step 2.2: Section Length Distribution / 步骤 2.2：章节长度分布
# -----------------------------------------------------------------------------

# Expected weight for key sections
# 关键章节的预期权重
EXPECTED_SECTION_WEIGHTS = {
    "introduction": 0.15,
    "literature_review": 0.15,
    "methodology": 0.25,
    "results": 0.20,
    "discussion": 0.15,
    "conclusion": 0.10,
}


@router.post("/step2-2/length", response_model=SectionLengthResponse)
async def analyze_section_length(request: SectionLengthRequest):
    """
    Step 2.2: Section Length Distribution Analysis
    步骤 2.2：章节长度分布分析

    Analyzes length distribution, CV, extreme sections, and key section weights.
    分析长度分布、变异系数、极端章节和关键章节权重。
    """
    start_time = time.time()

    try:
        # Get or detect sections
        # 获取或检测章节
        paragraphs = []
        if request.sections:
            sections = request.sections
            if request.paragraphs:
                paragraphs = request.paragraphs
        else:
            paragraphs = _get_paragraphs_from_request(request)
            id_response = await identify_sections(SectionIdentificationRequest(
                paragraphs=paragraphs
            ))
            sections = [s.model_dump() for s in id_response.sections]

        if not sections:
            return SectionLengthResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Calculate length statistics
        # 计算长度统计
        lengths = [s.get("word_count", 0) for s in sections]
        total_words = sum(lengths)

        if len(lengths) < 2:
            return SectionLengthResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                section_count=len(sections),
                total_words=total_words,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        mean_length = statistics.mean(lengths)
        stdev_length = statistics.stdev(lengths) if len(lengths) > 1 else 0
        length_cv = stdev_length / mean_length if mean_length > 0 else 0
        is_uniform = length_cv < 0.3

        # Build section length info
        # 构建章节长度信息
        section_infos: List[SectionLengthInfo] = []
        extremely_short: List[int] = []
        extremely_long: List[int] = []

        for idx, section in enumerate(sections):
            word_count = section.get("word_count", 0)
            role = section.get("role", "body")
            para_count = section.get("paragraph_count", 0)

            deviation = (word_count - mean_length) / stdev_length if stdev_length > 0 else 0
            is_extreme = abs(deviation) > 1.5

            if deviation < -1.5 and word_count < 100:
                extremely_short.append(idx)
            elif deviation > 1.5:
                extremely_long.append(idx)

            # Calculate weight deviation
            # 计算权重偏差
            actual_weight = word_count / total_words if total_words > 0 else 0
            expected_weight = EXPECTED_SECTION_WEIGHTS.get(role, 0.15)
            weight_deviation = actual_weight - expected_weight

            section_infos.append(SectionLengthInfo(
                index=idx,
                role=role,
                word_count=word_count,
                paragraph_count=para_count,
                deviation_from_mean=round(deviation, 2),
                is_extreme=is_extreme,
                expected_weight=expected_weight,
                actual_weight=round(actual_weight, 3),
                weight_deviation=round(weight_deviation, 3)
            ))

        # Calculate key section weight score
        # 计算关键章节权重分数
        weight_deviations = [abs(s.weight_deviation) for s in section_infos if s.expected_weight]
        key_section_weight_score = 100 - (sum(weight_deviations) * 100) if weight_deviations else 50

        # Issues and recommendations
        # 问题和建议
        issues: List[DetectionIssue] = []
        recommendations = []
        recommendations_zh = []

        if is_uniform:
            issues.append(DetectionIssue(
                type="uniform_section_lengths",
                description=f"Section lengths are too uniform (CV: {length_cv:.2f})",
                description_zh=f"章节长度过于均匀（变异系数：{length_cv:.2f}）",
                severity=IssueSeverity.MEDIUM,
                layer=LayerLevel.SECTION,
                suggestion="Vary section lengths - methodology should be longer than introduction",
                suggestion_zh="改变章节长度——方法论应该比引言更长"
            ))
            recommendations.append("Create asymmetric section lengths")
            recommendations_zh.append("创建非对称章节长度")

        # Calculate risk score
        # 计算风险分数
        risk_score = 0
        if is_uniform:
            risk_score += int((0.3 - length_cv) / 0.3 * 50)  # Up to 50 points for uniform
        if not extremely_short and not extremely_long:
            risk_score += 20  # Additional points for no extreme variation

        risk_level = RiskLevel.HIGH if risk_score >= 50 else (RiskLevel.MEDIUM if risk_score >= 25 else RiskLevel.LOW)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SectionLengthResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            section_count=len(sections),
            total_words=total_words,
            mean_length=round(mean_length, 1),
            stdev_length=round(stdev_length, 1),
            length_cv=round(length_cv, 3),
            is_uniform=is_uniform,
            sections=section_infos,
            extremely_short=extremely_short,
            extremely_long=extremely_long,
            key_section_weight_score=round(key_section_weight_score, 1),
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Section length analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Step 2.3: Internal Structure Similarity (NEW) / 步骤 2.3：章节内部结构相似性
# -----------------------------------------------------------------------------

@router.post("/step2-3/similarity", response_model=InternalStructureSimilarityResponse)
async def analyze_internal_structure_similarity(request: InternalStructureSimilarityRequest):
    """
    Step 2.3: Internal Structure Similarity Analysis (NEW)
    步骤 2.3：章节内部结构相似性分析（新）

    Compares internal paragraph function sequences across sections.
    比较不同章节内部段落功能序列的相似性。
    """
    start_time = time.time()

    try:
        # Get paragraphs and sections
        # 获取段落和章节
        paragraphs = []
        if request.paragraphs:
            paragraphs = request.paragraphs
        elif request.text:
            paragraphs = _split_text_to_paragraphs(request.text)

        if request.sections:
            sections = request.sections
        else:
            id_response = await identify_sections(SectionIdentificationRequest(
                paragraphs=paragraphs
            ))
            sections = [s.model_dump() for s in id_response.sections]

        if len(sections) < 2:
            return InternalStructureSimilarityResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Analyze internal structure of each section
        # 分析每个章节的内部结构
        section_structures: List[SectionInternalStructure] = []

        for section in sections:
            section_idx = section.get("index", 0)
            section_role = section.get("role", "body")
            start_para = section.get("start_paragraph_idx", 0)
            end_para = section.get("end_paragraph_idx", len(paragraphs))

            section_paras = paragraphs[start_para:end_para] if paragraphs else []

            # Detect paragraph functions
            # 检测段落功能
            para_functions: List[ParagraphFunctionInfo] = []
            function_sequence: List[str] = []

            for local_idx, para in enumerate(section_paras):
                global_idx = start_para + local_idx
                position = "first" if local_idx == 0 else ("last" if local_idx == len(section_paras) - 1 else "middle")

                func, confidence = _detect_paragraph_function(para, position)

                para_functions.append(ParagraphFunctionInfo(
                    paragraph_index=global_idx,
                    local_index=local_idx,
                    function=func,
                    function_confidence=confidence,
                    preview=para[:100] if para else ""
                ))
                function_sequence.append(func)

            # Count argument markers
            # 统计论点标记
            section_text = " ".join(section_paras)
            argument_count = sum(1 for pattern in ARGUMENT_MARKERS if re.search(pattern, section_text.lower()))
            word_count = len(section_text.split())
            argument_density = (argument_count / word_count * 100) if word_count > 0 else 0

            section_structures.append(SectionInternalStructure(
                section_index=section_idx,
                section_role=section_role,
                paragraph_functions=para_functions,
                function_sequence=function_sequence,
                heading_depth=0,  # Would need heading detection
                has_subheadings=False,
                argument_count=argument_count,
                argument_density=round(argument_density, 2)
            ))

        # Calculate pairwise similarity
        # 计算成对相似性
        similarity_pairs: List[StructureSimilarityPair] = []
        suspicious_pairs: List[StructureSimilarityPair] = []
        all_similarities = []

        for i in range(len(section_structures)):
            for j in range(i + 1, len(section_structures)):
                struct_a = section_structures[i]
                struct_b = section_structures[j]

                seq_similarity = _calculate_sequence_similarity(
                    struct_a.function_sequence,
                    struct_b.function_sequence
                )

                # Overall structure similarity (can be extended)
                structure_similarity = seq_similarity  # For now, just sequence similarity

                is_suspicious = seq_similarity > 80

                pair = StructureSimilarityPair(
                    section_a_index=struct_a.section_index,
                    section_b_index=struct_b.section_index,
                    section_a_role=struct_a.section_role,
                    section_b_role=struct_b.section_role,
                    function_sequence_similarity=seq_similarity,
                    structure_similarity=structure_similarity,
                    is_suspicious=is_suspicious
                )

                similarity_pairs.append(pair)
                all_similarities.append(seq_similarity)

                if is_suspicious:
                    suspicious_pairs.append(pair)

        # Calculate aggregate metrics
        # 计算聚合指标
        avg_similarity = statistics.mean(all_similarities) if all_similarities else 0
        max_similarity = max(all_similarities) if all_similarities else 0

        # Calculate CV for argument density and heading depth
        # 计算论点密度和标题深度的变异系数
        arg_densities = [s.argument_density for s in section_structures]
        heading_depths = [s.heading_depth for s in section_structures]

        arg_density_cv = 0.0
        if len(arg_densities) > 1 and statistics.mean(arg_densities) > 0:
            arg_density_cv = statistics.stdev(arg_densities) / statistics.mean(arg_densities)

        heading_depth_cv = 0.0
        if len(heading_depths) > 1 and statistics.mean(heading_depths) > 0:
            heading_depth_cv = statistics.stdev(heading_depths) / statistics.mean(heading_depths)

        # Issues and recommendations
        # 问题和建议
        issues: List[DetectionIssue] = []
        recommendations = []
        recommendations_zh = []

        if suspicious_pairs:
            issues.append(DetectionIssue(
                type="high_structure_similarity",
                description=f"Found {len(suspicious_pairs)} section pairs with >80% structural similarity",
                description_zh=f"发现{len(suspicious_pairs)}对章节结构相似度超过80%",
                severity=IssueSeverity.HIGH,
                layer=LayerLevel.SECTION,
                suggestion="Vary the internal structure of sections",
                suggestion_zh="变化章节的内部结构"
            ))
            recommendations.append("Use different paragraph organization patterns in different sections")
            recommendations_zh.append("在不同章节使用不同的段落组织模式")

        # Calculate risk score
        # 计算风险分数
        risk_score = int(avg_similarity * 0.5)  # 50% weight on average similarity
        if max_similarity > 80:
            risk_score += 30  # Additional penalty for high similarity

        risk_level = RiskLevel.HIGH if risk_score >= 60 else (RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return InternalStructureSimilarityResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            section_structures=section_structures,
            similarity_pairs=similarity_pairs,
            average_similarity=round(avg_similarity, 1),
            max_similarity=round(max_similarity, 1),
            heading_depth_cv=round(heading_depth_cv, 3),
            argument_density_cv=round(arg_density_cv, 3),
            suspicious_pairs=suspicious_pairs,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Internal structure similarity analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Step 2.4: Section Transition / 步骤 2.4：章节衔接与过渡
# -----------------------------------------------------------------------------

@router.post("/step2-4/transition", response_model=SectionTransitionResponse)
async def analyze_section_transition(request: SectionTransitionRequest):
    """
    Step 2.4: Section Transition Analysis
    步骤 2.4：章节衔接与过渡分析

    Analyzes transitions between sections including explicit markers and semantic echo.
    分析章节间的过渡，包括显性标记和语义回声。
    """
    start_time = time.time()

    try:
        # Get paragraphs and sections
        # 获取段落和章节
        paragraphs = []
        if request.paragraphs:
            paragraphs = request.paragraphs
        elif request.text:
            paragraphs = _split_text_to_paragraphs(request.text)

        if request.sections:
            sections = request.sections
        else:
            id_response = await identify_sections(SectionIdentificationRequest(
                paragraphs=paragraphs
            ))
            sections = [s.model_dump() for s in id_response.sections]

        if len(sections) < 2:
            return SectionTransitionResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Analyze transitions between consecutive sections
        # 分析连续章节之间的过渡
        transitions: List[SectionTransitionInfo] = []
        strength_distribution: Dict[str, int] = {"strong": 0, "moderate": 0, "weak": 0, "none": 0}
        explicit_count = 0
        formulaic_count = 0
        echo_scores = []

        for i in range(len(sections) - 1):
            from_section = sections[i]
            to_section = sections[i + 1]

            from_idx = from_section.get("index", i)
            to_idx = to_section.get("index", i + 1)
            from_role = from_section.get("role", "body")
            to_role = to_section.get("role", "body")

            # Get opener of target section
            # 获取目标章节的开头
            to_start = to_section.get("start_paragraph_idx", 0)
            opener_para = paragraphs[to_start] if to_start < len(paragraphs) else ""
            opener_sentences = re.split(r'[.!?]+', opener_para)
            opener_text = opener_sentences[0].strip() if opener_sentences else ""

            # Detect explicit transition words
            # 检测显性过渡词
            explicit_words = []
            transition_strength = "none"

            opener_lower = opener_text.lower()
            for strength, patterns in TRANSITION_WORD_PATTERNS.items():
                for pattern in patterns:
                    match = re.search(pattern, opener_lower)
                    if match:
                        explicit_words.append(match.group())
                        if transition_strength == "none" or strength == "strong":
                            transition_strength = strength

            has_explicit = len(explicit_words) > 0
            if has_explicit:
                explicit_count += 1

            strength_distribution[transition_strength] += 1

            # Detect formulaic opener
            # 检测公式化开头
            formulaic_patterns = [
                r"^in\s+this\s+section", r"^this\s+section", r"^the\s+following\s+section",
                r"^as\s+mentioned", r"^having\s+discussed"
            ]
            is_formulaic = any(re.search(p, opener_lower) for p in formulaic_patterns)
            if is_formulaic:
                formulaic_count += 1

            # Calculate semantic echo
            # 计算语义回声
            from_end = from_section.get("end_paragraph_idx", 0)
            from_paras = paragraphs[from_section.get("start_paragraph_idx", 0):from_end]
            to_paras = paragraphs[to_start:to_section.get("end_paragraph_idx", len(paragraphs))]

            from_text = " ".join(from_paras)
            to_text = " ".join(to_paras[:2])  # First 2 paragraphs of target

            from_keywords = set(_extract_keywords(from_text, 10))
            to_keywords = set(_extract_keywords(to_text, 10))
            echoed = from_keywords & to_keywords
            echo_score = (len(echoed) / len(from_keywords) * 100) if from_keywords else 0
            echo_scores.append(echo_score)

            # Calculate transition risk
            # 计算过渡风险
            trans_risk = 0
            if has_explicit:
                trans_risk += 30
            if is_formulaic:
                trans_risk += 20
            if echo_score < 20:
                trans_risk += 20

            transitions.append(SectionTransitionInfo(
                from_section_index=from_idx,
                to_section_index=to_idx,
                from_section_role=from_role,
                to_section_role=to_role,
                has_explicit_transition=has_explicit,
                explicit_words=explicit_words,
                transition_strength=transition_strength,
                semantic_echo_score=round(echo_score, 1),
                echoed_keywords=list(echoed)[:5],
                opener_text=opener_text[:200],
                opener_pattern="formulaic" if is_formulaic else "natural",
                is_formulaic_opener=is_formulaic,
                transition_risk_score=trans_risk
            ))

        # Calculate aggregate metrics
        # 计算聚合指标
        total_transitions = len(transitions)
        explicit_ratio = explicit_count / total_transitions if total_transitions > 0 else 0
        avg_echo = statistics.mean(echo_scores) if echo_scores else 0

        # Issues and recommendations
        # 问题和建议
        issues: List[DetectionIssue] = []
        recommendations = []
        recommendations_zh = []

        if explicit_ratio > 0.7:
            issues.append(DetectionIssue(
                type="excessive_explicit_transitions",
                description=f"Too many explicit transitions ({explicit_count}/{total_transitions})",
                description_zh=f"显性过渡过多（{explicit_count}/{total_transitions}）",
                severity=IssueSeverity.MEDIUM,
                layer=LayerLevel.SECTION,
                suggestion="Use semantic echo instead of explicit transitions",
                suggestion_zh="使用语义回声代替显性过渡"
            ))
            recommendations.append("Replace transition words with keyword echoes")
            recommendations_zh.append("用关键词回声替换过渡词")

        if formulaic_count > 0:
            issues.append(DetectionIssue(
                type="formulaic_section_openers",
                description=f"Found {formulaic_count} formulaic section openers",
                description_zh=f"发现{formulaic_count}个公式化章节开头",
                severity=IssueSeverity.LOW,
                layer=LayerLevel.SECTION,
                suggestion="Vary section opening patterns",
                suggestion_zh="变化章节开头模式"
            ))

        # Calculate risk score
        # 计算风险分数
        risk_score = int(explicit_ratio * 40) + int((100 - avg_echo) * 0.3)
        if formulaic_count > 0:
            risk_score += formulaic_count * 10

        risk_score = min(100, risk_score)
        risk_level = RiskLevel.HIGH if risk_score >= 60 else (RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SectionTransitionResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            total_transitions=total_transitions,
            explicit_transition_count=explicit_count,
            transitions=transitions,
            explicit_ratio=round(explicit_ratio, 3),
            avg_semantic_echo=round(avg_echo, 1),
            formulaic_opener_count=formulaic_count,
            strength_distribution=strength_distribution,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Section transition analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Step 2.5: Inter-Section Logic / 步骤 2.5：章节间逻辑关系
# -----------------------------------------------------------------------------

@router.post("/step2-5/logic", response_model=InterSectionLogicResponse)
async def analyze_inter_section_logic(request: InterSectionLogicRequest):
    """
    Step 2.5: Inter-Section Logic Analysis
    步骤 2.5：章节间逻辑关系分析

    Analyzes argument chains, redundancy, and progression patterns.
    分析论点链、冗余和推进模式。
    """
    start_time = time.time()

    try:
        # Get paragraphs and sections
        # 获取段落和章节
        paragraphs = []
        if request.paragraphs:
            paragraphs = request.paragraphs
        elif request.text:
            paragraphs = _split_text_to_paragraphs(request.text)

        if request.sections:
            sections = request.sections
        else:
            id_response = await identify_sections(SectionIdentificationRequest(
                paragraphs=paragraphs
            ))
            sections = [s.model_dump() for s in id_response.sections]

        if not sections:
            return InterSectionLogicResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Build argument chain
        # 构建论点链
        argument_chain: List[ArgumentChainNode] = []
        prev_keywords = set()

        for section in sections:
            section_idx = section.get("index", 0)
            section_role = section.get("role", "body")
            start_para = section.get("start_paragraph_idx", 0)
            end_para = section.get("end_paragraph_idx", len(paragraphs))

            section_paras = paragraphs[start_para:end_para] if paragraphs else []
            section_text = " ".join(section_paras)

            # Extract main argument (first sentence of first paragraph)
            first_sentences = re.split(r'[.!?]+', section_paras[0]) if section_paras else []
            main_argument = first_sentences[0].strip() if first_sentences else ""

            # Extract supporting points (look for argument markers)
            supporting_points = []
            for pattern in ARGUMENT_MARKERS[:4]:
                matches = re.findall(pattern + r'[^.!?]+', section_text.lower())
                supporting_points.extend(matches[:2])

            # Check connection to previous section
            current_keywords = set(_extract_keywords(section_text, 10))
            connects_to_prev = len(prev_keywords & current_keywords) >= 2

            # Determine connection type
            connection_type = ""
            if section_idx > 0:
                if section_role == "discussion" and sections[section_idx-1].get("role") == "results":
                    connection_type = "interprets"
                elif section_role == "conclusion":
                    connection_type = "summarizes"
                elif connects_to_prev:
                    connection_type = "extends"

            argument_chain.append(ArgumentChainNode(
                section_index=section_idx,
                section_role=section_role,
                main_argument=main_argument[:200],
                supporting_points=supporting_points[:3],
                connects_to_previous=connects_to_prev,
                connection_type=connection_type
            ))

            prev_keywords = current_keywords

        # Detect redundancy
        # 检测冗余
        redundancies: List[RedundancyInfo] = []

        for i in range(len(sections)):
            for j in range(i + 1, len(sections)):
                sec_i = sections[i]
                sec_j = sections[j]

                # Get section texts
                text_i = " ".join(paragraphs[sec_i.get("start_paragraph_idx", 0):sec_i.get("end_paragraph_idx", 0)])
                text_j = " ".join(paragraphs[sec_j.get("start_paragraph_idx", 0):sec_j.get("end_paragraph_idx", 0)])

                # Check for repeated phrases (simple n-gram overlap)
                words_i = text_i.lower().split()
                words_j = text_j.lower().split()

                # 4-gram overlap
                ngrams_i = set(" ".join(words_i[k:k+4]) for k in range(len(words_i)-3))
                ngrams_j = set(" ".join(words_j[k:k+4]) for k in range(len(words_j)-3))

                overlap = ngrams_i & ngrams_j
                if len(overlap) > 3:
                    redundancies.append(RedundancyInfo(
                        section_a_index=i,
                        section_b_index=j,
                        redundant_content=list(overlap)[0] if overlap else "",
                        redundancy_type="repeated_phrase",
                        severity="medium" if len(overlap) > 5 else "low"
                    ))

        # Detect progression patterns
        # 检测推进模式
        progression_patterns: List[ProgressionPatternInfo] = []

        # Check for sequential pattern
        roles = [s.get("role", "body") for s in sections]
        if roles == sorted(roles, key=lambda x: ["introduction", "literature_review", "methodology", "results", "discussion", "conclusion"].index(x) if x in ["introduction", "literature_review", "methodology", "results", "discussion", "conclusion"] else 999):
            progression_patterns.append(ProgressionPatternInfo(
                pattern_type="sequential",
                description="Sections follow a strict sequential order",
                description_zh="章节遵循严格的顺序排列",
                is_ai_typical=True,
                sections_involved=list(range(len(sections)))
            ))

        # Calculate chain coherence
        # 计算链条连贯性
        connected_count = sum(1 for node in argument_chain if node.connects_to_previous)
        chain_coherence = (connected_count / (len(argument_chain) - 1) * 100) if len(argument_chain) > 1 else 0

        # Determine dominant pattern
        # 确定主导模式
        dominant_pattern = progression_patterns[0].pattern_type if progression_patterns else "varied"

        # Pattern variety score
        # 模式多样性分数
        pattern_variety = 100 - (len(progression_patterns) * 20)  # Fewer patterns = more variety

        # Issues and recommendations
        # 问题和建议
        issues: List[DetectionIssue] = []
        recommendations = []
        recommendations_zh = []

        if any(p.is_ai_typical for p in progression_patterns):
            issues.append(DetectionIssue(
                type="predictable_progression",
                description="Document follows AI-typical sequential progression",
                description_zh="文档遵循AI典型的顺序推进模式",
                severity=IssueSeverity.MEDIUM,
                layer=LayerLevel.SECTION,
                suggestion="Add non-linear elements or returns to earlier points",
                suggestion_zh="添加非线性元素或回扣前文"
            ))
            recommendations.append("Break sequential flow with cross-references")
            recommendations_zh.append("用交叉引用打破顺序流")

        if redundancies:
            issues.append(DetectionIssue(
                type="content_redundancy",
                description=f"Found {len(redundancies)} instances of content redundancy",
                description_zh=f"发现{len(redundancies)}处内容冗余",
                severity=IssueSeverity.LOW,
                layer=LayerLevel.SECTION,
                suggestion="Remove redundant content or consolidate into one section",
                suggestion_zh="删除冗余内容或合并到一个章节"
            ))

        # Calculate risk score
        # 计算风险分数
        risk_score = 0
        if any(p.is_ai_typical for p in progression_patterns):
            risk_score += 40
        if chain_coherence > 80:
            risk_score += 20  # Too coherent can be suspicious
        risk_score += len(redundancies) * 5

        risk_score = min(100, risk_score)
        risk_level = RiskLevel.HIGH if risk_score >= 60 else (RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return InterSectionLogicResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            argument_chain=argument_chain,
            chain_coherence_score=round(chain_coherence, 1),
            redundancies=redundancies,
            total_redundancies=len(redundancies),
            progression_patterns=progression_patterns,
            dominant_pattern=dominant_pattern,
            pattern_variety_score=max(0, pattern_variety),
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Inter-section logic analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
