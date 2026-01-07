"""
Pydantic schemas for API request/response validation
API请求/响应验证的Pydantic模式
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# Enums
# 枚举类型
class RiskLevel(str, Enum):
    """Risk level enumeration 风险等级枚举"""
    SAFE = "safe"      # <10: No risk, likely human-written
    LOW = "low"        # 10-24: Low risk
    MEDIUM = "medium"  # 25-49: Medium risk
    HIGH = "high"      # ≥50: High risk


class SuggestionSource(str, Enum):
    """Suggestion source enumeration 建议来源枚举"""
    LLM = "llm"
    RULE = "rule"
    CUSTOM = "custom"


class ProcessMode(str, Enum):
    """Processing mode enumeration 处理模式枚举"""
    INTERVENTION = "intervention"
    YOLO = "yolo"


class SessionStatus(str, Enum):
    """Session status enumeration 会话状态枚举"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


# Request Models
# 请求模型
class AnalyzeRequest(BaseModel):
    """
    Text analysis request
    文本分析请求
    """
    text: str = Field(..., min_length=1, description="Text to analyze")
    target_lang: str = Field(default="zh", description="Target language for explanations")
    include_turnitin: bool = Field(default=True, description="Include Turnitin perspective")
    include_gptzero: bool = Field(default=True, description="Include GPTZero perspective")


class SuggestRequest(BaseModel):
    """
    Suggestion generation request
    建议生成请求

    CAASS v2.0 Phase 2: Added whitelist and context_baseline support
    """
    sentence: str = Field(..., min_length=1, description="Sentence to humanize")
    issues: List[Dict[str, Any]] = Field(default=[], description="Detected issues")
    locked_terms: List[str] = Field(default=[], description="Terms to protect")
    colloquialism_level: int = Field(default=4, ge=0, le=10, description="Colloquialism level 0-10")
    target_lang: str = Field(default="zh", description="Target language for explanations")
    whitelist: List[str] = Field(default=[], description="Domain-specific terms to exempt from scoring")
    context_baseline: int = Field(default=0, ge=0, le=25, description="Paragraph context baseline score")
    is_paraphrase: bool = Field(default=False, description="Whether the sentence is a paraphrase")


class SessionStartRequest(BaseModel):
    """
    Session start request
    会话启动请求
    """
    document_id: str = Field(..., description="Document ID to process")
    mode: ProcessMode = Field(default=ProcessMode.INTERVENTION, description="Processing mode")
    colloquialism_level: int = Field(default=4, ge=0, le=10, description="Colloquialism level")
    target_lang: str = Field(default="zh", description="Target language")
    process_levels: List[RiskLevel] = Field(
        default=[RiskLevel.HIGH, RiskLevel.MEDIUM],
        description="Risk levels to process"
    )


class ApplySuggestionRequest(BaseModel):
    """
    Apply suggestion request
    应用建议请求
    """
    session_id: str = Field(..., description="Session ID")
    sentence_id: str = Field(..., description="Sentence ID")
    source: SuggestionSource = Field(..., description="Suggestion source")
    modified_text: Optional[str] = Field(None, description="Custom modified text if source is custom")


class CustomInputRequest(BaseModel):
    """
    Custom input validation request
    自定义输入验证请求
    """
    session_id: str = Field(..., description="Session ID")
    sentence_id: str = Field(..., description="Sentence ID")
    custom_text: str = Field(..., min_length=1, description="User's custom modification")


# Response Models
# 响应模型
class FingerprintMatch(BaseModel):
    """
    Fingerprint word match result
    指纹词匹配结果
    """
    word: str
    position: int
    risk_weight: float
    category: str
    replacements: List[str] = []


class FingerprintWord(BaseModel):
    """
    Fingerprint word with position information
    带位置信息的指纹词
    """
    word: str
    position: int
    end_position: int
    risk_weight: float
    category: str
    replacements: List[str] = []


class IssueDetail(BaseModel):
    """
    Detected issue detail
    检测到的问题详情
    """
    type: str  # fingerprint, ppl, structure, etc.
    description: str
    description_zh: str
    severity: RiskLevel
    position: Optional[int] = None
    word: Optional[str] = None


class DetectorView(BaseModel):
    """
    Detector-specific analysis view
    检测器特定的分析视角
    """
    detector: str  # turnitin, gptzero
    risk_score: int
    key_issues: List[str]
    key_issues_zh: List[str]


class SentenceAnalysis(BaseModel):
    """
    Complete sentence analysis result
    完整的句子分析结果
    """
    id: str  # Database ID for API calls
    index: int
    text: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    ppl: float
    ppl_risk: RiskLevel
    fingerprints: List[FingerprintMatch] = []
    fingerprint_density: float
    issues: List[IssueDetail] = []
    turnitin_view: Optional[DetectorView] = None
    gptzero_view: Optional[DetectorView] = None
    locked_terms: List[str] = []
    status: Optional[str] = None  # pending, current, processed, skip, flag
    new_risk_score: Optional[int] = None  # Risk score after modification
    new_risk_level: Optional[RiskLevel] = None  # Risk level after modification
    # Phase 2: Enhanced metrics
    # 第二阶段：增强指标
    burstiness_value: float = 0.0  # Burstiness ratio (0-1), higher = more human-like
    burstiness_risk: str = "unknown"  # Burstiness risk level: low, medium, high
    connector_count: int = 0  # Number of explicit connectors in this sentence
    connector_word: Optional[str] = None  # Detected connector word if any
    context_baseline: int = 0  # Paragraph-level context baseline score
    paragraph_index: int = 0  # Index of the paragraph this sentence belongs to
    
    # Paraphrase detection
    # 释义检测
    is_paraphrase: bool = False


class ChangeDetail(BaseModel):
    """
    Single change detail
    单个改动详情
    """
    original: str
    replacement: str
    reason: str
    reason_zh: str


class Suggestion(BaseModel):
    """
    Single suggestion result
    单个建议结果
    """
    source: SuggestionSource
    rewritten: str
    changes: List[ChangeDetail] = []
    predicted_risk: int = Field(..., ge=0, le=100)
    semantic_similarity: float = Field(..., ge=0, le=1)
    explanation: str
    explanation_zh: str


class SuggestResponse(BaseModel):
    """
    Complete suggestion response
    完整的建议响应
    """
    original: str
    original_risk: int
    translation: str  # Original meaning in target language
    llm_suggestion: Optional[Suggestion] = None
    rule_suggestion: Optional[Suggestion] = None
    locked_terms: List[str] = []


class ValidationResult(BaseModel):
    """
    Validation result
    验证结果
    """
    passed: bool
    semantic_similarity: float
    terms_intact: bool
    new_risk_score: int
    new_risk_level: RiskLevel
    message: str
    message_zh: str


class SessionState(BaseModel):
    """
    Current session state
    当前会话状态
    """
    session_id: str
    document_id: str
    mode: ProcessMode
    total_sentences: int
    processed: int
    skipped: int
    flagged: int
    current_index: int
    current_sentence: Optional[SentenceAnalysis] = None
    suggestions: Optional[SuggestResponse] = None
    progress_percent: float
    status: str = "active"
    step_logs: List[Dict[str, Any]] = []


