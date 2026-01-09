"""
Unified Schemas for 5-Layer Analysis API
5层分析API的统一模式

Provides standardized request/response models for:
- Layer 5: Document analysis
- Layer 4: Section analysis
- Layer 3: Paragraph analysis
- Layer 2: Sentence analysis
- Layer 1: Lexical analysis
"""

from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# =============================================================================
# Enums
# =============================================================================

class LayerLevel(str, Enum):
    """Layer levels in the detection hierarchy"""
    DOCUMENT = "document"   # Layer 5
    SECTION = "section"     # Layer 4
    PARAGRAPH = "paragraph" # Layer 3
    SENTENCE = "sentence"   # Layer 2
    LEXICAL = "lexical"     # Layer 1


class RiskLevel(str, Enum):
    """Risk level classification"""
    SAFE = "safe"      # 0-9: No risk, clearly human-like
    LOW = "low"        # 10-29: Low risk, slight AI tendency
    MEDIUM = "medium"  # 30-59: Medium risk, needs attention
    HIGH = "high"      # 60-100: High risk, strong AI features


class IndicatorStatus(str, Enum):
    """Indicator status classification / 指标状态分类"""
    AI_LIKE = "ai_like"           # Value exceeds AI threshold
    BORDERLINE = "borderline"     # Value between thresholds
    HUMAN_LIKE = "human_like"     # Value below human threshold


