"""
Sentence Layer API Routes (Layer 2)
句子层API路由（第2层）

**IMPORTANT DESIGN PRINCIPLE | 重要设计原则**:
All sentence-level analysis MUST be performed within paragraph context.
Sentence rewriting with context-aware content requires paragraph-level information.

所有句子层分析必须在段落上下文中进行。
与上下文相关的句子改写需要段落级别信息的支持。

New Sub-Step Endpoints (按段落迭代处理):
- POST /step4-0/identify - Step 4.0: Sentence Identification & Labeling
- POST /step4-1/pattern - Step 4.1: Sentence Pattern Analysis
- POST /step4-2/length - Step 4.2: In-Paragraph Length Analysis
- POST /step4-3/merge - Step 4.3: Sentence Merger Suggestions
- POST /step4-4/connector - Step 4.4: Connector Optimization
- POST /step4-5/diversify - Step 4.5: Pattern Diversification
- POST /paragraph/{para_idx}/config - Paragraph processing config
- POST /paragraph/{para_idx}/process - Process single paragraph
- POST /paragraph/{para_idx}/revert - Revert to version
- GET /paragraph/{para_idx}/versions - Get version history
- POST /batch/config - Batch config multiple paragraphs
- POST /batch/lock - Batch lock/unlock paragraphs

Legacy Endpoints (kept for backward compatibility):
- POST /pattern - Step 4.1: Sentence Pattern Detection
- POST /void - Step 4.2: Syntactic Void Detection
- POST /role - Step 4.3: Sentence Role Classification
- POST /polish-context - Step 4.4: Sentence Polish Context
- POST /analyze - Combined sentence analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import logging
import time
import statistics

from src.api.routes.analysis.schemas import (
    SentenceAnalysisRequest,
    SentenceAnalysisResponse,
    SentenceWithContext,
    RewriteContextRequest,
    RewriteContextResponse,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
    IssueSeverity,
)
from src.core.analyzer.layers import SentenceOrchestrator, LayerContext
from src.core.analyzer.sentence_context import (
    SentenceContextProvider,
    create_sentence_context_from_layer_results,
)
from src.core.preprocessor.segmenter import SentenceSegmenter, ContentType

# Import Syntactic Void Detector for detecting semantically empty AI patterns
# 导入句法空洞检测器用于检测语义空洞的AI模式
try:
    from src.core.analyzer.syntactic_void import (
        detect_syntactic_voids,
        SyntacticVoidResult,
    )
    VOID_DETECTOR_AVAILABLE = True
except ImportError:
    VOID_DETECTOR_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter()

# Reusable segmenter instance
# 可重用的分句器实例
_segmenter = SentenceSegmenter()


# ============================================================================
# New Pydantic Models for Layer 2 Sub-Steps
# Layer 2 子步骤的新 Pydantic 模型
# ============================================================================

class SentenceInfo(BaseModel):
    """
    Information about a single sentence.
    单个句子的信息。
    """
    index: int
    text: str
    paragraph_index: int
    word_count: int
    sentence_type: str = "simple"  # simple/compound/complex/compound_complex
    function_role: str = "body"  # topic/evidence/analysis/transition/conclusion
    has_subordinate: bool = False
    clause_depth: int = 0
    voice: str = "active"  # active/passive
    opener_word: str = ""


class SentenceIdentificationRequest(BaseModel):
    """
    Request for sentence identification (Step 4.0).
    句子识别请求（步骤4.0）。
    """
    text: Optional[str] = None
    paragraphs: Optional[List[str]] = None
    session_id: Optional[str] = None
    paragraph_context: Optional[Dict[str, Any]] = None


class SentenceIdentificationResponse(BaseModel):
    """
    Response for sentence identification (Step 4.0).
    句子识别响应（步骤4.0）。
    """
    sentences: List[SentenceInfo]
    sentence_count: int
    paragraph_sentence_map: Dict[int, List[int]]
    type_distribution: Dict[str, int]
    risk_level: str
    risk_score: int
    issues: List[Dict[str, Any]] = []
    recommendations: List[str]
    recommendations_zh: List[str]
    processing_time_ms: int


class PatternAnalysisRequest(BaseModel):
    """
    Request for pattern analysis (Step 4.1).
    句式结构分析请求（步骤4.1）。
    """
    text: Optional[str] = None
    paragraphs: Optional[List[str]] = None
    sentences: Optional[List[SentenceInfo]] = None
    paragraph_sentence_map: Optional[Dict[int, List[int]]] = None
    session_id: Optional[str] = None


class TypeStats(BaseModel):
    """
    Statistics for a sentence type.
    句式类型统计。
    """
    count: int
    percentage: float
    is_risk: bool
    threshold: float


class OpenerAnalysis(BaseModel):
    """
    Analysis of sentence openers.
    句首词分析。
    """
    opener_counts: Dict[str, int]
    top_repeated: List[str]
    repetition_rate: float
    subject_opening_rate: float
    issues: List[str]


class PatternAnalysisResponse(BaseModel):
    """
    Response for pattern analysis (Step 4.1).
    句式结构分析响应（步骤4.1）。

    Now includes Syntactic Void Detection integration.
    现已集成句法空洞检测。
    """
    type_distribution: Dict[str, TypeStats]
    opener_analysis: OpenerAnalysis
    voice_distribution: Dict[str, int]
    clause_depth_stats: Dict[str, float]
    parallel_structure_count: int
    issues: List[Dict[str, Any]]
    risk_level: str
    risk_score: int
    high_risk_paragraphs: List[Dict[str, Any]] = []
    recommendations: List[str]
    recommendations_zh: List[str]
    processing_time_ms: int
    # Syntactic Void Detection fields (integrated from core/analyzer/syntactic_void.py)
    # 句法空洞检测字段（从 core/analyzer/syntactic_void.py 集成）
    syntactic_voids: List[Dict[str, Any]] = Field(default_factory=list, description="Detected syntactic void patterns / 检测到的句法空洞模式")
    void_score: int = Field(0, ge=0, le=100, description="Overall void score 0-100 / 总体空洞分数")
    void_density: float = Field(0, description="Voids per 100 words / 每100词的空洞数")
    has_critical_void: bool = Field(False, description="Has high-severity void patterns / 是否有高严重度空洞")


class LengthAnalysisRequest(BaseModel):
    """
    Request for length analysis (Step 4.2).
    句长分析请求（步骤4.2）。
    """
    text: Optional[str] = None
    paragraphs: Optional[List[str]] = None
    paragraph_index: Optional[int] = None  # For single paragraph processing
    session_id: Optional[str] = None


class LengthAnalysisResponse(BaseModel):
    """
    Response for length analysis (Step 4.2).
    句长分析响应（步骤4.2）。
    """
    paragraph_length_stats: List[Dict[str, Any]]
    overall_length_cv: float
    uniformity_issues: List[Dict[str, Any]]
    merge_candidates: List[Dict[str, Any]]
    split_candidates: List[Dict[str, Any]]
    risk_level: str
    risk_score: int
    recommendations: List[str]
    recommendations_zh: List[str]
    processing_time_ms: int


class MergeSuggestionRequest(BaseModel):
    """
    Request for sentence merge suggestions (Step 4.3).
    句子合并建议请求（步骤4.3）。
    """
    paragraph_text: str
    paragraph_index: int
    sentences: Optional[List[SentenceInfo]] = None
    max_merge_count: int = 2
    session_id: Optional[str] = None


class MergeCandidate(BaseModel):
    """
    A candidate for sentence merging.
    句子合并候选。
    """
    sentence_indices: List[int]
    original_sentences: List[str]
    merged_text: str
    merge_type: str  # causal/contrast/temporal/addition
    similarity_score: float
    readability_score: float
    word_count_before: int
    word_count_after: int
    complexity_gain: str  # simple->complex, simple->compound_complex


class MergeSuggestionResponse(BaseModel):
    """
    Response for sentence merge suggestions (Step 4.3).
    句子合并建议响应（步骤4.3）。
    """
    paragraph_index: int
    candidates: List[MergeCandidate]
    estimated_improvement: Dict[str, float]
    risk_level: str
    recommendations: List[str]
    recommendations_zh: List[str]
    processing_time_ms: int


class ConnectorOptimizationRequest(BaseModel):
    """
    Request for connector optimization (Step 4.4).
    连接词优化请求（步骤4.4）。
    """
    paragraph_text: str
    paragraph_index: int
    preserve_connectors: List[str] = []
    session_id: Optional[str] = None


class ConnectorIssue(BaseModel):
    """
    A connector issue.
    连接词问题。
    """
    sentence_index: int
    connector: str
    connector_type: str  # addition/causal/contrast/sequence/summary
    position: str  # start/middle
    risk_level: str
    context: str


class ReplacementSuggestion(BaseModel):
    """
    A replacement suggestion for a connector.
    连接词替换建议。
    """
    original_connector: str
    sentence_index: int
    replacement_type: str  # semantic_echo/remove/subordinate/pronoun/lexical
    new_text: str
    explanation: str
    explanation_zh: str


class ConnectorOptimizationResponse(BaseModel):
    """
    Response for connector optimization (Step 4.4).
    连接词优化响应（步骤4.4）。
    """
    paragraph_index: int
    connector_issues: List[ConnectorIssue]
    total_connectors: int
    explicit_ratio: float
    connector_type_distribution: Dict[str, int]
    replacement_suggestions: List[ReplacementSuggestion]
    risk_level: str
    recommendations: List[str]
    recommendations_zh: List[str]
    processing_time_ms: int


class DiversificationRequest(BaseModel):
    """
    Request for pattern diversification (Step 4.5).
    句式多样化请求（步骤4.5）。
    """
    paragraph_text: str
    paragraph_index: int
    rewrite_intensity: Literal["conservative", "moderate", "aggressive"] = "moderate"
    target_passive_ratio: Optional[float] = None
    session_id: Optional[str] = None


class ChangeRecord(BaseModel):
    """
    Record of a single change.
    单个修改记录。
    """
    sentence_index: int
    original: str
    modified: str
    change_type: str  # merge/split/rewrite/connector_remove/opener_change/voice_switch
    strategy: str
    improvement_type: str  # opener/voice/structure/length


class PatternMetrics(BaseModel):
    """
    Pattern metrics for before/after comparison.
    用于前后对比的句式指标。
    """
    simple_ratio: float
    compound_ratio: float
    complex_ratio: float
    compound_complex_ratio: float
    opener_diversity: float
    voice_balance: float
    length_cv: float
    overall_score: float


class DiversificationResponse(BaseModel):
    """
    Response for pattern diversification (Step 4.5).
    句式多样化响应（步骤4.5）。
    """
    paragraph_index: int
    original_text: str
    diversified_text: str
    changes: List[ChangeRecord]
    applied_strategies: Dict[str, int]
    before_metrics: PatternMetrics
    after_metrics: PatternMetrics
    improvement_summary: Dict[str, float]
    risk_level: str
    recommendations: List[str]
    recommendations_zh: List[str]
    processing_time_ms: int


# Paragraph config and version models
# 段落配置和版本模型

class ParagraphParams(BaseModel):
    """
    Paragraph-level parameter overrides.
    段落级参数覆盖。
    """
    target_passive_ratio: Optional[float] = None
    allow_merge: bool = True
    max_merge_count: int = 2
    preserve_connectors: List[str] = []
    rewrite_intensity: Literal["conservative", "moderate", "aggressive"] = "moderate"


class ParagraphVersion(BaseModel):
    """
    Version record for paragraph edits.
    段落编辑的版本记录。
    """
    version: int
    step: str
    text: str
    timestamp: str
    changes: List[ChangeRecord] = []
    metrics: Optional[Dict[str, float]] = None


class ParagraphProcessingConfig(BaseModel):
    """
    Configuration for processing each paragraph.
    每个段落的处理配置。
    """
    paragraph_index: int
    status: Literal["pending", "in_progress", "completed", "skipped", "locked"] = "pending"
    mode: Literal["auto", "merge_only", "connector_only", "diversify_only", "custom"] = "auto"
    enabled_steps: List[str] = ["step4-2", "step4-3", "step4-4", "step4-5"]
    params: ParagraphParams = Field(default_factory=ParagraphParams)
    versions: List[ParagraphVersion] = []
    current_version: int = 0


class BatchConfigRequest(BaseModel):
    """
    Request for batch configuration.
    批量配置请求。
    """
    paragraph_indices: List[int]
    config: Dict[str, Any]


class BatchLockRequest(BaseModel):
    """
    Request for batch lock/unlock.
    批量锁定/解锁请求。
    """
    paragraph_indices: List[int]
    locked: bool


# In-memory storage for paragraph configs (session-based)
# 段落配置的内存存储（基于会话）
_paragraph_configs: Dict[str, Dict[int, ParagraphProcessingConfig]] = {}


# ============================================================================
# Helper Functions for Layer 2 Sub-Step Analysis
# Layer 2 子步骤分析的帮助函数
# ============================================================================

# AI connector patterns by category
# AI连接词模式分类
AI_CONNECTORS = {
    "addition": ["Furthermore", "Moreover", "Additionally", "In addition", "Besides"],
    "causal": ["Therefore", "Thus", "Hence", "Consequently", "As a result"],
    "contrast": ["However", "Nevertheless", "On the other hand", "In contrast"],
    "sequence": ["First", "Second", "Third", "Finally", "Lastly"],
    "summary": ["In conclusion", "To summarize", "Overall", "In summary"],
}

# Subject pronouns and articles that indicate subject-first opening
# 表示主语开头的代词和冠词
SUBJECT_OPENERS = ["The", "This", "These", "It", "They", "We", "I", "A", "An"]

# Subordinate clause markers
# 从句标记词
SUBORDINATE_MARKERS = [
    "although", "though", "while", "whereas", "because", "since", "if", "unless",
    "when", "whenever", "where", "wherever", "who", "which", "that", "whom", "whose"
]

# Passive voice indicators
# 被动语态指示词
PASSIVE_INDICATORS = ["was", "were", "is", "are", "been", "being", "be"]


def _classify_sentence_type(text: str) -> str:
    """
    Classify sentence as simple/compound/complex/compound_complex.
    将句子分类为简单句/并列句/复杂句/复合复杂句。
    """
    text_lower = text.lower()
    words = text_lower.split()

    # Check for coordinating conjunctions (compound indicators)
    # 检查并列连词（并列句指示）
    has_coord = any(conj in [", and", ", but", ", or", ", yet", ", so"] for conj in [text_lower])
    coord_count = sum(1 for w in words if w in ["and", "but", "or", "yet", "so"])

    # Check for subordinate clauses
    # 检查从句
    has_subordinate = any(marker in text_lower for marker in SUBORDINATE_MARKERS)

    # Simple classification logic
    # 简单分类逻辑
    if has_subordinate and coord_count >= 1:
        return "compound_complex"
    elif has_subordinate:
        return "complex"
    elif coord_count >= 1 and ", " in text:
        return "compound"
    else:
        return "simple"


def _detect_voice(text: str) -> str:
    """
    Detect if sentence is active or passive voice.
    检测句子是主动语态还是被动语态。
    """
    text_lower = text.lower()
    words = text_lower.split()

    # Look for passive patterns: "was/were/is/are + past participle"
    # 查找被动模式
    for i, word in enumerate(words):
        if word in PASSIVE_INDICATORS:
            # Check if followed by a word ending in -ed or irregular past participle
            if i + 1 < len(words):
                next_word = words[i + 1]
                if next_word.endswith("ed") or next_word.endswith("en"):
                    return "passive"

    return "active"


def _get_opener_word(text: str) -> str:
    """
    Get the first word of a sentence.
    获取句子的第一个词。
    """
    words = text.split()
    return words[0] if words else ""


def _count_clause_depth(text: str) -> int:
    """
    Estimate the nesting depth of subordinate clauses.
    估计从句嵌套深度。
    """
    text_lower = text.lower()
    depth = 0
    for marker in SUBORDINATE_MARKERS:
        if marker in text_lower:
            depth += 1
    return min(depth, 4)  # Cap at 4


def _calculate_length_cv(lengths: List[int]) -> float:
    """
    Calculate coefficient of variation for sentence lengths.
    计算句子长度的变异系数。
    """
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    if mean == 0:
        return 0.0
    stdev = statistics.stdev(lengths)
    return stdev / mean


def _detect_explicit_connectors(text: str) -> List[Dict[str, Any]]:
    """
    Detect explicit connectors in text.
    检测文本中的显性连接词。
    """
    connectors_found = []
    for category, connectors in AI_CONNECTORS.items():
        for conn in connectors:
            if conn.lower() in text.lower():
                # Check if at start of sentence
                if text.strip().lower().startswith(conn.lower()):
                    position = "start"
                else:
                    position = "middle"
                connectors_found.append({
                    "connector": conn,
                    "type": category,
                    "position": position,
                })
    return connectors_found


def _calculate_risk_score(
    simple_ratio: float,
    length_cv: float,
    opener_repetition: float,
    connector_ratio: float
) -> int:
    """
    Calculate overall risk score based on AI detection metrics.
    根据AI检测指标计算总体风险分数。
    """
    score = 0

    # Simple sentence ratio (>60% is high risk)
    if simple_ratio > 0.7:
        score += 30
    elif simple_ratio > 0.6:
        score += 20
    elif simple_ratio > 0.5:
        score += 10

    # Length CV (<0.25 is high risk)
    if length_cv < 0.2:
        score += 30
    elif length_cv < 0.25:
        score += 20
    elif length_cv < 0.3:
        score += 10

    # Opener repetition (>30% is high risk)
    if opener_repetition > 0.4:
        score += 25
    elif opener_repetition > 0.3:
        score += 15
    elif opener_repetition > 0.2:
        score += 5

    # Connector ratio (>40% is high risk)
    if connector_ratio > 0.5:
        score += 20
    elif connector_ratio > 0.4:
        score += 15
    elif connector_ratio > 0.3:
        score += 10

    return min(score, 100)


def _get_risk_level(score: int) -> str:
    """
    Convert risk score to risk level.
    将风险分数转换为风险等级。
    """
    if score >= 60:
        return "high"
    elif score >= 30:
        return "medium"
    else:
        return "low"


def _identify_sentences_in_paragraph(para_text: str, para_idx: int) -> List[SentenceInfo]:
    """
    Identify and label all sentences in a paragraph.
    识别并标注段落中的所有句子。
    """
    sentences = []
    segments = _segmenter.segment(para_text)

    for i, seg in enumerate(segments):
        if not seg.should_process:
            continue

        text = seg.text
        word_count = len(text.split())
        sentence_type = _classify_sentence_type(text)
        voice = _detect_voice(text)
        opener = _get_opener_word(text)
        clause_depth = _count_clause_depth(text)
        has_subordinate = clause_depth > 0

        # Determine function role based on position
        # 根据位置确定功能角色
        if i == 0:
            function_role = "topic"
        elif i == len(segments) - 1:
            function_role = "conclusion"
        else:
            function_role = "body"

        sentences.append(SentenceInfo(
            index=len(sentences),
            text=text,
            paragraph_index=para_idx,
            word_count=word_count,
            sentence_type=sentence_type,
            function_role=function_role,
            has_subordinate=has_subordinate,
            clause_depth=clause_depth,
            voice=voice,
            opener_word=opener,
        ))

    return sentences


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


def _get_paragraphs(request: SentenceAnalysisRequest) -> list:
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
        layer=LayerLevel.SENTENCE,
        position=issue.position,
        suggestion=issue.suggestion,
        suggestion_zh=issue.suggestion_zh,
        details=issue.details,
    )


def _convert_sentence_context(ctx: Dict[str, Any]) -> SentenceWithContext:
    """Convert internal sentence context to API schema"""
    return SentenceWithContext(
        sentence_text=ctx.get("sentence_text", ""),
        sentence_index=ctx.get("sentence_idx", ctx.get("global_idx", 0)),
        paragraph_text=ctx.get("paragraph_text", ctx.get("para_text", "")),
        paragraph_index=ctx.get("paragraph_index", ctx.get("para_idx", 0)),
        paragraph_role=ctx.get("paragraph_role", ctx.get("para_role", "body")),
        position_in_paragraph=ctx.get("position_in_paragraph", ctx.get("position_in_para", 0)),
        is_first=ctx.get("is_first_sentence", ctx.get("is_first_in_para", False)),
        is_last=ctx.get("is_last_sentence", ctx.get("is_last_in_para", False)),
        previous_sentence=ctx.get("previous_sentence", ctx.get("prev_sentence")),
        next_sentence=ctx.get("next_sentence"),
        sentence_role=ctx.get("sentence_role", "unknown"),
        has_issues=ctx.get("has_issues", False),
        issue_types=ctx.get("issue_types", []),
    )


@router.post("/pattern", response_model=SentenceAnalysisResponse)
async def analyze_sentence_patterns(request: SentenceAnalysisRequest):
    """
    Step 4.1: Sentence Pattern Detection
    步骤 4.1：句式模式检测

    Detects repetitive sentence structures WITHIN paragraph context:
    - Repetitive sentence beginnings
    - Sentence length distribution per paragraph
    - Calculates burstiness score

    **Context**: Receives paragraph boundaries and role info from Layer 3
    """
    start_time = time.time()

    try:
        orchestrator = SentenceOrchestrator()

        # Create context with paragraphs (CRITICAL: must have paragraph context)
        context = LayerContext(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles or [],
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract pattern-specific details
        pattern_details = result.details.get("patterns", {})
        polish_context = result.details.get("polish_context", {})
        sentences_ctx = polish_context.get("sentences_with_context", [])

        return SentenceAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "pattern" in i.type or "repetitive" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=pattern_details,
            processing_time_ms=processing_time_ms,
            sentence_count=result.details.get("total_sentences", 0),
            sentences_with_context=[_convert_sentence_context(s) for s in sentences_ctx],
            sentence_roles=result.updated_context.sentence_roles or [],
            void_patterns=[],
            pattern_issues=[{"paragraph": str(k), **(v if isinstance(v, dict) else {"value": v})} for k, v in pattern_details.get("paragraph_patterns", {}).items()] if pattern_details.get("paragraph_patterns") else [],
        )

    except Exception as e:
        logger.error(f"Sentence pattern analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/void", response_model=SentenceAnalysisResponse)
async def analyze_syntactic_voids(request: SentenceAnalysisRequest):
    """
    Step 4.2: Syntactic Void Detection
    步骤 4.2：句法空洞检测

    Integrates syntactic_void.py (spaCy en_core_web_md).
    Detects 7 void pattern types:
    - Hollow constructions
    - Empty elaborations
    - Redundant qualifiers

    **Context**: Consider sentence position in paragraph for severity weighting
    """
    start_time = time.time()

    try:
        orchestrator = SentenceOrchestrator()

        # Create context with paragraphs (CRITICAL: must have paragraph context)
        context = LayerContext(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles or [],
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract void-specific details
        void_details = result.details.get("syntactic_voids", {})
        polish_context = result.details.get("polish_context", {})
        sentences_ctx = polish_context.get("sentences_with_context", [])

        # Build void patterns list
        void_patterns = []
        for v_type, count in void_details.get("voids_by_type", {}).items():
            void_patterns.append({
                "type": v_type,
                "count": count,
            })

        return SentenceAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "void" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=void_details,
            processing_time_ms=processing_time_ms,
            sentence_count=result.details.get("total_sentences", 0),
            sentences_with_context=[_convert_sentence_context(s) for s in sentences_ctx],
            sentence_roles=result.updated_context.sentence_roles or [],
            void_patterns=void_patterns,
            pattern_issues=[],
        )

    except Exception as e:
        logger.error(f"Syntactic void analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/role", response_model=SentenceAnalysisResponse)
async def analyze_sentence_roles(request: SentenceAnalysisRequest):
    """
    Step 4.3: Sentence Role Classification
    步骤 4.3：句子角色分类

    Classifies each sentence into 10 roles:
    - CLAIM, EVIDENCE, ANALYSIS, CRITIQUE, CONCESSION
    - SYNTHESIS, TRANSITION, CONTEXT, IMPLICATION, ELABORATION

    **Context**: Role classification depends on surrounding sentences in paragraph
    """
    start_time = time.time()

    try:
        orchestrator = SentenceOrchestrator()

        # Create context with paragraphs (CRITICAL: must have paragraph context)
        context = LayerContext(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles or [],
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract role-specific details
        role_details = result.details.get("sentence_roles", {})
        polish_context = result.details.get("polish_context", {})
        sentences_ctx = polish_context.get("sentences_with_context", [])

        return SentenceAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "role" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=role_details,
            processing_time_ms=processing_time_ms,
            sentence_count=result.details.get("total_sentences", 0),
            sentences_with_context=[_convert_sentence_context(s) for s in sentences_ctx],
            sentence_roles=result.updated_context.sentence_roles or [],
            void_patterns=[],
            pattern_issues=[],
        )

    except Exception as e:
        logger.error(f"Sentence role analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/polish-context", response_model=SentenceAnalysisResponse)
async def get_polish_context(request: SentenceAnalysisRequest):
    """
    Step 4.4: Sentence Polish Context
    步骤 4.4：句子润色上下文

    **CONTEXT-CRITICAL**: Returns all context needed for sentence rewriting.

    Rewriting prompts MUST include:
    - Full paragraph text for context
    - Sentence role in paragraph
    - Previous/next sentence for coherence
    - Paragraph's role in section

    Use this endpoint to get context for interactive (Intervention)
    or batch (Yolo) sentence polishing.
    """
    start_time = time.time()

    try:
        orchestrator = SentenceOrchestrator()

        # Create context with paragraphs (CRITICAL: must have paragraph context)
        context = LayerContext(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles or [],
        )

        # Run analysis to get full context
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract polish context (this is the key output)
        polish_context = result.details.get("polish_context", {})
        sentences_ctx = polish_context.get("sentences_with_context", [])

        return SentenceAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=polish_context,
            processing_time_ms=processing_time_ms,
            sentence_count=len(sentences_ctx),
            sentences_with_context=[_convert_sentence_context(s) for s in sentences_ctx],
            sentence_roles=result.updated_context.sentence_roles or [],
            void_patterns=[],
            pattern_issues=[],
        )

    except Exception as e:
        logger.error(f"Polish context extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=SentenceAnalysisResponse)
async def analyze_sentence(request: SentenceAnalysisRequest):
    """
    Combined Sentence Analysis (Layer 2)
    综合句子分析（第2层）

    **IMPORTANT**: All analysis performed within paragraph context.

    Runs all sentence-level analysis steps:
    - Step 4.1: Sentence Pattern Detection
    - Step 4.2: Syntactic Void Detection
    - Step 4.3: Sentence Role Classification
    - Step 4.4: Sentence Polish Context Preparation

    Returns complete sentence-level analysis results with full paragraph
    context for each sentence.
    """
    start_time = time.time()

    try:
        orchestrator = SentenceOrchestrator()

        # Create context with paragraphs and optional paragraph context from Layer 3
        context = LayerContext(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles or [],
        )

        # Apply Layer 3 context if provided
        if request.paragraph_context:
            context.paragraph_coherence = request.paragraph_context.get("paragraph_coherence", [])
            context.paragraph_anchor_density = request.paragraph_context.get("paragraph_anchor_density", [])

        # Run full analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract all details
        polish_context = result.details.get("polish_context", {})
        sentences_ctx = polish_context.get("sentences_with_context", [])
        void_details = result.details.get("syntactic_voids", {})

        # Build void patterns list
        void_patterns = []
        for v_type, count in void_details.get("voids_by_type", {}).items():
            void_patterns.append({
                "type": v_type,
                "count": count,
            })

        return SentenceAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=result.details,
            processing_time_ms=processing_time_ms,
            sentence_count=result.details.get("total_sentences", 0),
            sentences_with_context=[_convert_sentence_context(s) for s in sentences_ctx],
            sentence_roles=result.updated_context.sentence_roles or [],
            void_patterns=void_patterns,
            pattern_issues=[{"paragraph": str(k), **(v if isinstance(v, dict) else {"value": v})} for k, v in result.details.get("patterns", {}).get("paragraph_patterns", {}).items()] if result.details.get("patterns", {}).get("paragraph_patterns") else [],
        )

    except Exception as e:
        logger.error(f"Sentence analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rewrite-context", response_model=RewriteContextResponse)
async def get_rewrite_context(request: RewriteContextRequest):
    """
    Get Rewrite Context for a Specific Sentence
    获取特定句子的改写上下文

    **CONTEXT-CRITICAL**: Returns formatted context for rewriting prompts.

    This is the primary method for getting context when generating rewrite prompts.
    The returned context MUST be included in rewriting prompts for accurate
    context-aware sentence rewriting.

    Used by:
    - Intervention mode (user confirms each rewrite)
    - Yolo mode (batch auto rewriting)
    """
    try:
        # Create sentence context provider
        provider = SentenceContextProvider(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles,
            sentence_roles=request.sentence_roles,
        )

        # Get context for the specific sentence
        rewrite_ctx = provider.get_rewrite_prompt_context(request.sentence_index)

        if not rewrite_ctx:
            raise HTTPException(
                status_code=404,
                detail=f"Sentence index {request.sentence_index} not found"
            )

        sentence = provider.get_sentence_with_context(request.sentence_index)

        return RewriteContextResponse(
            original_sentence=rewrite_ctx["original_sentence"],
            full_paragraph=rewrite_ctx["full_paragraph"],
            paragraph_role=rewrite_ctx["paragraph_role"],
            sentence_role=rewrite_ctx["sentence_role"],
            position_info=rewrite_ctx["position_in_paragraph"],
            is_first_sentence=rewrite_ctx["is_first_sentence"],
            is_last_sentence=rewrite_ctx["is_last_sentence"],
            previous_sentence=rewrite_ctx["previous_sentence"] if rewrite_ctx["previous_sentence"] != "[None - this is the first sentence]" else None,
            next_sentence=rewrite_ctx["next_sentence"] if rewrite_ctx["next_sentence"] != "[None - this is the last sentence]" else None,
            issues_to_fix=rewrite_ctx["issues_to_fix"],
            section_role=rewrite_ctx["section_role"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rewrite context extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context")
async def get_sentence_context(request: SentenceAnalysisRequest):
    """
    Get sentence context for passing to lexical layer
    获取句子上下文以传递给词汇层

    Returns the updated LayerContext that can be used
    to initialize lexical-level analysis.
    """
    try:
        orchestrator = SentenceOrchestrator()

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=_get_paragraphs(request),
            paragraph_roles=request.paragraph_roles or [],
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Return the updated context as dict for lexical layer
        return {
            "sentences": result.updated_context.sentences,
            "sentence_roles": result.updated_context.sentence_roles,
            "sentence_to_paragraph": result.updated_context.sentence_to_paragraph,
        }

    except Exception as e:
        logger.error(f"Sentence context extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# New Sub-Step Endpoints for Layer 2 (Step 4.0 - 4.5)
# Layer 2 新子步骤端点（步骤 4.0 - 4.5）
# ============================================================================

@router.post("/step4-0/identify", response_model=SentenceIdentificationResponse)
async def identify_sentences(request: SentenceIdentificationRequest):
    """
    Step 4.0: Sentence Identification & Labeling
    步骤 4.0：句子识别与标注

    Identifies all sentences in the document and labels each with:
    - Sentence type (simple/compound/complex/compound_complex)
    - Function role (topic/evidence/analysis/transition/conclusion)
    - Voice (active/passive)
    - Opener word
    - Clause depth

    This is the foundation step for Layer 2 processing.
    这是Layer 2处理的基础步骤。
    """
    start_time = time.time()

    try:
        # Get paragraphs from request
        # 从请求获取段落
        if request.paragraphs:
            paragraphs = request.paragraphs
        elif request.text:
            paragraphs = _split_text_to_paragraphs(request.text)
        else:
            raise HTTPException(status_code=400, detail="Either 'text' or 'paragraphs' must be provided")

        # Identify sentences in each paragraph
        # 识别每个段落中的句子
        all_sentences: List[SentenceInfo] = []
        paragraph_sentence_map: Dict[int, List[int]] = {}
        type_distribution: Dict[str, int] = {"simple": 0, "compound": 0, "complex": 0, "compound_complex": 0}

        global_idx = 0
        for para_idx, para_text in enumerate(paragraphs):
            para_sentences = _identify_sentences_in_paragraph(para_text, para_idx)
            sentence_indices = []

            for sent in para_sentences:
                sent.index = global_idx
                all_sentences.append(sent)
                sentence_indices.append(global_idx)
                type_distribution[sent.sentence_type] = type_distribution.get(sent.sentence_type, 0) + 1
                global_idx += 1

            paragraph_sentence_map[para_idx] = sentence_indices

        # Calculate metrics and risk
        # 计算指标和风险
        total_sentences = len(all_sentences)
        simple_count = type_distribution.get("simple", 0)
        simple_ratio = simple_count / total_sentences if total_sentences > 0 else 0

        # Calculate opener repetition
        # 计算句首词重复率
        opener_counts: Dict[str, int] = {}
        for sent in all_sentences:
            opener = sent.opener_word.lower()
            opener_counts[opener] = opener_counts.get(opener, 0) + 1
        max_opener_count = max(opener_counts.values()) if opener_counts else 0
        opener_repetition = max_opener_count / total_sentences if total_sentences > 0 else 0

        # Calculate risk score
        # 计算风险分数
        lengths = [sent.word_count for sent in all_sentences]
        length_cv = _calculate_length_cv(lengths)
        risk_score = _calculate_risk_score(simple_ratio, length_cv, opener_repetition, 0)
        risk_level = _get_risk_level(risk_score)

        # Generate issues
        # 生成问题列表
        issues = []
        if simple_ratio > 0.6:
            issues.append({
                "type": "high_simple_ratio",
                "description": f"Simple sentence ratio ({simple_ratio:.0%}) exceeds 60% threshold",
                "description_zh": f"简单句比例（{simple_ratio:.0%}）超过60%阈值",
                "severity": "high",
            })
        if opener_repetition > 0.3:
            issues.append({
                "type": "opener_repetition",
                "description": f"Sentence opener repetition ({opener_repetition:.0%}) exceeds 30% threshold",
                "description_zh": f"句首词重复率（{opener_repetition:.0%}）超过30%阈值",
                "severity": "high",
            })

        # Generate recommendations
        # 生成建议
        recommendations = []
        recommendations_zh = []
        if simple_ratio > 0.6:
            recommendations.append("Consider merging simple sentences into complex sentences with subordinate clauses")
            recommendations_zh.append("建议将简单句合并为带从句的复杂句")
        if opener_repetition > 0.3:
            recommendations.append("Vary sentence openers to improve diversity")
            recommendations_zh.append("变换句首词以提高多样性")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SentenceIdentificationResponse(
            sentences=all_sentences,
            sentence_count=total_sentences,
            paragraph_sentence_map=paragraph_sentence_map,
            type_distribution=type_distribution,
            risk_level=risk_level,
            risk_score=risk_score,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sentence identification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step4-1/pattern", response_model=PatternAnalysisResponse)
async def analyze_patterns(request: PatternAnalysisRequest):
    """
    Step 4.1: Sentence Pattern Analysis
    步骤 4.1：句式结构分析

    Analyzes sentence patterns across the document:
    - Sentence type distribution (simple/compound/complex/compound_complex)
    - Sentence opener analysis (repetition, subject-first ratio)
    - Voice distribution (active/passive)
    - Clause depth statistics
    - Identifies high-risk paragraphs for processing

    分析全文的句式模式：
    - 句式类型分布
    - 句首词分析
    - 语态分布
    - 从句深度统计
    - 识别需要处理的高风险段落
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
            raise HTTPException(status_code=400, detail="Either 'text' or 'paragraphs' must be provided")

        # Collect all sentences
        # 收集所有句子
        all_sentences: List[SentenceInfo] = []
        para_sentence_map: Dict[int, List[SentenceInfo]] = {}

        for para_idx, para_text in enumerate(paragraphs):
            para_sentences = _identify_sentences_in_paragraph(para_text, para_idx)
            para_sentence_map[para_idx] = para_sentences
            all_sentences.extend(para_sentences)

        total_sentences = len(all_sentences)
        if total_sentences == 0:
            raise HTTPException(status_code=400, detail="No sentences found in text")

        # Calculate type distribution
        # 计算句式类型分布
        type_counts: Dict[str, int] = {"simple": 0, "compound": 0, "complex": 0, "compound_complex": 0}
        for sent in all_sentences:
            type_counts[sent.sentence_type] = type_counts.get(sent.sentence_type, 0) + 1

        type_distribution = {}
        thresholds = {"simple": 0.6, "compound": 0.15, "complex": 0.2, "compound_complex": 0.1}
        for stype, count in type_counts.items():
            pct = count / total_sentences
            is_risk = (stype == "simple" and pct > thresholds["simple"]) or \
                      (stype != "simple" and pct < thresholds[stype])
            type_distribution[stype] = TypeStats(
                count=count,
                percentage=pct,
                is_risk=is_risk,
                threshold=thresholds[stype],
            )

        # Analyze openers
        # 分析句首词
        opener_counts: Dict[str, int] = {}
        subject_opening_count = 0
        for sent in all_sentences:
            opener = sent.opener_word
            opener_counts[opener] = opener_counts.get(opener, 0) + 1
            if opener in SUBJECT_OPENERS:
                subject_opening_count += 1

        sorted_openers = sorted(opener_counts.items(), key=lambda x: -x[1])
        top_repeated = [o[0] for o in sorted_openers[:5]]
        max_opener_count = sorted_openers[0][1] if sorted_openers else 0
        repetition_rate = max_opener_count / total_sentences if total_sentences > 0 else 0
        subject_opening_rate = subject_opening_count / total_sentences if total_sentences > 0 else 0

        opener_issues = []
        if repetition_rate > 0.3:
            opener_issues.append(f"High opener repetition: '{top_repeated[0]}' used {max_opener_count} times ({repetition_rate:.0%})")
        if subject_opening_rate > 0.8:
            opener_issues.append(f"Subject-first opening rate ({subject_opening_rate:.0%}) exceeds 80%")

        opener_analysis = OpenerAnalysis(
            opener_counts=opener_counts,
            top_repeated=top_repeated,
            repetition_rate=repetition_rate,
            subject_opening_rate=subject_opening_rate,
            issues=opener_issues,
        )

        # Analyze voice distribution
        # 分析语态分布
        voice_counts = {"active": 0, "passive": 0}
        for sent in all_sentences:
            voice_counts[sent.voice] = voice_counts.get(sent.voice, 0) + 1

        # Analyze clause depth
        # 分析从句深度
        depths = [sent.clause_depth for sent in all_sentences]
        clause_depth_stats = {
            "mean": sum(depths) / len(depths) if depths else 0,
            "max": max(depths) if depths else 0,
            "min": min(depths) if depths else 0,
        }

        # Count parallel structures (simplified: count sentences with similar structure)
        # 计算平行结构（简化版）
        parallel_count = 0

        # Identify high-risk paragraphs
        # 识别高风险段落
        high_risk_paragraphs = []
        for para_idx, para_sents in para_sentence_map.items():
            if not para_sents:
                continue
            para_simple_count = sum(1 for s in para_sents if s.sentence_type == "simple")
            para_simple_ratio = para_simple_count / len(para_sents)

            lengths = [s.word_count for s in para_sents]
            para_length_cv = _calculate_length_cv(lengths)

            para_openers = [s.opener_word for s in para_sents]
            para_opener_counts = {}
            for o in para_openers:
                para_opener_counts[o] = para_opener_counts.get(o, 0) + 1
            para_max_opener = max(para_opener_counts.values()) if para_opener_counts else 0
            para_opener_rep = para_max_opener / len(para_sents)

            para_risk_score = _calculate_risk_score(para_simple_ratio, para_length_cv, para_opener_rep, 0)
            para_risk_level = _get_risk_level(para_risk_score)

            if para_risk_level in ["high", "medium"]:
                high_risk_paragraphs.append({
                    "paragraph_index": para_idx,
                    "risk_score": para_risk_score,
                    "risk_level": para_risk_level,
                    "simple_ratio": para_simple_ratio,
                    "length_cv": para_length_cv,
                    "opener_repetition": para_opener_rep,
                    "sentence_count": len(para_sents),
                })

        # Calculate overall risk
        # 计算总体风险
        simple_ratio = type_counts.get("simple", 0) / total_sentences
        lengths = [s.word_count for s in all_sentences]
        length_cv = _calculate_length_cv(lengths)
        risk_score = _calculate_risk_score(simple_ratio, length_cv, repetition_rate, 0)
        risk_level = _get_risk_level(risk_score)

        # Generate issues
        # 生成问题列表
        issues = []
        if simple_ratio > 0.6:
            issues.append({
                "type": "high_simple_ratio",
                "description": f"Simple sentence ratio ({simple_ratio:.0%}) exceeds 60%",
                "severity": "high",
            })
        if repetition_rate > 0.3:
            issues.append({
                "type": "opener_repetition",
                "description": f"Opener repetition rate ({repetition_rate:.0%}) exceeds 30%",
                "severity": "high",
            })
        if voice_counts["passive"] / total_sentences < 0.1:
            issues.append({
                "type": "low_passive_ratio",
                "description": f"Passive voice ratio ({voice_counts['passive']/total_sentences:.0%}) is below 10%",
                "severity": "medium",
            })

        # Recommendations
        # 建议
        recommendations = []
        recommendations_zh = []
        if simple_ratio > 0.6:
            recommendations.append("Merge simple sentences into complex sentences to increase variety")
            recommendations_zh.append("将简单句合并为复杂句以增加多样性")
        if repetition_rate > 0.3:
            recommendations.append("Use varied sentence openers (adverbs, participles, prepositional phrases)")
            recommendations_zh.append("使用多样化的句首（副词、分词、介词短语）")
        if voice_counts["passive"] / total_sentences < 0.1:
            recommendations.append("Add passive voice constructions for better balance (target: 15-30%)")
            recommendations_zh.append("增加被动语态以获得更好的平衡（目标：15-30%）")

        # Syntactic Void Detection Integration
        # 句法空洞检测集成
        syntactic_voids = []
        void_score = 0
        void_density = 0.0
        has_critical_void = False

        if VOID_DETECTOR_AVAILABLE and request.text:
            try:
                # Run syntactic void detection (using fast regex mode, spaCy optional)
                # 运行句法空洞检测（使用快速正则模式，spaCy可选）
                void_result: SyntacticVoidResult = detect_syntactic_voids(request.text, use_spacy=False)

                # Convert VoidMatch objects to dicts for JSON serialization
                # 将 VoidMatch 对象转换为 dict 以便 JSON 序列化
                for match in void_result.matches:
                    syntactic_voids.append({
                        "pattern_type": match.pattern_type.value if hasattr(match.pattern_type, 'value') else str(match.pattern_type),
                        "matched_text": match.matched_text,
                        "position": match.position,
                        "end_position": match.end_position,
                        "severity": match.severity,
                        "abstract_words": match.abstract_words,
                        "suggestion": match.suggestion,
                        "suggestion_zh": match.suggestion_zh
                    })

                void_score = void_result.void_score
                void_density = round(void_result.void_density, 3)
                has_critical_void = void_result.has_critical_void

                logger.info(f"Syntactic Void Analysis: score={void_score}, matches={len(syntactic_voids)}, critical={has_critical_void}")

                # Add void-related risk to overall score
                # 将空洞相关风险添加到总体分数
                if has_critical_void:
                    risk_score = min(100, risk_score + 25)
                    issues.append({
                        "type": "syntactic_void_critical",
                        "description": f"Critical syntactic voids detected ({len(syntactic_voids)} patterns)",
                        "description_zh": f"检测到严重句法空洞（{len(syntactic_voids)} 个模式）",
                        "severity": "critical",
                    })
                    recommendations.append("Remove or rewrite flowery empty phrases with concrete, specific language.")
                    recommendations_zh.append("删除或改写华丽空洞的短语，使用具体、明确的语言。")
                elif void_score > 30:
                    risk_score = min(100, risk_score + 15)
                    issues.append({
                        "type": "syntactic_void_moderate",
                        "description": f"Moderate syntactic voids detected (score: {void_score})",
                        "description_zh": f"检测到中等句法空洞（分数：{void_score}）",
                        "severity": "medium",
                    })

                # Recalculate risk level after void integration
                # 在集成空洞检测后重新计算风险级别
                risk_level = _get_risk_level(risk_score)

            except Exception as e:
                logger.warning(f"Syntactic void detection failed: {e}")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return PatternAnalysisResponse(
            type_distribution=type_distribution,
            opener_analysis=opener_analysis,
            voice_distribution=voice_counts,
            clause_depth_stats=clause_depth_stats,
            parallel_structure_count=parallel_count,
            issues=issues,
            risk_level=risk_level,
            risk_score=risk_score,
            high_risk_paragraphs=high_risk_paragraphs,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms,
            # Syntactic Void Detection Results
            # 句法空洞检测结果
            syntactic_voids=syntactic_voids,
            void_score=void_score,
            void_density=void_density,
            has_critical_void=has_critical_void,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pattern analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step4-2/length", response_model=LengthAnalysisResponse)
async def analyze_length(request: LengthAnalysisRequest):
    """
    Step 4.2: In-Paragraph Length Analysis
    步骤 4.2：段内句长分析

    Analyzes sentence length distribution within each paragraph:
    - Calculates length CV (coefficient of variation) per paragraph
    - Identifies uniformity issues (CV < 0.25)
    - Suggests merge candidates (short adjacent sentences)
    - Suggests split candidates (overly long sentences)

    分析每个段落内的句长分布：
    - 计算每段的句长变异系数
    - 识别句长均匀性问题
    - 建议合并候选（相邻短句）
    - 建议拆分候选（过长句子）
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
            raise HTTPException(status_code=400, detail="Either 'text' or 'paragraphs' must be provided")

        # If specific paragraph requested, filter
        # 如果请求特定段落，则过滤
        if request.paragraph_index is not None:
            if request.paragraph_index >= len(paragraphs):
                raise HTTPException(status_code=400, detail=f"Paragraph index {request.paragraph_index} out of range")
            paragraphs = {request.paragraph_index: paragraphs[request.paragraph_index]}
        else:
            paragraphs = {i: p for i, p in enumerate(paragraphs)}

        # Analyze each paragraph
        # 分析每个段落
        paragraph_stats = []
        all_lengths = []
        uniformity_issues = []
        merge_candidates = []
        split_candidates = []

        for para_idx, para_text in paragraphs.items():
            sentences = _identify_sentences_in_paragraph(para_text, para_idx)
            if not sentences:
                continue

            lengths = [s.word_count for s in sentences]
            all_lengths.extend(lengths)
            length_cv = _calculate_length_cv(lengths)
            min_length = min(lengths)
            max_length = max(lengths)
            avg_length = sum(lengths) / len(lengths)

            para_stat = {
                "paragraph_index": para_idx,
                "sentence_count": len(sentences),
                "length_cv": round(length_cv, 3),
                "min_length": min_length,
                "max_length": max_length,
                "avg_length": round(avg_length, 1),
                "lengths": lengths,
            }
            paragraph_stats.append(para_stat)

            # Check for uniformity issues
            # 检查句长均匀性问题
            if length_cv < 0.25:
                uniformity_issues.append({
                    "paragraph_index": para_idx,
                    "length_cv": round(length_cv, 3),
                    "issue": "Length CV below 0.25 threshold - sentences too uniform",
                    "issue_zh": "句长变异系数低于0.25阈值 - 句子长度过于均匀",
                })

            # Find merge candidates (adjacent short sentences)
            # 查找合并候选（相邻短句）
            for i in range(len(sentences) - 1):
                if sentences[i].word_count <= 15 and sentences[i + 1].word_count <= 15:
                    merge_candidates.append({
                        "paragraph_index": para_idx,
                        "sentence_indices": [sentences[i].index, sentences[i + 1].index],
                        "sentences": [sentences[i].text, sentences[i + 1].text],
                        "combined_length": sentences[i].word_count + sentences[i + 1].word_count,
                        "reason": "Adjacent short sentences can be merged for complexity",
                        "reason_zh": "相邻短句可以合并以增加复杂度",
                    })

            # Find split candidates (overly long sentences)
            # 查找拆分候选（过长句子）
            for sent in sentences:
                if sent.word_count > 40:
                    split_candidates.append({
                        "paragraph_index": para_idx,
                        "sentence_index": sent.index,
                        "sentence": sent.text,
                        "word_count": sent.word_count,
                        "reason": "Sentence exceeds 40 words - consider splitting",
                        "reason_zh": "句子超过40词 - 建议拆分",
                    })

        # Calculate overall CV
        # 计算总体变异系数
        overall_cv = _calculate_length_cv(all_lengths) if all_lengths else 0

        # Calculate risk
        # 计算风险
        risk_score = 0
        if overall_cv < 0.2:
            risk_score += 40
        elif overall_cv < 0.25:
            risk_score += 25

        if len(uniformity_issues) > len(paragraphs) * 0.5:
            risk_score += 30

        risk_level = _get_risk_level(risk_score)

        # Recommendations
        # 建议
        recommendations = []
        recommendations_zh = []
        if overall_cv < 0.25:
            recommendations.append("Overall sentence length CV is too low - add variety through merging short sentences and splitting long ones")
            recommendations_zh.append("总体句长变异系数过低 - 通过合并短句和拆分长句增加变化")
        if merge_candidates:
            recommendations.append(f"Found {len(merge_candidates)} merge candidates - consider combining adjacent short sentences")
            recommendations_zh.append(f"发现{len(merge_candidates)}个合并候选 - 建议合并相邻短句")
        if split_candidates:
            recommendations.append(f"Found {len(split_candidates)} overly long sentences - consider splitting for readability")
            recommendations_zh.append(f"发现{len(split_candidates)}个过长句子 - 建议拆分以提高可读性")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return LengthAnalysisResponse(
            paragraph_length_stats=paragraph_stats,
            overall_length_cv=round(overall_cv, 3),
            uniformity_issues=uniformity_issues,
            merge_candidates=merge_candidates,
            split_candidates=split_candidates,
            risk_level=risk_level,
            risk_score=risk_score,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Length analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step4-3/merge", response_model=MergeSuggestionResponse)
async def suggest_merges(request: MergeSuggestionRequest):
    """
    Step 4.3: Sentence Merger Suggestions
    步骤 4.3：句子合并建议

    Generates merge suggestions for a specific paragraph:
    - Identifies semantically related adjacent sentences
    - Generates nested clause merge previews
    - Evaluates readability and complexity gain

    为特定段落生成合并建议：
    - 识别语义相关的相邻句子
    - 生成嵌套从句合并预览
    - 评估可读性和复杂度提升
    """
    start_time = time.time()

    try:
        para_text = request.paragraph_text
        para_idx = request.paragraph_index
        max_merge = request.max_merge_count

        # Get sentences in paragraph
        # 获取段落中的句子
        sentences = _identify_sentences_in_paragraph(para_text, para_idx)

        if len(sentences) < 2:
            return MergeSuggestionResponse(
                paragraph_index=para_idx,
                candidates=[],
                estimated_improvement={},
                risk_level="low",
                recommendations=["Paragraph has fewer than 2 sentences - no merge needed"],
                recommendations_zh=["段落少于2个句子 - 无需合并"],
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        # Find merge candidates
        # 查找合并候选
        candidates = []
        merge_types = {
            "causal": ["because", "since", "as", "so"],
            "contrast": ["although", "while", "whereas", "but"],
            "temporal": ["when", "after", "before", "while"],
            "addition": ["which", "that", "who"],
        }

        for i in range(len(sentences) - 1):
            s1 = sentences[i]
            s2 = sentences[i + 1]

            # Only consider short sentences for merging
            # 只考虑短句进行合并
            if s1.word_count > 20 or s2.word_count > 20:
                continue

            # Determine merge type based on content
            # 根据内容确定合并类型
            merge_type = "addition"  # Default
            s2_lower = s2.text.lower()
            for mtype, keywords in merge_types.items():
                if any(kw in s2_lower for kw in keywords):
                    merge_type = mtype
                    break

            # Generate simple merged text (this would be enhanced with LLM)
            # 生成简单的合并文本（实际应使用LLM增强）
            if merge_type == "causal":
                merged = f"{s1.text[:-1]}, which leads to the finding that {s2.text.lower()}"
            elif merge_type == "contrast":
                merged = f"Although {s1.text.lower()[:-1]}, {s2.text.lower()}"
            elif merge_type == "temporal":
                merged = f"After {s1.text.lower()[:-1]}, {s2.text.lower()}"
            else:
                merged = f"{s1.text[:-1]}, and {s2.text.lower()}"

            word_count_after = len(merged.split())

            candidate = MergeCandidate(
                sentence_indices=[i, i + 1],
                original_sentences=[s1.text, s2.text],
                merged_text=merged,
                merge_type=merge_type,
                similarity_score=0.75,  # Placeholder
                readability_score=0.85,  # Placeholder
                word_count_before=s1.word_count + s2.word_count,
                word_count_after=word_count_after,
                complexity_gain=f"{s1.sentence_type}+{s2.sentence_type}->complex",
            )
            candidates.append(candidate)

            if len(candidates) >= max_merge * 2:
                break

        # Estimate improvement
        # 估算改进效果
        estimated_improvement = {}
        if candidates:
            simple_reduction = len([c for c in candidates if "simple" in c.complexity_gain]) / len(sentences)
            estimated_improvement = {
                "simple_ratio_reduction": round(simple_reduction, 2),
                "length_cv_increase": 0.08,  # Estimate
                "complexity_increase": len(candidates) / len(sentences),
            }

        processing_time_ms = int((time.time() - start_time) * 1000)

        return MergeSuggestionResponse(
            paragraph_index=para_idx,
            candidates=candidates,
            estimated_improvement=estimated_improvement,
            risk_level="low" if candidates else "medium",
            recommendations=["Review and apply merge suggestions to increase sentence complexity"],
            recommendations_zh=["审核并应用合并建议以增加句子复杂度"],
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        logger.error(f"Merge suggestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step4-4/connector", response_model=ConnectorOptimizationResponse)
async def optimize_connectors(request: ConnectorOptimizationRequest):
    """
    Step 4.4: Inter-Sentence Connector Optimization
    步骤 4.4：句间连接词优化

    Analyzes and optimizes explicit connectors in a paragraph:
    - Detects AI-style explicit connectors (Furthermore, Moreover, etc.)
    - Suggests implicit alternatives (semantic echo, removal, subordination)
    - Preserves user-specified connectors

    分析并优化段落中的显性连接词：
    - 检测AI风格显性连接词
    - 建议隐性替代方案
    - 保留用户指定的连接词
    """
    start_time = time.time()

    try:
        para_text = request.paragraph_text
        para_idx = request.paragraph_index
        preserve = set(c.lower() for c in request.preserve_connectors)

        # Get sentences
        # 获取句子
        sentences = _identify_sentences_in_paragraph(para_text, para_idx)

        # Find connectors
        # 查找连接词
        connector_issues = []
        connector_type_dist: Dict[str, int] = {}
        total_connectors = 0

        for i, sent in enumerate(sentences):
            connectors = _detect_explicit_connectors(sent.text)
            for conn_info in connectors:
                conn = conn_info["connector"]
                conn_type = conn_info["type"]

                if conn.lower() in preserve:
                    continue

                connector_type_dist[conn_type] = connector_type_dist.get(conn_type, 0) + 1
                total_connectors += 1

                risk = "high" if conn_type in ["addition", "sequence", "summary"] else "medium"

                connector_issues.append(ConnectorIssue(
                    sentence_index=i,
                    connector=conn,
                    connector_type=conn_type,
                    position=conn_info["position"],
                    risk_level=risk,
                    context=sent.text[:100] + "..." if len(sent.text) > 100 else sent.text,
                ))

        # Calculate explicit ratio
        # 计算显性连接词比例
        explicit_ratio = total_connectors / len(sentences) if sentences else 0

        # Generate replacement suggestions
        # 生成替换建议
        suggestions = []
        for issue in connector_issues:
            if issue.connector_type == "addition":
                suggestions.append(ReplacementSuggestion(
                    original_connector=issue.connector,
                    sentence_index=issue.sentence_index,
                    replacement_type="remove",
                    new_text=f"[Remove '{issue.connector}' and use semantic echo instead]",
                    explanation=f"Remove '{issue.connector}' - let content flow naturally",
                    explanation_zh=f"删除'{issue.connector}' - 让内容自然衔接",
                ))
            elif issue.connector_type == "causal":
                suggestions.append(ReplacementSuggestion(
                    original_connector=issue.connector,
                    sentence_index=issue.sentence_index,
                    replacement_type="subordinate",
                    new_text=f"[Convert to subordinate clause: 'Given that...' or 'Since...']",
                    explanation=f"Replace '{issue.connector}' with subordinate clause construction",
                    explanation_zh=f"用从句结构替换'{issue.connector}'",
                ))
            elif issue.connector_type == "contrast":
                suggestions.append(ReplacementSuggestion(
                    original_connector=issue.connector,
                    sentence_index=issue.sentence_index,
                    replacement_type="subordinate",
                    new_text=f"[Convert to 'Although...' or 'While...' clause]",
                    explanation=f"Replace '{issue.connector}' with contrast subordinate clause",
                    explanation_zh=f"用对比从句替换'{issue.connector}'",
                ))

        # Risk assessment
        # 风险评估
        risk_score = 0
        if explicit_ratio > 0.5:
            risk_score = 80
        elif explicit_ratio > 0.4:
            risk_score = 60
        elif explicit_ratio > 0.3:
            risk_score = 40

        risk_level = _get_risk_level(risk_score)

        # Recommendations
        # 建议
        recommendations = []
        recommendations_zh = []
        if explicit_ratio > 0.25:
            recommendations.append(f"Explicit connector ratio ({explicit_ratio:.0%}) exceeds 25% - reduce for more natural flow")
            recommendations_zh.append(f"显性连接词比例（{explicit_ratio:.0%}）超过25% - 建议减少以实现更自然的衔接")
        if connector_type_dist.get("addition", 0) > 2:
            recommendations.append("Too many addition connectors (Furthermore, Moreover) - use semantic linking instead")
            recommendations_zh.append("递进连接词过多 - 建议使用语义关联替代")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ConnectorOptimizationResponse(
            paragraph_index=para_idx,
            connector_issues=connector_issues,
            total_connectors=total_connectors,
            explicit_ratio=round(explicit_ratio, 2),
            connector_type_distribution=connector_type_dist,
            replacement_suggestions=suggestions,
            risk_level=risk_level,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        logger.error(f"Connector optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step4-5/diversify", response_model=DiversificationResponse)
async def diversify_patterns(request: DiversificationRequest):
    """
    Step 4.5: Pattern Diversification & Rewriting
    步骤 4.5：句式多样化与改写

    Comprehensive sentence pattern diversification:
    - Transforms sentence openers
    - Switches voice (active<->passive)
    - Adds inversion/emphasis structures
    - Generates before/after metrics comparison

    综合句式多样化处理：
    - 变换句首
    - 切换语态
    - 添加倒装/强调结构
    - 生成前后指标对比
    """
    start_time = time.time()

    try:
        para_text = request.paragraph_text
        para_idx = request.paragraph_index
        intensity = request.rewrite_intensity

        # Get sentences
        # 获取句子
        sentences = _identify_sentences_in_paragraph(para_text, para_idx)

        if not sentences:
            raise HTTPException(status_code=400, detail="No sentences found in paragraph")

        # Calculate before metrics
        # 计算改写前指标
        type_counts_before = {"simple": 0, "compound": 0, "complex": 0, "compound_complex": 0}
        voice_counts_before = {"active": 0, "passive": 0}
        openers_before: Dict[str, int] = {}

        for sent in sentences:
            type_counts_before[sent.sentence_type] += 1
            voice_counts_before[sent.voice] += 1
            openers_before[sent.opener_word] = openers_before.get(sent.opener_word, 0) + 1

        total = len(sentences)
        lengths = [s.word_count for s in sentences]
        length_cv_before = _calculate_length_cv(lengths)

        before_metrics = PatternMetrics(
            simple_ratio=type_counts_before["simple"] / total,
            compound_ratio=type_counts_before["compound"] / total,
            complex_ratio=type_counts_before["complex"] / total,
            compound_complex_ratio=type_counts_before["compound_complex"] / total,
            opener_diversity=len(openers_before) / total,
            voice_balance=voice_counts_before["passive"] / total,
            length_cv=length_cv_before,
            overall_score=_calculate_risk_score(
                type_counts_before["simple"] / total,
                length_cv_before,
                max(openers_before.values()) / total if openers_before else 0,
                0
            ),
        )

        # Generate diversification changes (simplified - would use LLM in production)
        # 生成多样化改变（简化版 - 生产环境应使用LLM）
        changes: List[ChangeRecord] = []
        applied_strategies: Dict[str, int] = {
            "opener_change": 0,
            "voice_switch": 0,
            "sentence_merge": 0,
            "inversion": 0,
        }
        diversified_sentences = []

        for i, sent in enumerate(sentences):
            new_text = sent.text
            changed = False

            # Apply opener change for sentences starting with "The"
            # 对以"The"开头的句子应用开头变换
            if sent.opener_word.lower() == "the" and intensity in ["moderate", "aggressive"]:
                if sent.sentence_type == "simple":
                    new_text = f"Notably, {sent.text[0].lower()}{sent.text[1:]}"
                    changes.append(ChangeRecord(
                        sentence_index=i,
                        original=sent.text,
                        modified=new_text,
                        change_type="opener_change",
                        strategy="adverb_opener",
                        improvement_type="opener",
                    ))
                    applied_strategies["opener_change"] += 1
                    changed = True

            # Apply voice switch for very simple active sentences
            # 对非常简单的主动句应用语态切换
            elif sent.voice == "active" and sent.word_count < 15 and intensity == "aggressive":
                # Simplified passive conversion
                new_text = f"[Passive version of: {sent.text}]"
                changes.append(ChangeRecord(
                    sentence_index=i,
                    original=sent.text,
                    modified=new_text,
                    change_type="voice_switch",
                    strategy="active_to_passive",
                    improvement_type="voice",
                ))
                applied_strategies["voice_switch"] += 1
                changed = True

            diversified_sentences.append(new_text if changed else sent.text)

        # Calculate after metrics (estimated)
        # 计算改写后指标（估算）
        after_metrics = PatternMetrics(
            simple_ratio=max(0, before_metrics.simple_ratio - 0.1),
            compound_ratio=before_metrics.compound_ratio + 0.05,
            complex_ratio=before_metrics.complex_ratio + 0.05,
            compound_complex_ratio=before_metrics.compound_complex_ratio,
            opener_diversity=min(1.0, before_metrics.opener_diversity + 0.2),
            voice_balance=min(0.3, before_metrics.voice_balance + 0.05),
            length_cv=min(0.5, before_metrics.length_cv + 0.05),
            overall_score=max(0, before_metrics.overall_score - 15),
        )

        # Improvement summary
        # 改进摘要
        improvement_summary = {
            "simple_ratio_change": after_metrics.simple_ratio - before_metrics.simple_ratio,
            "opener_diversity_change": after_metrics.opener_diversity - before_metrics.opener_diversity,
            "voice_balance_change": after_metrics.voice_balance - before_metrics.voice_balance,
            "overall_score_change": after_metrics.overall_score - before_metrics.overall_score,
        }

        diversified_text = " ".join(diversified_sentences)

        risk_level = _get_risk_level(int(after_metrics.overall_score))

        processing_time_ms = int((time.time() - start_time) * 1000)

        return DiversificationResponse(
            paragraph_index=para_idx,
            original_text=para_text,
            diversified_text=diversified_text,
            changes=changes,
            applied_strategies=applied_strategies,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            improvement_summary=improvement_summary,
            risk_level=risk_level,
            recommendations=["Review diversified text and apply changes as needed"],
            recommendations_zh=["审核多样化文本并按需应用更改"],
            processing_time_ms=processing_time_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pattern diversification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Paragraph Configuration and Version Management Endpoints
# 段落配置和版本管理端点
# ============================================================================

@router.post("/paragraph/{para_idx}/config")
async def set_paragraph_config(
    para_idx: int,
    config: ParagraphProcessingConfig,
    session_id: Optional[str] = None
):
    """
    Set processing configuration for a single paragraph.
    设置单个段落的处理配置。
    """
    try:
        sid = session_id or "default"
        if sid not in _paragraph_configs:
            _paragraph_configs[sid] = {}

        config.paragraph_index = para_idx
        _paragraph_configs[sid][para_idx] = config

        return {"status": "success", "paragraph_index": para_idx, "config": config.model_dump()}

    except Exception as e:
        logger.error(f"Failed to set paragraph config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paragraph/{para_idx}/config")
async def get_paragraph_config(para_idx: int, session_id: Optional[str] = None):
    """
    Get current configuration for a paragraph.
    获取段落的当前配置。
    """
    try:
        sid = session_id or "default"
        if sid in _paragraph_configs and para_idx in _paragraph_configs[sid]:
            return _paragraph_configs[sid][para_idx].model_dump()
        else:
            return {"status": "not_found", "message": f"No config for paragraph {para_idx}"}

    except Exception as e:
        logger.error(f"Failed to get paragraph config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paragraph/{para_idx}/versions")
async def get_paragraph_versions(para_idx: int, session_id: Optional[str] = None):
    """
    Get version history for a paragraph.
    获取段落的版本历史。
    """
    try:
        sid = session_id or "default"
        if sid in _paragraph_configs and para_idx in _paragraph_configs[sid]:
            config = _paragraph_configs[sid][para_idx]
            return {
                "paragraph_index": para_idx,
                "current_version": config.current_version,
                "versions": [v.model_dump() for v in config.versions],
            }
        else:
            return {"paragraph_index": para_idx, "current_version": 0, "versions": []}

    except Exception as e:
        logger.error(f"Failed to get paragraph versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/paragraph/{para_idx}/revert")
async def revert_paragraph(
    para_idx: int,
    target_version: int,
    session_id: Optional[str] = None
):
    """
    Revert paragraph to a specific version.
    将段落回退到指定版本。
    """
    try:
        sid = session_id or "default"
        if sid not in _paragraph_configs or para_idx not in _paragraph_configs[sid]:
            raise HTTPException(status_code=404, detail=f"No config for paragraph {para_idx}")

        config = _paragraph_configs[sid][para_idx]
        if target_version < 0 or target_version >= len(config.versions):
            raise HTTPException(status_code=400, detail=f"Invalid version {target_version}")

        config.current_version = target_version

        return {
            "status": "success",
            "paragraph_index": para_idx,
            "reverted_to": target_version,
            "text": config.versions[target_version].text,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revert paragraph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Batch Operation Endpoints
# 批量操作端点
# ============================================================================

@router.post("/batch/config")
async def batch_set_config(request: BatchConfigRequest, session_id: Optional[str] = None):
    """
    Set configuration for multiple paragraphs.
    批量设置多个段落的配置。
    """
    try:
        sid = session_id or "default"
        if sid not in _paragraph_configs:
            _paragraph_configs[sid] = {}

        updated = []
        for para_idx in request.paragraph_indices:
            config = ParagraphProcessingConfig(
                paragraph_index=para_idx,
                **request.config
            )
            _paragraph_configs[sid][para_idx] = config
            updated.append(para_idx)

        return {"status": "success", "updated_paragraphs": updated}

    except Exception as e:
        logger.error(f"Batch config failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/lock")
async def batch_lock(request: BatchLockRequest, session_id: Optional[str] = None):
    """
    Lock or unlock multiple paragraphs.
    批量锁定或解锁段落。
    """
    try:
        sid = session_id or "default"
        if sid not in _paragraph_configs:
            _paragraph_configs[sid] = {}

        updated = []
        for para_idx in request.paragraph_indices:
            if para_idx not in _paragraph_configs[sid]:
                _paragraph_configs[sid][para_idx] = ParagraphProcessingConfig(
                    paragraph_index=para_idx
                )

            _paragraph_configs[sid][para_idx].status = "locked" if request.locked else "pending"
            updated.append(para_idx)

        return {
            "status": "success",
            "locked": request.locked,
            "updated_paragraphs": updated
        }

    except Exception as e:
        logger.error(f"Batch lock failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
