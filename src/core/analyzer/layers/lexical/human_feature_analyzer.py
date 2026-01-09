"""
Step 5.2: Human Feature Vocabulary Analysis
步骤5.2：人类特征词汇分析

Analyzes human academic writing feature coverage:
- Human academic verbs coverage
- Human adjectives coverage
- Human phrases occurrence
- Hedging language coverage
- Identifies injection points for human features

分析人类学术写作特征覆盖率：
- 人类学术动词覆盖率
- 人类形容词覆盖率
- 人类短语出现率
- 谨慎表述语言覆盖率
- 识别可注入人类特征的位置
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import Counter

from src.core.analyzer.layers.lexical.context_preparation import (
    LexicalContext,
    ParagraphLexicalInfo,
)

logger = logging.getLogger(__name__)


@dataclass
class CoverageStats:
    """
    Coverage statistics for a feature category
    特征类别的覆盖统计
    """
    category: str
    target_words: List[str]
    found_words: List[str]
    found_count: int
    total_words: int
    coverage_rate: float  # Percentage of document words
    target_rate: float  # Target coverage rate
    is_sufficient: bool


@dataclass
class InjectionPoint:
    """
    A potential point to inject human features
    可以注入人类特征的潜在位置
    """
    paragraph_index: int
    sentence_index: int
    sentence_text: str
    suggested_features: List[str]
    feature_type: str  # verb, adjective, phrase, hedging
    reason: str
    reason_zh: str


@dataclass
class HumanFeatureAnalysisResult:
    """
    Complete human feature analysis result
    完整的人类特征分析结果
    """
    # Coverage by category
    verb_coverage: CoverageStats
    adjective_coverage: CoverageStats
    phrase_coverage: CoverageStats
    hedging_coverage: CoverageStats

    # Overall score
    overall_human_score: int  # 0-100

    # Gaps and injection points
    feature_gaps: List[str]
    injection_points: List[InjectionPoint]

    # Per-paragraph analysis
    paragraph_scores: Dict[int, int]

    # Recommendations
    recommendations: List[str]
    recommendations_zh: List[str]


class HumanFeatureAnalyzer:
    """
    Step 5.2: Human Feature Vocabulary Analyzer
    步骤5.2：人类特征词汇分析器
    """

    def __init__(self):
        """Initialize the analyzer with feature database"""
        self.feature_db = self._load_feature_database()

    def _load_feature_database(self) -> Dict[str, Any]:
        """Load human feature database"""
        try:
            import json
            from pathlib import Path
            db_path = Path(__file__).parent.parent.parent.parent / "data" / "human_features.json"
            if db_path.exists():
                with open(db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load human features database: {e}")

        # Return default features
        return self._get_default_features()

    def _get_default_features(self) -> Dict[str, Any]:
        """Get default human features if database not found"""
        return {
            "verbs": {
                "high_frequency": {
                    "examine": {"weight": 95}, "argue": {"weight": 92},
                    "suggest": {"weight": 90}, "demonstrate": {"weight": 87},
                    "identify": {"weight": 84}, "analyze": {"weight": 88},
                    "investigate": {"weight": 88}, "observe": {"weight": 86},
                    "measure": {"weight": 85}, "compare": {"weight": 80},
                    "assess": {"weight": 84}, "evaluate": {"weight": 82},
                    "validate": {"weight": 82}, "determine": {"weight": 83},
                },
                "target_coverage": 0.15
            },
            "adjectives": {
                "high_frequency": {
                    "significant": {"weight": 98}, "empirical": {"weight": 92},
                    "specific": {"weight": 94}, "consistent": {"weight": 90},
                    "preliminary": {"weight": 85}, "quantitative": {"weight": 90},
                    "qualitative": {"weight": 90}, "limited": {"weight": 88},
                },
                "target_coverage": 0.10
            },
            "phrases": {
                "high_frequency": {
                    "results indicate": {"weight": 95},
                    "in contrast to": {"weight": 94},
                    "data suggest": {"weight": 89},
                    "consistent with": {"weight": 88},
                    "future research": {"weight": 87},
                },
                "target_coverage": 0.05
            },
            "hedging": {
                "markers": {
                    "may": {"weight": 90}, "might": {"weight": 85},
                    "could": {"weight": 85}, "suggests": {"weight": 90},
                    "appears": {"weight": 88}, "seems": {"weight": 85},
                    "likely": {"weight": 85}, "possibly": {"weight": 80},
                    "tend to": {"weight": 85}, "appear to": {"weight": 88},
                },
                "target_coverage": 0.08
            }
        }

    def analyze(self, context: LexicalContext) -> HumanFeatureAnalysisResult:
        """
        Analyze human feature vocabulary coverage
        分析人类特征词汇覆盖率

        Args:
            context: Prepared lexical context from Step 5.0

        Returns:
            HumanFeatureAnalysisResult with coverage statistics
        """
        logger.info("Step 5.2: Analyzing human feature vocabulary")

        # Analyze each category
        verb_coverage = self._analyze_verbs(context)
        adjective_coverage = self._analyze_adjectives(context)
        phrase_coverage = self._analyze_phrases(context)
        hedging_coverage = self._analyze_hedging(context)

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            verb_coverage, adjective_coverage, phrase_coverage, hedging_coverage
        )

        # Identify feature gaps
        feature_gaps = self._identify_gaps(
            verb_coverage, adjective_coverage, phrase_coverage, hedging_coverage
        )

        # Find injection points
        injection_points = self._find_injection_points(context, feature_gaps)

        # Calculate per-paragraph scores
        paragraph_scores = self._calculate_paragraph_scores(context)

        # Generate recommendations
        recommendations, recommendations_zh = self._generate_recommendations(
            verb_coverage, adjective_coverage, phrase_coverage, hedging_coverage,
            feature_gaps
        )

        result = HumanFeatureAnalysisResult(
            verb_coverage=verb_coverage,
            adjective_coverage=adjective_coverage,
            phrase_coverage=phrase_coverage,
            hedging_coverage=hedging_coverage,
            overall_human_score=overall_score,
            feature_gaps=feature_gaps,
            injection_points=injection_points,
            paragraph_scores=paragraph_scores,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
        )

        logger.info(
            f"Step 5.2 complete: Human score {overall_score}/100, "
            f"Verbs: {verb_coverage.coverage_rate:.1%}, "
            f"Adjectives: {adjective_coverage.coverage_rate:.1%}, "
            f"Hedging: {hedging_coverage.coverage_rate:.1%}"
        )

        return result

    def _analyze_verbs(self, context: LexicalContext) -> CoverageStats:
        """Analyze human verb coverage"""
        verb_data = self.feature_db.get("verbs", {})
        target_verbs = set(verb_data.get("high_frequency", {}).keys())
        target_rate = verb_data.get("target_coverage", 0.15)

        found_verbs = []
        found_count = 0

        for para in context.paragraphs:
            for word_lower in para.word_positions.keys():
                # Check verb forms (base, -s, -ed, -ing)
                base_form = self._get_verb_base(word_lower)
                if base_form in target_verbs or word_lower in target_verbs:
                    found_verbs.append(word_lower)
                    found_count += len(para.word_positions[word_lower])

        coverage_rate = found_count / context.total_words if context.total_words > 0 else 0

        return CoverageStats(
            category="verbs",
            target_words=list(target_verbs),
            found_words=list(set(found_verbs)),
            found_count=found_count,
            total_words=context.total_words,
            coverage_rate=coverage_rate,
            target_rate=target_rate,
            is_sufficient=coverage_rate >= target_rate,
        )

    def _analyze_adjectives(self, context: LexicalContext) -> CoverageStats:
        """Analyze human adjective coverage"""
        adj_data = self.feature_db.get("adjectives", {})
        target_adjs = set(adj_data.get("high_frequency", {}).keys())
        target_rate = adj_data.get("target_coverage", 0.10)

        found_adjs = []
        found_count = 0

        for para in context.paragraphs:
            for word_lower in para.word_positions.keys():
                if word_lower in target_adjs:
                    found_adjs.append(word_lower)
                    found_count += len(para.word_positions[word_lower])

        coverage_rate = found_count / context.total_words if context.total_words > 0 else 0

        return CoverageStats(
            category="adjectives",
            target_words=list(target_adjs),
            found_words=list(set(found_adjs)),
            found_count=found_count,
            total_words=context.total_words,
            coverage_rate=coverage_rate,
            target_rate=target_rate,
            is_sufficient=coverage_rate >= target_rate,
        )

    def _analyze_phrases(self, context: LexicalContext) -> CoverageStats:
        """Analyze human phrase occurrence"""
        phrase_data = self.feature_db.get("phrases", {})
        target_phrases = list(phrase_data.get("high_frequency", {}).keys())
        target_rate = phrase_data.get("target_coverage", 0.05)

        found_phrases = []
        found_count = 0

        # Compile patterns
        patterns = {
            phrase: re.compile(re.escape(phrase), re.IGNORECASE)
            for phrase in target_phrases
        }

        for para in context.paragraphs:
            for phrase, pattern in patterns.items():
                matches = pattern.findall(para.text)
                if matches:
                    found_phrases.append(phrase)
                    found_count += len(matches)

        # Calculate as phrase occurrences per 100 words
        coverage_rate = (found_count / context.total_words * 100) if context.total_words > 0 else 0

        return CoverageStats(
            category="phrases",
            target_words=target_phrases,
            found_words=list(set(found_phrases)),
            found_count=found_count,
            total_words=context.total_words,
            coverage_rate=coverage_rate / 100,  # Convert back to rate
            target_rate=target_rate,
            is_sufficient=coverage_rate / 100 >= target_rate,
        )

    def _analyze_hedging(self, context: LexicalContext) -> CoverageStats:
        """Analyze hedging language coverage"""
        hedging_data = self.feature_db.get("hedging", {})
        target_markers = set(hedging_data.get("markers", {}).keys())
        target_rate = hedging_data.get("target_coverage", 0.08)

        found_markers = []
        found_count = 0

        # Check both words and phrases
        phrase_markers = [m for m in target_markers if " " in m]
        word_markers = [m for m in target_markers if " " not in m]

        for para in context.paragraphs:
            # Check word markers
            for word_lower in para.word_positions.keys():
                if word_lower in word_markers:
                    found_markers.append(word_lower)
                    found_count += len(para.word_positions[word_lower])

            # Check phrase markers
            for phrase in phrase_markers:
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                matches = pattern.findall(para.text)
                if matches:
                    found_markers.append(phrase)
                    found_count += len(matches)

        coverage_rate = found_count / context.total_words if context.total_words > 0 else 0

        return CoverageStats(
            category="hedging",
            target_words=list(target_markers),
            found_words=list(set(found_markers)),
            found_count=found_count,
            total_words=context.total_words,
            coverage_rate=coverage_rate,
            target_rate=target_rate,
            is_sufficient=coverage_rate >= target_rate,
        )

    def _get_verb_base(self, word: str) -> str:
        """Get base form of a verb (simple heuristic)"""
        if word.endswith("ing"):
            base = word[:-3]
            if base.endswith("e"):
                return base
            return base + "e" if len(base) > 2 else word
        if word.endswith("ed"):
            return word[:-2] if word[-3] not in "aeiou" else word[:-1]
        if word.endswith("es"):
            return word[:-2]
        if word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        return word

    def _calculate_overall_score(
        self,
        verbs: CoverageStats,
        adjs: CoverageStats,
        phrases: CoverageStats,
        hedging: CoverageStats
    ) -> int:
        """Calculate overall human feature score (0-100)"""
        # Weight each category
        weights = {"verbs": 30, "adjectives": 25, "phrases": 20, "hedging": 25}

        score = 0
        for stats, weight in [
            (verbs, weights["verbs"]),
            (adjs, weights["adjectives"]),
            (phrases, weights["phrases"]),
            (hedging, weights["hedging"]),
        ]:
            # Score based on how close to target
            if stats.target_rate > 0:
                ratio = min(1.0, stats.coverage_rate / stats.target_rate)
                score += ratio * weight

        return int(score)

    def _identify_gaps(
        self,
        verbs: CoverageStats,
        adjs: CoverageStats,
        phrases: CoverageStats,
        hedging: CoverageStats
    ) -> List[str]:
        """Identify feature gaps"""
        gaps = []

        if not verbs.is_sufficient:
            missing = set(verbs.target_words) - set(verbs.found_words)
            gaps.append(f"verbs:{','.join(list(missing)[:5])}")

        if not adjs.is_sufficient:
            missing = set(adjs.target_words) - set(adjs.found_words)
            gaps.append(f"adjectives:{','.join(list(missing)[:5])}")

        if not phrases.is_sufficient:
            missing = set(phrases.target_words) - set(phrases.found_words)
            gaps.append(f"phrases:{','.join(list(missing)[:3])}")

        if not hedging.is_sufficient:
            missing = set(hedging.target_words) - set(hedging.found_words)
            gaps.append(f"hedging:{','.join(list(missing)[:5])}")

        return gaps

    def _find_injection_points(
        self,
        context: LexicalContext,
        feature_gaps: List[str]
    ) -> List[InjectionPoint]:
        """Find suitable points to inject human features"""
        injection_points = []

        # Parse gaps
        missing_verbs = []
        missing_adjs = []
        missing_phrases = []
        missing_hedging = []

        for gap in feature_gaps:
            if gap.startswith("verbs:"):
                missing_verbs = gap.split(":")[1].split(",")
            elif gap.startswith("adjectives:"):
                missing_adjs = gap.split(":")[1].split(",")
            elif gap.startswith("phrases:"):
                missing_phrases = gap.split(":")[1].split(",")
            elif gap.startswith("hedging:"):
                missing_hedging = gap.split(":")[1].split(",")

        global_sent_idx = 0
        for para in context.paragraphs:
            for sent_idx, sentence in enumerate(para.sentences):
                sentence_lower = sentence.lower()

                # Check for verb injection opportunities
                if missing_verbs and self._can_inject_verb(sentence_lower):
                    injection_points.append(InjectionPoint(
                        paragraph_index=para.index,
                        sentence_index=global_sent_idx,
                        sentence_text=sentence[:100],
                        suggested_features=missing_verbs[:3],
                        feature_type="verb",
                        reason="Sentence could use stronger academic verbs",
                        reason_zh="句子可以使用更强的学术动词",
                    ))

                # Check for hedging injection opportunities
                if missing_hedging and self._should_add_hedging(sentence_lower):
                    injection_points.append(InjectionPoint(
                        paragraph_index=para.index,
                        sentence_index=global_sent_idx,
                        sentence_text=sentence[:100],
                        suggested_features=missing_hedging[:3],
                        feature_type="hedging",
                        reason="Claim could benefit from hedging language",
                        reason_zh="陈述可以添加谨慎表述语言",
                    ))

                global_sent_idx += 1

            # Check for phrase injection at paragraph level
            if missing_phrases and len(para.sentences) >= 3:
                injection_points.append(InjectionPoint(
                    paragraph_index=para.index,
                    sentence_index=global_sent_idx - 1,  # Last sentence
                    sentence_text=para.sentences[-1][:100],
                    suggested_features=missing_phrases[:2],
                    feature_type="phrase",
                    reason="Paragraph could use academic transition phrases",
                    reason_zh="段落可以使用学术过渡短语",
                ))

        return injection_points[:20]  # Limit to top 20

    def _can_inject_verb(self, sentence: str) -> bool:
        """Check if sentence could benefit from academic verb"""
        # Look for weak verbs that could be replaced
        weak_verbs = ["is", "are", "was", "were", "has", "have", "shows", "uses"]
        return any(f" {v} " in f" {sentence} " for v in weak_verbs)

    def _should_add_hedging(self, sentence: str) -> bool:
        """Check if sentence should have hedging language"""
        # Claims without hedging
        claim_patterns = [
            r"\bis\b .{5,20}\b(the|a)\b",
            r"\bproves?\b",
            r"\bclearly\b",
            r"\bdefinitely\b",
            r"\bobviously\b",
        ]
        return any(re.search(p, sentence) for p in claim_patterns)

    def _calculate_paragraph_scores(self, context: LexicalContext) -> Dict[int, int]:
        """Calculate human feature score for each paragraph"""
        scores = {}

        verb_targets = set(self.feature_db.get("verbs", {}).get("high_frequency", {}).keys())
        adj_targets = set(self.feature_db.get("adjectives", {}).get("high_frequency", {}).keys())
        hedging_targets = set(self.feature_db.get("hedging", {}).get("markers", {}).keys())

        for para in context.paragraphs:
            score = 0
            words_found = 0

            for word_lower in para.word_positions.keys():
                base = self._get_verb_base(word_lower)
                if base in verb_targets or word_lower in verb_targets:
                    words_found += 1
                if word_lower in adj_targets:
                    words_found += 1
                if word_lower in hedging_targets:
                    words_found += 1

            # Score based on density of human features
            if para.word_count > 0:
                density = words_found / para.word_count
                score = min(100, int(density * 500))  # Scale to 0-100

            scores[para.index] = score

        return scores

    def _generate_recommendations(
        self,
        verbs: CoverageStats,
        adjs: CoverageStats,
        phrases: CoverageStats,
        hedging: CoverageStats,
        gaps: List[str]
    ) -> Tuple[List[str], List[str]]:
        """Generate recommendations"""
        recs = []
        recs_zh = []

        if not verbs.is_sufficient:
            missing = list(set(verbs.target_words) - set(verbs.found_words))[:5]
            recs.append(
                f"Increase academic verb usage (current: {verbs.coverage_rate:.1%}, "
                f"target: {verbs.target_rate:.0%}). Suggested: {', '.join(missing)}"
            )
            recs_zh.append(
                f"增加学术动词使用（当前：{verbs.coverage_rate:.1%}，"
                f"目标：{verbs.target_rate:.0%}）。建议：{', '.join(missing)}"
            )

        if not adjs.is_sufficient:
            missing = list(set(adjs.target_words) - set(adjs.found_words))[:5]
            recs.append(
                f"Add academic adjectives (current: {adjs.coverage_rate:.1%}, "
                f"target: {adjs.target_rate:.0%}). Suggested: {', '.join(missing)}"
            )
            recs_zh.append(
                f"添加学术形容词（当前：{adjs.coverage_rate:.1%}，"
                f"目标：{adjs.target_rate:.0%}）。建议：{', '.join(missing)}"
            )

        if not hedging.is_sufficient:
            missing = list(set(hedging.target_words) - set(hedging.found_words))[:5]
            recs.append(
                f"Add hedging language for claims (current: {hedging.coverage_rate:.1%}, "
                f"target: {hedging.target_rate:.0%}). Suggested: {', '.join(missing)}"
            )
            recs_zh.append(
                f"为论点添加谨慎表述语言（当前：{hedging.coverage_rate:.1%}，"
                f"目标：{hedging.target_rate:.0%}）。建议：{', '.join(missing)}"
            )

        if not phrases.is_sufficient:
            missing = list(set(phrases.target_words) - set(phrases.found_words))[:3]
            recs.append(
                f"Include academic phrases. Suggested: {', '.join(missing)}"
            )
            recs_zh.append(
                f"包含学术短语。建议：{', '.join(missing)}"
            )

        return recs, recs_zh

    def get_analysis_summary(self, result: HumanFeatureAnalysisResult) -> Dict[str, Any]:
        """Get summary for API response"""
        return {
            "overall_human_score": result.overall_human_score,
            "verb_coverage": {
                "rate": round(result.verb_coverage.coverage_rate * 100, 1),
                "target": round(result.verb_coverage.target_rate * 100, 0),
                "is_sufficient": result.verb_coverage.is_sufficient,
                "found": result.verb_coverage.found_words[:10],
            },
            "adjective_coverage": {
                "rate": round(result.adjective_coverage.coverage_rate * 100, 1),
                "target": round(result.adjective_coverage.target_rate * 100, 0),
                "is_sufficient": result.adjective_coverage.is_sufficient,
                "found": result.adjective_coverage.found_words[:10],
            },
            "phrase_coverage": {
                "rate": round(result.phrase_coverage.coverage_rate * 100, 1),
                "target": round(result.phrase_coverage.target_rate * 100, 0),
                "is_sufficient": result.phrase_coverage.is_sufficient,
                "found": result.phrase_coverage.found_words[:5],
            },
            "hedging_coverage": {
                "rate": round(result.hedging_coverage.coverage_rate * 100, 1),
                "target": round(result.hedging_coverage.target_rate * 100, 0),
                "is_sufficient": result.hedging_coverage.is_sufficient,
                "found": result.hedging_coverage.found_words[:10],
            },
            "feature_gaps": result.feature_gaps,
            "injection_points_count": len(result.injection_points),
            "injection_points_sample": [
                {
                    "para": ip.paragraph_index,
                    "type": ip.feature_type,
                    "suggested": ip.suggested_features,
                }
                for ip in result.injection_points[:5]
            ],
            "paragraph_scores": result.paragraph_scores,
            "recommendations": result.recommendations,
            "recommendations_zh": result.recommendations_zh,
        }