class ProgressUpdate(BaseModel):
    """
    Progress update for YOLO mode
    YOLO模式的进度更新
    """
    total: int
    processed: int
    current_sentence: str
    percent: float
    estimated_remaining: Optional[int] = None  # seconds


class DocumentInfo(BaseModel):
    """
    Document information
    文档信息
    """
    id: str
    filename: str
    status: str
    total_sentences: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    created_at: datetime


class SessionInfo(BaseModel):
    """
    Session summary info for listing
    用于列表的会话摘要信息
    """
    session_id: str
    document_id: str
    document_name: str
    mode: ProcessMode
    status: str
    current_step: str = "step1-1"  # step1-1, step1-2, step2, step3, review
    total_sentences: int
    processed: int
    progress_percent: float
    colloquialism_level: int = 4  # Colloquialism level (0-10) / 口语化程度 (0-10)
    created_at: datetime
    completed_at: Optional[datetime] = None
    step_logs: List[Dict[str, Any]] = []


class ExportResult(BaseModel):
    """
    Export result
    导出结果
    """
    filename: str
    format: str
    size: int
    download_url: str


# Sentence Analysis Models
# 句子分析模型
class GrammarModifier(BaseModel):
    """
    Grammar modifier (attributive/adverbial/complement)
    语法修饰成分（定语/状语/补语）
    """
    type: str  # attributive, adverbial, complement
    type_zh: str
    text: str
    modifies: str


class GrammarStructure(BaseModel):
    """
    Sentence grammar structure
    句子语法结构
    """
    subject: str
    subject_zh: str
    predicate: str
    predicate_zh: str
    object: Optional[str] = None
    object_zh: Optional[str] = None
    modifiers: List[GrammarModifier] = []


class ClauseInfo(BaseModel):
    """
    Clause information
    从句信息
    """
    type: str  # relative, noun, adverbial, etc.
    type_zh: str
    text: str
    function: str
    function_zh: str


class PronounReference(BaseModel):
    """
    Pronoun reference information
    代词指代信息
    """
    pronoun: str
    reference: str
    reference_zh: str
    context: str


class AIWordSuggestion(BaseModel):
    """
    AI word replacement suggestion
    AI词汇替换建议
    """
    word: str
    level: int  # 1=high risk, 2=medium risk
    level_desc: str
    alternatives: List[str]
    context_suggestion: str


class RewriteSuggestion(BaseModel):
    """
    Sentence rewrite suggestion
    句式改写建议
    """
    type: str
    type_zh: str
    description: str
    description_zh: str
    example: Optional[str] = None


class SentenceAnalysisRequest(BaseModel):
    """
    Request for detailed sentence analysis
    详细句子分析请求
    """
    sentence: str = Field(..., min_length=1, description="Sentence to analyze")
    colloquialism_level: int = Field(default=5, ge=0, le=10, description="Colloquialism level for suggestions")


class SentenceAnalysisResponse(BaseModel):
    """
    Detailed sentence analysis response
    详细句子分析响应
    """
    original: str
    grammar: GrammarStructure
    clauses: List[ClauseInfo] = []
    pronouns: List[PronounReference] = []
    ai_words: List[AIWordSuggestion] = []
    rewrite_suggestions: List[RewriteSuggestion] = []


# Phase 3: Transition Analysis Models (Level 2 De-AIGC)
# 第三阶段：衔接分析模型（Level 2 De-AIGC）

class TransitionStrategy(str, Enum):
    """Transition strategy enumeration 过渡策略枚举"""
    SEMANTIC_ECHO = "semantic_echo"  # Use key concepts from para_a in para_b
    LOGICAL_HOOK = "logical_hook"    # Use question or problem-solution pattern
    RHYTHM_BREAK = "rhythm_break"    # Break uniform rhythm with varied structure


class TransitionAnalysisRequest(BaseModel):
    """
    Transition analysis request (Level 2)
    衔接分析请求（Level 2）
    """
    para_a: str = Field(..., min_length=1, description="Previous paragraph")
    para_b: str = Field(..., min_length=1, description="Next paragraph")
    context_hint: Optional[str] = Field(None, description="Core thesis from Level 1 analysis")


class TransitionIssue(BaseModel):
    """
    Detected transition issue
    检测到的衔接问题
    """
    type: str  # explicit_connector, too_smooth, topic_sentence_pattern, summary_ending, high_semantic_overlap
    description: str
    description_zh: str
    severity: str  # high, medium, low
    position: str  # para_a_end, para_b_start, both
    word: Optional[str] = None


class TransitionOption(BaseModel):
    """
    A single transition repair option
    单个衔接修复选项
    """
    strategy: TransitionStrategy
    strategy_name_zh: str
    para_a_ending: str  # Modified ending of paragraph A
    para_b_opening: str  # Modified opening of paragraph B
    key_concepts: List[str] = []  # For semantic_echo
    hook_type: Optional[str] = None  # For logical_hook: implication, observation, limitation
    rhythm_change: Optional[str] = None  # For rhythm_break: long→short, complex→simple
    explanation: str
    explanation_zh: str
    predicted_improvement: int = Field(default=0, ge=0, le=100, description="Expected score reduction")


class TransitionAnalysisResponse(BaseModel):
    """
    Complete transition analysis response
    完整的衔接分析响应
    """
    # Original content
    # 原始内容
    para_a_ending: str  # Last 1-2 sentences of paragraph A
    para_b_opening: str  # First 1-2 sentences of paragraph B

    # Analysis results
    # 分析结果
    smoothness_score: int = Field(ge=0, le=100, description="0-100, higher = more AI-like")
    risk_level: str  # low, medium, high
    issues: List[TransitionIssue] = []
    explicit_connectors: List[str] = []

    # Pattern detection
    # 模式检测
    has_topic_sentence_pattern: bool = False
    has_summary_ending: bool = False
    semantic_overlap: float = Field(default=0.0, ge=0, le=1)

    # Repair options (populated when suggestions are generated)
    # 修复选项（生成建议时填充）
    options: List[TransitionOption] = []

    # Messages
    # 消息
    message: str = ""
    message_zh: str = ""


class DocumentTransitionAnalysisRequest(BaseModel):
    """
    Request to analyze all transitions in a document
    分析文档中所有衔接的请求
    """
    document_id: str = Field(..., description="Document ID to analyze")
    context_hint: Optional[str] = Field(None, description="Core thesis for the document")


class DocumentTransitionSummary(BaseModel):
    """
    Summary of all paragraph transitions in a document
    文档中所有段落衔接的摘要
    """
    document_id: str
    total_transitions: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    avg_smoothness_score: float
    common_issues: List[str] = []
    transitions: List[TransitionAnalysisResponse] = []


# ============================================================================
# Structure Analysis Schemas (Phase 4: Level 1 De-AIGC)
# 结构分析模式（第4阶段：Level 1 De-AIGC）
# ============================================================================


class StructureStrategy(str, Enum):
    """Structure strategy types 结构策略类型"""
    OPTIMIZE_CONNECTION = "optimize_connection"
    DEEP_RESTRUCTURE = "deep_restructure"


