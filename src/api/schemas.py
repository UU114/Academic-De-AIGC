"""
Pydantic schemas for API request/response validation
API请求/响应验证的Pydantic模式
"""

from pydantic import BaseModel, Field
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
    """
    sentence: str = Field(..., min_length=1, description="Sentence to humanize")
    issues: List[Dict[str, Any]] = Field(default=[], description="Detected issues")
    locked_terms: List[str] = Field(default=[], description="Terms to protect")
    colloquialism_level: int = Field(default=4, ge=0, le=10, description="Colloquialism level 0-10")
    target_lang: str = Field(default="zh", description="Target language for explanations")


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
    total_sentences: int
    processed: int
    progress_percent: float
    created_at: datetime
    completed_at: Optional[datetime] = None


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
