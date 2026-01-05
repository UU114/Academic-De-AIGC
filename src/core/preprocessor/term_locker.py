"""
Term locking module - identifies and protects academic terms
术语锁定模块 - 识别并保护学术术语
"""

import re
import json
from dataclasses import dataclass
from typing import List, Set, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class LockedTerm:
    """
    Represents a locked (protected) term
    表示被锁定（保护）的术语
    """
    term: str
    start_pos: int
    end_pos: int
    source: str  # whitelist, ner, pattern
    domain: Optional[str] = None


class TermLocker:
    """
    Term identification and locking engine
    术语识别和锁定引擎

    Identifies terms that should not be modified:
    - Technical terms from whitelist
    - Named entities (via NER)
    - Statistical terms (e.g., p < 0.05, R² = 0.89)
    - Mathematical expressions
    - Citations and references
    """

    # Common statistical patterns
    # 常见统计模式
    STAT_PATTERNS = [
        r'p\s*[<>=≤≥]\s*0?\.\d+',  # p-values: p < 0.05
        r'[rRρ]²?\s*=\s*0?\.\d+',  # Correlation: r = 0.85, R² = 0.72
        r'[Ff]\s*\(\d+,\s*\d+\)\s*=\s*\d+\.?\d*',  # F-statistic
        r'[tT]\s*\(\d+\)\s*=\s*-?\d+\.?\d*',  # t-statistic
        r'χ²?\s*\(\d+\)\s*=\s*\d+\.?\d*',  # Chi-square
        r'\d+%\s*CI',  # Confidence interval
        r'[Nn]\s*=\s*\d+',  # Sample size
        r'[Mm]ean\s*=\s*\d+\.?\d*',  # Mean
        r'SD\s*=\s*\d+\.?\d*',  # Standard deviation
        r'SE\s*=\s*\d+\.?\d*',  # Standard error
        r'α\s*=\s*0?\.\d+',  # Alpha level
        r'β\s*=\s*-?\d+\.?\d*',  # Beta coefficient
    ]

    # Mathematical/scientific notation
    # 数学/科学符号
    MATH_PATTERNS = [
        r'\d+\s*[×x]\s*10\^?-?\d+',  # Scientific notation
        r'[A-Z][a-z]?\d*[⁺⁻±]?',  # Chemical formulas (simple)
        r'\d+\s*(?:nm|μm|mm|cm|m|km|mg|g|kg|mL|L|°C|K|Hz|kHz|MHz)',  # Units
    ]

    # Quotation patterns
    # 引用内容模式
    QUOTATION_PATTERNS = [
        r'"[^"]+?"',           # Straight double quotes
        r'"[^"]+?"',           # Curly double quotes (standard regex usually handles unicode chars if passed correctly, but let's be explicit if needed)
        r'[\u201C][^\u201D]+?[\u201D]', # Curly double quotes (Unicode)
        r"'[^']+?'",           # Straight single quotes (non-apostrophe)
        r'[\u2018][^\u2019]+?[\u2019]', # Curly single quotes (Unicode)
        r'「[^」]+?」',        # Chinese brackets
        r'『[^』]+?』',        # Chinese double brackets
    ]

    def __init__(self, whitelist_path: Optional[str] = None):
        """
        Initialize term locker
        初始化术语锁定器

        Args:
            whitelist_path: Path to custom whitelist JSON file
        """
        self.whitelist: Set[str] = set()
        self.domain_terms: dict = {}  # domain -> set of terms

        # Load default whitelist
        # 加载默认白名单
        self._load_default_whitelist()

        # Load custom whitelist if provided
        # 如果提供了自定义白名单则加载
        if whitelist_path:
            self._load_whitelist(whitelist_path)

        # Compile patterns
        # 编译模式
        self._compile_patterns()

    def _load_default_whitelist(self):
        """
        Load default academic term whitelist
        加载默认学术术语白名单
        """
        # Common statistical/methodological terms
        # 常见统计/方法学术语
        default_terms = {
            # Statistics
            "ANOVA", "MANOVA", "ANCOVA", "t-test", "chi-square",
            "regression", "correlation", "p-value", "confidence interval",
            "standard deviation", "standard error", "effect size",
            "Cohen's d", "Cronbach's alpha", "factor analysis",
            "principal component analysis", "PCA", "ICA",
            "maximum likelihood", "Bayesian", "Monte Carlo",

            # Machine Learning
            "neural network", "deep learning", "machine learning",
            "convolutional neural network", "CNN", "RNN", "LSTM", "GRU",
            "transformer", "attention mechanism", "backpropagation",
            "gradient descent", "stochastic gradient descent", "SGD",
            "Adam", "RMSprop", "dropout", "batch normalization",
            "cross-entropy", "softmax", "sigmoid", "ReLU", "tanh",
            "overfitting", "underfitting", "regularization", "L1", "L2",
            "hyperparameter", "epoch", "batch size", "learning rate",
            "precision", "recall", "F1 score", "accuracy", "AUC", "ROC",
            "confusion matrix", "cross-validation", "k-fold",

            # Research methodology
            "hypothesis", "null hypothesis", "alternative hypothesis",
            "independent variable", "dependent variable", "control variable",
            "randomized controlled trial", "RCT", "double-blind",
            "placebo", "longitudinal study", "cross-sectional",
            "qualitative", "quantitative", "mixed methods",
            "validity", "reliability", "generalizability",

            # Common abbreviations
            "et al.", "i.e.", "e.g.", "cf.", "viz.", "vs.",
        }

        self.whitelist.update(term.lower() for term in default_terms)

    def _load_whitelist(self, path: str):
        """
        Load whitelist from JSON file
        从JSON文件加载白名单
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                self.whitelist.update(term.lower() for term in data)
            elif isinstance(data, dict):
                for domain, terms in data.items():
                    self.domain_terms[domain] = set(term.lower() for term in terms)
                    self.whitelist.update(self.domain_terms[domain])

            logger.info(f"Loaded {len(self.whitelist)} terms from whitelist")
        except Exception as e:
            logger.warning(f"Failed to load whitelist from {path}: {e}")

    def _compile_patterns(self):
        """
        Compile regex patterns
        编译正则表达式
        """
        # Combine all patterns
        # 合并所有模式
        all_patterns = self.STAT_PATTERNS + self.MATH_PATTERNS
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in all_patterns]

        # Citation patterns
        # 引用模式
        self.citation_pattern = re.compile(
            r'\[[^\]]+\]|'  # [1], [1,2], [Smith 2020]
            r'\([A-Z][a-z]+(?:\s+(?:et\s+al\.|&|and)\s+[A-Z][a-z]+)*,?\s*\d{4}[a-z]?\)'
        )

    def identify_terms(self, text: str) -> List[LockedTerm]:
        """
        Identify all terms that should be locked in the text
        识别文本中所有应该被锁定的术语

        Args:
            text: Input text to analyze

        Returns:
            List of LockedTerm objects
        """
        locked_terms = []

        # Find whitelist terms
        # 查找白名单术语
        locked_terms.extend(self._find_whitelist_terms(text))

        # Find statistical/mathematical patterns
        # 查找统计/数学模式
        locked_terms.extend(self._find_pattern_terms(text))

        # Find citations
        # 查找引用
        locked_terms.extend(self._find_citations(text))

        # Find quotations
        # 查找引用内容
        locked_terms.extend(self._find_quotations(text))

        # Remove duplicates and sort by position
        # 去重并按位置排序
        locked_terms = self._deduplicate_terms(locked_terms)

        return locked_terms

    def _find_whitelist_terms(self, text: str) -> List[LockedTerm]:
        """
        Find terms from whitelist in text
        在文本中查找白名单术语
        """
        terms = []
        text_lower = text.lower()

        for term in self.whitelist:
            # Use word boundary matching
            # 使用词边界匹配
            pattern = r'\b' + re.escape(term) + r'\b'
            for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                # Get original case from text
                # 从文本获取原始大小写
                original_term = text[match.start():match.end()]

                # Find domain if available
                # 如果可用则查找领域
                domain = None
                for d, d_terms in self.domain_terms.items():
                    if term in d_terms:
                        domain = d
                        break

                terms.append(LockedTerm(
                    term=original_term,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    source="whitelist",
                    domain=domain
                ))

        return terms

    def _find_pattern_terms(self, text: str) -> List[LockedTerm]:
        """
        Find statistical/mathematical patterns in text
        在文本中查找统计/数学模式
        """
        terms = []

        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                terms.append(LockedTerm(
                    term=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    source="pattern"
                ))

        return terms

    def _find_citations(self, text: str) -> List[LockedTerm]:
        """
        Find citations in text
        在文本中查找引用
        """
        terms = []

        for match in self.citation_pattern.finditer(text):
            terms.append(LockedTerm(
                term=match.group(0),
                start_pos=match.start(),
                end_pos=match.end(),
                source="citation"
            ))

        return terms

    def _find_quotations(self, text: str) -> List[LockedTerm]:
        """
        Find quoted text
        查找引用内容
        """
        terms = []
        
        for pattern_str in self.QUOTATION_PATTERNS:
            try:
                pattern = re.compile(pattern_str)
                for match in pattern.finditer(text):
                    terms.append(LockedTerm(
                        term=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        source="quotation"
                    ))
            except re.error:
                continue

        return terms

    def _deduplicate_terms(self, terms: List[LockedTerm]) -> List[LockedTerm]:
        """
        Remove duplicate and overlapping terms
        移除重复和重叠的术语
        """
        if not terms:
            return []

        # Sort by start position, then by length (longer first)
        # 按起始位置排序，然后按长度排序（较长的优先）
        terms.sort(key=lambda t: (t.start_pos, -(t.end_pos - t.start_pos)))

        result = []
        last_end = -1

        for term in terms:
            # Skip if overlapping with previous term
            # 如果与前一个术语重叠则跳过
            if term.start_pos < last_end:
                continue

            result.append(term)
            last_end = term.end_pos

        return result

    def mark_locked(self, text: str, terms: List[LockedTerm]) -> str:
        """
        Mark locked terms in text with special tokens
        用特殊标记标注文本中的锁定术语

        Args:
            text: Original text
            terms: List of terms to lock

        Returns:
            Text with locked terms marked as <LOCK>term</LOCK>
        """
        if not terms:
            return text

        # Sort by position in reverse order
        # 按位置倒序排序
        terms_sorted = sorted(terms, key=lambda t: t.start_pos, reverse=True)

        result = text
        for term in terms_sorted:
            before = result[:term.start_pos]
            locked = f"<LOCK>{term.term}</LOCK>"
            after = result[term.end_pos:]
            result = before + locked + after

        return result

    def restore_locked(self, text: str) -> str:
        """
        Remove lock markers from text
        从文本中移除锁定标记

        Args:
            text: Text with <LOCK> markers

        Returns:
            Text with markers removed
        """
        return re.sub(r'</?LOCK>', '', text)

    def add_term(self, term: str, domain: Optional[str] = None):
        """
        Add a term to the whitelist
        将术语添加到白名单

        Args:
            term: Term to add
            domain: Optional domain category
        """
        self.whitelist.add(term.lower())
        if domain:
            if domain not in self.domain_terms:
                self.domain_terms[domain] = set()
            self.domain_terms[domain].add(term.lower())

    def remove_term(self, term: str):
        """
        Remove a term from the whitelist
        从白名单中移除术语
        """
        self.whitelist.discard(term.lower())
        for domain_terms in self.domain_terms.values():
            domain_terms.discard(term.lower())


# Convenience function
# 便捷函数
def identify_locked_terms(text: str) -> List[LockedTerm]:
    """
    Convenience function to identify locked terms
    识别锁定术语的便捷函数
    """
    locker = TermLocker()
    return locker.identify_terms(text)