class ParagraphInfo(BaseModel):
    """
    Information about a paragraph
    段落信息
    """
    index: int
    first_sentence: str
    last_sentence: str
    word_count: int
    sentence_count: int
    has_topic_sentence: bool
    has_summary_ending: bool
    connector_words: List[str] = []
    function_type: str  # introduction, body, conclusion, transition, evidence, analysis
    # Smart structure fields (optional, populated by LLM analysis)
    # 智能结构字段（可选，由 LLM 分析填充）
    position: Optional[str] = None  # Section position like "3.2(1)"
    summary: Optional[str] = None  # Content summary
    summary_zh: Optional[str] = None  # Chinese summary
    ai_risk: Optional[str] = None  # high/medium/low
    ai_risk_reason: Optional[str] = None  # Chinese reason (引用原文保留原语言)
    # Detailed rewrite suggestion fields
    # 详细修改建议字段
    rewrite_suggestion_zh: Optional[str] = None  # Specific Chinese rewrite advice (中文改写建议)
    rewrite_example: Optional[str] = None  # Example rewritten text in English (英文改写示例)


class SmartParagraphInfo(BaseModel):
    """
    Smart paragraph info from LLM analysis
    来自 LLM 分析的智能段落信息
    """
    position: str  # Section position like "3.2(1)"
    summary: str  # English content summary
    summary_zh: str  # Chinese content summary
    first_sentence: str
    last_sentence: str
    word_count: int
    ai_risk: str  # high/medium/low
    ai_risk_reason: str  # Chinese reason (中文原因，引用原文保留原语言)
    # Detailed rewrite suggestion for this paragraph (Chinese)
    # 针对此段落的具体修改建议（中文）
    rewrite_suggestion_zh: Optional[str] = None
    # Example rewritten opening (English)
    # 改写示例（英文）
    rewrite_example: Optional[str] = None


class SectionInfo(BaseModel):
    """
    Information about a document section
    文档章节信息
    """
    number: str  # Section number like "1", "1.1", "2.3.1"
    title: str  # Section title
    paragraphs: List[SmartParagraphInfo] = []


class SmartStructureIssue(BaseModel):
    """
    Structure issue from smart analysis
    智能分析的结构问题
    """
    type: str
    description: str
    description_zh: str
    severity: str
    affected_positions: List[str] = []  # Uses position instead of index


class ExplicitConnector(BaseModel):
    """
    Detected explicit connector word (AI fingerprint)
    检测到的显性连接词（AI指纹）
    """
    word: str
    position: str  # Paragraph position like "3.2(1)"
    location: str  # "paragraph_start" or "sentence_start"
    severity: str  # "high" or "medium"


class LogicBreak(BaseModel):
    """
    Detected logic break between paragraphs
    检测到的段落间逻辑断裂点
    """
    from_position: str  # e.g., "2(1)"
    to_position: str  # e.g., "2(2)"
    transition_type: str  # "smooth", "abrupt", "glue_word_only"
    issue: str  # English description
    issue_zh: str  # Chinese description
    # Optional fields - use str with default="" for Pydantic v2 compatibility
    # Pydantic v2 handles explicit None differently than missing fields
    # 可选字段 - 使用 str 和 default="" 以兼容 Pydantic v2
    # Pydantic v2 对显式 None 和缺失字段处理不同
    suggestion: str = Field(default="")  # English suggestion (empty for smooth transitions)
    suggestion_zh: str = Field(default="")  # Chinese suggestion (empty for smooth transitions)


class SectionSuggestion(BaseModel):
    """
    Detailed suggestion for a specific section/chapter
    针对特定章节的详细建议
    """
    section_number: str  # e.g., "1", "2.1", "Abstract"
    section_title: str  # e.g., "Introduction"
    severity: str  # high, medium, low
    suggestion_type: str  # e.g., "add_content", "restructure", "merge", "split", "reorder"
    suggestion_zh: str  # Detailed Chinese suggestion
    suggestion_en: str  # English version
    details: List[str] = []  # Specific action items in Chinese
    affected_paragraphs: List[str] = []  # e.g., ["1(1)", "1(2)"]


class DetailedImprovementSuggestions(BaseModel):
    """
    Comprehensive improvement suggestions for the document
    文档的全面改进建议
    """
    # Summary-level suggestions (for abstract/摘要)
    # 摘要层面的建议
    abstract_suggestions: List[str] = []  # e.g., ["摘要应提到第2章的研究方法在第4章的应用"]

    # Overall logic/order suggestions
    # 整体逻辑/顺序建议
    logic_suggestions: List[str] = []  # e.g., ["建议调整第3章和第4章的顺序"]

    # Section-by-section suggestions
    # 分章节建议
    section_suggestions: List[SectionSuggestion] = []

    # Priority ranking of suggestions
    # 建议优先级排序
    priority_order: List[str] = []  # Section numbers in priority order

    # Overall assessment
    # 总体评估
    overall_assessment_zh: str = ""
    overall_assessment_en: str = ""


class SmartStructureResponse(BaseModel):
    """
    Response from smart structure analysis
    智能结构分析响应
    """
    sections: List[SectionInfo] = []
    total_paragraphs: int
    total_sections: int
    structure_score: int  # 0-100, higher = more AI-like
    risk_level: str  # low, medium, high
    issues: List[SmartStructureIssue] = []
    score_breakdown: Dict[str, int] = {}
    recommendation: str = ""
    recommendation_zh: str = ""
    # New: Detailed section-by-section improvement suggestions
    # 新增：详细的分章节改进建议
    detailed_suggestions: Optional[DetailedImprovementSuggestions] = None
    # Explicit connectors detected (AI fingerprints)
    # 检测到的显性连接词（AI指纹）
    explicit_connectors: List[ExplicitConnector] = []
    # Logic breaks between paragraphs
    # 段落间逻辑断裂点
    logic_breaks: List[LogicBreak] = []
    # For compatibility with existing frontend
    # 为了与现有前端兼容
    paragraphs: List[ParagraphInfo] = []
    has_linear_flow: bool = False
    has_repetitive_pattern: bool = False
    has_uniform_length: bool = False
    has_predictable_order: bool = False
    options: List["StructureOption"] = []


class StructureIssue(BaseModel):
    """
    Detected structure issue
    检测到的结构问题
    """
    type: str  # linear_flow, repetitive_pattern, uniform_length, predictable_order
    description: str
    description_zh: str
    severity: str  # high, medium, low
    affected_paragraphs: List[int] = []
    suggestion: str
    suggestion_zh: str


class BreakPoint(BaseModel):
    """
    Logic break point in document structure
    文档结构中的逻辑断点
    """
    position: int  # Paragraph index
    type: str  # topic_shift, argument_gap, repetition, abrupt_transition
    description: str
    description_zh: str


class FlowRelation(BaseModel):
    """
    Logical flow relation between paragraphs
    段落之间的逻辑流关系
    """
    from_para: int = Field(..., alias="from")
    to_para: int = Field(..., alias="to")
    relation: str  # continuation, comparison, evidence, return, gap
    symbol: str  # →, ↔, ⤵, ⟳, ✗


class RiskArea(BaseModel):
    """
    Risk area in document structure
    文档结构中的风险区域
    """
    paragraph: int
    risk_level: str
    reason: str
    reason_zh: str


