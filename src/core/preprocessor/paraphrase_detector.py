"""
Paraphrase detector module
释义检测模块

Identifies sentences that appear to be paraphrases of cited work.
Paraphrases typically end with a citation (e.g., (Smith, 2020) or [1]).
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParaphraseInfo:
    """
    Information about a detected paraphrase
    """
    is_paraphrase: bool
    citation: Optional[str] = None
    citation_pos: Optional[int] = None


class ParaphraseDetector:
    """
    Detector for paraphrase sentences
    释义句检测器
    """

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """
        Compile regex patterns
        """
        # Common citation patterns at the end of a sentence
        # 句尾常见的引用模式
        
        # (Author, Year) or (Author et al., Year)
        # 允许句号在引用前或引用后
        self.author_year_pattern = re.compile(
            r'\(\s*[A-Z][a-z]+(?:\s+(?:et\s+al\.|&|and)\s+[A-Z][a-z]+)*,?\s*\d{4}[a-z]?\s*\)\s*[.!?]?\s*$'
        )
        
        # [1], [1,2], [1-3]
        self.numeric_pattern = re.compile(
            r'\[\s*\d+(?:[,\-]\s*\d+)*\s*\]\s*[.!?]?\s*$'
        )

        # Words that often introduce paraphrases (optional enhancement)
        self.intro_words = {
            "according", "states", "argues", "suggests", "demonstrates",
            "found", "reported", "concluded", "observed", "noted"
        }

    def detect(self, text: str) -> ParaphraseInfo:
        """
        Detect if text is a paraphrase
        检测文本是否为释义
        
        Args:
            text: Sentence text
            
        Returns:
            ParaphraseInfo object
        """
        text = text.strip()
        
        # Check author-year pattern
        match = self.author_year_pattern.search(text)
        if match:
            return ParaphraseInfo(
                is_paraphrase=True,
                citation=match.group(0),
                citation_pos=match.start()
            )
            
        # Check numeric pattern
        match = self.numeric_pattern.search(text)
        if match:
            return ParaphraseInfo(
                is_paraphrase=True,
                citation=match.group(0),
                citation_pos=match.start()
            )
            
        return ParaphraseInfo(is_paraphrase=False)
