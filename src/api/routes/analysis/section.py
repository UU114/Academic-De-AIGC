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

# Import LLM handlers for Layer 4 substeps
# 导入 Layer 4 子步骤的 LLM handler
from src.api.routes.substeps.layer4.step2_0_handler import Step2_0Handler
from src.api.routes.substeps.layer4.step2_1_handler import Step2_1Handler
from src.api.routes.substeps.layer4.step2_2_handler import Step2_2Handler
from src.api.routes.substeps.layer4.step2_3_handler import Step2_3Handler
from src.api.routes.substeps.layer4.step2_4_handler import Step2_4Handler
from src.api.routes.substeps.layer4.step2_5_handler import Step2_5Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handlers
# 初始化 LLM handler
step2_0_handler = Step2_0Handler()
step2_1_handler = Step2_1Handler()
step2_2_handler = Step2_2Handler()
step2_3_handler = Step2_3Handler()
step2_4_handler = Step2_4Handler()
step2_5_handler = Step2_5Handler()

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
    Step 2.0: Section Identification (LLM-based)
    步骤 2.0：章节识别与角色标注（基于LLM）

    Detects section boundaries and assigns roles to each section using LLM.
    使用LLM检测章节边界并为每个章节分配角色。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return SectionIdentificationResponse(
                section_count=0,
                sections=[],
                total_paragraphs=0,
                total_words=0,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Get paragraphs count for LLM
        # 获取段落数量供LLM使用
        temp_paragraphs = _get_paragraphs_from_request(request)
        paragraph_count = len(temp_paragraphs)

        # Call LLM handler for analysis
        # 调用LLM handler进行分析
        logger.info("Calling Step2_0Handler for LLM-based section identification")
        logger.info(f"Document text length: {len(document_text)} chars")
        logger.info(f"Document has {paragraph_count} paragraphs")
        logger.info(f"Document text preview (first 500 chars): {document_text[:500]}")
        logger.info(f"Document text preview (last 500 chars): {document_text[-500:]}")
        result = await step2_0_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer4-step2-0",
            use_cache=True,
            paragraph_count=paragraph_count
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        sections: List[SectionInfo] = []
        role_distribution: Dict[str, int] = {}

        # Get paragraphs for word count calculation
        # 获取段落用于计算词数
        paragraphs = _get_paragraphs_from_request(request)
        logger.info(f"Total paragraphs: {len(paragraphs)}")
        for i, para in enumerate(paragraphs):
            logger.info(f"  Paragraph {i}: {len(para.split())} words")

        for sec_data in result.get("sections", []):
            role = sec_data.get("role", "body")
            start_idx = sec_data.get("start_paragraph", 0)
            end_idx = sec_data.get("end_paragraph", 0)

            # ALWAYS calculate word_count from actual paragraphs (don't trust LLM's estimation)
            # 总是从实际段落计算词数（不相信LLM的估算）
            word_count = 0
            paragraph_count = 0

            if 0 <= start_idx <= end_idx < len(paragraphs):
                # Calculate from actual paragraphs
                # 从实际段落计算
                section_paragraphs = paragraphs[start_idx:end_idx + 1]
                paragraph_count = len(section_paragraphs)
                word_count = sum(len(p.split()) for p in section_paragraphs)
                logger.info(f"Section {sec_data.get('index', 0)} ({role}): para {start_idx}-{end_idx}, calculated {word_count} words, {paragraph_count} paragraphs")
            else:
                # Fallback: estimate paragraph count
                # 回退：估算段落数
                paragraph_count = max(1, end_idx - start_idx + 1)
                logger.warning(f"Section {sec_data.get('index', 0)}: paragraph index out of range ({start_idx}-{end_idx} vs {len(paragraphs)} paragraphs)")

            sections.append(SectionInfo(
                index=sec_data.get("index", len(sections)),
                role=role,
                role_confidence=sec_data.get("confidence", 0.7),
                start_paragraph_idx=start_idx,
                end_paragraph_idx=end_idx,
                paragraph_count=paragraph_count,
                word_count=word_count,
                char_count=0,
                preview=""
            ))
            role_distribution[role] = role_distribution.get(role, 0) + 1

        # If no sections from LLM, fallback to single body section
        # 如果LLM未返回章节，回退到单一正文章节
        if not sections:
            paragraphs = _get_paragraphs_from_request(request)
            total_words = sum(len(p.split()) for p in paragraphs)

            sections.append(SectionInfo(
                index=0,
                role="body",
                role_confidence=0.5,
                start_paragraph_idx=0,
                end_paragraph_idx=len(paragraphs),
                paragraph_count=len(paragraphs),
                word_count=total_words,
                char_count=sum(len(p) for p in paragraphs),
                preview=paragraphs[0][:150] if paragraphs else ""
            ))
            role_distribution["body"] = 1

        paragraphs = _get_paragraphs_from_request(request)
        total_words = sum(len(p.split()) for p in paragraphs)

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract issues from LLM result
        # 从LLM结果中提取问题
        issues_data = result.get("issues", [])
        issues = []
        for issue in issues_data:
            issues.append(DetectionIssue(
                type=issue.get("type", "unknown"),
                description=issue.get("description", ""),
                description_zh=issue.get("description_zh", ""),
                severity=issue.get("severity", "low"),
                layer="section",
                location=", ".join(issue.get("affected_positions", [])) if issue.get("affected_positions") else None,
                fix_suggestions=issue.get("fix_suggestions", []),
                fix_suggestions_zh=issue.get("fix_suggestions_zh", [])
            ))

        return SectionIdentificationResponse(
            section_count=len(sections),
            sections=sections,
            total_paragraphs=len(paragraphs),
            total_words=total_words,
            role_distribution=role_distribution,
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
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
    Step 2.1: Section Order & Structure Analysis (LLM-based)
    步骤 2.1：章节顺序与结构分析（基于LLM）

    Analyzes section order, detects missing sections, and evaluates function purity.
    分析章节顺序，检测缺失章节，评估功能纯度。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return SectionOrderResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                order_analysis=SectionOrderAnalysis(),
                issues=[],
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Call LLM handler for analysis
        # 调用LLM handler进行分析
        logger.info("Calling Step2_1Handler for LLM-based section order analysis")
        result = await step2_1_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer4-step2-1",
            use_cache=True
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "section_order_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.SECTION,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SectionOrderResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            order_analysis=SectionOrderAnalysis(
                detected_order=result.get("current_order", []),
                expected_order=result.get("expected_order", []),
                order_match_score=result.get("order_match_score", 0) / 100.0 if result.get("order_match_score", 0) > 1 else result.get("order_match_score", 0),
                is_predictable=result.get("order_match_score", 0) >= 80,
                missing_sections=result.get("missing_sections", []),
                unexpected_sections=[],
                fusion_score=result.get("function_fusion_score", 0) / 100.0 if result.get("function_fusion_score", 0) > 1 else result.get("function_fusion_score", 0),
                multi_function_sections=[]
            ),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
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
    Step 2.2: Section Length Distribution Analysis (LLM-based)
    步骤 2.2：章节长度分布分析（基于LLM）

    Analyzes length distribution, CV, extreme sections, and key section weights using LLM.
    使用LLM分析长度分布、变异系数、极端章节和关键章节权重。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return SectionLengthResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Call LLM handler for analysis (with chain-call to detect sections first)
        # 调用LLM handler进行分析（链式调用先检测章节）
        logger.info("Calling Step2_2Handler for LLM-based section length analysis")
        result = await step2_2_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer4-step2-2",
            use_cache=True
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        section_infos: List[SectionLengthInfo] = []
        for sec_data in result.get("sections", []):
            section_infos.append(SectionLengthInfo(
                index=sec_data.get("index", len(section_infos)),
                role=sec_data.get("role", "body"),
                word_count=sec_data.get("word_count", 0),
                paragraph_count=sec_data.get("paragraph_count", 0),
                deviation_from_mean=0.0,
                is_extreme=sec_data.get("deviation", "normal") != "normal",
                expected_weight=EXPECTED_SECTION_WEIGHTS.get(sec_data.get("role", "body"), 0.15),
                actual_weight=0.0,
                weight_deviation=0.0
            ))

        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "section_length_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.SECTION,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SectionLengthResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            section_count=len(section_infos),
            total_words=sum(s.word_count for s in section_infos),
            mean_length=0.0,  # LLM provides overall analysis
            stdev_length=0.0,
            length_cv=result.get("length_cv", 0.0),
            is_uniform=result.get("length_cv", 0.0) < 0.3,
            sections=section_infos,
            extremely_short=result.get("extreme_sections", []),
            extremely_long=[],
            key_section_weight_score=50.0,
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
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
    Step 2.3: Internal Structure Similarity Analysis (LLM-based)
    步骤 2.3：章节内部结构相似性分析（基于LLM）

    Compares internal paragraph function sequences across sections using LLM.
    使用LLM比较不同章节内部段落功能序列的相似性。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return InternalStructureSimilarityResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Call LLM handler for analysis (with chain-call to detect sections first)
        # 调用LLM handler进行分析（链式调用先检测章节）
        logger.info("Calling Step2_3Handler for LLM-based internal structure similarity analysis")
        result = await step2_3_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer4-step2-3",
            use_cache=True
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        section_structures: List[SectionInternalStructure] = []
        for pf_data in result.get("paragraph_functions", []):
            section_structures.append(SectionInternalStructure(
                section_index=pf_data.get("section_index", len(section_structures)),
                section_role="body",
                paragraph_functions=[],
                function_sequence=pf_data.get("functions", []),
                heading_depth=0,
                has_subheadings=False,
                argument_count=0,
                argument_density=0.0
            ))

        # Build similarity pairs from matrix
        similarity_pairs: List[StructureSimilarityPair] = []
        suspicious_pairs: List[StructureSimilarityPair] = []
        similarity_matrix = result.get("similarity_matrix", [])

        for i in range(len(similarity_matrix)):
            for j in range(i + 1, len(similarity_matrix)):
                if j < len(similarity_matrix[i]):
                    similarity = similarity_matrix[i][j] * 100 if similarity_matrix[i][j] <= 1 else similarity_matrix[i][j]
                    is_suspicious = similarity > 70
                    pair = StructureSimilarityPair(
                        section_a_index=i,
                        section_b_index=j,
                        section_a_role="body",
                        section_b_role="body",
                        function_sequence_similarity=similarity,
                        structure_similarity=similarity,
                        is_suspicious=is_suspicious
                    )
                    similarity_pairs.append(pair)
                    if is_suspicious:
                        suspicious_pairs.append(pair)

        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "structure_similarity_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.SECTION,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        return InternalStructureSimilarityResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            section_structures=section_structures,
            similarity_pairs=similarity_pairs,
            average_similarity=result.get("avg_similarity", 0.0) * 100 if result.get("avg_similarity", 0.0) <= 1 else result.get("avg_similarity", 0.0),
            max_similarity=max([p.function_sequence_similarity for p in similarity_pairs], default=0.0),
            heading_depth_cv=result.get("heading_variance", 0.0),
            argument_density_cv=result.get("argument_density_cv", 0.0),
            suspicious_pairs=suspicious_pairs,
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
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
    Step 2.4: Section Transition Analysis (LLM-based)
    步骤 2.4：章节衔接与过渡分析（基于LLM）

    Analyzes transitions between sections using LLM including explicit markers and semantic echo.
    使用LLM分析章节间的过渡，包括显性标记和语义回声。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return SectionTransitionResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Call LLM handler for analysis (with chain-call to detect sections first)
        # 调用LLM handler进行分析（链式调用先检测章节）
        logger.info("Calling Step2_4Handler for LLM-based section transition analysis")
        result = await step2_4_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer4-step2-4",
            use_cache=True
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        transitions: List[SectionTransitionInfo] = []
        for tw_data in result.get("transition_words", []):
            transitions.append(SectionTransitionInfo(
                from_section_index=tw_data.get("from_section", 0),
                to_section_index=tw_data.get("to_section", 0),
                from_section_role="body",
                to_section_role="body",
                has_explicit_transition=len(tw_data.get("words", [])) > 0,
                explicit_words=tw_data.get("words", []),
                transition_strength=tw_data.get("strength", "moderate"),
                semantic_echo_score=0.0,
                echoed_keywords=[],
                opener_text="",
                opener_pattern="natural",
                is_formulaic_opener=False,
                transition_risk_score=0
            ))

        # Add formulaic openers to transitions if available
        for op_data in result.get("opener_patterns", []):
            if op_data.get("is_formulaic", False):
                # Find or create transition for this section
                section_idx = op_data.get("section_index", 0)
                for trans in transitions:
                    if trans.to_section_index == section_idx:
                        trans.is_formulaic_opener = True
                        trans.opener_text = op_data.get("opener", "")
                        trans.opener_pattern = "formulaic"
                        break

        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "transition_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.SECTION,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        strength_distribution = result.get("strength_distribution", {"strong": 0, "moderate": 0, "weak": 0})
        formulaic_count = len([op for op in result.get("opener_patterns", []) if op.get("is_formulaic", False)])

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SectionTransitionResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            total_transitions=len(transitions),
            explicit_transition_count=int(result.get("explicit_transition_ratio", 0) * len(transitions)) if transitions else 0,
            transitions=transitions,
            explicit_ratio=result.get("explicit_transition_ratio", 0.0),
            avg_semantic_echo=result.get("semantic_echo_score", 0.0) * 100 if result.get("semantic_echo_score", 0.0) <= 1 else result.get("semantic_echo_score", 0.0),
            formulaic_opener_count=formulaic_count,
            strength_distribution=strength_distribution,
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
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
    Step 2.5: Inter-Section Logic Analysis (LLM-based)
    步骤 2.5：章节间逻辑关系分析（基于LLM）

    Analyzes argument chains, redundancy, and progression patterns using LLM.
    使用LLM分析论点链、冗余和推进模式。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return InterSectionLogicResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Call LLM handler for analysis (with chain-call to detect sections first)
        # 调用LLM handler进行分析（链式调用先检测章节）
        logger.info("Calling Step2_5Handler for LLM-based inter-section logic analysis")
        result = await step2_5_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer4-step2-5",
            use_cache=True
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        argument_chain: List[ArgumentChainNode] = []
        # LLM doesn't return detailed chain, create minimal structure
        for i, section in enumerate(result.get("detected_sections", [])):
            argument_chain.append(ArgumentChainNode(
                section_index=i,
                section_role=section.get("role", "body"),
                main_argument="",
                supporting_points=[],
                connects_to_previous=i > 0,
                connection_type="extends" if i > 0 else ""
            ))

        redundancies: List[RedundancyInfo] = []
        for red_data in result.get("redundancy_issues", []):
            redundancies.append(RedundancyInfo(
                section_a_index=red_data.get("section_a", 0),
                section_b_index=red_data.get("section_b", 0),
                redundant_content=red_data.get("overlap_content", ""),
                redundancy_type="repeated_phrase",
                severity="medium"
            ))

        progression_patterns: List[ProgressionPatternInfo] = []
        progression_pattern = result.get("progression_pattern", "varied")
        if progression_pattern == "linear":
            progression_patterns.append(ProgressionPatternInfo(
                pattern_type="sequential",
                description="Sections follow a strict sequential order",
                description_zh="章节遵循严格的顺序排列",
                is_ai_typical=True,
                sections_involved=list(range(len(argument_chain)))
            ))
        elif progression_pattern != "varied":
            progression_patterns.append(ProgressionPatternInfo(
                pattern_type=progression_pattern,
                description=f"Sections follow a {progression_pattern} pattern",
                description_zh=f"章节遵循{progression_pattern}模式",
                is_ai_typical=False,
                sections_involved=list(range(len(argument_chain)))
            ))

        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "logic_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.SECTION,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        return InterSectionLogicResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            argument_chain=argument_chain,
            chain_coherence_score=result.get("argument_chain_score", 0.0),
            redundancies=redundancies,
            total_redundancies=len(redundancies),
            progression_patterns=progression_patterns,
            dominant_pattern=result.get("progression_pattern", "varied"),
            pattern_variety_score=100 - result.get("linearity_score", 0),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Inter-section logic analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
