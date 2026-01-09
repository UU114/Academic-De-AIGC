"""
Step 5.3: Replacement Candidate Generation (替换候选生成)
Layer 1 Lexical Level

Generate replacement candidates for fingerprint words.
为指纹词生成替换候选。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ReplacementGenerationResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Replacement dictionary for common AI words
REPLACEMENTS = {
    # Type A: Dead giveaways
    "delve": ["explore", "examine", "investigate", "study"],
    "underscore": ["highlight", "emphasize", "show", "indicate"],
    "harness": ["use", "apply", "employ", "leverage"],
    "unveil": ["reveal", "show", "present", "introduce"],
    "pivotal": ["key", "important", "central", "essential"],
    "intricate": ["complex", "detailed", "elaborate", "involved"],
    "multifaceted": ["complex", "diverse", "varied", "multiple"],
    "paramount": ["critical", "essential", "vital", "crucial"],
    "tapestry": ["combination", "mix", "blend", "array"],
    "realm": ["area", "field", "domain", "sphere"],
    "landscape": ["environment", "context", "situation", "field"],

    # Type B: Academic clichés
    "comprehensive": ["thorough", "complete", "full", "extensive"],
    "robust": ["strong", "reliable", "solid", "stable"],
    "seamless": ["smooth", "integrated", "continuous", "unified"],
    "leverage": ["use", "apply", "employ", "utilize"],
    "facilitate": ["help", "enable", "support", "assist"],
    "utilize": ["use", "apply", "employ"],
    "crucial": ["important", "key", "essential", "critical"],
    "holistic": ["complete", "whole", "integrated", "comprehensive"],
    "transformative": ["significant", "major", "important", "substantial"],
    "innovative": ["new", "novel", "creative", "original"],
}


def _find_fingerprints(text: str, locked_terms: List[str]) -> List[Dict]:
    """Find fingerprint words in text"""
    text_lower = text.lower()
    locked_lower = [t.lower() for t in locked_terms]
    found = []

    for word in REPLACEMENTS.keys():
        if word in locked_lower:
            continue

        pattern = rf'\b{word}\b'
        matches = list(re.finditer(pattern, text_lower))

        for m in matches:
            context_start = max(0, m.start() - 40)
            context_end = min(len(text), m.end() + 40)

            found.append({
                "word": word,
                "position": m.start(),
                "context": text[context_start:context_end],
                "replacements": REPLACEMENTS[word]
            })

    return found


@router.post("/analyze", response_model=ReplacementGenerationResponse)
async def generate_replacements(request: SubstepBaseRequest):
    """
    Step 5.3: Generate replacement candidates
    步骤 5.3：生成替换候选

    - Finds fingerprint words
    - Generates context-appropriate replacements
    - Excludes locked terms
    """
    start_time = time.time()

    try:
        locked_terms = request.locked_terms or []
        fingerprints = _find_fingerprints(request.text, locked_terms)

        # Build replacements list
        replacements = []
        for fp in fingerprints:
            replacements.append({
                "original_word": fp["word"],
                "position": fp["position"],
                "context": fp["context"],
                "candidates": fp["replacements"],
                "recommended": fp["replacements"][0] if fp["replacements"] else None
            })

        replacement_count = len(replacements)

        # Calculate risk score
        if replacement_count >= 5:
            risk_score = 70
        elif replacement_count >= 3:
            risk_score = 50
        elif replacement_count >= 1:
            risk_score = 30
        else:
            risk_score = 10

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []

        if replacement_count > 0:
            unique_words = list(set(r["original_word"] for r in replacements))
            issues.append({
                "type": "replaceable_fingerprints",
                "description": f"{replacement_count} fingerprint words can be replaced",
                "description_zh": f"{replacement_count} 个指纹词可以替换",
                "severity": "high" if replacement_count >= 5 else "medium",
                "words": unique_words[:10]
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if replacement_count > 0:
            recommendations.append(f"Replace {replacement_count} fingerprint words with suggested alternatives.")
            recommendations_zh.append(f"用建议的替代词替换 {replacement_count} 个指纹词。")

            # Show top replacements
            for r in replacements[:3]:
                recommendations.append(f"Replace '{r['original_word']}' with '{r['recommended']}'")
                recommendations_zh.append(f"将 '{r['original_word']}' 替换为 '{r['recommended']}'")
        else:
            recommendations.append("No replaceable fingerprint words found.")
            recommendations_zh.append("未发现可替换的指纹词。")

        return ReplacementGenerationResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            replacements=replacements,
            replacement_count=replacement_count
        )

    except Exception as e:
        logger.error(f"Replacement generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_replacement_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for replacements"""
    return await generate_replacements(request)


@router.post("/apply")
async def apply_replacements(request: SubstepBaseRequest):
    """Apply selected replacements"""
    return await generate_replacements(request)


@router.post("/generate", response_model=ReplacementGenerationResponse)
async def generate_replacement_candidates(request: SubstepBaseRequest):
    """
    Generate replacement candidates (alias for analyze endpoint)
    生成替换候选（analyze端点的别名）
    """
    return await generate_replacements(request)
