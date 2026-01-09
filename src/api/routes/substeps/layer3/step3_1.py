"""
Step 3.1: Paragraph Role Detection (段落角色识别)
Layer 3 Paragraph Level

Identify the functional role of each paragraph.
识别每个段落的功能角色。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re
from collections import Counter

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ParagraphRoleResponse,
    ParagraphRoleInfo,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Role keywords for detection
ROLE_KEYWORDS = {
    "introduction": {
        "keywords": ["this paper", "this study", "we present", "aim", "purpose", "objective", "investigate", "examine"],
        "weight": 1.0
    },
    "background": {
        "keywords": ["previously", "prior studies", "existing research", "literature", "has shown", "has been"],
        "weight": 1.0
    },
    "methodology": {
        "keywords": ["method", "approach", "procedure", "experiment", "data collection", "participants", "sample", "measure"],
        "weight": 1.0
    },
    "results": {
        "keywords": ["found", "results", "data", "showed", "demonstrated", "revealed", "indicated", "significant"],
        "weight": 1.0
    },
    "discussion": {
        "keywords": ["suggests", "implies", "consistent with", "contrary to", "interpretation", "implication"],
        "weight": 1.0
    },
    "conclusion": {
        "keywords": ["in conclusion", "therefore", "summary", "future", "finally", "in summary"],
        "weight": 1.0
    },
    "transition": {
        "keywords": ["having discussed", "turning to", "next", "now we", "moving on", "before we"],
        "weight": 0.8
    }
}


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip() and len(p.split()) >= 5]


def _detect_paragraph_role(para: str) -> tuple:
    """Detect paragraph role and confidence"""
    para_lower = para.lower()

    role_scores = {}
    keywords_found = {}

    for role, config in ROLE_KEYWORDS.items():
        score = 0
        found = []
        for kw in config["keywords"]:
            if kw in para_lower:
                score += config["weight"]
                found.append(kw)
        role_scores[role] = score
        keywords_found[role] = found

    if not role_scores or max(role_scores.values()) == 0:
        return "body", 0.5, []

    best_role = max(role_scores, key=role_scores.get)
    best_score = role_scores[best_role]

    # Normalize confidence
    confidence = min(0.95, 0.4 + best_score * 0.15)

    return best_role, confidence, keywords_found.get(best_role, [])


def _assign_section_index(para_index: int, total_paras: int) -> int:
    """Assign section index based on position"""
    if total_paras <= 3:
        return 0
    section_size = max(3, total_paras // 5)
    return para_index // section_size


def _check_role_matches_section(role: str, section_index: int, total_sections: int) -> bool:
    """Check if role matches expected section position"""
    # Simple heuristic: introduction at start, conclusion at end
    if section_index == 0 and role in ["introduction", "background"]:
        return True
    if section_index == total_sections - 1 and role in ["conclusion", "discussion"]:
        return True
    if role in ["methodology", "results", "discussion", "body"]:
        return True
    return False


@router.post("/analyze", response_model=ParagraphRoleResponse)
async def analyze_paragraph_roles(request: SubstepBaseRequest):
    """
    Step 3.1: Detect paragraph roles
    步骤 3.1：检测段落角色

    - Identifies functional role of each paragraph
    - Calculates role distribution
    - Detects uniformity issues
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 2:
            return ParagraphRoleResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for role analysis."],
                recommendations_zh=["文档过短，无法进行角色分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                paragraph_roles=[],
                role_distribution={},
                uniformity_score=0,
                missing_roles=[]
            )

        total_sections = max(1, len(paragraphs) // 3)
        paragraph_roles = []
        role_counts = Counter()

        for i, para in enumerate(paragraphs):
            role, confidence, keywords = _detect_paragraph_role(para)
            section_index = _assign_section_index(i, len(paragraphs))
            role_matches = _check_role_matches_section(role, section_index, total_sections)

            paragraph_roles.append(ParagraphRoleInfo(
                paragraph_index=i,
                role=role,
                confidence=confidence,
                section_index=section_index,
                role_matches_section=role_matches,
                keywords_found=keywords
            ))
            role_counts[role] += 1

        # Calculate uniformity score (higher = more uniform = AI-like)
        unique_roles = len(role_counts)
        total_paras = len(paragraphs)

        if unique_roles <= 1:
            uniformity_score = 1.0
        elif unique_roles >= 5:
            uniformity_score = 0.3
        else:
            uniformity_score = 1.0 - (unique_roles / 7)

        # Find missing expected roles
        expected_roles = {"introduction", "methodology", "results", "conclusion"}
        present_roles = set(role_counts.keys())
        missing_roles = list(expected_roles - present_roles)

        # Calculate risk score
        risk_score = 0

        if uniformity_score > 0.8:
            risk_score += 40
        elif uniformity_score > 0.6:
            risk_score += 20

        if len(missing_roles) >= 2:
            risk_score += 20
        elif len(missing_roles) >= 1:
            risk_score += 10

        # Count role mismatches
        mismatch_count = sum(1 for pr in paragraph_roles if not pr.role_matches_section)
        if mismatch_count > len(paragraphs) * 0.3:
            risk_score += 20

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []

        if uniformity_score > 0.7:
            issues.append({
                "type": "high_uniformity",
                "description": f"Paragraph roles are too uniform ({uniformity_score:.0%})",
                "description_zh": f"段落角色过于单一（{uniformity_score:.0%}）",
                "severity": "high" if uniformity_score > 0.8 else "medium"
            })

        if missing_roles:
            issues.append({
                "type": "missing_roles",
                "description": f"Missing key roles: {', '.join(missing_roles)}",
                "description_zh": f"缺少关键角色：{', '.join(missing_roles)}",
                "severity": "medium"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if uniformity_score > 0.6:
            recommendations.append("Add more variety in paragraph functions. Include transitions and mixed-role paragraphs.")
            recommendations_zh.append("增加段落功能的多样性。添加过渡段落和混合角色段落。")

        if "transition" not in present_roles:
            recommendations.append("Consider adding transition paragraphs between major sections.")
            recommendations_zh.append("考虑在主要章节之间添加过渡段落。")

        if not issues:
            recommendations.append("Paragraph roles show good variety.")
            recommendations_zh.append("段落角色显示良好的多样性。")

        return ParagraphRoleResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            paragraph_roles=paragraph_roles,
            role_distribution=dict(role_counts),
            uniformity_score=round(uniformity_score, 3),
            missing_roles=missing_roles
        )

    except Exception as e:
        logger.error(f"Paragraph role detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-role")
async def update_paragraph_role(request: SubstepBaseRequest):
    """Manually update paragraph role"""
    return await analyze_paragraph_roles(request)
