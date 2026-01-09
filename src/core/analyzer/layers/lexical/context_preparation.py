"""
Step 5.0: Lexical Context Preparation
步骤5.0：词汇环境准备

Prepares the lexical analysis context by:
- Receiving sentence context from Layer 2
- Inheriting locked terms from Step 1.0
- Building paragraph-term mapping
- Loading vocabulary feature database

通过以下方式准备词汇分析上下文：
- 从Layer 2接收句子上下文
- 从Step 1.0继承锁定词汇
- 建立段落-词汇映射
- 加载词汇特征数据库
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class WordPosition:
    """
    Word position information
    词汇位置信息
    """
    word: str
    paragraph_index: int
    sentence_index: int
    word_index: int  # Position within sentence
    start_char: int  # Character offset
    end_char: int


@dataclass
class ParagraphLexicalInfo:
    """
    Lexical information for a paragraph
    段落的词汇信息
    """
    index: int
    text: str
    word_count: int
    sentences: List[str]
    word_positions: Dict[str, List[WordPosition]] = field(default_factory=dict)
    unique_words: Set[str] = field(default_factory=set)


@dataclass
class LexicalContext:
    """
    Complete lexical context for Layer 1 analysis
    Layer 1分析的完整词汇上下文
    """
    paragraphs: List[ParagraphLexicalInfo]
    locked_terms: List[str]
    locked_terms_lower: Set[str]  # Lowercase for matching
    total_words: int
    total_sentences: int
    paragraph_count: int
    sentence_to_paragraph: Dict[int, int]  # sentence_idx → para_idx
    feature_db: Dict[str, Any]
    colloquialism_level: int


class LexicalContextPreparer:
    """
    Step 5.0: Prepares lexical analysis context
    步骤5.0：准备词汇分析上下文
    """

    def __init__(self):
        """Initialize the context preparer"""
        self.feature_db = self._load_feature_database()
        self.aigc_fingerprints = self._load_aigc_fingerprints()

    def _load_feature_database(self) -> Dict[str, Any]:
        """
        Load human feature vocabulary database
        加载人类特征词汇数据库
        """
        try:
            db_path = Path(__file__).parent.parent.parent.parent / "data" / "human_features.json"
            if db_path.exists():
                with open(db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logger.warning(f"Human features database not found at {db_path}")
                return self._get_default_feature_db()
        except Exception as e:
            logger.error(f"Failed to load human features database: {e}")
            return self._get_default_feature_db()

    def _load_aigc_fingerprints(self) -> Dict[str, Any]:
        """
        Load AIGC fingerprint database from existing lexical_orchestrator
        从现有的lexical_orchestrator加载AIGC指纹数据库
        """
        try:
            from src.core.analyzer.layers.lexical_orchestrator import (
                FINGERPRINT_TYPE_A,
                FINGERPRINT_TYPE_B,
                FINGERPRINT_PHRASES,
            )
            return {
                "type_a": FINGERPRINT_TYPE_A,
                "type_b": FINGERPRINT_TYPE_B,
                "phrases": FINGERPRINT_PHRASES,
            }
        except ImportError:
            logger.warning("Could not import fingerprints from lexical_orchestrator")
            return self._get_default_fingerprints()

    def _get_default_feature_db(self) -> Dict[str, Any]:
        """
        Get default feature database if file not found
        如果文件未找到，获取默认特征数据库
        """
        return {
            "verbs": {
                "high_frequency": {
                    "examine": {"weight": 95},
                    "argue": {"weight": 92},
                    "suggest": {"weight": 90},
                    "demonstrate": {"weight": 87},
                    "identify": {"weight": 84},
                    "analyze": {"weight": 88},
                    "investigate": {"weight": 88},
                },
                "target_coverage": 0.15
            },
            "adjectives": {
                "high_frequency": {
                    "significant": {"weight": 98},
                    "empirical": {"weight": 92},
                    "specific": {"weight": 94},
                    "consistent": {"weight": 90},
                },
                "target_coverage": 0.10
            },
            "phrases": {
                "high_frequency": {
                    "results indicate": {"weight": 95},
                    "in contrast to": {"weight": 94},
                    "data suggest": {"weight": 89},
                },
                "target_coverage": 0.05
            },
            "hedging": {
                "markers": {
                    "may": {"weight": 90},
                    "suggests": {"weight": 90},
                    "appears": {"weight": 88},
                },
                "target_coverage": 0.08
            }
        }

    def _get_default_fingerprints(self) -> Dict[str, Any]:
        """
        Get default AIGC fingerprints if import fails
        如果导入失败，获取默认AIGC指纹
        """
        return {
            "type_a": {
                "delve": 99, "tapestry": 93, "multifaceted": 94,
                "pivotal": 98, "realm": 95, "landscape": 97,
                "intricate": 96, "harness": 92, "underscore": 95,
                "unveil": 87, "paramount": 88,
            },
            "type_b": {
                "comprehensive": 91, "robust": 89, "leverage": 90,
                "facilitate": 84, "utilize": 85, "seamless": 86,
                "holistic": 85, "transformative": 84, "crucial": 85,
            },
            "phrases": {
                "plays a crucial role": 92,
                "it is important to note": 96,
                "in the realm of": 30,
                "a plethora of": 82,
                "not only...but also": 94,
            }
        }

    def prepare_context(
        self,
        document_text: str,
        session_id: Optional[str] = None,
        sentence_context: Optional[Dict[str, Any]] = None,
        colloquialism_level: int = 4,
    ) -> LexicalContext:
        """
        Prepare complete lexical context for Layer 1 analysis
        为Layer 1分析准备完整的词汇上下文

        Args:
            document_text: Full document text
            session_id: Session ID for retrieving locked terms
            sentence_context: Context from Layer 2 (optional)
            colloquialism_level: Target formality level (0-10)

        Returns:
            LexicalContext with all prepared data
        """
        logger.info("Step 5.0: Preparing lexical context")

        # Get locked terms from session
        locked_terms = self._get_locked_terms(session_id)
        locked_terms_lower = {term.lower() for term in locked_terms}

        # Split into paragraphs
        paragraphs_text = self._split_paragraphs(document_text)

        # Build paragraph lexical info
        paragraphs: List[ParagraphLexicalInfo] = []
        sentence_to_paragraph: Dict[int, int] = {}
        global_sentence_idx = 0
        total_words = 0

        for para_idx, para_text in enumerate(paragraphs_text):
            # Split paragraph into sentences
            sentences = self._split_sentences(para_text)

            # Build word positions
            word_positions = defaultdict(list)
            unique_words = set()

            for sent_idx, sentence in enumerate(sentences):
                words = self._tokenize(sentence)
                char_offset = 0

                for word_idx, word in enumerate(words):
                    word_lower = word.lower()
                    unique_words.add(word_lower)

                    # Find character position
                    start = sentence.lower().find(word_lower, char_offset)
                    if start == -1:
                        start = char_offset
                    end = start + len(word)
                    char_offset = end

                    position = WordPosition(
                        word=word,
                        paragraph_index=para_idx,
                        sentence_index=global_sentence_idx,
                        word_index=word_idx,
                        start_char=start,
                        end_char=end,
                    )
                    word_positions[word_lower].append(position)

                sentence_to_paragraph[global_sentence_idx] = para_idx
                global_sentence_idx += 1

            word_count = sum(len(self._tokenize(s)) for s in sentences)
            total_words += word_count

            para_info = ParagraphLexicalInfo(
                index=para_idx,
                text=para_text,
                word_count=word_count,
                sentences=sentences,
                word_positions=dict(word_positions),
                unique_words=unique_words,
            )
            paragraphs.append(para_info)

        context = LexicalContext(
            paragraphs=paragraphs,
            locked_terms=locked_terms,
            locked_terms_lower=locked_terms_lower,
            total_words=total_words,
            total_sentences=global_sentence_idx,
            paragraph_count=len(paragraphs),
            sentence_to_paragraph=sentence_to_paragraph,
            feature_db=self.feature_db,
            colloquialism_level=colloquialism_level,
        )

        logger.info(
            f"Step 5.0 complete: {len(paragraphs)} paragraphs, "
            f"{total_words} words, {len(locked_terms)} locked terms"
        )

        return context

    def _get_locked_terms(self, session_id: Optional[str]) -> List[str]:
        """
        Get locked terms from session
        从会话获取锁定词汇
        """
        if not session_id:
            return []

        try:
            from src.api.routes.analysis.term_lock import get_session_locked_terms
            terms = get_session_locked_terms(session_id)
            logger.info(f"Loaded {len(terms)} locked terms from session {session_id}")
            return terms
        except ImportError:
            logger.warning("Could not import term_lock module")
            return []
        except Exception as e:
            logger.warning(f"Could not get locked terms: {e}")
            return []

    def _split_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs
        将文本分割成段落
        """
        # Split by double newlines or multiple newlines
        paragraphs = re.split(r'\n\s*\n', text.strip())
        # Filter empty paragraphs and strip whitespace
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        将文本分割成句子
        """
        # Simple sentence splitting - handles common cases
        # Avoid splitting on abbreviations like "Dr.", "Mr.", "e.g.", "i.e."
        text = re.sub(r'(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|e\.g|i\.e)\.\s', r'\1<DOT> ', text)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Restore dots
        sentences = [s.replace('<DOT>', '.') for s in sentences]
        return [s.strip() for s in sentences if s.strip()]

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple word tokenization
        简单的词汇分词
        """
        # Remove punctuation and split by whitespace
        words = re.findall(r'\b[a-zA-Z]+(?:\'[a-zA-Z]+)?\b', text)
        return words

    def is_term_locked(self, term: str, context: LexicalContext) -> bool:
        """
        Check if a term is locked
        检查词汇是否被锁定
        """
        term_lower = term.lower()

        # Direct match
        if term_lower in context.locked_terms_lower:
            return True

        # Check if term is part of a locked term
        for locked in context.locked_terms_lower:
            if term_lower in locked or locked in term_lower:
                return True

        return False

    def get_context_summary(self, context: LexicalContext) -> Dict[str, Any]:
        """
        Get a summary of the prepared context
        获取准备好的上下文摘要
        """
        return {
            "paragraph_count": context.paragraph_count,
            "total_sentences": context.total_sentences,
            "total_words": context.total_words,
            "locked_terms_count": len(context.locked_terms),
            "locked_terms": context.locked_terms[:10],  # First 10
            "colloquialism_level": context.colloquialism_level,
            "feature_db_loaded": bool(context.feature_db),
            "paragraphs_summary": [
                {
                    "index": p.index,
                    "word_count": p.word_count,
                    "sentence_count": len(p.sentences),
                    "unique_word_count": len(p.unique_words),
                }
                for p in context.paragraphs
            ],
        }