class StructureModification(BaseModel):
    """
    A single structure modification
    单个结构修改
    """
    paragraph_index: int
    change_type: str  # rewrite_opening, rewrite_transition, reorder
    original: Optional[str] = None
    modified: Optional[str] = None
    explanation: str = ""
    explanation_zh: str = ""
    echo_concept: Optional[str] = None  # Key concept for next paragraph


class StructureChange(BaseModel):
    """
    A structural change for deep restructure
    深度重组的结构变化
    """
    type: str  # reorder, split, merge, insert
    affected_paragraphs: List[int] = []
    description: str
    description_zh: str


class StructureOption(BaseModel):
    """
    A structure repair option
    结构修复选项
    """
    strategy: StructureStrategy
    strategy_name_zh: str
    modifications: List[StructureModification] = []  # For optimize_connection
    new_order: List[int] = []  # For deep_restructure
    restructure_type: Optional[str] = None  # For deep_restructure
    restructure_type_zh: Optional[str] = None
    changes: List[StructureChange] = []  # For deep_restructure
    outline: List[str] = []
    predicted_improvement: int
    explanation: str = ""
    explanation_zh: str


class StructureAnalysisRequest(BaseModel):
    """
    Request for structure analysis
    结构分析请求
    """
    text: str = Field(..., description="Full document text to analyze")
    extract_thesis: bool = Field(True, description="Whether to extract core thesis")


class StructureAnalysisResponse(BaseModel):
    """
    Response for structure analysis
    结构分析响应
    """
    # Basic info
    total_paragraphs: int
    total_sentences: int
    total_words: int
    avg_paragraph_length: float
    paragraph_length_variance: float

    # Scores and levels
    structure_score: int  # 0-100, higher = more AI-like
    risk_level: str  # low, medium, high

    # Paragraph info (abbreviated)
    paragraphs: List[ParagraphInfo] = []

    # Detected patterns
    issues: List[StructureIssue] = []
    break_points: List[BreakPoint] = []

    # Extracted thesis
    core_thesis: Optional[str] = None
    key_arguments: List[str] = []

    # Pattern flags
    has_linear_flow: bool = False
    has_repetitive_pattern: bool = False
    has_uniform_length: bool = False
    has_predictable_order: bool = False

    # Repair options (populated when suggestions requested)
    options: List[StructureOption] = []

    # Messages
    message: str = ""
    message_zh: str = ""


class LogicDiagnosisResponse(BaseModel):
    """
    Response for logic diagnosis card
    逻辑诊断卡响应
    """
    # Flow visualization
    flow_map: List[FlowRelation] = []

    # Structure pattern
    structure_pattern: str  # linear, parallel, nested, circular
    structure_pattern_zh: str
    pattern_description: str
    pattern_description_zh: str

    # Risk areas
    risk_areas: List[RiskArea] = []

    # Recommendation
    recommended_strategy: StructureStrategy
    recommendation_reason: str
    recommendation_reason_zh: str


class DocumentStructureRequest(BaseModel):
    """
    Request to analyze document structure by ID
    按ID分析文档结构的请求
    """
    document_id: str = Field(..., description="Document ID to analyze")
    extract_thesis: bool = Field(True, description="Whether to extract core thesis")
    session_id: Optional[str] = Field(None, description="Session ID to get colloquialism_level for style analysis")


class ParagraphSuggestionRequest(BaseModel):
    """
    Request for single paragraph rewrite suggestion
    单个段落改写建议请求
    """
    paragraph_text: str = Field(..., min_length=10, description="The paragraph text to analyze")
    paragraph_position: str = Field(..., description="Paragraph position like '3.2(1)'")
    ai_risk: Optional[str] = Field(None, description="Already detected AI risk level")
    ai_risk_reason: Optional[str] = Field(None, description="Already detected AI risk reason")
    context_hint: Optional[str] = Field(None, description="Context from previous paragraph or document")


class ParagraphSuggestionResponse(BaseModel):
    """
    Response for single paragraph rewrite suggestion
    单个段落改写建议响应
    """
    paragraph_position: str = Field(..., description="Paragraph position")
    rewrite_suggestion_zh: str = Field(..., description="Structured Chinese rewrite suggestion")
    rewrite_example: Optional[str] = Field(None, description="Optional rewrite example in English")
    ai_risk: str = Field(..., description="AI risk level: high/medium/low")
    ai_risk_reason: str = Field(..., description="Chinese reason for AI risk level")


class ApplyStructureRequest(BaseModel):
    """
    Request to apply a structure strategy
    应用结构策略的请求
    """
    session_id: str = Field(..., description="Session ID")
    strategy: StructureStrategy = Field(..., description="Strategy to apply")
    option_index: int = Field(0, description="Index of the option to apply")


# =============================================================================
# Enhanced Structure Analysis Schemas (Level 1 Enhancement)
# 增强结构分析模式（Level 1增强）
# =============================================================================

class DisruptionLevel(str, Enum):
    """Disruption level enumeration 扰动等级枚举"""
    LIGHT = "light"
    MEDIUM = "medium"
    STRONG = "strong"


class PredictabilityAnalysisRequest(BaseModel):
    """
    Request for structure predictability analysis
    结构预测性分析请求
    """
    text: str = Field(..., description="Full document text to analyze")


class ProgressionAnalysisResult(BaseModel):
    """
    Progression type analysis result
    推进类型分析结果
    """
    progression_type: str  # monotonic, non_monotonic, mixed
    progression_type_zh: str
    forward_transitions: int
    backward_references: int
    conditional_statements: int
    score: int  # 0-100, higher = more AI-like


class FunctionDistributionResult(BaseModel):
    """
    Function distribution analysis result
    功能分布分析结果
    """
    distribution_type: str  # uniform, asymmetric, balanced
    distribution_type_zh: str
    function_counts: Dict[str, int]
    depth_variance: float
    longest_section_ratio: float
    score: int
    asymmetry_opportunities: List[Dict[str, Any]] = []


class ClosureAnalysisResult(BaseModel):
    """
    Closure pattern analysis result
    闭合模式分析结果
    """
    closure_type: str  # strong, moderate, weak, open
    closure_type_zh: str
    has_formulaic_ending: bool
    has_complete_resolution: bool
    open_questions: int
    hedging_in_conclusion: int
    score: int
    detected_patterns: List[str] = []


class LexicalEchoResult(BaseModel):
    """
    Lexical echo analysis result
    词汇回声分析结果
    """
    total_transitions: int
    echo_transitions: int
    explicit_connector_transitions: int
    echo_ratio: float
    score: int
    transition_details: List[Dict[str, Any]] = []


class PredictabilityAnalysisResponse(BaseModel):
    """
    Response for structure predictability analysis
    结构预测性分析响应
    """
    # Overall predictability score
    # 整体预测性分数
    total_score: int = Field(..., description="0-100, higher = more AI-like")
    risk_level: str

    # Dimension scores
    # 维度分数
    progression_analysis: Optional[ProgressionAnalysisResult] = None
    function_distribution: Optional[FunctionDistributionResult] = None
    closure_analysis: Optional[ClosureAnalysisResult] = None
    lexical_echo_analysis: Optional[LexicalEchoResult] = None

    # Recommendations
    # 建议
    recommended_disruption_level: str  # light, medium, strong
    recommended_strategies: List[str] = []
    message: str = ""
    message_zh: str = ""


