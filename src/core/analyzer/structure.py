"""
Document Structure Analyzer (Level 1 De-AIGC)
文档结构分析器（Level 1 De-AIGC）

Phase 4: Analyzes full document structure for AI-like linear patterns
and suggests two restructuring strategies: optimize connection, deep restructure

Phase 4：分析全文结构的AI风格线性模式，
提供两种重构策略：优化连接、深度重组
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum


class StructureStrategy(str, Enum):
    """Structure strategy types 结构策略类型"""
    OPTIMIZE_CONNECTION = "optimize_connection"  # Optimize transitions without changing order
    DEEP_RESTRUCTURE = "deep_restructure"        # Reorder and restructure content


@dataclass
class ParagraphInfo:
    """
    Information about a paragraph
    段落信息
    """
    index: int
    text: str
    first_sentence: str
    last_sentence: str
    word_count: int
    sentence_count: int
    has_topic_sentence: bool
    has_summary_ending: bool
    connector_words: List[str]
    function_type: str  # introduction, body, conclusion, transition, evidence, analysis


@dataclass
class StructureIssue:
    """
    Detected structure issue
    检测到的结构问题
    """
    type: str  # linear_flow, repetitive_pattern, uniform_length, predictable_order
    description: str
    description_zh: str
    severity: str  # high, medium, low
    affected_paragraphs: List[int]
    suggestion: str
    suggestion_zh: str


@dataclass
class BreakPoint:
    """
    Logic break point in document structure
    文档结构中的逻辑断点
    """
    position: int  # Paragraph index
    type: str  # topic_shift, argument_gap, repetition, abrupt_transition
    description: str
    description_zh: str


@dataclass
class StructureOption:
    """
    A structure repair option
    结构修复选项
    """
    strategy: StructureStrategy
    strategy_name_zh: str
    outline: List[str]  # New paragraph order/structure
    changes: List[Dict]  # List of changes to make
    explanation: str
    explanation_zh: str
    predicted_improvement: int  # Expected structure score reduction


@dataclass
class ProgressionAnalysis:
    """
    Analysis of document progression type (P1 Enhancement)
    文档推进类型分析（P1增强）
    """
    progression_type: str  # "monotonic" | "non_monotonic" | "mixed"
    progression_type_zh: str
    forward_transitions: int  # Count of forward-only transitions
    backward_references: int  # Count of references to earlier content
    conditional_statements: int  # Count of conditional "if X then Y" patterns
    score: int  # 0-100, higher = more AI-like (monotonic)
    details: List[Dict] = field(default_factory=list)


@dataclass
class FunctionDistribution:
    """
    Analysis of paragraph function distribution (P1 Enhancement)
    段落功能分布分析（P1增强）
    """
    distribution_type: str  # "uniform" | "asymmetric" | "balanced"
    distribution_type_zh: str
    function_counts: Dict[str, int] = field(default_factory=dict)
    depth_variance: float = 0.0  # Variance in treatment depth
    longest_section_ratio: float = 0.0  # Ratio of longest to average
    score: int = 0  # 0-100, higher = more uniform (AI-like)
    asymmetry_opportunities: List[Dict] = field(default_factory=list)


@dataclass
class ClosureAnalysis:
    """
    Analysis of document closure pattern (P2 Enhancement)
    文档闭合模式分析（P2增强）
    """
    closure_type: str  # "strong" | "moderate" | "weak" | "open"
    closure_type_zh: str
    has_formulaic_ending: bool  # "In conclusion..." patterns
    has_complete_resolution: bool  # All tensions resolved
    open_questions: int  # Count of unresolved questions
    hedging_in_conclusion: int  # Count of hedging words in conclusion
    score: int = 0  # 0-100, higher = stronger closure (AI-like)
    detected_patterns: List[str] = field(default_factory=list)


@dataclass
class LexicalEchoAnalysis:
    """
    Analysis of lexical echo between paragraphs (P2 Enhancement)
    段落间词汇回声分析（P2增强）
    """
    total_transitions: int
    echo_transitions: int  # Transitions with lexical echo
    explicit_connector_transitions: int  # Transitions with explicit connectors
    echo_ratio: float  # Ratio of echo to explicit
    score: int = 0  # 0-100, lower = more echo (human-like)
    transition_details: List[Dict] = field(default_factory=list)


@dataclass
class CrossReferenceAnalysis:
    """
    Analysis of cross-referential links in document (7th AI Indicator Enhancement)
    文档交叉引用分析（第7项AI指征增强）

    Detects:
    - Cross-paragraph concept references
    - Core concept callbacks
    - Non-linear structural links
    """
    has_cross_references: bool  # Whether document has cross-references
    cross_reference_count: int  # Total count of cross-references
    concept_callbacks: int  # References back to core concepts
    forward_only_ratio: float  # Ratio of forward-only progression (0-1, higher = AI-like)
    score: int = 0  # 0-100, higher = more AI-like (lacking cross-refs)
    detected_references: List[Dict] = field(default_factory=list)
    core_concepts: List[str] = field(default_factory=list)


@dataclass
class StructuralIndicator:
    """
    Single structural AI indicator for risk card (7-Indicator System)
    单个结构AI指征用于风险卡片（7指征系统）
    """
    id: str  # Indicator ID
    name: str  # English name
    name_zh: str  # Chinese name
    triggered: bool  # Whether this indicator is triggered
    risk_level: int  # 1-3 stars
    emoji: str  # Visual emoji
    color: str  # hex color code
    description: str  # Brief description
    description_zh: str
    details: str = ""  # Specific details for this document
    details_zh: str = ""


@dataclass
class StructuralRiskCard:
    """
    7-Indicator Structural Risk Card for user visualization
    7指征结构风险卡片用于用户可视化
    """
    indicators: List[StructuralIndicator]
    triggered_count: int  # How many indicators are triggered
    overall_risk: str  # low, medium, high
    overall_risk_zh: str
    summary: str  # One-line summary
    summary_zh: str
    total_score: int  # Combined structure score


@dataclass
class StructureAnalysisResult:
    """
    Result of document structure analysis
    文档结构分析结果
    """
    # Basic info
    # 基本信息
    total_paragraphs: int
    total_sentences: int
    total_words: int
    avg_paragraph_length: float
    paragraph_length_variance: float

    # Scores and levels
    # 分数和等级
    structure_score: int  # 0-100, higher = more AI-like
    risk_level: str  # "low", "medium", "high"

    # Detected patterns
    # 检测到的模式
    paragraphs: List[ParagraphInfo] = field(default_factory=list)
    issues: List[StructureIssue] = field(default_factory=list)
    break_points: List[BreakPoint] = field(default_factory=list)

    # Extracted thesis
    # 提取的论点
    core_thesis: Optional[str] = None
    key_arguments: List[str] = field(default_factory=list)

    # Pattern detection
    # 模式检测
    has_linear_flow: bool = False  # 1-2-3 linear progression
    has_repetitive_pattern: bool = False  # Similar paragraph structures
    has_uniform_length: bool = False  # Similar paragraph lengths
    has_predictable_order: bool = False  # Introduction-body-conclusion

    # P1 Enhancement: Advanced pattern detection
    # P1增强：高级模式检测
    progression_analysis: Optional[ProgressionAnalysis] = None
    function_distribution: Optional[FunctionDistribution] = None

    # P2 Enhancement: Closure and lexical echo analysis
    # P2增强：闭合和词汇回声分析
    closure_analysis: Optional[ClosureAnalysis] = None
    lexical_echo_analysis: Optional[LexicalEchoAnalysis] = None

    # 7th Indicator Enhancement: Cross-reference analysis
    # 第7指征增强：交叉引用分析
    cross_reference_analysis: Optional[CrossReferenceAnalysis] = None

    # 7-Indicator Risk Card for user visualization
    # 7指征风险卡片用于用户可视化
    risk_card: Optional[StructuralRiskCard] = None

    # Repair options (populated when suggestions are generated)
    # 修复选项（生成建议时填充）
    options: List[StructureOption] = field(default_factory=list)

    # Messages
    # 消息
    message: str = ""
    message_zh: str = ""


class StructureAnalyzer:
    """
    Analyzes document structure for AI-like patterns
    分析文档结构的AI风格模式
    """

    # Topic sentence patterns (AI tendency)
    # 主题句模式（AI倾向）
    TOPIC_SENTENCE_PATTERNS = [
        r"^This (paper|study|research|analysis|section|paragraph) (examines|explores|investigates|discusses|presents)",
        r"^The (purpose|aim|goal|objective) of this",
        r"^In this (paper|study|section|paragraph)",
        r"^(First|Second|Third|Finally|Additionally|Moreover|Furthermore),",
        r"^One (key|crucial|important|significant) (aspect|factor|consideration)",
        r"^(An|The) important (aspect|factor|consideration) (is|of)",
    ]

    # Summary ending patterns
    # 总结结尾模式
    SUMMARY_PATTERNS = [
        r"(In summary|To summarize|In conclusion|Overall|Thus|Therefore|Hence),?.*\.$",
        r"(clearly|evidently|significantly) (demonstrates?|shows?|indicates?).*\.$",
        r"(This|These) (findings?|results?|observations?) (suggest|indicate|demonstrate).*\.$",
    ]

    # Linear transition patterns
    # 线性过渡模式
    LINEAR_TRANSITIONS = [
        "First", "Second", "Third", "Fourth", "Fifth",
        "Firstly", "Secondly", "Thirdly",
        "To begin with", "Next", "Then", "Finally", "Lastly",
        "In the first place", "In the second place",
    ]

    # Paragraph function keywords
    # 段落功能关键词
    FUNCTION_KEYWORDS = {
        "introduction": ["introduce", "overview", "background", "context", "aim", "purpose", "objective"],
        "conclusion": ["conclude", "summary", "findings", "implications", "future", "recommend"],
        "evidence": ["data", "results", "findings", "experiment", "survey", "analysis shows"],
        "analysis": ["analyze", "examine", "investigate", "explore", "discuss", "interpret"],
        "transition": ["turning to", "moving on", "having discussed", "building on"],
    }

    # P1 Enhancement: Backward reference patterns (non-monotonic indicators)
    # P1增强：回指模式（非单调指示器）
    BACKWARD_REFERENCE_PATTERNS = [
        r"as (mentioned|noted|discussed|stated|shown|demonstrated) (earlier|above|previously|before)",
        r"returning to (the|our|this)",
        r"recall(ing)? (that|the)",
        r"(this|these) earlier (point|observation|finding|argument)",
        r"revisit(ing)? (the|our)",
        r"as we (saw|noted|observed)",
        r"the (previous|earlier|above) (section|paragraph|discussion)",
    ]

    # P1 Enhancement: Conditional statement patterns (human-like)
    # P1增强：条件陈述模式（人类特征）
    CONDITIONAL_PATTERNS = [
        r"\bif\b.*\bthen\b",
        r"\bwhen\b.*,.*\b(this|it|they)\b",
        r"\bassuming\b.*,",
        r"\bgiven\b.*,",
        r"\bprovided\b.*,",
        r"\bunless\b.*,",
        r"\bwhile\b.*\balso\b",
    ]

    # P1 Enhancement: Forward-only transition patterns (monotonic indicators)
    # P1增强：单向推进模式（单调指示器）
    FORWARD_ONLY_PATTERNS = [
        r"^(furthermore|moreover|additionally|in addition),",
        r"^(building on this|extending this|taking this further)",
        r"^(the next|another|a further) (point|aspect|consideration)",
        r"^having (established|shown|demonstrated).*,.*now",
    ]

    # P2 Enhancement: Formulaic conclusion patterns (AI-like strong closure)
    # P2增强：公式化结论模式（AI风格强闭合）
    FORMULAIC_CONCLUSION_PATTERNS = [
        r"^in conclusion,",
        r"^to (summarize|conclude|sum up),",
        r"^in summary,",
        r"^this (paper|study|research|analysis) (has |)(demonstrated|shown|established)",
        r"^overall,.*findings",
        r"^the (results|findings|evidence) (clearly |)(demonstrate|show|indicate)",
        r"^taken together,",
    ]

    # P2 Enhancement: Open ending patterns (human-like weak closure)
    # P2增强：开放式结尾模式（人类风格弱闭合）
    OPEN_ENDING_PATTERNS = [
        r"(remains|remain) (unclear|to be seen|open)",
        r"further (research|investigation|study) (is|are) (needed|required|warranted)",
        r"(what|whether|how|why).*\?$",
        r"(may|might|could) (warrant|require|benefit from)",
        r"the (extent|degree|nature) of.*remains",
        r"(opens|raises|suggests) (new )?(questions|possibilities)",
    ]

    # P2 Enhancement: Hedging words for conclusion analysis
    # P2增强：结论分析中的弱化词
    HEDGING_WORDS = [
        "may", "might", "could", "possibly", "perhaps", "likely",
        "appears", "seems", "suggests", "indicates", "potentially",
        "to some extent", "in part", "somewhat", "arguably",
    ]

    # P2 Enhancement: Explicit connectors for lexical echo analysis
    # P2增强：词汇回声分析的显性连接词
    EXPLICIT_CONNECTORS = [
        "furthermore", "moreover", "additionally", "in addition",
        "however", "nevertheless", "nonetheless", "conversely",
        "therefore", "thus", "hence", "consequently", "accordingly",
        "similarly", "likewise", "in contrast", "on the other hand",
        "first", "second", "third", "finally", "lastly",
        "for example", "for instance", "specifically", "namely",
    ]

    # 7th Indicator Enhancement: Cross-reference patterns
    # 第7指征增强：交叉引用模式
    CROSS_REFERENCE_PATTERNS = [
        r"as (mentioned|discussed|noted|shown|demonstrated|described) (earlier|above|previously|before|in section)",
        r"(this|these|the) (mechanism|phenomenon|pattern|approach|method|finding|result|observation)s? (again |)(appear|emerge|manifest|recur)",
        r"returning to (the|our|this)",
        r"recall(ing)? (that |)(the |our |this )",
        r"(revisiting|revisit) (the|our|this)",
        r"as we (saw|noted|observed|discussed|mentioned)",
        r"(the|this) (earlier|previous|above|aforementioned) (discussion|analysis|section|point|argument)",
        r"building (on|upon) (the|this|our) (earlier|previous)",
        r"(this|these) (connect|relate|link|tie)s? (back )?(to|with)",
        r"(consistent|in line|in keeping) with (the|our|this) (earlier|previous)",
    ]

    # 7th Indicator: Core concept callback patterns
    # 第7指征：核心概念回调模式
    CONCEPT_CALLBACK_PATTERNS = [
        r"(this|the) (central|core|key|main|primary|fundamental) (concept|idea|theme|argument|thesis)",
        r"(the|this) (recurring|underlying|overarching) (theme|pattern|principle)",
        r"once again",
        r"(return|come back) to",
        r"(echo|mirror|reflect)s? (the|this|our) (earlier|initial|original)",
    ]

    # 7-Indicator Configuration
    # 7指征配置
    INDICATOR_CONFIG = {
        "symmetry": {
            "name": "Perfect Symmetry",
            "name_zh": "逻辑推进对称",
            "risk_level": 3,
            "emoji": "⚖️",
            "color_triggered": "#ef4444",  # red
            "color_safe": "#22c55e",  # green
            "description": "Parallel structure: First/Second/Third pattern",
            "description_zh": "首先/其次/最后 的平行结构"
        },
        "uniform_function": {
            "name": "Uniform Paragraph Function",
            "name_zh": "段落功能均匀",
            "risk_level": 2,
            "emoji": "📊",
            "color_triggered": "#f97316",  # orange
            "color_safe": "#22c55e",
            "description": "Every paragraph has complete claim-explain-conclude",
            "description_zh": "每段都完整'提出-解释-总结'"
        },
        "explicit_connectors": {
            "name": "Over-signaled Transitions",
            "name_zh": "连接词依赖",
            "risk_level": 3,
            "emoji": "🔗",
            "color_triggered": "#ef4444",
            "color_safe": "#22c55e",
            "description": "Heavy use of Furthermore/Moreover/Additionally",
            "description_zh": "段首密集使用显性连接词"
        },
        "linear_progression": {
            "name": "Linear Enumeration",
            "name_zh": "单一线性推进",
            "risk_level": 3,
            "emoji": "📝",
            "color_triggered": "#ef4444",
            "color_safe": "#22c55e",
            "description": "Point 1 → Point 2 → Point 3 → Conclusion",
            "description_zh": "观点1→观点2→观点3→总结"
        },
        "rhythmic_regularity": {
            "name": "Rhythmic Regularity",
            "name_zh": "段落节奏均衡",
            "risk_level": 2,
            "emoji": "📏",
            "color_triggered": "#f97316",
            "color_safe": "#22c55e",
            "description": "All paragraphs have similar length",
            "description_zh": "各段长度高度一致"
        },
        "over_conclusive": {
            "name": "Over-conclusive Ending",
            "name_zh": "结尾过度闭合",
            "risk_level": 2,
            "emoji": "🔒",
            "color_triggered": "#f97316",
            "color_safe": "#22c55e",
            "description": "Strong 'In conclusion...' pattern with no open questions",
            "description_zh": "'In conclusion...'式结尾，无开放问题"
        },
        "no_cross_reference": {
            "name": "No Cross-References",
            "name_zh": "缺乏回指结构",
            "risk_level": 2,
            "emoji": "🔄",
            "color_triggered": "#f97316",
            "color_safe": "#22c55e",
            "description": "Paragraphs are independent modules without callbacks",
            "description_zh": "段落如独立模块，无交叉呼应"
        },
    }

    def __init__(self):
        """Initialize the structure analyzer 初始化结构分析器"""
        # Compile patterns for efficiency
        # 预编译模式以提高效率
        self.topic_patterns = [re.compile(p, re.IGNORECASE) for p in self.TOPIC_SENTENCE_PATTERNS]
        self.summary_patterns = [re.compile(p, re.IGNORECASE) for p in self.SUMMARY_PATTERNS]

        # P1 Enhancement: Compile progression detection patterns
        # P1增强：编译推进检测模式
        self.backward_ref_patterns = [re.compile(p, re.IGNORECASE) for p in self.BACKWARD_REFERENCE_PATTERNS]
        self.conditional_patterns = [re.compile(p, re.IGNORECASE) for p in self.CONDITIONAL_PATTERNS]
        self.forward_only_patterns = [re.compile(p, re.IGNORECASE) for p in self.FORWARD_ONLY_PATTERNS]

        # P2 Enhancement: Compile closure and lexical echo patterns
        # P2增强：编译闭合和词汇回声模式
        self.formulaic_conclusion_patterns = [re.compile(p, re.IGNORECASE) for p in self.FORMULAIC_CONCLUSION_PATTERNS]
        self.open_ending_patterns = [re.compile(p, re.IGNORECASE) for p in self.OPEN_ENDING_PATTERNS]

        # 7th Indicator Enhancement: Compile cross-reference patterns
        # 第7指征增强：编译交叉引用模式
        self.cross_reference_patterns = [re.compile(p, re.IGNORECASE) for p in self.CROSS_REFERENCE_PATTERNS]
        self.concept_callback_patterns = [re.compile(p, re.IGNORECASE) for p in self.CONCEPT_CALLBACK_PATTERNS]

    def analyze(
        self,
        text: str,
        extract_thesis: bool = True
    ) -> StructureAnalysisResult:
        """
        Analyze document structure
        分析文档结构

        Args:
            text: Full document text 完整文档文本
            extract_thesis: Whether to extract core thesis 是否提取核心论点

        Returns:
            StructureAnalysisResult with issues and scores
            包含问题和分数的StructureAnalysisResult
        """
        # Split into paragraphs
        # 分割为段落
        paragraphs = self._split_paragraphs(text)

        if len(paragraphs) < 2:
            return StructureAnalysisResult(
                total_paragraphs=len(paragraphs),
                total_sentences=0,
                total_words=0,
                avg_paragraph_length=0,
                paragraph_length_variance=0,
                structure_score=0,
                risk_level="low",
                message="Document too short for structure analysis.",
                message_zh="文档太短，无法进行结构分析。"
            )

        # Analyze each paragraph
        # 分析每个段落
        paragraph_infos = [self._analyze_paragraph(i, p) for i, p in enumerate(paragraphs)]

        # Calculate basic statistics
        # 计算基本统计
        total_words = sum(p.word_count for p in paragraph_infos)
        total_sentences = sum(p.sentence_count for p in paragraph_infos)
        avg_length = total_words / len(paragraphs)
        lengths = [p.word_count for p in paragraph_infos]
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)

        # Initialize result
        # 初始化结果
        result = StructureAnalysisResult(
            total_paragraphs=len(paragraphs),
            total_sentences=total_sentences,
            total_words=total_words,
            avg_paragraph_length=avg_length,
            paragraph_length_variance=variance,
            structure_score=0,
            risk_level="low",
            paragraphs=paragraph_infos
        )

        issues: List[StructureIssue] = []
        break_points: List[BreakPoint] = []
        score = 0

        # 1. Check for linear flow (1-2-3 pattern)
        # 1. 检查线性流程（1-2-3模式）
        linear_result = self._check_linear_flow(paragraph_infos)
        if linear_result["detected"]:
            result.has_linear_flow = True
            issues.append(StructureIssue(
                type="linear_flow",
                description=linear_result["description"],
                description_zh=linear_result["description_zh"],
                severity="high",
                affected_paragraphs=linear_result["affected"],
                suggestion="Consider reorganizing to break the predictable sequence.",
                suggestion_zh="考虑重新组织以打破可预测的顺序。"
            ))
            score += 25

        # 2. Check for repetitive paragraph structure
        # 2. 检查重复的段落结构
        repetitive_result = self._check_repetitive_pattern(paragraph_infos)
        if repetitive_result["detected"]:
            result.has_repetitive_pattern = True
            issues.append(StructureIssue(
                type="repetitive_pattern",
                description=repetitive_result["description"],
                description_zh=repetitive_result["description_zh"],
                severity="medium",
                affected_paragraphs=repetitive_result["affected"],
                suggestion="Vary paragraph openings and structures.",
                suggestion_zh="变化段落开头和结构。"
            ))
            score += 20

        # 3. Check for uniform paragraph lengths
        # 3. 检查均匀的段落长度
        uniform_result = self._check_uniform_length(paragraph_infos)
        if uniform_result["detected"]:
            result.has_uniform_length = True
            issues.append(StructureIssue(
                type="uniform_length",
                description=uniform_result["description"],
                description_zh=uniform_result["description_zh"],
                severity="medium",
                affected_paragraphs=uniform_result["affected"],
                suggestion="Vary paragraph lengths for natural rhythm.",
                suggestion_zh="变化段落长度以获得自然节奏。"
            ))
            score += 15

        # 4. Check for predictable introduction-body-conclusion
        # 4. 检查可预测的引言-正文-结论结构
        predictable_result = self._check_predictable_order(paragraph_infos)
        if predictable_result["detected"]:
            result.has_predictable_order = True
            issues.append(StructureIssue(
                type="predictable_order",
                description=predictable_result["description"],
                description_zh=predictable_result["description_zh"],
                severity="low",
                affected_paragraphs=predictable_result["affected"],
                suggestion="Consider interspersing evidence and analysis.",
                suggestion_zh="考虑穿插证据和分析。"
            ))
            score += 10

        # 5. Find break points
        # 5. 找出断点
        break_points = self._find_break_points(paragraph_infos)
        result.break_points = break_points

        # 6. Extract thesis if requested
        # 6. 如果需要，提取论点
        if extract_thesis:
            thesis_result = self._extract_thesis(paragraph_infos)
            result.core_thesis = thesis_result.get("thesis")
            result.key_arguments = thesis_result.get("arguments", [])

        # 7. P1 Enhancement: Analyze progression type
        # 7. P1增强：分析推进类型
        result.progression_analysis = self.analyze_progression_type(paragraph_infos)
        # Add to score if monotonic (AI-like)
        # 如果是单调的（AI风格），加入分数
        if result.progression_analysis.progression_type == "monotonic":
            score += 15

        # 8. P1 Enhancement: Analyze function distribution
        # 8. P1增强：分析功能分布
        result.function_distribution = self.analyze_function_distribution(paragraph_infos)
        # Add to score if uniform (AI-like)
        # 如果是均匀的（AI风格），加入分数
        if result.function_distribution.distribution_type == "uniform":
            score += 10

        # 9. P2 Enhancement: Analyze closure pattern
        # 9. P2增强：分析闭合模式
        result.closure_analysis = self.analyze_closure(paragraph_infos)
        # Add to score if strong closure (AI-like)
        # 如果是强闭合（AI风格），加入分数
        if result.closure_analysis.closure_type == "strong":
            score += 10

        # 10. P2 Enhancement: Analyze lexical echo
        # 10. P2增强：分析词汇回声
        result.lexical_echo_analysis = self.analyze_lexical_echo(paragraph_infos)
        # Add to score if high explicit connector ratio (AI-like)
        # 如果显性连接词比例高（AI风格），加入分数
        if result.lexical_echo_analysis.score >= 60:
            score += 5

        # 11. 7th Indicator Enhancement: Analyze cross-references
        # 11. 第7指征增强：分析交叉引用
        result.cross_reference_analysis = self.analyze_cross_references(paragraph_infos)
        # Add to score if lacking cross-references (AI-like)
        # 如果缺少交叉引用（AI风格），加入分数
        if not result.cross_reference_analysis.has_cross_references:
            score += 5

        # Calculate final score and level
        # 计算最终分数和等级
        result.structure_score = min(score, 100)
        result.risk_level = self._score_to_level(result.structure_score)
        result.issues = issues

        # Generate messages
        # 生成消息
        result.message, result.message_zh = self._generate_messages(result)

        # 12. Generate 7-Indicator Risk Card
        # 12. 生成7指征风险卡片
        result.risk_card = self.generate_risk_card(result)

        return result

    def _split_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs
        将文本分割为段落
        """
        # Split by double newlines or more
        # 按双换行符或更多分割
        paragraphs = re.split(r'\n\s*\n', text.strip())
        # Filter out empty paragraphs and very short ones
        # 过滤空段落和非常短的段落
        return [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 20]

    def _analyze_paragraph(self, index: int, text: str) -> ParagraphInfo:
        """
        Analyze a single paragraph
        分析单个段落
        """
        sentences = self._split_sentences(text)
        words = text.split()

        first_sentence = sentences[0] if sentences else ""
        last_sentence = sentences[-1] if sentences else ""

        # Check for topic sentence pattern
        # 检查主题句模式
        has_topic = any(p.search(first_sentence) for p in self.topic_patterns)

        # Check for summary ending
        # 检查总结结尾
        has_summary = any(p.search(last_sentence) for p in self.summary_patterns)

        # Find connector words
        # 查找连接词
        connectors = []
        for trans in self.LINEAR_TRANSITIONS:
            if text.lower().startswith(trans.lower()):
                connectors.append(trans)
            elif f" {trans.lower()}" in text.lower():
                connectors.append(trans)

        # Determine function type
        # 确定功能类型
        function_type = self._determine_function(text)

        return ParagraphInfo(
            index=index,
            text=text,
            first_sentence=first_sentence,
            last_sentence=last_sentence,
            word_count=len(words),
            sentence_count=len(sentences),
            has_topic_sentence=has_topic,
            has_summary_ending=has_summary,
            connector_words=connectors,
            function_type=function_type
        )

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        将文本分割为句子
        """
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _determine_function(self, text: str) -> str:
        """
        Determine the function type of a paragraph
        确定段落的功能类型
        """
        text_lower = text.lower()

        for func_type, keywords in self.FUNCTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return func_type

        return "body"  # Default to body paragraph

    def _check_linear_flow(self, paragraphs: List[ParagraphInfo]) -> Dict:
        """
        Check for linear 1-2-3 flow pattern
        检查线性1-2-3流程模式
        """
        linear_markers = []
        affected = []

        for p in paragraphs:
            if p.connector_words:
                for conn in p.connector_words:
                    if conn in self.LINEAR_TRANSITIONS[:10]:  # First, Second, Third, etc.
                        linear_markers.append(p.index)
                        affected.append(p.index)

        if len(linear_markers) >= 3:
            return {
                "detected": True,
                "description": f"Found {len(linear_markers)} linear transition markers (First, Second, etc.)",
                "description_zh": f"发现 {len(linear_markers)} 个线性过渡标记（第一、第二等）",
                "affected": affected
            }

        return {"detected": False}

    def _check_repetitive_pattern(self, paragraphs: List[ParagraphInfo]) -> Dict:
        """
        Check for repetitive paragraph structure
        检查重复的段落结构
        """
        topic_count = sum(1 for p in paragraphs if p.has_topic_sentence)
        total = len(paragraphs)

        if total >= 3 and topic_count / total > 0.7:
            affected = [p.index for p in paragraphs if p.has_topic_sentence]
            return {
                "detected": True,
                "description": f"{topic_count}/{total} paragraphs start with topic sentences",
                "description_zh": f"{topic_count}/{total} 个段落以主题句开头",
                "affected": affected
            }

        return {"detected": False}

    def _check_uniform_length(self, paragraphs: List[ParagraphInfo]) -> Dict:
        """
        Check for uniform paragraph lengths
        检查均匀的段落长度
        """
        lengths = [p.word_count for p in paragraphs]
        if not lengths:
            return {"detected": False}

        avg = sum(lengths) / len(lengths)
        # Check if all lengths are within 30% of average
        # 检查所有长度是否在平均值的30%以内
        uniform_count = sum(1 for l in lengths if abs(l - avg) / avg < 0.3)

        if len(paragraphs) >= 4 and uniform_count / len(paragraphs) > 0.75:
            return {
                "detected": True,
                "description": f"Paragraphs have uniform length (avg: {avg:.0f} words, {uniform_count}/{len(paragraphs)} similar)",
                "description_zh": f"段落长度均匀（平均：{avg:.0f}词，{uniform_count}/{len(paragraphs)}个相似）",
                "affected": list(range(len(paragraphs)))
            }

        return {"detected": False}

    def _check_predictable_order(self, paragraphs: List[ParagraphInfo]) -> Dict:
        """
        Check for predictable introduction-body-conclusion pattern
        检查可预测的引言-正文-结论模式
        """
        if len(paragraphs) < 3:
            return {"detected": False}

        functions = [p.function_type for p in paragraphs]

        # Check for classic pattern
        # 检查经典模式
        if (functions[0] == "introduction" and
            functions[-1] == "conclusion" and
            all(f == "body" for f in functions[1:-1])):
            return {
                "detected": True,
                "description": "Classic introduction-body-conclusion structure detected",
                "description_zh": "检测到经典的引言-正文-结论结构",
                "affected": [0, len(paragraphs) - 1]
            }

        return {"detected": False}

    def _find_break_points(self, paragraphs: List[ParagraphInfo]) -> List[BreakPoint]:
        """
        Find logic break points in document
        查找文档中的逻辑断点
        """
        break_points = []

        for i in range(1, len(paragraphs)):
            prev = paragraphs[i - 1]
            curr = paragraphs[i]

            # Check for abrupt topic shift
            # 检查突然的主题转变
            if prev.function_type != curr.function_type:
                if prev.function_type == "evidence" and curr.function_type == "conclusion":
                    break_points.append(BreakPoint(
                        position=i,
                        type="abrupt_transition",
                        description="Jump from evidence to conclusion without analysis",
                        description_zh="从证据直接跳到结论，缺少分析"
                    ))

        return break_points

    def _extract_thesis(self, paragraphs: List[ParagraphInfo]) -> Dict:
        """
        Extract core thesis and key arguments
        提取核心论点和关键论据
        """
        # Look in first few paragraphs for thesis
        # 在前几段中查找论点
        thesis = None
        arguments = []

        for p in paragraphs[:3]:
            # Look for thesis indicators
            # 查找论点指示词
            if "argue" in p.text.lower() or "thesis" in p.text.lower() or "claim" in p.text.lower():
                thesis = p.first_sentence
                break
            elif p.function_type == "introduction":
                # Use last sentence of introduction as thesis
                # 使用引言的最后一句作为论点
                thesis = p.last_sentence

        # Extract key arguments from body paragraphs
        # 从正文段落中提取关键论据
        for p in paragraphs:
            if p.has_topic_sentence and p.function_type in ["body", "analysis", "evidence"]:
                arguments.append(p.first_sentence)

        return {
            "thesis": thesis,
            "arguments": arguments[:5]  # Limit to top 5
        }

    def _score_to_level(self, score: int) -> str:
        """
        Convert structure score to risk level
        将结构分数转换为风险等级
        """
        if score >= 50:
            return "high"
        elif score >= 25:
            return "medium"
        return "low"

    def _generate_messages(self, result: StructureAnalysisResult) -> Tuple[str, str]:
        """
        Generate human-readable messages
        生成人类可读的消息
        """
        if result.structure_score < 25:
            return (
                "Document structure appears natural with varied patterns.",
                "文档结构看起来自然，模式多样。"
            )
        elif result.structure_score < 50:
            return (
                f"Some structural patterns detected ({len(result.issues)} issues). Consider varying structure.",
                f"检测到一些结构模式（{len(result.issues)}个问题）。建议变化结构。"
            )
        else:
            return (
                f"Strong AI structural patterns detected ({len(result.issues)} issues). Structure needs significant revision.",
                f"检测到强AI结构模式（{len(result.issues)}个问题）。结构需要大幅修改。"
            )

    # =========================================================================
    # P1 Enhancement: Progression Type Detection
    # P1增强：推进类型检测
    # =========================================================================

    def analyze_progression_type(self, paragraphs: List[ParagraphInfo]) -> ProgressionAnalysis:
        """
        Analyze the progression type of document structure
        分析文档结构的推进类型

        Detects:
        - Monotonic: Forward-only progression (AI-typical)
        - Non-monotonic: References back, conditional, recursive (human-typical)
        - Mixed: Combination of both

        Args:
            paragraphs: List of analyzed paragraphs 分析后的段落列表

        Returns:
            ProgressionAnalysis with type and score 包含类型和分数的推进分析
        """
        forward_count = 0
        backward_count = 0
        conditional_count = 0
        details = []

        full_text = " ".join([p.text for p in paragraphs])

        # Count forward-only transitions
        # 统计单向推进过渡
        for i, pattern in enumerate(self.forward_only_patterns):
            matches = pattern.findall(full_text)
            if matches:
                forward_count += len(matches)
                details.append({
                    "type": "forward",
                    "pattern_id": i,
                    "count": len(matches)
                })

        # Count backward references
        # 统计回指
        for i, pattern in enumerate(self.backward_ref_patterns):
            matches = pattern.findall(full_text)
            if matches:
                backward_count += len(matches)
                details.append({
                    "type": "backward",
                    "pattern_id": i,
                    "count": len(matches)
                })

        # Count conditional statements
        # 统计条件陈述
        for i, pattern in enumerate(self.conditional_patterns):
            matches = pattern.findall(full_text)
            if matches:
                conditional_count += len(matches)
                details.append({
                    "type": "conditional",
                    "pattern_id": i,
                    "count": len(matches)
                })

        # Also count linear markers from existing detection
        # 同时统计现有检测中的线性标记
        linear_marker_count = sum(len(p.connector_words) for p in paragraphs)
        forward_count += linear_marker_count

        # Determine progression type
        # 确定推进类型
        total_non_monotonic = backward_count + conditional_count
        total_forward = forward_count

        if total_non_monotonic == 0 and total_forward > 0:
            progression_type = "monotonic"
            progression_type_zh = "单调推进"
            # High score = AI-like
            score = min(100, 50 + (total_forward * 10))
        elif total_non_monotonic > total_forward:
            progression_type = "non_monotonic"
            progression_type_zh = "非单调推进"
            # Low score = human-like
            score = max(0, 50 - (total_non_monotonic * 10))
        else:
            progression_type = "mixed"
            progression_type_zh = "混合推进"
            # Medium score
            ratio = total_forward / max(1, total_forward + total_non_monotonic)
            score = int(ratio * 100)

        return ProgressionAnalysis(
            progression_type=progression_type,
            progression_type_zh=progression_type_zh,
            forward_transitions=forward_count,
            backward_references=backward_count,
            conditional_statements=conditional_count,
            score=score,
            details=details
        )

    # =========================================================================
    # P1 Enhancement: Function Distribution Detection
    # P1增强：功能分布检测
    # =========================================================================

    def analyze_function_distribution(self, paragraphs: List[ParagraphInfo]) -> FunctionDistribution:
        """
        Analyze the function distribution across paragraphs
        分析段落间的功能分布

        Detects:
        - Uniform: All paragraphs have similar depth/length (AI-typical)
        - Asymmetric: Some topics get deep dives, others brief mention (human-typical)
        - Balanced: Reasonable variation

        Args:
            paragraphs: List of analyzed paragraphs 分析后的段落列表

        Returns:
            FunctionDistribution with type and score 包含类型和分数的功能分布
        """
        if not paragraphs:
            return FunctionDistribution(
                distribution_type="unknown",
                distribution_type_zh="未知",
                function_counts={},
                depth_variance=0.0,
                longest_section_ratio=0.0,
                score=50,
                asymmetry_opportunities=[]
            )

        # Count functions
        # 统计功能
        function_counts: Dict[str, int] = {}
        for p in paragraphs:
            func = p.function_type
            function_counts[func] = function_counts.get(func, 0) + 1

        # Calculate depth variance using word counts
        # 使用词数计算深度方差
        word_counts = [p.word_count for p in paragraphs]
        avg_words = sum(word_counts) / len(word_counts)
        variance = sum((wc - avg_words) ** 2 for wc in word_counts) / len(word_counts)
        std_dev = variance ** 0.5
        coefficient_of_variation = std_dev / avg_words if avg_words > 0 else 0

        # Find longest section ratio
        # 找出最长部分的比例
        max_words = max(word_counts)
        longest_ratio = max_words / avg_words if avg_words > 0 else 1.0

        # Identify asymmetry opportunities (paragraphs that could be expanded/compressed)
        # 识别非对称机会（可以扩展/压缩的段落）
        asymmetry_opportunities = []

        # Find paragraphs significantly shorter than average (compression candidates)
        # 找出显著短于平均值的段落（压缩候选）
        short_threshold = avg_words * 0.6
        long_threshold = avg_words * 1.4

        for i, p in enumerate(paragraphs):
            if p.word_count < short_threshold:
                asymmetry_opportunities.append({
                    "index": i,
                    "type": "expand_candidate",
                    "current_words": p.word_count,
                    "reason": "Paragraph is significantly shorter than average",
                    "reason_zh": "段落显著短于平均值"
                })
            elif p.word_count > long_threshold:
                asymmetry_opportunities.append({
                    "index": i,
                    "type": "already_expanded",
                    "current_words": p.word_count,
                    "reason": "Paragraph has good depth",
                    "reason_zh": "段落深度良好"
                })

        # Determine distribution type based on coefficient of variation
        # 根据变异系数确定分布类型
        if coefficient_of_variation < 0.2:
            distribution_type = "uniform"
            distribution_type_zh = "均匀分布"
            # High score = AI-like
            score = 80 + int((0.2 - coefficient_of_variation) * 100)
        elif coefficient_of_variation > 0.5:
            distribution_type = "asymmetric"
            distribution_type_zh = "非对称分布"
            # Low score = human-like
            score = max(10, 50 - int((coefficient_of_variation - 0.5) * 60))
        else:
            distribution_type = "balanced"
            distribution_type_zh = "平衡分布"
            # Medium score
            score = 50

        return FunctionDistribution(
            distribution_type=distribution_type,
            distribution_type_zh=distribution_type_zh,
            function_counts=function_counts,
            depth_variance=variance,
            longest_section_ratio=longest_ratio,
            score=min(100, max(0, score)),
            asymmetry_opportunities=asymmetry_opportunities
        )

    # =========================================================================
    # P2 Enhancement: Closure Pattern Detection
    # P2增强：闭合模式检测
    # =========================================================================

    def analyze_closure(self, paragraphs: List[ParagraphInfo]) -> ClosureAnalysis:
        """
        Analyze the closure pattern of the document
        分析文档的闭合模式

        Detects:
        - Strong: Formulaic conclusion with complete resolution (AI-typical)
        - Moderate: Some closure but with open elements
        - Weak: Minimal closure, questions remain
        - Open: Ends with questions or unresolved tension (human-typical)

        Args:
            paragraphs: List of analyzed paragraphs 分析后的段落列表

        Returns:
            ClosureAnalysis with type and score 包含类型和分数的闭合分析
        """
        if not paragraphs:
            return ClosureAnalysis(
                closure_type="unknown",
                closure_type_zh="未知",
                has_formulaic_ending=False,
                has_complete_resolution=False,
                open_questions=0,
                hedging_in_conclusion=0,
                score=50,
                detected_patterns=[]
            )

        # Focus on last 1-2 paragraphs for conclusion analysis
        # 关注最后1-2段进行结论分析
        conclusion_paras = paragraphs[-2:] if len(paragraphs) >= 2 else paragraphs[-1:]
        conclusion_text = " ".join([p.text for p in conclusion_paras])
        conclusion_text_lower = conclusion_text.lower()

        # Check for formulaic conclusion patterns
        # 检查公式化结论模式
        detected_patterns = []
        has_formulaic = False
        for pattern in self.formulaic_conclusion_patterns:
            if pattern.search(conclusion_text):
                has_formulaic = True
                detected_patterns.append(f"formulaic: {pattern.pattern}")

        # Check for open ending patterns
        # 检查开放式结尾模式
        open_questions = 0
        for pattern in self.open_ending_patterns:
            matches = pattern.findall(conclusion_text)
            if matches:
                open_questions += len(matches)
                detected_patterns.append(f"open: {pattern.pattern}")

        # Count hedging words in conclusion
        # 统计结论中的弱化词
        hedging_count = 0
        for hedge in self.HEDGING_WORDS:
            count = conclusion_text_lower.count(hedge.lower())
            hedging_count += count

        # Check for question marks (indicates open questions)
        # 检查问号（表示开放问题）
        question_marks = conclusion_text.count("?")
        open_questions += question_marks

        # Determine if there's complete resolution
        # 确定是否有完全解决
        # Strong resolution indicators
        resolution_words = ["demonstrates", "proves", "confirms", "establishes", "clearly shows"]
        has_complete_resolution = any(word in conclusion_text_lower for word in resolution_words)

        # Calculate closure score and type
        # 计算闭合分数和类型
        score = 50  # Start at neutral

        if has_formulaic:
            score += 30
        if has_complete_resolution:
            score += 20

        if open_questions > 0:
            score -= 15 * min(open_questions, 3)
        if hedging_count > 2:
            score -= 10

        score = max(0, min(100, score))

        # Determine closure type
        # 确定闭合类型
        if score >= 70:
            closure_type = "strong"
            closure_type_zh = "强闭合"
        elif score >= 45:
            closure_type = "moderate"
            closure_type_zh = "中等闭合"
        elif score >= 25:
            closure_type = "weak"
            closure_type_zh = "弱闭合"
        else:
            closure_type = "open"
            closure_type_zh = "开放式"

        return ClosureAnalysis(
            closure_type=closure_type,
            closure_type_zh=closure_type_zh,
            has_formulaic_ending=has_formulaic,
            has_complete_resolution=has_complete_resolution,
            open_questions=open_questions,
            hedging_in_conclusion=hedging_count,
            score=score,
            detected_patterns=detected_patterns
        )

    # =========================================================================
    # P2 Enhancement: Lexical Echo Score
    # P2增强：词汇回声分数
    # =========================================================================

    def analyze_lexical_echo(self, paragraphs: List[ParagraphInfo]) -> LexicalEchoAnalysis:
        """
        Analyze lexical echo between paragraphs
        分析段落间的词汇回声

        Detects whether paragraph transitions use:
        - Explicit connectors (AI-typical): Furthermore, Moreover, However
        - Lexical echo (human-typical): Repeating key concepts from previous paragraph

        Args:
            paragraphs: List of analyzed paragraphs 分析后的段落列表

        Returns:
            LexicalEchoAnalysis with scores and details 包含分数和细节的词汇回声分析
        """
        if len(paragraphs) < 2:
            return LexicalEchoAnalysis(
                total_transitions=0,
                echo_transitions=0,
                explicit_connector_transitions=0,
                echo_ratio=0.0,
                score=50,
                transition_details=[]
            )

        total_transitions = len(paragraphs) - 1
        echo_transitions = 0
        explicit_transitions = 0
        transition_details = []

        for i in range(1, len(paragraphs)):
            prev_para = paragraphs[i - 1]
            curr_para = paragraphs[i]

            # Get key content words from previous paragraph ending
            # 从上一段落结尾获取关键内容词
            prev_ending = prev_para.last_sentence.lower()
            prev_content_words = self._extract_content_words(prev_ending)

            # Get words from current paragraph opening
            # 获取当前段落开头的词
            curr_opening = curr_para.first_sentence.lower()

            # Check for explicit connectors
            # 检查显性连接词
            has_explicit = False
            for connector in self.EXPLICIT_CONNECTORS:
                if curr_opening.startswith(connector.lower()):
                    has_explicit = True
                    explicit_transitions += 1
                    break

            # Check for lexical echo (shared content words)
            # 检查词汇回声（共享内容词）
            curr_content_words = self._extract_content_words(curr_opening)
            shared_words = prev_content_words.intersection(curr_content_words)
            has_echo = len(shared_words) > 0

            if has_echo:
                echo_transitions += 1

            transition_details.append({
                "from_paragraph": i - 1,
                "to_paragraph": i,
                "has_explicit_connector": has_explicit,
                "has_lexical_echo": has_echo,
                "shared_words": list(shared_words),
                "connector_found": next((c for c in self.EXPLICIT_CONNECTORS
                                        if curr_opening.startswith(c.lower())), None)
            })

        # Calculate score (higher = more explicit connectors = AI-like)
        # 计算分数（越高 = 越多显性连接词 = AI风格）
        explicit_ratio = explicit_transitions / total_transitions if total_transitions > 0 else 0
        echo_ratio = echo_transitions / total_transitions if total_transitions > 0 else 0

        # Score: high explicit ratio is AI-like
        score = int(explicit_ratio * 80) + 20 if explicit_ratio > 0 else 20
        # Reduce score if there's good lexical echo
        if echo_ratio > 0.5:
            score = max(10, score - 20)

        return LexicalEchoAnalysis(
            total_transitions=total_transitions,
            echo_transitions=echo_transitions,
            explicit_connector_transitions=explicit_transitions,
            echo_ratio=echo_ratio,
            score=min(100, max(0, score)),
            transition_details=transition_details
        )

    def _extract_content_words(self, text: str) -> set:
        """
        Extract content words (nouns, verbs, adjectives) from text
        从文本中提取内容词（名词、动词、形容词）

        Simple heuristic: words longer than 4 characters that aren't stopwords
        简单启发式：长度超过4个字符且不是停用词的词
        """
        STOPWORDS = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall", "can", "need",
            "this", "that", "these", "those", "it", "its", "they", "them",
            "their", "which", "who", "whom", "what", "when", "where", "why",
            "how", "all", "each", "every", "both", "few", "more", "most",
            "other", "some", "such", "no", "not", "only", "same", "so",
            "than", "too", "very", "just", "also", "now", "here", "there",
        }

        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        return {w for w in words if w not in STOPWORDS}

    # =========================================================================
    # 7th Indicator Enhancement: Cross-Reference Analysis
    # 第7指征增强：交叉引用分析
    # =========================================================================

    def analyze_cross_references(self, paragraphs: List[ParagraphInfo]) -> CrossReferenceAnalysis:
        """
        Analyze cross-referential links in the document
        分析文档中的交叉引用链接

        Detects:
        - Explicit cross-references (as mentioned earlier, returning to...)
        - Core concept callbacks
        - Non-linear structural links

        Args:
            paragraphs: List of analyzed paragraphs 分析后的段落列表

        Returns:
            CrossReferenceAnalysis with detection results 包含检测结果的交叉引用分析
        """
        if len(paragraphs) < 2:
            return CrossReferenceAnalysis(
                has_cross_references=False,
                cross_reference_count=0,
                concept_callbacks=0,
                forward_only_ratio=1.0,
                score=80,  # High score = AI-like (no cross-refs)
                detected_references=[],
                core_concepts=[]
            )

        full_text = " ".join([p.text for p in paragraphs])
        cross_ref_count = 0
        callback_count = 0
        detected_references = []

        # Detect explicit cross-references
        # 检测显式交叉引用
        for i, pattern in enumerate(self.cross_reference_patterns):
            matches = pattern.findall(full_text)
            if matches:
                cross_ref_count += len(matches)
                for match in matches:
                    match_str = match if isinstance(match, str) else " ".join(match)
                    detected_references.append({
                        "type": "cross_reference",
                        "pattern_id": i,
                        "match": match_str
                    })

        # Detect concept callbacks
        # 检测概念回调
        for i, pattern in enumerate(self.concept_callback_patterns):
            matches = pattern.findall(full_text)
            if matches:
                callback_count += len(matches)
                for match in matches:
                    match_str = match if isinstance(match, str) else " ".join(match)
                    detected_references.append({
                        "type": "concept_callback",
                        "pattern_id": i,
                        "match": match_str
                    })

        # Extract core concepts from first paragraph (likely thesis area)
        # 从第一段提取核心概念（可能是论点区域）
        core_concepts = list(self._extract_content_words(paragraphs[0].text))[:5]

        # Check if core concepts appear in later paragraphs (concept echoing)
        # 检查核心概念是否出现在后面的段落中（概念回声）
        concept_echo_count = 0
        for concept in core_concepts:
            for p in paragraphs[2:]:  # Skip first two paragraphs
                if concept.lower() in p.text.lower():
                    concept_echo_count += 1

        # Calculate forward-only ratio
        # 计算单向推进比例
        total_references = cross_ref_count + callback_count + concept_echo_count
        if total_references > 0:
            forward_only_ratio = max(0, 1.0 - (total_references / (len(paragraphs) * 0.5)))
        else:
            forward_only_ratio = 1.0

        # Calculate score (higher = more AI-like, lacking cross-refs)
        # 计算分数（越高 = 越像AI，缺少交叉引用）
        if total_references == 0:
            score = 85
        elif total_references < 2:
            score = 70
        elif total_references < 4:
            score = 50
        else:
            score = max(10, 50 - (total_references * 5))

        return CrossReferenceAnalysis(
            has_cross_references=total_references > 0,
            cross_reference_count=cross_ref_count + callback_count,
            concept_callbacks=concept_echo_count,
            forward_only_ratio=forward_only_ratio,
            score=score,
            detected_references=detected_references,
            core_concepts=core_concepts
        )

    # =========================================================================
    # 7-Indicator Risk Card Generation
    # 7指征风险卡片生成
    # =========================================================================

    def generate_risk_card(self, result: 'StructureAnalysisResult') -> StructuralRiskCard:
        """
        Generate a 7-indicator structural risk card for user visualization
        生成7指征结构风险卡片用于用户可视化

        Args:
            result: Complete structure analysis result 完整结构分析结果

        Returns:
            StructuralRiskCard with all 7 indicators 包含7个指征的风险卡片
        """
        indicators = []

        # 1. Perfect Symmetry (逻辑推进对称)
        # Check if progression is monotonic
        symmetry_triggered = (
            result.progression_analysis and
            result.progression_analysis.progression_type == "monotonic"
        )
        config = self.INDICATOR_CONFIG["symmetry"]
        indicators.append(StructuralIndicator(
            id="symmetry",
            name=config["name"],
            name_zh=config["name_zh"],
            triggered=symmetry_triggered,
            risk_level=config["risk_level"],
            emoji=config["emoji"],
            color=config["color_triggered"] if symmetry_triggered else config["color_safe"],
            description=config["description"],
            description_zh=config["description_zh"],
            details=f"Forward transitions: {result.progression_analysis.forward_transitions}" if result.progression_analysis else "",
            details_zh=f"单向推进: {result.progression_analysis.forward_transitions}次" if result.progression_analysis else ""
        ))

        # 2. Uniform Paragraph Function (段落功能均匀)
        uniform_triggered = (
            result.function_distribution and
            result.function_distribution.distribution_type == "uniform"
        )
        config = self.INDICATOR_CONFIG["uniform_function"]
        indicators.append(StructuralIndicator(
            id="uniform_function",
            name=config["name"],
            name_zh=config["name_zh"],
            triggered=uniform_triggered,
            risk_level=config["risk_level"],
            emoji=config["emoji"],
            color=config["color_triggered"] if uniform_triggered else config["color_safe"],
            description=config["description"],
            description_zh=config["description_zh"],
            details=f"Depth variance: {result.function_distribution.depth_variance:.1f}" if result.function_distribution else "",
            details_zh=f"深度方差: {result.function_distribution.depth_variance:.1f}" if result.function_distribution else ""
        ))

        # 3. Over-signaled Transitions (连接词依赖)
        connector_triggered = (
            result.lexical_echo_analysis and
            result.lexical_echo_analysis.explicit_connector_transitions >= 3
        )
        config = self.INDICATOR_CONFIG["explicit_connectors"]
        indicators.append(StructuralIndicator(
            id="explicit_connectors",
            name=config["name"],
            name_zh=config["name_zh"],
            triggered=connector_triggered,
            risk_level=config["risk_level"],
            emoji=config["emoji"],
            color=config["color_triggered"] if connector_triggered else config["color_safe"],
            description=config["description"],
            description_zh=config["description_zh"],
            details=f"Explicit connectors: {result.lexical_echo_analysis.explicit_connector_transitions}" if result.lexical_echo_analysis else "",
            details_zh=f"显性连接词: {result.lexical_echo_analysis.explicit_connector_transitions}个" if result.lexical_echo_analysis else ""
        ))

        # 4. Linear Enumeration (单一线性推进)
        linear_triggered = result.has_linear_flow
        config = self.INDICATOR_CONFIG["linear_progression"]
        indicators.append(StructuralIndicator(
            id="linear_progression",
            name=config["name"],
            name_zh=config["name_zh"],
            triggered=linear_triggered,
            risk_level=config["risk_level"],
            emoji=config["emoji"],
            color=config["color_triggered"] if linear_triggered else config["color_safe"],
            description=config["description"],
            description_zh=config["description_zh"],
            details="First/Second/Third pattern detected" if linear_triggered else "",
            details_zh="检测到首先/其次/最后模式" if linear_triggered else ""
        ))

        # 5. Rhythmic Regularity (段落节奏均衡)
        rhythm_triggered = result.has_uniform_length
        config = self.INDICATOR_CONFIG["rhythmic_regularity"]
        indicators.append(StructuralIndicator(
            id="rhythmic_regularity",
            name=config["name"],
            name_zh=config["name_zh"],
            triggered=rhythm_triggered,
            risk_level=config["risk_level"],
            emoji=config["emoji"],
            color=config["color_triggered"] if rhythm_triggered else config["color_safe"],
            description=config["description"],
            description_zh=config["description_zh"],
            details=f"Avg length: {result.avg_paragraph_length:.0f} words" if result.avg_paragraph_length else "",
            details_zh=f"平均长度: {result.avg_paragraph_length:.0f}词" if result.avg_paragraph_length else ""
        ))

        # 6. Over-conclusive Ending (结尾过度闭合)
        conclusive_triggered = (
            result.closure_analysis and
            result.closure_analysis.closure_type == "strong"
        )
        config = self.INDICATOR_CONFIG["over_conclusive"]
        indicators.append(StructuralIndicator(
            id="over_conclusive",
            name=config["name"],
            name_zh=config["name_zh"],
            triggered=conclusive_triggered,
            risk_level=config["risk_level"],
            emoji=config["emoji"],
            color=config["color_triggered"] if conclusive_triggered else config["color_safe"],
            description=config["description"],
            description_zh=config["description_zh"],
            details="Formulaic conclusion detected" if (result.closure_analysis and result.closure_analysis.has_formulaic_ending) else "",
            details_zh="检测到公式化结论" if (result.closure_analysis and result.closure_analysis.has_formulaic_ending) else ""
        ))

        # 7. No Cross-References (缺乏回指结构)
        no_crossref_triggered = (
            result.cross_reference_analysis and
            not result.cross_reference_analysis.has_cross_references
        )
        config = self.INDICATOR_CONFIG["no_cross_reference"]
        indicators.append(StructuralIndicator(
            id="no_cross_reference",
            name=config["name"],
            name_zh=config["name_zh"],
            triggered=no_crossref_triggered,
            risk_level=config["risk_level"],
            emoji=config["emoji"],
            color=config["color_triggered"] if no_crossref_triggered else config["color_safe"],
            description=config["description"],
            description_zh=config["description_zh"],
            details=f"Cross-refs found: {result.cross_reference_analysis.cross_reference_count}" if result.cross_reference_analysis else "",
            details_zh=f"交叉引用: {result.cross_reference_analysis.cross_reference_count}个" if result.cross_reference_analysis else ""
        ))

        # Count triggered indicators
        # 统计触发的指征数量
        triggered_count = sum(1 for ind in indicators if ind.triggered)

        # Determine overall risk
        # 确定整体风险
        high_risk_triggered = sum(1 for ind in indicators if ind.triggered and ind.risk_level == 3)

        if triggered_count >= 4 or high_risk_triggered >= 2:
            overall_risk = "high"
            overall_risk_zh = "高风险"
            summary = f"🚨 {triggered_count}/7 AI structural indicators triggered - significant revision needed"
            summary_zh = f"🚨 触发 {triggered_count}/7 项AI结构指征 - 需要显著修改"
        elif triggered_count >= 2:
            overall_risk = "medium"
            overall_risk_zh = "中风险"
            summary = f"⚠️ {triggered_count}/7 AI structural indicators triggered - some revision recommended"
            summary_zh = f"⚠️ 触发 {triggered_count}/7 项AI结构指征 - 建议部分修改"
        else:
            overall_risk = "low"
            overall_risk_zh = "低风险"
            summary = f"✅ {triggered_count}/7 AI structural indicators - structure appears natural"
            summary_zh = f"✅ 仅触发 {triggered_count}/7 项AI结构指征 - 结构看起来自然"

        return StructuralRiskCard(
            indicators=indicators,
            triggered_count=triggered_count,
            overall_risk=overall_risk,
            overall_risk_zh=overall_risk_zh,
            summary=summary,
            summary_zh=summary_zh,
            total_score=result.structure_score
        )
