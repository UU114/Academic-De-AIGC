"""
Step 1.3: Logic Pattern & Closure Detection (推进模式与闭合检测)
Layer 5 Document Level

Detects:
- Monotonic progression (AI-like)
- Strong closure patterns (AI-like)
- Sequential markers (First, Second, Third...)
检测推进模式和闭合强度
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    LogicPatternResponse,
    RiskLevel,
)
from src.core.analyzer.structure_predictability import StructurePredictabilityAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter()


class LogicPatternRequest(SubstepBaseRequest):
    """Request for logic pattern analysis"""
    pass


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


@router.post("/analyze", response_model=LogicPatternResponse)
async def analyze_logic_pattern(request: LogicPatternRequest):
    """
    Step 1.3: Analyze progression and closure patterns
    步骤 1.3：分析推进模式和闭合强度

    Detects:
    - Monotonic progression (sequential, additive, one-directional)
    - Non-monotonic (returns, conditionals, reversals)
    - Strong closure (definitive conclusions)
    - Weak closure (open questions, unresolved tensions)
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 3:
            return LogicPatternResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for progression/closure analysis."],
                recommendations_zh=["文档过短，无法进行推进/闭合分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                progression_score=0,
                progression_type="unknown",
                closure_score=0,
                closure_type="unknown",
                sequential_markers_count=0,
                progression_markers=[]
            )

        # Use StructurePredictabilityAnalyzer
        analyzer = StructurePredictabilityAnalyzer()
        result = analyzer.analyze(paragraphs)

        # Extract progression details
        prog_details = result.details.get("progression", {})
        markers_data = prog_details.get("markers", {"monotonic": [], "non_monotonic": []})

        # Build progression markers list
        progression_markers = []
        for m in markers_data.get("monotonic", []):
            progression_markers.append({
                "paragraph_index": m.get("paragraph", 0),
                "marker": m.get("marker", ""),
                "category": m.get("category", "unknown"),
                "is_monotonic": True
            })
        for m in markers_data.get("non_monotonic", []):
            progression_markers.append({
                "paragraph_index": m.get("paragraph", 0),
                "marker": m.get("marker", ""),
                "category": m.get("category", "unknown"),
                "is_monotonic": False
            })

        # Extract closure details
        closure_details = result.details.get("closure", {})

        # Map progression type
        prog_type_map = {
            "monotonic": "monotonic",
            "non_monotonic": "non_monotonic",
            "mixed": "mixed",
        }
        prog_type = prog_type_map.get(result.progression_type, "unknown")

        # Map closure type
        closure_type_map = {
            "strong": "strong",
            "moderate": "moderate",
            "weak": "weak",
            "open": "open",
        }
        closure_type = closure_type_map.get(result.closure_type, "moderate")

        # Calculate combined score
        combined_score = (result.progression_predictability + result.closure_strength) // 2

        # Determine risk level
        if combined_score >= 60:
            risk_level = RiskLevel.HIGH
        elif combined_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Build issues
        issues = []
        if result.progression_predictability > 60:
            issues.append({
                "type": "monotonic_progression",
                "description": f"Progression is too predictable (score: {result.progression_predictability})",
                "description_zh": f"推进过于可预测（分数：{result.progression_predictability}）",
                "severity": "high" if result.progression_predictability > 75 else "medium",
                "position": "document"
            })

        if result.closure_strength > 60:
            issues.append({
                "type": "strong_closure",
                "description": f"Closure is too strong (score: {result.closure_strength})",
                "description_zh": f"闭合过于强烈（分数：{result.closure_strength}）",
                "severity": "medium",
                "position": "document"
            })

        sequential_markers = prog_details.get("sequential_markers", 0)
        if sequential_markers >= 3:
            issues.append({
                "type": "sequential_markers",
                "description": f"Multiple sequential markers detected: {sequential_markers}",
                "description_zh": f"检测到多个顺序标记：{sequential_markers}个",
                "severity": "high",
                "position": "document"
            })

        # Generate recommendations
        recommendations = []
        recommendations_zh = []

        if result.progression_predictability > 60:
            recommendations.append(
                "Progression is too predictable (monotonic). Add returns to earlier points, "
                "conditionals, or local reversals to break the linear flow."
            )
            recommendations_zh.append(
                "推进过于可预测（单调）。添加回扣、条件触发或局部反转来打破线性流动。"
            )

        if result.closure_strength > 60:
            recommendations.append(
                "Closure is too strong. Consider ending with an open question or "
                "unresolved tension instead of a definitive summary."
            )
            recommendations_zh.append(
                "闭合过于强烈。考虑以开放问题或未解决的张力结尾，而非明确总结。"
            )

        if sequential_markers >= 3:
            recommendations.append(
                "Multiple sequential markers detected (First, Second, Third...). "
                "This is a strong AI signal. Vary your transitions."
            )
            recommendations_zh.append(
                "检测到多个顺序标记（First, Second, Third...）。"
                "这是强烈的AI信号。请变化您的过渡方式。"
            )

        if not recommendations:
            recommendations.append("Progression and closure patterns look natural.")
            recommendations_zh.append("推进和闭合模式看起来自然。")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return LogicPatternResponse(
            risk_score=combined_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms,
            progression_score=result.progression_predictability,
            progression_type=prog_type,
            closure_score=result.closure_strength,
            closure_type=closure_type,
            sequential_markers_count=sequential_markers,
            progression_markers=progression_markers
        )

    except Exception as e:
        logger.error(f"Logic pattern analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_logic_pattern(request: LogicPatternRequest):
    """
    Process and apply logic pattern improvements
    处理并应用逻辑模式改进
    """
    return await analyze_logic_pattern(request)
