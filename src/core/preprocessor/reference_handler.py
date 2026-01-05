"""
Reference handler module - separates and restores reference sections
参考文献处理模块 - 分离和恢复参考文献部分
"""

import re
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ReferenceHandler:
    """
    Handles separation and restoration of reference sections
    处理参考文献部分的分离和恢复
    """

    # Reference section headers
    # 参考文献章节标题
    REFERENCE_HEADERS = [
        r'\n\s*(?:[0-9]+\.\s*)?(?:References|Bibliography|Works Cited|Literature Cited|参考文献)\s*\n',
        r'\n\s*(?:[0-9]+\.\s*)?(?:References|Bibliography|Works Cited|Literature Cited|参考文献)\s*$'
    ]

    def extract(self, text: str) -> Tuple[str, Optional[str]]:
        """
        Extract reference section from text
        从文本中提取参考文献部分

        Args:
            text: Full document text

        Returns:
            Tuple of (body_text, reference_section)
        """
        if not text:
            return "", None

        # Try to find the last occurrence of any reference header
        # 尝试查找任何参考文献标题的最后一次出现
        last_match = None
        last_match_end = -1

        for pattern in self.REFERENCE_HEADERS:
            # We want the last one because "References" might appear in TOC
            # 我们想要最后一个，因为"References"可能出现在目录中
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                # Pick the last match that is in the last 30% of the document
                # 选择位于文档最后30%的最后一个匹配项
                # This helps avoid false positives in TOC
                potential_match = matches[-1]
                if potential_match.start() > len(text) * 0.7:
                    if potential_match.end() > last_match_end:
                        last_match = potential_match
                        last_match_end = potential_match.end()

        if last_match:
            # Split text
            # 分割文本
            split_point = last_match.start()
            body = text[:split_point].strip()
            # Include the header in the reference section
            # 将标题包含在参考文献部分中
            reference_section = text[split_point:].strip()
            
            logger.info(f"Extracted reference section (length: {len(reference_section)})")
            return body, reference_section

        return text, None

    def restore(self, body: str, reference_section: Optional[str]) -> str:
        """
        Restore reference section to body
        将参考文献部分恢复到正文

        Args:
            body: Body text
            reference_section: Reference section text

        Returns:
            Combined text
        """
        if not reference_section:
            return body

        return f"{body}\n\n{reference_section}"
