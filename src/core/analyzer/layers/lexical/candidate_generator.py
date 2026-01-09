"""
Step 5.3: Replacement Candidate Generation
步骤5.3：替换候选生成

Generates replacement candidates for AIGC fingerprint words:
- Context-aware replacement suggestions
- Colloquialism level adaptation
- Prioritizes human feature words
- Rule-based suggestions (Track B)

为AIGC指纹词生成替换候选：
- 上下文感知的替换建议
- 口语化等级适配
- 优先选择人类特征词
- 规则建议（轨道B）
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from src.core.analyzer.layers.lexical.context_preparation import LexicalContext
from src.core.analyzer.layers.lexical.fingerprint_detector import (
    FingerprintDetectionResult,
    FingerprintMatch,
    FingerprintType,
)
from src.core.analyzer.layers.lexical.human_feature_analyzer import (
    HumanFeatureAnalysisResult,
)

logger = logging.getLogger(__name__)


@dataclass
class CandidateOption:
    """
    A single replacement candidate option
    单个替换候选选项
    """
    replacement: str
    is_human_feature: bool
    colloquialism_level: str  # academic, moderate, casual
    confidence: float  # 0-1
    reason: str
    reason_zh: str


@dataclass
class ReplacementCandidate:
    """
    Replacement candidate for a fingerprint
    指纹词的替换候选
    """
    original: str
    original_type: str  # type_a, type_b, phrase
    paragraph_index: int
    sentence_index: int
    context: str
    candidates: List[CandidateOption]
    recommended: Optional[CandidateOption] = None


@dataclass
class ReplacementCandidateResult:
    """
    Complete replacement candidate generation result
    完整的替换候选生成结果
    """
    candidates: List[ReplacementCandidate]
    total_replaceable: int
    type_a_candidates: int
    type_b_candidates: int
    phrase_candidates: int
    recommendations: List[str]
    recommendations_zh: List[str]


class ReplacementCandidateGenerator:
    """
    Step 5.3: Replacement Candidate Generator
    步骤5.3：替换候选生成器
    """

    # Replacement mapping for Type A words (must replace)
    TYPE_A_REPLACEMENTS = {
        "delve": {
            "academic": ["examine", "investigate", "explore", "analyze"],
            "moderate": ["study", "look at", "research"],
            "casual": ["look into", "check out", "dig into"],
            "human_feature": ["examine", "investigate", "analyze"],
        },
        "delves": {
            "academic": ["examines", "investigates", "explores"],
            "moderate": ["studies", "looks at", "researches"],
            "casual": ["looks into", "checks out"],
            "human_feature": ["examines", "investigates"],
        },
        "delving": {
            "academic": ["examining", "investigating", "exploring"],
            "moderate": ["studying", "looking at", "researching"],
            "casual": ["looking into", "checking out"],
            "human_feature": ["examining", "investigating"],
        },
        "tapestry": {
            "academic": ["combination", "synthesis", "array"],
            "moderate": ["mix", "collection", "range"],
            "casual": ["mix", "blend", "combo"],
            "human_feature": ["combination", "synthesis"],
        },
        "multifaceted": {
            "academic": ["complex", "diverse", "varied"],
            "moderate": ["complex", "varied", "diverse"],
            "casual": ["complex", "mixed"],
            "human_feature": ["complex", "diverse"],
        },
        "pivotal": {
            "academic": ["essential", "critical", "central"],
            "moderate": ["key", "important", "central"],
            "casual": ["key", "important", "main"],
            "human_feature": ["essential", "critical"],
        },
        "realm": {
            "academic": ["domain", "field", "area"],
            "moderate": ["area", "field", "space"],
            "casual": ["area", "space"],
            "human_feature": ["domain", "field"],
        },
        "realms": {
            "academic": ["domains", "fields", "areas"],
            "moderate": ["areas", "fields", "spaces"],
            "casual": ["areas", "spaces"],
            "human_feature": ["domains", "fields"],
        },
        "landscape": {
            "academic": ["environment", "context", "field"],
            "moderate": ["situation", "area", "scene"],
            "casual": ["scene", "situation"],
            "human_feature": ["environment", "context"],
        },
        "intricate": {
            "academic": ["complex", "detailed", "elaborate"],
            "moderate": ["complex", "detailed"],
            "casual": ["complex", "detailed"],
            "human_feature": ["complex", "detailed"],
        },
        "harness": {
            "academic": ["utilize", "employ", "apply"],
            "moderate": ["use", "apply", "take advantage of"],
            "casual": ["use", "take advantage of"],
            "human_feature": ["employ", "apply"],
        },
        "harnessing": {
            "academic": ["utilizing", "employing", "applying"],
            "moderate": ["using", "applying"],
            "casual": ["using"],
            "human_feature": ["employing", "applying"],
        },
        "underscore": {
            "academic": ["emphasize", "highlight", "stress"],
            "moderate": ["highlight", "show", "point out"],
            "casual": ["show", "point out"],
            "human_feature": ["emphasize", "highlight"],
        },
        "underscores": {
            "academic": ["emphasizes", "highlights", "stresses"],
            "moderate": ["highlights", "shows", "points out"],
            "casual": ["shows", "points out"],
            "human_feature": ["emphasizes", "highlights"],
        },
        "unveil": {
            "academic": ["reveal", "present", "disclose"],
            "moderate": ["reveal", "show", "present"],
            "casual": ["show", "reveal"],
            "human_feature": ["reveal", "present"],
        },
        "paramount": {
            "academic": ["essential", "critical", "primary"],
            "moderate": ["most important", "key", "main"],
            "casual": ["most important", "key"],
            "human_feature": ["essential", "critical"],
        },
        "plethora": {
            "academic": ["abundance", "multitude", "variety"],
            "moderate": ["many", "numerous", "variety"],
            "casual": ["lots of", "many"],
            "human_feature": ["abundance", "variety"],
        },
        "myriad": {
            "academic": ["numerous", "countless", "many"],
            "moderate": ["many", "numerous", "various"],
            "casual": ["many", "lots of"],
            "human_feature": ["numerous"],
        },
        "inextricably": {
            "academic": ["closely", "deeply", "fundamentally"],
            "moderate": ["closely", "deeply"],
            "casual": ["closely", "tightly"],
            "human_feature": ["closely", "fundamentally"],
        },
        "cornerstone": {
            "academic": ["foundation", "basis", "core"],
            "moderate": ["foundation", "base", "key element"],
            "casual": ["base", "foundation"],
            "human_feature": ["foundation", "basis"],
        },
    }

    # Replacement mapping for Type B words (reduce density)
    TYPE_B_REPLACEMENTS = {
        "comprehensive": {
            "academic": ["thorough", "complete", "extensive"],
            "moderate": ["full", "complete", "detailed"],
            "casual": ["full", "complete"],
            "human_feature": ["thorough", "extensive"],
        },
        "robust": {
            "academic": ["strong", "resilient", "reliable"],
            "moderate": ["strong", "solid", "reliable"],
            "casual": ["strong", "solid"],
            "human_feature": ["strong", "reliable"],
        },
        "leverage": {
            "academic": ["employ", "use", "apply"],
            "moderate": ["use", "apply", "build on"],
            "casual": ["use", "take advantage of"],
            "human_feature": ["employ", "apply"],
        },
        "leveraging": {
            "academic": ["employing", "using", "applying"],
            "moderate": ["using", "applying"],
            "casual": ["using"],
            "human_feature": ["employing", "applying"],
        },
        "facilitate": {
            "academic": ["enable", "support", "assist"],
            "moderate": ["help", "enable", "support"],
            "casual": ["help", "make easier"],
            "human_feature": ["enable", "support"],
        },
        "facilitates": {
            "academic": ["enables", "supports", "assists"],
            "moderate": ["helps", "enables", "supports"],
            "casual": ["helps", "makes easier"],
            "human_feature": ["enables", "supports"],
        },
        "utilize": {
            "academic": ["employ", "use", "apply"],
            "moderate": ["use", "apply"],
            "casual": ["use"],
            "human_feature": ["employ", "apply"],
        },
        "utilizes": {
            "academic": ["employs", "uses", "applies"],
            "moderate": ["uses", "applies"],
            "casual": ["uses"],
            "human_feature": ["employs", "applies"],
        },
        "utilizing": {
            "academic": ["employing", "using", "applying"],
            "moderate": ["using", "applying"],
            "casual": ["using"],
            "human_feature": ["employing", "applying"],
        },
        "crucial": {
            "academic": ["essential", "critical", "vital"],
            "moderate": ["important", "key", "essential"],
            "casual": ["important", "key"],
            "human_feature": ["essential", "critical"],
        },
        "holistic": {
            "academic": ["integrated", "complete", "overall"],
            "moderate": ["complete", "full", "overall"],
            "casual": ["complete", "full"],
            "human_feature": ["integrated", "complete"],
        },
        "seamless": {
            "academic": ["smooth", "integrated", "unified"],
            "moderate": ["smooth", "easy", "simple"],
            "casual": ["smooth", "easy"],
            "human_feature": ["smooth", "integrated"],
        },
        "furthermore": {
            "academic": ["additionally", "also", "moreover"],
            "moderate": ["also", "and", "plus"],
            "casual": ["also", "and"],
            "human_feature": ["additionally"],
        },
        "moreover": {
            "academic": ["additionally", "also", "further"],
            "moderate": ["also", "and", "plus"],
            "casual": ["also", "and"],
            "human_feature": ["additionally", "further"],
        },
        "subsequently": {
            "academic": ["thereafter", "later", "following this"],
            "moderate": ["then", "later", "after that"],
            "casual": ["then", "after that"],
            "human_feature": ["thereafter", "later"],
        },
        "foster": {
            "academic": ["promote", "encourage", "cultivate"],
            "moderate": ["encourage", "support", "help"],
            "casual": ["help", "support"],
            "human_feature": ["promote", "encourage"],
        },
        "nuanced": {
            "academic": ["subtle", "detailed", "refined"],
            "moderate": ["subtle", "detailed"],
            "casual": ["subtle", "detailed"],
            "human_feature": ["subtle", "detailed"],
        },
    }

    # Replacement mapping for phrases
    PHRASE_REPLACEMENTS = {
        "plays a crucial role": {
            "academic": "is essential to",
            "moderate": "is important for",
            "casual": "matters for",
        },
        "plays a pivotal role": {
            "academic": "is central to",
            "moderate": "is key to",
            "casual": "is really important for",
        },
        "it is important to note": {
            "academic": "notably",
            "moderate": "note that",
            "casual": "note that",
        },
        "it is worth noting": {
            "academic": "notably",
            "moderate": "it's worth noting",
            "casual": "worth noting",
        },
        "in the realm of": {
            "academic": "within",
            "moderate": "in",
            "casual": "in",
        },
        "a plethora of": {
            "academic": "numerous",
            "moderate": "many",
            "casual": "lots of",
        },
        "a myriad of": {
            "academic": "numerous",
            "moderate": "many",
            "casual": "lots of",
        },
        "in conclusion": {
            "academic": "to conclude",
            "moderate": "finally",
            "casual": "finally",
        },
        "in summary": {
            "academic": "overall",
            "moderate": "to sum up",
            "casual": "so",
        },
        "holistic approach": {
            "academic": "integrated approach",
            "moderate": "complete approach",
            "casual": "full approach",
        },
        "comprehensive approach": {
            "academic": "thorough approach",
            "moderate": "complete approach",
            "casual": "full approach",
        },
        "pave the way": {
            "academic": "enable",
            "moderate": "allow",
            "casual": "make possible",
        },
        "shed light on": {
            "academic": "clarify",
            "moderate": "explain",
            "casual": "explain",
        },
        "ever-evolving": {
            "academic": "continuously changing",
            "moderate": "changing",
            "casual": "changing",
        },
        "game-changer": {
            "academic": "significant development",
            "moderate": "major change",
            "casual": "big change",
        },
    }

    def __init__(self):
        """Initialize the candidate generator"""
        pass

    def generate(
        self,
        context: LexicalContext,
        fingerprint_result: FingerprintDetectionResult,
        human_feature_result: Optional[HumanFeatureAnalysisResult] = None,
    ) -> ReplacementCandidateResult:
        """
        Generate replacement candidates for detected fingerprints
        为检测到的指纹生成替换候选

        Args:
            context: Lexical context
            fingerprint_result: Fingerprint detection result from Step 5.1
            human_feature_result: Human feature analysis result from Step 5.2 (optional)

        Returns:
            ReplacementCandidateResult with all candidates
        """
        logger.info("Step 5.3: Generating replacement candidates")

        candidates: List[ReplacementCandidate] = []
        style_level = self._get_style_level(context.colloquialism_level)

        # Generate candidates for Type A fingerprints (must replace)
        for match in fingerprint_result.type_a_matches:
            candidate = self._generate_candidate(
                match, FingerprintType.TYPE_A, style_level, context
            )
            if candidate:
                candidates.append(candidate)

        # Generate candidates for Type B fingerprints (reduce density)
        for match in fingerprint_result.type_b_matches:
            candidate = self._generate_candidate(
                match, FingerprintType.TYPE_B, style_level, context
            )
            if candidate:
                candidates.append(candidate)

        # Generate candidates for phrase fingerprints
        for match in fingerprint_result.phrase_matches:
            candidate = self._generate_phrase_candidate(
                match, style_level, context
            )
            if candidate:
                candidates.append(candidate)

        # Generate recommendations
        recommendations, recommendations_zh = self._generate_recommendations(
            candidates, fingerprint_result
        )

        result = ReplacementCandidateResult(
            candidates=candidates,
            total_replaceable=len(candidates),
            type_a_candidates=len([c for c in candidates if c.original_type == "type_a"]),
            type_b_candidates=len([c for c in candidates if c.original_type == "type_b"]),
            phrase_candidates=len([c for c in candidates if c.original_type == "phrase"]),
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
        )

        logger.info(
            f"Step 5.3 complete: Generated {len(candidates)} replacement candidates"
        )

        return result

    def _get_style_level(self, colloquialism_level: int) -> str:
        """Map colloquialism level to style category"""
        if colloquialism_level <= 2:
            return "academic"
        elif colloquialism_level <= 6:
            return "moderate"
        else:
            return "casual"

    def _generate_candidate(
        self,
        match: FingerprintMatch,
        fp_type: FingerprintType,
        style_level: str,
        context: LexicalContext,
    ) -> Optional[ReplacementCandidate]:
        """Generate replacement candidate for a word fingerprint"""
        word_lower = match.word.lower()

        # Get replacement mapping
        if fp_type == FingerprintType.TYPE_A:
            replacements = self.TYPE_A_REPLACEMENTS.get(word_lower, {})
        else:
            replacements = self.TYPE_B_REPLACEMENTS.get(word_lower, {})

        if not replacements:
            return None

        # Generate candidate options
        options: List[CandidateOption] = []

        # Add style-appropriate replacements
        style_replacements = replacements.get(style_level, [])
        human_feature_replacements = replacements.get("human_feature", [])

        for i, rep in enumerate(style_replacements[:4]):
            is_human = rep in human_feature_replacements
            options.append(CandidateOption(
                replacement=self._match_case(rep, match.word),
                is_human_feature=is_human,
                colloquialism_level=style_level,
                confidence=0.9 - (i * 0.1),
                reason=f"Style-appropriate replacement ({style_level})" +
                       (" [Human feature]" if is_human else ""),
                reason_zh=f"风格适配替换（{style_level}）" +
                          ("【人类特征】" if is_human else ""),
            ))

        if not options:
            return None

        # Select recommended option (prefer human feature)
        recommended = next(
            (opt for opt in options if opt.is_human_feature),
            options[0]
        )

        return ReplacementCandidate(
            original=match.word,
            original_type=fp_type.value,
            paragraph_index=match.paragraph_index,
            sentence_index=match.sentence_index,
            context=match.context,
            candidates=options,
            recommended=recommended,
        )

    def _generate_phrase_candidate(
        self,
        match: FingerprintMatch,
        style_level: str,
        context: LexicalContext,
    ) -> Optional[ReplacementCandidate]:
        """Generate replacement candidate for a phrase fingerprint"""
        phrase_lower = match.word.lower()

        # Find matching phrase replacement
        replacement = None
        for phrase, replacements in self.PHRASE_REPLACEMENTS.items():
            if phrase.lower() in phrase_lower or phrase_lower in phrase.lower():
                replacement = replacements.get(style_level)
                break

        if not replacement:
            return None

        options = [CandidateOption(
            replacement=self._match_case(replacement, match.word),
            is_human_feature=False,
            colloquialism_level=style_level,
            confidence=0.85,
            reason=f"Phrase replacement ({style_level})",
            reason_zh=f"短语替换（{style_level}）",
        )]

        return ReplacementCandidate(
            original=match.word,
            original_type="phrase",
            paragraph_index=match.paragraph_index,
            sentence_index=match.sentence_index,
            context=match.context,
            candidates=options,
            recommended=options[0],
        )

    def _match_case(self, replacement: str, original: str) -> str:
        """Match the case of replacement to original"""
        if original[0].isupper():
            return replacement.capitalize()
        if original.isupper():
            return replacement.upper()
        return replacement

    def _generate_recommendations(
        self,
        candidates: List[ReplacementCandidate],
        fingerprint_result: FingerprintDetectionResult,
    ) -> Tuple[List[str], List[str]]:
        """Generate recommendations for replacement"""
        recs = []
        recs_zh = []

        type_a_count = len([c for c in candidates if c.original_type == "type_a"])
        type_b_count = len([c for c in candidates if c.original_type == "type_b"])
        phrase_count = len([c for c in candidates if c.original_type == "phrase"])

        if type_a_count > 0:
            recs.append(
                f"PRIORITY: Replace {type_a_count} Type A fingerprint(s) - "
                f"these are strong AI indicators"
            )
            recs_zh.append(
                f"优先：替换 {type_a_count} 个Type A指纹 - 这些是强AI指标"
            )

        if type_b_count > 0:
            recs.append(
                f"Replace or vary {type_b_count} Type B cliché(s) to reduce density"
            )
            recs_zh.append(
                f"替换或变化 {type_b_count} 个Type B陈词以降低密度"
            )

        if phrase_count > 0:
            recs.append(
                f"Rewrite {phrase_count} AI-typical phrase(s)"
            )
            recs_zh.append(
                f"改写 {phrase_count} 个AI典型短语"
            )

        # Add human feature recommendation
        human_feature_count = sum(
            1 for c in candidates
            if c.recommended and c.recommended.is_human_feature
        )
        if human_feature_count > 0:
            recs.append(
                f"{human_feature_count} replacement(s) will add human writing features"
            )
            recs_zh.append(
                f"{human_feature_count} 个替换将增加人类写作特征"
            )

        return recs, recs_zh

    def get_candidates_summary(
        self,
        result: ReplacementCandidateResult
    ) -> Dict[str, Any]:
        """Get summary for API response"""
        return {
            "total_replaceable": result.total_replaceable,
            "type_a_candidates": result.type_a_candidates,
            "type_b_candidates": result.type_b_candidates,
            "phrase_candidates": result.phrase_candidates,
            "candidates": [
                {
                    "original": c.original,
                    "type": c.original_type,
                    "paragraph": c.paragraph_index,
                    "recommended": c.recommended.replacement if c.recommended else None,
                    "is_human_feature": c.recommended.is_human_feature if c.recommended else False,
                    "options": [
                        {
                            "replacement": opt.replacement,
                            "is_human_feature": opt.is_human_feature,
                            "confidence": opt.confidence,
                        }
                        for opt in c.candidates[:3]
                    ],
                }
                for c in result.candidates
            ],
            "recommendations": result.recommendations,
            "recommendations_zh": result.recommendations_zh,
        }
