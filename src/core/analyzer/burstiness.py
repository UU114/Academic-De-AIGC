"""
Burstiness Analyzer Module
突发性分析模块

Calculates text burstiness (sentence length variation) as a key indicator
of AI-generated vs human-written text. AI text tends to have lower burstiness
(more uniform sentence lengths), while human text shows higher variation.

计算文本突发性（句子长度变化）作为区分AI生成和人类撰写文本的关键指标。
AI文本往往突发性较低（句子长度更均匀），而人类文本变化更大。
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import statistics
import logging

logger = logging.getLogger(__name__)


@dataclass
class BurstinessResult:
    """
    Burstiness analysis result
    突发性分析结果
    """
    burstiness_score: float  # 0-1, higher = more human-like / 越高越像人类
    risk_score: int  # 0-30, higher = more AI-like / 越高越像AI
    risk_level: str  # "low", "medium", "high"
    sentence_lengths: List[int]  # Word counts per sentence / 每句词数
    mean_length: float  # Average sentence length / 平均句长
    std_length: float  # Standard deviation / 标准差
    min_length: int  # Shortest sentence / 最短句
    max_length: int  # Longest sentence / 最长句
    message: str  # Human-readable explanation / 人类可读解释
    message_zh: str  # Chinese explanation / 中文解释


class BurstinessAnalyzer:
    """
    Analyzes text burstiness to detect AI-generated content.
    分析文本突发性以检测AI生成内容。

    Burstiness = std(sentence_length) / mean(sentence_length)

    Thresholds (based on research):
    阈值（基于研究）：
    - burstiness < 0.3: High AI risk (very uniform) / 高AI风险（非常均匀）
    - burstiness 0.3-0.5: Medium risk / 中等风险
    - burstiness > 0.5: Low risk (natural variation) / 低风险（自然变化）
    """

    # Thresholds for burstiness classification
    # 突发性分类阈值
    HIGH_RISK_THRESHOLD = 0.3  # Below this = high AI risk
    MEDIUM_RISK_THRESHOLD = 0.5  # Below this = medium risk

    # Risk score mapping (contribution to total AIGC score)
    # 风险分数映射（对总AIGC分数的贡献）
    HIGH_RISK_SCORE = 25
    MEDIUM_RISK_SCORE = 12
    LOW_RISK_SCORE = 0

    def __init__(self):
        """Initialize the burstiness analyzer."""
        pass

    def analyze(
        self,
        sentences: List[str],
        min_sentences: int = 3
    ) -> BurstinessResult:
        """
        Analyze burstiness of a list of sentences.
        分析句子列表的突发性。

        Args:
            sentences: List of sentences to analyze / 待分析的句子列表
            min_sentences: Minimum sentences required for valid analysis / 有效分析所需的最少句子数

        Returns:
            BurstinessResult with analysis details / 包含分析详情的BurstinessResult
        """
        # Calculate word counts for each sentence
        # 计算每句的词数
        sentence_lengths = [self._count_words(s) for s in sentences]

        # Filter out empty sentences
        # 过滤空句子
        sentence_lengths = [l for l in sentence_lengths if l > 0]

        # Handle edge cases
        # 处理边界情况
        if len(sentence_lengths) < min_sentences:
            return BurstinessResult(
                burstiness_score=0.5,  # Neutral / 中性
                risk_score=0,
                risk_level="unknown",
                sentence_lengths=sentence_lengths,
                mean_length=0,
                std_length=0,
                min_length=0,
                max_length=0,
                message=f"Insufficient sentences ({len(sentence_lengths)}/{min_sentences}) for burstiness analysis",
                message_zh=f"句子数量不足（{len(sentence_lengths)}/{min_sentences}），无法进行突发性分析"
            )

        # Calculate statistics
        # 计算统计数据
        mean_len = statistics.mean(sentence_lengths)
        std_len = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
        min_len = min(sentence_lengths)
        max_len = max(sentence_lengths)

        # Calculate burstiness (coefficient of variation)
        # 计算突发性（变异系数）
        if mean_len > 0:
            burstiness = std_len / mean_len
        else:
            burstiness = 0

        # Normalize to 0-1 range (cap at 1.0)
        # 归一化到0-1范围（上限1.0）
        burstiness_normalized = min(1.0, burstiness)

        # Determine risk level and score
        # 确定风险等级和分数
        if burstiness_normalized < self.HIGH_RISK_THRESHOLD:
            risk_level = "high"
            risk_score = self.HIGH_RISK_SCORE
            message = f"Very uniform sentence lengths (burstiness={burstiness_normalized:.2f}). Strong AI pattern."
            message_zh = f"句子长度非常均匀（突发性={burstiness_normalized:.2f}）。明显的AI特征。"
        elif burstiness_normalized < self.MEDIUM_RISK_THRESHOLD:
            risk_level = "medium"
            risk_score = self.MEDIUM_RISK_SCORE
            message = f"Moderately uniform sentence lengths (burstiness={burstiness_normalized:.2f}). Some AI indicators."
            message_zh = f"句子长度较为均匀（突发性={burstiness_normalized:.2f}）。存在一些AI指标。"
        else:
            risk_level = "low"
            risk_score = self.LOW_RISK_SCORE
            message = f"Natural sentence length variation (burstiness={burstiness_normalized:.2f}). Human-like pattern."
            message_zh = f"句子长度变化自然（突发性={burstiness_normalized:.2f}）。类似人类写作模式。"

        return BurstinessResult(
            burstiness_score=burstiness_normalized,
            risk_score=risk_score,
            risk_level=risk_level,
            sentence_lengths=sentence_lengths,
            mean_length=round(mean_len, 1),
            std_length=round(std_len, 1),
            min_length=min_len,
            max_length=max_len,
            message=message,
            message_zh=message_zh
        )

    def analyze_text(self, text: str) -> BurstinessResult:
        """
        Analyze burstiness of raw text by first splitting into sentences.
        通过先分句来分析原始文本的突发性。

        Args:
            text: Raw text to analyze / 待分析的原始文本

        Returns:
            BurstinessResult with analysis details / 包含分析详情的BurstinessResult
        """
        sentences = self._split_sentences(text)
        return self.analyze(sentences)

    def analyze_paragraph(
        self,
        sentences: List[str]
    ) -> BurstinessResult:
        """
        Analyze burstiness at paragraph level (typically 3-10 sentences).
        在段落级别分析突发性（通常3-10句）。

        Uses lower minimum sentence requirement for paragraph-level analysis.
        对段落级分析使用较低的最少句子要求。

        Args:
            sentences: Sentences in the paragraph / 段落中的句子

        Returns:
            BurstinessResult / 突发性分析结果
        """
        return self.analyze(sentences, min_sentences=2)

    def _count_words(self, sentence: str) -> int:
        """
        Count words in a sentence.
        计算句子中的词数。

        Args:
            sentence: Sentence to count words in / 待计算词数的句子

        Returns:
            Word count / 词数
        """
        if not sentence or not sentence.strip():
            return 0

        # Split on whitespace and filter empty tokens
        # 按空白分割并过滤空token
        words = sentence.strip().split()
        return len(words)

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences for analysis.
        将文本分割成句子用于分析。

        Simple sentence splitting for burstiness calculation.
        用于突发性计算的简单分句。

        Args:
            text: Text to split / 待分割的文本

        Returns:
            List of sentences / 句子列表
        """
        import re

        if not text:
            return []

        # Split on sentence-ending punctuation
        # 按句末标点分割
        # Handles: . ! ? and their combinations with quotes
        pattern = r'(?<=[.!?])\s+'
        sentences = re.split(pattern, text.strip())

        # Filter empty and very short sentences
        # 过滤空句和极短句
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]

        return sentences

    def get_improvement_suggestions(
        self,
        result: BurstinessResult
    ) -> List[str]:
        """
        Get suggestions for improving burstiness (making text more human-like).
        获取改善突发性的建议（使文本更像人类）。

        Args:
            result: BurstinessResult from analyze() / analyze()的BurstinessResult

        Returns:
            List of improvement suggestions / 改进建议列表
        """
        suggestions = []

        if result.risk_level == "high":
            suggestions.append(
                "Vary sentence lengths more - mix short punchy sentences with longer complex ones"
            )
            suggestions.append(
                "Break up some long sentences into shorter ones"
            )
            suggestions.append(
                "Combine some short related sentences into compound sentences"
            )

        elif result.risk_level == "medium":
            suggestions.append(
                "Add a few shorter sentences for emphasis or transition"
            )
            suggestions.append(
                "Consider varying paragraph opening sentence lengths"
            )

        # Add specific suggestions based on statistics
        # 根据统计数据添加具体建议
        if result.mean_length > 25:
            suggestions.append(
                f"Average sentence length ({result.mean_length:.0f} words) is high - consider shorter sentences"
            )
        elif result.mean_length < 10:
            suggestions.append(
                f"Average sentence length ({result.mean_length:.0f} words) is low - consider more complex sentences"
            )

        if result.max_length - result.min_length < 10 and result.risk_level != "low":
            suggestions.append(
                f"Sentence length range ({result.min_length}-{result.max_length} words) is narrow - add more variety"
            )

        return suggestions


# Module-level instance for convenience
# 模块级实例方便使用
_analyzer = BurstinessAnalyzer()


def analyze_burstiness(sentences: List[str]) -> BurstinessResult:
    """
    Convenience function to analyze burstiness.
    便捷函数用于分析突发性。

    Args:
        sentences: List of sentences / 句子列表

    Returns:
        BurstinessResult / 突发性分析结果
    """
    return _analyzer.analyze(sentences)


def analyze_text_burstiness(text: str) -> BurstinessResult:
    """
    Convenience function to analyze text burstiness.
    便捷函数用于分析文本突发性。

    Args:
        text: Raw text / 原始文本

    Returns:
        BurstinessResult / 突发性分析结果
    """
    return _analyzer.analyze_text(text)
