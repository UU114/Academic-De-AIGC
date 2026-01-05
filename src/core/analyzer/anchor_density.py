"""
Academic Anchor Density Analyzer - Detects "hallucination risk" in AI-generated text
学术锚点密度分析器 - 检测AI生成文本中的"幻觉风险"

Part of DEAI Engine 2.0 - Layer 3 (Information Density & Anchors)
DEAI引擎2.0的一部分 - 第三层（信息密度与锚点）

This module calculates the density of "academic anchors" - concrete elements that
ground text in real evidence:
- Specific numbers and statistics
- Citations and references
- Units and measurements
- Technical acronyms
- Proper nouns

Low anchor density in a long paragraph suggests the content may be AI-generated
"filler" without real substantive information (hallucination risk).
此模块计算"学术锚点"的密度 - 这些具体元素将文本建立在真实证据之上：
- 具体数字和统计数据
- 引用和参考文献
- 单位和测量值
- 技术缩写
- 专有名词

长段落中低锚点密度表明内容可能是AI生成的没有真实实质性信息的"填充物"（幻觉风险）。
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum

logger = logging.getLogger(__name__)


class AnchorType(Enum):
    """Types of academic anchors"""
    DECIMAL_NUMBER = "decimal_number"  # 14.2, 3.5
    PERCENTAGE = "percentage"  # 50%, 14.2%
    STATISTICAL_VALUE = "statistical_value"  # p < 0.05, r = 0.82
    SAMPLE_SIZE = "sample_size"  # n = 500, N = 1000
    CITATION_BRACKET = "citation_bracket"  # [1], [2,3]
    CITATION_AUTHOR = "citation_author"  # (Smith, 2020), (Jones et al., 2021)
    UNIT_MEASUREMENT = "unit_measurement"  # 5mL, 20°C, 3.5kg
    CHEMICAL_FORMULA = "chemical_formula"  # H2O, CO2, NaCl
    SPECIFIC_COUNT = "specific_count"  # 500 samples, 3 groups
    SCIENTIFIC_NOTATION = "scientific_notation"  # 1.5e-3, 2.0×10^6
    ACRONYM = "acronym"  # ANOVA, CNN, LSTM
    EQUATION_REF = "equation_ref"  # Eq. 1, Equation (2)
    FIGURE_TABLE_REF = "figure_table_ref"  # Fig. 1, Table 2
    PROPER_NOUN = "proper_noun"  # Specific names, places


@dataclass
class AnchorMatch:
    """
    Represents a detected academic anchor
    表示检测到的学术锚点
    """
    anchor_type: AnchorType
    matched_text: str
    position: int
    end_position: int
    weight: float  # Importance weight (1.0 = standard)


@dataclass
class ParagraphAnchorAnalysis:
    """
    Anchor analysis for a single paragraph
    单个段落的锚点分析
    """
    paragraph_index: int
    text: str
    word_count: int
    anchor_count: int
    anchor_density: float  # Anchors per 100 words
    anchors: List[AnchorMatch]
    has_hallucination_risk: bool
    risk_level: str  # low, medium, high
    risk_reason: Optional[str]


@dataclass
class AnchorDensityResult:
    """
    Complete anchor density analysis result
    完整的锚点密度分析结果
    """
    overall_density: float  # Anchors per 100 words across document
    total_anchors: int
    total_words: int
    paragraph_analyses: List[ParagraphAnchorAnalysis]
    high_risk_paragraphs: List[int]  # Indices of paragraphs with hallucination risk
    anchor_type_distribution: Dict[str, int]  # Count by anchor type
    document_hallucination_risk: str  # low, medium, high


class AnchorDensityAnalyzer:
    """
    Analyzer for academic anchor density
    学术锚点密度分析器

    Detects various types of academic anchors and calculates their density
    to identify potentially AI-generated "filler" content.
    检测各种类型的学术锚点并计算其密度，以识别可能的AI生成的"填充"内容。
    """

    # Minimum word count for hallucination risk analysis
    # 幻觉风险分析的最小词数
    MIN_WORDS_FOR_RISK = 50

    # Anchor density threshold (anchors per 100 words)
    # 锚点密度阈值（每100词的锚点数）
    LOW_DENSITY_THRESHOLD = 5.0  # Below this = hallucination risk
    MEDIUM_DENSITY_THRESHOLD = 10.0

    # Anchor detection patterns
    # 锚点检测模式
    ANCHOR_PATTERNS = [
        # Numbers with decimals (e.g., 14.2, 3.5, 0.05) - exclude years
        (r'(?<!\d)\d+\.\d+(?!\d{2})', AnchorType.DECIMAL_NUMBER, 1.0),

        # Percentages (e.g., 50%, 14.2%)
        (r'\d+(?:\.\d+)?%', AnchorType.PERCENTAGE, 1.2),

        # Statistical values (e.g., p < 0.05, r = 0.82, χ² = 4.5)
        (r'[pnrRtFχβα]\s*[<>=≤≥]\s*\d+(?:\.\d+)?', AnchorType.STATISTICAL_VALUE, 1.5),

        # Sample sizes (e.g., n=500, N = 1000)
        (r'[nN]\s*=\s*\d+', AnchorType.SAMPLE_SIZE, 1.3),

        # Citations with brackets (e.g., [1], [2,3], [1-5])
        (r'\[\d+(?:[,\-–]\s*\d+)*\]', AnchorType.CITATION_BRACKET, 1.5),

        # Citations with author (e.g., (Smith, 2020), (Jones et al., 2021))
        (r'\([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&\s+[A-Z][a-z]+))?,?\s*\d{4}[a-z]?\)', AnchorType.CITATION_AUTHOR, 1.5),

        # Units with numbers (e.g., 5mL, 20°C, 3.5kg, 100ms)
        (r'\d+(?:\.\d+)?\s*(?:mL|L|kg|g|mg|µg|ng|°C|°F|K|ms|s|min|h|Hz|kHz|MHz|GHz|nm|µm|mm|cm|m|km|mol|M|mM|µM|nM|pM|Da|kDa|bp|kb|Mb|Gb)', AnchorType.UNIT_MEASUREMENT, 1.3),

        # Chemical formulas (e.g., H2O, CO2, NaCl, C6H12O6)
        (r'\b[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)+\b', AnchorType.CHEMICAL_FORMULA, 1.2),

        # Specific counts with context (e.g., 500 samples, 3 groups)
        (r'\d+\s+(?:samples?|participants?|subjects?|groups?|trials?|experiments?|patients?|cases?|observations?|iterations?|epochs?|layers?|neurons?)', AnchorType.SPECIFIC_COUNT, 1.4),

        # Scientific notation (e.g., 1.5e-3, 2.0×10^6)
        (r'\d+(?:\.\d+)?[eE][+-]?\d+', AnchorType.SCIENTIFIC_NOTATION, 1.3),
        (r'\d+(?:\.\d+)?\s*[×x]\s*10[⁰¹²³⁴⁵⁶⁷⁸⁹\^]+\d+', AnchorType.SCIENTIFIC_NOTATION, 1.3),

        # Technical acronyms (e.g., ANOVA, CNN, LSTM, PCR)
        (r'\b[A-Z]{2,}(?:-\d+)?(?:/[A-Z]+)?\b', AnchorType.ACRONYM, 1.0),

        # Equation references (e.g., Eq. 1, Equation (2))
        (r'(?:Eq(?:uation)?\.?\s*\(?|Eqs?\.\s*\(?)\d+\)?', AnchorType.EQUATION_REF, 1.4),

        # Figure/Table references (e.g., Fig. 1, Table 2, Figure 3a)
        (r'(?:Fig(?:ure)?\.?|Table|Tab\.)\s*\d+[a-z]?', AnchorType.FIGURE_TABLE_REF, 1.4),

        # Year in isolation (likely a reference)
        (r'(?:19|20)\d{2}(?:\s*[–-]\s*(?:19|20)?\d{2})?', AnchorType.CITATION_AUTHOR, 0.5),
    ]

    def __init__(self):
        """Initialize analyzer with compiled patterns"""
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE if atype != AnchorType.ACRONYM else 0), atype, weight)
            for pattern, atype, weight in self.ANCHOR_PATTERNS
        ]

    def analyze_paragraph(self, text: str, paragraph_index: int = 0) -> ParagraphAnchorAnalysis:
        """
        Analyze anchor density in a single paragraph
        分析单个段落的锚点密度

        Args:
            text: Paragraph text
            paragraph_index: Index of paragraph in document

        Returns:
            ParagraphAnchorAnalysis result
        """
        words = text.split()
        word_count = len(words)

        # Detect all anchors
        # 检测所有锚点
        anchors = self._detect_anchors(text)
        anchor_count = len(anchors)

        # Calculate density (per 100 words)
        # 计算密度（每100词）
        if word_count > 0:
            anchor_density = (anchor_count / word_count) * 100
        else:
            anchor_density = 0.0

        # Determine hallucination risk
        # 确定幻觉风险
        has_risk = False
        risk_level = "low"
        risk_reason = None

        if word_count >= self.MIN_WORDS_FOR_RISK:
            if anchor_density < self.LOW_DENSITY_THRESHOLD:
                has_risk = True
                risk_level = "high"
                risk_reason = f"Low anchor density ({anchor_density:.1f}%) in long paragraph ({word_count} words) - possible AI filler"
            elif anchor_density < self.MEDIUM_DENSITY_THRESHOLD:
                risk_level = "medium"
                risk_reason = f"Below average anchor density ({anchor_density:.1f}%) - may need more specific evidence"

        return ParagraphAnchorAnalysis(
            paragraph_index=paragraph_index,
            text=text[:200] + "..." if len(text) > 200 else text,
            word_count=word_count,
            anchor_count=anchor_count,
            anchor_density=anchor_density,
            anchors=anchors,
            has_hallucination_risk=has_risk,
            risk_level=risk_level,
            risk_reason=risk_reason
        )

    def analyze_document(self, paragraphs: List[str]) -> AnchorDensityResult:
        """
        Analyze anchor density across entire document
        分析整个文档的锚点密度

        Args:
            paragraphs: List of paragraph texts

        Returns:
            AnchorDensityResult with complete analysis
        """
        paragraph_analyses = []
        all_anchors = []
        total_words = 0
        high_risk_indices = []
        anchor_type_counts: Dict[str, int] = {}

        for i, para in enumerate(paragraphs):
            analysis = self.analyze_paragraph(para, i)
            paragraph_analyses.append(analysis)

            total_words += analysis.word_count
            all_anchors.extend(analysis.anchors)

            if analysis.has_hallucination_risk:
                high_risk_indices.append(i)

            # Count anchor types
            # 统计锚点类型
            for anchor in analysis.anchors:
                type_name = anchor.anchor_type.value
                anchor_type_counts[type_name] = anchor_type_counts.get(type_name, 0) + 1

        # Calculate overall density
        # 计算整体密度
        total_anchors = len(all_anchors)
        if total_words > 0:
            overall_density = (total_anchors / total_words) * 100
        else:
            overall_density = 0.0

        # Determine document-level risk
        # 确定文档级风险
        high_risk_ratio = len(high_risk_indices) / max(1, len(paragraphs))
        if high_risk_ratio > 0.3:
            doc_risk = "high"
        elif high_risk_ratio > 0.1 or overall_density < self.MEDIUM_DENSITY_THRESHOLD:
            doc_risk = "medium"
        else:
            doc_risk = "low"

        return AnchorDensityResult(
            overall_density=overall_density,
            total_anchors=total_anchors,
            total_words=total_words,
            paragraph_analyses=paragraph_analyses,
            high_risk_paragraphs=high_risk_indices,
            anchor_type_distribution=anchor_type_counts,
            document_hallucination_risk=doc_risk
        )

    def _detect_anchors(self, text: str) -> List[AnchorMatch]:
        """
        Detect all academic anchors in text
        检测文本中的所有学术锚点
        """
        matches = []
        covered_positions: Set[int] = set()

        for pattern, atype, weight in self.compiled_patterns:
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()

                # Skip if position already covered by another anchor
                # 如果位置已被其他锚点覆盖则跳过
                if any(pos in covered_positions for pos in range(start, end)):
                    continue

                # Skip common false positives
                # 跳过常见的误报
                matched_text = match.group(0)
                if self._is_false_positive(matched_text, atype, text, start):
                    continue

                matches.append(AnchorMatch(
                    anchor_type=atype,
                    matched_text=matched_text,
                    position=start,
                    end_position=end,
                    weight=weight
                ))

                # Mark positions as covered
                # 标记位置为已覆盖
                covered_positions.update(range(start, end))

        # Sort by position
        # 按位置排序
        matches.sort(key=lambda m: m.position)
        return matches

    def _is_false_positive(
        self,
        matched_text: str,
        anchor_type: AnchorType,
        full_text: str,
        position: int
    ) -> bool:
        """
        Check if match is a false positive
        检查匹配是否为误报
        """
        text_lower = matched_text.lower()

        # Filter out common non-anchor acronyms
        # 过滤掉常见的非锚点缩写
        if anchor_type == AnchorType.ACRONYM:
            # Skip common words that happen to be uppercase
            # 跳过碰巧是大写的常见词
            non_anchors = {
                "THE", "AND", "FOR", "NOT", "BUT", "ARE", "WAS", "HAS",
                "HAD", "HAVE", "THIS", "THAT", "WITH", "FROM", "THEY",
                "BEEN", "WERE", "WILL", "WHEN", "WHAT", "INTO", "ALSO",
                "SUCH", "THEIR", "ABOUT", "WOULD", "COULD", "SHOULD",
                "OTHER", "SOME", "THESE", "THOSE", "THAN", "THEN",
                "ONLY", "JUST", "OVER", "UNDER", "AFTER", "BEFORE",
                # Common abbreviations that aren't technical
                "USA", "UK", "EU", "US", "UN", "OK",
            }
            if matched_text in non_anchors:
                return True

            # Skip single letters followed by lowercase
            # 跳过后面跟小写字母的单个大写字母
            if len(matched_text) == 2 and position + 2 < len(full_text):
                next_char = full_text[position + 2:position + 3]
                if next_char.islower():
                    return True

        # Filter chemical formulas that are actually words
        # 过滤实际上是单词的化学式
        if anchor_type == AnchorType.CHEMICAL_FORMULA:
            # Skip if it's a capitalized word at sentence start
            # 跳过句首大写单词
            if position == 0 or full_text[position - 1] in '.!?':
                if not any(c.isdigit() for c in matched_text):
                    return True

            # Skip common words that match chemical formula pattern
            # 跳过匹配化学式模式的常见词
            false_chemical = {"PhD", "MSc", "BSc", "Mr", "Mrs", "Dr", "PhD"}
            if matched_text in false_chemical:
                return True

        return False

    def get_anchor_summary(self, result: AnchorDensityResult) -> Dict[str, any]:
        """
        Get a summary of anchor analysis for API response
        获取用于API响应的锚点分析摘要
        """
        return {
            "overall_density": round(result.overall_density, 2),
            "total_anchors": result.total_anchors,
            "total_words": result.total_words,
            "document_risk": result.document_hallucination_risk,
            "high_risk_paragraph_count": len(result.high_risk_paragraphs),
            "high_risk_paragraph_indices": result.high_risk_paragraphs,
            "anchor_type_distribution": result.anchor_type_distribution,
            "paragraphs_with_risk": [
                {
                    "index": p.paragraph_index,
                    "density": round(p.anchor_density, 2),
                    "reason": p.risk_reason
                }
                for p in result.paragraph_analyses if p.has_hallucination_risk
            ]
        }


# Convenience functions
# 便捷函数
def analyze_paragraph_anchors(text: str) -> ParagraphAnchorAnalysis:
    """
    Analyze anchor density in a paragraph
    分析段落的锚点密度
    """
    analyzer = AnchorDensityAnalyzer()
    return analyzer.analyze_paragraph(text)


def analyze_document_anchors(paragraphs: List[str]) -> AnchorDensityResult:
    """
    Analyze anchor density across document
    分析整个文档的锚点密度
    """
    analyzer = AnchorDensityAnalyzer()
    return analyzer.analyze_document(paragraphs)


def has_hallucination_risk(text: str, min_words: int = 50) -> Tuple[bool, Optional[str]]:
    """
    Quick check if paragraph has hallucination risk
    快速检查段落是否有幻觉风险

    Args:
        text: Paragraph text
        min_words: Minimum word count to trigger check

    Returns:
        Tuple of (has_risk, reason)
    """
    words = text.split()
    if len(words) < min_words:
        return (False, None)

    analyzer = AnchorDensityAnalyzer()
    result = analyzer.analyze_paragraph(text)
    return (result.has_hallucination_risk, result.risk_reason)
