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

# Import Layer 2 sub-step handlers for LLM-based analysis
# 导入 Layer 2 子步骤处理器用于基于LLM的分析
from src.api.routes.substeps.layer2.step4_0_handler import Step4_0Handler
from src.api.routes.substeps.layer2.step4_1_handler import Step4_1Handler
from src.api.routes.substeps.layer2.step4_2_handler import Step4_2Handler
from src.api.routes.substeps.layer2.step4_3_handler import Step4_3Handler
from src.api.routes.substeps.layer2.step4_4_handler import Step4_4Handler
from src.api.routes.substeps.layer2.step4_5_handler import Step4_5Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Reusable segmenter instance
# 可重用的分句器实例
_segmenter = SentenceSegmenter()

# Initialize Layer 2 sub-step handlers
# 初始化 Layer 2 子步骤处理器
step4_0_handler = Step4_0Handler()
step4_1_handler = Step4_1Handler()
step4_2_handler = Step4_2Handler()
step4_3_handler = Step4_3Handler()
step4_4_handler = Step4_4Handler()
step4_5_handler = Step4_5Handler()


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
        # Get document text from request
        # 从请求获取文档文本
        if request.text:
            document_text = request.text
        elif request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)
        else:
            raise HTTPException(status_code=400, detail="Either 'text' or 'paragraphs' must be provided")

        # Call Step4_0Handler for LLM-based sentence identification
        # 调用 Step4_0Handler 进行基于LLM的句子识别
        logger.info("Calling Step4_0Handler for LLM-based sentence identification")
        result = await step4_0_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer2-step4-0",
            use_cache=True
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Convert handler result to response model
        # 将处理器结果转换为响应模型
        sentences = []
        for idx, sent_data in enumerate(result.get("sentences", [])):
            if isinstance(sent_data, dict):
                sentences.append(SentenceInfo(
                    index=sent_data.get("index", idx),
                    text=sent_data.get("text", ""),
                    paragraph_index=sent_data.get("paragraph_index", 0),
                    word_count=sent_data.get("word_count", 0),
                    sentence_type=sent_data.get("sentence_type", "simple"),
                    function_role=sent_data.get("function_role", "body"),
                    has_subordinate=sent_data.get("has_subordinate", False),
                    clause_depth=sent_data.get("clause_depth", 0),
                    voice=sent_data.get("voice", "active"),
                    opener_word=sent_data.get("opener_word", "")
                ))

        return SentenceIdentificationResponse(
            sentences=sentences,
            sentence_count=result.get("sentence_count", len(sentences)),
            paragraph_sentence_map=result.get("paragraph_sentence_map", {}),
            type_distribution=result.get("type_distribution", {}),
            risk_level=result.get("risk_level", "low"),
            risk_score=result.get("risk_score", 0),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
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
        # Get document text from request
        # 从请求获取文档文本
        if request.text:
            document_text = request.text
        elif request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)
        else:
            raise HTTPException(status_code=400, detail="Either 'text' or 'paragraphs' must be provided")

        # Call Step4_1Handler for LLM-based pattern analysis
        # 调用 Step4_1Handler 进行基于LLM的句式分析
        logger.info("Calling Step4_1Handler for LLM-based pattern analysis")
        result = await step4_1_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="layer2-step4-1",
            use_cache=True
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Convert handler result to response model
        # 将处理器结果转换为响应模型
        type_dist_raw = result.get("type_distribution", {})
        type_distribution = {}
        for stype, data in type_dist_raw.items():
            if isinstance(data, dict):
                type_distribution[stype] = TypeStats(
                    count=data.get("count", 0),
                    percentage=data.get("percentage", 0.0),
                    is_risk=data.get("is_risk", False),
                    threshold=data.get("threshold", 0.0),
                )
            else:
                type_distribution[stype] = TypeStats(count=0, percentage=0.0, is_risk=False, threshold=0.0)

        opener_raw = result.get("opener_analysis", {})
        opener_analysis = OpenerAnalysis(
            opener_counts=opener_raw.get("opener_counts", {}),
            top_repeated=opener_raw.get("top_repeated", []),
            repetition_rate=opener_raw.get("repetition_rate", 0.0),
            subject_opening_rate=opener_raw.get("subject_opening_rate", 0.0),
            issues=opener_raw.get("issues", []),
        )

        # Get high_risk_paragraphs from LLM result, or compute from issues
        # 从LLM结果获取高风险段落，或从issues计算
        high_risk_paragraphs = result.get("high_risk_paragraphs", [])

        # Always compute paragraph-level metrics for ALL paragraphs
        # 始终为所有段落计算段落级指标
        paragraphs = document_text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # Build existing high_risk_paragraphs map
        # 构建现有的高风险段落映射
        existing_para_map = {p.get("paragraph_index"): p for p in high_risk_paragraphs if isinstance(p, dict)}

        # Track issues per paragraph from LLM result
        # 从LLM结果跟踪每个段落的问题
        paragraph_issues = {}
        for issue in result.get("issues", []):
            severity = issue.get("severity", "low")
            affected_positions = issue.get("affected_positions", [])

            for pos in affected_positions:
                para_idx = None
                if isinstance(pos, str):
                    if pos.startswith("para_"):
                        try:
                            para_idx = int(pos.replace("para_", ""))
                        except ValueError:
                            pass
                    elif pos.startswith("sent_") or pos.startswith("sentence_"):
                        # Map sentence to paragraph
                        # 将句子映射到段落
                        try:
                            sent_idx = int(pos.replace("sent_", "").replace("sentence_", ""))
                            total_sents = 0
                            for pi, para in enumerate(paragraphs):
                                para_sents = len([s for s in para.split('.') if s.strip()])
                                if total_sents + para_sents > sent_idx:
                                    para_idx = pi
                                    break
                                total_sents += para_sents
                        except ValueError:
                            pass

                if para_idx is not None and 0 <= para_idx < len(paragraphs):
                    if para_idx not in paragraph_issues:
                        paragraph_issues[para_idx] = {"high": 0, "medium": 0, "low": 0}
                    paragraph_issues[para_idx][severity] = paragraph_issues[para_idx].get(severity, 0) + 1

        # Compute metrics for ALL paragraphs
        # 为所有段落计算指标
        all_paragraph_data = []
        global_opener_repetition = opener_raw.get("repetition_rate", 0.0)
        global_subject_rate = opener_raw.get("subject_opening_rate", 0.0)

        for para_idx, para_text in enumerate(paragraphs):
            # Get sentences in this paragraph
            # 获取此段落的句子
            para_sentences = [s.strip() for s in para_text.split('.') if s.strip()]
            sentence_count = len(para_sentences)

            # Calculate sentence lengths for length CV
            # 计算句长以得到长度变异系数
            sentence_lengths = [len(s.split()) for s in para_sentences if s]
            if len(sentence_lengths) >= 2:
                mean_length = statistics.mean(sentence_lengths)
                if mean_length > 0:
                    std_length = statistics.stdev(sentence_lengths)
                    length_cv = std_length / mean_length
                else:
                    length_cv = 0.0
            else:
                length_cv = 0.3  # Default for single sentence

            # Calculate opener repetition for this paragraph
            # 计算此段落的句首重复率
            if para_sentences:
                openers = [s.split()[0].strip('.,!?;:') if s.split() else '' for s in para_sentences]
                opener_counts = {}
                for opener in openers:
                    if opener:
                        opener_counts[opener] = opener_counts.get(opener, 0) + 1
                max_repeat = max(opener_counts.values()) if opener_counts else 0
                para_opener_repetition = max_repeat / len(para_sentences) if para_sentences else 0.0
            else:
                para_opener_repetition = 0.0

            # Calculate simple sentence ratio (estimate based on sentence structure)
            # 计算简单句比例（基于句子结构估算）
            simple_count = 0
            for sent in para_sentences:
                # Simple heuristic: no subordinate conjunctions = likely simple sentence
                # 简单启发式：没有从属连词 = 可能是简单句
                subordinate_markers = ['which', 'that', 'because', 'although', 'while', 'when', 'if', 'since', 'unless', 'whereas']
                sent_lower = sent.lower()
                has_subordinate = any(marker in sent_lower for marker in subordinate_markers)
                if not has_subordinate:
                    simple_count += 1
            simple_ratio = simple_count / sentence_count if sentence_count > 0 else 0.0

            # Get issue counts for this paragraph
            # 获取此段落的问题计数
            issue_counts = paragraph_issues.get(para_idx, {"high": 0, "medium": 0, "low": 0})

            # Calculate risk score based on metrics and issues
            # 根据指标和问题计算风险分数
            risk_score = 20  # Base score

            # Add risk from issues
            risk_score += issue_counts.get("high", 0) * 20
            risk_score += issue_counts.get("medium", 0) * 10
            risk_score += issue_counts.get("low", 0) * 5

            # Add risk from metrics
            if simple_ratio > 0.7:
                risk_score += 15
            elif simple_ratio > 0.5:
                risk_score += 8
            if length_cv < 0.2:
                risk_score += 15  # Too uniform
            elif length_cv < 0.3:
                risk_score += 8
            if para_opener_repetition > 0.5:
                risk_score += 15
            elif para_opener_repetition > 0.3:
                risk_score += 8

            risk_score = min(100, risk_score)

            # Determine risk level
            # 确定风险等级
            if risk_score >= 60:
                risk_level = "high"
            elif risk_score >= 40:
                risk_level = "medium"
            else:
                risk_level = "low"

            # Use existing data if available, otherwise use computed data
            # 如果有现有数据则使用，否则使用计算的数据
            if para_idx in existing_para_map:
                existing = existing_para_map[para_idx]
                all_paragraph_data.append({
                    "paragraph_index": para_idx,
                    "risk_score": existing.get("risk_score", risk_score),
                    "risk_level": existing.get("risk_level", risk_level),
                    "simple_ratio": existing.get("simple_ratio", simple_ratio),
                    "length_cv": existing.get("length_cv", length_cv),
                    "opener_repetition": existing.get("opener_repetition", para_opener_repetition),
                    "sentence_count": sentence_count
                })
            else:
                all_paragraph_data.append({
                    "paragraph_index": para_idx,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "simple_ratio": round(simple_ratio, 2),
                    "length_cv": round(length_cv, 2),
                    "opener_repetition": round(para_opener_repetition, 2),
                    "sentence_count": sentence_count
                })

        # Replace high_risk_paragraphs with all paragraph data
        # 用所有段落数据替换 high_risk_paragraphs
        high_risk_paragraphs = all_paragraph_data
        logger.info(f"Computed metrics for {len(high_risk_paragraphs)} paragraphs")

        return PatternAnalysisResponse(
            type_distribution=type_distribution,
            opener_analysis=opener_analysis,
            voice_distribution=result.get("voice_distribution", {}),
            clause_depth_stats=result.get("clause_depth_stats", {}),
            parallel_structure_count=result.get("parallel_structure_count", 0),
            issues=result.get("issues", []),
            risk_level=result.get("risk_level", "low"),
            risk_score=result.get("risk_score", 0),
            high_risk_paragraphs=high_risk_paragraphs,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            syntactic_voids=result.get("syntactic_voids", []),
            void_score=result.get("void_score", 0),
            void_density=result.get("void_density", 0.0),
            has_critical_void=result.get("has_critical_void", False),
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
        # Get document text from request
        # 从请求获取文档文本
        if request.text:
            document_text = request.text
        elif request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)
        else:
            raise HTTPException(status_code=400, detail="Either 'text' or 'paragraphs' must be provided")

        # Call Step4_2Handler for LLM-based length analysis
        # 调用 Step4_2Handler 进行基于LLM的句长分析
        # Use paragraph-specific cache key to avoid sharing results between paragraphs
        # 使用段落特定的缓存键，避免段落间共享结果
        para_idx = request.paragraph_index if request.paragraph_index is not None else 0
        cache_step_name = f"layer2-step4-2-para{para_idx}"
        logger.info(f"Calling Step4_2Handler for paragraph {para_idx}")
        result = await step4_2_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name=cache_step_name,
            use_cache=True
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Convert handler result to response model
        # 将处理器结果转换为响应模型
        return LengthAnalysisResponse(
            paragraph_length_stats=result.get("paragraph_length_stats", []),
            overall_length_cv=result.get("overall_length_cv", 0.0),
            uniformity_issues=result.get("uniformity_issues", []),
            merge_candidates=result.get("merge_candidates", []),
            split_candidates=result.get("split_candidates", []),
            risk_level=result.get("risk_level", "low"),
            risk_score=result.get("risk_score", 0),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
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
        # Get document text from request
        # 从请求获取文档文本
        document_text = request.paragraph_text

        # Call Step4_3Handler for LLM-based merge suggestions
        # 调用 Step4_3Handler 进行基于LLM的合并建议
        # Use paragraph-specific cache key to avoid sharing results between paragraphs
        # 使用段落特定的缓存键，避免段落间共享结果
        para_idx = request.paragraph_index
        cache_step_name = f"layer2-step4-3-para{para_idx}"
        logger.info(f"Calling Step4_3Handler for paragraph {para_idx}")
        result = await step4_3_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id if hasattr(request, 'session_id') else None,
            step_name=cache_step_name,
            use_cache=True
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Convert handler result to response model
        # 将处理器结果转换为响应模型
        candidates = []
        for cand_data in result.get("candidates", []):
            if isinstance(cand_data, dict):
                candidates.append(MergeCandidate(
                    sentence_indices=cand_data.get("sentence_indices", []),
                    original_sentences=cand_data.get("original_sentences", []),
                    merged_text=cand_data.get("merged_text", ""),
                    merge_type=cand_data.get("merge_type", "addition"),
                    similarity_score=cand_data.get("similarity_score", 0.0),
                    readability_score=cand_data.get("readability_score", 0.0),
                    word_count_before=cand_data.get("word_count_before", 0),
                    word_count_after=cand_data.get("word_count_after", 0),
                    complexity_gain=cand_data.get("complexity_gain", ""),
                ))

        return MergeSuggestionResponse(
            paragraph_index=request.paragraph_index,
            candidates=candidates,
            estimated_improvement=result.get("estimated_improvement", {}),
            risk_level=result.get("risk_level", "low"),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
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
        # Get document text from request
        # 从请求获取文档文本
        document_text = request.paragraph_text

        # Call Step4_4Handler for LLM-based connector optimization
        # 调用 Step4_4Handler 进行基于LLM的连接词优化
        # Use paragraph-specific cache key to avoid sharing results between paragraphs
        # 使用段落特定的缓存键，避免段落间共享结果
        para_idx = request.paragraph_index
        cache_step_name = f"layer2-step4-4-para{para_idx}"
        logger.info(f"Calling Step4_4Handler for paragraph {para_idx}")
        result = await step4_4_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id if hasattr(request, 'session_id') else None,
            step_name=cache_step_name,
            use_cache=True
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Convert handler result to response model
        # 将处理器结果转换为响应模型
        connector_issues = []
        for issue_data in result.get("connector_issues", []):
            if isinstance(issue_data, dict):
                connector_issues.append(ConnectorIssue(
                    sentence_index=issue_data.get("sentence_index", 0),
                    connector=issue_data.get("connector", ""),
                    connector_type=issue_data.get("connector_type", ""),
                    position=issue_data.get("position", 0),
                    risk_level=issue_data.get("risk_level", "medium"),
                    context=issue_data.get("context", ""),
                ))

        replacement_suggestions = []
        for sugg_data in result.get("replacement_suggestions", []):
            if isinstance(sugg_data, dict):
                replacement_suggestions.append(ReplacementSuggestion(
                    original_connector=sugg_data.get("original_connector", ""),
                    sentence_index=sugg_data.get("sentence_index", 0),
                    replacement_type=sugg_data.get("replacement_type", "remove"),
                    new_text=sugg_data.get("new_text", ""),
                    explanation=sugg_data.get("explanation", ""),
                    explanation_zh=sugg_data.get("explanation_zh", ""),
                ))

        return ConnectorOptimizationResponse(
            paragraph_index=request.paragraph_index,
            connector_issues=connector_issues,
            total_connectors=result.get("total_connectors", 0),
            explicit_ratio=result.get("explicit_ratio", 0.0),
            connector_type_distribution=result.get("connector_type_distribution", {}),
            replacement_suggestions=replacement_suggestions,
            risk_level=result.get("risk_level", "low"),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
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
        # Get document text from request
        # 从请求获取文档文本
        document_text = request.paragraph_text

        # Call Step4_5Handler for LLM-based pattern diversification
        # 调用 Step4_5Handler 进行基于LLM的句式多样化
        # Use paragraph-specific cache key to avoid sharing results between paragraphs
        # 使用段落特定的缓存键，避免段落间共享结果
        para_idx = request.paragraph_index
        cache_step_name = f"layer2-step4-5-para{para_idx}"
        logger.info(f"Calling Step4_5Handler for paragraph {para_idx}")
        result = await step4_5_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id if hasattr(request, 'session_id') else None,
            step_name=cache_step_name,
            use_cache=True
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Convert handler result to response model
        # 将处理器结果转换为响应模型
        changes = []
        for change_data in result.get("changes", []):
            if isinstance(change_data, dict):
                changes.append(ChangeRecord(
                    sentence_index=change_data.get("sentence_index", 0),
                    original=change_data.get("original", ""),
                    modified=change_data.get("modified", ""),
                    change_type=change_data.get("change_type", ""),
                    strategy=change_data.get("strategy", ""),
                    improvement_type=change_data.get("improvement_type", ""),
                ))

        before_raw = result.get("before_metrics", {})
        before_metrics = PatternMetrics(
            simple_ratio=before_raw.get("simple_ratio", 0.0),
            compound_ratio=before_raw.get("compound_ratio", 0.0),
            complex_ratio=before_raw.get("complex_ratio", 0.0),
            compound_complex_ratio=before_raw.get("compound_complex_ratio", 0.0),
            opener_diversity=before_raw.get("opener_diversity", 0.0),
            voice_balance=before_raw.get("voice_balance", 0.0),
            length_cv=before_raw.get("length_cv", 0.0),
            overall_score=before_raw.get("overall_score", 0.0),
        )

        after_raw = result.get("after_metrics", {})
        after_metrics = PatternMetrics(
            simple_ratio=after_raw.get("simple_ratio", 0.0),
            compound_ratio=after_raw.get("compound_ratio", 0.0),
            complex_ratio=after_raw.get("complex_ratio", 0.0),
            compound_complex_ratio=after_raw.get("compound_complex_ratio", 0.0),
            opener_diversity=after_raw.get("opener_diversity", 0.0),
            voice_balance=after_raw.get("voice_balance", 0.0),
            length_cv=after_raw.get("length_cv", 0.0),
            overall_score=after_raw.get("overall_score", 0.0),
        )

        return DiversificationResponse(
            paragraph_index=request.paragraph_index,
            original_text=request.paragraph_text,
            diversified_text=result.get("diversified_text", ""),
            changes=changes,
            applied_strategies=result.get("applied_strategies", {}),
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            improvement_summary=result.get("improvement_summary", {}),
            risk_level=result.get("risk_level", "low"),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
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
