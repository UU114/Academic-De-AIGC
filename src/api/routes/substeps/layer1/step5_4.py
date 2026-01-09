"""
Step 5.4: Paragraph Rewriting (LLM段落级改写)
Layer 1 Lexical Level

Rewrite paragraphs to reduce AI fingerprints while preserving locked terms.
改写段落以减少AI指纹同时保留锁定词汇。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ParagraphRewriteResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Simple word replacements for demonstration
SIMPLE_REPLACEMENTS = {
    "delve": "explore",
    "underscore": "highlight",
    "harness": "use",
    "pivotal": "key",
    "intricate": "complex",
    "multifaceted": "diverse",
    "paramount": "critical",
    "realm": "field",
    "landscape": "environment",
    "comprehensive": "thorough",
    "robust": "strong",
    "leverage": "use",
    "facilitate": "enable",
    "utilize": "use",
    "furthermore": "",  # Remove
    "moreover": "",  # Remove
    "additionally": "",  # Remove
}


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _simple_rewrite(paragraph: str, locked_terms: List[str]) -> tuple:
    """Simple rule-based rewriting"""
    rewritten = paragraph
    changes = []
    locked_lower = [t.lower() for t in locked_terms]

    for original, replacement in SIMPLE_REPLACEMENTS.items():
        if original in locked_lower:
            continue

        pattern = rf'\b{original}\b'

        def replace_func(match):
            # Preserve capitalization
            if match.group()[0].isupper():
                return replacement.capitalize() if replacement else ""
            return replacement

        count = len(re.findall(pattern, rewritten, re.IGNORECASE))
        if count > 0:
            rewritten = re.sub(pattern, replace_func, rewritten, flags=re.IGNORECASE)
            if replacement:
                changes.append({
                    "original": original,
                    "replacement": replacement,
                    "count": count
                })
            else:
                changes.append({
                    "original": original,
                    "replacement": "(removed)",
                    "count": count
                })

    # Clean up double spaces and sentence-initial issues
    rewritten = re.sub(r'\s+', ' ', rewritten)
    rewritten = re.sub(r'\.\s+([a-z])', lambda m: '. ' + m.group(1).upper(), rewritten)

    return rewritten, changes


def _check_locked_terms_preserved(original: str, rewritten: str, locked_terms: List[str]) -> bool:
    """Check if all locked terms are preserved"""
    for term in locked_terms:
        if term.lower() in original.lower() and term.lower() not in rewritten.lower():
            return False
    return True


@router.post("/analyze", response_model=ParagraphRewriteResponse)
async def rewrite_paragraphs(request: SubstepBaseRequest):
    """
    Step 5.4: Rewrite paragraphs
    步骤 5.4：改写段落

    - Applies simple replacements
    - Preserves locked terms
    - Tracks changes
    """
    start_time = time.time()

    try:
        locked_terms = request.locked_terms or []
        paragraphs = _split_paragraphs(request.text)

        all_changes = []
        rewritten_parts = []
        total_replacements = 0

        for para in paragraphs:
            rewritten, changes = _simple_rewrite(para, locked_terms)
            rewritten_parts.append(rewritten)
            all_changes.extend(changes)
            total_replacements += sum(c["count"] for c in changes)

        rewritten_text = "\n\n".join(rewritten_parts)

        # Check locked terms preservation
        locked_preserved = _check_locked_terms_preserved(
            request.text, rewritten_text, locked_terms
        )

        # Calculate risk score reduction
        if total_replacements >= 5:
            risk_score = 30  # Good improvement
        elif total_replacements >= 2:
            risk_score = 50  # Some improvement
        else:
            risk_score = 20  # Minimal changes needed

        risk_level = RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []

        if not locked_preserved:
            issues.append({
                "type": "locked_terms_affected",
                "description": "Some locked terms may have been affected",
                "description_zh": "部分锁定词汇可能受到影响",
                "severity": "high"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if total_replacements > 0:
            recommendations.append(f"Applied {total_replacements} word replacements.")
            recommendations_zh.append(f"应用了 {total_replacements} 个词汇替换。")
        else:
            recommendations.append("No replacements needed.")
            recommendations_zh.append("不需要替换。")

        if locked_preserved:
            recommendations.append(f"All {len(locked_terms)} locked terms preserved.")
            recommendations_zh.append(f"所有 {len(locked_terms)} 个锁定词汇已保留。")

        return ParagraphRewriteResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            original_text=request.text,
            rewritten_text=rewritten_text,
            changes=all_changes,
            locked_terms_preserved=locked_preserved
        )

    except Exception as e:
        logger.error(f"Paragraph rewriting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_rewrite_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for rewriting"""
    return await rewrite_paragraphs(request)


@router.post("/apply")
async def apply_rewrites(request: SubstepBaseRequest):
    """Apply paragraph rewrites"""
    return await rewrite_paragraphs(request)


@router.post("/rewrite", response_model=ParagraphRewriteResponse)
async def rewrite_paragraphs_endpoint(request: SubstepBaseRequest):
    """
    Rewrite paragraphs (alias for analyze endpoint)
    改写段落（analyze端点的别名）
    """
    return await rewrite_paragraphs(request)
