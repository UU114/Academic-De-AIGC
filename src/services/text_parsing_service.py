"""
Unified Text Parsing Service
统一文本解析服务

This service provides consistent text parsing across all substeps:
- Paragraph splitting (accurate boundary detection)
- Section detection (header recognition and content grouping)
- Word counting (language-aware)
- Statistical calculations (CV, mean, stdev, etc.)

All substeps should use this service to ensure consistent analysis.
所有子步骤应使用此服务以确保一致的分析。
"""

import re
import statistics
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content type classification / 内容类型分类"""
    BODY = "body"                    # Regular paragraph content / 正文段落
    SECTION_HEADER = "section_header"  # Main section title (1., 2., etc.) / 主章节标题
    SUBSECTION_HEADER = "subsection_header"  # Subsection title (1.1, 2.1, etc.) / 子章节标题
    TITLE = "title"                  # Document title / 文档标题
    ABSTRACT = "abstract"            # Abstract section / 摘要
    FIGURE_CAPTION = "figure_caption"  # Figure caption / 图片说明
    TABLE_CAPTION = "table_caption"  # Table caption / 表格说明
    REFERENCE = "reference"          # Reference entry / 参考文献条目
    METADATA = "metadata"            # Author, keywords, etc. / 作者、关键词等
    SHORT_FRAGMENT = "short_fragment"  # Too short to be a paragraph / 过短片段


@dataclass
class ParsedParagraph:
    """Parsed paragraph with metadata / 带元数据的解析段落"""
    index: int                       # Paragraph index (0-based) / 段落索引
    text: str                        # Paragraph text / 段落文本
    word_count: int                  # Word count / 词数
    char_count: int                  # Character count / 字符数
    sentence_count: int              # Sentence count / 句数
    content_type: ContentType        # Content type / 内容类型
    section_index: int = -1          # Which section this belongs to / 所属章节索引
    start_line: int = 0              # Original line number / 原始行号
    is_processable: bool = True      # Should be processed for analysis / 是否应该被分析


@dataclass
class ParsedSection:
    """Parsed section with metadata / 带元数据的解析章节"""
    index: int                       # Section index (0-based) / 章节索引
    role: str                        # Section role (introduction, methods, etc.) / 章节角色
    title: str                       # Section title / 章节标题
    start_paragraph: int             # First paragraph index / 起始段落索引
    end_paragraph: int               # Last paragraph index (inclusive) / 结束段落索引
    paragraph_count: int             # Number of paragraphs / 段落数
    word_count: int                  # Total word count / 总词数
    paragraphs: List[ParsedParagraph] = field(default_factory=list)


@dataclass
class DocumentStatistics:
    """Document-level statistics / 文档级统计"""
    total_paragraphs: int            # Total paragraph count / 总段落数
    total_words: int                 # Total word count / 总词数
    total_sentences: int             # Total sentence count / 总句数
    total_sections: int              # Total section count / 总章节数

    # Paragraph length statistics / 段落长度统计
    paragraph_lengths: List[int]     # List of paragraph word counts / 段落词数列表
    mean_paragraph_length: float     # Mean paragraph length / 平均段落长度
    stdev_paragraph_length: float    # Stdev of paragraph length / 段落长度标准差
    cv_paragraph_length: float       # CV of paragraph length / 段落长度变异系数
    min_paragraph_length: int        # Min paragraph length / 最小段落长度
    max_paragraph_length: int        # Max paragraph length / 最大段落长度

    # Section statistics / 章节统计
    section_paragraph_counts: List[int]  # Paragraphs per section / 每章节段落数
    section_word_counts: List[int]   # Words per section / 每章节词数


class TextParsingService:
    """
    Unified text parsing service for all substeps
    所有子步骤的统一文本解析服务
    """

    # Section header patterns (numbered and named)
    # 章节标题模式（编号和命名）
    # MAIN section patterns - single number (1., 2., etc.)
    # 主章节模式 - 单个数字（1., 2.等）
    MAIN_SECTION_PATTERNS = [
        r'^(\d+)\.?\s+[A-Z]',                        # 1. Title or 2 Title (single digit + capital letter)
        r'^([IVXLCDM]+)\.?\s+[A-Z]',                 # I. II. III. (Roman numerals)
        r'^(chapter\s+\d+[:\s]*)',                   # Chapter 1:
        r'^(section\s+\d+[:\s]*)',                   # Section 1:
        r'^(part\s+\d+[:\s]*)',                      # Part 1:
        r'^([一二三四五六七八九十]+)[、.]\s*',        # Chinese numbered: 一、二、
        r'^(第[一二三四五六七八九十\d]+[章部分])[：:\s]*',  # Chinese: 第一章 第一部分
    ]

    # SUBSECTION patterns - multiple numbers (1.1, 1.2, 2.1.1, etc.)
    # 子章节模式 - 多个数字（1.1, 1.2, 2.1.1等）
    SUBSECTION_PATTERNS = [
        r'^(\d+\.\d+(?:\.\d+)*)\s+',                 # 1.1 or 1.1.1 or 1.2.3.4
        r'^(第[一二三四五六七八九十\d]+节)[：:\s]*',  # Chinese: 第一节
    ]

    # Combined patterns for backward compatibility (deprecated - use MAIN_SECTION_PATTERNS)
    # 兼容性的组合模式（已弃用 - 使用 MAIN_SECTION_PATTERNS）
    NUMBERED_SECTION_PATTERNS = [
        r'^(\d+)\.?\s+[A-Z]',                        # 1. Title (main section)
        r'^(\d+\.\d+(?:\.\d+)*)\s+',                 # 1.1 or 1.1.1 (subsection)
        r'^([IVXLCDM]+\.?\s+)',                      # I. II. III. (Roman numerals)
        r'^(chapter\s+\d+[:\s]*)',                   # Chapter 1:
        r'^(section\s+\d+[:\s]*)',                   # Section 1:
        r'^(part\s+\d+[:\s]*)',                      # Part 1:
        r'^([一二三四五六七八九十]+[、.]\s*)',        # Chinese numbered: 一、二、
        r'^(第[一二三四五六七八九十\d]+[章节部分][：:\s]*)',  # Chinese: 第一章
    ]

    # Common academic section titles (case-insensitive)
    # 常见学术章节标题（不区分大小写）
    SECTION_TITLES = {
        # English
        'abstract': 'abstract',
        'introduction': 'introduction',
        'background': 'background',
        'literature review': 'literature_review',
        'related work': 'related_work',
        'theoretical framework': 'background',
        'methodology': 'methodology',
        'methods': 'methodology',
        'materials and methods': 'methodology',
        'research design': 'methodology',
        'data and methods': 'methodology',
        'experimental setup': 'methodology',
        'results': 'results',
        'findings': 'results',
        'analysis': 'results',
        'data analysis': 'results',
        'discussion': 'discussion',
        'discussion and analysis': 'discussion',
        'conclusion': 'conclusion',
        'conclusions': 'conclusion',
        'summary': 'conclusion',
        'summary and conclusions': 'conclusion',
        'implications': 'conclusion',
        'future work': 'conclusion',
        'limitations': 'discussion',
        'references': 'references',
        'bibliography': 'references',
        'works cited': 'references',
        'acknowledgments': 'acknowledgments',
        'acknowledgements': 'acknowledgments',
        'appendix': 'appendix',
        'appendices': 'appendix',
        # Chinese
        '摘要': 'abstract',
        '引言': 'introduction',
        '绪论': 'introduction',
        '前言': 'introduction',
        '背景': 'background',
        '文献综述': 'literature_review',
        '相关工作': 'related_work',
        '研究方法': 'methodology',
        '方法': 'methodology',
        '实验方法': 'methodology',
        '材料与方法': 'methodology',
        '结果': 'results',
        '实验结果': 'results',
        '结果与分析': 'results',
        '讨论': 'discussion',
        '分析与讨论': 'discussion',
        '结论': 'conclusion',
        '总结': 'conclusion',
        '结论与展望': 'conclusion',
        '参考文献': 'references',
        '致谢': 'acknowledgments',
        '附录': 'appendix',
    }

    # Patterns to identify non-body content
    # 识别非正文内容的模式
    FIGURE_PATTERN = re.compile(
        r'^(figure|fig\.?|图)\s*\d+',
        re.IGNORECASE
    )
    TABLE_PATTERN = re.compile(
        r'^(table|tab\.?|表)\s*\d+',
        re.IGNORECASE
    )
    REFERENCE_ENTRY_PATTERN = re.compile(
        r'^\[\d+\]|^[A-Z][a-z]+,?\s+[A-Z].*\(\d{4}\)|^\d+\.\s+[A-Z][a-z]+'
    )
    KEYWORDS_PATTERN = re.compile(
        r'^(keywords?|key\s*words?|关键词|关键字)[：:]\s*',
        re.IGNORECASE
    )
    AUTHOR_PATTERN = re.compile(
        r'^(author|作者|通讯作者|correspondence)[：:s]*',
        re.IGNORECASE
    )

    # Sentence splitting patterns
    # 分句模式
    SENTENCE_END_PATTERN = re.compile(
        r'(?<=[.!?。！？])\s+(?=[A-Z\u4e00-\u9fff])|(?<=[。！？])'
    )

    def __init__(self, min_paragraph_words: int = 15, language: str = 'auto'):
        """
        Initialize the text parsing service
        初始化文本解析服务

        Args:
            min_paragraph_words: Minimum words to be considered a paragraph (default 15)
                                 被视为段落的最小词数（默认15）
            language: 'en', 'zh', or 'auto' for automatic detection
                      'en'、'zh' 或 'auto' 自动检测
        """
        self.min_paragraph_words = min_paragraph_words
        self.language = language

    def parse_document(self, text: str) -> Tuple[List[ParsedParagraph], List[ParsedSection], DocumentStatistics]:
        """
        Parse document into paragraphs, sections, and statistics
        将文档解析为段落、章节和统计数据

        Args:
            text: Document text

        Returns:
            Tuple of (paragraphs, sections, statistics)
        """
        # Step 1: Split into raw paragraphs
        # 第1步：分割为原始段落
        raw_paragraphs = self._split_raw_paragraphs(text)

        # Step 2: Classify and parse each paragraph
        # 第2步：分类并解析每个段落
        parsed_paragraphs = self._parse_paragraphs(raw_paragraphs)

        # Step 3: Detect sections
        # 第3步：检测章节
        sections = self._detect_sections(parsed_paragraphs)

        # Step 4: Calculate statistics
        # 第4步：计算统计数据
        stats = self._calculate_statistics(parsed_paragraphs, sections)

        return parsed_paragraphs, sections, stats

    def _split_raw_paragraphs(self, text: str) -> List[Tuple[str, int]]:
        """
        Split text into raw paragraphs with line numbers
        将文本分割为带行号的原始段落

        Returns:
            List of (paragraph_text, start_line_number)
        """
        # Normalize line endings
        # 规范化换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Try double newline first
        # 首先尝试双换行
        if '\n\n' in text:
            parts = re.split(r'\n\n+', text)
        else:
            # Fall back to single newline
            # 回退到单换行
            parts = text.split('\n')

        result = []
        current_line = 1

        for part in parts:
            stripped = part.strip()
            if stripped:
                # Check if paragraph starts with a section header followed by content
                # 检查段落是否以章节标题开头，后面跟着内容
                lines = stripped.split('\n')
                if len(lines) > 1:
                    first_line = lines[0].strip()
                    # Check if first line looks like a section header
                    # 检查第一行是否看起来像章节标题
                    if self._is_section_header(first_line):
                        # Split: first add header, then add remaining content
                        # 拆分：先添加标题，再添加剩余内容
                        result.append((first_line, current_line))
                        remaining = '\n'.join(lines[1:]).strip()
                        if remaining:
                            result.append((remaining, current_line + 1))
                    else:
                        result.append((stripped, current_line))
                else:
                    result.append((stripped, current_line))
            # Count lines in this part
            current_line += part.count('\n') + 2  # +2 for the split delimiter

        return result

    def _parse_paragraphs(self, raw_paragraphs: List[Tuple[str, int]]) -> List[ParsedParagraph]:
        """
        Parse raw paragraphs into ParsedParagraph objects
        将原始段落解析为ParsedParagraph对象
        """
        parsed = []
        body_index = 0  # Index for body paragraphs only / 仅正文段落的索引

        for i, (text, line_num) in enumerate(raw_paragraphs):
            content_type = self._classify_content(text)
            word_count = self._count_words(text)
            char_count = len(text)
            sentence_count = self._count_sentences(text)

            # Determine if this is processable (body content)
            # 确定是否可处理（正文内容）
            is_processable = (
                content_type == ContentType.BODY and
                word_count >= self.min_paragraph_words
            )

            para = ParsedParagraph(
                index=i,
                text=text,
                word_count=word_count,
                char_count=char_count,
                sentence_count=sentence_count,
                content_type=content_type,
                start_line=line_num,
                is_processable=is_processable
            )

            parsed.append(para)

            if is_processable:
                body_index += 1

        return parsed

    def _classify_content(self, text: str) -> ContentType:
        """
        Classify content type of a text block
        分类文本块的内容类型
        """
        text_lower = text.lower().strip()
        word_count = self._count_words(text)

        # Check for figure/table caption
        # 检查图表说明
        if self.FIGURE_PATTERN.match(text_lower):
            return ContentType.FIGURE_CAPTION
        if self.TABLE_PATTERN.match(text_lower):
            return ContentType.TABLE_CAPTION

        # Check for keywords/author metadata
        # 检查关键词/作者元数据
        if self.KEYWORDS_PATTERN.match(text_lower) or self.AUTHOR_PATTERN.match(text_lower):
            return ContentType.METADATA

        # Check for section header BEFORE reference entry
        # 在检查参考文献之前先检查章节标题
        # This is important because "1. Introduction" matches both patterns
        # 这很重要，因为 "1. Introduction" 同时匹配两种模式
        first_line = text.split('\n')[0].strip()

        # Check if it's a subsection header (1.1, 1.2, 2.1.1, etc.)
        # 检查是否为子章节标题（1.1, 1.2, 2.1.1等）
        if self._is_subsection_header(first_line):
            return ContentType.SUBSECTION_HEADER

        # Check if it's a main section header (1., 2., Introduction, etc.)
        # 检查是否为主章节标题（1., 2., Introduction等）
        if self._is_main_section_header(first_line):
            return ContentType.SECTION_HEADER

        # Check for reference entry (after section headers to avoid false positives)
        # 检查参考文献条目（在章节标题之后，避免误判）
        if self.REFERENCE_ENTRY_PATTERN.match(text):
            return ContentType.REFERENCE

        # Check if too short
        # 检查是否过短
        if word_count < self.min_paragraph_words:
            # Could be a title if very short and at beginning
            # 如果非常短且在开头可能是标题
            if word_count <= 3 and text.isupper():
                return ContentType.TITLE
            return ContentType.SHORT_FRAGMENT

        return ContentType.BODY

    def _is_main_section_header(self, text: str) -> bool:
        """
        Check if text is a MAIN section header (1., 2., not 1.1, 1.2)
        检查文本是否为主章节标题（1., 2.，不是1.1, 1.2）
        """
        text_stripped = text.strip()
        word_count = self._count_words(text)

        # Headers are usually short (< 15 words)
        # 标题通常较短（< 15词）
        if word_count > 15:
            return False

        # FIRST check if it's a subsection (1.1, 1.2, etc.) - NOT a main section
        # 首先检查是否为子章节（1.1, 1.2等）- 不是主章节
        for pattern in self.SUBSECTION_PATTERNS:
            if re.match(pattern, text_stripped, re.IGNORECASE):
                return False

        # Check main section patterns
        # 检查主章节模式
        for pattern in self.MAIN_SECTION_PATTERNS:
            if re.match(pattern, text_stripped, re.IGNORECASE):
                return True

        # Check named section titles (case-insensitive)
        # 检查命名章节标题（不区分大小写）
        text_lower = text_stripped.lower()
        clean_text = re.sub(r'^[\d.]+\s*', '', text_lower).strip()
        clean_text = re.sub(r'^[IVXLCDM]+[.:\s]+', '', clean_text, flags=re.IGNORECASE).strip()

        for title in self.SECTION_TITLES:
            if clean_text == title or clean_text.startswith(title + ':') or clean_text.startswith(title + ':'):
                return True

        # Check if all caps (likely a header)
        # 检查是否全大写（可能是标题）
        if text_stripped.isupper() and word_count < 10:
            return True

        return False

    def _is_subsection_header(self, text: str) -> bool:
        """
        Check if text is a SUBSECTION header (1.1, 1.2, 2.1.1, etc.)
        检查文本是否为子章节标题（1.1, 1.2, 2.1.1等）
        """
        text_stripped = text.strip()
        word_count = self._count_words(text)

        # Headers are usually short (< 15 words)
        # 标题通常较短（< 15词）
        if word_count > 15:
            return False

        # Check subsection patterns
        # 检查子章节模式
        for pattern in self.SUBSECTION_PATTERNS:
            if re.match(pattern, text_stripped, re.IGNORECASE):
                return True

        return False

    def _is_section_header(self, text: str) -> bool:
        """
        Check if text is ANY section header (main or subsection)
        检查文本是否为任何章节标题（主章节或子章节）

        For backward compatibility. Use _is_main_section_header or _is_subsection_header
        for more specific checks.
        为了向后兼容。使用 _is_main_section_header 或 _is_subsection_header 进行更具体的检查。
        """
        return self._is_main_section_header(text) or self._is_subsection_header(text)

    def _get_section_role(self, header_text: str) -> str:
        """
        Get the role of a section from its header
        从标题获取章节角色
        """
        text_lower = header_text.lower().strip()

        # Remove Arabic numbering (e.g., "1." "1.1")
        # 移除阿拉伯数字编号
        clean_text = re.sub(r'^[\d.]+\s*', '', text_lower).strip()

        # Remove Roman numerals ONLY if followed by period/colon/space
        # 仅当罗马数字后跟句点/冒号/空格时才移除
        clean_text = re.sub(r'^[IVXLCDM]+[.:\s]+', '', clean_text, flags=re.IGNORECASE).strip()

        # Remove chapter/section/part prefix
        # 移除 chapter/section/part 前缀
        clean_text = re.sub(r'^(chapter|section|part)\s*\d*[:\s]*', '', clean_text).strip()

        # Check known section titles
        # 检查已知章节标题
        for title, role in self.SECTION_TITLES.items():
            if clean_text == title or clean_text.startswith(title):
                return role

        return 'body'

    def _detect_sections(self, paragraphs: List[ParsedParagraph]) -> List[ParsedSection]:
        """
        Detect sections from parsed paragraphs
        从解析的段落中检测章节
        """
        sections = []
        current_section = None
        current_paragraphs = []
        body_para_count = 0

        for para in paragraphs:
            if para.content_type == ContentType.SECTION_HEADER:
                # Save previous section
                # 保存前一个章节
                if current_section is not None:
                    current_section.paragraphs = current_paragraphs
                    current_section.paragraph_count = len([p for p in current_paragraphs if p.is_processable])
                    current_section.word_count = sum(p.word_count for p in current_paragraphs if p.is_processable)
                    current_section.end_paragraph = body_para_count - 1 if body_para_count > 0 else 0
                    sections.append(current_section)

                # Start new section
                # 开始新章节
                role = self._get_section_role(para.text)
                current_section = ParsedSection(
                    index=len(sections),
                    role=role,
                    title=para.text,
                    start_paragraph=body_para_count,
                    end_paragraph=body_para_count,  # Will be updated
                    paragraph_count=0,
                    word_count=0
                )
                current_paragraphs = []
            else:
                # Add to current section
                # 添加到当前章节
                if current_section is None:
                    # Create default section for content before first header
                    # 为第一个标题之前的内容创建默认章节
                    current_section = ParsedSection(
                        index=0,
                        role='body',
                        title='Main Content',
                        start_paragraph=0,
                        end_paragraph=0,
                        paragraph_count=0,
                        word_count=0
                    )

                current_paragraphs.append(para)
                para.section_index = current_section.index

                if para.is_processable:
                    body_para_count += 1

        # Don't forget the last section
        # 不要忘记最后一个章节
        if current_section is not None:
            current_section.paragraphs = current_paragraphs
            current_section.paragraph_count = len([p for p in current_paragraphs if p.is_processable])
            current_section.word_count = sum(p.word_count for p in current_paragraphs if p.is_processable)
            current_section.end_paragraph = body_para_count - 1 if body_para_count > 0 else 0
            sections.append(current_section)

        # If no sections found, create one default section
        # 如果没有找到章节，创建一个默认章节
        if not sections:
            processable = [p for p in paragraphs if p.is_processable]
            sections.append(ParsedSection(
                index=0,
                role='body',
                title='Main Content',
                start_paragraph=0,
                end_paragraph=len(processable) - 1 if processable else 0,
                paragraph_count=len(processable),
                word_count=sum(p.word_count for p in processable),
                paragraphs=paragraphs
            ))

        return sections

    def _calculate_statistics(
        self,
        paragraphs: List[ParsedParagraph],
        sections: List[ParsedSection]
    ) -> DocumentStatistics:
        """
        Calculate document statistics
        计算文档统计数据
        """
        # Get processable paragraphs only
        # 仅获取可处理的段落
        processable = [p for p in paragraphs if p.is_processable]

        if not processable:
            return DocumentStatistics(
                total_paragraphs=0,
                total_words=0,
                total_sentences=0,
                total_sections=len(sections),
                paragraph_lengths=[],
                mean_paragraph_length=0,
                stdev_paragraph_length=0,
                cv_paragraph_length=0,
                min_paragraph_length=0,
                max_paragraph_length=0,
                section_paragraph_counts=[s.paragraph_count for s in sections],
                section_word_counts=[s.word_count for s in sections]
            )

        # Calculate paragraph statistics
        # 计算段落统计
        lengths = [p.word_count for p in processable]
        total_words = sum(lengths)
        total_sentences = sum(p.sentence_count for p in processable)

        mean_len = statistics.mean(lengths) if lengths else 0
        stdev_len = statistics.stdev(lengths) if len(lengths) > 1 else 0
        cv = stdev_len / mean_len if mean_len > 0 else 0

        return DocumentStatistics(
            total_paragraphs=len(processable),
            total_words=total_words,
            total_sentences=total_sentences,
            total_sections=len(sections),
            paragraph_lengths=lengths,
            mean_paragraph_length=round(mean_len, 1),
            stdev_paragraph_length=round(stdev_len, 1),
            cv_paragraph_length=round(cv, 3),
            min_paragraph_length=min(lengths) if lengths else 0,
            max_paragraph_length=max(lengths) if lengths else 0,
            section_paragraph_counts=[s.paragraph_count for s in sections],
            section_word_counts=[s.word_count for s in sections]
        )

    def _count_words(self, text: str) -> int:
        """
        Count words in text (language-aware)
        计算文本中的词数（语言感知）

        For English: Count space-separated words
        For Chinese: Count characters (excluding punctuation)
        """
        if not text:
            return 0

        # Detect language if auto
        # 自动检测语言
        lang = self.language
        if lang == 'auto':
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            total_chars = len(re.sub(r'\s+', '', text))
            lang = 'zh' if chinese_chars > total_chars * 0.3 else 'en'

        if lang == 'zh':
            # Count Chinese characters
            # 计算中文字符
            chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
            # Also count English words
            english = len(re.findall(r'\b[a-zA-Z]+\b', text))
            return chinese + english
        else:
            # Count English words
            # 计算英文单词
            # Remove URLs and emails first
            text = re.sub(r'https?://\S+', '', text)
            text = re.sub(r'\S+@\S+\.\S+', '', text)
            words = re.findall(r"\b[a-zA-Z]+(?:[-'][a-zA-Z]+)*\b", text)
            return len(words)

    def _count_sentences(self, text: str) -> int:
        """
        Count sentences in text
        计算文本中的句数
        """
        if not text:
            return 0

        # Split by sentence-ending punctuation
        # 按句末标点分割
        sentences = re.split(r'[.!?。！？]+', text)
        # Filter empty strings
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences) if sentences else 1  # At least 1 if there's text

    # ==========================================================================
    # Two-Stage Section Analysis: Calculate statistics based on LLM structure
    # 两阶段章节分析：根据LLM结构计算统计数据
    # ==========================================================================

    def calculate_section_statistics(
        self,
        text: str,
        llm_sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Stage 2: Calculate accurate statistics for sections identified by LLM
        阶段2：为LLM识别的章节计算准确的统计数据

        This method takes the section structure from LLM (titles, roles, start_line)
        and calculates accurate word counts, paragraph counts, etc. using rules.

        此方法接收LLM识别的章节结构（标题、角色、起始行），
        并使用规则计算准确的词数、段落数等统计数据。

        Args:
            text: Document text
            llm_sections: List of sections from LLM with 'role', 'title', 'start_line'

        Returns:
            List of sections with both structure and accurate statistics
        """
        if not llm_sections:
            logger.warning("No sections from LLM, falling back to rule-based detection")
            return self.get_section_distribution(text)

        # Split text into lines for accurate boundary mapping
        # 将文本分割为行以进行准确的边界映射
        lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        total_lines = len(lines)
        logger.info(f"Document has {total_lines} total lines")

        # IMPORTANT: Re-map section positions by searching for titles in actual document
        # 重要：通过在实际文档中搜索标题来重新映射章节位置
        # LLM's start_line may not match actual document due to truncation
        # LLM的start_line可能因截断而与实际文档不匹配
        remapped_sections = []
        for section in llm_sections:
            title = section.get('title', '')
            role = section.get('role', 'body')
            llm_start_line = section.get('start_line', 0)

            # Search for the title in actual document
            # 在实际文档中搜索标题
            actual_start_line = None
            title_lower = title.lower().strip()

            # Extract the main title part (e.g., "Introduction" from "1. Introduction")
            # 提取标题主要部分
            title_parts = title.split('. ', 1)
            main_title = title_parts[1].lower().strip() if len(title_parts) > 1 else title_lower

            for i, line in enumerate(lines):
                line_stripped = line.strip()
                line_lower = line_stripped.lower()
                line_word_count = len(line_stripped.split())

                # Only match SHORT lines (headers are usually < 10 words)
                # 只匹配短行（标题通常少于10个词）
                if line_word_count > 10:
                    continue

                # Priority 1: Exact match
                # 优先级1：精确匹配
                if line_lower == title_lower:
                    actual_start_line = i
                    break

                # Priority 2: Line starts with the full title (e.g., "1. Introduction")
                # 优先级2：行以完整标题开头
                if line_lower.startswith(title_lower):
                    actual_start_line = i
                    break

                # Priority 3: For numbered sections, match "N. SectionName" pattern
                # 优先级3：对于编号章节，匹配"N. 章节名"模式
                # e.g., for "4. Experiments", match lines like "4. Experiments" or "4.Experiments"
                if len(title_parts) > 1 and title_parts[0].isdigit():
                    number = title_parts[0]
                    section_name = main_title
                    # Match "4. Experiments" or "4.Experiments" (with or without space)
                    # 匹配"4. Experiments"或"4.Experiments"（有或无空格）
                    if (line_lower.startswith(number + '. ' + section_name) or
                        line_lower.startswith(number + '.' + section_name) or
                        line_lower == number + '. ' + section_name or
                        line_lower == number + '.' + section_name):
                        actual_start_line = i
                        break

                # Priority 4: Match standalone section name (for unnumbered sections)
                # 优先级4：匹配独立章节名（用于无编号章节）
                # Only if line is very short (1-3 words) to avoid false matches
                if line_word_count <= 3 and line_lower == main_title:
                    actual_start_line = i
                    break

            if actual_start_line is None:
                # Fall back to LLM's start_line if title not found
                # 如果未找到标题，回退到LLM的start_line
                actual_start_line = min(llm_start_line, total_lines - 1)
                logger.warning(f"Could not find title '{title}' in document, using LLM line {llm_start_line}")
            else:
                if actual_start_line != llm_start_line:
                    logger.info(f"Remapped '{title}' from line {llm_start_line} to {actual_start_line}")

            remapped_sections.append({
                'role': role,
                'title': title,
                'start_line': actual_start_line
            })

        # Sort sections by actual start_line
        # 按实际start_line排序
        sorted_sections = sorted(remapped_sections, key=lambda s: s.get('start_line', 0))

        # Calculate end_line for each section (next section's start_line - 1)
        # 计算每个章节的结束行（下一章节的起始行 - 1）
        result_sections = []
        for i, section in enumerate(sorted_sections):
            start_line = section.get('start_line', 0)

            # Determine end_line
            # 确定结束行
            if i + 1 < len(sorted_sections):
                end_line = sorted_sections[i + 1].get('start_line', total_lines) - 1
            else:
                end_line = total_lines - 1

            # Ensure valid bounds
            # 确保有效边界
            start_line = max(0, min(start_line, total_lines - 1))
            end_line = max(start_line, min(end_line, total_lines - 1))

            # Extract section text
            # 提取章节文本
            section_lines = lines[start_line:end_line + 1]
            section_text = '\n'.join(section_lines)

            # Calculate statistics for this section
            # 计算此章节的统计数据
            word_count = self._count_words(section_text)
            paragraph_count = self._count_paragraphs(section_text)
            sentence_count = self._count_sentences(section_text)

            # Build result section with snake_case field names
            # 构建结果章节，使用snake_case字段名
            result_sections.append({
                'index': i,
                'role': section.get('role', 'body'),
                'title': section.get('title', f'Section {i + 1}'),
                'start_line': start_line,
                'end_line': end_line,
                'paragraph_count': paragraph_count,
                'word_count': word_count,
                'sentence_count': sentence_count,
                # For backward compatibility (camelCase)
                # 向后兼容（驼峰命名）
                'startLine': start_line,
                'endLine': end_line,
                'paragraphCount': paragraph_count,
                'wordCount': word_count,
                'sentenceCount': sentence_count,
                'startParagraph': start_line,
                'endParagraph': end_line,
            })

            logger.debug(f"Section '{section.get('title')}' ({section.get('role')}): "
                        f"lines {start_line}-{end_line}, {word_count} words, {paragraph_count} paragraphs")

        # Filter out title-only sections (role='title' with very few words)
        # 过滤掉仅标题的章节（role='title'且词数很少）
        filtered_sections = []
        for s in result_sections:
            if s['role'] == 'title' and s['word_count'] < 20:
                logger.debug(f"Filtering out title-only section: '{s['title']}'")
                continue
            filtered_sections.append(s)

        # Re-index filtered sections
        # 重新为过滤后的章节编号
        for i, s in enumerate(filtered_sections):
            s['index'] = i

        return filtered_sections

    def _count_words(self, text: str) -> int:
        """
        Count words in text (handles both English and Chinese)
        计算文本中的词数（处理英文和中文）
        """
        if not text or not text.strip():
            return 0

        # Count English words
        # 计算英文词数
        english_words = len(re.findall(r'[a-zA-Z]+', text))

        # Count Chinese characters (each character is a "word")
        # 计算中文字符数（每个字符算一个"词"）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))

        return english_words + chinese_chars

    def _count_paragraphs(self, text: str) -> int:
        """
        Count paragraphs in text
        计算文本中的段落数
        """
        if not text or not text.strip():
            return 0

        # Split by double newlines or blank lines
        # 按双换行或空行分割
        paragraphs = re.split(r'\n\s*\n', text.strip())
        # Filter empty paragraphs
        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return len(paragraphs) if paragraphs else 1

    # ==========================================================================
    # Convenience methods for getting specific data
    # 获取特定数据的便捷方法
    # ==========================================================================

    def get_body_paragraphs(self, text: str) -> List[ParsedParagraph]:
        """
        Get only body paragraphs (processable content)
        仅获取正文段落（可处理的内容）
        """
        paragraphs, _, _ = self.parse_document(text)
        return [p for p in paragraphs if p.is_processable]

    def get_section_distribution(self, text: str) -> List[Dict[str, Any]]:
        """
        Get section distribution in dict format (for API responses)
        获取章节分布（字典格式，用于API响应）

        Note: Filters out "Main Content" sections with 0 body paragraphs,
        as these typically contain only title/metadata and should not be
        included in section uniformity analysis (CV calculation).
        注意：过滤掉没有正文段落的"Main Content"章节，因为这些章节通常
        只包含标题/元数据，不应该被计入章节均匀性分析（CV计算）。
        """
        _, sections, _ = self.parse_document(text)

        # Filter out default "Main Content" sections with 0 body paragraphs
        # These are placeholder sections for content before the first header
        # (typically just document title/metadata, not actual body content)
        # 过滤掉没有正文段落的默认"Main Content"章节
        # 这些是第一个标题之前内容的占位符章节（通常只是文档标题/元数据）
        filtered_sections = []
        for s in sections:
            # Keep section if it has body paragraphs, OR if it's the only section
            # 如果章节有正文段落，或者它是唯一的章节，则保留
            if s.paragraph_count > 0 or len(sections) == 1:
                filtered_sections.append(s)
            else:
                logger.debug(f"Filtering out empty section: '{s.title}' (role={s.role}, paragraphs={s.paragraph_count})")

        # Re-index the remaining sections
        # 重新为剩余章节编号
        result = []
        for idx, s in enumerate(filtered_sections):
            result.append({
                'index': idx,
                'role': s.role,
                'title': s.title,
                'paragraphCount': s.paragraph_count,
                'wordCount': s.word_count,
                'startParagraph': s.start_paragraph,
                'endParagraph': s.end_paragraph
            })

        return result

    def get_statistics_dict(self, text: str) -> Dict[str, Any]:
        """
        Get statistics in dict format (for API responses and LLM prompts)
        获取统计数据（字典格式，用于API响应和LLM提示）
        """
        paragraphs, sections, stats = self.parse_document(text)

        # Get filtered section distribution (excludes empty sections)
        # 获取过滤后的章节分布（排除空章节）
        section_distribution = self.get_section_distribution(text)

        return {
            'paragraph_count': stats.total_paragraphs,
            'total_word_count': stats.total_words,
            'total_sentence_count': stats.total_sentences,
            'paragraph_lengths': stats.paragraph_lengths,
            'mean_length': stats.mean_paragraph_length,
            'stdev_length': stats.stdev_paragraph_length,
            'cv': stats.cv_paragraph_length,
            'min_length': stats.min_paragraph_length,
            'max_length': stats.max_paragraph_length,
            # Use filtered section count for consistency
            # 使用过滤后的章节数以保持一致性
            'section_count': len(section_distribution),
            'section_distribution': section_distribution
        }


