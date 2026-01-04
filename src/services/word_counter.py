"""
Word Counter Service for AcademicGuard
AcademicGuard 字数统计服务

This module provides word counting and billing calculation services.
此模块提供字数统计和计费计算服务。

Billing Rules (计费规则):
- Price: 2 RMB per 100 words (单价：2元/100词)
- Minimum charge: 50 RMB (最低消费：50元)
- Billing unit: 100 words, round up (计费单元：100词，向上取整)
- Exclude: References, Bibliography, Works Cited sections (排除：参考文献部分)
"""

import re
import math
import hashlib
from typing import Tuple, Optional
from pydantic import BaseModel


class WordCountResult(BaseModel):
    """
    Word counting result
    字数统计结果
    """
    raw_word_count: int          # Original word count (原始字数)
    clean_word_count: int        # Cleaned word count excluding references (排除参考文献后字数)
    billable_units: int          # Billing units, 100 words per unit, round up (计费单元数)
    has_references: bool         # Whether references section was detected (是否检测到参考文献)
    content_hash: Optional[str] = None  # SHA-256 hash of cleaned content (清洗后内容哈希)


class PriceResult(BaseModel):
    """
    Price calculation result
    价格计算结果
    """
    calculated_price: float      # Calculated price before minimum (计算价格)
    final_price: float           # Final price after minimum applied (最终价格)
    is_minimum_charge: bool      # Whether minimum charge was applied (是否触发最低消费)
    billable_units: int          # Number of billing units (计费单元数)


class WordCounter:
    """
    Word counter for academic text billing
    学术文本计费字数统计器
    """

    # Reference section markers (参考文献标记)
    REF_MARKERS = [
        r"^\s*references?\s*$",
        r"^\s*bibliography\s*$",
        r"^\s*works?\s+cited\s*$",
        r"^\s*reference\s+list\s*$",
        r"^\s*cited\s+works?\s*$",
        r"^\s*参考文献\s*$",
        r"^\s*引用文献\s*$",
        r"^\s*文献引用\s*$",
    ]

    def __init__(
        self,
        price_per_100_words: float = 2.0,
        minimum_charge: float = 50.0
    ):
        """
        Initialize word counter with pricing settings
        初始化字数统计器和定价设置

        Args:
            price_per_100_words: Price per 100 words in RMB (每100词价格，单位人民币)
            minimum_charge: Minimum charge threshold (最低消费门槛)
        """
        self.price_per_100_words = price_per_100_words
        self.minimum_charge = minimum_charge

    def _strip_references(self, text: str) -> Tuple[str, bool]:
        """
        Remove reference section from text
        从文本中移除参考文献部分

        Args:
            text: Full document text

        Returns:
            Tuple of (cleaned_text, has_references)
        """
        lines = text.split('\n')
        clean_lines = []
        has_refs = False

        for line in lines:
            # Check if this line is a reference marker
            # 检查此行是否为参考文献标记
            is_ref_marker = any(
                re.match(marker, line.strip(), re.IGNORECASE)
                for marker in self.REF_MARKERS
            )
            if is_ref_marker:
                has_refs = True
                break  # Stop at reference section
            clean_lines.append(line)

        return "\n".join(clean_lines), has_refs

    def _count_words(self, text: str) -> int:
        """
        Count words in text (English-focused, academic style)
        统计文本中的单词数（以英文学术风格为主）

        This counts:
        - English words (alphabetic sequences)
        - Hyphenated words as single words
        - Contractions as single words

        Args:
            text: Text to count

        Returns:
            Word count
        """
        # Remove URLs and email addresses
        # 移除URL和电子邮件地址
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\S+@\S+\.\S+', '', text)

        # Find all words (including hyphenated and contracted)
        # 查找所有单词（包括连字符和缩写）
        words = re.findall(r"\b[a-zA-Z]+(?:[-'][a-zA-Z]+)*\b", text)

        return len(words)

    def _calculate_hash(self, text: str) -> str:
        """
        Calculate SHA-256 hash of text
        计算文本的SHA-256哈希值

        Args:
            text: Text to hash

        Returns:
            Hex digest of SHA-256 hash
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def count(self, text: str, calculate_hash: bool = True) -> WordCountResult:
        """
        Count billable words in text
        统计文本中的计费字数

        Args:
            text: Full document text
            calculate_hash: Whether to calculate content hash (是否计算内容哈希)

        Returns:
            WordCountResult with all counting metrics
        """
        # Count raw words
        # 统计原始字数
        raw_count = self._count_words(text)

        # Strip references and count clean words
        # 剔除参考文献并统计清洗后字数
        clean_text, has_refs = self._strip_references(text)
        clean_count = self._count_words(clean_text)

        # Calculate billable units (100 words per unit, round up)
        # 计算计费单元（100词/单元，向上取整）
        billable_units = math.ceil(clean_count / 100) if clean_count > 0 else 0

        # Calculate hash if requested
        # 如果需要则计算哈希
        content_hash = self._calculate_hash(clean_text) if calculate_hash else None

        return WordCountResult(
            raw_word_count=raw_count,
            clean_word_count=clean_count,
            billable_units=billable_units,
            has_references=has_refs,
            content_hash=content_hash
        )

    def calculate_price(self, word_count_result: WordCountResult) -> PriceResult:
        """
        Calculate price based on word count result
        根据字数统计结果计算价格

        Args:
            word_count_result: Result from count() method

        Returns:
            PriceResult with pricing details
        """
        # Calculate price: units * price_per_100_words
        # 计算价格：单元数 * 每100词价格
        calculated = word_count_result.billable_units * self.price_per_100_words

        # Apply minimum charge
        # 应用最低消费
        is_minimum = calculated < self.minimum_charge
        final_price = max(self.minimum_charge, calculated)

        return PriceResult(
            calculated_price=calculated,
            final_price=final_price,
            is_minimum_charge=is_minimum,
            billable_units=word_count_result.billable_units
        )

    def count_and_price(self, text: str) -> Tuple[WordCountResult, PriceResult]:
        """
        Convenience method to count words and calculate price in one call
        便捷方法：一次调用完成字数统计和价格计算

        Args:
            text: Full document text

        Returns:
            Tuple of (WordCountResult, PriceResult)
        """
        count_result = self.count(text)
        price_result = self.calculate_price(count_result)
        return count_result, price_result


# Default instance with standard pricing
# 使用标准定价的默认实例
def get_word_counter() -> WordCounter:
    """
    Get word counter instance with settings from config
    获取使用配置中设置的字数统计器实例
    """
    from src.config import get_settings

    settings = get_settings()
    return WordCounter(
        price_per_100_words=settings.price_per_100_words,
        minimum_charge=settings.minimum_charge
    )
