"""
Substep Shared Schemas
Substep共享模式定义
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IssueSeverity(str, Enum):
    """Issue severity level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Common Request/Response Base Classes
# 通用请求/响应基类
# =============================================================================

class SubstepBaseRequest(BaseModel):
    """Base request for all substep endpoints"""
    text: str = Field(..., min_length=10, description="Document text to analyze")
    session_id: Optional[str] = Field(None, description="Session ID for context tracking")
    locked_terms: Optional[List[str]] = Field(default_factory=list, description="Terms locked in Step 1.0")


class SubstepBaseResponse(BaseModel):
    """Base response for all substep endpoints"""
    risk_score: int = Field(0, ge=0, le=100, description="Risk score 0-100")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="Risk level")
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="Detected issues")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations (English)")
    recommendations_zh: List[str] = Field(default_factory=list, description="Recommendations (Chinese)")
    processing_time_ms: int = Field(0, description="Processing time in milliseconds")


# =============================================================================
# Layer 5 Specific Schemas
# Layer 5 特定模式
# =============================================================================

class TermLockRequest(BaseModel):
    """Request for term extraction"""
    document_text: str = Field(..., min_length=10, description="Document text to analyze")
    session_id: str = Field(..., description="Session ID for term storage")


class ExtractedTerm(BaseModel):
    """Single extracted term"""
    term: str = Field(..., description="The extracted term")
    term_type: str = Field(..., description="Type: technical_term, proper_noun, acronym, key_phrase, core_word")
    frequency: int = Field(..., description="Frequency in document")
    reason: str = Field(..., description="Why this should be locked (English)")
    reason_zh: str = Field(..., description="Why this should be locked (Chinese)")
    recommended: bool = Field(True, description="Whether recommended for locking")


class ExtractTermsResponse(BaseModel):
    """Response with extracted terms"""
    extracted_terms: List[ExtractedTerm] = Field(default_factory=list)
    total_count: int = Field(0, description="Total number of terms extracted")
    by_type: Dict[str, int] = Field(default_factory=dict, description="Count by term type")
    processing_time_ms: int = Field(0, description="Processing time in milliseconds")


class ConfirmLockRequest(BaseModel):
    """Request to confirm locked terms"""
    session_id: str = Field(..., description="Session ID")
    locked_terms: List[str] = Field(default_factory=list, description="Terms selected for locking")
    custom_terms: List[str] = Field(default_factory=list, description="Custom terms added by user")


class ConfirmLockResponse(BaseModel):
    """Response after confirming locked terms"""
    locked_count: int = Field(0, description="Number of terms locked")
    locked_terms: List[str] = Field(default_factory=list, description="All locked terms")
    message: str = Field("", description="Status message")
    message_zh: str = Field("", description="Status message in Chinese")


class StructureAnalysisResponse(SubstepBaseResponse):
    """Response for structure analysis (Step 1.1)"""
    symmetry_score: int = Field(0, description="Section symmetry score 0-100")
    predictability_score: int = Field(0, description="Predictability score 0-100")
    linear_flow_score: int = Field(0, description="Linear flow score 0-100")
    progression_type: str = Field("unknown", description="monotonic, non_monotonic, mixed")
    sections: List[Dict[str, Any]] = Field(default_factory=list, description="Detected sections")


class SectionUniformityResponse(SubstepBaseResponse):
    """Response for section uniformity analysis (Step 1.2)"""
    paragraph_count: int = Field(0, description="Total paragraph count")
    mean_length: float = Field(0, description="Mean paragraph length in words")
    stdev_length: float = Field(0, description="Standard deviation of lengths")
    cv: float = Field(0, description="Coefficient of variation")
    target_cv: float = Field(0.4, description="Target CV for human-like writing")
    paragraphs: List[Dict[str, Any]] = Field(default_factory=list, description="Paragraph info")


class LogicPatternResponse(SubstepBaseResponse):
    """Response for logic pattern analysis (Step 1.3)"""
    progression_score: int = Field(0, description="Progression predictability score")
    progression_type: str = Field("unknown", description="monotonic, non_monotonic, mixed")
    closure_score: int = Field(0, description="Closure strength score")
    closure_type: str = Field("unknown", description="strong, moderate, weak, open")
    sequential_markers_count: int = Field(0, description="Count of sequential markers")
    progression_markers: List[Dict[str, Any]] = Field(default_factory=list)


