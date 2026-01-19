"""
Section Layer API Routes (Layer 4)
章节层API路由（第4层）

Sub-step Endpoints:
- POST /step2-0/identify - Step 2.0: Section Identification
- POST /step2-1/order - Step 2.1: Section Order & Structure
- POST /step2-2/length - Step 2.2: Section Length Distribution
- POST /step2-3/similarity - Step 2.3: Internal Structure Similarity (NEW)
- POST /step2-4/transition - Step 2.4: Section Transition
- POST /step2-5/logic - Step 2.5: Inter-Section Logic

Legacy Endpoints:
- POST /logic - Step 2.1: Section Logic Flow (legacy)
- POST /transition - Step 2.2: Section Transitions (legacy)
- POST /length - Step 2.3: Section Length Distribution (legacy)
- POST /analyze - Combined section analysis
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any, List, Tuple
import logging
import time
import re
import statistics
from collections import Counter

from src.api.routes.analysis.schemas import (
    SectionAnalysisRequest,
    SectionAnalysisResponse,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
    IssueSeverity,
    # Step 2.0 schemas
    SectionIdentificationRequest,
    SectionIdentificationResponse,
    SectionInfo,
    # Step 2.1 schemas
    SectionOrderRequest,
    SectionOrderResponse,
    SectionOrderAnalysis,
    # Step 2.2 schemas
    SectionLengthRequest,
    SectionLengthResponse,
    SectionLengthInfo,
    # Step 2.3 schemas
    InternalStructureSimilarityRequest,
    InternalStructureSimilarityResponse,
    SectionInternalStructure,
    ParagraphFunctionInfo,
    StructureSimilarityPair,
    # Step 2.4 schemas
    SectionTransitionRequest,
    SectionTransitionResponse,
    SectionTransitionInfo,
    # Step 2.5 schemas
    InterSectionLogicRequest,
    InterSectionLogicResponse,
    ArgumentChainNode,
    RedundancyInfo,
    ProgressionPatternInfo,
)
from src.core.analyzer.layers import SectionAnalyzer, LayerContext
from src.core.preprocessor.segmenter import SentenceSegmenter, ContentType
from src.services.text_parsing_service import get_text_parsing_service

# Import LLM handlers for Layer 4 substeps
# 导入 Layer 4 子步骤的 LLM handler
from src.api.routes.substeps.layer4.step2_0_handler import Step2_0Handler
from src.api.routes.substeps.layer4.step2_1_handler import Step2_1Handler
from src.api.routes.substeps.layer4.step2_2_handler import Step2_2Handler
from src.api.routes.substeps.layer4.step2_3_handler import Step2_3Handler
from src.api.routes.substeps.layer4.step2_4_handler import Step2_4Handler
from src.api.routes.substeps.layer4.step2_5_handler import Step2_5Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handlers
# 初始化 LLM handler
step2_0_handler = Step2_0Handler()
step2_1_handler = Step2_1Handler()
step2_2_handler = Step2_2Handler()
step2_3_handler = Step2_3Handler()
step2_4_handler = Step2_4Handler()
step2_5_handler = Step2_5Handler()

# Reusable segmenter instance
# 可重用的分句器实例
_segmenter = SentenceSegmenter()


# Patterns for detecting section headers (main vs subsection)
# 检测章节标题的模式（主章节 vs 子章节）
MAIN_SECTION_PATTERN = re.compile(
    r'^(?:\s*)(\d+)\.?\s+(.+)$'  # Pattern: "1. Title" or "2 Title" (single number)
)
SUBSECTION_PATTERN = re.compile(
    r'^(?:\s*)(\d+)\.(\d+)(?:\.\d+)*\.?\s+(.+)$'  # Pattern: "1.1 Title" or "2.1.1 Title"
)
ROMAN_MAIN_SECTION_PATTERN = re.compile(
    r'^(?:\s*)([IVXLCDM]+)\.?\s+(.+)$',  # Pattern: "I. Title" or "II Title"
    re.IGNORECASE
)

# Standalone keyword section headers (no numbering required)
# 独立关键词章节标题（无需编号）
# These are commonly used as section titles without numbering in academic papers
# 这些是学术论文中常用的无编号章节标题
STANDALONE_SECTION_KEYWORDS = {
    # Pre-body sections (appear before numbered sections)
    # 正文前章节（出现在编号章节之前）
    "abstract": {"role": "abstract", "position": "pre", "priority": 1},
    "摘要": {"role": "abstract", "position": "pre", "priority": 1},
    "keywords": {"role": "keywords", "position": "pre", "priority": 2},
    "关键词": {"role": "keywords", "position": "pre", "priority": 2},
    "key words": {"role": "keywords", "position": "pre", "priority": 2},

    # Main body sections (can be numbered or standalone)
    # 正文章节（可编号或独立）
    "introduction": {"role": "introduction", "position": "body", "priority": 10},
    "引言": {"role": "introduction", "position": "body", "priority": 10},
    "背景": {"role": "background", "position": "body", "priority": 11},
    "background": {"role": "background", "position": "body", "priority": 11},
    "literature review": {"role": "literature_review", "position": "body", "priority": 12},
    "related work": {"role": "literature_review", "position": "body", "priority": 12},
    "文献综述": {"role": "literature_review", "position": "body", "priority": 12},
    "methodology": {"role": "methodology", "position": "body", "priority": 20},
    "methods": {"role": "methodology", "position": "body", "priority": 20},
    "method": {"role": "methodology", "position": "body", "priority": 20},
    "方法": {"role": "methodology", "position": "body", "priority": 20},
    "研究方法": {"role": "methodology", "position": "body", "priority": 20},
    "materials and methods": {"role": "methodology", "position": "body", "priority": 20},
    "experimental": {"role": "methodology", "position": "body", "priority": 21},
    "experiment": {"role": "methodology", "position": "body", "priority": 21},
    "experiments": {"role": "methodology", "position": "body", "priority": 21},
    "实验": {"role": "methodology", "position": "body", "priority": 21},
    "results": {"role": "results", "position": "body", "priority": 30},
    "结果": {"role": "results", "position": "body", "priority": 30},
    "findings": {"role": "results", "position": "body", "priority": 30},
    "analysis": {"role": "results", "position": "body", "priority": 31},
    "分析": {"role": "results", "position": "body", "priority": 31},
    "results and discussion": {"role": "results", "position": "body", "priority": 32},
    "discussion": {"role": "discussion", "position": "body", "priority": 40},
    "讨论": {"role": "discussion", "position": "body", "priority": 40},

    # Post-body sections (appear after numbered sections)
    # 正文后章节（出现在编号章节之后）
    "conclusion": {"role": "conclusion", "position": "post", "priority": 90},
    "conclusions": {"role": "conclusion", "position": "post", "priority": 90},
    "结论": {"role": "conclusion", "position": "post", "priority": 90},
    "summary": {"role": "conclusion", "position": "post", "priority": 91},
    "总结": {"role": "conclusion", "position": "post", "priority": 91},
    "future work": {"role": "conclusion", "position": "post", "priority": 92},
    "limitations": {"role": "conclusion", "position": "post", "priority": 93},
    "acknowledgments": {"role": "acknowledgments", "position": "post", "priority": 95},
    "acknowledgements": {"role": "acknowledgments", "position": "post", "priority": 95},
    "acknowledgment": {"role": "acknowledgments", "position": "post", "priority": 95},
    "致谢": {"role": "acknowledgments", "position": "post", "priority": 95},
    "references": {"role": "references", "position": "post", "priority": 98},
    "bibliography": {"role": "references", "position": "post", "priority": 98},
    "参考文献": {"role": "references", "position": "post", "priority": 98},
    "appendix": {"role": "appendix", "position": "post", "priority": 99},
    "appendices": {"role": "appendix", "position": "post", "priority": 99},
    "附录": {"role": "appendix", "position": "post", "priority": 99},
}

# Pattern for standalone section header (keyword only or keyword + short modifier)
# 独立章节标题模式（仅关键词或关键词+短修饰语）
def _build_standalone_pattern():
    """Build regex pattern for standalone section keywords"""
    # Escape special regex characters in keywords and join with |
    # 转义关键词中的特殊正则字符并用|连接
    keywords = sorted(STANDALONE_SECTION_KEYWORDS.keys(), key=len, reverse=True)
    escaped_keywords = [re.escape(kw) for kw in keywords]
    pattern_str = r'^(?:\s*)(' + '|'.join(escaped_keywords) + r')(?:\s*[:：]?\s*)$'
    return re.compile(pattern_str, re.IGNORECASE)

STANDALONE_SECTION_PATTERN = _build_standalone_pattern()

# Block type constants
# 块类型常量
BLOCK_TYPE_MAIN_HEADER = "main_section_header"
BLOCK_TYPE_SUBSECTION_HEADER = "subsection_header"
BLOCK_TYPE_CONTENT = "content"
BLOCK_TYPE_CAPTION = "caption"
BLOCK_TYPE_METADATA = "metadata"

# Caption patterns (Table, Figure, etc.)
# 图表标题模式
CAPTION_PATTERN = re.compile(
    r'^(?:Table|Figure|Fig\.|Tab\.|Scheme|Algorithm|Listing)\s*\d*[.:\s]',
    re.IGNORECASE
)


def _is_standalone_section_header(text: str) -> Tuple[bool, str, str, Dict[str, Any]]:
    """
    Check if text is a standalone section header (keyword without numbering)
    检查文本是否为独立章节标题（无编号的关键词）

    Returns: (is_standalone, section_number, section_title, metadata)
        - section_number will be empty string for standalone headers
        - metadata contains role, position, priority info
    """
    text = text.strip()

    # Skip if too long (standalone headers are usually very short, 1-4 words)
    # 跳过过长的文本（独立标题通常非常短，1-4个词）
    word_count = len(text.split())
    if word_count > 6:
        return False, "", "", {}

    # Try exact match first (case-insensitive)
    # 首先尝试精确匹配（不区分大小写）
    text_lower = text.lower().strip().rstrip(':').rstrip('：').strip()

    if text_lower in STANDALONE_SECTION_KEYWORDS:
        kw_info = STANDALONE_SECTION_KEYWORDS[text_lower]
        return True, "", text, kw_info

    # Try pattern match for variations like "Abstract:" or "ABSTRACT"
    # 尝试模式匹配变体，如 "Abstract:" 或 "ABSTRACT"
    match = STANDALONE_SECTION_PATTERN.match(text)
    if match:
        matched_keyword = match.group(1).lower()
        if matched_keyword in STANDALONE_SECTION_KEYWORDS:
            kw_info = STANDALONE_SECTION_KEYWORDS[matched_keyword]
            # Use the original text as title (preserves case)
            # 使用原始文本作为标题（保留大小写）
            return True, "", text.strip().rstrip(':').rstrip('：').strip(), kw_info

    return False, "", "", {}


def _is_main_section_header(text: str, check_standalone: bool = True) -> Tuple[bool, str, str]:
    """
    Check if text is a MAIN section header (not subsection)
    检查文本是否为主章节标题（非子章节）

    Args:
        text: Text to check
        check_standalone: Whether to also check for standalone keyword headers

    Returns: (is_main_section, section_number, section_title)
    """
    text = text.strip()

    # Skip if too long (headers are usually short)
    # 跳过过长的文本（标题通常较短）
    if len(text.split()) > 15:
        return False, "", ""

    # Check for subsection pattern first (1.1, 2.1.1, etc.) - these are NOT main sections
    # 首先检查子章节模式（1.1, 2.1.1等）- 这些不是主章节
    if SUBSECTION_PATTERN.match(text):
        return False, "", ""

    # Check for main section pattern (1., 2., etc.)
    # 检查主章节模式（1., 2.等）
    match = MAIN_SECTION_PATTERN.match(text)
    if match:
        section_num = match.group(1)
        section_title = match.group(2).strip()
        # Validate that the title part looks like a title (starts with capital or contains known keywords)
        # 验证标题部分看起来像标题（以大写字母开头或包含已知关键词）
        title_lower = section_title.lower()
        known_keywords = [
            'introduction', 'background', 'related work', 'literature',
            'methodology', 'methods', 'method', 'approach',
            'experiment', 'results', 'findings', 'analysis',
            'discussion', 'conclusion', 'summary', 'future',
            'abstract', 'acknowledgment', 'reference', 'appendix'
        ]
        if section_title and (section_title[0].isupper() or any(kw in title_lower for kw in known_keywords)):
            return True, section_num, section_title

    # Check for Roman numeral pattern (I., II., etc.)
    # 检查罗马数字模式（I., II.等）
    match = ROMAN_MAIN_SECTION_PATTERN.match(text)
    if match:
        section_num = match.group(1)
        section_title = match.group(2).strip()
        if section_title and section_title[0].isupper():
            return True, section_num, section_title

    # Check for standalone keyword headers (Abstract, Conclusion, etc.)
    # 检查独立关键词标题（Abstract, Conclusion等）
    if check_standalone:
        is_standalone, _, standalone_title, _ = _is_standalone_section_header(text)
        if is_standalone:
            # Use empty string as section number for standalone headers
            # 独立标题使用空字符串作为章节编号
            return True, "", standalone_title

    return False, "", ""


def _is_subsection_header(text: str) -> Tuple[bool, str, str]:
    """
    Check if text is a SUBSECTION header (1.1, 2.1, etc.)
    检查文本是否为子章节标题（1.1, 2.1等）

    Returns: (is_subsection, section_number, section_title)
    """
    text = text.strip()

    # Skip if too long (headers are usually short)
    # 跳过过长的文本（标题通常较短）
    if len(text.split()) > 15:
        return False, "", ""

    # Check for subsection pattern (1.1, 2.1.1, etc.)
    # 检查子章节模式（1.1, 2.1.1等）
    match = SUBSECTION_PATTERN.match(text)
    if match:
        section_num = f"{match.group(1)}.{match.group(2)}"
        section_title = match.group(3).strip()
        if section_title and section_title[0].isupper():
            return True, section_num, section_title

    return False, "", ""


def _classify_block_type(text: str, check_standalone: bool = True) -> Tuple[str, Dict[str, Any]]:
    """
    Classify a text block into one of the block types
    将文本块分类为块类型之一

    Args:
        text: Text to classify
        check_standalone: Whether to check for standalone keyword headers

    Returns: (block_type, metadata)
        - block_type: BLOCK_TYPE_MAIN_HEADER, BLOCK_TYPE_SUBSECTION_HEADER, BLOCK_TYPE_CONTENT, etc.
        - metadata: dict with additional info like section_number, title, etc.
    """
    text = text.strip()
    word_count = len(text.split())

    # Check for numbered main section header first (1., 2., etc.)
    # 首先检查编号主章节标题（1., 2.等）
    is_main, section_num, section_title = _is_main_section_header(text, check_standalone=False)
    if is_main:
        return BLOCK_TYPE_MAIN_HEADER, {
            "section_number": section_num,
            "title": section_title,
            "full_title": f"{section_num}. {section_title}",
            "word_count": word_count,
            "is_standalone": False
        }

    # Check for subsection header
    # 检查子章节标题
    is_sub, sub_num, sub_title = _is_subsection_header(text)
    if is_sub:
        return BLOCK_TYPE_SUBSECTION_HEADER, {
            "section_number": sub_num,
            "title": sub_title,
            "full_title": f"{sub_num} {sub_title}",
            "word_count": word_count
        }

    # Check for standalone keyword headers (Abstract, Conclusion, etc.)
    # 检查独立关键词标题（Abstract, Conclusion等）
    if check_standalone:
        is_standalone, _, standalone_title, kw_metadata = _is_standalone_section_header(text)
        if is_standalone:
            return BLOCK_TYPE_MAIN_HEADER, {
                "section_number": "",
                "title": standalone_title,
                "full_title": standalone_title,
                "word_count": word_count,
                "is_standalone": True,
                "role": kw_metadata.get("role", "body"),
                "position": kw_metadata.get("position", "body"),
                "priority": kw_metadata.get("priority", 50)
            }

    # Check for caption (Table, Figure, etc.)
    # 检查图表标题
    if CAPTION_PATTERN.match(text):
        return BLOCK_TYPE_CAPTION, {
            "word_count": word_count
        }

    # Check for metadata (very short, might be author, keywords, etc.)
    # 检查元数据（非常短，可能是作者、关键词等）
    # But NOT if it looks like a standalone keyword that wasn't matched
    # 但如果它看起来像一个未匹配的独立关键词，则不是
    if word_count <= 3 and not any(c.isalpha() and c.islower() for c in text[:20] if c.isalpha()):
        # All uppercase or very short - likely metadata
        # 全大写或非常短 - 可能是元数据
        return BLOCK_TYPE_METADATA, {
            "word_count": word_count
        }

    # Default to content
    # 默认为内容
    return BLOCK_TYPE_CONTENT, {
        "word_count": word_count
    }


def _create_default_section(index: int) -> Dict[str, Any]:
    """
    Create a default body section when no section header is found
    当没有找到章节标题时创建默认的正文章节
    """
    return {
        "index": index,
        "title": "Main Content",
        "title_zh": "正文",
        "number": "",
        "role": "body",
        "blocks": [],
        "content_paragraphs": [],
        "content_word_count": 0,
        "total_word_count": 0,
        "subsections": [],
        "is_standalone": False,
        "priority": 50
    }


def _is_document_title(text: str, is_first_block: bool) -> bool:
    """
    Check if a block is likely a document title (not a section header)
    检查一个块是否可能是文档标题（不是章节标题）

    Document titles typically:
    - Are the first block in the document
    - Are not numbered (no "1.", "2.", etc.)
    - Are not known section keywords (Abstract, Introduction, etc.)
    - Are relatively short (1-3 lines, < 50 words)
    - Often contain colons, question marks, or specific patterns

    文档标题通常：
    - 是文档的第一个块
    - 没有编号（没有"1.", "2."等）
    - 不是已知的章节关键词（Abstract, Introduction等）
    - 相对较短（1-3行，<50词）
    - 通常包含冒号、问号或特定模式
    """
    if not is_first_block:
        return False

    text = text.strip()
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    if not lines:
        return False

    first_line = lines[0]
    word_count = len(text.split())

    # If it's a section header, it's not a document title
    # 如果是章节标题，则不是文档标题
    block_type, _ = _classify_block_type(first_line, check_standalone=True)
    if block_type == BLOCK_TYPE_MAIN_HEADER:
        return False

    # Document titles are typically 5-50 words
    # 文档标题通常是5-50词
    if word_count < 5 or word_count > 50:
        return False

    # Document titles often have title case or contain specific patterns
    # 文档标题通常有标题大小写或包含特定模式
    title_patterns = [
        r':',  # Colons are common in titles
        r'\?',  # Question marks
        r'A\s+(Novel|New|Comprehensive|Study|Survey|Review|Framework)',  # Common title patterns
        r'(Towards|Understanding|Learning|Exploring|Analyzing)',  # Common starting words
    ]

    for pattern in title_patterns:
        if re.search(pattern, first_line, re.IGNORECASE):
            return True

    # If it's a short block (1-2 lines) with title-like capitalization, likely a title
    # 如果是短块（1-2行）且有标题样式的大写，可能是标题
    if len(lines) <= 2 and first_line[0].isupper():
        # Check if most words start with capital letters (title case)
        # 检查大多数词是否以大写字母开头（标题大小写）
        words = first_line.split()
        if len(words) >= 3:
            capital_words = sum(1 for w in words if w[0].isupper())
            if capital_words / len(words) > 0.5:
                return True

    return False


def _extract_sections_with_headers(text: str) -> List[Dict[str, Any]]:
    """
    Extract sections from text with proper block classification.
    Supports both numbered headers (1., 2., etc.) and standalone keyword headers (Abstract, Conclusion).
    Handles mixed mode where some sections are numbered and others are standalone keywords.
    Skips document title (first block that is not a section header).

    从文本中提取章节，正确分类块。
    支持编号标题（1., 2.等）和独立关键词标题（Abstract, Conclusion等）。
    处理混合模式，其中部分章节有编号，部分章节是独立关键词。
    跳过文档标题（第一个不是章节标题的块）。

    Returns: List of section dictionaries with:
        - index, title, number, role
        - blocks: all blocks in this section with their types
        - content_paragraphs: only content blocks (for paragraph count)
        - content_word_count: words in content blocks only
        - total_word_count: words in all blocks (including headers)
        - subsections: list of subsection titles
        - is_standalone: whether this section uses standalone keyword header
    """
    # First, split by double newlines to get raw blocks
    # 首先，按双换行分割得到原始块
    raw_blocks = [p.strip() for p in text.split('\n\n') if p.strip()]

    # Also try single newline split if we got too few blocks
    # 如果块太少，也尝试单换行分割
    if len(raw_blocks) <= 1:
        # Try splitting by single newlines for documents that use single newlines
        # 尝试按单换行分割，用于使用单换行的文档
        single_line_blocks = [p.strip() for p in text.split('\n') if p.strip()]
        if len(single_line_blocks) > len(raw_blocks):
            raw_blocks = single_line_blocks

    # Skip document title if present (first block that is not a section header)
    # 如果存在文档标题则跳过（第一个不是章节标题的块）
    document_title = None
    if raw_blocks and _is_document_title(raw_blocks[0], is_first_block=True):
        document_title = raw_blocks[0]
        raw_blocks = raw_blocks[1:]
        logger.info(f"Detected and skipped document title: {document_title[:80]}...")

    sections = []
    current_section = None  # Start with no section, wait for first header

    for idx, block in enumerate(raw_blocks):
        # Split block into lines to check for headers on first line
        # 将块分割为行以检查第一行的标题
        lines = [l.strip() for l in block.split('\n') if l.strip()]

        if not lines:
            continue

        # Check the first line of this block
        # 检查此块的第一行
        first_line = lines[0]
        block_type, metadata = _classify_block_type(first_line)

        if block_type == BLOCK_TYPE_MAIN_HEADER:
            # Found a main section header - save current section and start new one
            # 找到主章节标题 - 保存当前章节并开始新章节
            if current_section and (current_section["blocks"] or current_section["content_paragraphs"]):
                sections.append(current_section)

            # Determine section role - use metadata if available (for standalone headers)
            # 确定章节角色 - 如果可用则使用元数据（用于独立标题）
            is_standalone = metadata.get("is_standalone", False)
            if is_standalone and "role" in metadata:
                # Use role from standalone keyword metadata
                # 使用独立关键词元数据中的角色
                role = metadata["role"]
            else:
                # Determine role from title text
                # 从标题文本确定角色
                role = _get_section_role_from_title(metadata["title"])

            # Start new section
            # 开始新章节
            current_section = {
                "index": len(sections),
                "title": metadata["full_title"],
                "title_zh": metadata["title"],
                "number": metadata["section_number"],
                "role": role,
                "blocks": [],
                "content_paragraphs": [],
                "content_word_count": 0,
                "total_word_count": 0,
                "subsections": [],
                "is_standalone": is_standalone,
                "priority": metadata.get("priority", 50)
            }

            # Add the header itself as a block (counts towards total_word_count)
            # 将标题本身作为块添加（计入total_word_count）
            current_section["blocks"].append({
                "text": first_line,
                "type": BLOCK_TYPE_MAIN_HEADER,
                "word_count": metadata["word_count"]
            })
            current_section["total_word_count"] += metadata["word_count"]

            # If there's content after the header line, process it separately
            # 如果标题行后有内容，单独处理
            if len(lines) > 1:
                remaining_content = '\n'.join(lines[1:])
                # Don't check for standalone headers in remaining content to avoid false positives
                # 在剩余内容中不检查独立标题以避免误报
                remaining_type, remaining_meta = _classify_block_type(remaining_content, check_standalone=False)
                current_section["blocks"].append({
                    "text": remaining_content,
                    "type": remaining_type,
                    "word_count": remaining_meta["word_count"]
                })
                current_section["total_word_count"] += remaining_meta["word_count"]

                if remaining_type == BLOCK_TYPE_CONTENT:
                    current_section["content_paragraphs"].append(remaining_content)
                    current_section["content_word_count"] += remaining_meta["word_count"]
                elif remaining_type == BLOCK_TYPE_SUBSECTION_HEADER:
                    current_section["subsections"].append(remaining_meta.get("full_title", remaining_content))

        elif block_type == BLOCK_TYPE_SUBSECTION_HEADER:
            # Subsection header - add to current section but NOT as content paragraph
            # 子章节标题 - 添加到当前章节但不作为内容段落
            # If no current section exists, create a default body section
            # 如果没有当前章节，创建一个默认的正文章节
            if current_section is None:
                current_section = _create_default_section(len(sections))

            current_section["blocks"].append({
                "text": first_line,
                "type": BLOCK_TYPE_SUBSECTION_HEADER,
                "word_count": metadata["word_count"]
            })
            current_section["total_word_count"] += metadata["word_count"]
            current_section["subsections"].append(metadata["full_title"])

            # If there's content after the subsection header, process it
            # 如果子章节标题后有内容，处理它
            if len(lines) > 1:
                remaining_content = '\n'.join(lines[1:])
                # Don't check for standalone headers in remaining content
                # 在剩余内容中不检查独立标题
                remaining_type, remaining_meta = _classify_block_type(remaining_content, check_standalone=False)
                current_section["blocks"].append({
                    "text": remaining_content,
                    "type": remaining_type,
                    "word_count": remaining_meta["word_count"]
                })
                current_section["total_word_count"] += remaining_meta["word_count"]

                if remaining_type == BLOCK_TYPE_CONTENT:
                    current_section["content_paragraphs"].append(remaining_content)
                    current_section["content_word_count"] += remaining_meta["word_count"]

        else:
            # Regular content or other block types
            # 常规内容或其他块类型
            # If no current section exists, create a default body section
            # 如果没有当前章节，创建一个默认的正文章节
            if current_section is None:
                current_section = _create_default_section(len(sections))

            current_section["blocks"].append({
                "text": block,
                "type": block_type,
                "word_count": metadata["word_count"]
            })
            current_section["total_word_count"] += metadata["word_count"]

            # Only add to content_paragraphs if it's actual content
            # 只有实际内容才添加到content_paragraphs
            if block_type == BLOCK_TYPE_CONTENT:
                current_section["content_paragraphs"].append(block)
                current_section["content_word_count"] += metadata["word_count"]

    # Don't forget the last section
    # 不要忘记最后一个章节
    if current_section and (current_section["blocks"] or current_section["content_paragraphs"]):
        sections.append(current_section)

    # Log detected sections for debugging
    # 记录检测到的章节用于调试
    logger.info(f"Extracted {len(sections)} sections:")
    for sec in sections:
        standalone_str = " (standalone)" if sec.get("is_standalone") else ""
        logger.info(f"  [{sec['index']}] {sec['role']}{standalone_str}: {sec['title']}")

    return sections


def _get_section_role_from_title(title: str) -> str:
    """
    Determine section role from its title
    从标题确定章节角色
    """
    title_lower = title.lower().strip()

    # Known section title mappings
    # 已知章节标题映射
    role_keywords = {
        "introduction": ["introduction", "intro"],
        "background": ["background", "overview", "preliminary", "preliminaries"],
        "literature_review": ["related work", "literature review", "prior work", "related studies"],
        "methodology": ["methodology", "methods", "method", "approach", "framework", "model", "proposed"],
        "results": ["results", "findings", "experiment", "experiments", "evaluation", "empirical"],
        "discussion": ["discussion", "analysis", "implication", "implications"],
        "conclusion": ["conclusion", "conclusions", "summary", "future work", "future"],
        "abstract": ["abstract"],
        "references": ["reference", "references", "bibliography"],
        "appendix": ["appendix", "appendices", "supplementary"]
    }

    for role, keywords in role_keywords.items():
        for kw in keywords:
            if kw in title_lower:
                return role

    return "body"


def _split_text_to_paragraphs(text: str) -> list:
    """
    Split text into paragraphs, filtering out non-paragraph content
    将文本分割为段落，过滤掉非段落内容（标题、表头、keywords等）

    Uses SentenceSegmenter to detect and filter:
    - Section headers (Abstract, Introduction, etc.)
    - Table/Figure captions
    - Keywords lines
    - Metadata (author info, affiliations)
    - Short fragments
    """
    # First split into raw paragraphs
    # 首先分割为原始段落
    raw_paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(raw_paragraphs) <= 1:
        raw_paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    # Filter paragraphs using segmenter
    # 使用分句器过滤段落
    filtered_paragraphs = []
    for para in raw_paragraphs:
        # Segment the paragraph to detect content types
        # 分割段落以检测内容类型
        sentences = _segmenter.segment(para)

        # Check if this paragraph should be processed
        # 检查这个段落是否应该被处理
        if not sentences:
            continue

        # If the first sentence is not processable (header, keywords, etc.), skip the paragraph
        # 如果第一个句子不可处理（标题、关键词等），跳过该段落
        first_sent = sentences[0]
        if not first_sent.should_process:
            continue

        # Count processable sentences
        # 统计可处理的句子数量
        processable = [s for s in sentences if s.should_process]
        if not processable:
            continue

        # Reconstruct paragraph from processable sentences only
        # 仅从可处理的句子重建段落
        if len(processable) == len(sentences):
            # All sentences are processable, use original
            # 所有句子都可处理，使用原文
            filtered_paragraphs.append(para)
        else:
            # Some sentences filtered, rebuild
            # 部分句子被过滤，重建
            filtered_text = ' '.join(s.text for s in processable)
            if filtered_text.strip():
                filtered_paragraphs.append(filtered_text)

    return filtered_paragraphs


def _get_paragraphs(request: SectionAnalysisRequest) -> list:
    """Extract paragraphs from request (either from text or paragraphs field)"""
    if request.paragraphs:
        return request.paragraphs
    elif request.text:
        return _split_text_to_paragraphs(request.text)
    else:
        return []


def _convert_issue(issue) -> DetectionIssue:
    """Convert internal issue to API schema"""
    return DetectionIssue(
        type=issue.type,
        description=issue.description,
        description_zh=issue.description_zh,
        severity=IssueSeverity(issue.severity.value),
        layer=LayerLevel.SECTION,
        position=issue.position,
        suggestion=issue.suggestion,
        suggestion_zh=issue.suggestion_zh,
        details=issue.details,
    )


@router.post("/logic", response_model=SectionAnalysisResponse)
async def analyze_section_logic(request: SectionAnalysisRequest):
    """
    Step 2.1: Section Logic Flow
    步骤 2.1：章节逻辑?

    Analyzes logical relationships between sections:
    - Check section sequence rationality
    - Detect structural anomalies
    - Compare against expected academic structure
    """
    start_time = time.time()

    try:
        analyzer = SectionAnalyzer()
        paragraphs = _get_paragraphs(request)

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=paragraphs,
            document_structure=request.document_context or {},
        )

        # Run analysis
        result = await analyzer.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract logic-specific details
        logic_details = result.details.get("logic_flow", {})
        sections = result.details.get("sections", [])

        # Transform section details for frontend
        section_details = _transform_section_details(sections)

        return SectionAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if i.type.startswith(("predictable", "missing"))],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=logic_details,
            processing_time_ms=processing_time_ms,
            section_details=section_details,
            section_count=len(sections),
            logic_flow_score=0,
            transition_quality=0,
            logic_flow=logic_details,
            transitions=[],
            length_distribution=None,
        )

    except Exception as e:
        logger.error(f"Section logic analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transition", response_model=SectionAnalysisResponse)
async def analyze_section_transitions(request: SectionAnalysisRequest):
    """
    Step 2.2: Section Transitions
    步骤 2.2：章节衔?

    Analyzes transition quality between sections:
    - Detect abrupt topic changes
    - Evaluate cross-section coherence
    - Check for AI-like explicit transitions
    """
    start_time = time.time()

    try:
        analyzer = SectionAnalyzer()
        paragraphs = _get_paragraphs(request)

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=paragraphs,
            document_structure=request.document_context or {},
        )

        # Run analysis
        result = await analyzer.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract transition-specific details
        transitions = result.details.get("transitions", {})
        sections = result.details.get("sections", [])

        # Transform section details for frontend
        section_details = _transform_section_details(sections)

        return SectionAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "transition" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=transitions,
            processing_time_ms=processing_time_ms,
            section_details=section_details,
            section_count=len(sections),
            logic_flow_score=0,
            transition_quality=transitions.get("explicit_transition_count", 0),
            logic_flow=None,
            transitions=result.updated_context.section_transitions or [],
            length_distribution=None,
        )

    except Exception as e:
        logger.error(f"Section transition analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/length", response_model=SectionAnalysisResponse)
async def analyze_section_length(request: SectionAnalysisRequest):
    """
    Step 2.3: Section Length Distribution
    步骤 2.3：章节长度分?

    Analyzes length balance across sections:
    - Detect abnormal length patterns
    - Calculate length CV (coefficient of variation)
    - Identify very short or long sections
    """
    start_time = time.time()

    try:
        analyzer = SectionAnalyzer()
        paragraphs = _get_paragraphs(request)

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=paragraphs,
            document_structure=request.document_context or {},
        )

        # Run analysis
        result = await analyzer.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract length-specific details
        length_details = result.details.get("length_distribution", {})
        sections = result.details.get("sections", [])

        # Transform section details for frontend
        section_details = _transform_section_details(sections)

        return SectionAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "length" in i.type or "short" in i.type or "long" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=length_details,
            processing_time_ms=processing_time_ms,
            section_details=section_details,
            section_count=len(sections),
            logic_flow_score=0,
            transition_quality=0,
            logic_flow=None,
            transitions=[],
            length_distribution=_transform_length_distribution(length_details),
        )

    except Exception as e:
        logger.error(f"Section length analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _transform_length_distribution(length_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform length distribution data to frontend-expected format.
    将长度分布数据转换为前端期望的格式?

    Backend returns: mean_length, stdev_length, length_cv
    Frontend expects: mean, stdDev, cv, isUniform
    """
    if not length_details:
        return None

    cv = length_details.get("length_cv", 0)
    return {
        "mean": length_details.get("mean_length", 0),
        "stdDev": length_details.get("stdev_length", 0),
        "cv": cv,
        "isUniform": cv < 0.3 if cv else False,  # CV < 0.3 is considered uniform (AI-like)
    }