class IssueSeverity(str, Enum):
    """Issue severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# =============================================================================
# Base Models
# =============================================================================

class DetectionIssue(BaseModel):
    """
    Unified issue model for all layers
    所有层级的统一问题模型
    """
    type: str = Field(..., description="Issue type identifier")
    description: str = Field(..., description="English description")
    description_zh: str = Field(..., description="Chinese description")
    severity: IssueSeverity = Field(..., description="Issue severity")
    layer: LayerLevel = Field(..., description="Which layer detected this")
    position: Optional[str] = Field(None, description="Position reference")
    suggestion: str = Field("", description="Suggestion for fix")
    suggestion_zh: str = Field("", description="Chinese suggestion")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


# =============================================================================
# Unified Substep Risk Assessment Models
# 统一的子步骤风险评估模型
# =============================================================================

class DimensionScore(BaseModel):
    """
    Score for a single dimension/indicator within a substep
    子步骤内单个维度/指标的分数

    Based on plan: Each indicator has AI/human thresholds and contributes to risk score
    基于计划：每个指标有AI/人类阈值并贡献风险分数
    """
    dimension_id: str = Field(..., description="Unique dimension identifier, e.g., 'symmetry_score'")
    dimension_name: str = Field(..., description="English name, e.g., 'Symmetry Score'")
    dimension_name_zh: str = Field(..., description="Chinese name, e.g., '对称性分数'")
    value: float = Field(..., description="Current measured value")
    threshold_ai: float = Field(..., description="AI threshold (high risk if value > this)")
    threshold_human: float = Field(..., description="Human threshold (low risk if value < this)")
    weight: float = Field(default=1.0, ge=0, le=1, description="Weight for this dimension (0-1)")
    risk_contribution: int = Field(default=0, ge=0, le=100, description="Contribution to total risk score")
    status: IndicatorStatus = Field(default=IndicatorStatus.BORDERLINE, description="Current status based on thresholds")
    description: str = Field(default="", description="English description of what this measures")
    description_zh: str = Field(default="", description="Chinese description")


class SubstepRiskAssessment(BaseModel):
    """
    Unified risk assessment model for each substep
    每个子步骤的统一风险评估模型

    This is the core model for the multi-layer risk assessment framework.
    Based on plan Section 3.1: Standard risk output structure for each substep

    这是多层级风险评估框架的核心模型。
    基于计划第3.1节：每个子步骤的标准风险输出结构

    Risk Level Thresholds (Section 3.2):
    - SAFE (0-9): Clear human features / 明显人类特征
    - LOW (10-29): Slight AI tendency / 轻微AI倾向
    - MEDIUM (30-59): Needs attention / 需要关注
    - HIGH (60-100): Strong AI features / 强AI特征
    """
    # Identification / 标识
    substep_id: str = Field(..., description="Substep identifier, e.g., 'step1_1', 'step2_3'")
    substep_name: str = Field(..., description="English name, e.g., 'Structure Framework Analysis'")
    substep_name_zh: str = Field(..., description="Chinese name, e.g., '结构框架分析'")
    layer: LayerLevel = Field(..., description="Which layer this substep belongs to")

    # Risk Assessment / 风险评估
    risk_score: int = Field(..., ge=0, le=100, description="Overall risk score 0-100")
    risk_level: RiskLevel = Field(..., description="Risk level classification")

    # Dimension Scores / 维度分数
    dimension_scores: Dict[str, DimensionScore] = Field(
        default_factory=dict,
        description="Detailed scores for each dimension/indicator"
    )

    # Issues and Recommendations / 问题和建议
    issues: List[DetectionIssue] = Field(default_factory=list, description="Detected issues")
    recommendations: List[str] = Field(default_factory=list, description="English recommendations")
    recommendations_zh: List[str] = Field(default_factory=list, description="Chinese recommendations")

    # Processing Info / 处理信息
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")

    # Human Feature Indicators / 人类特征指标
    human_features_detected: List[str] = Field(
        default_factory=list,
        description="List of human-like features detected (reduce risk score)"
    )
    human_features_detected_zh: List[str] = Field(
        default_factory=list,
        description="Chinese description of human features"
    )


class LayerRiskSummary(BaseModel):
    """
    Summary of risk assessment for an entire layer
    整个层级的风险评估汇总

    Aggregates substep scores using layer weights from plan Section 8.1
    使用计划第8.1节的层级权重聚合子步骤分数
    """
    layer: LayerLevel = Field(..., description="Layer identifier")
    layer_name: str = Field(..., description="English layer name")
    layer_name_zh: str = Field(..., description="Chinese layer name")

    # Aggregated Risk / 聚合风险
    layer_risk_score: int = Field(..., ge=0, le=100, description="Aggregated layer risk score")
    layer_risk_level: RiskLevel = Field(..., description="Layer risk level")

    # Substep Results / 子步骤结果
    substep_assessments: List[SubstepRiskAssessment] = Field(
        default_factory=list,
        description="Risk assessments for each substep in this layer"
    )

    # Summary Statistics / 汇总统计
    total_issues: int = Field(default=0, description="Total issues detected in this layer")
    high_risk_substeps: List[str] = Field(default_factory=list, description="IDs of high-risk substeps")

    # Key Indicators Summary / 关键指标汇总
    key_indicators: Dict[str, float] = Field(
        default_factory=dict,
        description="Key indicator values for this layer (e.g., burstiness, subject_diversity)"
    )


class GlobalRiskAssessment(BaseModel):
    """
    Global risk assessment across all layers
    跨所有层级的全局风险评估

    Aggregates layer scores using global weights from plan Section 8.1:
    - Document (Layer 5): 15%
    - Section (Layer 4): 20%
    - Paragraph (Layer 3): 25%
    - Sentence (Layer 2): 25%
    - Lexical (Layer 1): 15%
    """
    # Global Risk / 全局风险
    global_risk_score: int = Field(..., ge=0, le=100, description="Global aggregated risk score")
    global_risk_level: RiskLevel = Field(..., description="Global risk level")

    # Layer Summaries / 层级汇总
    layer_summaries: Dict[str, LayerRiskSummary] = Field(
        default_factory=dict,
        description="Risk summaries for each layer"
    )

    # Layer Weights Used / 使用的层级权重
    layer_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "document": 0.15,
            "section": 0.20,
            "paragraph": 0.25,
            "sentence": 0.25,
            "lexical": 0.15
        },
        description="Weights used for layer aggregation"
    )

    # Top Issues Across All Layers / 所有层级的最高优先问题
    priority_issues: List[DetectionIssue] = Field(
        default_factory=list,
        description="Top priority issues across all layers"
    )

    # Overall Recommendations / 整体建议
    overall_recommendations: List[str] = Field(default_factory=list)
    overall_recommendations_zh: List[str] = Field(default_factory=list)

    # Processing Info / 处理信息
    total_processing_time_ms: int = Field(default=0)
    analyzed_layers: List[LayerLevel] = Field(default_factory=list)


class LayerAnalysisResult(BaseModel):
    """
    Unified result model for all layer analyses
    所有层级分析的统一结果模型
    """
    layer: LayerLevel = Field(..., description="Layer that produced this result")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score 0-100")
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    issues: List[DetectionIssue] = Field(default_factory=list, description="Detected issues")
    recommendations: List[str] = Field(default_factory=list, description="English recommendations")
    recommendations_zh: List[str] = Field(default_factory=list, description="Chinese recommendations")
    details: Dict[str, Any] = Field(default_factory=dict, description="Layer-specific details")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


# =============================================================================
# Request Models
# =============================================================================

class BaseAnalysisRequest(BaseModel):
    """Base request model for all analysis endpoints"""
    text: str = Field(..., min_length=1, description="Text to analyze")
    include_recommendations: bool = Field(default=True, description="Include recommendations")


class DocumentAnalysisRequest(BaseAnalysisRequest):
    """
    Request for Layer 5: Document analysis
    第5层文档分析请求
    """
    include_style_analysis: bool = Field(default=True, description="Include style analysis")


class SectionAnalysisRequest(BaseModel):
    """
    Request for Layer 4: Section analysis
    第4层章节分析请求

    Accepts either raw text or pre-split paragraphs.
    接受原始文本或已分割的段落列表。
    """
    text: Optional[str] = Field(default=None, min_length=1, description="Raw text to analyze (will be split into paragraphs)")
    paragraphs: Optional[List[str]] = Field(default=None, description="List of paragraphs (alternative to text)")
    document_context: Optional[Dict[str, Any]] = Field(default=None, description="Context from Layer 5")

    @model_validator(mode='after')
    def validate_input(self):
        """Ensure either text or paragraphs is provided"""
        if not self.text and not self.paragraphs:
            raise ValueError('Either text or paragraphs must be provided')
        return self


class ParagraphAnalysisRequest(BaseModel):
    """
    Request for Layer 3: Paragraph analysis
    第3层段落分析请求

    Accepts either raw text or pre-split paragraphs.
    接受原始文本或已分割的段落列表。
    """
    text: Optional[str] = Field(default=None, min_length=1, description="Raw text to analyze")
    paragraphs: Optional[List[str]] = Field(default=None, description="List of paragraphs")
    paragraph_roles: Optional[List[str]] = Field(default=None, description="Pre-detected paragraph roles")
    section_context: Optional[Dict[str, Any]] = Field(default=None, description="Context from Layer 4")

    @model_validator(mode='after')
    def validate_input(self):
        """Ensure either text or paragraphs is provided"""
        if not self.text and not self.paragraphs:
            raise ValueError('Either text or paragraphs must be provided')
        return self


class SentenceAnalysisRequest(BaseModel):
    """
    Request for Layer 2: Sentence analysis
    第2层句子分析请求

    **IMPORTANT**: Includes paragraph context for context-aware analysis
    **重要**: 包含段落上下文用于上下文感知分析

    Accepts either raw text or pre-split paragraphs.
    接受原始文本或已分割的段落列表。
    """
    text: Optional[str] = Field(default=None, min_length=1, description="Raw text to analyze")
    paragraphs: Optional[List[str]] = Field(default=None, description="List of paragraphs")
    paragraph_roles: Optional[List[str]] = Field(default=None, description="Paragraph roles from Layer 3")
    paragraph_context: Optional[Dict[str, Any]] = Field(default=None, description="Context from Layer 3")

    @model_validator(mode='after')
    def validate_input(self):
        """Ensure either text or paragraphs is provided"""
        if not self.text and not self.paragraphs:
            raise ValueError('Either text or paragraphs must be provided')
        return self


class LexicalAnalysisRequest(BaseModel):
    """
    Request for Layer 1: Lexical analysis
    第1层词汇分析请求
    """
    text: str = Field(..., min_length=1, description="Text to analyze")
    sentences: Optional[List[str]] = Field(None, description="Pre-segmented sentences")
    sentence_context: Optional[Dict[str, Any]] = Field(None, description="Context from Layer 2")


class PipelineAnalysisRequest(BaseModel):
    """
    Request for full pipeline analysis (all layers)
    全流水线分析请求（所有层级）
    """
    text: str = Field(..., min_length=1, description="Full document text")
    layers: List[LayerLevel] = Field(
        default=[LayerLevel.DOCUMENT, LayerLevel.SECTION, LayerLevel.PARAGRAPH, LayerLevel.SENTENCE, LayerLevel.LEXICAL],
        description="Layers to analyze (in order)"
    )
    stop_on_low_risk: bool = Field(default=False, description="Stop if layer returns low risk")
    include_context_passing: bool = Field(default=True, description="Pass context between layers")


# =============================================================================
# Response Models
# =============================================================================

class DocumentSection(BaseModel):
    """Document section info for frontend display"""
    index: int = Field(..., description="Section index")
    role: str = Field(..., description="Section role")
    title: Optional[str] = Field(None, description="Section title if detected")
    paragraph_count: int = Field(0, alias="paragraphCount", description="Number of paragraphs in section")
    word_count: int = Field(0, alias="wordCount", description="Word count in section")

    class Config:
        populate_by_name = True


class DocumentAnalysisResponse(LayerAnalysisResult):
    """
    Response for Layer 5: Document analysis
    第5层文档分析响应
    """
    layer: LayerLevel = LayerLevel.DOCUMENT
    structure: Optional[Dict[str, Any]] = Field(None, description="Document structure info")
    predictability_score: Optional[Dict[str, Any]] = Field(None, description="Structure predictability scores")
    paragraph_count: int = Field(0, description="Number of paragraphs")
    word_count: int = Field(0, description="Total word count")
    # Fields expected by frontend / 前端期望的字段
    structure_score: int = Field(0, description="Structure predictability total score")
    structure_pattern: str = Field("unknown", description="Detected structure pattern")
    sections: List[DocumentSection] = Field(default_factory=list, description="Detected document sections")
    global_risk_factors: List[str] = Field(default_factory=list, description="Global risk factors")
    predictability_scores: Dict[str, int] = Field(default_factory=dict, description="Predictability dimension scores")


class SectionAnalysisResponse(LayerAnalysisResult):
    """
    Response for Layer 4: Section analysis
    第4层章节分析响应
    """
    layer: LayerLevel = LayerLevel.SECTION
    section_details: List[Dict[str, Any]] = Field(default_factory=list, description="Detected sections with details")
    section_count: int = Field(0, description="Number of sections")
    logic_flow_score: int = Field(0, description="Logic flow score")
    transition_quality: int = Field(0, description="Transition quality score")
    logic_flow: Optional[Dict[str, Any]] = Field(None, description="Section logic flow analysis")
    transitions: List[Dict[str, Any]] = Field(default_factory=list, description="Section transitions")
    length_distribution: Optional[Dict[str, Any]] = Field(None, description="Length distribution analysis")


class ParagraphAnalysisResponse(LayerAnalysisResult):
    """
    Response for Layer 3: Paragraph analysis
    第3层段落分析响应
    """
    layer: LayerLevel = LayerLevel.PARAGRAPH
    paragraphs: List[str] = Field(default_factory=list, description="Filtered paragraphs (headers/keywords removed)")
    paragraph_roles: List[str] = Field(default_factory=list, description="Detected roles for each paragraph")
    coherence_scores: List[float] = Field(default_factory=list, description="Coherence score per paragraph")
    anchor_densities: List[float] = Field(default_factory=list, description="Anchor density per paragraph")
    sentence_length_cvs: List[float] = Field(default_factory=list, description="Sentence length CV per paragraph")
    low_burstiness_paragraphs: List[int] = Field(default_factory=list, description="Indices of low burstiness paragraphs")


class SentenceWithContext(BaseModel):
    """
    Sentence with paragraph context for rewriting
    带段落上下文的句子（用于改写）
    """
    sentence_text: str = Field(..., description="The sentence text")
    sentence_index: int = Field(..., description="Global sentence index")
    paragraph_text: str = Field(..., description="Full paragraph containing this sentence")
    paragraph_index: int = Field(..., description="Index of containing paragraph")
    paragraph_role: str = Field("body", description="Role of the paragraph")
    position_in_paragraph: int = Field(..., description="Position within paragraph")
    is_first: bool = Field(False, description="Is first sentence in paragraph")
    is_last: bool = Field(False, description="Is last sentence in paragraph")
    previous_sentence: Optional[str] = Field(None, description="Previous sentence for coherence")
    next_sentence: Optional[str] = Field(None, description="Next sentence for coherence")
    sentence_role: str = Field("unknown", description="Detected role of this sentence")
    has_issues: bool = Field(False, description="Whether flagged for rewriting")
    issue_types: List[str] = Field(default_factory=list, description="Types of issues detected")


class SentenceAnalysisResponse(LayerAnalysisResult):
    """
    Response for Layer 2: Sentence analysis
    第2层句子分析响应

    **CRITICAL**: Includes paragraph context for all sentences
    **关键**: 包含所有句子的段落上下文
    """
    layer: LayerLevel = LayerLevel.SENTENCE
    sentence_count: int = Field(0, description="Total number of sentences")
    sentences_with_context: List[SentenceWithContext] = Field(
        default_factory=list,
        description="Sentences with full paragraph context"
    )
    sentence_roles: List[str] = Field(default_factory=list, description="Role of each sentence")
    void_patterns: List[Dict[str, Any]] = Field(default_factory=list, description="Detected syntactic void patterns")
    pattern_issues: List[Dict[str, Any]] = Field(default_factory=list, description="Sentence pattern issues")


class LexicalAnalysisResponse(LayerAnalysisResult):
    """
    Response for Layer 1: Lexical analysis
    第1层词汇分析响应
    """
    layer: LayerLevel = LayerLevel.LEXICAL
    fingerprint_matches: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Fingerprint matches by type (type_a, type_b, phrases)"
    )
    fingerprint_density: float = Field(0.0, description="Fingerprint density percentage")
    connector_matches: List[Dict[str, Any]] = Field(default_factory=list, description="Detected connector overuse")
    connector_ratio: float = Field(0.0, description="Ratio of sentences starting with connectors")
    replacement_suggestions: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Suggested replacements for flagged words"
    )


class PipelineAnalysisResponse(BaseModel):
    """
    Response for full pipeline analysis
    全流水线分析响应
    """
    overall_risk_score: int = Field(..., ge=0, le=100, description="Combined risk score")
    overall_risk_level: RiskLevel = Field(..., description="Overall risk level")
    layers_analyzed: List[LayerLevel] = Field(..., description="Layers that were analyzed")
    layer_results: Dict[str, LayerAnalysisResult] = Field(..., description="Results from each layer")
    total_issues: int = Field(0, description="Total issues across all layers")
    priority_issues: List[DetectionIssue] = Field(default_factory=list, description="High-priority issues to address")
    processing_time_ms: int = Field(0, description="Total processing time")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


# =============================================================================
# Rewriting Context Models
# =============================================================================

class RewriteContextRequest(BaseModel):
    """
    Request for getting rewrite context for a sentence
    获取句子改写上下文的请求
    """
    sentence_index: int = Field(..., ge=0, description="Global sentence index")
    paragraphs: List[str] = Field(..., min_length=1, description="All paragraphs")
    paragraph_roles: Optional[List[str]] = Field(None, description="Paragraph roles")
    sentence_roles: Optional[List[str]] = Field(None, description="Sentence roles")


class RewriteContextResponse(BaseModel):
    """
    Response with full context for rewriting
    包含完整改写上下文的响应
    """
    original_sentence: str = Field(..., description="Original sentence to rewrite")
    full_paragraph: str = Field(..., description="Full paragraph for context")
    paragraph_role: str = Field(..., description="Role of the paragraph")
    sentence_role: str = Field(..., description="Role of the sentence")
    position_info: str = Field(..., description="Position info like '2/5' (sentence 2 of 5)")
    is_first_sentence: bool = Field(..., description="Is first in paragraph")
    is_last_sentence: bool = Field(..., description="Is last in paragraph")
    previous_sentence: Optional[str] = Field(None, description="Previous sentence")
    next_sentence: Optional[str] = Field(None, description="Next sentence")
    issues_to_fix: List[str] = Field(default_factory=list, description="Issues to address")
    section_role: str = Field("body", description="Role of containing section")


# =============================================================================
# Step 1.4: Connectors & Transitions Models
# 步骤 1.4：连接词与衔接模型
# =============================================================================

class TransitionIssueSchema(BaseModel):
    """
    Transition issue detected between paragraphs
    段落间检测到的衔接问题
    """
    type: str = Field(..., description="Issue type: explicit_connector, too_smooth, topic_sentence_pattern, etc.")
    description: str = Field(..., description="English description")
    description_zh: str = Field(..., description="Chinese description")
    severity: IssueSeverity = Field(..., description="Issue severity")
    position: str = Field(..., description="Position: para_a_end, para_b_start, both")
    word: Optional[str] = Field(None, description="Problematic word if applicable")


class TransitionResultSchema(BaseModel):
    """
    Result for a single paragraph transition analysis
    单个段落衔接分析的结果
    """
    transition_index: int = Field(..., description="Index of this transition (between para N and N+1)")
    para_a_index: int = Field(..., description="Index of first paragraph")
    para_b_index: int = Field(..., description="Index of second paragraph")
    para_a_ending: str = Field(..., description="Last 1-2 sentences of paragraph A")
    para_b_opening: str = Field(..., description="First 1-2 sentences of paragraph B")
    smoothness_score: int = Field(..., ge=0, le=100, description="Smoothness score 0-100, higher = more AI-like")
    risk_level: RiskLevel = Field(..., description="Risk level for this transition")
    issues: List[TransitionIssueSchema] = Field(default_factory=list, description="Detected transition issues")
    explicit_connectors: List[str] = Field(default_factory=list, description="Explicit connectors found")
    has_topic_sentence_pattern: bool = Field(False, description="Para B starts with formulaic topic sentence")
    has_summary_ending: bool = Field(False, description="Para A ends with explicit summary")
    semantic_overlap: float = Field(0.0, description="Keyword overlap ratio")


class ConnectorAnalysisRequest(BaseModel):
    """
    Request for Step 1.4: Connector & Transition Analysis
    步骤 1.4：连接词与衔接分析请求
    """
    text: str = Field(..., min_length=1, description="Full document text")
    session_id: Optional[str] = Field(None, description="Session ID for locked terms")


class ConnectorAnalysisResponse(BaseModel):
    """
    Response for Step 1.4: Connector & Transition Analysis
    步骤 1.4：连接词与衔接分析响应
    """
    # Overall statistics / 总体统计
    total_transitions: int = Field(..., description="Total number of paragraph transitions")
    problematic_transitions: int = Field(..., description="Number of transitions with issues")
    overall_smoothness_score: int = Field(..., ge=0, le=100, description="Average smoothness score")
    overall_risk_level: RiskLevel = Field(..., description="Overall risk level")

    # Explicit connector statistics / 显性连接词统计
    total_explicit_connectors: int = Field(0, description="Total explicit connectors found")
    connector_density: float = Field(0.0, description="Percentage of paragraphs starting with explicit connectors")
    connector_list: List[str] = Field(default_factory=list, description="All explicit connectors found")

    # Per-transition results / 每个衔接的结果
    transitions: List[TransitionResultSchema] = Field(default_factory=list, description="Analysis for each transition")

    # Aggregated issues / 汇总问题
    issues: List[DetectionIssue] = Field(default_factory=list, description="All issues across all transitions")

    # Recommendations / 建议
    recommendations: List[str] = Field(default_factory=list, description="English recommendations")
    recommendations_zh: List[str] = Field(default_factory=list, description="Chinese recommendations")

    # Processing time / 处理时间
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


# =============================================================================
# Step 1.3: Progression & Closure Models
# 步骤 1.3：推进模式与闭合模型
# =============================================================================

class ProgressionType(str, Enum):
    """Progression type classification"""
    MONOTONIC = "monotonic"         # Linear/sequential progression (AI-like)
    NON_MONOTONIC = "non_monotonic" # Non-linear with returns/conditionals (Human-like)
    MIXED = "mixed"                 # Mixed patterns
    UNKNOWN = "unknown"


class ClosureType(str, Enum):
    """Closure type classification"""
    STRONG = "strong"    # Definitive conclusions (AI-like)
    MODERATE = "moderate"
    WEAK = "weak"        # Open-ended, unresolved (Human-like)
    OPEN = "open"


class ProgressionMarker(BaseModel):
    """
    Detected progression marker in the document
    文档中检测到的推进标记
    """
    paragraph_index: int = Field(..., description="Paragraph index where marker was found")
    marker: str = Field(..., description="The marker text")
    category: str = Field(..., description="Category: sequential, additive, causal, return, conditional, etc.")
    is_monotonic: bool = Field(..., description="Whether this is a monotonic (AI-like) marker")


class ProgressionClosureRequest(BaseModel):
    """
    Request for Step 1.3: Progression & Closure Analysis
    步骤 1.3：推进模式与闭合分析请求
    """
    text: str = Field(..., min_length=1, description="Full document text")
    session_id: Optional[str] = Field(None, description="Session ID")


class ProgressionClosureResponse(BaseModel):
    """
    Response for Step 1.3: Progression & Closure Analysis
    步骤 1.3：推进模式与闭合分析响应
    """
    # Progression Analysis / 推进分析
    progression_score: int = Field(..., ge=0, le=100, description="Progression predictability score (higher = more AI-like)")
    progression_type: ProgressionType = Field(..., description="Detected progression type")
    monotonic_count: int = Field(0, description="Number of monotonic markers found")
    non_monotonic_count: int = Field(0, description="Number of non-monotonic markers found")
    sequential_markers_found: int = Field(0, description="Number of sequential markers (First, Second, etc.)")
    progression_markers: List[ProgressionMarker] = Field(default_factory=list, description="All progression markers found")

    # Closure Analysis / 闭合分析
    closure_score: int = Field(..., ge=0, le=100, description="Closure strength score (higher = stronger = more AI-like)")
    closure_type: ClosureType = Field(..., description="Detected closure type")
    strong_closure_patterns: List[str] = Field(default_factory=list, description="Strong closure patterns detected")
    weak_closure_patterns: List[str] = Field(default_factory=list, description="Weak/open closure patterns detected")
    last_paragraph_preview: str = Field("", description="Preview of last paragraph")

    # Combined Risk / 综合风险
    combined_score: int = Field(..., ge=0, le=100, description="Combined progression + closure score")
    risk_level: RiskLevel = Field(..., description="Overall risk level")

    # Recommendations / 建议
    recommendations: List[str] = Field(default_factory=list, description="English recommendations")
    recommendations_zh: List[str] = Field(default_factory=list, description="Chinese recommendations")

    # Processing time / 处理时间
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


# =============================================================================
# Step 1.5: Content Substantiality Models
# 步骤 1.5：内容实质性模型
# =============================================================================

class SubstantialityLevel(str, Enum):
    """Content substantiality level"""
    HIGH = "high"         # High specific content (Human-like)
    MEDIUM = "medium"
    LOW = "low"           # Generic/vague content (AI-like)


class ParagraphSubstantiality(BaseModel):
    """
    Substantiality analysis for a single paragraph
    单个段落的实质性分析
    """
    index: int = Field(..., description="Paragraph index")
    preview: str = Field(..., description="First 100 chars of paragraph")
    word_count: int = Field(..., description="Word count")

    # Substantiality metrics / 实质性指标
    specificity_score: int = Field(..., ge=0, le=100, description="How specific/concrete (higher = better)")
    generic_phrase_count: int = Field(0, description="Number of generic phrases detected")
    specific_detail_count: int = Field(0, description="Number of specific details (numbers, names, etc.)")
    filler_ratio: float = Field(0.0, description="Ratio of filler words")

    # Detected patterns / 检测到的模式
    generic_phrases: List[str] = Field(default_factory=list, description="Generic phrases found")
    specific_details: List[str] = Field(default_factory=list, description="Specific details found")

    # Assessment / 评估
    substantiality_level: SubstantialityLevel = Field(..., description="Overall substantiality level")
    suggestion: str = Field("", description="Suggestion for improvement")
    suggestion_zh: str = Field("", description="Chinese suggestion")


class ContentSubstantialityRequest(BaseModel):
    """
    Request for Step 1.5: Content Substantiality Analysis
    步骤 1.5：内容实质性分析请求
    """
    text: str = Field(..., min_length=1, description="Full document text")
    session_id: Optional[str] = Field(None, description="Session ID")


class ContentSubstantialityResponse(BaseModel):
    """
    Response for Step 1.5: Content Substantiality Analysis
    步骤 1.5：内容实质性分析响应
    """
    # Overall statistics / 总体统计
    paragraph_count: int = Field(..., description="Total paragraphs analyzed")
    overall_specificity_score: int = Field(..., ge=0, le=100, description="Overall specificity (higher = more specific = more human-like)")
    overall_substantiality: SubstantialityLevel = Field(..., description="Overall substantiality level")
    risk_level: RiskLevel = Field(..., description="Risk level based on substantiality")

    # Aggregated metrics / 汇总指标
    total_generic_phrases: int = Field(0, description="Total generic phrases in document")
    total_specific_details: int = Field(0, description="Total specific details in document")
    average_filler_ratio: float = Field(0.0, description="Average filler word ratio")

    # High-risk paragraphs / 高风险段落
    low_substantiality_paragraphs: List[int] = Field(default_factory=list, description="Indices of low substantiality paragraphs")

    # Per-paragraph details / 每段落详情
    paragraphs: List[ParagraphSubstantiality] = Field(default_factory=list, description="Per-paragraph analysis")

    # Common generic phrases / 常见泛泛短语
    common_generic_phrases: List[str] = Field(default_factory=list, description="Most common generic phrases")

    # Recommendations / 建议
    recommendations: List[str] = Field(default_factory=list, description="English recommendations")
    recommendations_zh: List[str] = Field(default_factory=list, description="Chinese recommendations")

    # Processing time / 处理时间
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


# =============================================================================
# Step 1.2: Paragraph Length Regularity Models
# 步骤 1.2：段落长度规律性模型
# =============================================================================

class ParagraphLengthStrategy(str, Enum):
    """Strategy type for paragraph length adjustment"""
    MERGE = "merge"       # Merge with adjacent paragraph
    SPLIT = "split"       # Split into smaller paragraphs
    EXPAND = "expand"     # Expand with more content
    COMPRESS = "compress" # Compress/summarize content
    NONE = "none"         # No action needed


class ParagraphLengthInfo(BaseModel):
    """
    Length info for a single paragraph
    单个段落的长度信息
    """
    index: int = Field(..., description="Paragraph index (0-based)")
    word_count: int = Field(..., description="Number of words in paragraph")
    char_count: int = Field(..., description="Number of characters")
    sentence_count: int = Field(0, description="Number of sentences")
    preview: str = Field(..., description="First 100 chars of paragraph")
    deviation_from_mean: float = Field(0.0, description="How far from mean length (in stddev)")
    suggested_strategy: ParagraphLengthStrategy = Field(ParagraphLengthStrategy.NONE, description="Suggested adjustment")
    strategy_reason: str = Field("", description="Reason for the strategy suggestion")
    strategy_reason_zh: str = Field("", description="Chinese reason")


class ParagraphLengthAnalysisRequest(BaseModel):
    """
    Request for Step 1.2: Paragraph Length Regularity Analysis
    步骤 1.2：段落长度规律性分析请求
    """
    text: str = Field(..., min_length=1, description="Full document text")
    session_id: Optional[str] = Field(None, description="Session ID")


class ParagraphLengthAnalysisResponse(BaseModel):
    """
    Response for Step 1.2: Paragraph Length Regularity Analysis
    步骤 1.2：段落长度规律性分析响应
    """
    # Overall statistics / 总体统计
    paragraph_count: int = Field(..., description="Total number of paragraphs")
    total_word_count: int = Field(..., description="Total words in document")

    # Length metrics / 长度指标
    mean_length: float = Field(..., description="Average paragraph length (words)")
    stdev_length: float = Field(..., description="Standard deviation of length")
    cv: float = Field(..., description="Coefficient of variation (stdev/mean)")
    min_length: int = Field(..., description="Minimum paragraph length")
    max_length: int = Field(..., description="Maximum paragraph length")

    # Risk assessment / 风险评估
    length_regularity_score: int = Field(..., ge=0, le=100, description="Length regularity score (higher = more uniform = more AI-like)")
    risk_level: RiskLevel = Field(..., description="Risk level based on CV")
    target_cv: float = Field(0.4, description="Target CV for human-like writing")

    # Per-paragraph details / 每个段落的详情
    paragraphs: List[ParagraphLengthInfo] = Field(default_factory=list, description="Length info for each paragraph")

    # Suggested strategies / 建议策略
    merge_suggestions: List[int] = Field(default_factory=list, description="Paragraph indices suggested for merging")
    split_suggestions: List[int] = Field(default_factory=list, description="Paragraph indices suggested for splitting")
    expand_suggestions: List[int] = Field(default_factory=list, description="Paragraph indices suggested for expansion")
    compress_suggestions: List[int] = Field(default_factory=list, description="Paragraph indices suggested for compression")

    # Recommendations / 建议
    recommendations: List[str] = Field(default_factory=list, description="English recommendations")
    recommendations_zh: List[str] = Field(default_factory=list, description="Chinese recommendations")

    # Processing time / 处理时间
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


# =============================================================================
# Layer 4 Sub-step Models (Step 2.0 - 2.5)
# 第4层子步骤模型（步骤 2.0 - 2.5）
# =============================================================================

class SectionRole(str, Enum):
    """Section role classification / 章节角色分类"""
    INTRODUCTION = "introduction"
    LITERATURE_REVIEW = "literature_review"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    ABSTRACT = "abstract"
    BODY = "body"
    UNKNOWN = "unknown"


class TransitionStrength(str, Enum):
    """Transition strength classification / 过渡强度分类"""
    STRONG = "strong"      # Explicit, formulaic (AI-like)
    MODERATE = "moderate"
    WEAK = "weak"          # Subtle, implicit (Human-like)
    NONE = "none"


class ParagraphFunction(str, Enum):
    """Paragraph function within a section / 段落在章节中的功能"""
    TOPIC_SENTENCE = "topic_sentence"       # Topic/thesis statement
    EVIDENCE = "evidence"                   # Supporting evidence/data
    ANALYSIS = "analysis"                   # Analysis/interpretation
    EXAMPLE = "example"                     # Concrete example
    TRANSITION = "transition"               # Transitional paragraph
    MINI_CONCLUSION = "mini_conclusion"     # Mini summary/conclusion
    ELABORATION = "elaboration"             # Elaboration on previous point
    UNKNOWN = "unknown"


# -----------------------------------------------------------------------------
# Step 2.0: Section Identification / 步骤 2.0：章节识别
# -----------------------------------------------------------------------------

class SectionInfo(BaseModel):
    """
    Detailed section information
    章节详细信息
    """
    index: int = Field(..., description="Section index (0-based)")
    role: str = Field(..., description="Detected section role")
    role_confidence: float = Field(0.0, ge=0, le=1, description="Confidence of role detection")
    title: Optional[str] = Field(None, description="Section title if detected")
    start_paragraph_idx: int = Field(..., description="Starting paragraph index")
    end_paragraph_idx: int = Field(..., description="Ending paragraph index (exclusive)")
    paragraph_count: int = Field(0, description="Number of paragraphs in section")
    word_count: int = Field(0, description="Total words in section")
    char_count: int = Field(0, description="Total characters in section")
    preview: str = Field("", description="First 150 chars of section")
    user_assigned_role: Optional[str] = Field(None, description="User-assigned role override")


class SectionIdentificationRequest(BaseModel):
    """
    Request for Step 2.0: Section Identification
    步骤 2.0：章节识别请求
    """
    text: Optional[str] = Field(None, description="Full document text")
    paragraphs: Optional[List[str]] = Field(None, description="Pre-split paragraphs")
    session_id: Optional[str] = Field(None, description="Session ID")

    @model_validator(mode='after')
    def validate_input(self):
        if not self.text and not self.paragraphs:
            raise ValueError('Either text or paragraphs must be provided')
        return self


class SectionIdentificationResponse(BaseModel):
    """
    Response for Step 2.0: Section Identification
    步骤 2.0：章节识别响应
    """
    section_count: int = Field(..., description="Number of detected sections")
    sections: List[SectionInfo] = Field(default_factory=list, description="Detected sections")
    total_paragraphs: int = Field(0, description="Total number of paragraphs")
    total_words: int = Field(0, description="Total word count")
    role_distribution: Dict[str, int] = Field(default_factory=dict, description="Count of each role")
    recommendations: List[str] = Field(default_factory=list)
    recommendations_zh: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[int] = Field(None)


# -----------------------------------------------------------------------------
# Step 2.1: Section Order & Structure / 步骤 2.1：章节顺序与结构
# -----------------------------------------------------------------------------

class SectionOrderAnalysis(BaseModel):
    """
    Analysis of section order and structure
    章节顺序与结构分析
    """
    detected_order: List[str] = Field(default_factory=list, description="Detected section order")
    expected_order: List[str] = Field(default_factory=list, description="Expected academic order")
    order_match_score: float = Field(0.0, ge=0, le=1, description="How well order matches template")
    is_predictable: bool = Field(False, description="True if order is highly predictable (AI-like)")
    missing_sections: List[str] = Field(default_factory=list, description="Missing critical sections")
    unexpected_sections: List[str] = Field(default_factory=list, description="Unexpected section positions")
    fusion_score: float = Field(0.0, ge=0, le=1, description="Section function purity")
    multi_function_sections: List[int] = Field(default_factory=list, description="Indices of multi-function sections")


class SectionOrderRequest(BaseModel):
    """
    Request for Step 2.1: Section Order & Structure
    步骤 2.1：章节顺序与结构请求
    """
    text: Optional[str] = Field(None, description="Full document text")
    paragraphs: Optional[List[str]] = Field(None, description="Pre-split paragraphs")
    sections: Optional[List[Dict[str, Any]]] = Field(None, description="Pre-identified sections from Step 2.0")
    session_id: Optional[str] = Field(None, description="Session ID")

    @model_validator(mode='after')
    def validate_input(self):
        if not self.text and not self.paragraphs and not self.sections:
            raise ValueError('Either text, paragraphs, or sections must be provided')
        return self


class SectionOrderResponse(BaseModel):
    """
    Response for Step 2.1: Section Order & Structure
    步骤 2.1：章节顺序与结构响应
    """
    risk_score: int = Field(0, ge=0, le=100, description="Risk score for this step")
    risk_level: RiskLevel = Field(RiskLevel.LOW)
    order_analysis: SectionOrderAnalysis = Field(..., description="Order analysis result")
    issues: List[DetectionIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    recommendations_zh: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[int] = Field(None)


# -----------------------------------------------------------------------------
# Step 2.2: Section Length Distribution / 步骤 2.2：章节长度分布
# -----------------------------------------------------------------------------

class SectionLengthInfo(BaseModel):
    """
    Length information for a single section
    单个章节的长度信息
    """
    index: int = Field(..., description="Section index")
    role: str = Field(..., description="Section role")
    word_count: int = Field(0)
    paragraph_count: int = Field(0)
    deviation_from_mean: float = Field(0.0, description="Deviation from mean in stddev units")
    is_extreme: bool = Field(False, description="True if extremely long or short")
    expected_weight: Optional[float] = Field(None, description="Expected proportion for this role")
    actual_weight: float = Field(0.0, description="Actual proportion of total")
    weight_deviation: float = Field(0.0, description="Difference from expected")


class SectionLengthRequest(BaseModel):
    """
    Request for Step 2.2: Section Length Distribution
    步骤 2.2：章节长度分布请求
    """
    text: Optional[str] = Field(None)
    paragraphs: Optional[List[str]] = Field(None)
    sections: Optional[List[Dict[str, Any]]] = Field(None)
    session_id: Optional[str] = Field(None)

    @model_validator(mode='after')
    def validate_input(self):
        if not self.text and not self.paragraphs and not self.sections:
            raise ValueError('Either text, paragraphs, or sections must be provided')
        return self


class SectionLengthResponse(BaseModel):
    """
    Response for Step 2.2: Section Length Distribution
    步骤 2.2：章节长度分布响应
    """
    risk_score: int = Field(0, ge=0, le=100)
    risk_level: RiskLevel = Field(RiskLevel.LOW)
    section_count: int = Field(0)
    total_words: int = Field(0)
    mean_length: float = Field(0.0)
    stdev_length: float = Field(0.0)
    length_cv: float = Field(0.0, description="Coefficient of variation")
    is_uniform: bool = Field(False, description="True if CV < 0.3 (AI-like)")
    sections: List[SectionLengthInfo] = Field(default_factory=list)
    extremely_short: List[int] = Field(default_factory=list)
    extremely_long: List[int] = Field(default_factory=list)
    key_section_weight_score: float = Field(0.0, description="How well key sections are weighted")
    issues: List[DetectionIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    recommendations_zh: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[int] = Field(None)


# -----------------------------------------------------------------------------
# Step 2.3: Internal Structure Similarity (NEW) / 步骤 2.3：章节内部结构相似性
# -----------------------------------------------------------------------------

class ParagraphFunctionInfo(BaseModel):
    """
    Function information for a paragraph within a section
    段落在章节内的功能信息
    """
    paragraph_index: int = Field(..., description="Global paragraph index")
    local_index: int = Field(..., description="Index within section")
    function: str = Field("unknown")
    function_confidence: float = Field(0.0, ge=0, le=1)
    preview: str = Field("", description="First 100 chars")


class SectionInternalStructure(BaseModel):
    """
    Internal structure analysis for a single section
    单个章节的内部结构分析
    """
    section_index: int = Field(...)
    section_role: str = Field(...)
    paragraph_functions: List[ParagraphFunctionInfo] = Field(default_factory=list)
    function_sequence: List[str] = Field(default_factory=list, description="Sequence of function labels")
    heading_depth: int = Field(0, description="Maximum heading depth in section")
    has_subheadings: bool = Field(False)
    argument_count: int = Field(0, description="Number of argument markers detected")
    argument_density: float = Field(0.0, description="Arguments per 100 words")


class StructureSimilarityPair(BaseModel):
    """
    Similarity comparison between two sections
    两个章节之间的相似性比较
    """
    section_a_index: int = Field(...)
    section_b_index: int = Field(...)
    section_a_role: str = Field(...)
    section_b_role: str = Field(...)
    function_sequence_similarity: float = Field(0.0, ge=0, le=100, description="Sequence similarity percentage")
    structure_similarity: float = Field(0.0, ge=0, le=100, description="Overall structure similarity")
    is_suspicious: bool = Field(False, description="True if similarity > 80% (AI-like)")


class InternalStructureSimilarityRequest(BaseModel):
    """
    Request for Step 2.3: Internal Structure Similarity
    步骤 2.3：章节内部结构相似性请求
    """
    text: Optional[str] = Field(None)
    paragraphs: Optional[List[str]] = Field(None)
    sections: Optional[List[Dict[str, Any]]] = Field(None)
    session_id: Optional[str] = Field(None)

    @model_validator(mode='after')
    def validate_input(self):
        if not self.text and not self.paragraphs and not self.sections:
            raise ValueError('Either text, paragraphs, or sections must be provided')
        return self


class InternalStructureSimilarityResponse(BaseModel):
    """
    Response for Step 2.3: Internal Structure Similarity
    步骤 2.3：章节内部结构相似性响应
    """
    risk_score: int = Field(0, ge=0, le=100)
    risk_level: RiskLevel = Field(RiskLevel.LOW)
    section_structures: List[SectionInternalStructure] = Field(default_factory=list)
    similarity_pairs: List[StructureSimilarityPair] = Field(default_factory=list)
    average_similarity: float = Field(0.0, description="Average pairwise similarity")
    max_similarity: float = Field(0.0, description="Maximum pairwise similarity")
    heading_depth_cv: float = Field(0.0, description="CV of heading depths across sections")
    argument_density_cv: float = Field(0.0, description="CV of argument densities")
    suspicious_pairs: List[StructureSimilarityPair] = Field(default_factory=list)
    issues: List[DetectionIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    recommendations_zh: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[int] = Field(None)


# -----------------------------------------------------------------------------
# Step 2.4: Section Transition / 步骤 2.4：章节衔接与过渡
# -----------------------------------------------------------------------------

class SectionTransitionInfo(BaseModel):
    """
    Transition analysis between two sections
    两个章节之间的过渡分析
    """
    from_section_index: int = Field(...)
    to_section_index: int = Field(...)
    from_section_role: str = Field(...)
    to_section_role: str = Field(...)
    has_explicit_transition: bool = Field(False, description="Has explicit transition words")
    explicit_words: List[str] = Field(default_factory=list, description="Explicit transition words found")
    transition_strength: str = Field("none")
    semantic_echo_score: float = Field(0.0, ge=0, le=100, description="Keyword echo between sections")
    echoed_keywords: List[str] = Field(default_factory=list)
    opener_text: str = Field("", description="First sentence of target section")
    opener_pattern: str = Field("", description="Detected opener pattern type")
    is_formulaic_opener: bool = Field(False, description="True if opener is formulaic (AI-like)")
    transition_risk_score: int = Field(0, ge=0, le=100)


class SectionTransitionRequest(BaseModel):
    """
    Request for Step 2.4: Section Transition
    步骤 2.4：章节衔接与过渡请求
    """
    text: Optional[str] = Field(None)
    paragraphs: Optional[List[str]] = Field(None)
    sections: Optional[List[Dict[str, Any]]] = Field(None)
    session_id: Optional[str] = Field(None)

    @model_validator(mode='after')
    def validate_input(self):
        if not self.text and not self.paragraphs and not self.sections:
            raise ValueError('Either text, paragraphs, or sections must be provided')
        return self


class SectionTransitionResponse(BaseModel):
    """
    Response for Step 2.4: Section Transition
    步骤 2.4：章节衔接与过渡响应
    """
    risk_score: int = Field(0, ge=0, le=100)
    risk_level: RiskLevel = Field(RiskLevel.LOW)
    total_transitions: int = Field(0)
    explicit_transition_count: int = Field(0)
    transitions: List[SectionTransitionInfo] = Field(default_factory=list)
    explicit_ratio: float = Field(0.0, description="Ratio of explicit transitions")
    avg_semantic_echo: float = Field(0.0, description="Average semantic echo score")
    formulaic_opener_count: int = Field(0)
    strength_distribution: Dict[str, int] = Field(default_factory=dict)
    issues: List[DetectionIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    recommendations_zh: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[int] = Field(None)


# -----------------------------------------------------------------------------
# Step 2.5: Inter-Section Logic / 步骤 2.5：章节间逻辑关系
# -----------------------------------------------------------------------------

class ArgumentChainNode(BaseModel):
    """
    Node in the argument chain
    论点链中的节点
    """
    section_index: int = Field(...)
    section_role: str = Field(...)
    main_argument: str = Field("", description="Main argument/claim in this section")
    supporting_points: List[str] = Field(default_factory=list)
    connects_to_previous: bool = Field(False, description="Logically connects to previous section")
    connection_type: str = Field("", description="Type: supports, extends, contrasts, etc.")


class RedundancyInfo(BaseModel):
    """
    Redundancy detection between sections
    章节间冗余检测
    """
    section_a_index: int = Field(...)
    section_b_index: int = Field(...)
    redundant_content: str = Field("", description="The redundant content")
    redundancy_type: str = Field("", description="Type: repeated_point, overlapping_evidence, etc.")
    severity: str = Field("low", description="Severity: low, medium, high")


class ProgressionPatternInfo(BaseModel):
    """
    Progression pattern analysis
    推进模式分析
    """
    pattern_type: str = Field("", description="Type: sequential, parallel, comparative, etc.")
    description: str = Field("")
    description_zh: str = Field("")
    is_ai_typical: bool = Field(False)
    sections_involved: List[int] = Field(default_factory=list)


class InterSectionLogicRequest(BaseModel):
    """
    Request for Step 2.5: Inter-Section Logic
    步骤 2.5：章节间逻辑关系请求
    """
    text: Optional[str] = Field(None)
    paragraphs: Optional[List[str]] = Field(None)
    sections: Optional[List[Dict[str, Any]]] = Field(None)
    session_id: Optional[str] = Field(None)

    @model_validator(mode='after')
    def validate_input(self):
        if not self.text and not self.paragraphs and not self.sections:
            raise ValueError('Either text, paragraphs, or sections must be provided')
        return self


class InterSectionLogicResponse(BaseModel):
    """
    Response for Step 2.5: Inter-Section Logic
    步骤 2.5：章节间逻辑关系响应
    """
    risk_score: int = Field(0, ge=0, le=100)
    risk_level: RiskLevel = Field(RiskLevel.LOW)
    argument_chain: List[ArgumentChainNode] = Field(default_factory=list)
    chain_coherence_score: float = Field(0.0, ge=0, le=100, description="How well arguments connect")
    redundancies: List[RedundancyInfo] = Field(default_factory=list)
    total_redundancies: int = Field(0)
    progression_patterns: List[ProgressionPatternInfo] = Field(default_factory=list)
    dominant_pattern: str = Field("", description="Most common progression pattern")
    pattern_variety_score: float = Field(0.0, description="Variety in progression patterns")
    issues: List[DetectionIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    recommendations_zh: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[int] = Field(None)
