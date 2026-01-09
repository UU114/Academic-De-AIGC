"""
Step 2.2: Section Length Distribution (章节长度分布检测)
Layer 4 Section Level
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re
import statistics

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SectionLengthResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


@router.post("/analyze", response_model=SectionLengthResponse)
async def analyze_section_length(request: SubstepBaseRequest):
    """
    Step 2.2: Analyze section length distribution
    步骤 2.2：分析章节长度分布

    Detects:
    - Section length CV (< 0.3 = too uniform = AI-like)
    - Extreme length sections
    - Key section weight issues
    - Paragraph count variance
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        # Group paragraphs into sections (basic heuristic)
        section_word_counts = []
        section_para_counts = []
        current_section_words = 0
        current_section_paras = 0

        for i, para in enumerate(paragraphs):
            word_count = len(para.split())
            current_section_words += word_count
            current_section_paras += 1

            # Simple section break heuristic: every 3-4 paragraphs
            if current_section_paras >= 3 and (i + 1) % 3 == 0:
                section_word_counts.append(current_section_words)
                section_para_counts.append(current_section_paras)
                current_section_words = 0
                current_section_paras = 0

        # Add last section
        if current_section_paras > 0:
            section_word_counts.append(current_section_words)
            section_para_counts.append(current_section_paras)

        # Calculate length CV
        if len(section_word_counts) > 1:
            mean_len = statistics.mean(section_word_counts)
            stdev_len = statistics.stdev(section_word_counts)
            length_cv = stdev_len / mean_len if mean_len > 0 else 0
        else:
            length_cv = 0

        # Calculate paragraph count CV
        if len(section_para_counts) > 1:
            mean_para = statistics.mean(section_para_counts)
            stdev_para = statistics.stdev(section_para_counts)
            para_cv = stdev_para / mean_para if mean_para > 0 else 0
        else:
            para_cv = 0

        # Build section info
        sections = []
        mean_len = statistics.mean(section_word_counts) if section_word_counts else 0
        for i, (wc, pc) in enumerate(zip(section_word_counts, section_para_counts)):
            sections.append({
                "index": i,
                "word_count": wc,
                "paragraph_count": pc,
                "ratio_to_mean": round(wc / mean_len, 2) if mean_len > 0 else 1.0
            })

        # Find extreme sections
        extreme_sections = []
        for i, wc in enumerate(section_word_counts):
            if wc < 100 or wc > mean_len * 3:
                extreme_sections.append(i)

        # Calculate risk score
        if length_cv < 0.2:
            risk_score = 90
        elif length_cv < 0.3:
            risk_score = 70
        elif length_cv < 0.4:
            risk_score = 50
        else:
            risk_score = 30

        if risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        issues = []
        if length_cv < 0.3:
            issues.append({
                "type": "uniform_section_length",
                "description": f"Section lengths too uniform (CV={length_cv:.2f})",
                "description_zh": f"章节长度过于均匀（CV={length_cv:.2f}）",
                "severity": "high" if length_cv < 0.2 else "medium"
            })

        if para_cv < 0.3:
            issues.append({
                "type": "uniform_paragraph_count",
                "description": f"Paragraph counts per section too uniform (CV={para_cv:.2f})",
                "description_zh": f"每章节段落数过于均匀（CV={para_cv:.2f}）",
                "severity": "medium"
            })

        recommendations = []
        recommendations_zh = []

        if length_cv < 0.3:
            recommendations.append("Expand core sections and condense background sections for more natural variation.")
            recommendations_zh.append("扩展核心章节，压缩背景章节以获得更自然的变化。")

        if not issues:
            recommendations.append("Section length distribution appears natural.")
            recommendations_zh.append("章节长度分布看起来自然。")

        return SectionLengthResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            length_cv=round(length_cv, 3),
            paragraph_count_cv=round(para_cv, 3),
            sections=sections,
            extreme_sections=extreme_sections,
            key_weight_issues=[]
        )

    except Exception as e:
        logger.error(f"Section length analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_length_suggestions(request: SubstepBaseRequest):
    return await analyze_section_length(request)


@router.post("/apply")
async def apply_length_changes(request: SubstepBaseRequest):
    return await analyze_section_length(request)
