"""
Sentence Context Provider
句子上下文提供器

Provides paragraph-level context for sentence-level analysis and rewriting.
This is a critical component for the "Sentence-in-Paragraph" design principle.

为句子级分析和改写提供段落级上下文。
这是"句子段落化"设计原则的关键组件。

**Design Principle 设计原则:**
All sentence-level operations (analysis, rewriting) MUST be performed with
paragraph context. This ensures:
1. Context-aware analysis (understanding sentence role in paragraph)
2. Coherent rewriting (maintaining flow with adjacent sentences)
3. Semantic consistency (preserving paragraph meaning)

所有句子级操作（分析、改写）必须在段落上下文中进行。这确保：
1. 上下文感知分析（理解句子在段落中的角色）
2. 连贯改写（与相邻句子保持流畅）
3. 语义一致性（保持段落含义）
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class SentencePosition(Enum):
    """Position of sentence within paragraph"""
    FIRST = "first"      # Opening sentence
    MIDDLE = "middle"    # Body sentence
    LAST = "last"        # Closing sentence
    ONLY = "only"        # Single sentence paragraph


@dataclass
class SentenceWithContext:
    """
    A sentence with its full paragraph context
    带有完整段落上下文的句子

    This is the primary data structure for context-aware sentence operations.
    这是上下文感知句子操作的主要数据结构。
    """
    # Sentence info
    sentence_text: str
    sentence_index: int           # Global index in document
    position_in_paragraph: int    # Index within paragraph (0-based)
    word_count: int

    # Paragraph context (CRITICAL for rewriting)
    paragraph_text: str           # Full paragraph text
    paragraph_index: int          # Paragraph index in document
    paragraph_role: str           # Role of paragraph (intro, body, conclusion, etc.)
    paragraph_word_count: int

    # Adjacent sentences (for coherence)
    previous_sentence: Optional[str] = None
    next_sentence: Optional[str] = None

    # Position info
    position: SentencePosition = SentencePosition.MIDDLE
    total_sentences_in_paragraph: int = 1

    # Sentence analysis (from Layer 2)
    sentence_role: str = "unknown"     # Role within paragraph
    has_issues: bool = False           # Whether flagged for rewriting
    issue_types: List[str] = field(default_factory=list)

    # Section context (from Layer 4)
    section_role: str = "body"         # Role of containing section
    section_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "sentence_text": self.sentence_text,
            "sentence_index": self.sentence_index,
            "position_in_paragraph": self.position_in_paragraph,
            "word_count": self.word_count,
            "paragraph_text": self.paragraph_text,
            "paragraph_index": self.paragraph_index,
            "paragraph_role": self.paragraph_role,
            "paragraph_word_count": self.paragraph_word_count,
            "previous_sentence": self.previous_sentence,
            "next_sentence": self.next_sentence,
            "position": self.position.value,
            "total_sentences_in_paragraph": self.total_sentences_in_paragraph,
            "sentence_role": self.sentence_role,
            "has_issues": self.has_issues,
            "issue_types": self.issue_types,
            "section_role": self.section_role,
            "section_index": self.section_index,
        }

    def get_rewrite_context(self) -> Dict[str, Any]:
        """
        Get context dict formatted for rewriting prompts
        获取为改写提示格式化的上下文字典

        This is the context that MUST be included in rewriting prompts.
        这是必须包含在改写提示中的上下文。
        """
        return {
            "original_sentence": self.sentence_text,
            "full_paragraph": self.paragraph_text,
            "paragraph_role": self.paragraph_role,
            "sentence_role": self.sentence_role,
            "position_in_paragraph": f"{self.position_in_paragraph + 1}/{self.total_sentences_in_paragraph}",
            "is_first_sentence": self.position == SentencePosition.FIRST or self.position == SentencePosition.ONLY,
            "is_last_sentence": self.position == SentencePosition.LAST or self.position == SentencePosition.ONLY,
            "previous_sentence": self.previous_sentence or "[None - this is the first sentence]",
            "next_sentence": self.next_sentence or "[None - this is the last sentence]",
            "issues_to_fix": self.issue_types,
            "section_role": self.section_role,
        }


class SentenceContextProvider:
    """
    Provides paragraph context for sentence-level operations
    为句子级操作提供段落上下文

    Usage:
    1. Initialize with document text and optional analysis results
    2. Call get_sentence_with_context() for any sentence
    3. Use the context for analysis or rewriting

    用法：
    1. 用文档文本和可选分析结果初始化
    2. 对任何句子调用 get_sentence_with_context()
    3. 使用上下文进行分析或改写
    """

    def __init__(
        self,
        paragraphs: List[str],
        paragraph_roles: Optional[List[str]] = None,
        sentence_roles: Optional[List[str]] = None,
        section_boundaries: Optional[List[int]] = None,
        section_roles: Optional[List[str]] = None,
    ):
        """
        Initialize context provider

        Args:
            paragraphs: List of paragraph texts
            paragraph_roles: Role of each paragraph (from Layer 3)
            sentence_roles: Role of each sentence (from Layer 2)
            section_boundaries: Paragraph indices where sections start (from Layer 4)
            section_roles: Role of each section (from Layer 4)
        """
        self.paragraphs = paragraphs
        self.paragraph_roles = paragraph_roles or ["body"] * len(paragraphs)
        self.sentence_roles = sentence_roles or []
        self.section_boundaries = section_boundaries or [0]
        self.section_roles = section_roles or ["body"]

        # Build sentence index
        self._build_sentence_index()

    def _build_sentence_index(self):
        """
        Build index mapping sentences to paragraphs
        构建句子到段落的索引映射
        """
        self.sentences: List[SentenceWithContext] = []
        self.sentence_to_paragraph: Dict[int, int] = {}
        self.paragraph_sentences: Dict[int, List[int]] = {}

        global_idx = 0

        for para_idx, para in enumerate(self.paragraphs):
            # Split paragraph into sentences
            para_sentences = self._split_into_sentences(para)
            self.paragraph_sentences[para_idx] = []

            # Get section info for this paragraph
            section_idx = self._get_section_for_paragraph(para_idx)
            section_role = self.section_roles[section_idx] if section_idx < len(self.section_roles) else "body"

            for pos_in_para, sentence_text in enumerate(para_sentences):
                # Determine position
                if len(para_sentences) == 1:
                    position = SentencePosition.ONLY
                elif pos_in_para == 0:
                    position = SentencePosition.FIRST
                elif pos_in_para == len(para_sentences) - 1:
                    position = SentencePosition.LAST
                else:
                    position = SentencePosition.MIDDLE

                # Get adjacent sentences
                prev_sent = para_sentences[pos_in_para - 1] if pos_in_para > 0 else None
                next_sent = para_sentences[pos_in_para + 1] if pos_in_para < len(para_sentences) - 1 else None

                # Get sentence role if available
                sent_role = self.sentence_roles[global_idx] if global_idx < len(self.sentence_roles) else "unknown"

                sentence_ctx = SentenceWithContext(
                    sentence_text=sentence_text,
                    sentence_index=global_idx,
                    position_in_paragraph=pos_in_para,
                    word_count=len(sentence_text.split()),
                    paragraph_text=para,
                    paragraph_index=para_idx,
                    paragraph_role=self.paragraph_roles[para_idx] if para_idx < len(self.paragraph_roles) else "body",
                    paragraph_word_count=len(para.split()),
                    previous_sentence=prev_sent,
                    next_sentence=next_sent,
                    position=position,
                    total_sentences_in_paragraph=len(para_sentences),
                    sentence_role=sent_role,
                    section_role=section_role,
                    section_index=section_idx,
                )

                self.sentences.append(sentence_ctx)
                self.sentence_to_paragraph[global_idx] = para_idx
                self.paragraph_sentences[para_idx].append(global_idx)
                global_idx += 1

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_section_for_paragraph(self, para_idx: int) -> int:
        """Get section index for a paragraph"""
        section_idx = 0
        for i, boundary in enumerate(self.section_boundaries):
            if para_idx >= boundary:
                section_idx = i
            else:
                break
        return section_idx

    def get_sentence_with_context(self, sentence_index: int) -> Optional[SentenceWithContext]:
        """
        Get a sentence with its full context
        获取带有完整上下文的句子

        Args:
            sentence_index: Global sentence index

        Returns:
            SentenceWithContext or None if index out of range
        """
        if 0 <= sentence_index < len(self.sentences):
            return self.sentences[sentence_index]
        return None

    def get_sentences_in_paragraph(self, paragraph_index: int) -> List[SentenceWithContext]:
        """
        Get all sentences in a paragraph with context
        获取段落中所有带上下文的句子
        """
        if paragraph_index in self.paragraph_sentences:
            return [self.sentences[idx] for idx in self.paragraph_sentences[paragraph_index]]
        return []

    def get_all_sentences(self) -> List[SentenceWithContext]:
        """Get all sentences with context"""
        return self.sentences

    def mark_sentence_for_rewriting(
        self,
        sentence_index: int,
        issue_types: List[str]
    ):
        """
        Mark a sentence as needing rewriting
        标记句子需要改写

        Args:
            sentence_index: Global sentence index
            issue_types: List of issue types detected
        """
        if 0 <= sentence_index < len(self.sentences):
            self.sentences[sentence_index].has_issues = True
            self.sentences[sentence_index].issue_types = issue_types

    def get_sentences_needing_rewrite(self) -> List[SentenceWithContext]:
        """Get all sentences that have been flagged for rewriting"""
        return [s for s in self.sentences if s.has_issues]

    def get_rewrite_prompt_context(self, sentence_index: int) -> Optional[Dict[str, Any]]:
        """
        Get formatted context for a rewriting prompt
        获取改写提示的格式化上下文

        This is the primary method for getting context when generating rewrite prompts.
        这是生成改写提示时获取上下文的主要方法。
        """
        sentence = self.get_sentence_with_context(sentence_index)
        if sentence:
            return sentence.get_rewrite_context()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "total_paragraphs": len(self.paragraphs),
            "total_sentences": len(self.sentences),
            "sentences_needing_rewrite": len(self.get_sentences_needing_rewrite()),
            "sentences": [s.to_dict() for s in self.sentences],
        }


def create_sentence_context_from_layer_results(
    paragraphs: List[str],
    layer_3_result: Optional[Dict[str, Any]] = None,
    layer_2_result: Optional[Dict[str, Any]] = None,
    layer_4_result: Optional[Dict[str, Any]] = None,
) -> SentenceContextProvider:
    """
    Factory function to create SentenceContextProvider from layer analysis results
    从层分析结果创建SentenceContextProvider的工厂函数

    Args:
        paragraphs: List of paragraph texts
        layer_3_result: Result from ParagraphOrchestrator
        layer_2_result: Result from SentenceOrchestrator
        layer_4_result: Result from SectionAnalyzer

    Returns:
        Configured SentenceContextProvider
    """
    # Extract paragraph roles from Layer 3
    paragraph_roles = None
    if layer_3_result:
        paragraph_roles = layer_3_result.get("details", {}).get("roles", {}).get("paragraph_roles", None)

    # Extract sentence roles from Layer 2
    sentence_roles = None
    if layer_2_result:
        sentence_roles = layer_2_result.get("details", {}).get("sentence_roles", {}).get("roles", None)

    # Extract section info from Layer 4
    section_boundaries = None
    section_roles = None
    if layer_4_result:
        sections = layer_4_result.get("details", {}).get("sections", [])
        section_boundaries = [s.get("start_para_idx", 0) for s in sections]
        section_roles = [s.get("role", "body") for s in sections]

    return SentenceContextProvider(
        paragraphs=paragraphs,
        paragraph_roles=paragraph_roles,
        sentence_roles=sentence_roles,
        section_boundaries=section_boundaries,
        section_roles=section_roles,
    )