class DisruptionRestructureRequest(BaseModel):
    """
    Request for disruption-based restructuring
    基于扰动的重组请求
    """
    text: str = Field(..., description="Full document text to restructure")
    disruption_level: DisruptionLevel = Field(
        default=DisruptionLevel.MEDIUM,
        description="Disruption level: light, medium, strong"
    )
    selected_strategies: List[str] = Field(
        default=[],
        description="Specific strategies to apply (empty = use level defaults)"
    )
    extract_thesis: bool = Field(True, description="Whether to extract core thesis")


class DisruptionModification(BaseModel):
    """
    Single modification in disruption restructure
    扰动重组中的单个修改
    """
    strategy: str
    paragraph_index: int
    change_type: str
    original: str
    modified: str
    explanation: str
    explanation_zh: str


class DisruptionStructureChange(BaseModel):
    """
    Structural change in disruption restructure
    扰动重组中的结构变化
    """
    type: str  # reorder, merge, split, insert
    affected_paragraphs: List[int]
    new_position: Optional[int] = None
    description: str
    description_zh: str


class DisruptionRestructureResponse(BaseModel):
    """
    Response for disruption-based restructuring
    基于扰动的重组响应
    """
    disruption_level: str
    applied_strategies: List[str]
    modifications: List[DisruptionModification] = []
    structure_changes: List[DisruptionStructureChange] = []
    new_outline: List[str] = []
    human_features_introduced: List[str] = []
    predicted_score_reduction: int
    overall_explanation: str
    overall_explanation_zh: str


# =============================================================================
# 7-Indicator Structural Risk Card Schemas
# 7指征结构风险卡片模式
# =============================================================================

class StructuralIndicatorResponse(BaseModel):
    """
    Single structural AI indicator for risk card visualization
    用于风险卡片可视化的单个结构AI指征
    """
    id: str  # Indicator ID
    name: str  # English name
    name_zh: str  # Chinese name
    triggered: bool  # Whether this indicator is triggered
    risk_level: int  # 1-3 stars (★★★)
    emoji: str  # Visual emoji
    color: str  # hex color code (#ef4444 red, #22c55e green)
    description: str  # Brief description
    description_zh: str
    details: str = ""  # Specific details for this document
    details_zh: str = ""


class CrossReferenceResult(BaseModel):
    """
    Cross-reference analysis result (7th indicator)
    交叉引用分析结果（第7指征）
    """
    has_cross_references: bool
    cross_reference_count: int
    concept_callbacks: int
    forward_only_ratio: float
    score: int
    detected_references: List[Dict[str, Any]] = []
    core_concepts: List[str] = []


class StructuralRiskCardResponse(BaseModel):
    """
    7-Indicator Structural Risk Card for user visualization
    7指征结构风险卡片用于用户可视化

    Provides at-a-glance view of AI structural patterns with:
    - 7 indicators with emoji and color coding
    - Triggered count and overall risk level
    - One-line summary with emoji
    """
    indicators: List[StructuralIndicatorResponse]
    triggered_count: int  # How many indicators are triggered (0-7)
    overall_risk: str  # low, medium, high
    overall_risk_zh: str
    summary: str  # One-line summary with emoji
    summary_zh: str
    total_score: int  # Combined structure score (0-100)


class RiskCardRequest(BaseModel):
    """
    Request for structural risk card analysis
    结构风险卡片分析请求
    """
    text: str = Field(..., description="Full document text to analyze")


# =============================================================================
# Level 1 Guided Interaction Schemas
# Level 1 指引式交互模式
# =============================================================================

class IssueCategory(str, Enum):
    """Issue category enumeration 问题分类枚举"""
    STRUCTURE = "structure"     # 全文结构问题
    TRANSITION = "transition"   # 段落关系问题


class StructureIssueType(str, Enum):
    """Structure issue type enumeration 结构问题类型枚举"""
    # Structure issues (全文结构问题)
    LINEAR_FLOW = "linear_flow"                     # 线性流程
    UNIFORM_LENGTH = "uniform_length"               # 均匀段落长度
    PREDICTABLE_STRUCTURE = "predictable_structure" # 可预测结构

    # Transition issues (段落关系问题)
    EXPLICIT_CONNECTOR = "explicit_connector"       # 显性连接词
    MISSING_SEMANTIC_ECHO = "missing_semantic_echo" # 缺少语义回声
    LOGIC_GAP = "logic_gap"                         # 逻辑断裂
    PARAGRAPH_TOO_SHORT = "paragraph_too_short"     # 段落过短
    PARAGRAPH_TOO_LONG = "paragraph_too_long"       # 段落过长
    FORMULAIC_OPENING = "formulaic_opening"         # 公式化开头
    WEAK_TRANSITION = "weak_transition"             # 薄弱过渡


class IssueStatus(str, Enum):
    """Issue processing status 问题处理状态"""
    PENDING = "pending"       # 待处理
    EXPANDED = "expanded"     # 已展开
    FIXED = "fixed"           # 已修复
    SKIPPED = "skipped"       # 已跳过


class StructureIssueItem(BaseModel):
    """
    Single structure issue item for list display
    用于列表展示的单个结构问题项
    """
    id: str = Field(..., description="Unique issue ID")
    type: str = Field(..., description="Issue type from StructureIssueType")
    category: str = Field(..., description="Issue category: structure or transition")
    severity: str = Field(..., description="Severity: high, medium, low")
    title_zh: str = Field(..., description="Chinese title for display")
    title_en: str = Field(..., description="English title for display")
    brief_zh: str = Field(..., description="Brief Chinese description")
    brief_en: str = Field("", description="Brief English description")
    affected_positions: List[str] = Field(default=[], description="Affected paragraph positions like ['P2', 'P3(1)']")
    affected_text_preview: str = Field("", description="Preview of affected text (first 100 chars)")
    can_generate_reference: bool = Field(..., description="Whether reference version can be generated")
    status: str = Field(default="pending", description="Processing status")

    # Additional context for expansion
    # 展开时需要的额外上下文
    connector_word: Optional[str] = Field(None, description="For explicit_connector: the connector word")
    word_count: Optional[int] = Field(None, description="For paragraph length issues: word count")
    neighbor_avg: Optional[int] = Field(None, description="For paragraph length issues: neighbor average")


class StructureIssueListRequest(BaseModel):
    """
    Request for structure issue list
    结构问题列表请求
    """
    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(..., alias="documentId", description="Document ID to analyze")
    include_low_severity: bool = Field(default=False, alias="includeLowSeverity", description="Include low severity issues")


