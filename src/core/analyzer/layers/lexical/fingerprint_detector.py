"""
Step 5.1: Enhanced AIGC Fingerprint Detection
步骤5.1：增强的AIGC指纹词检测

Enhanced fingerprint detection with:
- Type A: Dead Giveaway words (death sentence for AI detection)
- Type B: Academic Cliché words (high AI tendency)
- Type C: Fingerprint phrases
- Per-paragraph distribution statistics
- Locked term exclusion

增强的指纹检测，包括：
- Type A: 死证词（AI检测的死刑）
- Type B: 学术陈词（高AI倾向）
- Type C: 指纹短语
- 按段落的分布统计
- 锁定词汇排除
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

from src.core.analyzer.layers.lexical.context_preparation import (
    LexicalContext,
    ParagraphLexicalInfo,
)

logger = logging.getLogger(__name__)


class FingerprintType(Enum):
    """Fingerprint type classification"""
    TYPE_A = "type_a"  # Dead giveaways - must remove
    TYPE_B = "type_b"  # Academic clichés - reduce density
    PHRASE = "phrase"  # Fingerprint phrases


@dataclass
class FingerprintMatch:
    """
    A detected fingerprint match
    检测到的指纹匹配
    """
    word: str
    fingerprint_type: FingerprintType
    risk_weight: int
    paragraph_index: int
    sentence_index: int
    position_in_sentence: int
    context: str  # Surrounding text (50 chars before/after)
    is_locked: bool = False  # True if overlaps with locked term


@dataclass
class ParagraphFingerprintStats:
    """
    Fingerprint statistics for a paragraph
    段落的指纹统计
    """
    paragraph_index: int
    word_count: int
    type_a_count: int = 0
    type_b_count: int = 0
    phrase_count: int = 0
    total_risk_score: int = 0
    density: float = 0.0  # Fingerprints per 100 words
    risk_level: str = "low"
    matches: List[FingerprintMatch] = field(default_factory=list)


@dataclass
class FingerprintDetectionResult:
    """
    Complete fingerprint detection result
    完整的指纹检测结果
    """
    # Overall statistics
    total_fingerprints: int
    type_a_count: int
    type_b_count: int
    phrase_count: int
    overall_density: float
    overall_risk_score: int
    risk_level: str

    # Per-type matches
    type_a_matches: List[FingerprintMatch]
    type_b_matches: List[FingerprintMatch]
    phrase_matches: List[FingerprintMatch]

    # Per-paragraph statistics
    paragraph_stats: Dict[int, ParagraphFingerprintStats]

    # Locked terms excluded
    locked_terms_excluded: List[str]

    # Recommendations
    recommendations: List[str]
    recommendations_zh: List[str]


class EnhancedFingerprintDetector:
    """
    Step 5.1: Enhanced AIGC Fingerprint Detector
    步骤5.1：增强的AIGC指纹检测器
    """

    # Type A: Dead Giveaways (死证词) - Risk weight 35-45
    # These words are extremely rare in human writing but common in AI
    TYPE_A_FINGERPRINTS = {
        "delve": 99, "delves": 99, "delving": 99,
        "tapestry": 93, "tapestries": 93,
        "multifaceted": 94,
        "pivotal": 98,
        "realm": 95, "realms": 95,
        "landscape": 97, "landscapes": 97,
        "intricate": 96, "intricately": 96,
        "harness": 92, "harnessing": 92, "harnessed": 92,
        "underscore": 95, "underscores": 95, "underscoring": 95,
        "unveil": 87, "unveils": 87, "unveiling": 87, "unveiled": 87,
        "paramount": 88,
        "plethora": 82,
        "myriad": 85,
        "elucidate": 80, "elucidates": 80, "elucidating": 80,
        "inextricably": 90,
        "embark": 85, "embarks": 85, "embarking": 85,
        "beacon": 88,
        "spearhead": 84, "spearheading": 84,
        "epitomize": 82, "epitomizes": 82,
        "cornerstone": 86,
    }

    # Type B: Academic Clichés (学术陈词) - Risk weight 15-30
    # Common in AI writing, but also used by humans (reduce density)
    TYPE_B_FINGERPRINTS = {
        "comprehensive": 91, "comprehensively": 91,
        "robust": 89, "robustly": 89,
        "leverage": 90, "leveraging": 90, "leveraged": 90,
        "facilitate": 84, "facilitates": 84, "facilitating": 84,
        "utilize": 85, "utilizes": 85, "utilizing": 85, "utilized": 85,
        "seamless": 86, "seamlessly": 86,
        "holistic": 85, "holistically": 85,
        "transformative": 84,
        "crucial": 85, "crucially": 85,
        "innovative": 75, "innovatively": 75,
        "cutting-edge": 80,
        "state-of-the-art": 78,
        "groundbreaking": 82,
        "noteworthy": 75,
        "furthermore": 70,
        "moreover": 70,
        "additionally": 65,
        "consequently": 68,
        "subsequently": 72,
        "hence": 65,
        "thereby": 70,
        "nonetheless": 68,
        "whilst": 72,
        "synergy": 80, "synergistic": 80,
        "optimal": 75, "optimally": 75,
        "endeavor": 78, "endeavors": 78,
        "commence": 72, "commences": 72,
        "dynamic": 70, "dynamics": 70,
        "nuanced": 78, "nuance": 78, "nuances": 78,
        "foster": 75, "fosters": 75, "fostering": 75,
    }

    # Type C: Fingerprint Phrases - Risk weight 20-35
    FINGERPRINT_PHRASES = {
        "plays a crucial role": 92,
        "plays a pivotal role": 95,
        "plays an important role": 80,
        "plays a significant role": 82,
        "it is important to note": 96,
        "it is worth noting": 90,
        "it is crucial to": 88,
        "it is essential to": 85,
        "in the realm of": 30,
        "in the context of": 60,
        "a plethora of": 82,
        "a myriad of": 85,
        "not only but also": 94,
        "serves as a": 75,
        "acts as a catalyst": 85,
        "pave the way": 88,
        "shed light on": 88,
        "at the forefront": 80,
        "in conclusion": 99,
        "in summary": 85,
        "to summarize": 80,
        "ever-evolving": 95,
        "rapidly changing": 75,
        "game-changer": 90,
        "paradigm shift": 85,
        "holistic approach": 88,
        "comprehensive approach": 85,
        "intricate interplay": 92,
        "complex dynamics": 88,
        "vast majority": 75,
        "stark contrast": 78,
        "integral part": 80,
        "treasure trove": 85,
        "digital age": 72,
    }

    # Risk weight mapping
    RISK_WEIGHTS = {
        FingerprintType.TYPE_A: 40,  # High risk per match
        FingerprintType.TYPE_B: 20,  # Medium risk per match
        FingerprintType.PHRASE: 25,  # Medium-high risk per match
    }

    def __init__(self):
        """Initialize the fingerprint detector"""
        # Pre-compile phrase patterns for efficiency
        self.phrase_patterns = {
            phrase: re.compile(re.escape(phrase), re.IGNORECASE)
            for phrase in self.FINGERPRINT_PHRASES.keys()
        }

    def detect(self, context: LexicalContext) -> FingerprintDetectionResult:
        """
        Detect AIGC fingerprints in the document
        检测文档中的AIGC指纹

        Args:
            context: Prepared lexical context from Step 5.0

        Returns:
            FingerprintDetectionResult with all detections and statistics
        """
        logger.info("Step 5.1: Detecting AIGC fingerprints")

        type_a_matches: List[FingerprintMatch] = []
        type_b_matches: List[FingerprintMatch] = []
        phrase_matches: List[FingerprintMatch] = []
        paragraph_stats: Dict[int, ParagraphFingerprintStats] = {}
        locked_terms_excluded: List[str] = []

        # Process each paragraph
        for para in context.paragraphs:
            para_stats = ParagraphFingerprintStats(
                paragraph_index=para.index,
                word_count=para.word_count,
            )

            # Detect Type A fingerprints
            a_matches, a_excluded = self._detect_type_a(para, context)
            type_a_matches.extend(a_matches)
            locked_terms_excluded.extend(a_excluded)
            para_stats.type_a_count = len(a_matches)

            # Detect Type B fingerprints
            b_matches, b_excluded = self._detect_type_b(para, context)
            type_b_matches.extend(b_matches)
            locked_terms_excluded.extend(b_excluded)
            para_stats.type_b_count = len(b_matches)

            # Detect phrase fingerprints
            p_matches, p_excluded = self._detect_phrases(para, context)
            phrase_matches.extend(p_matches)
            locked_terms_excluded.extend(p_excluded)
            para_stats.phrase_count = len(p_matches)

            # Calculate paragraph statistics
            para_stats.matches = a_matches + b_matches + p_matches
            para_stats.total_risk_score = self._calculate_risk_score(para_stats)
            para_stats.density = self._calculate_density(para_stats)
            para_stats.risk_level = self._determine_risk_level(para_stats)

            paragraph_stats[para.index] = para_stats

        # Calculate overall statistics
        total_fingerprints = len(type_a_matches) + len(type_b_matches) + len(phrase_matches)
        overall_risk_score = sum(ps.total_risk_score for ps in paragraph_stats.values())
        overall_density = (total_fingerprints / context.total_words * 100) if context.total_words > 0 else 0
        risk_level = self._determine_overall_risk(total_fingerprints, len(type_a_matches), overall_density)

        # Generate recommendations
        recommendations, recommendations_zh = self._generate_recommendations(
            type_a_matches, type_b_matches, phrase_matches, paragraph_stats
        )

        result = FingerprintDetectionResult(
            total_fingerprints=total_fingerprints,
            type_a_count=len(type_a_matches),
            type_b_count=len(type_b_matches),
            phrase_count=len(phrase_matches),
            overall_density=overall_density,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            type_a_matches=type_a_matches,
            type_b_matches=type_b_matches,
            phrase_matches=phrase_matches,
            paragraph_stats=paragraph_stats,
            locked_terms_excluded=list(set(locked_terms_excluded)),
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
        )

        logger.info(
            f"Step 5.1 complete: {total_fingerprints} fingerprints detected, "
            f"Type A: {len(type_a_matches)}, Type B: {len(type_b_matches)}, "
            f"Phrases: {len(phrase_matches)}, Risk: {risk_level}"
        )

        return result

    def _detect_type_a(
        self,
        para: ParagraphLexicalInfo,
        context: LexicalContext
    ) -> Tuple[List[FingerprintMatch], List[str]]:
        """
        Detect Type A (Dead Giveaway) fingerprints
        检测Type A（死证词）指纹
        """
        matches = []
        excluded = []

        for word_lower, positions in para.word_positions.items():
            if word_lower in self.TYPE_A_FINGERPRINTS:
                # Check if locked
                if self._is_locked(word_lower, context):
                    excluded.append(word_lower)
                    continue

                for pos in positions:
                    match = FingerprintMatch(
                        word=pos.word,
                        fingerprint_type=FingerprintType.TYPE_A,
                        risk_weight=self.TYPE_A_FINGERPRINTS[word_lower],
                        paragraph_index=para.index,
                        sentence_index=pos.sentence_index,
                        position_in_sentence=pos.word_index,
                        context=self._get_context(para.text, pos.start_char, pos.end_char),
                        is_locked=False,
                    )
                    matches.append(match)

        return matches, excluded

    def _detect_type_b(
        self,
        para: ParagraphLexicalInfo,
        context: LexicalContext
    ) -> Tuple[List[FingerprintMatch], List[str]]:
        """
        Detect Type B (Academic Cliché) fingerprints
        检测Type B（学术陈词）指纹
        """
        matches = []
        excluded = []

        for word_lower, positions in para.word_positions.items():
            if word_lower in self.TYPE_B_FINGERPRINTS:
                # Check if locked
                if self._is_locked(word_lower, context):
                    excluded.append(word_lower)
                    continue

                for pos in positions:
                    match = FingerprintMatch(
                        word=pos.word,
                        fingerprint_type=FingerprintType.TYPE_B,
                        risk_weight=self.TYPE_B_FINGERPRINTS[word_lower],
                        paragraph_index=para.index,
                        sentence_index=pos.sentence_index,
                        position_in_sentence=pos.word_index,
                        context=self._get_context(para.text, pos.start_char, pos.end_char),
                        is_locked=False,
                    )
                    matches.append(match)

        return matches, excluded

    def _detect_phrases(
        self,
        para: ParagraphLexicalInfo,
        context: LexicalContext
    ) -> Tuple[List[FingerprintMatch], List[str]]:
        """
        Detect fingerprint phrases
        检测指纹短语
        """
        matches = []
        excluded = []

        para_text_lower = para.text.lower()

        for phrase, pattern in self.phrase_patterns.items():
            for match in pattern.finditer(para.text):
                matched_text = match.group(0)

                # Check if any part is locked
                if self._phrase_overlaps_locked(matched_text, context):
                    excluded.append(phrase)
                    continue

                # Find which sentence contains this phrase
                sent_idx = self._find_sentence_for_position(para, match.start())

                fp_match = FingerprintMatch(
                    word=matched_text,
                    fingerprint_type=FingerprintType.PHRASE,
                    risk_weight=self.FINGERPRINT_PHRASES[phrase],
                    paragraph_index=para.index,
                    sentence_index=sent_idx,
                    position_in_sentence=0,  # Phrase position
                    context=self._get_context(para.text, match.start(), match.end()),
                    is_locked=False,
                )
                matches.append(fp_match)

        return matches, excluded

    def _is_locked(self, word: str, context: LexicalContext) -> bool:
        """Check if a word is locked"""
        word_lower = word.lower()
        for locked in context.locked_terms_lower:
            if word_lower in locked or locked in word_lower:
                return True
        return False

    def _phrase_overlaps_locked(self, phrase: str, context: LexicalContext) -> bool:
        """Check if a phrase overlaps with any locked term"""
        phrase_lower = phrase.lower()
        for locked in context.locked_terms_lower:
            if locked in phrase_lower or phrase_lower in locked:
                return True
        return False

    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Get surrounding context for a match"""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return text[ctx_start:ctx_end]

    def _find_sentence_for_position(self, para: ParagraphLexicalInfo, char_pos: int) -> int:
        """Find which sentence index contains a character position"""
        current_pos = 0
        for i, sentence in enumerate(para.sentences):
            sentence_end = current_pos + len(sentence)
            if char_pos < sentence_end:
                return i
            current_pos = sentence_end + 1  # Account for space
        return len(para.sentences) - 1

    def _calculate_risk_score(self, stats: ParagraphFingerprintStats) -> int:
        """Calculate risk score for a paragraph"""
        score = 0
        score += stats.type_a_count * self.RISK_WEIGHTS[FingerprintType.TYPE_A]
        score += stats.type_b_count * self.RISK_WEIGHTS[FingerprintType.TYPE_B]
        score += stats.phrase_count * self.RISK_WEIGHTS[FingerprintType.PHRASE]
        return score

    def _calculate_density(self, stats: ParagraphFingerprintStats) -> float:
        """Calculate fingerprint density (per 100 words)"""
        if stats.word_count == 0:
            return 0.0
        total = stats.type_a_count + stats.type_b_count + stats.phrase_count
        return (total / stats.word_count) * 100

    def _determine_risk_level(self, stats: ParagraphFingerprintStats) -> str:
        """Determine risk level for a paragraph"""
        if stats.type_a_count > 0:
            return "critical"
        if stats.density > 5.0:
            return "high"
        if stats.density > 2.0:
            return "medium"
        if stats.type_b_count > 2 or stats.phrase_count > 1:
            return "medium"
        return "low"

    def _determine_overall_risk(
        self,
        total: int,
        type_a_count: int,
        density: float
    ) -> str:
        """Determine overall document risk level"""
        if type_a_count > 0:
            return "critical"
        if density > 3.0:
            return "high"
        if density > 1.5 or total > 10:
            return "medium"
        return "low"

    def _generate_recommendations(
        self,
        type_a: List[FingerprintMatch],
        type_b: List[FingerprintMatch],
        phrases: List[FingerprintMatch],
        para_stats: Dict[int, ParagraphFingerprintStats]
    ) -> Tuple[List[str], List[str]]:
        """Generate recommendations based on detection results"""
        recs = []
        recs_zh = []

        # Type A recommendations
        if type_a:
            unique_a = set(m.word.lower() for m in type_a)
            recs.append(
                f"CRITICAL: Remove {len(type_a)} Type A fingerprint word(s): "
                f"{', '.join(list(unique_a)[:5])}. These are strong AI indicators."
            )
            recs_zh.append(
                f"严重：移除 {len(type_a)} 个Type A指纹词：{', '.join(list(unique_a)[:5])}。"
                f"这些是强AI指标。"
            )

        # Type B recommendations
        if type_b:
            unique_b = set(m.word.lower() for m in type_b)
            recs.append(
                f"Replace or reduce {len(type_b)} Type B cliché word(s): "
                f"{', '.join(list(unique_b)[:5])}. Reduce density below 1%."
            )
            recs_zh.append(
                f"替换或减少 {len(type_b)} 个Type B陈词：{', '.join(list(unique_b)[:5])}。"
                f"将密度降至1%以下。"
            )

        # Phrase recommendations
        if phrases:
            unique_p = set(m.word.lower() for m in phrases)
            recs.append(
                f"Rewrite {len(phrases)} fingerprint phrase(s): "
                f"{', '.join(list(unique_p)[:3])}..."
            )
            recs_zh.append(
                f"改写 {len(phrases)} 个指纹短语：{', '.join(list(unique_p)[:3])}..."
            )

        # High-risk paragraph recommendations
        high_risk_paras = [
            idx for idx, stats in para_stats.items()
            if stats.risk_level in ("critical", "high")
        ]
        if high_risk_paras:
            recs.append(
                f"Focus on paragraph(s) {high_risk_paras[:5]} - highest fingerprint concentration."
            )
            recs_zh.append(
                f"重点关注段落 {high_risk_paras[:5]} - 指纹浓度最高。"
            )

        return recs, recs_zh

    def get_detection_summary(self, result: FingerprintDetectionResult) -> Dict[str, Any]:
        """
        Get a summary of detection results for API response
        获取检测结果摘要用于API响应
        """
        return {
            "total_fingerprints": result.total_fingerprints,
            "type_a_count": result.type_a_count,
            "type_b_count": result.type_b_count,
            "phrase_count": result.phrase_count,
            "overall_density": round(result.overall_density, 2),
            "overall_risk_score": result.overall_risk_score,
            "risk_level": result.risk_level,
            "locked_terms_excluded": result.locked_terms_excluded,
            "type_a_words": list(set(m.word for m in result.type_a_matches)),
            "type_b_words": list(set(m.word for m in result.type_b_matches))[:10],
            "phrase_samples": [m.word for m in result.phrase_matches[:5]],
            "paragraph_risk_levels": {
                idx: stats.risk_level
                for idx, stats in result.paragraph_stats.items()
            },
            "recommendations": result.recommendations,
            "recommendations_zh": result.recommendations_zh,
        }
