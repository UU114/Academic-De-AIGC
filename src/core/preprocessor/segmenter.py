"""
Text segmentation module - splits text into sentences
文本分句模块 - 将文本分割为句子
"""

import re
from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class ContentType:
    """
    Content type enumeration for filtering
    内容类型枚举，用于过滤
    """
    SENTENCE = "sentence"           # Normal sentence to process 正常句子，需处理
    TITLE = "title"                 # Document title 文档标题
    SECTION_HEADER = "section"      # Section header (Abstract, Introduction, etc.) 章节标题
    TABLE_HEADER = "table_header"   # Table header/caption 表格标题
    FIGURE_CAPTION = "figure"       # Figure caption 图片说明
    REFERENCE = "reference"         # Reference entry 参考文献条目
    METADATA = "metadata"           # Author info, affiliation, etc. 作者信息等元数据
    SHORT_FRAGMENT = "fragment"     # Too short to be meaningful 过短的片段


@dataclass
class Sentence:
    """
    Represents a single sentence with position information
    表示单个句子及其位置信息
    """
    text: str
    start_pos: int
    end_pos: int
    index: int
    paragraph_index: Optional[int] = None
    content_type: str = ContentType.SENTENCE  # Content type for filtering 内容类型用于过滤
    should_process: bool = True               # Whether this should be processed 是否应该处理