class StructureIssueListResponse(BaseModel):
    """
    Response containing categorized structure issues
    包含分类结构问题的响应
    """
    # Categorized issues
    # 分类问题
    structure_issues: List[StructureIssueItem] = Field(
        default=[],
        description="全文结构问题 - Structure issues (displayed first)"
    )
    transition_issues: List[StructureIssueItem] = Field(
        default=[],
        description="段落关系问题 - Transition issues (displayed second)"
    )

    # Summary counts
    # 摘要计数
    total_issues: int = Field(0, description="Total number of issues")
    high_severity_count: int = Field(0, description="Number of high severity issues")
    medium_severity_count: int = Field(0, description="Number of medium severity issues")
    low_severity_count: int = Field(0, description="Number of low severity issues")

    # Document context
    # 文档上下文
    document_id: str = Field(..., description="Document ID")
    structure_score: int = Field(0, description="Overall structure score (0-100)")
    risk_level: str = Field("low", description="Overall risk level")


class IssueGuidanceRequest(BaseModel):
    """
    Request for detailed guidance on a specific issue
    获取特定问题详细指引的请求
    """
    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(..., alias="documentId", description="Document ID")
    issue_id: str = Field(..., alias="issueId", description="Issue ID from issue list")
    issue_type: str = Field(..., alias="issueType", description="Issue type")
    affected_positions: List[str] = Field(default=[], alias="affectedPositions", description="Affected positions")

    # Optional context for better guidance
    # 可选的上下文信息以获得更好的指引
    affected_text: Optional[str] = Field(None, alias="affectedText", description="The affected text (if not fetching from DB)")
    prev_paragraph: Optional[str] = Field(None, alias="prevParagraph", description="Previous paragraph text")
    next_paragraph: Optional[str] = Field(None, alias="nextParagraph", description="Next paragraph text")
    connector_word: Optional[str] = Field(None, alias="connectorWord", description="For explicit_connector issues")


class KeyConcepts(BaseModel):
    """
    Key concepts extracted for semantic echo
    用于语义回声的关键概念
    """
    from_prev: List[str] = Field(default=[], description="Key concepts from previous paragraph")
    from_next: List[str] = Field(default=[], description="Key concepts from next paragraph")


class IssueGuidanceResponse(BaseModel):
    """
    Response containing detailed guidance for an issue
    包含问题详细指引的响应
    """
    issue_id: str = Field(..., description="Issue ID")
    issue_type: str = Field(..., description="Issue type")

    # Detailed guidance
    # 详细指引
    guidance_zh: str = Field(..., description="Detailed Chinese guidance with sections")
    guidance_en: str = Field("", description="Brief English summary")

    # Reference version (if applicable)
    # 参考版本（如果适用）
    reference_version: Optional[str] = Field(None, description="Suggested rewritten text")
    reference_explanation_zh: Optional[str] = Field(None, description="Explanation of the reference version")

    # If no reference
    # 如果没有参考版本
    why_no_reference: Optional[str] = Field(None, description="Explanation of why no reference is provided")

    # Context
    # 上下文
    affected_text: str = Field("", description="The original affected text")
    key_concepts: KeyConcepts = Field(default_factory=KeyConcepts, description="Key concepts for semantic echo")

    # Metadata
    # 元数据
    confidence: float = Field(0.8, description="Confidence score 0-1")
    can_generate_reference: bool = Field(True, description="Whether reference was/could be generated")


class ApplyStructureFixRequest(BaseModel):
    """
    Request to apply a structure fix
    应用结构修复的请求
    """
    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(..., alias="documentId", description="Document ID")
    issue_id: str = Field(..., alias="issueId", description="Issue ID")
    fix_type: str = Field(..., alias="fixType", description="Fix type: use_reference, custom, skip, mark_done")
    custom_text: Optional[str] = Field(None, alias="customText", description="Custom text if fix_type is 'custom'")
    affected_positions: List[str] = Field(default=[], alias="affectedPositions", description="Affected positions")


class ApplyStructureFixResponse(BaseModel):
    """
    Response after applying a structure fix
    应用结构修复后的响应
    """
    success: bool = Field(..., description="Whether the fix was applied successfully")
    issue_id: str = Field(..., description="Issue ID")
    new_status: str = Field(..., description="New status of the issue")
    message: str = Field("", description="Status message")
    message_zh: str = Field("", description="Chinese status message")

    # If fix was applied, provide the updated text
    # 如果应用了修复，提供更新后的文本
    updated_text: Optional[str] = Field(None, description="The updated text after fix")


class ReorderChange(BaseModel):
    """
    Single reorder change in paragraph reordering
    段落重排中的单个变更
    """
    action: str = Field("move", description="Action type: move")
    paragraph_index: int = Field(..., description="Original paragraph index")
    from_position: int = Field(..., description="Original position in order")
    to_position: int = Field(..., description="New position in order")
    paragraph_summary: str = Field("", description="Brief summary of the paragraph")
    reason_zh: str = Field(..., description="Chinese reason for this change")
    reason_en: str = Field("", description="English reason for this change")


class ReorderSuggestionRequest(BaseModel):
    """
    Request for paragraph reorder suggestion
    段落重排建议请求
    """
    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(..., alias="documentId", description="Document ID")


class ReorderSuggestionResponse(BaseModel):
    """
    Response containing paragraph reorder suggestion
    包含段落重排建议的响应
    """
    # Order information
    # 顺序信息
    current_order: List[int] = Field(..., description="Current paragraph order (indices)")
    suggested_order: List[int] = Field(..., description="Suggested new order (indices)")

    # Changes
    # 变更
    changes: List[ReorderChange] = Field(default=[], description="List of specific changes")

    # Guidance
    # 指引
    overall_guidance_zh: str = Field("", description="Overall Chinese guidance")
    warnings_zh: List[str] = Field(default=[], description="Chinese warnings about the reorder")
    preview_flow_zh: str = Field("", description="Preview of new structure flow")

    # Estimates
    # 预估
    estimated_improvement: int = Field(0, description="Estimated score improvement")
    confidence: float = Field(0.8, description="Confidence score 0-1")


# =============================================================================
# Issue-Specific Suggestion Schemas (Step 1-1 Click-to-Expand)
# 针对特定问题的建议模式（Step 1-1 点击展开）
# =============================================================================

class IssueSuggestionStrategy(BaseModel):
    """
    A single strategy for addressing a structure issue
    解决结构问题的单个策略
    """
    name_zh: str = Field(..., description="Chinese name of the strategy")
    description_zh: str = Field(..., description="Detailed Chinese description with steps")
    example_before: Optional[str] = Field(None, description="Example before modification")
    example_after: Optional[str] = Field(None, description="Example after modification")
    difficulty: str = Field("medium", description="Difficulty level: easy/medium/hard")
    effectiveness: str = Field("medium", description="Effectiveness: high/medium/low")


class IssueSuggestionRequest(BaseModel):
    """
    Request for issue-specific suggestion
    针对特定问题的建议请求
    """
    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(..., alias="documentId", description="Document ID")
    issue_type: str = Field(..., alias="issueType", description="Type of the structure issue")
    issue_description: str = Field("", alias="issueDescription", description="English description")
    issue_description_zh: str = Field(..., alias="issueDescriptionZh", description="Chinese description")
    severity: str = Field("medium", description="Issue severity: high/medium/low")
    affected_positions: List[str] = Field(default=[], alias="affectedPositions", description="Affected positions")
    quick_mode: bool = Field(False, alias="quickMode", description="Use quick mode for faster response")


