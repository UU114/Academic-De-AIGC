"""
Step 2.3: Internal Structure Similarity (章节内部结构相似性检测)
Layer 4 Section Level
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    InternalSimilarityResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Paragraph function keywords
FUNCTION_KEYWORDS = {
    "topic_sentence": ["this", "we", "the", "in this", "here"],
    "evidence": ["found", "showed", "demonstrated", "data", "results", "study", "%", "figure", "table"],
    "analysis": ["suggests", "indicates", "implies", "therefore", "thus", "because"],
    "transition": ["however", "furthermore", "moreover", "additionally", "next"],
    "mini_conclusion": ["in summary", "overall", "together", "these results", "collectively"]
}


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _classify_paragraph_function(para: str) -> str:
    """Classify paragraph by its function"""
    para_lower = para.lower()
    scores = {func: 0 for func in FUNCTION_KEYWORDS}

    for func, keywords in FUNCTION_KEYWORDS.items():
        for kw in keywords:
            if kw in para_lower:
                scores[func] += 1

    # Return highest scoring function
    max_score = max(scores.values())
    if max_score == 0:
        return "body"

    for func, score in scores.items():
        if score == max_score:
            return func

    return "body"


def _calculate_sequence_similarity(seq1: List[str], seq2: List[str]) -> float:
    """Calculate similarity between two function sequences"""
    if not seq1 or not seq2:
        return 0

    # Simple matching
    min_len = min(len(seq1), len(seq2))
    matches = sum(1 for i in range(min_len) if seq1[i] == seq2[i])

    return matches / max(len(seq1), len(seq2))


@router.post("/analyze", response_model=InternalSimilarityResponse)
async def analyze_internal_similarity(request: SubstepBaseRequest):
    """
    Step 2.3: Analyze internal structure similarity between sections
    步骤 2.3：分析章节间内部结构相似性

    Detects if different sections share highly similar internal structures (AI pattern)
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        # Classify each paragraph's function
        paragraph_functions = []
        for i, para in enumerate(paragraphs):
            func = _classify_paragraph_function(para)
            paragraph_functions.append({
                "paragraph_index": i,
                "function": func,
                "preview": para[:80] + "..." if len(para) > 80 else para
            })

        # Group into sections and build function sequences
        section_sequences = []
        current_sequence = []

        for i, pf in enumerate(paragraph_functions):
            current_sequence.append(pf["function"])
            # Simple section break every 3 paragraphs
            if (i + 1) % 3 == 0:
                section_sequences.append(current_sequence)
                current_sequence = []

        if current_sequence:
            section_sequences.append(current_sequence)

        # Calculate similarity matrix
        n = len(section_sequences)
        similarity_matrix = []
        total_similarity = 0
        comparison_count = 0

        for i in range(n):
            row = []
            for j in range(n):
                if i == j:
                    row.append(1.0)
                else:
                    sim = _calculate_sequence_similarity(section_sequences[i], section_sequences[j])
                    row.append(round(sim, 2))
                    if i < j:
                        total_similarity += sim
                        comparison_count += 1
            similarity_matrix.append(row)

        avg_similarity = total_similarity / comparison_count if comparison_count > 0 else 0

        # Calculate risk score
        if avg_similarity > 0.9:
            risk_score = 90
        elif avg_similarity > 0.8:
            risk_score = 75
        elif avg_similarity > 0.7:
            risk_score = 60
        elif avg_similarity > 0.6:
            risk_score = 45
        else:
            risk_score = 30

        if risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        issues = []
        if avg_similarity > 0.7:
            issues.append({
                "type": "high_similarity",
                "description": f"Section structures are too similar ({avg_similarity:.0%} avg similarity)",
                "description_zh": f"章节结构过于相似（平均相似度 {avg_similarity:.0%}）",
                "severity": "high" if avg_similarity > 0.8 else "medium"
            })

        recommendations = []
        recommendations_zh = []

        if avg_similarity > 0.7:
            recommendations.append("Vary the internal structure of sections. Use different paragraph patterns.")
            recommendations_zh.append("变化章节的内部结构。使用不同的段落模式。")

        if not issues:
            recommendations.append("Section internal structures show good variation.")
            recommendations_zh.append("章节内部结构显示良好的变化。")

        return InternalSimilarityResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            avg_similarity=round(avg_similarity, 3),
            similarity_matrix=similarity_matrix,
            heading_variance=0.5,  # Placeholder
            argument_density_cv=0.3,  # Placeholder
            paragraph_functions=paragraph_functions
        )

    except Exception as e:
        logger.error(f"Internal similarity analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_similarity_suggestions(request: SubstepBaseRequest):
    return await analyze_internal_similarity(request)


@router.post("/apply")
async def apply_similarity_changes(request: SubstepBaseRequest):
    return await analyze_internal_similarity(request)