class ConnectorTransitionResponse(SubstepBaseResponse):
    """Response for connector/transition analysis (Step 1.4/1.5)"""
    total_transitions: int = Field(0, description="Total transition points")
    problematic_transitions: int = Field(0, description="Problematic transitions count")
    connector_density: float = Field(0, description="Connector density percentage")
    explicit_connectors: List[str] = Field(default_factory=list, description="Detected connectors")
    transitions: List[Dict[str, Any]] = Field(default_factory=list, description="Transition details")


class ContentSubstantialityResponse(SubstepBaseResponse):
    """Response for content substantiality analysis (Step 1.5)"""
    overall_specificity_score: int = Field(0, description="Overall specificity score")
    total_generic_phrases: int = Field(0, description="Total generic phrases found")
    total_specific_details: int = Field(0, description="Total specific details found")
    average_filler_ratio: float = Field(0, description="Average filler word ratio")
    paragraphs: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Layer 4 Specific Schemas
# Layer 4 特定模式
# =============================================================================

class SectionInfo(BaseModel):
    """Single section information"""
    index: int = Field(..., description="Section index")
    role: str = Field(..., description="Section role: introduction, methodology, etc.")
    start_paragraph: int = Field(..., description="Start paragraph index")
    end_paragraph: int = Field(..., description="End paragraph index")
    word_count: int = Field(0, description="Word count")
    confidence: float = Field(0, description="Classification confidence")


class SectionIdentifyResponse(SubstepBaseResponse):
    """Response for section identification (Step 2.0)"""
    sections: List[SectionInfo] = Field(default_factory=list)
    section_boundaries: List[int] = Field(default_factory=list)
    total_sections: int = Field(0)
    total_paragraphs: int = Field(0)


class SectionOrderResponse(SubstepBaseResponse):
    """Response for section order analysis (Step 2.1)"""
    order_match_score: int = Field(0, description="Template match score 0-100")
    missing_sections: List[str] = Field(default_factory=list)
    function_fusion_score: int = Field(0, description="Function fusion score 0-100")
    current_order: List[str] = Field(default_factory=list)
    expected_order: List[str] = Field(default_factory=list)


class SectionLengthResponse(SubstepBaseResponse):
    """Response for section length analysis (Step 2.2)"""
    length_cv: float = Field(0, description="Section length CV")
    paragraph_count_cv: float = Field(0, description="Paragraph count CV per section")
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    extreme_sections: List[int] = Field(default_factory=list)
    key_weight_issues: List[Dict[str, Any]] = Field(default_factory=list)


class InternalSimilarityResponse(SubstepBaseResponse):
    """Response for internal structure similarity (Step 2.3)"""
    avg_similarity: float = Field(0, description="Average structure similarity 0-1")
    similarity_matrix: List[List[float]] = Field(default_factory=list)
    heading_variance: float = Field(0, description="Heading depth variance")
    argument_density_cv: float = Field(0, description="Argument density CV")
    paragraph_functions: List[Dict[str, Any]] = Field(default_factory=list)


class SectionTransitionResponse(SubstepBaseResponse):
    """Response for section transition analysis (Step 2.4)"""
    explicit_transition_ratio: float = Field(0, description="Explicit transition ratio")
    semantic_echo_score: float = Field(0, description="Semantic echo score")
    opener_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    transition_words: List[Dict[str, Any]] = Field(default_factory=list)
    strength_distribution: Dict[str, int] = Field(default_factory=dict, description="Strong/Moderate/Weak distribution")


class InterSectionLogicResponse(SubstepBaseResponse):
    """Response for inter-section logic analysis (Step 2.5)"""
    argument_chain_score: int = Field(0, description="Argument chain completeness")
    redundancy_issues: List[Dict[str, Any]] = Field(default_factory=list)
    progression_pattern: str = Field("unknown", description="linear, branching, etc.")
    causal_density: float = Field(0, description="Causal marker density")
    linearity_score: int = Field(0, description="Linearity score 0-100")


# =============================================================================
# Layer 3 Specific Schemas
# Layer 3 特定模式
# =============================================================================

class ParagraphMeta(BaseModel):
    """Paragraph metadata"""
    index: int
    word_count: int
    sentence_count: int
    section_index: int
    preview: str = Field("", description="First 100 chars")