class IssueSuggestionResponse(BaseModel):
    """
    Response containing issue-specific suggestions
    包含针对特定问题建议的响应
    """
    diagnosis_zh: str = Field(..., description="Detailed Chinese diagnosis")
    strategies: List[IssueSuggestionStrategy] = Field(default=[], description="List of modification strategies")
    modification_prompt: str = Field("", description="Copy-pasteable prompt for other AI tools")
    priority_tips_zh: str = Field("", description="Prioritized tips in Chinese")
    caution_zh: str = Field("", description="Cautions to maintain academic quality")
    quick_fix_zh: Optional[str] = Field(None, description="Quick fix suggestion")
    estimated_improvement: Optional[int] = Field(None, description="Estimated score improvement")


# =============================================================================
# Merge Modify Schemas (Step 1-1 Combined Issue Modification)
# 合并修改模式（Step 1-1 多问题合并修改）
# =============================================================================

class SelectedIssue(BaseModel):
    """
    A single selected issue for merge modification
    合并修改中选择的单个问题
    """
    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(..., description="Issue type identifier")
    description: str = Field("", description="English description")
    description_zh: str = Field(..., alias="descriptionZh", description="Chinese description")
    severity: str = Field("medium", description="Severity: high/medium/low")
    affected_positions: List[str] = Field(default=[], alias="affectedPositions", description="Affected positions")


class MergeModifyRequest(BaseModel):
    """
    Request for merge modification (generate prompt or apply directly)
    合并修改请求（生成提示词或直接修改）

    User selects multiple issues and can optionally provide notes.
    用户选择多个问题，可选择性地提供注意事项。
    """
    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(..., alias="documentId", description="Document ID")
    session_id: Optional[str] = Field(None, alias="sessionId", description="Session ID for colloquialism level")
    selected_issues: List[SelectedIssue] = Field(..., alias="selectedIssues", description="List of selected issues")
    user_notes: Optional[str] = Field(None, alias="userNotes", description="User's optional notes/requirements")
    mode: str = Field("prompt", description="Mode: 'prompt' (generate prompt) or 'apply' (direct modification)")


class MergeModifyPromptResponse(BaseModel):
    """
    Response containing generated modification prompt
    包含生成的修改提示词的响应
    """
    prompt: str = Field(..., description="Generated modification prompt for user to copy")
    prompt_zh: str = Field(..., description="Prompt description in Chinese")
    issues_summary_zh: str = Field("", description="Summary of selected issues in Chinese")
    colloquialism_level: Optional[int] = Field(None, description="Target colloquialism level (0-10)")
    estimated_changes: int = Field(0, description="Estimated number of changes")


class MergeModifyApplyResponse(BaseModel):
    """
    Response containing AI-modified document
    包含AI修改后文档的响应
    """
    modified_text: str = Field(..., description="Modified document text")
    changes_summary_zh: str = Field("", description="Summary of changes in Chinese")
    changes_count: int = Field(0, description="Number of changes made")
    issues_addressed: List[str] = Field(default=[], description="List of issue types addressed")
    remaining_attempts: int = Field(3, description="Remaining regeneration attempts")
    colloquialism_level: Optional[int] = Field(None, description="Target colloquialism level used")


# =============================================================================
# Paragraph Length Analysis Schemas (Step 1-2 Two-Phase Enhancement)
# 段落长度分析模式（Step 1-2 两阶段增强）
# =============================================================================

class ParagraphLengthStrategyItem(BaseModel):
    """
    Single strategy suggestion for paragraph length optimization
    段落长度优化的单个策略建议
    """
    model_config = ConfigDict(populate_by_name=True)

    strategy_type: str = Field(..., alias="strategyType", description="merge|expand|split|compress")
    target_positions: List[str] = Field(..., alias="targetPositions", description="Affected paragraph positions")
    description: str = Field(..., description="Strategy description in English")
    description_zh: str = Field(..., alias="descriptionZh", description="策略描述")
    reason: str = Field(..., description="Why this strategy is suggested")
    reason_zh: str = Field(..., alias="reasonZh", description="建议原因")
    priority: int = Field(..., description="Priority 1-5, lower = more important")
    # For expand strategy, what kind of content to add
    # 对于扩展策略，建议添加什么类型的内容
    expand_suggestion: Optional[str] = Field(None, alias="expandSuggestion", description="Suggestion for what to expand")
    expand_suggestion_zh: Optional[str] = Field(None, alias="expandSuggestionZh", description="扩展建议")
    # For merge strategy, semantic relationship between paragraphs
    # 对于合并策略，段落间的语义关系
    semantic_relation: Optional[str] = Field(None, alias="semanticRelation", description="Semantic relationship for merge")
    semantic_relation_zh: Optional[str] = Field(None, alias="semanticRelationZh", description="合并的语义关系说明")
    # For split/compress strategy, what aspects to separate or remove
    # 对于拆分/压缩策略，应分离或删除哪些方面
    split_points: Optional[List[str]] = Field(None, alias="splitPoints", description="Points where to split")
    split_points_zh: Optional[List[str]] = Field(None, alias="splitPointsZh", description="建议拆分点")


class ParagraphLengthInfo(BaseModel):
    """
    Information about a single paragraph's length
    单个段落长度信息
    """
    model_config = ConfigDict(populate_by_name=True)

    position: str = Field(..., description="Paragraph position e.g., '1(2)'")
    word_count: int = Field(..., alias="wordCount", description="Number of words in paragraph")
    section: str = Field(..., description="Section number or name")
    summary: str = Field("", description="Paragraph summary")
    summary_zh: str = Field("", alias="summaryZh", description="段落摘要")


class ParagraphLengthAnalysisRequest(BaseModel):
    """
    Request for Phase 1 paragraph length analysis
    第一阶段段落长度分析请求
    """
    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(..., alias="documentId", description="Document ID")


class ParagraphLengthAnalysisResponse(BaseModel):
    """
    Response from Phase 1 paragraph length analysis
    第一阶段段落长度分析响应

    Contains statistics and strategy suggestions for the user to select.
    包含统计数据和供用户选择的策略建议。
    """
    model_config = ConfigDict(populate_by_name=True)

    paragraph_lengths: List[ParagraphLengthInfo] = Field(..., alias="paragraphLengths", description="List of paragraph length info")
    mean_length: float = Field(..., alias="meanLength", description="Mean paragraph length in words")
    std_dev: float = Field(..., alias="stdDev", description="Standard deviation of paragraph lengths")
    cv: float = Field(..., description="Coefficient of variation (std_dev / mean)")
    is_uniform: bool = Field(..., alias="isUniform", description="Whether lengths are too uniform (CV < 0.3)")
    human_like_cv_target: float = Field(0.4, alias="humanLikeCvTarget", description="Target CV for human-like distribution")
    strategies: List[ParagraphLengthStrategyItem] = Field(..., description="Suggested strategies")
    summary: str = Field(..., description="Summary of analysis in English")
    summary_zh: str = Field(..., alias="summaryZh", description="分析摘要")