def _transform_section_details(sections: list) -> list:
    """
    Transform section details to include expected frontend fields.
    转换章节详情以包含前端期望的字段?
    """
    transformed = []
    for idx, section in enumerate(sections):
        transformed.append({
            "index": idx,
            "role": section.get("role", "unknown"),
            "wordCount": section.get("word_count", 0),
            "transitionScore": section.get("transition_score", 0),
            "issues": section.get("issues", []),
        })
    return transformed


@router.post("/analyze", response_model=SectionAnalysisResponse)
async def analyze_section(request: SectionAnalysisRequest):
    """
    Combined Section Analysis (Layer 4)
    综合章节分析（第4层）

    Runs all section-level analysis steps:
    - Step 2.1: Section Logic Flow
    - Step 2.2: Section Transitions
    - Step 2.3: Section Length Distribution

    Returns complete section-level analysis results with context
    for passing to lower layers.
    """
    start_time = time.time()

    try:
        analyzer = SectionAnalyzer()
        paragraphs = _get_paragraphs(request)

        # Create context with paragraphs and optional document context
        context = LayerContext(
            paragraphs=paragraphs,
            document_structure=request.document_context or {},
        )

        # Run full analysis
        result = await analyzer.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract all details
        sections = result.details.get("sections", [])
        logic_flow = result.details.get("logic_flow", {})
        transitions_detail = result.details.get("transitions", {})
        length_distribution = result.details.get("length_distribution", {})

        # Transform section details for frontend
        section_details = _transform_section_details(sections)

        # Debug log to check section_details
        logger.info(f"Section analysis - sections count: {len(sections)}, section_details: {section_details[:2] if section_details else 'empty'}")

        # Calculate scores for frontend display
        logic_flow_score = int(logic_flow.get("order_match_score", 0) * 100) if logic_flow else 0
        transition_quality = transitions_detail.get("explicit_transition_count", 0)

        return SectionAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=result.details,
            processing_time_ms=processing_time_ms,
            section_details=section_details,
            section_count=len(sections),
            logic_flow_score=logic_flow_score,
            transition_quality=transition_quality,
            logic_flow=logic_flow,
            transitions=result.updated_context.section_transitions or [],
            length_distribution=_transform_length_distribution(length_distribution),
        )

    except Exception as e:
        logger.error(f"Section analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context")
