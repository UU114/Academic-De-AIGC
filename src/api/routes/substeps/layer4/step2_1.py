"""
Step 2.1: Section Order & Structure (章节顺序与结构检测)
Layer 4 Section Level
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SectionOrderResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


EXPECTED_ORDER = ["introduction", "literature_review", "methodology", "results", "discussion", "conclusion"]


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _detect_sections_with_roles(paragraphs: List[str]) -> List[Dict[str, Any]]:
    """Detect sections and their roles"""
    role_patterns = {
        "introduction": ["introduction", "background", "overview", "this paper"],
        "literature_review": ["literature", "review", "previous", "prior"],
        "methodology": ["method", "approach", "procedure", "experiment"],
        "results": ["result", "finding", "outcome", "showed"],
        "discussion": ["discussion", "implication", "interpretation"],
        "conclusion": ["conclusion", "summary", "future", "in conclusion"]
    }

    sections = []
    current_role = None
    current_paragraphs = []
    current_words = 0

    for i, para in enumerate(paragraphs):
        para_lower = para.lower()
        detected_role = "body"

        for role, keywords in role_patterns.items():
            if any(kw in para_lower for kw in keywords):
                detected_role = role
                break

        if current_role is None:
            current_role = detected_role
            current_paragraphs = [i]
            current_words = len(para.split())
        elif detected_role != "body" and detected_role != current_role:
            sections.append({
                "role": current_role,
                "paragraphs": current_paragraphs,
                "word_count": current_words
            })
            current_role = detected_role
            current_paragraphs = [i]
            current_words = len(para.split())
        else:
            current_paragraphs.append(i)
            current_words += len(para.split())

    if current_paragraphs:
        sections.append({
            "role": current_role,
            "paragraphs": current_paragraphs,
            "word_count": current_words
        })

    return sections


@router.post("/analyze", response_model=SectionOrderResponse)
async def analyze_section_order(request: SubstepBaseRequest):
    """
    Step 2.1: Analyze section order and structure
    步骤 2.1：分析章节顺序和结构
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)
        sections = _detect_sections_with_roles(paragraphs)

        # Get actual order
        actual_order = [s["role"] for s in sections]

        # Calculate order match score
        matches = 0
        for i, role in enumerate(actual_order):
            if role in EXPECTED_ORDER:
                expected_idx = EXPECTED_ORDER.index(role)
                if i == expected_idx or (i < len(EXPECTED_ORDER) and role == EXPECTED_ORDER[i]):
                    matches += 1

        order_match_score = int(100 * matches / len(EXPECTED_ORDER)) if EXPECTED_ORDER else 0

        # Find missing sections
        present_roles = set(actual_order)
        missing_sections = [r for r in EXPECTED_ORDER if r not in present_roles]

        # Calculate function fusion score (how isolated are section functions)
        unique_roles = len(set(actual_order))
        fusion_score = 100 - (unique_roles * 15)  # More unique = less fusion = higher score

        # Combined risk score
        risk_score = (order_match_score * 0.5 + fusion_score * 0.5)

        if risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        issues = []
        if order_match_score >= 70:
            issues.append({
                "type": "predictable_order",
                "description": f"Section order matches academic template ({order_match_score}%)",
                "description_zh": f"章节顺序匹配学术模板（{order_match_score}%）",
                "severity": "high" if order_match_score >= 80 else "medium"
            })

        recommendations = []
        recommendations_zh = []

        if order_match_score >= 60:
            recommendations.append("Consider reordering or merging sections for more natural flow.")
            recommendations_zh.append("考虑重新排序或合并章节以获得更自然的流程。")

        if missing_sections:
            recommendations.append(f"Missing sections: {', '.join(missing_sections)}. This may be intentional.")
            recommendations_zh.append(f"缺少章节：{', '.join(missing_sections)}。这可能是有意为之。")

        if not recommendations:
            recommendations.append("Section order appears natural.")
            recommendations_zh.append("章节顺序看起来自然。")

        return SectionOrderResponse(
            risk_score=int(risk_score),
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            order_match_score=order_match_score,
            missing_sections=missing_sections,
            function_fusion_score=fusion_score,
            current_order=actual_order,
            expected_order=EXPECTED_ORDER
        )

    except Exception as e:
        logger.error(f"Section order analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_order_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for section reordering"""
    return await analyze_section_order(request)


@router.post("/apply")
async def apply_order_changes(request: SubstepBaseRequest):
    """Apply section order changes"""
    return await analyze_section_order(request)
