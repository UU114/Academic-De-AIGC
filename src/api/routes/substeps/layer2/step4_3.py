"""
Step 4.3: Sentence Merger Suggestions (句子合并建议)
Layer 2 Sentence Level

Identify sentence pairs that can be merged for complexity.
识别可以合并的句子对以增加复杂性。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SubstepBaseResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Keywords indicating semantic relation for merging
MERGE_RELATION_KEYWORDS = {
    "causal": ["because", "therefore", "thus", "hence", "as a result"],
    "contrast": ["however", "but", "although", "while", "whereas"],
    "addition": ["furthermore", "moreover", "additionally", "also", "in addition"],
    "example": ["for example", "for instance", "such as", "specifically"],
    "temporal": ["then", "after", "before", "when", "while"]
}


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip() and len(p.split()) >= 10]


def _split_sentences(para: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', para.strip())
    return [s.strip() for s in sentences if s.strip() and len(s.split()) >= 3]


def _extract_keywords(sentence: str) -> set:
    """Extract content keywords from sentence"""
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "this", "that", "these", "those",
                  "to", "of", "in", "for", "on", "with", "by", "from", "as", "at"}
    words = re.findall(r'\b[a-z]{3,}\b', sentence.lower())
    return set(words) - stop_words


def _calculate_semantic_similarity(sent1: str, sent2: str) -> float:
    """Calculate simple semantic similarity between sentences"""
    kw1 = _extract_keywords(sent1)
    kw2 = _extract_keywords(sent2)

    if not kw1 or not kw2:
        return 0

    overlap = len(kw1 & kw2)
    return overlap / min(len(kw1), len(kw2), 5)


def _detect_relation_type(sent2: str) -> str:
    """Detect relation type based on second sentence"""
    sent_lower = sent2.lower()

    for rel_type, keywords in MERGE_RELATION_KEYWORDS.items():
        if any(kw in sent_lower for kw in keywords):
            return rel_type

    return "continuation"


def _is_mergeable(sent1: str, sent2: str) -> tuple:
    """Check if two sentences are good merge candidates"""
    len1 = len(sent1.split())
    len2 = len(sent2.split())

    # Combined length should be reasonable (not too long)
    combined_len = len1 + len2
    if combined_len > 50:
        return False, "too_long", 0

    # At least one should be short
    if len1 > 20 and len2 > 20:
        return False, "both_long", 0

    # Check semantic similarity
    similarity = _calculate_semantic_similarity(sent1, sent2)
    if similarity < 0.2:
        return False, "unrelated", similarity

    # Check relation
    relation = _detect_relation_type(sent2)

    return True, relation, similarity


@router.post("/analyze")
async def analyze_merge_candidates(request: SubstepBaseRequest):
    """
    Step 4.3: Identify sentence merge candidates
    步骤 4.3：识别可合并的句子

    - Finds semantically related adjacent sentences
    - Suggests merge strategies
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        merge_candidates = []
        total_pairs = 0

        for para_idx, para in enumerate(paragraphs):
            sentences = _split_sentences(para)

            for i in range(len(sentences) - 1):
                sent1 = sentences[i]
                sent2 = sentences[i + 1]
                total_pairs += 1

                mergeable, relation, similarity = _is_mergeable(sent1, sent2)

                if mergeable:
                    # Generate merge preview
                    preview = f"{sent1[:-1]} while {sent2[0].lower()}{sent2[1:]}"
                    if relation == "causal":
                        preview = f"{sent1[:-1]} because {sent2[0].lower()}{sent2[1:]}"
                    elif relation == "contrast":
                        preview = f"Although {sent1[0].lower()}{sent1[1:-1]}, {sent2[0].lower()}{sent2[1:]}"

                    merge_candidates.append({
                        "paragraph_index": para_idx,
                        "sentence_1_index": i,
                        "sentence_2_index": i + 1,
                        "sentence_1": sent1[:80] + "..." if len(sent1) > 80 else sent1,
                        "sentence_2": sent2[:80] + "..." if len(sent2) > 80 else sent2,
                        "relation_type": relation,
                        "similarity": round(similarity, 2),
                        "merge_preview": preview[:150] + "..." if len(preview) > 150 else preview,
                        "complexity_gain": "high" if relation in ["causal", "contrast"] else "medium"
                    })

        # Calculate metrics
        merge_ratio = len(merge_candidates) / total_pairs if total_pairs > 0 else 0

        # If there are too few complex sentences, more merges = lower risk
        # But we present this as opportunity rather than risk
        risk_score = max(0, 50 - len(merge_candidates) * 10)  # More candidates = lower risk

        risk_level = RiskLevel.MEDIUM if len(merge_candidates) >= 3 else RiskLevel.LOW

        issues = []
        if len(merge_candidates) >= 3:
            issues.append({
                "type": "merge_opportunity",
                "description": f"{len(merge_candidates)} sentence pairs can be merged for complexity",
                "description_zh": f"{len(merge_candidates)} 对句子可以合并以增加复杂性",
                "severity": "medium"
            })

        recommendations = []
        recommendations_zh = []

        if merge_candidates:
            recommendations.append(f"Consider merging {len(merge_candidates)} sentence pairs to increase complexity.")
            recommendations_zh.append(f"考虑合并 {len(merge_candidates)} 对句子以增加复杂性。")
        else:
            recommendations.append("No obvious merge candidates found.")
            recommendations_zh.append("未发现明显的合并候选项。")

        return {
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "issues": issues,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "merge_candidates": merge_candidates,
            "total_pairs_analyzed": total_pairs,
            "mergeable_ratio": round(merge_ratio, 3)
        }

    except Exception as e:
        logger.error(f"Merge analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_merge_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for sentence merging"""
    return await analyze_merge_candidates(request)


@router.post("/apply")
async def apply_merges(request: SubstepBaseRequest):
    """Apply selected merges"""
    return await analyze_merge_candidates(request)
