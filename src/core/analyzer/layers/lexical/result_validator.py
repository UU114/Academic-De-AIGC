"""
Step 5.5: Rewrite Result Validation
步骤5.5：改写结果验证

Validates rewrite results:
- Semantic similarity validation (>=0.85)
- AIGC risk reduction assessment
- Human feature improvement assessment
- Locked term integrity check
- Academic norm verification

验证改写结果：
- 语义相似度验证（>=0.85）
- AIGC风险降低评估
- 人类特征提升评估
- 锁定词汇完整性检查
- 学术规范检查
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from src.core.analyzer.layers.lexical.context_preparation import LexicalContext
from src.core.analyzer.layers.lexical.fingerprint_detector import (
    EnhancedFingerprintDetector,
    FingerprintDetectionResult,
)
from src.core.analyzer.layers.lexical.human_feature_analyzer import (
    HumanFeatureAnalyzer,
    HumanFeatureAnalysisResult,
)
from src.core.analyzer.layers.lexical.paragraph_rewriter import (
    LLMRewriteResult,
    ParagraphRewriteResult,
)

logger = logging.getLogger(__name__)


@dataclass
class NormViolation:
    """An academic norm violation"""
    paragraph_index: int
    violation_type: str
    matched_text: str
    suggestion: str
    suggestion_zh: str


@dataclass
class ValidatedParagraph:
    """Validation result for a paragraph"""
    index: int
    original: str
    rewritten: str
    accepted: bool
    semantic_similarity: float
    aigc_risk_before: int
    aigc_risk_after: int
    risk_reduction_percent: float
    human_score_before: int
    human_score_after: int
    human_improvement_percent: float
    locked_terms_preserved: bool
    norm_violations: List[NormViolation]
    issues: List[str]


@dataclass
class QualityReport:
    """Overall quality report"""
    total_paragraphs: int
    paragraphs_improved: int
    paragraphs_unchanged: int
    paragraphs_failed: int
    overall_quality_score: int
    avg_semantic_similarity: float
    avg_risk_reduction: float
    avg_human_improvement: float
    all_locked_preserved: bool
    total_norm_violations: int


@dataclass
class ValidationResult:
    """Complete validation result"""
    overall_pass: bool
    semantic_similarity_pass: bool
    risk_reduction_pass: bool
    human_improvement_pass: bool
    locked_terms_pass: bool
    academic_norms_pass: bool
    paragraphs: List[ValidatedParagraph]
    quality_report: QualityReport
    recommendations: List[str]
    recommendations_zh: List[str]


class RewriteResultValidator:
    """
    Step 5.5: Rewrite Result Validator
    步骤5.5：改写结果验证器
    """

    # Validation thresholds
    SEMANTIC_SIMILARITY_THRESHOLD = 0.85
    RISK_REDUCTION_TARGET = 0.30  # 30% reduction
    HUMAN_IMPROVEMENT_TARGET = 0.10  # 10% improvement

    # Academic norm patterns to check
    ACADEMIC_NORM_CHECKS = {
        "no_contractions": {
            "pattern": r"\b(don't|won't|can't|isn't|aren't|wasn't|weren't|didn't|couldn't|shouldn't|wouldn't|haven't|hasn't|hadn't)\b",
            "level_threshold": 5,  # Only check for formal levels
            "message": "Academic writing should avoid contractions",
            "message_zh": "学术写作应避免缩写",
            "suggestion": "Expand to full form (e.g., 'do not' instead of 'don't')",
            "suggestion_zh": "展开为完整形式（如用 'do not' 代替 'don't'）",
        },
        "no_first_person": {
            "pattern": r"\b(I|we|my|our|us|me)\b",
            "level_threshold": 5,
            "message": "Academic writing should avoid first-person pronouns",
            "message_zh": "学术写作应避免第一人称代词",
            "suggestion": "Use 'this study', 'the analysis', or passive voice",
            "suggestion_zh": "使用 'this study'、'the analysis' 或被动语态",
        },
        "no_informal_language": {
            "pattern": r"\b(kind of|sort of|basically|actually|really|pretty much|a lot|stuff|things|got|gonna|wanna)\b",
            "level_threshold": 6,
            "message": "Avoid informal language in academic writing",
            "message_zh": "学术写作中应避免非正式语言",
            "suggestion": "Replace with more formal alternatives",
            "suggestion_zh": "用更正式的替代词替换",
        },
    }

    def __init__(self):
        """Initialize the validator"""
        self.fingerprint_detector = EnhancedFingerprintDetector()
        self.human_feature_analyzer = HumanFeatureAnalyzer()

    def validate(
        self,
        context: LexicalContext,
        original_fingerprints: FingerprintDetectionResult,
        original_human_features: Optional[HumanFeatureAnalysisResult],
        rewrite_result: LLMRewriteResult,
    ) -> ValidationResult:
        """
        Validate rewrite results
        验证改写结果

        Args:
            context: Original lexical context
            original_fingerprints: Original fingerprint detection
            original_human_features: Original human feature analysis
            rewrite_result: LLM rewrite results

        Returns:
            ValidationResult with all validation data
        """
        logger.info("Step 5.5: Validating rewrite results")

        validated_paragraphs: List[ValidatedParagraph] = []

        # Validate each paragraph
        for para_result in rewrite_result.paragraphs:
            validated = self._validate_paragraph(
                para_result,
                context,
                original_fingerprints,
                original_human_features,
            )
            validated_paragraphs.append(validated)

        # Calculate overall metrics
        quality_report = self._calculate_quality_report(validated_paragraphs)

        # Determine pass/fail for each criterion
        semantic_pass = quality_report.avg_semantic_similarity >= self.SEMANTIC_SIMILARITY_THRESHOLD
        risk_pass = quality_report.avg_risk_reduction >= self.RISK_REDUCTION_TARGET
        human_pass = quality_report.avg_human_improvement >= 0  # Any improvement is good
        locked_pass = quality_report.all_locked_preserved
        norms_pass = quality_report.total_norm_violations <= 2  # Allow some minor violations

        overall_pass = semantic_pass and locked_pass and (risk_pass or human_pass)

        # Generate recommendations
        recommendations, recommendations_zh = self._generate_recommendations(
            validated_paragraphs, quality_report, semantic_pass, risk_pass, human_pass, locked_pass
        )

        result = ValidationResult(
            overall_pass=overall_pass,
            semantic_similarity_pass=semantic_pass,
            risk_reduction_pass=risk_pass,
            human_improvement_pass=human_pass,
            locked_terms_pass=locked_pass,
            academic_norms_pass=norms_pass,
            paragraphs=validated_paragraphs,
            quality_report=quality_report,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
        )

        logger.info(
            f"Step 5.5 complete: Overall {'PASS' if overall_pass else 'FAIL'}, "
            f"Quality: {quality_report.overall_quality_score}/100"
        )

        return result

    def _validate_paragraph(
        self,
        para_result: ParagraphRewriteResult,
        context: LexicalContext,
        original_fingerprints: FingerprintDetectionResult,
        original_human_features: Optional[HumanFeatureAnalysisResult],
    ) -> ValidatedParagraph:
        """Validate a single paragraph"""
        issues: List[str] = []

        # Calculate semantic similarity (simple word overlap for now)
        similarity = self._calculate_semantic_similarity(
            para_result.original_text,
            para_result.rewritten_text,
        )

        # Get original risk for this paragraph
        orig_para_stats = original_fingerprints.paragraph_stats.get(para_result.paragraph_index)
        risk_before = orig_para_stats.total_risk_score if orig_para_stats else 0

        # Calculate new risk (re-detect fingerprints in rewritten text)
        risk_after = self._calculate_new_risk(para_result.rewritten_text)

        # Calculate risk reduction
        risk_reduction = 0.0
        if risk_before > 0:
            risk_reduction = (risk_before - risk_after) / risk_before

        # Get human feature scores
        human_before = 0
        human_after = 0
        if original_human_features:
            human_before = original_human_features.paragraph_scores.get(
                para_result.paragraph_index, 0
            )
        human_after = self._calculate_human_score(para_result.rewritten_text)

        human_improvement = 0.0
        if human_before > 0:
            human_improvement = (human_after - human_before) / human_before
        elif human_after > 0:
            human_improvement = 1.0

        # Check locked terms
        locked_preserved = self._verify_locked_terms(
            para_result.rewritten_text,
            context.locked_terms,
        )

        if not locked_preserved:
            issues.append("Some locked terms may have been modified")

        # Check academic norms
        norm_violations = self._check_academic_norms(
            para_result.rewritten_text,
            para_result.paragraph_index,
            context.colloquialism_level,
        )

        if norm_violations:
            issues.append(f"{len(norm_violations)} academic norm violation(s)")

        # Determine if accepted
        accepted = (
            similarity >= self.SEMANTIC_SIMILARITY_THRESHOLD and
            locked_preserved and
            len(issues) <= 2
        )

        if similarity < self.SEMANTIC_SIMILARITY_THRESHOLD:
            issues.append(f"Semantic similarity {similarity:.0%} below threshold {self.SEMANTIC_SIMILARITY_THRESHOLD:.0%}")

        return ValidatedParagraph(
            index=para_result.paragraph_index,
            original=para_result.original_text,
            rewritten=para_result.rewritten_text,
            accepted=accepted,
            semantic_similarity=similarity,
            aigc_risk_before=risk_before,
            aigc_risk_after=risk_after,
            risk_reduction_percent=risk_reduction * 100,
            human_score_before=human_before,
            human_score_after=human_after,
            human_improvement_percent=human_improvement * 100,
            locked_terms_preserved=locked_preserved,
            norm_violations=norm_violations,
            issues=issues,
        )

    def _calculate_semantic_similarity(self, original: str, rewritten: str) -> float:
        """
        Calculate semantic similarity between original and rewritten text
        Simple word overlap for now - production should use Sentence-BERT
        """
        # Tokenize
        orig_words = set(re.findall(r'\b[a-zA-Z]+\b', original.lower()))
        new_words = set(re.findall(r'\b[a-zA-Z]+\b', rewritten.lower()))

        if not orig_words:
            return 1.0

        # Jaccard similarity
        intersection = len(orig_words & new_words)
        union = len(orig_words | new_words)

        if union == 0:
            return 1.0

        jaccard = intersection / union

        # Length ratio factor
        len_ratio = min(len(rewritten), len(original)) / max(len(rewritten), len(original))

        # Combined score with length bonus
        similarity = (jaccard * 0.7) + (len_ratio * 0.3)

        # Boost for high overlap
        if jaccard > 0.6:
            similarity = min(1.0, similarity + 0.1)

        return min(1.0, similarity)

    def _calculate_new_risk(self, text: str) -> int:
        """Calculate AIGC risk score for rewritten text"""
        # Quick fingerprint check
        risk = 0

        text_lower = text.lower()

        # Check Type A words
        for word in self.fingerprint_detector.TYPE_A_FINGERPRINTS:
            if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                risk += 40

        # Check Type B words (reduced weight)
        for word in self.fingerprint_detector.TYPE_B_FINGERPRINTS:
            if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                risk += 15

        # Check phrases
        for phrase in self.fingerprint_detector.FINGERPRINT_PHRASES:
            if phrase.lower() in text_lower:
                risk += 25

        return risk

    def _calculate_human_score(self, text: str) -> int:
        """Calculate human feature score for text"""
        score = 0

        text_lower = text.lower()

        # Check for human verbs
        human_verbs = ["examine", "argue", "suggest", "demonstrate", "identify",
                       "analyze", "investigate", "observe", "assess", "evaluate"]
        for verb in human_verbs:
            if re.search(r'\b' + verb, text_lower):
                score += 5

        # Check for hedging
        hedging = ["may", "might", "could", "suggests", "appears", "seems", "likely"]
        for h in hedging:
            if re.search(r'\b' + h + r'\b', text_lower):
                score += 3

        # Check for academic adjectives
        adjs = ["significant", "empirical", "specific", "consistent", "preliminary"]
        for adj in adjs:
            if adj in text_lower:
                score += 3

        return min(100, score)

    def _verify_locked_terms(self, text: str, locked_terms: List[str]) -> bool:
        """Verify all locked terms are present in text"""
        text_lower = text.lower()
        for term in locked_terms:
            if term.lower() not in text_lower:
                return False
        return True

    def _check_academic_norms(
        self,
        text: str,
        para_index: int,
        colloquialism_level: int,
    ) -> List[NormViolation]:
        """Check for academic norm violations"""
        violations: List[NormViolation] = []

        for check_name, check_data in self.ACADEMIC_NORM_CHECKS.items():
            # Only check if colloquialism level is formal enough
            if colloquialism_level > check_data["level_threshold"]:
                continue

            pattern = re.compile(check_data["pattern"], re.IGNORECASE)
            matches = pattern.findall(text)

            for match in matches:
                violations.append(NormViolation(
                    paragraph_index=para_index,
                    violation_type=check_name,
                    matched_text=match if isinstance(match, str) else match[0],
                    suggestion=check_data["suggestion"],
                    suggestion_zh=check_data["suggestion_zh"],
                ))

        return violations

    def _calculate_quality_report(
        self,
        paragraphs: List[ValidatedParagraph]
    ) -> QualityReport:
        """Calculate overall quality report"""
        if not paragraphs:
            return QualityReport(
                total_paragraphs=0,
                paragraphs_improved=0,
                paragraphs_unchanged=0,
                paragraphs_failed=0,
                overall_quality_score=0,
                avg_semantic_similarity=0,
                avg_risk_reduction=0,
                avg_human_improvement=0,
                all_locked_preserved=True,
                total_norm_violations=0,
            )

        improved = sum(1 for p in paragraphs if p.risk_reduction_percent > 10)
        unchanged = sum(1 for p in paragraphs if p.original == p.rewritten)
        failed = sum(1 for p in paragraphs if not p.accepted)

        avg_similarity = sum(p.semantic_similarity for p in paragraphs) / len(paragraphs)
        avg_risk_reduction = sum(p.risk_reduction_percent for p in paragraphs) / len(paragraphs) / 100
        avg_human_improvement = sum(p.human_improvement_percent for p in paragraphs) / len(paragraphs) / 100

        all_preserved = all(p.locked_terms_preserved for p in paragraphs)
        total_violations = sum(len(p.norm_violations) for p in paragraphs)

        # Calculate overall quality score
        quality_score = 0
        quality_score += min(30, int(avg_similarity * 30))  # Max 30 for similarity
        quality_score += min(30, int(avg_risk_reduction * 100))  # Max 30 for risk reduction
        quality_score += min(20, int(avg_human_improvement * 100))  # Max 20 for human improvement
        quality_score += 10 if all_preserved else 0  # 10 for locked terms
        quality_score += 10 if total_violations <= 2 else 0  # 10 for norms

        return QualityReport(
            total_paragraphs=len(paragraphs),
            paragraphs_improved=improved,
            paragraphs_unchanged=unchanged,
            paragraphs_failed=failed,
            overall_quality_score=quality_score,
            avg_semantic_similarity=avg_similarity,
            avg_risk_reduction=avg_risk_reduction,
            avg_human_improvement=avg_human_improvement,
            all_locked_preserved=all_preserved,
            total_norm_violations=total_violations,
        )

    def _generate_recommendations(
        self,
        paragraphs: List[ValidatedParagraph],
        report: QualityReport,
        semantic_pass: bool,
        risk_pass: bool,
        human_pass: bool,
        locked_pass: bool,
    ) -> Tuple[List[str], List[str]]:
        """Generate recommendations based on validation"""
        recs = []
        recs_zh = []

        if not semantic_pass:
            recs.append(
                f"Semantic similarity ({report.avg_semantic_similarity:.0%}) below threshold. "
                f"Review paragraphs with similarity < 85%"
            )
            recs_zh.append(
                f"语义相似度（{report.avg_semantic_similarity:.0%}）低于阈值。"
                f"审查相似度 < 85% 的段落"
            )

        if not locked_pass:
            not_preserved = [p.index for p in paragraphs if not p.locked_terms_preserved]
            recs.append(
                f"Locked terms modified in paragraph(s) {not_preserved}. "
                f"Restore original terms."
            )
            recs_zh.append(
                f"段落 {not_preserved} 中的锁定词汇被修改。恢复原始词汇。"
            )

        if risk_pass:
            recs.append(
                f"AIGC risk reduced by {report.avg_risk_reduction:.0%} on average"
            )
            recs_zh.append(
                f"AIGC风险平均降低 {report.avg_risk_reduction:.0%}"
            )

        if report.total_norm_violations > 0:
            recs.append(
                f"{report.total_norm_violations} academic norm violation(s) detected. "
                f"Consider fixing for formal academic writing."
            )
            recs_zh.append(
                f"检测到 {report.total_norm_violations} 个学术规范问题。"
                f"建议修复以符合正式学术写作规范。"
            )

        # Success summary
        if report.paragraphs_improved > 0:
            recs.append(
                f"{report.paragraphs_improved}/{report.total_paragraphs} paragraph(s) improved"
            )
            recs_zh.append(
                f"{report.paragraphs_improved}/{report.total_paragraphs} 个段落已改进"
            )

        return recs, recs_zh

    def get_validation_summary(self, result: ValidationResult) -> Dict[str, Any]:
        """Get summary for API response"""
        return {
            "overall_pass": result.overall_pass,
            "checks": {
                "semantic_similarity": result.semantic_similarity_pass,
                "risk_reduction": result.risk_reduction_pass,
                "human_improvement": result.human_improvement_pass,
                "locked_terms": result.locked_terms_pass,
                "academic_norms": result.academic_norms_pass,
            },
            "quality_report": {
                "total_paragraphs": result.quality_report.total_paragraphs,
                "paragraphs_improved": result.quality_report.paragraphs_improved,
                "paragraphs_failed": result.quality_report.paragraphs_failed,
                "overall_score": result.quality_report.overall_quality_score,
                "avg_semantic_similarity": round(result.quality_report.avg_semantic_similarity * 100, 1),
                "avg_risk_reduction": round(result.quality_report.avg_risk_reduction * 100, 1),
                "avg_human_improvement": round(result.quality_report.avg_human_improvement * 100, 1),
                "all_locked_preserved": result.quality_report.all_locked_preserved,
                "total_norm_violations": result.quality_report.total_norm_violations,
            },
            "paragraphs": [
                {
                    "index": p.index,
                    "accepted": p.accepted,
                    "semantic_similarity": round(p.semantic_similarity * 100, 1),
                    "risk_before": p.aigc_risk_before,
                    "risk_after": p.aigc_risk_after,
                    "risk_reduction": round(p.risk_reduction_percent, 1),
                    "human_before": p.human_score_before,
                    "human_after": p.human_score_after,
                    "human_improvement": round(p.human_improvement_percent, 1),
                    "locked_preserved": p.locked_terms_preserved,
                    "norm_violations": len(p.norm_violations),
                    "issues": p.issues,
                }
                for p in result.paragraphs
            ],
            "recommendations": result.recommendations,
            "recommendations_zh": result.recommendations_zh,
        }