async def get_section_context(request: SectionAnalysisRequest):
    """
    Get section context for passing to lower layers
    获取章节上下文以传递给下层

    Returns the updated LayerContext that can be used
    to initialize lower layer analysis.
    """
    try:
        analyzer = SectionAnalyzer()
        paragraphs = _get_paragraphs(request)

        # Create context with paragraphs
        context = LayerContext(
            paragraphs=paragraphs,
            document_structure=request.document_context or {},
        )

        # Run analysis
        result = await analyzer.analyze(context)

        # Return the updated context as dict
        return {
            "sections": result.updated_context.sections,
            "section_boundaries": result.updated_context.section_boundaries,
            "section_transitions": result.updated_context.section_transitions,
        }

    except Exception as e:
        logger.error(f"Section context extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Layer 4 Sub-step API Routes (Step 2.0 - 2.5)
# 第4层子步骤API路由（步骤 2.0 - 2.5）
# =============================================================================

# Section role patterns for detection
# 章节角色检测模式
SECTION_ROLE_PATTERNS = {
    "introduction": [
        r"\bintroduction\b", r"\bbackground\b", r"\boverview\b",
        r"\bthis (paper|study|research|work)\b", r"\bwe (present|propose|introduce)\b"
    ],
    "literature_review": [
        r"\bliterature\s+review\b", r"\brelated\s+work\b", r"\bprior\s+(work|research)\b",
        r"\bprevious\s+studies\b", r"\bstate\s+of\s+the\s+art\b"
    ],
    "methodology": [
        r"\bmethodology\b", r"\bmethods?\b", r"\bapproach\b", r"\bprocedure\b",
        r"\bexperimental\s+design\b", r"\bdata\s+collection\b"
    ],
    "results": [
        r"\bresults?\b", r"\bfindings?\b", r"\bobservation\b",
        r"\b(we|our)\s+(found|observed|noted)\b", r"\bthe\s+data\s+show\b"
    ],
    "discussion": [
        r"\bdiscussion\b", r"\bimplications?\b", r"\binterpreting\b",
        r"\bthese\s+(results|findings)\s+(suggest|indicate|demonstrate)\b"
    ],
    "conclusion": [
        r"\bconclusion\b", r"\bsummary\b", r"\bin\s+conclusion\b",
        r"\bfuture\s+(work|research|directions?)\b", r"\blimitations?\b"
    ],
}

# Paragraph function patterns
# 段落功能模式
PARAGRAPH_FUNCTION_PATTERNS = {
    "topic_sentence": [
        r"^this\s+(section|paper|study)\s+", r"^in\s+this\s+(section|paper)\s+",
        r"^the\s+(main|primary|key)\s+", r"^we\s+(argue|propose|suggest|examine)\s+"
    ],
    "evidence": [
        r"\baccording\s+to\b", r"\bresearch\s+shows\b", r"\bstudies\s+(indicate|show|demonstrate)\b",
        r"\bdata\s+from\b", r"\bthe\s+results\s+(show|indicate)\b", r"\d+%", r"\bp\s*[<>=]"
    ],
    "analysis": [
        r"\bthis\s+(suggests|indicates|demonstrates)\b", r"\bcan\s+be\s+(explained|understood)\b",
        r"\bthe\s+reason\s+for\b", r"\bone\s+possible\s+explanation\b"
    ],
    "example": [
        r"\bfor\s+(example|instance)\b", r"\bsuch\s+as\b", r"\bto\s+illustrate\b",
        r"\bconsider\s+the\s+case\b", r"\ba\s+good\s+example\b"
    ],
    "transition": [
        r"^(however|moreover|furthermore|additionally|in\s+addition)\b",
        r"^on\s+the\s+other\s+hand\b", r"^in\s+contrast\b"
    ],
    "mini_conclusion": [
        r"\bin\s+summary\b", r"\bto\s+summarize\b", r"\boverall\b",
        r"\btherefore\b", r"\bthus\b", r"\bconsequently\b"
    ],
}

# Transition word patterns by strength
# 按强度分类的过渡词模式
TRANSITION_WORD_PATTERNS = {
    "strong": [
        r"\bhaving\s+established\b", r"\bbuilding\s+on\b", r"\bgiven\s+the\b",
        r"\bwith\s+this\s+(understanding|foundation)\b", r"\bbased\s+on\b",
        r"\bas\s+demonstrated\s+above\b", r"\bas\s+mentioned\s+earlier\b"
    ],
    "moderate": [
        r"^\s*(now|next)\b", r"^turning\s+to\b", r"^moving\s+to\b",
        r"^(first|second|third|finally)\b", r"^in\s+the\s+following\s+section\b"
    ],
    "weak": [
        r"^(however|moreover|furthermore|additionally)\b", r"^in\s+addition\b",
        r"^consequently\b", r"^therefore\b"
    ],
}

# Argument markers
# 论点标记
ARGUMENT_MARKERS = [
    r"\bwe\s+argue\s+that\b", r"\bour\s+claim\s+is\b", r"\bthe\s+(main|key)\s+point\b",
    r"\bit\s+is\s+important\s+to\s+note\b", r"\bsignificantly\b", r"\bcrucially\b",
    r"\bthe\s+evidence\s+suggests\b", r"\bthis\s+demonstrates\b"
]


def _get_paragraphs_from_request(request) -> List[str]:
    """
    Extract paragraphs from various request types
    从各种请求类型中提取段落
    """
    if hasattr(request, 'paragraphs') and request.paragraphs:
        return request.paragraphs
    elif hasattr(request, 'text') and request.text:
        return _split_text_to_paragraphs(request.text)
    else:
        return []


def _detect_paragraph_role(para: str) -> Tuple[str, float]:
    """
    Detect the role of a paragraph based on content patterns
    根据内容模式检测段落的角色

    Returns: (role, confidence)
    """
    para_lower = para.lower()
    matches = {}

    for role, patterns in SECTION_ROLE_PATTERNS.items():
        match_count = 0
        for pattern in patterns:
            if re.search(pattern, para_lower):
                match_count += 1
        if match_count > 0:
            matches[role] = match_count

    if not matches:
        return ("body", 0.5)

    best_role = max(matches, key=matches.get)
    confidence = min(1.0, matches[best_role] / 3)  # Scale to 0-1

    return (best_role, confidence)


def _detect_paragraph_function(para: str, position: str = "middle") -> Tuple[str, float]:
    """
    Detect the function of a paragraph within a section
    检测段落在章节内的功能

    Args:
        para: Paragraph text
        position: "first", "last", or "middle"

    Returns: (function, confidence)
    """
    para_lower = para.lower()

    # Check for specific function patterns
    for func, patterns in PARAGRAPH_FUNCTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, para_lower):
                return (func, 0.8)

    # Position-based heuristics
    if position == "first":
        return ("topic_sentence", 0.6)
    elif position == "last":
        return ("mini_conclusion", 0.5)
    else:
        # Check for evidence indicators
        if re.search(r'\d+', para):  # Contains numbers
            return ("evidence", 0.5)
        return ("elaboration", 0.4)


