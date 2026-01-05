"""
Auto-fix Templates - Rule-based fixes for common AI sentence patterns
自动修复模板 - 常见AI句式的规则化修复

Part of DEAI Engine 2.0 - Deterministic Solutions
DEAI引擎2.0的一部分 - 确定性解决方案

This module provides deterministic (non-LLM) fixes for common AI writing patterns.
Users confirm fixes before application.
此模块提供常见AI写作模式的确定性（非LLM）修复。用户确认后才应用修复。
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class FixType(Enum):
    """Types of auto-fixes"""
    DELETE_AND_CAPITALIZE = "delete_and_capitalize"  # Remove phrase, capitalize next word
    REPLACE_PHRASE = "replace_phrase"  # Direct phrase replacement
    REPLACE_WORD = "replace_word"  # Single word replacement
    SIMPLIFY_CONNECTOR = "simplify_connector"  # Replace connector with simpler version
    RESTRUCTURE = "restructure"  # Regex-based restructuring


@dataclass
class AutoFixMatch:
    """
    Represents a detected pattern that can be auto-fixed
    表示可以自动修复的检测到的模式
    """
    pattern_id: str
    matched_text: str
    position: int
    end_position: int
    fix_type: FixType
    suggested_fix: str
    explanation: str
    explanation_zh: str
    confidence: float  # 0-1, how confident we are in the fix


@dataclass
class AutoFixPreview:
    """
    Preview of an auto-fix before application
    应用前的自动修复预览
    """
    original_text: str
    fixed_text: str
    matches: List[AutoFixMatch]
    total_fixes: int
    risk_reduction_estimate: int  # Estimated points reduction


class AutoFixTemplates:
    """
    Collection of auto-fix templates for common AI patterns
    常见AI模式的自动修复模板集合
    """

    # Templates: (pattern, fix_type, replacement_or_handler, explanation_en, explanation_zh, confidence)
    # 模板：（模式，修复类型，替换或处理函数，英文解释，中文解释，置信度）
    TEMPLATES = [
        # === DELETE AND CAPITALIZE ===
        # Filler phrases that should be removed entirely
        # 应该完全删除的填充短语
        (
            r'\b[Ii]t is important to note that\s+',
            FixType.DELETE_AND_CAPITALIZE,
            "",
            "Remove filler phrase 'It is important to note that'",
            "删除填充短语 'It is important to note that'",
            0.95
        ),
        (
            r'\b[Ii]t should be noted that\s+',
            FixType.DELETE_AND_CAPITALIZE,
            "",
            "Remove filler phrase 'It should be noted that'",
            "删除填充短语 'It should be noted that'",
            0.95
        ),
        (
            r'\b[Ii]t is worth noting that\s+',
            FixType.DELETE_AND_CAPITALIZE,
            "",
            "Remove filler phrase 'It is worth noting that'",
            "删除填充短语 'It is worth noting that'",
            0.95
        ),
        (
            r'\b[Ii]t is worth mentioning that\s+',
            FixType.DELETE_AND_CAPITALIZE,
            "",
            "Remove filler phrase 'It is worth mentioning that'",
            "删除填充短语 'It is worth mentioning that'",
            0.95
        ),
        (
            r'\b[Ii]t is crucial to understand that\s+',
            FixType.DELETE_AND_CAPITALIZE,
            "",
            "Remove filler phrase 'It is crucial to understand that'",
            "删除填充短语 'It is crucial to understand that'",
            0.95
        ),
        (
            r'\b[Ii]t is essential to recognize that\s+',
            FixType.DELETE_AND_CAPITALIZE,
            "",
            "Remove filler phrase 'It is essential to recognize that'",
            "删除填充短语 'It is essential to recognize that'",
            0.95
        ),

        # === PHRASE REPLACEMENTS ===
        # Common AI phrases with direct replacements
        # 常见AI短语及其直接替换
        (
            r'\bplays a crucial role in\b',
            FixType.REPLACE_PHRASE,
            "is important for",
            "Replace 'plays a crucial role in' with simpler phrase",
            "用更简单的短语替换 'plays a crucial role in'",
            0.90
        ),
        (
            r'\bplays a pivotal role in\b',
            FixType.REPLACE_PHRASE,
            "is central to",
            "Replace 'plays a pivotal role in' with simpler phrase",
            "用更简单的短语替换 'plays a pivotal role in'",
            0.90
        ),
        (
            r'\bplays an important role in\b',
            FixType.REPLACE_PHRASE,
            "matters for",
            "Replace 'plays an important role in' with simpler phrase",
            "用更简单的短语替换 'plays an important role in'",
            0.85
        ),
        (
            r'\bdue to the fact that\b',
            FixType.REPLACE_PHRASE,
            "because",
            "Replace 'due to the fact that' with 'because'",
            "用 'because' 替换 'due to the fact that'",
            0.95
        ),
        (
            r'\bin order to\b',
            FixType.REPLACE_PHRASE,
            "to",
            "Replace 'in order to' with 'to'",
            "用 'to' 替换 'in order to'",
            0.90
        ),
        (
            r'\ba plethora of\b',
            FixType.REPLACE_PHRASE,
            "many",
            "Replace 'a plethora of' with 'many'",
            "用 'many' 替换 'a plethora of'",
            0.95
        ),
        (
            r'\ba myriad of\b',
            FixType.REPLACE_PHRASE,
            "many",
            "Replace 'a myriad of' with 'many'",
            "用 'many' 替换 'a myriad of'",
            0.95
        ),
        (
            r'\bserves as a testament to\b',
            FixType.REPLACE_PHRASE,
            "shows",
            "Replace 'serves as a testament to' with 'shows'",
            "用 'shows' 替换 'serves as a testament to'",
            0.90
        ),
        (
            r'\bin the realm of\b',
            FixType.REPLACE_PHRASE,
            "in",
            "Replace 'in the realm of' with 'in'",
            "用 'in' 替换 'in the realm of'",
            0.90
        ),
        (
            r'\bin the context of\b',
            FixType.REPLACE_PHRASE,
            "for",
            "Replace 'in the context of' with 'for'",
            "用 'for' 替换 'in the context of'",
            0.85
        ),
        (
            r'\bis of paramount importance\b',
            FixType.REPLACE_PHRASE,
            "is very important",
            "Replace 'is of paramount importance' with simpler phrase",
            "用更简单的短语替换 'is of paramount importance'",
            0.90
        ),
        (
            r'\bthe advent of\b',
            FixType.REPLACE_PHRASE,
            "the introduction of",
            "Replace 'the advent of' with 'the introduction of'",
            "用 'the introduction of' 替换 'the advent of'",
            0.85
        ),
        (
            r'\bwith regard to\b',
            FixType.REPLACE_PHRASE,
            "about",
            "Replace 'with regard to' with 'about'",
            "用 'about' 替换 'with regard to'",
            0.85
        ),
        (
            r'\bwith respect to\b',
            FixType.REPLACE_PHRASE,
            "about",
            "Replace 'with respect to' with 'about'",
            "用 'about' 替换 'with respect to'",
            0.85
        ),
        (
            r'\bin light of\b',
            FixType.REPLACE_PHRASE,
            "given",
            "Replace 'in light of' with 'given'",
            "用 'given' 替换 'in light of'",
            0.85
        ),
        (
            r'\bis characterized by\b',
            FixType.REPLACE_PHRASE,
            "has",
            "Replace 'is characterized by' with 'has'",
            "用 'has' 替换 'is characterized by'",
            0.80
        ),
        (
            r'\bcan be described as\b',
            FixType.REPLACE_PHRASE,
            "is",
            "Replace 'can be described as' with 'is'",
            "用 'is' 替换 'can be described as'",
            0.80
        ),

        # === WORD REPLACEMENTS ===
        # Single word replacements
        # 单词替换
        (
            r'\bdelve\b',
            FixType.REPLACE_WORD,
            "explore",
            "Replace 'delve' with 'explore'",
            "用 'explore' 替换 'delve'",
            0.95
        ),
        (
            r'\bdelves\b',
            FixType.REPLACE_WORD,
            "explores",
            "Replace 'delves' with 'explores'",
            "用 'explores' 替换 'delves'",
            0.95
        ),
        (
            r'\bdelving\b',
            FixType.REPLACE_WORD,
            "exploring",
            "Replace 'delving' with 'exploring'",
            "用 'exploring' 替换 'delving'",
            0.95
        ),
        (
            r'\butilize\b',
            FixType.REPLACE_WORD,
            "use",
            "Replace 'utilize' with 'use'",
            "用 'use' 替换 'utilize'",
            0.90
        ),
        (
            r'\butilizes\b',
            FixType.REPLACE_WORD,
            "uses",
            "Replace 'utilizes' with 'uses'",
            "用 'uses' 替换 'utilizes'",
            0.90
        ),
        (
            r'\butilizing\b',
            FixType.REPLACE_WORD,
            "using",
            "Replace 'utilizing' with 'using'",
            "用 'using' 替换 'utilizing'",
            0.90
        ),
        (
            r'\bcommence\b',
            FixType.REPLACE_WORD,
            "start",
            "Replace 'commence' with 'start'",
            "用 'start' 替换 'commence'",
            0.90
        ),
        (
            r'\bcommences\b',
            FixType.REPLACE_WORD,
            "starts",
            "Replace 'commences' with 'starts'",
            "用 'starts' 替换 'commences'",
            0.90
        ),
        (
            r'\baforementioned\b',
            FixType.REPLACE_WORD,
            "these",
            "Replace 'aforementioned' with 'these'",
            "用 'these' 替换 'aforementioned'",
            0.90
        ),
        (
            r'\bhenceforth\b',
            FixType.REPLACE_WORD,
            "from now on",
            "Replace 'henceforth' with 'from now on'",
            "用 'from now on' 替换 'henceforth'",
            0.90
        ),
        (
            r'\bparamount\b',
            FixType.REPLACE_WORD,
            "important",
            "Replace 'paramount' with 'important'",
            "用 'important' 替换 'paramount'",
            0.85
        ),
        (
            r'\bmultifaceted\b',
            FixType.REPLACE_WORD,
            "complex",
            "Replace 'multifaceted' with 'complex'",
            "用 'complex' 替换 'multifaceted'",
            0.85
        ),

        # === CONNECTOR SIMPLIFICATIONS ===
        # Formal connectors to simpler versions (at sentence start)
        # 正式连接词简化为更简单的版本（在句首）
        (
            r'^Furthermore,\s*',
            FixType.SIMPLIFY_CONNECTOR,
            "Also, ",
            "Replace 'Furthermore' with 'Also'",
            "用 'Also' 替换 'Furthermore'",
            0.80
        ),
        (
            r'^Moreover,\s*',
            FixType.SIMPLIFY_CONNECTOR,
            "Also, ",
            "Replace 'Moreover' with 'Also'",
            "用 'Also' 替换 'Moreover'",
            0.80
        ),
        (
            r'^Additionally,\s*',
            FixType.SIMPLIFY_CONNECTOR,
            "Also, ",
            "Replace 'Additionally' with 'Also'",
            "用 'Also' 替换 'Additionally'",
            0.80
        ),
        (
            r'^Consequently,\s*',
            FixType.SIMPLIFY_CONNECTOR,
            "So, ",
            "Replace 'Consequently' with 'So'",
            "用 'So' 替换 'Consequently'",
            0.80
        ),
        (
            r'^Nevertheless,\s*',
            FixType.SIMPLIFY_CONNECTOR,
            "Still, ",
            "Replace 'Nevertheless' with 'Still'",
            "用 'Still' 替换 'Nevertheless'",
            0.80
        ),
    ]

    def __init__(self):
        """Initialize with compiled patterns"""
        self.compiled_templates = []
        for pattern, fix_type, replacement, exp_en, exp_zh, confidence in self.TEMPLATES:
            compiled = re.compile(pattern, re.IGNORECASE if fix_type != FixType.SIMPLIFY_CONNECTOR else 0)
            self.compiled_templates.append(
                (compiled, pattern, fix_type, replacement, exp_en, exp_zh, confidence)
            )

    def detect_fixable_patterns(self, text: str) -> List[AutoFixMatch]:
        """
        Detect all patterns that can be auto-fixed
        检测所有可以自动修复的模式

        Args:
            text: Input text to scan

        Returns:
            List of AutoFixMatch objects
        """
        matches = []

        for compiled, pattern_str, fix_type, replacement, exp_en, exp_zh, confidence in self.compiled_templates:
            for match in compiled.finditer(text):
                # Generate the suggested fix
                # 生成建议的修复
                suggested = self._generate_fix(match.group(0), fix_type, replacement)

                matches.append(AutoFixMatch(
                    pattern_id=pattern_str[:30],
                    matched_text=match.group(0),
                    position=match.start(),
                    end_position=match.end(),
                    fix_type=fix_type,
                    suggested_fix=suggested,
                    explanation=exp_en,
                    explanation_zh=exp_zh,
                    confidence=confidence
                ))

        # Sort by position
        # 按位置排序
        matches.sort(key=lambda m: m.position)
        return matches

    def _generate_fix(self, matched: str, fix_type: FixType, replacement: str) -> str:
        """
        Generate the fixed text
        生成修复后的文本
        """
        if fix_type == FixType.DELETE_AND_CAPITALIZE:
            return ""  # Will be handled in apply_fixes
        elif fix_type in (FixType.REPLACE_PHRASE, FixType.REPLACE_WORD, FixType.SIMPLIFY_CONNECTOR):
            return replacement
        else:
            return replacement

    def preview_fixes(self, text: str, matches: List[AutoFixMatch] = None) -> AutoFixPreview:
        """
        Preview all fixes without applying them
        预览所有修复而不应用

        Args:
            text: Original text
            matches: Pre-detected matches (optional)

        Returns:
            AutoFixPreview showing before and after
        """
        if matches is None:
            matches = self.detect_fixable_patterns(text)

        if not matches:
            return AutoFixPreview(
                original_text=text,
                fixed_text=text,
                matches=[],
                total_fixes=0,
                risk_reduction_estimate=0
            )

        # Apply fixes in reverse order to preserve positions
        # 逆序应用修复以保持位置
        fixed_text = text
        for match in reversed(matches):
            fixed_text = self._apply_single_fix(fixed_text, match)

        # Estimate risk reduction (rough: 5-10 points per fix)
        # 估计风险降低（粗略：每个修复5-10分）
        high_confidence_fixes = sum(1 for m in matches if m.confidence >= 0.9)
        medium_confidence_fixes = sum(1 for m in matches if 0.8 <= m.confidence < 0.9)
        risk_reduction = (high_confidence_fixes * 8) + (medium_confidence_fixes * 5)

        return AutoFixPreview(
            original_text=text,
            fixed_text=fixed_text,
            matches=matches,
            total_fixes=len(matches),
            risk_reduction_estimate=min(50, risk_reduction)  # Cap at 50
        )

    def apply_fixes(
        self,
        text: str,
        matches: List[AutoFixMatch] = None,
        selected_indices: List[int] = None
    ) -> str:
        """
        Apply selected fixes to text
        将选定的修复应用到文本

        Args:
            text: Original text
            matches: Detected matches
            selected_indices: Which matches to apply (None = all)

        Returns:
            Fixed text
        """
        if matches is None:
            matches = self.detect_fixable_patterns(text)

        if not matches:
            return text

        # Filter to selected indices if specified
        # 如果指定则过滤到选定的索引
        if selected_indices is not None:
            matches = [matches[i] for i in selected_indices if i < len(matches)]

        # Apply fixes in reverse order
        # 逆序应用修复
        fixed_text = text
        for match in reversed(matches):
            fixed_text = self._apply_single_fix(fixed_text, match)

        return fixed_text

    def _apply_single_fix(self, text: str, match: AutoFixMatch) -> str:
        """
        Apply a single fix to text
        将单个修复应用到文本
        """
        before = text[:match.position]
        after = text[match.end_position:]

        if match.fix_type == FixType.DELETE_AND_CAPITALIZE:
            # Delete the phrase and capitalize the next word
            # 删除短语并将下一个词大写
            if after and after[0].isalpha():
                after = after[0].upper() + after[1:]
            return before + after

        else:
            # Simple replacement
            # 简单替换
            return before + match.suggested_fix + after

    def get_quick_fixes(self, text: str, max_fixes: int = 5) -> List[Dict]:
        """
        Get quick fix suggestions for UI display
        获取用于UI显示的快速修复建议

        Args:
            text: Input text
            max_fixes: Maximum number of fixes to return

        Returns:
            List of fix dictionaries for UI
        """
        matches = self.detect_fixable_patterns(text)[:max_fixes]

        return [
            {
                "original": m.matched_text,
                "replacement": m.suggested_fix if m.suggested_fix else "[DELETE]",
                "explanation": m.explanation,
                "explanation_zh": m.explanation_zh,
                "confidence": m.confidence,
                "position": m.position
            }
            for m in matches
        ]


# Convenience functions
# 便捷函数
def detect_autofix_patterns(text: str) -> List[AutoFixMatch]:
    """Detect patterns that can be auto-fixed"""
    return AutoFixTemplates().detect_fixable_patterns(text)


def preview_autofixes(text: str) -> AutoFixPreview:
    """Preview all auto-fixes"""
    return AutoFixTemplates().preview_fixes(text)


def apply_autofixes(text: str, selected_indices: List[int] = None) -> str:
    """Apply auto-fixes to text"""
    templates = AutoFixTemplates()
    matches = templates.detect_fixable_patterns(text)
    return templates.apply_fixes(text, matches, selected_indices)
