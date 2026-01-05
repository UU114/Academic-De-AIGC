"""
Quality gate module - multi-layer validation
质量门控模块 - 多层验证
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import json
from pathlib import Path

from src.config import get_settings
from src.core.validator.semantic import SemanticValidator
from src.core.analyzer.scorer import RiskScorer, LEVEL_1_FINGERPRINTS, LEVEL_2_FINGERPRINTS
from src.core.preprocessor.term_locker import TermLocker
from src.core.analyzer.fingerprint import FingerprintDetector, FingerprintMatch

logger = logging.getLogger(__name__)
settings = get_settings()

# Academic level threshold for strict first-person pronoun prohibition
# Level 0-5: Academic writing, first-person pronouns strictly forbidden
# Level 6-10: Casual/semi-formal writing, first-person pronouns allowed
# 学术级别阈值：0-5级严格禁止第一人称代词
ACADEMIC_LEVEL_THRESHOLD = 5

# First-person pronouns to check (case-insensitive)
# 第一人称代词列表（不区分大小写）
FIRST_PERSON_PRONOUNS = {
    "i", "we", "my", "our", "us", "me", "myself", "ourselves"
}


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


@dataclass
class SuggestionValidationResult:
    """
    Result of post-generation suggestion validation (DEAI Engine 2.0)
    生成后建议验证结果
    """
    passed: bool
    action: str  # accept, retry_without_p0, retry, retry_without_pronouns, flag_manual
    blocked_words: List[str]  # P0 words found in suggestion
    introduced_fingerprints: List[str]  # New fingerprints introduced
    first_person_pronouns: List[str] = None  # First-person pronouns found (for academic levels)
    message: str = ""
    message_zh: str = ""


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
        self.fingerprint_detector = FingerprintDetector()

        # P0 word blocklist for post-generation validation (DEAI Engine 2.0)
        # 生成后验证的P0词黑名单
        self._init_p0_blocklist()

    async def validate(
        self,
        original: str,
        modified: str,
        locked_terms: List[str],
        target_risk: int = None,
        is_paraphrase: bool = False
    ) -> QualityGateResult:
        """
        Run all quality checks
        执行所有质量检查

        Args:
            original: Original sentence
            modified: Modified sentence
            locked_terms: List of protected terms
            target_risk: Target risk score
            is_paraphrase: Whether the sentence is a paraphrase (requires stricter semantic check)

        Returns:
            QualityGateResult with all check results
        """
        target = target_risk or self.risk_target
        checks = []

        # Layer 1: Semantic similarity check
        # 层1: 语义相似度检查
        semantic_threshold = 0.95 if is_paraphrase else self.semantic_threshold
        semantic_result = self._check_semantic(original, modified, threshold=semantic_threshold)
        checks.append(semantic_result)

        # Layer 2: Term integrity check
        # 层2: 术语完整性检查
        term_result = self._check_terms(modified, locked_terms)
        checks.append(term_result)

        # Layer 2.5: Citation format check
        # 层2.5: 引用格式检查
        citation_result = self._check_citation_format(original, modified)
        checks.append(citation_result)

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

    def _check_semantic(self, original: str, modified: str, threshold: float = None) -> QualityCheckResult:
        """
        Check semantic similarity
        检查语义相似度
        """
        # Use provided threshold or default
        target_threshold = threshold if threshold is not None else self.semantic_threshold
        
        # We need to temporarily set the validator's threshold or check against the score directly
        result = self.semantic_validator.validate(original, modified)
        
        # Override result based on dynamic threshold
        passed = result.similarity >= target_threshold
        
        message = result.message
        if not passed and result.passed:
            # It passed default but failed stricter threshold
            message = f"Similarity {result.similarity:.2f} below strict threshold {target_threshold}"

        return QualityCheckResult(
            name="semantic",
            passed=passed,
            score=result.similarity,
            message=message,
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

    def _check_citation_format(self, original: str, modified: str) -> QualityCheckResult:
        """
        Check that all citations maintain their exact original format
        检查所有引用是否保持其确切的原始格式
        """
        # Citation patterns
        # 引用模式
        citation_patterns = [
            r'\([A-Z][a-z]+(?:\s+(?:et\s+al\.|&|and)\s+[A-Z][a-z]+)*,?\s*\d{4}[a-z]?\)',  # (Author, Year)
            r'\[\d+(?:[,\-]\d+)*\]',  # [1], [1,2], [1-3]
        ]

        # Extract citations from original
        # 从原文中提取引用
        original_citations = []
        for pattern in citation_patterns:
            original_citations.extend(re.findall(pattern, original))

        if not original_citations:
            return QualityCheckResult(
                name="citation_format",
                passed=True,
                score=1.0,
                message="No citations to check",
                message_zh="无引用需检查"
            )

        # Check each citation exists with exact same format in modified
        # 检查每个引用是否以完全相同的格式存在于修改后的文本中
        format_changed = []
        for citation in original_citations:
            if citation not in modified:
                format_changed.append(citation)

        if format_changed:
            return QualityCheckResult(
                name="citation_format",
                passed=False,
                score=1 - (len(format_changed) / len(original_citations)),
                message=f"Citation format changed: {', '.join(format_changed)}",
                message_zh=f"引用格式被改变: {', '.join(format_changed)}"
            )
        else:
            return QualityCheckResult(
                name="citation_format",
                passed=True,
                score=1.0,
                message="All citation formats preserved",
                message_zh="所有引用格式已保留"
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

        if "citation_format" in failed:
            # Citation format changed - critical failure, reject
            # 引用格式被改变 - 严重失败，拒绝
            return "reject"

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

    def _init_p0_blocklist(self):
        """
        Initialize P0 word blocklist for post-generation validation (DEAI Engine 2.0)
        初始化生成后验证的P0词黑名单

        The blocklist includes:
        - All LEVEL_1 fingerprints (dead giveaways)
        - High-risk LEVEL_2 fingerprints (pivotal, paramount, crucial, etc.)
        """
        # Start with all LEVEL_1 fingerprints
        # 从所有LEVEL_1指纹词开始
        self.p0_blocklist = set(LEVEL_1_FINGERPRINTS)

        # Add high-risk LEVEL_2 fingerprints
        # 添加高风险LEVEL_2指纹词
        high_risk_level2 = {
            "pivotal", "paramount", "crucial", "holistic", "comprehensive",
            "underscores", "underscore", "foster", "fosters", "noteworthy",
            "groundbreaking", "plays a pivotal role", "plays a crucial role",
            "of paramount importance", "holistic approach", "comprehensive framework",
            "underscores the importance", "foster a culture"
        }
        self.p0_blocklist.update(high_risk_level2)

        # Try to load additional blocklist from JSON if exists
        # 尝试从JSON加载额外的黑名单
        try:
            blocklist_path = Path("data/fingerprints/safe_replacements.json")
            if blocklist_path.exists():
                with open(blocklist_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "p0_blocklist" in data:
                        self.p0_blocklist.update(data["p0_blocklist"])
                        logger.info(f"Loaded P0 blocklist from {blocklist_path}")
        except Exception as e:
            logger.warning(f"Failed to load P0 blocklist from JSON: {e}")

        logger.debug(f"P0 blocklist initialized with {len(self.p0_blocklist)} entries")

    def _check_p0_words(self, text: str) -> List[str]:
        """
        Check if text contains any P0 blocked words (DEAI Engine 2.0)
        检查文本是否包含任何P0黑名单词

        Args:
            text: Text to check

        Returns:
            List of blocked words found
        """
        text_lower = text.lower()
        found = []

        for word in self.p0_blocklist:
            # Use word boundary matching for single words
            # 对单个词使用词边界匹配
            if ' ' not in word:
                pattern = r'\b' + re.escape(word) + r'\b'
                if re.search(pattern, text_lower, re.IGNORECASE):
                    found.append(word)
            else:
                # For phrases, simple substring match
                # 对短语使用简单子字符串匹配
                if word.lower() in text_lower:
                    found.append(word)

        return found

    def _get_introduced_fingerprints(
        self,
        original_fps: List[FingerprintMatch],
        new_fps: List[FingerprintMatch]
    ) -> List[str]:
        """
        Get fingerprints that were introduced (not in original) (DEAI Engine 2.0)
        获取新引入的指纹词（原文中没有的）

        Args:
            original_fps: Fingerprints from original text
            new_fps: Fingerprints from new text

        Returns:
            List of newly introduced fingerprint words
        """
        original_words = {fp.word.lower() for fp in original_fps}
        introduced = []

        for fp in new_fps:
            if fp.word.lower() not in original_words:
                # Only count high-risk fingerprints as "introduced"
                # 只把高风险指纹词计为"新引入"
                if fp.risk_weight >= 0.6:
                    introduced.append(fp.word)

        return introduced

    def _check_first_person_pronouns(self, text: str) -> List[str]:
        """
        Check if text contains first-person pronouns (DEAI Engine 2.0)
        检查文本是否包含第一人称代词

        Args:
            text: Text to check

        Returns:
            List of first-person pronouns found
        """
        found = []
        text_lower = text.lower()
        words = re.findall(r'\b[a-zA-Z]+\b', text_lower)

        for pronoun in FIRST_PERSON_PRONOUNS:
            if pronoun in words:
                # Find all occurrences and their positions for context
                # 找到所有出现的位置以提供上下文
                pattern = r'\b' + re.escape(pronoun) + r'\b'
                if re.search(pattern, text_lower, re.IGNORECASE):
                    found.append(pronoun)

        return found

    def verify_suggestion(
        self,
        original: str,
        suggestion: str,
        max_introduced_fps: int = 0,
        colloquialism_level: int = 4
    ) -> SuggestionValidationResult:
        """
        Verify LLM suggestion doesn't introduce P0 words or new fingerprints (DEAI Engine 2.0)
        验证LLM建议不引入P0词或新指纹词

        This is the "gatekeeper" that prevents suggestions from making text
        more AI-like. It should be called after LLM generates a suggestion
        but before presenting it to the user.
        这是防止建议使文本更像AI的"守门员"。应该在LLM生成建议后、
        展示给用户之前调用。

        Args:
            original: Original text
            suggestion: LLM's suggested rewrite
            max_introduced_fps: Maximum allowed new fingerprints (default: 0)
            colloquialism_level: Colloquialism level (0-10), levels 0-5 forbid first-person pronouns

        Returns:
            SuggestionValidationResult with validation outcome
        """
        # Check for first-person pronouns in academic levels (0-5)
        # 检查学术级别(0-5)中的第一人称代词
        if colloquialism_level <= ACADEMIC_LEVEL_THRESHOLD:
            pronouns_found = self._check_first_person_pronouns(suggestion)
            if pronouns_found:
                logger.warning(
                    f"Suggestion contains first-person pronouns in academic level {colloquialism_level}: "
                    f"{pronouns_found}. Suggestion rejected."
                )
                return SuggestionValidationResult(
                    passed=False,
                    action="retry_without_pronouns",
                    blocked_words=[],
                    introduced_fingerprints=[],
                    first_person_pronouns=pronouns_found,
                    message=f"Academic writing (Level {colloquialism_level}) cannot contain first-person pronouns: {', '.join(pronouns_found)}",
                    message_zh=f"学术写作(级别{colloquialism_level})不能包含第一人称代词: {', '.join(pronouns_found)}"
                )

        # Check for P0 blocked words
        # 检查P0黑名单词
        blocked_words = self._check_p0_words(suggestion)

        if blocked_words:
            logger.warning(
                f"Suggestion contains P0 words: {blocked_words}. "
                f"Suggestion rejected."
            )
            return SuggestionValidationResult(
                passed=False,
                action="retry_without_p0",
                blocked_words=blocked_words,
                introduced_fingerprints=[],
                first_person_pronouns=[],
                message=f"Suggestion contains blocked P0 words: {', '.join(blocked_words)}",
                message_zh=f"建议包含P0黑名单词: {', '.join(blocked_words)}"
            )

        # Check for introduced fingerprints
        # 检查新引入的指纹词
        original_fps = self.fingerprint_detector.detect(original)
        suggestion_fps = self.fingerprint_detector.detect(suggestion)
        introduced = self._get_introduced_fingerprints(original_fps, suggestion_fps)

        if len(introduced) > max_introduced_fps:
            logger.warning(
                f"Suggestion introduces new fingerprints: {introduced}. "
                f"Suggestion needs review."
            )
            return SuggestionValidationResult(
                passed=False,
                action="retry",
                blocked_words=[],
                introduced_fingerprints=introduced,
                first_person_pronouns=[],
                message=f"Suggestion introduces new AI fingerprints: {', '.join(introduced)}",
                message_zh=f"建议引入了新的AI指纹词: {', '.join(introduced)}"
            )

        # All checks passed
        # 所有检查通过
        return SuggestionValidationResult(
            passed=True,
            action="accept",
            blocked_words=[],
            introduced_fingerprints=[],
            first_person_pronouns=[],
            message="Suggestion passed all validation checks",
            message_zh="建议通过所有验证检查"
        )
