"""
Explicit Connector Detector Module
显性连接词检测模块

Detects overused AI-style explicit connectors that make text sound
formulaic and machine-generated. These connectors are commonly overused
by AI language models.

检测被AI语言模型过度使用的显性连接词，这些连接词使文本听起来公式化和机器生成。
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConnectorMatch:
    """
    A detected connector match
    检测到的连接词匹配
    """
    connector: str  # The connector word/phrase / 连接词/短语
    position: str  # "sentence_start", "paragraph_start", "mid_sentence"
    severity: str  # "high", "medium", "low"
    sentence_index: int  # Index of the sentence containing the connector
    suggestion: str  # Suggested replacement or action / 建议的替换或操作
    suggestion_zh: str  # Chinese suggestion / 中文建议


@dataclass
class ConnectorAnalysisResult:
    """
    Result of connector analysis
    连接词分析结果
    """
    total_connectors: int  # Total explicit connectors found / 发现的显性连接词总数
    high_severity_count: int  # High severity connectors / 高严重性连接词数量
    medium_severity_count: int  # Medium severity connectors / 中等严重性连接词数量
    risk_score: int  # Contribution to AIGC score (0-30) / 对AIGC分数的贡献
    matches: List[ConnectorMatch]  # Detailed matches / 详细匹配
    density: float  # Connectors per sentence / 每句连接词数
    message: str  # Human-readable summary / 人类可读摘要
    message_zh: str  # Chinese summary / 中文摘要


class ConnectorDetector:
    """
    Detects explicit connectors that are overused by AI.
    检测被AI过度使用的显性连接词。

    Categories:
    类别：
    1. Sentence-start connectors (highest severity) / 句首连接词（最高严重性）
    2. Paragraph-start connectors (high severity) / 段首连接词（高严重性）
    3. Mid-sentence transition phrases (medium severity) / 句中过渡短语（中等严重性）
    """

    # High severity: Classic AI sentence starters
    # 高严重性：经典AI句首词
    HIGH_SEVERITY_CONNECTORS = [
        # Additive connectors / 添加性连接词
        "Furthermore",
        "Moreover",
        "Additionally",
        "In addition",
        "Besides",
        "What's more",

        # Result/Conclusion connectors / 结果/结论连接词
        "Consequently",
        "Therefore",
        "Thus",
        "Hence",
        "Accordingly",
        "As a result",

        # Contrast connectors / 对比连接词
        "However",
        "Nevertheless",
        "Nonetheless",
        "On the other hand",
        "Conversely",

        # Emphasis connectors / 强调连接词
        "Notably",
        "Importantly",
        "Significantly",
        "Crucially",
        "Essentially",

        # Sequence connectors / 顺序连接词
        "Subsequently",
        "Thereafter",
        "Ultimately",
    ]

    # Medium severity: Less obvious but still AI-favored
    # 中等严重性：不太明显但仍受AI青睐
    MEDIUM_SEVERITY_CONNECTORS = [
        # Introductory phrases / 引导短语
        "It is worth noting that",
        "It should be noted that",
        "It is important to note that",
        "It is evident that",
        "It is clear that",

        # Emphasis phrases / 强调短语
        "In particular",
        "Particularly",
        "Specifically",
        "Indeed",
        "In fact",

        # Transition phrases / 过渡短语
        "In this context",
        "In this regard",
        "In light of",
        "With respect to",
        "With regard to",
        "In terms of",

        # Summary phrases / 总结短语
        "In conclusion",
        "To summarize",
        "In summary",
        "To conclude",
        "Overall",
        "All in all",
    ]

    # Paragraph-start patterns (only flagged at paragraph beginning)
    # 段首模式（仅在段落开头标记）
    PARAGRAPH_START_PATTERNS = [
        "First,",
        "Firstly,",
        "Second,",
        "Secondly,",
        "Third,",
        "Thirdly,",
        "Finally,",
        "Lastly,",
        "To begin with,",
        "To start with,",
    ]

    # Replacement suggestions for common connectors
    # 常见连接词的替换建议
    REPLACEMENT_SUGGESTIONS = {
        "Furthermore": ("Remove or rephrase to connect ideas naturally", "删除或自然地重新表述连接"),
        "Moreover": ("Use 'Also' or merge with previous sentence", "使用'Also'或与前句合并"),
        "Additionally": ("Remove or use 'Also'", "删除或使用'Also'"),
        "However": ("Try starting with the contrasting point directly", "尝试直接从对比点开始"),
        "Therefore": ("Remove or integrate conclusion into the sentence", "删除或将结论融入句子"),
        "Thus": ("Remove or use cause-effect structure", "删除或使用因果结构"),
        "Consequently": ("Use 'So' or restructure sentence", "使用'So'或重构句子"),
        "Nevertheless": ("Simplify to 'But' or 'Still'", "简化为'But'或'Still'"),
        "Notably": ("Remove - let the content speak for itself", "删除 - 让内容自己说话"),
        "Importantly": ("Remove - importance should be evident", "删除 - 重要性应该是显而易见的"),
        "In conclusion": ("Use specific summary or remove", "使用具体总结或删除"),
        "It is important to note that": ("Remove this padding phrase", "删除这个填充短语"),
    }

    def __init__(self):
        """Initialize the connector detector."""
        # Compile regex patterns for efficiency
        # 编译正则表达式模式以提高效率
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for connector detection."""
        # Pattern for sentence-start detection (case-insensitive)
        # 句首检测模式（不区分大小写）
        high_pattern = r'^(' + '|'.join(
            re.escape(c) for c in self.HIGH_SEVERITY_CONNECTORS
        ) + r')[,\s]'
        self._high_pattern = re.compile(high_pattern, re.IGNORECASE)

        medium_pattern = r'^(' + '|'.join(
            re.escape(c) for c in self.MEDIUM_SEVERITY_CONNECTORS
        ) + r')[,\s]?'
        self._medium_pattern = re.compile(medium_pattern, re.IGNORECASE)

        para_pattern = r'^(' + '|'.join(
            re.escape(c) for c in self.PARAGRAPH_START_PATTERNS
        ) + r')'
        self._para_pattern = re.compile(para_pattern, re.IGNORECASE)

    def analyze(
        self,
        sentences: List[str],
        paragraph_starts: Optional[List[int]] = None
    ) -> ConnectorAnalysisResult:
        """
        Analyze sentences for explicit connector overuse.
        分析句子中显性连接词的过度使用。

        Args:
            sentences: List of sentences to analyze / 待分析的句子列表
            paragraph_starts: Indices of paragraph-starting sentences / 段落起始句子的索引

        Returns:
            ConnectorAnalysisResult with analysis details / 包含分析详情的ConnectorAnalysisResult
        """
        if paragraph_starts is None:
            paragraph_starts = [0]  # Assume first sentence starts a paragraph

        matches: List[ConnectorMatch] = []
        high_count = 0
        medium_count = 0

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue

            is_para_start = i in paragraph_starts

            # Check high severity connectors
            # 检查高严重性连接词
            high_match = self._high_pattern.match(sentence)
            if high_match:
                connector = high_match.group(1)
                suggestion = self.REPLACEMENT_SUGGESTIONS.get(
                    connector,
                    ("Consider removing or rephrasing", "考虑删除或重新表述")
                )
                matches.append(ConnectorMatch(
                    connector=connector,
                    position="paragraph_start" if is_para_start else "sentence_start",
                    severity="high",
                    sentence_index=i,
                    suggestion=suggestion[0],
                    suggestion_zh=suggestion[1]
                ))
                high_count += 1
                continue  # Don't double-count

            # Check medium severity connectors
            # 检查中等严重性连接词
            medium_match = self._medium_pattern.match(sentence)
            if medium_match:
                connector = medium_match.group(1)
                suggestion = self.REPLACEMENT_SUGGESTIONS.get(
                    connector,
                    ("Consider simplifying this phrase", "考虑简化这个短语")
                )
                matches.append(ConnectorMatch(
                    connector=connector,
                    position="sentence_start",
                    severity="medium",
                    sentence_index=i,
                    suggestion=suggestion[0],
                    suggestion_zh=suggestion[1]
                ))
                medium_count += 1
                continue

            # Check paragraph-start patterns (only for paragraph starts)
            # 检查段首模式（仅限段落开始）
            if is_para_start:
                para_match = self._para_pattern.match(sentence)
                if para_match:
                    connector = para_match.group(1)
                    matches.append(ConnectorMatch(
                        connector=connector,
                        position="paragraph_start",
                        severity="medium",
                        sentence_index=i,
                        suggestion="Avoid enumeration patterns (First, Second...)",
                        suggestion_zh="避免枚举模式（首先、其次...）"
                    ))
                    medium_count += 1

        # Calculate risk score
        # 计算风险分数
        total_connectors = high_count + medium_count
        risk_score = min(30, high_count * 8 + medium_count * 4)

        # Calculate density
        # 计算密度
        density = total_connectors / len(sentences) if sentences else 0

        # Generate message
        # 生成消息
        if total_connectors == 0:
            message = "No explicit AI-style connectors detected. Good variation in sentence starts."
            message_zh = "未检测到显性AI风格连接词。句子开头变化良好。"
        elif high_count >= 3:
            message = f"High connector overuse detected ({high_count} high-severity). Strong AI pattern."
            message_zh = f"检测到连接词过度使用（{high_count}个高严重性）。明显的AI模式。"
        elif total_connectors >= 3:
            message = f"Moderate connector use detected ({total_connectors} total). Some AI indicators."
            message_zh = f"检测到中等程度的连接词使用（共{total_connectors}个）。存在一些AI指标。"
        else:
            message = f"Low connector use ({total_connectors} total). Acceptable pattern."
            message_zh = f"连接词使用较少（共{total_connectors}个）。模式可接受。"

        return ConnectorAnalysisResult(
            total_connectors=total_connectors,
            high_severity_count=high_count,
            medium_severity_count=medium_count,
            risk_score=risk_score,
            matches=matches,
            density=round(density, 2),
            message=message,
            message_zh=message_zh
        )

    def analyze_single_sentence(self, sentence: str) -> Optional[ConnectorMatch]:
        """
        Check if a single sentence starts with an explicit connector.
        检查单个句子是否以显性连接词开头。

        Args:
            sentence: Sentence to check / 待检查的句子

        Returns:
            ConnectorMatch if found, None otherwise / 如果找到返回ConnectorMatch，否则返回None
        """
        sentence = sentence.strip()
        if not sentence:
            return None

        # Check high severity
        high_match = self._high_pattern.match(sentence)
        if high_match:
            connector = high_match.group(1)
            suggestion = self.REPLACEMENT_SUGGESTIONS.get(
                connector,
                ("Consider removing or rephrasing", "考虑删除或重新表述")
            )
            return ConnectorMatch(
                connector=connector,
                position="sentence_start",
                severity="high",
                sentence_index=0,
                suggestion=suggestion[0],
                suggestion_zh=suggestion[1]
            )

        # Check medium severity
        medium_match = self._medium_pattern.match(sentence)
        if medium_match:
            connector = medium_match.group(1)
            suggestion = self.REPLACEMENT_SUGGESTIONS.get(
                connector,
                ("Consider simplifying this phrase", "考虑简化这个短语")
            )
            return ConnectorMatch(
                connector=connector,
                position="sentence_start",
                severity="medium",
                sentence_index=0,
                suggestion=suggestion[0],
                suggestion_zh=suggestion[1]
            )

        return None

    def get_all_connectors(self) -> Dict[str, List[str]]:
        """
        Get all tracked connectors by severity.
        获取按严重性分类的所有跟踪连接词。

        Returns:
            Dictionary with severity levels as keys / 以严重性级别为键的字典
        """
        return {
            "high": self.HIGH_SEVERITY_CONNECTORS.copy(),
            "medium": self.MEDIUM_SEVERITY_CONNECTORS.copy(),
            "paragraph_patterns": self.PARAGRAPH_START_PATTERNS.copy()
        }


# Module-level instance for convenience
# 模块级实例方便使用
_detector = ConnectorDetector()


def detect_connectors(
    sentences: List[str],
    paragraph_starts: Optional[List[int]] = None
) -> ConnectorAnalysisResult:
    """
    Convenience function to detect connectors.
    便捷函数用于检测连接词。

    Args:
        sentences: List of sentences / 句子列表
        paragraph_starts: Optional paragraph start indices / 可选的段落起始索引

    Returns:
        ConnectorAnalysisResult / 连接词分析结果
    """
    return _detector.analyze(sentences, paragraph_starts)


def check_sentence_connector(sentence: str) -> Optional[ConnectorMatch]:
    """
    Convenience function to check a single sentence.
    便捷函数用于检查单个句子。

    Args:
        sentence: Sentence to check / 待检查的句子

    Returns:
        ConnectorMatch if found / 如果找到返回ConnectorMatch
    """
    return _detector.analyze_single_sentence(sentence)
