"""
Syntactic Void Detector - Detects semantically empty but grammatically correct AI patterns
句法空洞检测器 - 检测语法正确但语义空洞的AI模式

Part of DEAI Engine 2.0 - Layer 2 (Syntactic Void Detection)
DEAI引擎2.0的一部分 - 第二层（句法空洞检测）

This module uses spaCy's dependency parsing to detect "flowery but empty" constructions
that are characteristic of AI-generated text. These patterns are syntactically complex
but carry little semantic content.
此模块使用spaCy的依存句法分析来检测AI生成文本特有的"华丽但空洞"结构。
这些模式在句法上复杂，但语义内容很少。
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Any
from enum import Enum

logger = logging.getLogger(__name__)

# Track spaCy availability
# 跟踪spaCy可用性
_spacy_available = False
_nlp = None


def _init_spacy():
    """
    Initialize spaCy with en_core_web_md model
    使用en_core_web_md模型初始化spaCy
    """
    global _spacy_available, _nlp

    if _nlp is not None:
        return _spacy_available

    try:
        import spacy
        try:
            _nlp = spacy.load("en_core_web_md")
            _spacy_available = True
            logger.info("spaCy en_core_web_md model loaded successfully")
        except OSError:
            # Try smaller model as fallback
            # 尝试使用更小的模型作为后备
            try:
                _nlp = spacy.load("en_core_web_sm")
                _spacy_available = True
                logger.warning("Using en_core_web_sm model (en_core_web_md not found)")
            except OSError:
                logger.warning(
                    "spaCy model not found. Install with: "
                    "python -m spacy download en_core_web_md"
                )
                _spacy_available = False
    except ImportError:
        logger.warning("spaCy not installed. Install with: pip install spacy")
        _spacy_available = False

    return _spacy_available


class VoidPatternType(Enum):
    """Types of syntactic void patterns"""
    ABSTRACT_VERB_NOUN = "abstract_verb_noun"  # "underscores the significance"
    TESTAMENT_PHRASE = "testament_phrase"  # "serves as a testament to"
    PIVOTAL_ROLE = "pivotal_role"  # "plays a pivotal role in"
    LANDSCAPE_PHRASE = "landscape_phrase"  # "in the comprehensive landscape of"
    EMPTY_FILLER = "empty_filler"  # "it is important to note that"
    CHARACTERIZED_BY = "characterized_by"  # "is characterized by"
    OFFERS_PATHWAY = "offers_pathway"  # "offers a novel pathway/approach"


@dataclass
class VoidMatch:
    """
    Represents a detected syntactic void pattern
    表示检测到的句法空洞模式
    """
    pattern_type: VoidPatternType
    matched_text: str
    position: int
    end_position: int
    severity: str  # high, medium, low
    abstract_words: List[str]  # The abstract words involved
    suggestion: str
    suggestion_zh: str


@dataclass
class SyntacticVoidResult:
    """
    Result of syntactic void analysis
    句法空洞分析结果
    """
    void_score: int  # 0-100, higher = more void patterns
    matches: List[VoidMatch]
    has_critical_void: bool  # Has high-severity void
    void_density: float  # Voids per 100 words
    sentence_count: int
    void_sentence_count: int


class SyntacticVoidDetector:
    """
    Detector for semantically empty but grammatically correct patterns
    语义空洞但语法正确模式的检测器

    Uses both regex patterns (fast) and spaCy dependency parsing (accurate)
    to detect AI-characteristic "flowery but empty" constructions.
    使用正则表达式模式（快速）和spaCy依存句法分析（准确）
    来检测AI特有的"华丽但空洞"结构。
    """

    # Abstract verbs often used in void patterns
    # 空洞模式中常用的抽象动词
    ABSTRACT_VERBS = {
        "underscore", "underscores", "underscoring", "underscored",
        "highlight", "highlights", "highlighting", "highlighted",
        "exemplify", "exemplifies", "exemplifying", "exemplified",
        "demonstrate", "demonstrates", "demonstrating", "demonstrated",
        "illustrate", "illustrates", "illustrating", "illustrated",
        "showcase", "showcases", "showcasing", "showcased",
        "emphasize", "emphasizes", "emphasizing", "emphasized",
        "signify", "signifies", "signifying", "signified",
        "epitomize", "epitomizes", "epitomizing", "epitomized",
        "encapsulate", "encapsulates", "encapsulating", "encapsulated",
        "embody", "embodies", "embodying", "embodied",
    }

    # Abstract nouns that often appear in void patterns
    # 空洞模式中常出现的抽象名词
    ABSTRACT_NOUNS = {
        "significance", "importance", "relevance", "nuance", "nuances",
        "complexity", "complexities", "intricacy", "intricacies",
        "landscape", "tapestry", "framework", "paradigm",
        "dynamic", "dynamics", "interplay", "intersection",
        "trajectory", "evolution", "transformation", "dimension",
        "facet", "facets", "aspect", "aspects",
        "essence", "nature", "character", "fabric",
        "realm", "domain", "sphere", "scope",
        "magnitude", "scale", "extent", "depth",
    }

    # Regex patterns for void detection (fast path)
    # 空洞检测的正则表达式模式（快速路径）
    VOID_REGEX_PATTERNS = [
        # Pattern: "underscores/highlights the significance/importance of"
        (
            r'\b(underscores?|highlights?|exemplif(?:y|ies)|demonstrates?|illustrates?)\s+'
            r'the\s+(significance|importance|relevance|nuance|complexity|intricacy)\s+of\b',
            VoidPatternType.ABSTRACT_VERB_NOUN,
            "high"
        ),
        # Pattern: "serves as a testament to"
        (
            r'\bserves?\s+as\s+a\s+testament\s+to\b',
            VoidPatternType.TESTAMENT_PHRASE,
            "high"
        ),
        # Pattern: "plays a pivotal/crucial/vital role in"
        (
            r'\bplays?\s+a\s+(pivotal|crucial|vital|critical|key|central|important)\s+role\s+in\b',
            VoidPatternType.PIVOTAL_ROLE,
            "high"
        ),
        # Pattern: "in the comprehensive/evolving landscape of"
        (
            r'\bin\s+the\s+(comprehensive|evolving|dynamic|complex|intricate|broader)\s+'
            r'(landscape|tapestry|framework|paradigm|context)\s+of\b',
            VoidPatternType.LANDSCAPE_PHRASE,
            "high"
        ),
        # Pattern: "it is important/worth/crucial to note that"
        (
            r'\bit\s+is\s+(important|worth|crucial|essential|vital|notable|noteworthy)\s+to\s+'
            r'(note|mention|highlight|emphasize|stress|observe)\s+that\b',
            VoidPatternType.EMPTY_FILLER,
            "medium"
        ),
        # Pattern: "is characterized by"
        (
            r'\bis\s+characterized\s+by\b',
            VoidPatternType.CHARACTERIZED_BY,
            "medium"
        ),
        # Pattern: "offers/provides a novel/innovative pathway/approach/framework"
        (
            r'\b(offers?|provides?)\s+a\s+'
            r'(novel|innovative|unique|comprehensive|robust|promising)\s+'
            r'(pathway|approach|framework|solution|perspective|avenue)\b',
            VoidPatternType.OFFERS_PATHWAY,
            "medium"
        ),
        # Pattern: "the multifaceted nature of"
        (
            r'\bthe\s+(multifaceted|intricate|complex|dynamic|evolving)\s+'
            r'(nature|character|essence|aspect)\s+of\b',
            VoidPatternType.ABSTRACT_VERB_NOUN,
            "high"
        ),
        # Pattern: "within the realm/scope of"
        (
            r'\bwithin\s+the\s+(realm|scope|domain|sphere|context)\s+of\b',
            VoidPatternType.LANDSCAPE_PHRASE,
            "medium"
        ),
        # Pattern: "at the intersection of X and Y"
        (
            r'\bat\s+the\s+(intersection|confluence|nexus|crossroads)\s+of\b',
            VoidPatternType.LANDSCAPE_PHRASE,
            "medium"
        ),
    ]

    # Suggestions for each pattern type
    # 每种模式类型的建议
    SUGGESTIONS = {
        VoidPatternType.ABSTRACT_VERB_NOUN: {
            "en": "Replace abstract verb+noun with concrete action. E.g., 'shows' instead of 'underscores the significance of'",
            "zh": "用具体动作替换抽象动词+名词。例如用 'shows' 替代 'underscores the significance of'"
        },
        VoidPatternType.TESTAMENT_PHRASE: {
            "en": "Remove 'serves as a testament to' - just state the evidence directly",
            "zh": "删除 'serves as a testament to' - 直接陈述证据"
        },
        VoidPatternType.PIVOTAL_ROLE: {
            "en": "Replace with specific function. E.g., 'X enables Y' instead of 'X plays a pivotal role in Y'",
            "zh": "用具体功能替换。例如用 'X enables Y' 替代 'X plays a pivotal role in Y'"
        },
        VoidPatternType.LANDSCAPE_PHRASE: {
            "en": "Remove metaphorical landscape phrases - use direct reference to the field",
            "zh": "删除隐喻性的landscape短语 - 直接引用领域"
        },
        VoidPatternType.EMPTY_FILLER: {
            "en": "Delete the filler phrase entirely - start with the actual point",
            "zh": "完全删除填充短语 - 直接从要点开始"
        },
        VoidPatternType.CHARACTERIZED_BY: {
            "en": "Replace with more direct description. E.g., 'X has/includes' instead of 'X is characterized by'",
            "zh": "用更直接的描述替换。例如用 'X has/includes' 替代 'X is characterized by'"
        },
        VoidPatternType.OFFERS_PATHWAY: {
            "en": "State what the approach actually does instead of vague 'offers a pathway'",
            "zh": "陈述方法实际做什么，而不是模糊的 'offers a pathway'"
        },
    }

    def __init__(self, use_spacy: bool = True):
        """
        Initialize detector
        初始化检测器

        Args:
            use_spacy: Whether to use spaCy for deep analysis (slower but more accurate)
        """
        self.use_spacy = use_spacy
        if use_spacy:
            _init_spacy()

        # Compile regex patterns
        # 编译正则表达式模式
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), ptype, severity)
            for pattern, ptype, severity in self.VOID_REGEX_PATTERNS
        ]

    def detect(self, text: str) -> SyntacticVoidResult:
        """
        Detect syntactic void patterns in text
        检测文本中的句法空洞模式

        Args:
            text: Input text to analyze

        Returns:
            SyntacticVoidResult with detected patterns
        """
        matches = []

        # Fast path: regex detection
        # 快速路径：正则表达式检测
        regex_matches = self._detect_regex(text)
        matches.extend(regex_matches)

        # Slow path: spaCy dependency parsing (if enabled and available)
        # 慢速路径：spaCy依存句法分析（如果启用且可用）
        if self.use_spacy and _spacy_available:
            spacy_matches = self._detect_spacy(text)
            # Merge matches, avoiding duplicates
            # 合并匹配，避免重复
            existing_positions = {(m.position, m.end_position) for m in matches}
            for sm in spacy_matches:
                if (sm.position, sm.end_position) not in existing_positions:
                    matches.append(sm)

        # Calculate statistics
        # 计算统计数据
        word_count = len(text.split())
        sentence_count = len([s for s in re.split(r'[.!?]+', text) if s.strip()])
        void_sentence_count = len(set(m.position // 100 for m in matches))  # Approximate

        void_density = (len(matches) / max(1, word_count)) * 100

        # Calculate void score
        # 计算空洞分数
        void_score = self._calculate_void_score(matches, word_count)

        has_critical = any(m.severity == "high" for m in matches)

        return SyntacticVoidResult(
            void_score=void_score,
            matches=matches,
            has_critical_void=has_critical,
            void_density=void_density,
            sentence_count=sentence_count,
            void_sentence_count=void_sentence_count
        )

    def _detect_regex(self, text: str) -> List[VoidMatch]:
        """
        Detect void patterns using regex
        使用正则表达式检测空洞模式
        """
        matches = []

        for pattern, ptype, severity in self.compiled_patterns:
            for match in pattern.finditer(text):
                # Extract abstract words from match
                # 从匹配中提取抽象词
                matched_text = match.group(0)
                abstract_words = self._extract_abstract_words(matched_text)

                suggestion_info = self.SUGGESTIONS.get(ptype, {"en": "", "zh": ""})

                matches.append(VoidMatch(
                    pattern_type=ptype,
                    matched_text=matched_text,
                    position=match.start(),
                    end_position=match.end(),
                    severity=severity,
                    abstract_words=abstract_words,
                    suggestion=suggestion_info["en"],
                    suggestion_zh=suggestion_info["zh"]
                ))

        return matches

    def _detect_spacy(self, text: str) -> List[VoidMatch]:
        """
        Detect void patterns using spaCy dependency parsing
        使用spaCy依存句法分析检测空洞模式
        """
        global _nlp
        if not _spacy_available or _nlp is None:
            return []

        matches = []

        try:
            doc = _nlp(text)

            for sent in doc.sents:
                # Look for abstract verb + abstract noun patterns
                # 寻找抽象动词 + 抽象名词模式
                for token in sent:
                    # Check if token is an abstract verb
                    # 检查token是否是抽象动词
                    if token.lemma_.lower() in {
                        "underscore", "highlight", "exemplify", "demonstrate",
                        "illustrate", "showcase", "emphasize", "signify"
                    }:
                        # Look for direct object that is abstract noun
                        # 寻找作为抽象名词的直接宾语
                        for child in token.children:
                            if child.dep_ in ("dobj", "attr", "pobj"):
                                if child.lemma_.lower() in self.ABSTRACT_NOUNS:
                                    # Found abstract verb + abstract noun
                                    # 找到抽象动词 + 抽象名词
                                    start = min(token.idx, child.idx)
                                    end = max(
                                        token.idx + len(token.text),
                                        child.idx + len(child.text)
                                    )

                                    # Get the full phrase
                                    # 获取完整短语
                                    phrase_text = text[start:end + 20].split('.')[0]

                                    matches.append(VoidMatch(
                                        pattern_type=VoidPatternType.ABSTRACT_VERB_NOUN,
                                        matched_text=phrase_text,
                                        position=start,
                                        end_position=end,
                                        severity="medium",
                                        abstract_words=[token.text, child.text],
                                        suggestion=self.SUGGESTIONS[VoidPatternType.ABSTRACT_VERB_NOUN]["en"],
                                        suggestion_zh=self.SUGGESTIONS[VoidPatternType.ABSTRACT_VERB_NOUN]["zh"]
                                    ))

        except Exception as e:
            logger.warning(f"spaCy analysis failed: {e}")

        return matches

    def _extract_abstract_words(self, text: str) -> List[str]:
        """
        Extract abstract words from matched text
        从匹配文本中提取抽象词
        """
        words = text.lower().split()
        abstract = []

        for word in words:
            # Remove punctuation
            # 移除标点
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in self.ABSTRACT_VERBS or clean_word in self.ABSTRACT_NOUNS:
                abstract.append(clean_word)

        return abstract

    def _calculate_void_score(self, matches: List[VoidMatch], word_count: int) -> int:
        """
        Calculate overall void score
        计算整体空洞分数
        """
        if not matches:
            return 0

        # Base score from match count and severity
        # 基于匹配数量和严重程度的基础分数
        severity_weights = {"high": 20, "medium": 12, "low": 5}
        base_score = sum(severity_weights.get(m.severity, 10) for m in matches)

        # Density multiplier
        # 密度乘数
        if word_count > 0:
            density = len(matches) / word_count * 100
            if density > 5:
                base_score = int(base_score * 1.5)
            elif density > 2:
                base_score = int(base_score * 1.2)

        return min(100, base_score)


# Convenience function
# 便捷函数
def detect_syntactic_voids(text: str, use_spacy: bool = True) -> SyntacticVoidResult:
    """
    Convenience function to detect syntactic voids
    检测句法空洞的便捷函数

    Args:
        text: Input text to analyze
        use_spacy: Whether to use spaCy (slower but more accurate)

    Returns:
        SyntacticVoidResult with detected patterns
    """
    detector = SyntacticVoidDetector(use_spacy=use_spacy)
    return detector.detect(text)