class ParagraphIdentifyResponse(SubstepBaseResponse):
    """Response for paragraph identification (Step 3.0)"""
    paragraphs: List[str] = Field(default_factory=list)
    paragraph_count: int = Field(0)
    paragraph_metadata: List[ParagraphMeta] = Field(default_factory=list)
    filtered_count: int = Field(0, description="Filtered non-body paragraphs")


class ParagraphRoleInfo(BaseModel):
    """Paragraph role information"""
    paragraph_index: int
    role: str  # introduction, background, methodology, results, discussion, conclusion, transition
    confidence: float
    section_index: int
    role_matches_section: bool
    keywords_found: List[str] = Field(default_factory=list)


class ParagraphRoleResponse(SubstepBaseResponse):
    """Response for paragraph role detection (Step 3.1)"""
    paragraph_roles: List[ParagraphRoleInfo] = Field(default_factory=list)
    role_distribution: Dict[str, int] = Field(default_factory=dict)
    uniformity_score: float = Field(0, description="0-1, higher = more uniform (AI-like)")
    missing_roles: List[str] = Field(default_factory=list)


class ParagraphCoherenceInfo(BaseModel):
    """Paragraph coherence information"""
    paragraph_index: int
    subject_diversity: float  # 0-1
    length_variation_cv: float
    logic_structure: str  # linear, mixed, hierarchical
    connector_density: float  # 0-1
    first_person_ratio: float  # 0-1
    overall_score: float  # 0-100


class CoherenceAnalysisResponse(SubstepBaseResponse):
    """Response for internal coherence analysis (Step 3.2)"""
    paragraph_coherence: List[ParagraphCoherenceInfo] = Field(default_factory=list)
    overall_coherence_score: float = Field(0)
    high_risk_paragraphs: List[int] = Field(default_factory=list)


class ParagraphAnchorInfo(BaseModel):
    """Paragraph anchor density information"""
    paragraph_index: int
    word_count: int
    anchor_count: int
    density: float  # anchors per 100 words
    has_hallucination_risk: bool
    risk_level: str
    anchor_types: Dict[str, int] = Field(default_factory=dict)


class AnchorDensityResponse(SubstepBaseResponse):
    """Response for anchor density analysis (Step 3.3)"""
    overall_density: float = Field(0)
    paragraph_densities: List[ParagraphAnchorInfo] = Field(default_factory=list)
    high_risk_paragraphs: List[int] = Field(default_factory=list)
    anchor_type_distribution: Dict[str, int] = Field(default_factory=dict)
    document_hallucination_risk: str = Field("low")


class ParagraphSentenceLengthInfo(BaseModel):
    """Paragraph sentence length information"""
    paragraph_index: int
    sentence_count: int
    sentence_lengths: List[int] = Field(default_factory=list)
    mean_length: float
    std_length: float
    cv: float
    burstiness: float
    has_short_sentence: bool
    has_long_sentence: bool
    rhythm_score: float


class SentenceLengthDistributionResponse(SubstepBaseResponse):
    """Response for sentence length distribution (Step 3.4)"""
    paragraph_lengths: List[ParagraphSentenceLengthInfo] = Field(default_factory=list)
    low_burstiness_paragraphs: List[int] = Field(default_factory=list)
    overall_cv: float = Field(0)


class TransitionInfo(BaseModel):
    """Paragraph transition information"""
    from_paragraph: int
    to_paragraph: int
    has_explicit_connector: bool
    connector_word: Optional[str] = None
    semantic_echo_score: float
    transition_quality: str  # smooth, abrupt, formulaic


class ParagraphTransitionResponse(SubstepBaseResponse):
    """Response for paragraph transition analysis (Step 3.5)"""
    transitions: List[TransitionInfo] = Field(default_factory=list)
    explicit_connector_count: int = Field(0)
    explicit_ratio: float = Field(0)
    avg_semantic_echo: float = Field(0)
    suggestions: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Layer 2 Specific Schemas
# Layer 2 特定模式
# =============================================================================

class SentenceContextResponse(SubstepBaseResponse):
    """Response for sentence context preparation (Step 4.0)"""
    sentences: List[Dict[str, Any]] = Field(default_factory=list)
    sentence_count: int = Field(0)
    paragraph_context: List[Dict[str, Any]] = Field(default_factory=list)


