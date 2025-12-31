"""
Quality gate module - multi-layer validation
质量门控模块 - 多层验证
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from src.config import get_settings
from src.core.validator.semantic import SemanticValidator
from src.core.analyzer.scorer import RiskScorer
from src.core.preprocessor.term_locker import TermLocker

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class QualityCheckResult:
    """Result of a single quality check"""
    name: str
    passed: bool
    score: float
    message: str
    message_zh: str


@dataclass
class QualityGateResult:
    """
    Complete quality gate result
    完整的质量门控结果
    """
    passed: bool
    checks: List[QualityCheckResult]
    semantic_similarity: float
    terms_intact: bool
    new_risk_score: int
    new_risk_level: str
    action: str  # accept, retry_with_rule, retry_stronger, flag_manual
    message: str
    message_zh: str


class QualityGate:
    """
    Multi-layer quality validation gate
    多层质量验证门控

    Validates modifications across multiple dimensions:
    1. Semantic similarity (meaning preserved)
    2. Term integrity (protected terms intact)
    3. Risk reduction (AIGC score improved)
    4. Readability (not degraded)
    """

    def __init__(
        self,
        semantic_threshold: float = None,
        risk_target: int = 40
    ):
        """
        Initialize quality gate

        Args:
            semantic_threshold: Minimum semantic similarity
            risk_target: Target risk score (modification should achieve below this)
        """
        self.semantic_threshold = semantic_threshold or settings.semantic_similarity_threshold
        self.risk_target = risk_target

        self.semantic_validator = SemanticValidator(self.semantic_threshold)
        self.risk_scorer = RiskScorer()
        self.term_locker = TermLocker()

    async def validate(
        self,
        original: str,
        modified: str,
        locked_terms: List[str],
        target_risk: int = None
    ) -> QualityGateResult:
        """
        Run all quality checks
        执行所有质量检查

        Args:
            original: Original sentence
            modified: Modified sentence
            locked_terms: List of protected terms
            target_risk: Target risk score

        Returns:
            QualityGateResult with all check results
        """
        target = target_risk or self.risk_target
        checks = []

        # Layer 1: Semantic similarity check
        # 层1: 语义相似度检查
        semantic_result = self._check_semantic(original, modified)
        checks.append(semantic_result)

        # Layer 2: Term integrity check
        # 层2: 术语完整性检查
        term_result = self._check_terms(modified, locked_terms)
        checks.append(term_result)

        # Layer 3: Risk reduction check
        # 层3: 风险降低检查
        risk_result = self._check_risk(modified, target)
        checks.append(risk_result)

        # Aggregate results
        # 汇总结果
        all_passed = all(check.passed for check in checks)

        # Determine action based on which checks failed
        # 根据哪些检查失败来决定动作
        action = self._determine_action(checks)

        # Generate overall message
        # 生成总体消息
        if all_passed:
            message = "All quality checks passed"
            message_zh = "所有质量检查通过"
        else:
            failed_checks = [c.name for c in checks if not c.passed]
            message = f"Failed checks: {', '.join(failed_checks)}"
            message_zh = f"未通过的检查: {', '.join(failed_checks)}"

        return QualityGateResult(
            passed=all_passed,
            checks=checks,
            semantic_similarity=semantic_result.score,
            terms_intact=term_result.passed,
            new_risk_score=int(risk_result.score),
            new_risk_level=self._get_risk_level(int(risk_result.score)),
            action=action,
            message=message,
            message_zh=message_zh
        )

    def _check_semantic(self, original: str, modified: str) -> QualityCheckResult:
        """
        Check semantic similarity
        检查语义相似度
        """
        result = self.semantic_validator.validate(original, modified)

        return QualityCheckResult(
            name="semantic",
            passed=result.passed,
            score=result.similarity,
            message=result.message,
            message_zh=result.message_zh
        )

    def _check_terms(self, modified: str, locked_terms: List[str]) -> QualityCheckResult:
        """
        Check that all locked terms are preserved
        检查所有锁定术语是否保留
        """
        if not locked_terms:
            return QualityCheckResult(
                name="terms",
                passed=True,
                score=1.0,
                message="No locked terms to check",
                message_zh="无锁定术语需检查"
            )

        modified_lower = modified.lower()
        missing_terms = []

        for term in locked_terms:
            if term.lower() not in modified_lower:
                missing_terms.append(term)

        if missing_terms:
            return QualityCheckResult(
                name="terms",
                passed=False,
                score=1 - (len(missing_terms) / len(locked_terms)),
                message=f"Missing terms: {', '.join(missing_terms)}",
                message_zh=f"缺失术语: {', '.join(missing_terms)}"
            )
        else:
            return QualityCheckResult(
                name="terms",
                passed=True,
                score=1.0,
                message="All locked terms preserved",
                message_zh="所有锁定术语已保留"
            )

    def _check_risk(self, modified: str, target: int, tone_level: int = 4) -> QualityCheckResult:
        """
        Check that risk score is reduced (CAASS v2.0)
        检查风险分数是否降低（CAASS v2.0）
        """
        analysis = self.risk_scorer.analyze(modified, tone_level=tone_level)
        new_score = analysis.risk_score

        if new_score <= target:
            return QualityCheckResult(
                name="risk",
                passed=True,
                score=float(new_score),
                message=f"Risk score {new_score} meets target {target}",
                message_zh=f"风险分数 {new_score} 达到目标 {target}"
            )
        else:
            return QualityCheckResult(
                name="risk",
                passed=False,
                score=float(new_score),
                message=f"Risk score {new_score} exceeds target {target}",
                message_zh=f"风险分数 {new_score} 超过目标 {target}"
            )

    def _determine_action(self, checks: List[QualityCheckResult]) -> str:
        """
        Determine next action based on check results
        根据检查结果决定下一步动作
        """
        if all(c.passed for c in checks):
            return "accept"

        # Find which checks failed
        # 找出哪些检查失败
        failed = {c.name: c for c in checks if not c.passed}

        if "terms" in failed:
            # Term modification is critical - needs human review
            # 术语修改是关键的 - 需要人工审核
            return "flag_manual"

        if "semantic" in failed:
            semantic_score = failed["semantic"].score
            if semantic_score >= 0.70:
                # Close to passing - try rule-based instead
                # 接近通过 - 尝试基于规则的方法
                return "retry_with_rule"
            else:
                # Major semantic drift - needs human review
                # 重大语义漂移 - 需要人工审核
                return "flag_manual"

        if "risk" in failed:
            risk_score = failed["risk"].score
            if risk_score <= 60:
                # Moderate risk - might be acceptable
                # 中等风险 - 可能可接受
                return "accept"  # With warning
            else:
                # High risk still - try stronger rewrite
                # 仍然高风险 - 尝试更强的改写
                return "retry_stronger"

        return "flag_manual"

    def _get_risk_level(self, score: int) -> str:
        """Get risk level from score"""
        if score >= 61:
            return "high"
        elif score >= 31:
            return "medium"
        else:
            return "low"

    def quick_validate(
        self,
        original: str,
        modified: str,
        locked_terms: List[str] = None
    ) -> Dict[str, Any]:
        """
        Quick validation without full analysis
        快速验证，不进行完整分析

        Returns simplified dict for API responses
        """
        # Semantic check
        # 语义检查
        semantic = self.semantic_validator.get_similarity_score(original, modified)
        semantic_passed = semantic >= self.semantic_threshold

        # Term check
        # 术语检查
        terms_passed = True
        if locked_terms:
            modified_lower = modified.lower()
            terms_passed = all(term.lower() in modified_lower for term in locked_terms)

        # Overall pass
        # 总体通过
        passed = semantic_passed and terms_passed

        return {
            "passed": passed,
            "semantic_similarity": semantic,
            "semantic_passed": semantic_passed,
            "terms_intact": terms_passed
        }