def _calculate_sequence_similarity(seq1: List[str], seq2: List[str]) -> float:
    """
    Calculate similarity between two function sequences using edit distance
    使用编辑距离计算两个功能序列之间的相似性

    Returns: Similarity percentage (0-100)
    """
    if not seq1 or not seq2:
        return 0.0

    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i-1] == seq2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    edit_distance = dp[m][n]
    max_len = max(m, n)
    similarity = (1 - edit_distance / max_len) * 100 if max_len > 0 else 0

    return round(similarity, 1)


def _extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    Extract important keywords from text
    从文本中提取重要关键词
    """
    # Remove common stopwords
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "and", "but", "or",
        "nor", "for", "yet", "so", "as", "if", "of", "at", "by", "from", "up",
        "down", "in", "out", "on", "off", "over", "under", "to", "into", "onto",
        "this", "that", "these", "those", "it", "its", "their", "our", "we",
        "they", "them", "which", "what", "who", "whom", "with", "about"
    }

    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    word_counts = Counter(w for w in words if w not in stopwords)

    return [w for w, _ in word_counts.most_common(top_n)]


# -----------------------------------------------------------------------------
# Step 2.0: Section Identification / 步骤 2.0：章节识别
# -----------------------------------------------------------------------------

@router.post("/step2-0/identify", response_model=SectionIdentificationResponse)
async def identify_sections(request: SectionIdentificationRequest):
    """
    Step 2.0: Section Identification (Rule-based)
    步骤 2.0：章节识别与角色标注（基于规则）

    Detects section boundaries using:
    1. Numbered headers (1., 2., 3., I., II., etc.)
    2. Standalone keyword headers (Abstract, Conclusion, References, etc.)

    使用以下方式检测章节边界：
    1. 编号标题（1., 2., 3., I., II.等）
    2. 独立关键词标题（Abstract, Conclusion, References等）
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return SectionIdentificationResponse(
                section_count=0,
                sections=[],
                total_paragraphs=0,
                total_words=0,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # STEP 1: Extract sections using rule-based detection
        # 步骤1：使用规则检测提取章节
        logger.info(f"Extracting sections from document ({len(document_text)} chars)")

        extracted_sections = _extract_sections_with_headers(document_text)

        logger.info(f"Found {len(extracted_sections)} sections")
        for sec in extracted_sections:
            content_para_count = len(sec.get("content_paragraphs", []))
            content_words = sec.get("content_word_count", 0)
            total_words_sec = sec.get("total_word_count", 0)
            subsec_count = len(sec.get("subsections", []))
            logger.info(f"  Section {sec['index']}: {sec['title']} ({sec['role']}, "
                       f"content_paras={content_para_count}, content_words={content_words}, "
                       f"total_words={total_words_sec}, subsections={subsec_count})")

        # STEP 2: Convert to response format
        # 步骤2：转换为响应格式
        sections: List[SectionInfo] = []
        role_distribution: Dict[str, int] = {}
        total_paragraphs = 0  # Only content paragraphs (not headers)
        total_words = 0  # Total words including headers

        # Track paragraph indices across sections
        # 跨章节跟踪段落索引
        current_para_idx = 0

        for sec in extracted_sections:
            # Use content_paragraphs for paragraph count (excludes headers)
            # 使用content_paragraphs计算段落数（不包括标题）
            content_para_count = len(sec.get("content_paragraphs", []))
            content_word_count = sec.get("content_word_count", 0)
            total_word_count = sec.get("total_word_count", 0)

            # Calculate char count from content paragraphs only
            # 仅从内容段落计算字符数
            char_count = sum(len(p) for p in sec.get("content_paragraphs", []))

            sections.append(SectionInfo(
                index=sec["index"],
                role=sec["role"],
                role_confidence=0.9 if sec.get("number") else 0.7,  # Higher confidence if numbered
                title=sec.get("title", ""),
                start_paragraph_idx=current_para_idx,
                end_paragraph_idx=current_para_idx + content_para_count - 1 if content_para_count > 0 else current_para_idx,
                paragraph_count=content_para_count,  # Only content paragraphs
                word_count=total_word_count,  # Total words including headers
                char_count=char_count,
                preview=sec.get("title", "")
            ))

            role_distribution[sec["role"]] = role_distribution.get(sec["role"], 0) + 1
            total_paragraphs += content_para_count  # Only content paragraphs
            total_words += total_word_count  # Total words including headers
            current_para_idx += content_para_count

        # If no sections found, create a single body section
        # 如果没有找到章节，创建一个单一的正文章节
        if not sections:
            paragraphs = _get_paragraphs_from_request(request)
            total_words = sum(len(p.split()) for p in paragraphs)
            total_paragraphs = len(paragraphs)

            sections.append(SectionInfo(
                index=0,
                role="body",
                role_confidence=0.5,
                title="Main Content",
                start_paragraph_idx=0,
                end_paragraph_idx=len(paragraphs) - 1 if paragraphs else 0,
                paragraph_count=len(paragraphs),
                word_count=total_words,
                char_count=sum(len(p) for p in paragraphs),
                preview=paragraphs[0][:150] if paragraphs else ""
            ))
            role_distribution["body"] = 1

        processing_time_ms = int((time.time() - start_time) * 1000)

        # STEP 3: Generate issues based on rule-based analysis
        # 步骤3：基于规则分析生成问题
        issues = []

        # Check for missing standard sections
        # 检查缺失的标准章节
        expected_sections = {"introduction", "methodology", "results", "conclusion"}
        found_roles = set(role_distribution.keys())
        missing_sections = expected_sections - found_roles

        if missing_sections:
            missing_list = ", ".join(missing_sections)
            issues.append(DetectionIssue(
                type="missing_section",
                description=f"Document may be missing standard sections: {missing_list}",
                description_zh=f"文档可能缺少标准章节：{missing_list}",
                severity="medium",
                layer="section",
                location=None,
                fix_suggestions=[f"Consider adding a {s} section" for s in missing_sections],
                fix_suggestions_zh=[f"考虑添加{s}章节" for s in missing_sections]
            ))

        # Check for section length imbalance
        # 检查章节长度不平衡
        if len(sections) >= 2:
            word_counts = [s.word_count for s in sections if s.word_count > 0]
            if word_counts:
                avg_words = sum(word_counts) / len(word_counts)
                for sec in sections:
                    if sec.word_count > 0:
                        ratio = sec.word_count / avg_words if avg_words > 0 else 0
                        if ratio > 3:
                            issues.append(DetectionIssue(
                                type="section_too_long",
                                description=f"Section '{sec.preview}' is significantly longer than average",
                                description_zh=f"章节'{sec.preview}'明显长于平均水平",
                                severity="low",
                                layer="section",
                                location=f"Section {sec.index}",
                                fix_suggestions=["Consider splitting into smaller sections"],
                                fix_suggestions_zh=["考虑拆分为更小的章节"]
                            ))
                        elif ratio < 0.2 and sec.word_count < 50:
                            issues.append(DetectionIssue(
                                type="section_too_short",
                                description=f"Section '{sec.preview}' appears underdeveloped ({sec.word_count} words)",
                                description_zh=f"章节'{sec.preview}'内容不足（{sec.word_count}词）",
                                severity="low",
                                layer="section",
                                location=f"Section {sec.index}",
                                fix_suggestions=["Consider expanding this section or merging with adjacent section"],
                                fix_suggestions_zh=["考虑扩展此章节或与相邻章节合并"]
                            ))

        return SectionIdentificationResponse(
            section_count=len(sections),
            sections=sections,
            total_paragraphs=total_paragraphs,
            total_words=total_words,
            role_distribution=role_distribution,
            issues=issues,
            recommendations=[],
            recommendations_zh=[],
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Section identification failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Step 2.1: Section Order & Structure / 步骤 2.1：章节顺序与结构
# -----------------------------------------------------------------------------

@router.post("/step2-1/order", response_model=SectionOrderResponse)
async def analyze_section_order(request: SectionOrderRequest):
    """
    Step 2.1: Section Order & Structure Analysis (LLM-based)
    步骤 2.1：章节顺序与结构分析（基于LLM）

    Analyzes section order, detects missing sections, and evaluates function purity.
    分析章节顺序，检测缺失章节，评估功能纯度。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return SectionOrderResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                order_analysis=SectionOrderAnalysis(),
                issues=[],
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Call LLM handler for analysis
        # 调用LLM handler进行分析
        logger.info("Calling Step2_1Handler for LLM-based section order analysis")
        result = await step2_1_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step2-1",
            use_cache=True
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "section_order_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.SECTION,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SectionOrderResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            order_analysis=SectionOrderAnalysis(
                detected_order=result.get("current_order", []),
                expected_order=result.get("expected_order", []),
                order_match_score=result.get("order_match_score", 0) / 100.0 if result.get("order_match_score", 0) > 1 else result.get("order_match_score", 0),
                is_predictable=result.get("order_match_score", 0) >= 80,
                missing_sections=result.get("missing_sections", []),
                unexpected_sections=[],
                fusion_score=result.get("function_fusion_score", 0) / 100.0 if result.get("function_fusion_score", 0) > 1 else result.get("function_fusion_score", 0),
                multi_function_sections=[]
            ),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Section order analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Step 2.2: Section Length Distribution / 步骤 2.2：章节长度分布
# -----------------------------------------------------------------------------

# Expected weight for key sections
# 关键章节的预期权重
EXPECTED_SECTION_WEIGHTS = {
    "introduction": 0.15,
    "literature_review": 0.15,
    "methodology": 0.25,
    "results": 0.20,
    "discussion": 0.15,
    "conclusion": 0.10,
}


@router.post("/step2-2/length", response_model=SectionLengthResponse)
async def analyze_section_length(request: SectionLengthRequest):
    """
    Step 2.2: Section Length Distribution Analysis (Rule-based + LLM)
    步骤 2.2：章节长度分布分析（规则分析 + LLM）

    Uses rule-based text parsing for section detection, then passes to LLM for pattern analysis.
    使用规则分析检测章节，然后传递给LLM进行模式分析。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return SectionLengthResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # STEP 1: Call handler with two-stage analysis (LLM structure + Rule statistics)
        # 步骤1：调用handler进行两阶段分析（LLM结构 + 规则统计）
        logger.info("Calling Step2_2Handler for two-stage section length analysis")
        result = await step2_2_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step2-2",
            use_cache=True
        )

        # Get sections from handler result (two-stage: LLM structure + Rule statistics)
        # 从handler结果获取章节（两阶段：LLM结构 + 规则统计）
        sections_from_handler = result.get("detected_sections", [])
        logger.info(f"Step 2.2: Two-stage detected {len(sections_from_handler)} sections: {[s.get('role') for s in sections_from_handler]}")

        # Calculate statistics from detected sections
        # 从检测到的章节计算统计数据
        word_counts = [s.get("word_count", 0) for s in sections_from_handler if s.get("word_count", 0) > 0]
        total_words = sum(word_counts) if word_counts else 0

        if len(word_counts) >= 2:
            mean_length = statistics.mean(word_counts)
            stdev_length = statistics.stdev(word_counts)
            length_cv = round(stdev_length / mean_length, 3) if mean_length > 0 else 0
        else:
            mean_length = word_counts[0] if word_counts else 0
            stdev_length = 0
            length_cv = 0

        # Identify extreme sections (>1.5 stdev from mean)
        # 识别极端章节（与平均值相差超过1.5个标准差）
        extreme_short = []
        extreme_long = []
        if stdev_length > 0:
            for i, sec in enumerate(sections_from_handler):
                wc = sec.get("word_count", 0)
                if wc < mean_length - 1.5 * stdev_length:
                    extreme_short.append({"index": i, "word_count": wc})
                elif wc > mean_length + 1.5 * stdev_length:
                    extreme_long.append({"index": i, "word_count": wc})

        # STEP 2: Build section_infos from handler's detected sections (two-stage analysis)
        # 步骤2：从handler检测到的章节构建section_infos（两阶段分析）
        section_infos: List[SectionLengthInfo] = []
        for i, sec_data in enumerate(sections_from_handler):
            word_count = sec_data.get("word_count", 0)
            section_infos.append(SectionLengthInfo(
                index=i,
                role=sec_data.get("role", "body"),
                title=sec_data.get("title"),  # Actual section title from document / 文档中的实际章节标题
                word_count=word_count,
                paragraph_count=sec_data.get("paragraph_count", 0),
                deviation_from_mean=round((word_count - mean_length) / mean_length, 2) if mean_length > 0 else 0,
                is_extreme=abs(word_count - mean_length) > 1.5 * stdev_length if stdev_length > 0 else False,
                expected_weight=EXPECTED_SECTION_WEIGHTS.get(sec_data.get("role", "body"), 0.15),
                actual_weight=round(word_count / total_words, 3) if total_words > 0 else 0,
                weight_deviation=0.0
            ))

        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "section_length_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.SECTION,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        # STEP 4: Return two-stage analysis statistics and sections
        # 步骤4：返回两阶段分析的统计数据和章节
        return SectionLengthResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            section_count=len(section_infos),
            total_words=total_words,
            mean_length=round(mean_length, 1),
            stdev_length=round(stdev_length, 1),
            length_cv=round(length_cv, 3),
            is_uniform=length_cv < 0.3,
            sections=section_infos,  # Use two-stage sections (LLM structure + Rule stats)
            extremely_short=[es["index"] for es in extreme_short],
            extremely_long=[el["index"] for el in extreme_long],
            key_section_weight_score=50.0,
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Section length analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Step 2.3: Internal Structure Similarity (NEW) / 步骤 2.3：章节内部结构相似性
# -----------------------------------------------------------------------------

@router.post("/step2-3/similarity", response_model=InternalStructureSimilarityResponse)
async def analyze_internal_structure_similarity(request: InternalStructureSimilarityRequest):
    """
    Step 2.3: Internal Structure Similarity Analysis (LLM-based)
    步骤 2.3：章节内部结构相似性分析（基于LLM）

    Compares internal paragraph function sequences across sections using LLM.
    使用LLM比较不同章节内部段落功能序列的相似性。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return InternalStructureSimilarityResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Call LLM handler for analysis (with chain-call to detect sections first)
        # 调用LLM handler进行分析（链式调用先检测章节）
        logger.info("Calling Step2_3Handler for LLM-based internal structure similarity analysis")
        result = await step2_3_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step2-3",
            use_cache=True
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        section_structures: List[SectionInternalStructure] = []
        for pf_data in result.get("paragraph_functions", []):
            section_structures.append(SectionInternalStructure(
                section_index=pf_data.get("section_index", len(section_structures)),
                section_role="body",
                paragraph_functions=[],
                function_sequence=pf_data.get("functions", []),
                heading_depth=0,
                has_subheadings=False,
                argument_count=0,
                argument_density=0.0
            ))

        # Build similarity pairs from matrix
        similarity_pairs: List[StructureSimilarityPair] = []
        suspicious_pairs: List[StructureSimilarityPair] = []
        similarity_matrix = result.get("similarity_matrix", [])

        for i in range(len(similarity_matrix)):
            for j in range(i + 1, len(similarity_matrix)):
                if j < len(similarity_matrix[i]):
                    similarity = similarity_matrix[i][j] * 100 if similarity_matrix[i][j] <= 1 else similarity_matrix[i][j]
                    is_suspicious = similarity > 70
                    pair = StructureSimilarityPair(
                        section_a_index=i,
                        section_b_index=j,
                        section_a_role="body",
                        section_b_role="body",
                        function_sequence_similarity=similarity,
                        structure_similarity=similarity,
                        is_suspicious=is_suspicious
                    )
                    similarity_pairs.append(pair)
                    if is_suspicious:
                        suspicious_pairs.append(pair)

        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "structure_similarity_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.SECTION,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        return InternalStructureSimilarityResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            section_structures=section_structures,
            similarity_pairs=similarity_pairs,
            average_similarity=result.get("avg_similarity", 0.0) * 100 if result.get("avg_similarity", 0.0) <= 1 else result.get("avg_similarity", 0.0),
            max_similarity=max([p.function_sequence_similarity for p in similarity_pairs], default=0.0),
            heading_depth_cv=result.get("heading_variance", 0.0),
            argument_density_cv=result.get("argument_density_cv", 0.0),
            suspicious_pairs=suspicious_pairs,
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Internal structure similarity analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Step 2.4: Section Transition / 步骤 2.4：章节衔接与过渡
# -----------------------------------------------------------------------------

@router.post("/step2-4/transition", response_model=SectionTransitionResponse)
async def analyze_section_transition(request: SectionTransitionRequest):
    """
    Step 2.4: Section Transition Analysis (LLM-based with pre-calculated statistics)
    步骤 2.4：章节衔接与过渡分析（基于LLM，使用预计算统计数据）

    Pre-calculates explicit transition markers, then passes to LLM for semantic analysis.
    预计算显性过渡标记，然后传递给LLM进行语义分析。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return SectionTransitionResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # STEP 1: Pre-calculate transition statistics from text
        # 步骤1：从文本预计算过渡统计数据
        paragraphs = _get_paragraphs_from_request(request)
        paragraph_count = len(paragraphs)

        # Detect explicit transition markers at paragraph starts
        # 检测段落开头的显性过渡标记
        explicit_transition_patterns = [
            r"^(in this section|this section|now let us|now we|moving on|turning to|having discussed|building on)",
            r"^(first|second|third|fourth|finally|firstly|secondly|thirdly|lastly)",
            r"^(moreover|furthermore|additionally|in addition|similarly|likewise)",
            r"^(however|nevertheless|nonetheless|on the other hand|in contrast|conversely)",
            r"^(therefore|thus|consequently|as a result|hence|accordingly)",
            r"^(to summarize|in summary|in conclusion|to conclude|overall)"
        ]

        explicit_transitions = []
        for i, para in enumerate(paragraphs):
            para_lower = para.lower().strip()
            for pattern in explicit_transition_patterns:
                match = re.search(pattern, para_lower, re.IGNORECASE)
                if match:
                    explicit_transitions.append({
                        "paragraph_index": i,
                        "matched_word": match.group(1),
                        "pattern_type": "explicit_transition"
                    })
                    break  # One match per paragraph

        explicit_count = len(explicit_transitions)
        explicit_ratio = round(explicit_count / paragraph_count, 3) if paragraph_count > 0 else 0

        # Build pre-calculated statistics JSON
        # 构建预计算统计数据JSON
        parsed_statistics = {
            "paragraph_count": paragraph_count,
            "explicit_transition_count": explicit_count,
            "explicit_transition_ratio": explicit_ratio,
            "is_high_explicit": explicit_ratio > 0.5,
            "explicit_transitions": explicit_transitions[:10],  # Limit for prompt size
            "evaluation": "AI-like (too many explicit transitions)" if explicit_ratio > 0.5 else ("Borderline" if explicit_ratio > 0.3 else "Human-like (natural transitions)")
        }

        import json
        parsed_statistics_str = json.dumps(parsed_statistics, indent=2, ensure_ascii=False)

        logger.info(f"Step 2.4: Pre-calculated explicit_ratio={explicit_ratio}, count={explicit_count}")

        # STEP 2: Pass pre-calculated statistics to LLM
        # 步骤2：将预计算统计数据传递给LLM
        logger.info("Calling Step2_4Handler for LLM-based section transition analysis")
        result = await step2_4_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step2-4",
            use_cache=True,
            parsed_statistics=parsed_statistics_str,
            explicit_ratio=explicit_ratio
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        transitions: List[SectionTransitionInfo] = []
        for tw_data in result.get("transition_words", []):
            transitions.append(SectionTransitionInfo(
                from_section_index=tw_data.get("from_section", 0),
                to_section_index=tw_data.get("to_section", 0),
                from_section_role="body",
                to_section_role="body",
                has_explicit_transition=len(tw_data.get("words", [])) > 0,
                explicit_words=tw_data.get("words", []),
                transition_strength=tw_data.get("strength", "moderate"),
                semantic_echo_score=0.0,
                echoed_keywords=[],
                opener_text="",
                opener_pattern="natural",
                is_formulaic_opener=False,
                transition_risk_score=0
            ))

        # Add formulaic openers to transitions if available
        for op_data in result.get("opener_patterns", []):
            if op_data.get("is_formulaic", False):
                # Find or create transition for this section
                section_idx = op_data.get("section_index", 0)
                for trans in transitions:
                    if trans.to_section_index == section_idx:
                        trans.is_formulaic_opener = True
                        trans.opener_text = op_data.get("opener", "")
                        trans.opener_pattern = "formulaic"
                        break

        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "transition_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.SECTION,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        strength_distribution = result.get("strength_distribution", {"strong": 0, "moderate": 0, "weak": 0})
        formulaic_count = len([op for op in result.get("opener_patterns", []) if op.get("is_formulaic", False)])

        processing_time_ms = int((time.time() - start_time) * 1000)

        # STEP 3: Return CALCULATED statistics (not LLM's)
        # 步骤3：返回计算的统计数据（不是LLM的）
        return SectionTransitionResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            total_transitions=len(transitions) if transitions else paragraph_count - 1,
            explicit_transition_count=explicit_count,  # Use pre-calculated value
            transitions=transitions,
            explicit_ratio=explicit_ratio,  # Use pre-calculated value
            avg_semantic_echo=result.get("semantic_echo_score", 0.0) * 100 if result.get("semantic_echo_score", 0.0) <= 1 else result.get("semantic_echo_score", 0.0),
            formulaic_opener_count=formulaic_count,
            strength_distribution=strength_distribution,
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Section transition analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Step 2.5: Inter-Section Logic / 步骤 2.5：章节间逻辑关系
# -----------------------------------------------------------------------------

@router.post("/step2-5/logic", response_model=InterSectionLogicResponse)
async def analyze_inter_section_logic(request: InterSectionLogicRequest):
    """
    Step 2.5: Inter-Section Logic Analysis (LLM-based)
    步骤 2.5：章节间逻辑关系分析（基于LLM）

    Analyzes argument chains, redundancy, and progression patterns using LLM.
    使用LLM分析论点链、冗余和推进模式。
    """
    start_time = time.time()

    try:
        # Get document text
        # 获取文档文本
        document_text = request.text if request.text else ""
        if not document_text and request.paragraphs:
            document_text = "\n\n".join(request.paragraphs)

        if not document_text:
            return InterSectionLogicResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Call LLM handler for analysis (with chain-call to detect sections first)
        # 调用LLM handler进行分析（链式调用先检测章节）
        logger.info("Calling Step2_5Handler for LLM-based inter-section logic analysis")
        result = await step2_5_handler.analyze(
            document_text=document_text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step2-5",
            use_cache=True
        )

        # Convert LLM result to response model
        # 将LLM结果转换为响应模型
        argument_chain: List[ArgumentChainNode] = []
        # LLM doesn't return detailed chain, create minimal structure
        for i, section in enumerate(result.get("detected_sections", [])):
            argument_chain.append(ArgumentChainNode(
                section_index=i,
                section_role=section.get("role", "body"),
                main_argument="",
                supporting_points=[],
                connects_to_previous=i > 0,
                connection_type="extends" if i > 0 else ""
            ))

        redundancies: List[RedundancyInfo] = []
        for red_data in result.get("redundancy_issues", []):
            redundancies.append(RedundancyInfo(
                section_a_index=red_data.get("section_a", 0),
                section_b_index=red_data.get("section_b", 0),
                redundant_content=red_data.get("overlap_content", ""),
                redundancy_type="repeated_phrase",
                severity="medium"
            ))

        progression_patterns: List[ProgressionPatternInfo] = []
        progression_pattern = result.get("progression_pattern", "varied")
        if progression_pattern == "linear":
            progression_patterns.append(ProgressionPatternInfo(
                pattern_type="sequential",
                description="Sections follow a strict sequential order",
                description_zh="章节遵循严格的顺序排列",
                is_ai_typical=True,
                sections_involved=list(range(len(argument_chain)))
            ))
        elif progression_pattern != "varied":
            progression_patterns.append(ProgressionPatternInfo(
                pattern_type=progression_pattern,
                description=f"Sections follow a {progression_pattern} pattern",
                description_zh=f"章节遵循{progression_pattern}模式",
                is_ai_typical=False,
                sections_involved=list(range(len(argument_chain)))
            ))

        issues: List[DetectionIssue] = []
        for issue_data in result.get("issues", []):
            issues.append(DetectionIssue(
                type=issue_data.get("type", "logic_issue"),
                description=issue_data.get("description", ""),
                description_zh=issue_data.get("description_zh", ""),
                severity=IssueSeverity(issue_data.get("severity", "medium")),
                layer=LayerLevel.SECTION,
                location=", ".join(issue_data.get("affected_positions", [])) if issue_data.get("affected_positions") else None,
                suggestion=issue_data.get("fix_suggestions", [""])[0] if issue_data.get("fix_suggestions") else "",
                suggestion_zh=issue_data.get("fix_suggestions_zh", [""])[0] if issue_data.get("fix_suggestions_zh") else ""
            ))

        processing_time_ms = int((time.time() - start_time) * 1000)

        return InterSectionLogicResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            argument_chain=argument_chain,
            chain_coherence_score=result.get("argument_chain_score", 0.0),
            redundancies=redundancies,
            total_redundancies=len(redundancies),
            progression_patterns=progression_patterns,
            dominant_pattern=result.get("progression_pattern", "varied"),
            pattern_variety_score=100 - result.get("linearity_score", 0),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Inter-section logic analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