class SentenceSegmenter:
    """
    Sentence segmentation engine
    句子分割引擎

    Handles academic text with special cases like:
    - Abbreviations (e.g., Dr., et al., Fig.)
    - Citations (e.g., [1], (Smith, 2020))
    - Decimal numbers (e.g., 3.14)
    - URLs and emails
    - Content type detection (titles, headers, references)
    """

    # Common abbreviations that should not end sentences
    # 不应该结束句子的常见缩写
    ABBREVIATIONS = {
        "dr", "mr", "mrs", "ms", "prof", "sr", "jr",
        "vs", "etc", "al", "fig", "eq", "no", "vol",
        "pp", "ed", "eds", "trans", "rev", "approx",
        "dept", "univ", "assoc", "corp", "inc", "ltd",
        "jan", "feb", "mar", "apr", "jun", "jul", "aug",
        "sep", "oct", "nov", "dec", "st", "nd", "rd", "th",
        "i.e", "e.g", "cf", "viz"
    }

    # Sentence ending punctuation
    # 句子结束标点
    SENTENCE_ENDINGS = ".!?"

    # Section header keywords (case-insensitive)
    # 章节标题关键词（不区分大小写）
    SECTION_HEADERS = {
        "abstract", "introduction", "background", "literature review",
        "related work", "methodology", "methods", "method", "materials and methods",
        "results", "findings", "discussion", "analysis", "conclusion", "conclusions",
        "summary", "references", "bibliography", "appendix", "appendices",
        "acknowledgments", "acknowledgements", "funding", "declaration",
        "conflict of interest", "data availability", "author contributions",
        "supplementary", "supplementary materials", "supporting information"
    }

    # Table/Figure prefixes
    # 表格/图片前缀
    TABLE_PREFIXES = {"table", "tab.", "tab"}
    FIGURE_PREFIXES = {"figure", "fig.", "fig", "image", "diagram", "chart", "graph"}

    def __init__(self, lang: str = "en"):
        """
        Initialize segmenter
        初始化分句器

        Args:
            lang: Language code (currently only 'en' supported)
        """
        self.lang = lang
        self._compile_patterns()

    def _compile_patterns(self):
        """
        Compile regex patterns for efficiency
        编译正则表达式以提高效率
        """
        # Pattern for citations like [1], [1,2], [1-3]
        # 引用模式，如 [1], [1,2], [1-3]
        self.citation_pattern = re.compile(r'\[\d+(?:[,\-]\d+)*\]')

        # Pattern for author citations like (Smith, 2020)
        # 作者引用模式，如 (Smith, 2020)
        self.author_citation_pattern = re.compile(
            r'\([A-Z][a-z]+(?:\s+(?:et\s+al\.|&|and)\s+[A-Z][a-z]+)*,?\s*\d{4}[a-z]?\)'
        )

        # Pattern for decimal numbers
        # 小数模式
        self.decimal_pattern = re.compile(r'\d+\.\d+')

        # Pattern for URLs
        # URL模式
        self.url_pattern = re.compile(
            r'https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        )

        # Pattern for abbreviations
        # 缩写模式
        abbr_pattern = '|'.join(re.escape(abbr) for abbr in self.ABBREVIATIONS)
        self.abbr_pattern = re.compile(
            rf'\b({abbr_pattern})\.(?!\s+[A-Z])',
            re.IGNORECASE
        )

        # === Content type detection patterns 内容类型检测模式 ===

        # Numbered section headers: 1. Introduction, 1.1 Background, etc.
        # 编号的章节标题
        self.numbered_section_pattern = re.compile(
            r'^[\s]*(\d+\.?)+\s*[A-Z][A-Za-z\s]+$'
        )

        # Reference entry patterns (various citation styles)
        # 参考文献条目模式（各种引用格式）
        self.reference_patterns = [
            # [1] Author, Title...
            re.compile(r'^\s*\[\d+\]\s*[A-Z]'),
            # Author, A. B. (2020). Title...
            re.compile(r'^[A-Z][a-z]+,\s*[A-Z]\..*\(\d{4}\)'),
            # Author (2020) Title...
            re.compile(r'^[A-Z][a-z]+(?:\s+(?:et\s+al\.?|and|&)\s*)?.*\(\d{4}[a-z]?\)'),
            # DOI pattern
            re.compile(r'doi:\s*10\.\d{4,}', re.IGNORECASE),
            # URL in reference
            re.compile(r'(?:Retrieved|Available|Accessed)\s+(?:from|at)', re.IGNORECASE),
            # ISBN/ISSN
            re.compile(r'ISBN|ISSN', re.IGNORECASE),
            # Journal volume/issue pattern
            re.compile(r',\s*\d+\s*\(\d+\)\s*,\s*\d+[-–]\d+'),
            # pp. pages pattern
            re.compile(r'pp?\.\s*\d+[-–]\d+'),
        ]

        # Table/Figure caption pattern
        # 表格/图片说明模式
        self.table_pattern = re.compile(
            r'^(?:Table|Tab\.?)\s*\d+[.:]?\s*',
            re.IGNORECASE
        )
        self.figure_pattern = re.compile(
            r'^(?:Figure|Fig\.?|Image|Diagram|Chart|Graph)\s*\d+[.:]?\s*',
            re.IGNORECASE
        )

        # Metadata patterns (author info, affiliation, etc.)
        # 元数据模式（作者信息、单位等）
        self.metadata_patterns = [
            # Email pattern as main content
            re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            # ORCID
            re.compile(r'ORCID:', re.IGNORECASE),
            # Affiliation with superscript numbers
            re.compile(r'^\d+\s*[A-Z][a-z]+\s+(?:University|Institute|College|Department)', re.IGNORECASE),
            # Corresponding author
            re.compile(r'^\*?\s*Corresponding\s+author', re.IGNORECASE),
            # Keywords line
            re.compile(r'^Keywords?\s*:', re.IGNORECASE),
        ]

    def segment(self, text: str) -> List[Sentence]:
        """
        Segment text into sentences
        将文本分割为句子

        Args:
            text: Input text to segment

        Returns:
            List of Sentence objects
        """
        if not text or not text.strip():
            return []

        # Normalize whitespace
        # 规范化空白字符
        text = self._normalize_whitespace(text)

        # Protect special patterns from splitting
        # 保护特殊模式不被分割
        protected_text, placeholders = self._protect_patterns(text)

        # Split into sentences
        # 分割为句子
        raw_sentences = self._split_sentences(protected_text)

        # Restore protected patterns and build Sentence objects
        # 恢复受保护的模式并构建Sentence对象
        sentences = []
        current_pos = 0

        for idx, raw in enumerate(raw_sentences):
            # Restore placeholders
            # 恢复占位符
            restored = self._restore_placeholders(raw, placeholders)
            restored = restored.strip()

            if not restored:
                continue

            # Find position in original text
            # 在原文中查找位置
            start_pos = text.find(restored, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(restored)
            current_pos = end_pos

            sentences.append(Sentence(
                text=restored,
                start_pos=start_pos,
                end_pos=end_pos,
                index=len(sentences)
            ))

        # Merge fragments
        # 合并片段
        sentences = self._merge_fragments(sentences)

        # Detect content types and mark which sentences should be processed
        # 检测内容类型并标记哪些句子应该被处理
        sentences = self._detect_content_types(sentences)

        return sentences

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text
        规范化文本中的空白字符
        """
        # Replace multiple spaces with single space
        # 将多个空格替换为单个空格
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with double newline
        # 将多个换行替换为双换行
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()

    def _protect_patterns(self, text: str) -> tuple:
        """
        Replace patterns that shouldn't be split with placeholders
        将不应该被分割的模式替换为占位符
        """
        placeholders = {}
        counter = 0

        def make_placeholder(match, prefix):
            nonlocal counter
            placeholder = f"__PROTECTED_{prefix}_{counter}__"
            placeholders[placeholder] = match.group(0)
            counter += 1
            return placeholder

        # Protect URLs and emails
        # 保护URL和电子邮件
        text = self.url_pattern.sub(
            lambda m: make_placeholder(m, "URL"), text
        )

        # Protect decimal numbers
        # 保护小数
        text = self.decimal_pattern.sub(
            lambda m: make_placeholder(m, "NUM"), text
        )

        # Protect citations
        # 保护引用
        text = self.citation_pattern.sub(
            lambda m: make_placeholder(m, "CIT"), text
        )

        # Protect author citations
        # 保护作者引用
        text = self.author_citation_pattern.sub(
            lambda m: make_placeholder(m, "AUTH"), text
        )

        # Protect abbreviations
        # 保护缩写
        text = self.abbr_pattern.sub(
            lambda m: make_placeholder(m, "ABBR"), text
        )

        return text, placeholders

    def _restore_placeholders(self, text: str, placeholders: dict) -> str:
        """
        Restore placeholders to original text
        将占位符恢复为原始文本
        """
        for placeholder, original in placeholders.items():
            text = text.replace(placeholder, original)
        return text

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text at sentence boundaries
        在句子边界处分割文本
        """
        # First split on any newlines (single or double) to preserve line structure
        # 首先在任何换行处分割以保留行结构
        lines = re.split(r'\r?\n', text)

        result = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Split on sentence-ending punctuation followed by space and capital letter
            # 在句子结束标点后跟空格和大写字母处分割
            pattern = r'(?<=[.!?])\s+(?=[A-Z])'
            sentences = re.split(pattern, line)
            result.extend([s.strip() for s in sentences if s.strip()])

        return result

    def _merge_fragments(self, sentences: List[Sentence]) -> List[Sentence]:
        """
        Merge sentence fragments that were incorrectly split
        合并被错误分割的句子片段
        """
        if len(sentences) <= 1:
            return sentences

        merged = []
        i = 0

        while i < len(sentences):
            current = sentences[i]

            # Check if this looks like a fragment
            # 检查是否看起来像片段
            if self._is_fragment(current.text):
                # Try to merge with previous sentence
                # 尝试与前一个句子合并
                if merged:
                    prev = merged[-1]
                    merged[-1] = Sentence(
                        text=prev.text + " " + current.text,
                        start_pos=prev.start_pos,
                        end_pos=current.end_pos,
                        index=prev.index
                    )
                    i += 1
                    continue

            merged.append(current)
            i += 1

        # Reindex
        # 重新索引
        for idx, sent in enumerate(merged):
            sent.index = idx

        return merged

    def _is_fragment(self, text: str) -> bool:
        """
        Check if text appears to be a sentence fragment
        检查文本是否看起来是句子片段
        """
        text = text.strip()

        # Too short
        # 太短
        if len(text) < 10:
            return True

        # Starts with lowercase (unless it's a special word)
        # 以小写字母开头（除非是特殊词）
        if text[0].islower() and not text.startswith(("i.e.", "e.g.", "etc.")):
            return True

        # Don't treat header-like text as fragments (even without period)
        # 不将类似标题的文本视为片段（即使没有句号）
        if self._looks_like_header(text):
            return False

        # Doesn't end with sentence-ending punctuation
        # 不以句子结束标点结尾
        if text[-1] not in self.SENTENCE_ENDINGS:
            # But allow if it ends with a closing quote or parenthesis
            # 但允许以引号或括号结尾
            if text[-1] not in '"\')':
                return True

        return False

    def _looks_like_header(self, text: str) -> bool:
        """
        Check if text looks like a title or section header
        检查文本是否看起来像标题或章节标题
        """
        text = text.strip()

        # Check for numbered section pattern
        # 检查编号章节模式
        if self.numbered_section_pattern.match(text):
            return True

        # Check if text is a known section header
        # 检查是否为已知的章节标题
        text_lower = text.lower()
        cleaned = re.sub(r'^[\d.]+\s*', '', text_lower)
        if cleaned in self.SECTION_HEADERS:
            return True

        # Short text with mostly capitalized words (title-like)
        # 大多数单词首字母大写的短文本（像标题）
        words = text.split()
        if 3 <= len(words) <= 20 and len(text) <= 200:
            # Count capitalized words (excluding short words like "of", "the", "and")
            # 统计首字母大写的单词（排除短词如 "of", "the", "and"）
            capitalized = sum(1 for w in words if len(w) > 3 and w[0].isupper())
            total_significant = sum(1 for w in words if len(w) > 3)
            if total_significant > 0 and capitalized >= total_significant * 0.6:
                return True

        # Check for colon in middle (common in academic titles)
        # 检查中间是否有冒号（学术标题常见）
        if ':' in text and len(text) < 200 and text[-1] not in '.!?':
            return True

        return False

    def _detect_content_types(self, sentences: List[Sentence]) -> List[Sentence]:
        """
        Detect content type for each sentence and mark if it should be processed
        检测每个句子的内容类型并标记是否应该处理

        Args:
            sentences: List of Sentence objects

        Returns:
            Updated list with content_type and should_process set
        """
        in_references_section = False

        for i, sent in enumerate(sentences):
            text = sent.text.strip()

            # Track if we're in the References section
            # 跟踪是否在参考文献部分
            if self._is_references_header(text):
                in_references_section = True
                sent.content_type = ContentType.SECTION_HEADER
                sent.should_process = False
                continue

            # If in references section, mark as reference
            # 如果在参考文献部分，标记为参考文献
            if in_references_section:
                sent.content_type = ContentType.REFERENCE
                sent.should_process = False
                continue

            # Check for section headers
            # 检查章节标题
            if self._is_section_header(text):
                sent.content_type = ContentType.SECTION_HEADER
                sent.should_process = False
                continue

            # Check for title (first sentence, short, no period, title case)
            # 检查标题（第一个句子，短，无句号，标题格式）
            if i == 0 and self._is_title(text):
                sent.content_type = ContentType.TITLE
                sent.should_process = False
                continue

            # Check for table captions
            # 检查表格说明
            if self._is_table_caption(text):
                sent.content_type = ContentType.TABLE_HEADER
                sent.should_process = False
                continue

            # Check for figure captions
            # 检查图片说明
            if self._is_figure_caption(text):
                sent.content_type = ContentType.FIGURE_CAPTION
                sent.should_process = False
                continue

            # Check for metadata (author info, affiliation, etc.)
            # 检查元数据（作者信息、单位等）
            if self._is_metadata(text):
                sent.content_type = ContentType.METADATA
                sent.should_process = False
                continue

            # Check for reference entries (outside of references section)
            # 检查参考文献条目（在参考文献部分之外）
            if self._is_reference_entry(text):
                sent.content_type = ContentType.REFERENCE
                sent.should_process = False
                continue

            # Check for short fragments
            # 检查过短的片段
            if len(text) < 15 or len(text.split()) < 4:
                sent.content_type = ContentType.SHORT_FRAGMENT
                sent.should_process = False
                continue

            # Normal sentence - should be processed
            # 正常句子 - 应该处理
            sent.content_type = ContentType.SENTENCE
            sent.should_process = True

        return sentences

    def _is_section_header(self, text: str) -> bool:
        """
        Check if text is a section header
        检查文本是否为章节标题
        """
        text_lower = text.lower().strip()

        # Remove leading numbers and punctuation
        # 移除开头的数字和标点
        cleaned = re.sub(r'^[\d.]+\s*', '', text_lower)

        # Check against known section headers
        # 检查是否为已知的章节标题
        if cleaned in self.SECTION_HEADERS:
            return True

        # Check for numbered section pattern: "1. Introduction", "1.1 Background"
        # 检查编号章节模式
        if self.numbered_section_pattern.match(text):
            return True

        # Short text without sentence-ending punctuation (likely a header)
        # 没有句子结束标点的短文本（可能是标题）
        if len(text) < 50 and text[-1] not in '.!?':
            words = text.split()
            # Most words capitalized = likely header
            # 大多数词首字母大写 = 可能是标题
            if len(words) <= 6:
                capitalized = sum(1 for w in words if w[0].isupper() or w[0].isdigit())
                if capitalized >= len(words) * 0.6:
                    return True

        return False

    def _is_references_header(self, text: str) -> bool:
        """
        Check if text is the References section header
        检查文本是否为参考文献部分标题
        """
        text_lower = text.lower().strip()
        cleaned = re.sub(r'^[\d.]+\s*', '', text_lower)
        return cleaned in {"references", "bibliography", "works cited", "literature cited"}

    def _is_title(self, text: str) -> bool:
        """
        Check if text is likely a document title
        检查文本是否可能是文档标题
        """
        # Short enough to be a title
        # 短到足以成为标题
        if len(text) > 200:
            return False

        # Doesn't end with typical sentence punctuation
        # 不以典型的句子标点结尾
        if text[-1] in '.!?':
            return False

        # Contains mostly title-case words or all caps
        # 包含大多数首字母大写的词或全大写
        words = text.split()
        if len(words) < 3:
            return True

        capitalized = sum(1 for w in words if len(w) > 3 and w[0].isupper())
        return capitalized >= len(words) * 0.5

    def _is_table_caption(self, text: str) -> bool:
        """
        Check if text is a table caption
        检查文本是否为表格说明
        """
        return bool(self.table_pattern.match(text))

    def _is_figure_caption(self, text: str) -> bool:
        """
        Check if text is a figure caption
        检查文本是否为图片说明
        """
        return bool(self.figure_pattern.match(text))

    def _is_metadata(self, text: str) -> bool:
        """
        Check if text is metadata (author info, affiliation, etc.)
        检查文本是否为元数据
        """
        for pattern in self.metadata_patterns:
            if pattern.search(text):
                return True
        return False

    def _is_reference_entry(self, text: str) -> bool:
        """
        Check if text is a reference entry
        检查文本是否为参考文献条目
        """
        # Count how many reference patterns match
        # 计算匹配了多少参考文献模式
        matches = sum(1 for pattern in self.reference_patterns if pattern.search(text))
        # If multiple patterns match, it's likely a reference
        # 如果多个模式匹配，可能是参考文献
        return matches >= 2

    def segment_with_paragraphs(self, text: str) -> List[Sentence]:
        """
        Segment text while preserving paragraph information
        分割文本同时保留段落信息
        """
        paragraphs = text.split('\n\n')
        all_sentences = []

        for para_idx, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue

            sentences = self.segment(paragraph)
            for sent in sentences:
                sent.paragraph_index = para_idx
                sent.index = len(all_sentences)
                all_sentences.append(sent)

        return all_sentences


# Convenience function
# 便捷函数
def segment_text(text: str) -> List[Sentence]:
    """
    Convenience function to segment text
    分割文本的便捷函数
    """
    segmenter = SentenceSegmenter()
    return segmenter.segment(text)