class SelectedStrategy(BaseModel):
    """
    User-selected strategy with optional expand text
    用户选择的策略（可选扩展文本）
    """
    model_config = ConfigDict(populate_by_name=True)

    strategy_type: str = Field(..., alias="strategyType", description="merge|expand|split")
    target_positions: List[str] = Field(..., alias="targetPositions", description="Affected paragraph positions")
    # For expand strategy, user-provided new content
    # 对于扩展策略，用户提供的新内容
    expand_text: Optional[str] = Field(None, alias="expandText", description="User-provided text for expand strategy")


class ApplyParagraphStrategiesRequest(BaseModel):
    """
    Request for Phase 2: Apply selected paragraph strategies
    第二阶段请求：应用选中的段落策略
    """
    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(..., alias="documentId", description="Document ID")
    session_id: Optional[str] = Field(None, alias="sessionId", description="Session ID for colloquialism level")
    selected_strategies: List[SelectedStrategy] = Field(..., alias="selectedStrategies", description="User-selected strategies")


class ApplyParagraphStrategiesResponse(BaseModel):
    """
    Response from Phase 2: Applied paragraph strategies
    第二阶段响应：已应用的段落策略
    """
    model_config = ConfigDict(populate_by_name=True)

    modified_text: str = Field(..., alias="modifiedText", description="Modified document text")
    changes_summary_zh: str = Field("", alias="changesSummaryZh", description="Summary of changes in Chinese")
    strategies_applied: int = Field(..., alias="strategiesApplied", description="Number of strategies applied")
    new_cv: Optional[float] = Field(None, alias="newCv", description="New CV after modifications")


# =============================================================================
# Authentication Schemas (Dual-Mode System)
# 认证模式（双模式系统）
# =============================================================================

class SystemModeType(str, Enum):
    """System mode enumeration 系统模式枚举"""
    DEBUG = "debug"
    OPERATIONAL = "operational"


class SendCodeRequest(BaseModel):
    """
    Send verification code request
    发送验证码请求
    """
    phone: str = Field(..., min_length=11, max_length=11, description="Phone number")


class LoginRequest(BaseModel):
    """
    Phone login request
    手机登录请求
    """
    phone: str = Field(..., min_length=11, max_length=11, description="Phone number")
    code: str = Field(..., min_length=4, max_length=6, description="Verification code")


class LoginResponse(BaseModel):
    """
    Login response
    登录响应
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: "UserProfile" = Field(..., description="User profile")


class UserProfile(BaseModel):
    """
    User profile information
    用户信息
    """
    user_id: str = Field(..., description="User ID")
    phone: str = Field(..., description="Masked phone number")
    nickname: Optional[str] = Field(None, description="User nickname")
    is_debug: bool = Field(default=False, description="Whether this is a debug user")
    created_at: datetime = Field(..., description="Account creation time")


class ModeResponse(BaseModel):
    """
    System mode response
    系统模式响应
    """
    mode: SystemModeType = Field(..., description="Current system mode")
    is_debug: bool = Field(..., description="Whether in debug mode")
    features: "FeatureFlags" = Field(..., description="Feature flags")
    pricing: "PricingInfo" = Field(..., description="Pricing information")


class FeatureFlags(BaseModel):
    """
    Feature flags based on mode
    基于模式的功能开关
    """
    require_login: bool = Field(..., description="Whether login is required")
    require_payment: bool = Field(..., description="Whether payment is required")
    show_pricing: bool = Field(..., description="Whether to show pricing")


class PricingInfo(BaseModel):
    """
    Pricing information
    定价信息
    """
    price_per_unit: float = Field(..., description="Price per 100 words (RMB)")
    minimum_charge: float = Field(..., description="Minimum charge (RMB)")
    currency: str = Field(default="CNY", description="Currency code")


# =============================================================================
# Payment Schemas (Dual-Mode System)
# 支付模式（双模式系统）
# =============================================================================

class TaskStatus(str, Enum):
    """Task status enumeration 任务状态枚举"""
    CREATED = "created"
    QUOTED = "quoted"
    PAYING = "paying"
    PAID = "paid"
    PROCESSING = "processing"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"


class PaymentStatusType(str, Enum):
    """Payment status enumeration 支付状态枚举"""
    UNPAID = "unpaid"
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class CreateTaskRequest(BaseModel):
    """
    Create billing task request
    创建计费任务请求
    """
    document_id: str = Field(..., description="Document ID to create task for")


class TaskResponse(BaseModel):
    """
    Task information response
    任务信息响应
    """
    task_id: str = Field(..., description="Task ID")
    document_id: str = Field(..., description="Associated document ID")
    word_count_raw: int = Field(0, description="Raw word count")
    word_count_billable: int = Field(0, description="Billable word count (excluding references)")
    billable_units: int = Field(0, description="Number of billing units (100 words each)")
    price_calculated: float = Field(0.0, description="Calculated price")
    price_final: float = Field(0.0, description="Final price (after minimum charge)")
    is_minimum_charge: bool = Field(False, description="Whether minimum charge applied")
    status: str = Field(..., description="Task status")
    payment_status: str = Field(..., description="Payment status")
    is_debug_mode: bool = Field(False, description="Whether in debug mode")


class QuoteResponse(BaseModel):
    """
    Price quote response
    报价响应
    """
    task_id: str = Field(..., description="Task ID")
    word_count_raw: int = Field(..., description="Raw word count")
    word_count_billable: int = Field(..., description="Billable word count")
    billable_units: int = Field(..., description="Billing units")
    calculated_price: float = Field(..., description="Calculated price")
    final_price: float = Field(..., description="Final price")
    is_minimum_charge: bool = Field(..., description="Whether minimum charge applied")
    minimum_charge: float = Field(..., description="Minimum charge amount")
    is_debug_mode: bool = Field(..., description="Whether in debug mode")
    payment_required: bool = Field(..., description="Whether payment is required")


class PayRequest(BaseModel):
    """
    Payment initiation request
    发起支付请求
    """
    task_id: str = Field(..., description="Task ID to pay for")


class PayResponse(BaseModel):
    """
    Payment initiation response
    发起支付响应
    """
    task_id: str = Field(..., description="Task ID")
    platform_order_id: str = Field(..., description="Platform order ID")
    payment_url: Optional[str] = Field(None, description="Payment page URL")
    qr_code_url: Optional[str] = Field(None, description="QR code URL for payment")
    amount: float = Field(..., description="Payment amount")
    expires_at: Optional[datetime] = Field(None, description="Payment expiration time")
    is_debug_mode: bool = Field(False, description="Whether in debug mode")
    auto_paid: bool = Field(False, description="Whether auto-paid in debug mode")


class PaymentStatusResponse(BaseModel):
    """
    Payment status check response
    支付状态查询响应
    """
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    payment_status: str = Field(..., description="Payment status")
    paid_at: Optional[datetime] = Field(None, description="Payment completion time")
    can_process: bool = Field(..., description="Whether processing can start")


class PaymentCallbackRequest(BaseModel):
    """
    Payment callback from platform
    平台支付回调
    """
    order_id: str = Field(..., description="Platform order ID")
    status: str = Field(..., description="Payment status")
    paid_at: Optional[datetime] = Field(None, description="Payment time")
    amount: float = Field(..., description="Paid amount")
    signature: str = Field(..., description="HMAC signature for verification")
