"""
Step 5.5: Rewrite Validation (改写结果验证)
Layer 1 Lexical Level

Validate rewriting results for quality and compliance.
验证改写结果的质量和合规性。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ValidationResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Fingerprint words to check (subset for validation)
FINGERPRINT_WORDS = [
    "delve", "underscore", "harness", "unveil", "pivotal",
    "intricate", "multifaceted", "paramount", "tapestry", "realm",
    "landscape", "comprehensive", "robust", "seamless", "leverage"
]


class ValidationRequest(SubstepBaseRequest):
    """Validation request with original text"""
    original_text: str = ""


def _count_fingerprints(text: str) -> int:
    """Count fingerprint words in text"""
    text_lower = text.lower()
    count = 0
    for word in FINGERPRINT_WORDS:
        count += len(re.findall(rf'\b{word}\b', text_lower))
    return count


def _calculate_semantic_similarity(original: str, rewritten: str) -> float:
    """Simple similarity calculation based on word overlap"""
    orig_words = set(re.findall(r'\b[a-z]{4,}\b', original.lower()))
    rewr_words = set(re.findall(r'\b[a-z]{4,}\b', rewritten.lower()))

    if not orig_words:
        return 1.0

    overlap = len(orig_words & rewr_words)
    similarity = overlap / len(orig_words)

    return min(1.0, similarity + 0.15)  # Boost since replacements are expected


def _check_locked_terms(original: str, rewritten: str, locked_terms: List[str]) -> tuple:
    """Check if locked terms are preserved"""
    preserved = True
    missing = []

    for term in locked_terms:
        orig_count = len(re.findall(rf'\b{re.escape(term)}\b', original, re.IGNORECASE))
        rewr_count = len(re.findall(rf'\b{re.escape(term)}\b', rewritten, re.IGNORECASE))

        if orig_count > 0 and rewr_count < orig_count:
            preserved = False
            missing.append(term)

    return preserved, missing


def _check_academic_norms(text: str) -> List[Dict]:
    """Check basic academic writing norms"""
    issues = []

    # Check for contractions
    contractions = re.findall(r"\b\w+'\w+\b", text)
    if contractions:
        issues.append({
            "type": "contractions",
            "description": f"Found contractions: {', '.join(contractions[:3])}",
            "severity": "low"
        })

    # Check for first person overuse
    first_person = len(re.findall(r'\b(I|my|me)\b', text, re.IGNORECASE))
    word_count = len(text.split())
    if word_count > 0 and first_person / word_count > 0.03:
        issues.append({
            "type": "first_person_overuse",
            "description": "High first-person pronoun usage",
            "severity": "low"
        })

    return issues


@router.post("/validate", response_model=ValidationResponse)
async def validate_rewrite(request: ValidationRequest):
    """
    Step 5.5: Validate rewriting results
    步骤 5.5：验证改写结果

    - Semantic similarity check
    - Risk reduction assessment
    - Locked terms verification
    - Academic norm compliance
    """
    start_time = time.time()

    try:
        original_text = request.original_text or request.text
        rewritten_text = request.text
        locked_terms = request.locked_terms or []

        # Calculate fingerprint counts
        original_fingerprints = _count_fingerprints(original_text)
        final_fingerprints = _count_fingerprints(rewritten_text)

        # Calculate risk scores (based on fingerprint density)
        orig_word_count = len(original_text.split())
        final_word_count = len(rewritten_text.split())

        original_risk = min(100, original_fingerprints * 10)
        final_risk = min(100, final_fingerprints * 10)
        improvement = original_risk - final_risk

        # Calculate semantic similarity
        similarity = _calculate_semantic_similarity(original_text, rewritten_text)

        # Check locked terms
        locked_check, missing_terms = _check_locked_terms(
            original_text, rewritten_text, locked_terms
        )

        # Check academic norms
        norm_issues = _check_academic_norms(rewritten_text)

        # Determine validation status
        validation_passed = (
            similarity >= 0.75 and  # Minimum semantic similarity
            locked_check and  # All locked terms preserved
            final_risk < original_risk  # Risk reduced
        )

        risk_level = RiskLevel.LOW if validation_passed else RiskLevel.MEDIUM

        # Build issues
        issues = []

        if similarity < 0.75:
            issues.append({
                "type": "low_similarity",
                "description": f"Semantic similarity too low ({similarity:.0%})",
                "description_zh": f"语义相似度过低（{similarity:.0%}）",
                "severity": "high"
            })

        if not locked_check:
            issues.append({
                "type": "locked_terms_missing",
                "description": f"Missing locked terms: {', '.join(missing_terms)}",
                "description_zh": f"缺少锁定词汇：{', '.join(missing_terms)}",
                "severity": "critical"
            })

        if final_risk >= original_risk:
            issues.append({
                "type": "no_improvement",
                "description": "Risk score did not improve",
                "description_zh": "风险评分未改善",
                "severity": "medium"
            })

        issues.extend(norm_issues)

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if validation_passed:
            recommendations.append(f"Validation passed. Risk reduced by {improvement} points.")
            recommendations_zh.append(f"验证通过。风险降低了 {improvement} 分。")
        else:
            if not locked_check:
                recommendations.append("Restore missing locked terms before finalizing.")
                recommendations_zh.append("在完成前恢复缺失的锁定词汇。")
            if similarity < 0.75:
                recommendations.append("Rewriting changed too much meaning. Consider lighter edits.")
                recommendations_zh.append("改写改变了太多含义。考虑更轻微的编辑。")

        recommendations.append(f"Final fingerprint count: {final_fingerprints} (was {original_fingerprints})")
        recommendations_zh.append(f"最终指纹词数量：{final_fingerprints}（原为 {original_fingerprints}）")

        return ValidationResponse(
            risk_score=final_risk,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            original_risk_score=original_risk,
            final_risk_score=final_risk,
            improvement=improvement,
            locked_terms_check=locked_check,
            semantic_similarity=round(similarity, 3),
            validation_passed=validation_passed
        )

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_validation(request: SubstepBaseRequest):
    """Analyze without original text comparison"""
    # Create a validation request with same text as original
    val_request = ValidationRequest(
        text=request.text,
        original_text=request.text,
        session_id=request.session_id,
        locked_terms=request.locked_terms
    )
    return await validate_rewrite(val_request)
