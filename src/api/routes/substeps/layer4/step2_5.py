"""
Step 2.5: Inter-Section Logic Detection (章节间逻辑关系检测)
Layer 4 Section Level

Detects:
- Argument chain completeness (too perfect = AI)
- Inter-section information redundancy
- Progression pattern (too linear = AI)
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    InterSectionLogicResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Preview/summary patterns (AI-like redundancy)
PREVIEW_PATTERNS = [
    r"the (?:next|following) section (?:will|shall)",
    r"we will (?:now |then )?(?:discuss|examine|explore|present)",
    r"in the (?:next|following) section",
    r"this (?:will be|is) discussed (?:in|below)",
    r"as will be shown"
]

SUMMARY_PATTERNS = [
    r"as (?:discussed|mentioned|noted) (?:above|previously|earlier)",
    r"in (?:the previous|preceding) section",
    r"to summarize",
    r"in summary",
    r"having (?:established|demonstrated|shown)",
    r"as we have seen"
]

# Argument chain markers
CAUSAL_MARKERS = [
    "therefore", "thus", "hence", "consequently", "as a result",
    "this leads to", "this demonstrates", "this proves", "this shows"
]

PROGRESSION_MARKERS = [
    "first", "second", "third", "finally", "next", "then",
    "subsequently", "following this", "building on this"
]


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _detect_redundancy_patterns(text: str) -> Dict[str, List[Dict]]:
    """Detect preview and summary redundancy patterns"""
    text_lower = text.lower()
    results = {"previews": [], "summaries": []}

    for pattern in PREVIEW_PATTERNS:
        matches = list(re.finditer(pattern, text_lower))
        for m in matches:
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 50)
            results["previews"].append({
                "pattern": pattern,
                "match": m.group(),
                "context": text[start:end],
                "position": m.start()
            })

    for pattern in SUMMARY_PATTERNS:
        matches = list(re.finditer(pattern, text_lower))
        for m in matches:
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 50)
            results["summaries"].append({
                "pattern": pattern,
                "match": m.group(),
                "context": text[start:end],
                "position": m.start()
            })

    return results


def _analyze_argument_chain(paragraphs: List[str]) -> Dict[str, Any]:
    """Analyze argument chain completeness"""
    causal_count = 0
    total_paragraphs = len(paragraphs)

    causal_locations = []
    for i, para in enumerate(paragraphs):
        para_lower = para.lower()
        for marker in CAUSAL_MARKERS:
            if marker in para_lower:
                causal_count += 1
                causal_locations.append({
                    "paragraph_index": i,
                    "marker": marker,
                    "preview": para[:80] + "..." if len(para) > 80 else para
                })
                break  # Count once per paragraph

    # Calculate causal density
    causal_density = causal_count / max(1, total_paragraphs)

    # Check for perfect chain (high risk if too many causal links)
    chain_score = min(100, causal_density * 200)  # 50% causal = 100 score

    return {
        "causal_count": causal_count,
        "causal_density": causal_density,
        "chain_completeness_score": chain_score,
        "causal_locations": causal_locations
    }


def _analyze_progression_pattern(paragraphs: List[str]) -> Dict[str, Any]:
    """Analyze if progression is too linear"""
    text_lower = " ".join(paragraphs).lower()

    # Count progression markers
    progression_count = 0
    found_markers = []
    for marker in PROGRESSION_MARKERS:
        count = text_lower.count(marker)
        if count > 0:
            progression_count += count
            found_markers.append({"marker": marker, "count": count})

    # Check for numbered sequence (1, 2, 3...)
    number_sequences = len(re.findall(r'\b(?:first|second|third|fourth|fifth)\b', text_lower))

    # Calculate linearity score
    total_words = len(text_lower.split())
    progression_density = progression_count / max(1, total_words) * 1000  # per 1000 words

    # High density = high risk
    if progression_density > 10:
        linearity_score = 90
    elif progression_density > 5:
        linearity_score = 70
    elif progression_density > 3:
        linearity_score = 50
    else:
        linearity_score = 30

    return {
        "progression_count": progression_count,
        "progression_density": progression_density,
        "linearity_score": linearity_score,
        "found_markers": found_markers,
        "number_sequences": number_sequences
    }


@router.post("/analyze", response_model=InterSectionLogicResponse)
async def analyze_inter_section_logic(request: SubstepBaseRequest):
    """
    Step 2.5: Analyze inter-section logical relationships
    步骤 2.5：分析章节间逻辑关系

    Detects:
    - Argument chain completeness (perfect chain = AI risk)
    - Inter-section redundancy (excessive previews/summaries)
    - Progression pattern (perfect linear = AI risk)
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 3:
            return InterSectionLogicResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for logic analysis."],
                recommendations_zh=["文档过短，无法进行逻辑分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                argument_chain_score=0,
                redundancy_issues=[],
                progression_pattern="unknown",
                causal_density=0.0,
                linearity_score=0
            )

        # Analyze argument chain
        chain_analysis = _analyze_argument_chain(paragraphs)

        # Detect redundancy
        redundancy = _detect_redundancy_patterns(request.text)
        redundancy_issues = []
        for preview in redundancy["previews"]:
            redundancy_issues.append({
                "type": "excessive_preview",
                "description": f"Preview phrase: '{preview['match']}'",
                "description_zh": f"预告短语：'{preview['match']}'",
                "context": preview["context"],
                "position": preview["position"]
            })
        for summary in redundancy["summaries"]:
            redundancy_issues.append({
                "type": "excessive_summary",
                "description": f"Summary phrase: '{summary['match']}'",
                "description_zh": f"总结短语：'{summary['match']}'",
                "context": summary["context"],
                "position": summary["position"]
            })

        # Analyze progression
        progression_analysis = _analyze_progression_pattern(paragraphs)

        # Determine progression pattern type
        if progression_analysis["linearity_score"] > 70:
            progression_pattern = "perfect_linear"
        elif progression_analysis["linearity_score"] > 50:
            progression_pattern = "mostly_linear"
        else:
            progression_pattern = "natural"

        # Calculate risk score
        risk_score = 0

        # Chain completeness risk
        if chain_analysis["chain_completeness_score"] > 70:
            risk_score += 35
        elif chain_analysis["chain_completeness_score"] > 50:
            risk_score += 20

        # Redundancy risk
        redundancy_count = len(redundancy_issues)
        if redundancy_count >= 4:
            risk_score += 30
        elif redundancy_count >= 2:
            risk_score += 15

        # Linearity risk
        if progression_analysis["linearity_score"] > 70:
            risk_score += 25
        elif progression_analysis["linearity_score"] > 50:
            risk_score += 15

        # Determine risk level
        if risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Build issues
        issues = []

        if chain_analysis["chain_completeness_score"] > 70:
            issues.append({
                "type": "perfect_chain",
                "description": f"Argument chain is too perfect ({chain_analysis['chain_completeness_score']:.0f}% completeness)",
                "description_zh": f"论证链过于完美（完整度 {chain_analysis['chain_completeness_score']:.0f}%）",
                "severity": "high" if chain_analysis["chain_completeness_score"] > 80 else "medium"
            })

        if redundancy_count >= 2:
            issues.append({
                "type": "redundant_transitions",
                "description": f"Too many preview/summary phrases ({redundancy_count} found)",
                "description_zh": f"预告/总结短语过多（发现 {redundancy_count} 个）",
                "severity": "high" if redundancy_count >= 4 else "medium"
            })

        if progression_pattern == "perfect_linear":
            issues.append({
                "type": "linear_progression",
                "description": "Progression pattern is too linear (A→B→C→D without branches)",
                "description_zh": "递进模式过于线性（A→B→C→D无分支）",
                "severity": "high"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if chain_analysis["chain_completeness_score"] > 50:
            recommendations.append("Add some open-ended questions or unresolved tensions to break the perfect chain.")
            recommendations_zh.append("添加一些开放性问题或未解决的张力来打破完美的论证链。")

        if redundancy_count >= 2:
            recommendations.append("Remove excessive preview/summary phrases between sections.")
            recommendations_zh.append("删除章节间过多的预告/总结短语。")

        if progression_pattern != "natural":
            recommendations.append("Add non-linear elements like digressions, side notes, or unexpected findings.")
            recommendations_zh.append("添加非线性元素，如旁支、附注或意外发现。")

        if not issues:
            recommendations.append("Inter-section logic appears natural.")
            recommendations_zh.append("章节间逻辑关系看起来自然。")

        return InterSectionLogicResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            argument_chain_score=int(chain_analysis["chain_completeness_score"]),
            redundancy_issues=redundancy_issues,
            progression_pattern=progression_pattern,
            causal_density=round(chain_analysis["causal_density"], 3),
            linearity_score=progression_analysis["linearity_score"]
        )

    except Exception as e:
        logger.error(f"Inter-section logic analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_logic_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for logic improvements"""
    return await analyze_inter_section_logic(request)


@router.post("/apply")
async def apply_logic_changes(request: SubstepBaseRequest):
    """Apply logic modifications"""
    return await analyze_inter_section_logic(request)
