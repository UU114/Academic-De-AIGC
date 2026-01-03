"""
Paragraph Transition Analyzer (Level 2 De-AIGC)
段落衔接分析器（Level 2 De-AIGC）

Phase 3: Analyzes paragraph transitions for AI-like smoothness patterns
and suggests three transition strategies: semantic echo, logical hook, rhythm break

Phase 3：分析段落衔接的AI风格平滑模式，
提供三种过渡策略：语义回声、逻辑设问、节奏打断
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum


class TransitionStrategy(str, Enum):
    """Transition strategy types 过渡策略类型"""
    SEMANTIC_ECHO = "semantic_echo"  # Use key concepts from para_a in para_b
    LOGICAL_HOOK = "logical_hook"    # Use question or problem-solution pattern
    RHYTHM_BREAK = "rhythm_break"    # Break uniform rhythm with varied structure


@dataclass
class TransitionIssue:
    """
    Detected transition issue
    检测到的衔接问题
    """
    type: str  # "explicit_connector", "too_smooth", "abrupt", "repetitive_opener"
    description: str
    description_zh: str
    severity: str  # "high", "medium", "low"
    position: str  # "para_a_end", "para_b_start", "both"
    word: Optional[str] = None


@dataclass
class TransitionAnalysisResult:
    """
    Result of paragraph transition analysis
    段落衔接分析结果
    """
    # Basic info
    # 基本信息
    para_a_ending: str  # Last 1-2 sentences of paragraph A
    para_b_opening: str  # First 1-2 sentences of paragraph B

    # Scores and levels
    # 分数和等级
    smoothness_score: int  # 0-100, higher = more AI-like smooth
    risk_level: str  # "low", "medium", "high"

    # Issues detected
    # 检测到的问题
    issues: List[TransitionIssue] = field(default_factory=list)

    # Explicit connectors found
    # 发现的显性连接词
    explicit_connectors: List[str] = field(default_factory=list)

    # Analysis details
    # 分析详情
    has_topic_sentence_pattern: bool = False  # Para B starts with topic sentence
    has_summary_ending: bool = False  # Para A ends with summary
    semantic_overlap: float = 0.0  # Keyword overlap ratio

    # Messages
    # 消息
    message: str = ""
    message_zh: str = ""


@dataclass
class TransitionOption:
    """
    A transition repair option
    衔接修复选项
    """
    strategy: TransitionStrategy
    strategy_name_zh: str
    para_a_ending: str  # Modified ending of paragraph A
    para_b_opening: str  # Modified opening of paragraph B
    explanation: str
    explanation_zh: str
    predicted_improvement: int  # Expected smoothness score reduction


class TransitionAnalyzer:
    """
    Analyzes paragraph transitions for AI-like patterns
    分析段落衔接的AI风格模式
    """

    # High-severity transition connectors (AI overuses these)
    # 高严重度过渡连接词（AI过度使用）
    HIGH_SEVERITY_CONNECTORS_EN = [
        "Furthermore", "Moreover", "Additionally", "In addition",
        "Consequently", "Therefore", "Thus", "Hence",
        "However", "Nevertheless", "Nonetheless",
        "In conclusion", "To conclude", "In summary",
        "First", "Firstly", "Second", "Secondly", "Third", "Thirdly", "Finally",
        "On the other hand", "In contrast", "Conversely",
        "As a result", "For this reason",
        "It is important to note", "It should be noted",
        "Notably", "Importantly", "Significantly",
    ]

    # Chinese high-severity connectors (AI fingerprints)
    # 中文高严重度连接词（AI指纹）
    HIGH_SEVERITY_CONNECTORS_ZH = [
        "首先", "其次", "再次", "第一", "第二", "第三",
        "此外", "另外", "除此之外", "不仅如此",
        "因此", "所以", "由此可见", "综上所述", "总之", "总而言之",
        "然而", "但是", "不过", "尽管如此", "相反",
        "另一方面", "与此同时", "同时",
        "值得注意的是", "需要指出的是", "重要的是",
    ]

    # Combined for convenience
    # 合并以便使用
    HIGH_SEVERITY_CONNECTORS = HIGH_SEVERITY_CONNECTORS_EN + HIGH_SEVERITY_CONNECTORS_ZH

    # Medium-severity transition patterns
    # 中严重度过渡模式
    MEDIUM_SEVERITY_PATTERNS = [
        r"^It is (important|worth|necessary) to note that",
        r"^It should be (noted|mentioned|emphasized) that",
        r"^This (section|paragraph|study|paper) (will|aims to|seeks to)",
        r"^Having (discussed|examined|analyzed)",
        r"^Building on (the|this|these)",
        r"^As (mentioned|discussed|noted) (above|earlier|previously)",
        r"^The (following|next|subsequent) (section|paragraph|part)",
    ]

    # Topic sentence patterns (AI tendency)
    # 主题句模式（AI倾向）
    TOPIC_SENTENCE_PATTERNS = [
        r"^The \w+ (of|in|for) \w+ (is|are|plays|demonstrates)",
        r"^This (paper|study|research|analysis) (examines|explores|investigates)",
        r"^(An|The) important (aspect|factor|consideration) (is|of)",
        r"^One (key|crucial|significant) (aspect|factor|element)",
    ]

    # Summary ending patterns
    # 总结结尾模式
    SUMMARY_ENDING_PATTERNS = [
        r"(In summary|To summarize|In conclusion|Overall),?.*\.$",
        r"(Thus|Therefore|Hence|Consequently),? (this|these|the|we).*\.$",
        r"(clearly|evidently|significantly) (demonstrates?|shows?|indicates?).*\.$",
    ]

    def __init__(self):
        """Initialize the transition analyzer 初始化衔接分析器"""
        # Compile patterns for efficiency
        # 预编译模式以提高效率
        self.medium_patterns = [re.compile(p, re.IGNORECASE) for p in self.MEDIUM_SEVERITY_PATTERNS]
        self.topic_patterns = [re.compile(p, re.IGNORECASE) for p in self.TOPIC_SENTENCE_PATTERNS]
        self.summary_patterns = [re.compile(p, re.IGNORECASE) for p in self.SUMMARY_ENDING_PATTERNS]

    def analyze(
        self,
        para_a: str,
        para_b: str,
        context_hint: Optional[str] = None
    ) -> TransitionAnalysisResult:
        """
        Analyze transition between two paragraphs
        分析两个段落之间的衔接

        Args:
            para_a: Previous paragraph 前一段落
            para_b: Next paragraph 后一段落
            context_hint: Optional core thesis from Level 1 可选的核心论点（来自Level 1）

        Returns:
            TransitionAnalysisResult with issues and scores
            包含问题和分数的TransitionAnalysisResult
        """
        # Extract transition zone (ending of A, opening of B)
        # 提取过渡区域（A的结尾，B的开头）
        para_a_ending = self._extract_ending(para_a)
        para_b_opening = self._extract_opening(para_b)

        # Initialize result
        # 初始化结果
        result = TransitionAnalysisResult(
            para_a_ending=para_a_ending,
            para_b_opening=para_b_opening,
            smoothness_score=0,
            risk_level="low"
        )

        issues: List[TransitionIssue] = []
        score = 0

        # 1. Check for explicit connectors in para_b opening
        # 1. 检查段落B开头的显性连接词
        connector_result = self._check_explicit_connectors(para_b_opening)
        if connector_result:
            issues.extend(connector_result["issues"])
            result.explicit_connectors = connector_result["connectors"]
            score += connector_result["score_addition"]

        # 2. Check for medium-severity patterns
        # 2. 检查中等严重度模式
        pattern_result = self._check_medium_patterns(para_b_opening)
        if pattern_result:
            issues.extend(pattern_result["issues"])
            score += pattern_result["score_addition"]

        # 3. Check for topic sentence pattern in para_b
        # 3. 检查段落B的主题句模式
        if self._has_topic_sentence_pattern(para_b_opening):
            result.has_topic_sentence_pattern = True
            issues.append(TransitionIssue(
                type="topic_sentence_pattern",
                description="Paragraph starts with formulaic topic sentence (AI pattern)",
                description_zh="段落以公式化主题句开头（AI模式）",
                severity="medium",
                position="para_b_start"
            ))
            score += 15

        # 4. Check for summary ending in para_a
        # 4. 检查段落A的总结结尾
        if self._has_summary_ending(para_a_ending):
            result.has_summary_ending = True
            issues.append(TransitionIssue(
                type="summary_ending",
                description="Paragraph ends with explicit summary (AI pattern)",
                description_zh="段落以显式总结结尾（AI模式）",
                severity="medium",
                position="para_a_end"
            ))
            score += 15

        # 5. Check semantic overlap (keyword repetition)
        # 5. 检查语义重叠（关键词重复）
        overlap = self._calculate_semantic_overlap(para_a_ending, para_b_opening)
        result.semantic_overlap = overlap
        if overlap > 0.4:  # Too much overlap indicates mechanical connection
            issues.append(TransitionIssue(
                type="high_semantic_overlap",
                description=f"High keyword overlap ({overlap:.0%}) suggests mechanical connection",
                description_zh=f"高关键词重叠率（{overlap:.0%}）表明机械式连接",
                severity="low",
                position="both"
            ))
            score += 10

        # 6. Check for too-smooth transition (both patterns present)
        # 6. 检查过于平滑的衔接（两种模式都存在）
        if result.has_summary_ending and result.has_topic_sentence_pattern:
            issues.append(TransitionIssue(
                type="too_smooth",
                description="Summary + Topic sentence pattern is overly formulaic (strong AI indicator)",
                description_zh="总结+主题句模式过于公式化（强AI特征）",
                severity="high",
                position="both"
            ))
            score += 20

        # Calculate final score and level
        # 计算最终分数和等级
        result.smoothness_score = min(score, 100)
        result.risk_level = self._score_to_level(result.smoothness_score)
        result.issues = issues

        # Generate messages
        # 生成消息
        result.message, result.message_zh = self._generate_messages(result)

        return result

    def _extract_ending(self, paragraph: str) -> str:
        """
        Extract last 1-2 sentences of a paragraph
        提取段落的最后1-2句
        """
        sentences = self._split_sentences(paragraph)
        if len(sentences) >= 2:
            return " ".join(sentences[-2:])
        return paragraph.strip()

    def _extract_opening(self, paragraph: str) -> str:
        """
        Extract first 1-2 sentences of a paragraph
        提取段落的前1-2句
        """
        sentences = self._split_sentences(paragraph)
        if len(sentences) >= 2:
            return " ".join(sentences[:2])
        return paragraph.strip()

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        将文本分割为句子
        """
        # Simple sentence splitter
        # 简单的句子分割器
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _check_explicit_connectors(self, text: str) -> Optional[Dict]:
        """
        Check for high-severity explicit connectors
        检查高严重度显性连接词
        """
        found_connectors = []
        issues = []
        score_addition = 0

        text_lower = text.lower()
        first_word_match = re.match(r'^(\w+)', text)
        first_word = first_word_match.group(1) if first_word_match else ""

        for connector in self.HIGH_SEVERITY_CONNECTORS:
            # Check if connector appears at start of paragraph
            # 检查连接词是否出现在段落开头
            if text_lower.startswith(connector.lower()):
                found_connectors.append(connector)
                issues.append(TransitionIssue(
                    type="explicit_connector",
                    description=f'Starts with explicit connector "{connector}" (AI overuse)',
                    description_zh=f'以显性连接词 "{connector}" 开头（AI过度使用）',
                    severity="high",
                    position="para_b_start",
                    word=connector
                ))
                score_addition += 25
                break  # Only count first connector

        if not found_connectors:
            return None

        return {
            "connectors": found_connectors,
            "issues": issues,
            "score_addition": score_addition
        }

    def _check_medium_patterns(self, text: str) -> Optional[Dict]:
        """
        Check for medium-severity transition patterns
        检查中等严重度过渡模式
        """
        issues = []
        score_addition = 0

        for pattern in self.medium_patterns:
            match = pattern.search(text)
            if match:
                issues.append(TransitionIssue(
                    type="formulaic_opener",
                    description=f'Uses formulaic opener pattern: "{match.group()}"',
                    description_zh=f'使用公式化开头模式："{match.group()}"',
                    severity="medium",
                    position="para_b_start",
                    word=match.group()
                ))
                score_addition += 15
                break  # Only count first pattern

        if not issues:
            return None

        return {
            "issues": issues,
            "score_addition": score_addition
        }

    def _has_topic_sentence_pattern(self, text: str) -> bool:
        """
        Check if text starts with AI-style topic sentence
        检查文本是否以AI风格主题句开头
        """
        for pattern in self.topic_patterns:
            if pattern.search(text):
                return True
        return False

    def _has_summary_ending(self, text: str) -> bool:
        """
        Check if text ends with AI-style summary
        检查文本是否以AI风格总结结尾
        """
        for pattern in self.summary_patterns:
            if pattern.search(text):
                return True
        return False

    def _calculate_semantic_overlap(self, text_a: str, text_b: str) -> float:
        """
        Calculate keyword overlap between two texts
        计算两段文本之间的关键词重叠率
        """
        # Extract content words (remove stop words)
        # 提取内容词（去除停用词）
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "under", "again", "further", "then", "once",
            "this", "that", "these", "those", "it", "its", "they", "their",
            "and", "but", "or", "nor", "so", "yet", "both", "either", "neither"
        }

        def extract_words(text: str) -> set:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            return {w for w in words if w not in stop_words}

        words_a = extract_words(text_a)
        words_b = extract_words(text_b)

        if not words_a or not words_b:
            return 0.0

        overlap = len(words_a & words_b)
        min_size = min(len(words_a), len(words_b))

        return overlap / min_size if min_size > 0 else 0.0

    def _score_to_level(self, score: int) -> str:
        """
        Convert smoothness score to risk level
        将平滑度分数转换为风险等级
        """
        if score >= 50:
            return "high"
        elif score >= 25:
            return "medium"
        return "low"

    def _generate_messages(self, result: TransitionAnalysisResult) -> Tuple[str, str]:
        """
        Generate human-readable messages
        生成人类可读的消息
        """
        if result.smoothness_score < 25:
            return (
                "Transition appears natural with minimal AI patterns.",
                "衔接看起来自然，AI模式较少。"
            )
        elif result.smoothness_score < 50:
            return (
                f"Some AI patterns detected ({len(result.issues)} issues). Consider revising the transition.",
                f"检测到一些AI模式（{len(result.issues)}个问题）。建议修改衔接方式。"
            )
        else:
            return (
                f"Strong AI patterns detected ({len(result.issues)} issues). Transition needs significant revision.",
                f"检测到强AI模式（{len(result.issues)}个问题）。衔接需要大幅修改。"
            )

    def analyze_document_transitions(
        self,
        paragraphs: List[str],
        context_hint: Optional[str] = None
    ) -> List[TransitionAnalysisResult]:
        """
        Analyze all paragraph transitions in a document
        分析文档中所有段落衔接

        Args:
            paragraphs: List of paragraph texts 段落文本列表
            context_hint: Optional core thesis 可选的核心论点

        Returns:
            List of TransitionAnalysisResult for each transition
            每个衔接的TransitionAnalysisResult列表
        """
        results = []

        for i in range(len(paragraphs) - 1):
            result = self.analyze(
                paragraphs[i],
                paragraphs[i + 1],
                context_hint
            )
            results.append(result)

        return results