# =============================================================================
# Singleton instance for global use
# 全局使用的单例实例
# =============================================================================

_default_service: Optional[TextParsingService] = None


def get_text_parsing_service(min_paragraph_words: int = 15, language: str = 'auto') -> TextParsingService:
    """
    Get the default text parsing service instance
    获取默认的文本解析服务实例
    """
    global _default_service
    if _default_service is None:
        _default_service = TextParsingService(min_paragraph_words, language)
    return _default_service


def parse_document(text: str) -> Tuple[List[ParsedParagraph], List[ParsedSection], DocumentStatistics]:
    """
    Convenience function to parse document using default service
    使用默认服务解析文档的便捷函数
    """
    return get_text_parsing_service().parse_document(text)


def get_body_paragraphs(text: str) -> List[ParsedParagraph]:
    """
    Convenience function to get body paragraphs
    获取正文段落的便捷函数
    """
    return get_text_parsing_service().get_body_paragraphs(text)


def get_section_distribution(text: str) -> List[Dict[str, Any]]:
    """
    Convenience function to get section distribution
    获取章节分布的便捷函数
    """
    return get_text_parsing_service().get_section_distribution(text)


def get_statistics(text: str) -> Dict[str, Any]:
    """
    Convenience function to get statistics
    获取统计数据的便捷函数
    """
    return get_text_parsing_service().get_statistics_dict(text)
