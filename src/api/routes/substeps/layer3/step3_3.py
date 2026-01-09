"""
Step 3.3: Anchor Density Analysis (锚点密度分析)
Layer 3 Paragraph Level

Detect academic anchors (data, citations, evidence) and identify AI filler content.
检测学术锚点（数据、引用、证据）并识别AI填充内容。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re
from collections import defaultdict

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    AnchorDensityResponse,
    ParagraphAnchorInfo,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# 13 types of academic anchors with regex patterns
ANCHOR_PATTERNS = {
    "decimal_number": r'\d+\.\d+(?![\d\w])',
    "percentage": r'\d+(?:\.\d+)?%',
    "statistical_value": r'(?:p\s*[<>=]\s*0?\.\d+|r\s*=\s*0?\.\d+|χ²?\s*=\s*\d+)',
    "sample_size": r'[Nn]\s*=\s*\d+',
    "citation_bracket": r'\[\d+(?:[-,]\d+)*\]',
    "citation_author": r'\([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&|and)\s*[A-Z]?[a-z]*)?[,;]?\s*\d{4}\)',
    "unit_measurement": r'\d+(?:\.\d+)?\s*(?:mL|mg|kg|cm|mm|°C|°F|Hz|kHz|MHz)',
    "chemical_formula": r'\b(?:H2O|CO2|NaCl|O2|N2|CH4|C\d+H\d+)\b',
    "specific_count": r'\d+\s+(?:samples?|participants?|subjects?|groups?|items?|trials?)',
    "scientific_notation": r'\d+(?:\.\d+)?(?:e|×10\^?)[−+-]?\d+',
    "acronym": r'\b[A-Z]{2,5}\b(?!\s+[a-z])',
    "equation_ref": r'(?:Eq(?:uation)?\.?\s*\(?\d+\)?|Equation\s+\d+)',
    "figure_table_ref": r'(?:Fig(?:ure)?\.?\s*\d+|Table\s+\d+)',
}

# Weights for different anchor types
ANCHOR_WEIGHTS = {
    "decimal_number": 1.0,
    "percentage": 1.2,
    "statistical_value": 1.5,
    "sample_size": 1.3,
    "citation_bracket": 1.5,
    "citation_author": 1.5,
    "unit_measurement": 1.3,
    "chemical_formula": 1.2,
    "specific_count": 1.4,
    "scientific_notation": 1.3,
    "acronym": 1.0,
    "equation_ref": 1.4,
    "figure_table_ref": 1.4,
}


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip() and len(p.split()) >= 10]


def _count_anchors(text: str) -> Dict[str, int]:
    """Count all anchor types in text"""
    counts = defaultdict(int)

    for anchor_type, pattern in ANCHOR_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        counts[anchor_type] = len(matches)

    return dict(counts)


def _calculate_weighted_density(anchor_counts: Dict[str, int], word_count: int) -> float:
    """Calculate weighted anchor density per 100 words"""
    if word_count == 0:
        return 0

    weighted_sum = sum(
        count * ANCHOR_WEIGHTS.get(atype, 1.0)
        for atype, count in anchor_counts.items()
    )

    density = (weighted_sum / word_count) * 100
    return round(density, 2)


def _assess_hallucination_risk(density: float, word_count: int) -> tuple:
    """Assess hallucination risk based on density"""
    if word_count < 30:
        return False, "low"

    if density < 3.0:
        return True, "high"
    elif density < 6.0:
        return True, "medium"
    else:
        return False, "low"


@router.post("/analyze", response_model=AnchorDensityResponse)
async def analyze_anchor_density(request: SubstepBaseRequest):
    """
    Step 3.3: Analyze anchor density
    步骤 3.3：分析锚点密度

    - Detects 13 types of academic anchors
    - Calculates paragraph-level density
    - Identifies potential AI filler content (low anchors)
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 1:
            return AnchorDensityResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for anchor analysis."],
                recommendations_zh=["文档过短，无法进行锚点分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                overall_density=0,
                paragraph_densities=[],
                high_risk_paragraphs=[],
                anchor_type_distribution={},
                document_hallucination_risk="low"
            )

        paragraph_densities = []
        high_risk_paragraphs = []
        total_anchor_counts = defaultdict(int)
        total_words = 0
        total_weighted_anchors = 0

        for i, para in enumerate(paragraphs):
            word_count = len(para.split())
            anchor_counts = _count_anchors(para)
            density = _calculate_weighted_density(anchor_counts, word_count)
            has_risk, risk_level = _assess_hallucination_risk(density, word_count)

            # Aggregate totals
            total_words += word_count
            for atype, count in anchor_counts.items():
                total_anchor_counts[atype] += count
                total_weighted_anchors += count * ANCHOR_WEIGHTS.get(atype, 1.0)

            if has_risk:
                high_risk_paragraphs.append(i)

            paragraph_densities.append(ParagraphAnchorInfo(
                paragraph_index=i,
                word_count=word_count,
                anchor_count=sum(anchor_counts.values()),
                density=density,
                has_hallucination_risk=has_risk,
                risk_level=risk_level,
                anchor_types=anchor_counts
            ))

        # Calculate overall density
        overall_density = (total_weighted_anchors / total_words) * 100 if total_words > 0 else 0

        # Determine document-level risk
        high_risk_ratio = len(high_risk_paragraphs) / len(paragraphs) if paragraphs else 0

        if high_risk_ratio > 0.4:
            doc_risk = "high"
        elif high_risk_ratio > 0.2:
            doc_risk = "medium"
        else:
            doc_risk = "low"

        # Calculate risk score
        if doc_risk == "high":
            risk_score = 70 + int(high_risk_ratio * 30)
        elif doc_risk == "medium":
            risk_score = 40 + int(high_risk_ratio * 30)
        else:
            risk_score = 20

        risk_level_enum = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []

        if len(high_risk_paragraphs) > 0:
            issues.append({
                "type": "low_anchor_density",
                "description": f"{len(high_risk_paragraphs)} paragraphs have low anchor density (potential AI filler)",
                "description_zh": f"{len(high_risk_paragraphs)} 个段落锚点密度低（可能是AI填充内容）",
                "severity": "high" if len(high_risk_paragraphs) >= 3 else "medium",
                "paragraphs": high_risk_paragraphs
            })

        if overall_density < 5.0:
            issues.append({
                "type": "overall_low_density",
                "description": f"Overall anchor density is low ({overall_density:.1f}/100 words)",
                "description_zh": f"整体锚点密度较低（{overall_density:.1f}/100词）",
                "severity": "medium"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if high_risk_paragraphs:
            recommendations.append("Add specific data, citations, or evidence to low-density paragraphs.")
            recommendations_zh.append("在低密度段落中添加具体数据、引用或证据。")

        if total_anchor_counts.get("citation_bracket", 0) + total_anchor_counts.get("citation_author", 0) == 0:
            recommendations.append("Consider adding citations to support your claims.")
            recommendations_zh.append("考虑添加引用来支持你的论点。")

        if not issues:
            recommendations.append("Anchor density appears sufficient for academic writing.")
            recommendations_zh.append("锚点密度对于学术写作来说足够。")

        return AnchorDensityResponse(
            risk_score=risk_score,
            risk_level=risk_level_enum,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            overall_density=round(overall_density, 2),
            paragraph_densities=paragraph_densities,
            high_risk_paragraphs=high_risk_paragraphs,
            anchor_type_distribution=dict(total_anchor_counts),
            document_hallucination_risk=doc_risk
        )

    except Exception as e:
        logger.error(f"Anchor density analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_anchor_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for adding anchors"""
    return await analyze_anchor_density(request)