class SentenceRoleResponse(SubstepBaseResponse):
    """Response for sentence role detection (Step 4.1)"""
    sentence_roles: List[Dict[str, Any]] = Field(default_factory=list)
    role_distribution: Dict[str, int] = Field(default_factory=dict)


class SentencePatternResponse(SubstepBaseResponse):
    """Response for sentence pattern detection (Step 4.1)"""
    patterns_detected: List[Dict[str, Any]] = Field(default_factory=list)
    pattern_counts: Dict[str, Any] = Field(default_factory=dict)
    # Syntactic Void Detection Integration
    # 句法空洞检测集成
    syntactic_voids: List[Dict[str, Any]] = Field(default_factory=list, description="Detected syntactic void patterns")
    void_score: int = Field(0, ge=0, le=100, description="Overall void score 0-100")
    void_density: float = Field(0, description="Voids per 100 words")
    has_critical_void: bool = Field(False, description="Has high-severity void patterns")


class SentenceConnectorResponse(SubstepBaseResponse):
    """Response for sentence connector analysis (Step 4.3)"""
    connector_sentences: List[Dict[str, Any]] = Field(default_factory=list)
    connector_types: Dict[str, int] = Field(default_factory=dict)
    connector_density: float = Field(0)


class SentenceLengthDiversityResponse(SubstepBaseResponse):
    """Response for sentence length diversity (Step 4.4)"""
    sentences: List[Dict[str, Any]] = Field(default_factory=list)
    cv: float = Field(0)
    burstiness: float = Field(0)
    target_cv: float = Field(0.4)


class SentenceRewriteResponse(SubstepBaseResponse):
    """Response for sentence rewriting (Step 4.5)"""
    original_sentences: List[str] = Field(default_factory=list)
    rewritten_sentences: List[str] = Field(default_factory=list)
    changes: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Layer 1 Specific Schemas
# Layer 1 特定模式
# =============================================================================

class LexicalContextResponse(SubstepBaseResponse):
    """Response for lexical context preparation (Step 5.0)"""
    tokens: List[Dict[str, Any]] = Field(default_factory=list)
    vocabulary_stats: Dict[str, Any] = Field(default_factory=dict)


class FingerprintDetectionResponse(SubstepBaseResponse):
    """Response for fingerprint detection (Step 5.1)"""
    type_a_words: List[Dict[str, Any]] = Field(default_factory=list)  # Dead giveaways
    type_b_words: List[Dict[str, Any]] = Field(default_factory=list)  # Clichés
    type_c_phrases: List[Dict[str, Any]] = Field(default_factory=list)  # Phrases
    total_fingerprints: int = Field(0)
    fingerprint_density: float = Field(0)
    # PPL (Perplexity) Analysis Integration
    # PPL（困惑度）分析集成
    ppl_score: Optional[float] = Field(None, description="Perplexity score from ONNX model")
    ppl_risk_level: Optional[str] = Field(None, description="PPL risk: low (>40), medium (20-40), high (<20)")
    ppl_used_onnx: bool = Field(False, description="Whether ONNX model was used for PPL calculation")
    ppl_analysis: Optional[Dict[str, Any]] = Field(None, description="Detailed PPL analysis per paragraph")


class HumanFeatureResponse(SubstepBaseResponse):
    """Response for human feature analysis (Step 5.2)"""
    human_features: List[Dict[str, Any]] = Field(default_factory=list)
    feature_score: float = Field(0)


class ReplacementGenerationResponse(SubstepBaseResponse):
    """Response for replacement generation (Step 5.3)"""
    replacements: List[Dict[str, Any]] = Field(default_factory=list)
    replacement_count: int = Field(0)


class ParagraphRewriteResponse(SubstepBaseResponse):
    """Response for paragraph rewriting (Step 5.4)"""
    original_text: str = Field("")
    rewritten_text: str = Field("")
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    locked_terms_preserved: bool = Field(True)


class ValidationResponse(SubstepBaseResponse):
    """Response for validation (Step 5.5)"""
    original_risk_score: int = Field(0)
    final_risk_score: int = Field(0)
    improvement: int = Field(0)
    locked_terms_check: bool = Field(True)
    semantic_similarity: float = Field(0)
    validation_passed: bool = Field(True)
