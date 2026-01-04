"""
Whitelist extraction module - extracts domain-specific terms to exempt from scoring
白名单提取模块 - 提取学科特定术语以免于评分

CAASS v2.0 Phase 2: Smart whitelist extraction from Abstract
"""

import re
import logging
from typing import Set, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WhitelistResult:
    """
    Result of whitelist extraction
    白名单提取结果
    """
    terms: Set[str]
    source: str  # abstract, user, combined
    confidence: float


class WhitelistExtractor:
    """
    Extract domain-specific terms to whitelist
    提取需要白名单的学科特定术语

    These terms are legitimate academic vocabulary that should not
    be penalized as AI fingerprints.
    这些是合法的学术词汇，不应被惩罚为AI指纹。
    """

    # Common domain-specific term patterns
    # 常见学科特定术语模式
    DOMAIN_PATTERNS = [
        # Scientific/technical compound terms
        # 科学/技术复合术语
        r'\b[A-Z][a-z]+(?:-[a-z]+)+\b',  # e.g., soil-plant, multi-scale
        r'\b[a-z]+-[a-z]+(?:-[a-z]+)*\b',  # e.g., life-cycle, trade-offs

        # Acronyms defined in text
        # 文中定义的缩写
        r'\b[A-Z]{2,6}\b',  # e.g., AIGC, PPL, SEM

        # Greek letters in science
        # 科学中的希腊字母
        r'\b(?:alpha|beta|gamma|delta|theta|sigma|omega)\b',
    ]

    # Domain-specific suffixes that indicate technical terms
    # 表示技术术语的学科特定后缀
    TECHNICAL_SUFFIXES = [
        'ization', 'ification', 'ation', 'ology', 'ometry',
        'osis', 'itis', 'ase', 'ide', 'ate', 'ene', 'ane',
        'metric', 'thermal', 'dynamic', 'static', 'genic',
    ]

    # Known domain-specific terms that are often false positives
    # 已知的经常被误判的学科特定术语
    KNOWN_DOMAIN_TERMS = {
        # Environmental science
        # 环境科学
        'remediation', 'bioremediation', 'phytoremediation',
        'salinization', 'desalinization', 'eutrophication',
        'bioaccumulation', 'biomagnification',

        # Circular economy / sustainability
        # 循环经济/可持续性
        'circular economy', 'life-cycle', 'life cycle',
        'valorization', 'upcycling', 'downcycling',

        # Chemistry / materials
        # 化学/材料
        'interfacial', 'nanoparticle', 'microstructure',
        'crystallization', 'polymerization',

        # Biology
        # 生物学
        'biodiversity', 'ecosystem', 'symbiosis',
        'photosynthesis', 'metabolism',

        # Statistics / methodology
        # 统计/方法论
        'heterogeneity', 'homogeneity', 'multicollinearity',
        'autocorrelation', 'stationarity',
    }

    def __init__(self):
        """Initialize whitelist extractor"""
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns"""
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.DOMAIN_PATTERNS
        ]

    def extract_from_abstract(self, abstract_text: str) -> WhitelistResult:
        """
        Extract domain-specific terms from the Abstract section
        从摘要部分提取学科特定术语

        Args:
            abstract_text: The Abstract text

        Returns:
            WhitelistResult with extracted terms
        """
        terms = set()

        if not abstract_text or len(abstract_text) < 50:
            return WhitelistResult(terms=terms, source="abstract", confidence=0.0)

        abstract_lower = abstract_text.lower()

        # 1. Extract technical compound terms
        # 1. 提取技术复合术语
        for pattern in self.compiled_patterns:
            matches = pattern.findall(abstract_text)
            for match in matches:
                if len(match) >= 3:  # Skip very short matches
                    terms.add(match.lower())

        # 2. Find terms with technical suffixes
        # 2. 查找带有技术后缀的术语
        words = re.findall(r'\b[a-z]{6,}\b', abstract_lower)
        for word in words:
            for suffix in self.TECHNICAL_SUFFIXES:
                if word.endswith(suffix) and len(word) > len(suffix) + 3:
                    terms.add(word)

        # 3. Add known domain terms if they appear in abstract
        # 3. 如果已知学科术语出现在摘要中，添加它们
        for term in self.KNOWN_DOMAIN_TERMS:
            if term in abstract_lower:
                terms.add(term)

        # 4. Extract defined acronyms: "X (ABC)" pattern
        # 4. 提取定义的缩写："X (ABC)" 模式
        acronym_pattern = re.compile(r'([A-Za-z\s]+)\s*\(([A-Z]{2,6})\)')
        for match in acronym_pattern.finditer(abstract_text):
            full_term = match.group(1).strip().lower()
            acronym = match.group(2)
            if len(full_term) >= 10:  # Substantial term
                terms.add(full_term)
                terms.add(acronym.lower())

        # Calculate confidence based on number of terms found
        # 根据找到的术语数量计算置信度
        confidence = min(1.0, len(terms) / 20)  # Max confidence at 20 terms

        return WhitelistResult(
            terms=terms,
            source="abstract",
            confidence=confidence
        )

    def extract_from_document(
        self,
        full_text: str,
        abstract_text: Optional[str] = None
    ) -> WhitelistResult:
        """
        Extract whitelist from full document, prioritizing Abstract
        从完整文档提取白名单，优先使用摘要

        Args:
            full_text: Full document text
            abstract_text: Pre-extracted Abstract text (optional)

        Returns:
            WhitelistResult with extracted terms
        """
        terms = set()
        
        if not full_text:
            return WhitelistResult(
                terms=terms,
                source="document",
                confidence=0.0
            )

        # Try to find Abstract section if not provided
        # 如果未提供，尝试查找摘要部分
        if not abstract_text:
            abstract_text = self._extract_abstract_section(full_text)

        # Extract from Abstract
        # 从摘要提取
        if abstract_text:
            abstract_result = self.extract_from_abstract(abstract_text)
            terms.update(abstract_result.terms)

        # Also scan Introduction for key terms (first 2000 chars after Abstract)
        # 也扫描引言中的关键术语（摘要后前2000字符）
        intro_start = full_text.lower().find('introduction')
        if intro_start != -1:
            intro_text = full_text[intro_start:intro_start + 2000]
            intro_result = self.extract_from_abstract(intro_text)
            # Only add high-confidence terms from intro
            # 只添加引言中高置信度的术语
            for term in intro_result.terms:
                if term in self.KNOWN_DOMAIN_TERMS or len(term) > 10:
                    terms.add(term)

        confidence = min(1.0, len(terms) / 30)

        return WhitelistResult(
            terms=terms,
            source="document",
            confidence=confidence
        )

    def _extract_abstract_section(self, text: str) -> Optional[str]:
        """
        Extract Abstract section from document text
        从文档文本中提取摘要部分
        """
        if not text:
            return None

        text_lower = text.lower()

        # Find "abstract" keyword
        # 查找 "abstract" 关键词
        abstract_start = text_lower.find('abstract')
        if abstract_start == -1:
            return None

        # Find end of Abstract (next section header)
        # 查找摘要结束位置（下一个章节标题）
        section_headers = [
            'introduction', 'keywords', 'key words',
            '1.', '1 ', 'background'
        ]

        abstract_end = len(text)
        for header in section_headers:
            pos = text_lower.find(header, abstract_start + 10)
            if pos != -1 and pos < abstract_end:
                abstract_end = pos

        # Extract Abstract text (skip the "Abstract" header itself)
        # 提取摘要文本（跳过 "Abstract" 标题本身）
        abstract_text = text[abstract_start + 8:abstract_end].strip()

        # Limit to reasonable length
        # 限制合理长度
        if len(abstract_text) > 3000:
            abstract_text = abstract_text[:3000]

        return abstract_text if len(abstract_text) >= 100 else None

    def merge_with_user_whitelist(
        self,
        extracted: WhitelistResult,
        user_terms: List[str]
    ) -> WhitelistResult:
        """
        Merge extracted whitelist with user-provided terms
        将提取的白名单与用户提供的术语合并

        Args:
            extracted: Auto-extracted whitelist
            user_terms: User-provided terms to whitelist

        Returns:
            Combined WhitelistResult
        """
        combined_terms = extracted.terms.copy()

        for term in user_terms:
            combined_terms.add(term.lower().strip())

        return WhitelistResult(
            terms=combined_terms,
            source="combined",
            confidence=max(extracted.confidence, 0.8 if user_terms else 0.0)
        )


# Convenience function
# 便捷函数
def extract_whitelist(text: str) -> Set[str]:
    """
    Convenience function to extract whitelist from text
    从文本提取白名单的便捷函数
    """
    extractor = WhitelistExtractor()
    result = extractor.extract_from_document(text)
    return result.terms
