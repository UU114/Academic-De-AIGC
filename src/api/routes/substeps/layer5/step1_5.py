"""
Step 1.5: Transitions & Connectors (衔接与连接词检测)
Layer 5 Document Level

Detects:
- Explicit connectors at paragraph openings
- Formulaic topic sentences
- Summary endings
- Too-smooth transitions
检测段落衔接问题
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ConnectorTransitionResponse,
    RiskLevel,
)
from src.core.analyzer.transition import TransitionAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter()


class TransitionRequest(SubstepBaseRequest):
    """Request for transition analysis"""
    pass


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


@router.post("/analyze", response_model=ConnectorTransitionResponse)
async def analyze_transitions(request: TransitionRequest):
    """
    Step 1.5: Analyze paragraph transitions and connectors
    步骤 1.5：分析段落衔接和连接词

    Detects:
    - Explicit connectors at paragraph openings
    - Formulaic topic sentences
    - Summary endings
    - Too-smooth transitions
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 2:
            return ConnectorTransitionResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for transition analysis."],
                recommendations_zh=["文档过短，无法进行衔接分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                total_transitions=0,
                problematic_transitions=0,
                connector_density=0,
                explicit_connectors=[],
                transitions=[]
            )

        # Initialize transition analyzer
        analyzer = TransitionAnalyzer()

        # Analyze all transitions
        transition_results = analyzer.analyze_document_transitions(paragraphs)

        # Convert to response format
        transitions = []
        all_issues = []
        all_connectors = []
        total_score = 0
        problematic_count = 0

        for idx, result in enumerate(transition_results):
            # Convert issues
            issues = [
                {
                    "type": issue.type,
                    "description": issue.description,
                    "description_zh": issue.description_zh,
                    "severity": issue.severity,
                    "position": issue.position,
                    "word": issue.word
                }
                for issue in result.issues
            ]

            # Create transition result
            transition = {
                "transition_index": idx,
                "para_a_index": idx,
                "para_b_index": idx + 1,
                "para_a_ending": result.para_a_ending,
                "para_b_opening": result.para_b_opening,
                "smoothness_score": result.smoothness_score,
                "risk_level": result.risk_level,
                "issues": issues,
                "explicit_connectors": result.explicit_connectors,
                "has_topic_sentence_pattern": result.has_topic_sentence_pattern,
                "has_summary_ending": result.has_summary_ending,
                "semantic_overlap": result.semantic_overlap
            }
            transitions.append(transition)

            # Aggregate statistics
            total_score += result.smoothness_score
            if result.issues:
                problematic_count += 1

            # Collect all explicit connectors
            all_connectors.extend(result.explicit_connectors)

            # Build unified issues
            for issue in result.issues:
                all_issues.append({
                    "type": issue.type,
                    "description": issue.description,
                    "description_zh": issue.description_zh,
                    "severity": issue.severity,
                    "position": f"transition_{idx}",
                    "para_a_index": idx,
                    "para_b_index": idx + 1,
                    "word": issue.word
                })

        # Calculate overall statistics
        num_transitions = len(transition_results)
        overall_score = total_score // num_transitions if num_transitions > 0 else 0
        connector_density = (len(all_connectors) / len(paragraphs)) * 100 if paragraphs else 0

        # Determine overall risk level
        if overall_score >= 50:
            risk_level = RiskLevel.HIGH
        elif overall_score >= 25:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Generate recommendations
        recommendations = []
        recommendations_zh = []

        if connector_density > 30:
            recommendations.append("High connector density detected. Replace explicit connectors with semantic echoes.")
            recommendations_zh.append("检测到高连接词密度。建议用语义回声替换显性连接词。")

        topic_sentence_count = sum(1 for t in transitions if t.get("has_topic_sentence_pattern"))
        if topic_sentence_count > 0:
            recommendations.append(f"Formulaic topic sentences detected ({topic_sentence_count} times). Vary paragraph openings.")
            recommendations_zh.append(f"检测到公式化主题句（{topic_sentence_count}次）。建议变化段落开头。")

        summary_ending_count = sum(1 for t in transitions if t.get("has_summary_ending"))
        if summary_ending_count > 0:
            recommendations.append(f"Summary endings detected ({summary_ending_count} times). Consider using open-ended transitions.")
            recommendations_zh.append(f"检测到总结性结尾（{summary_ending_count}次）。建议使用开放式过渡。")

        if not recommendations:
            recommendations.append("Transitions look natural. No major issues detected.")
            recommendations_zh.append("衔接看起来自然。未检测到重大问题。")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ConnectorTransitionResponse(
            risk_score=overall_score,
            risk_level=risk_level,
            issues=all_issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms,
            total_transitions=num_transitions,
            problematic_transitions=problematic_count,
            connector_density=connector_density,
            explicit_connectors=list(set(all_connectors)),
            transitions=transitions
        )

    except Exception as e:
        logger.error(f"Transition analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_transitions(request: TransitionRequest):
    """
    Process and apply transition improvements
    处理并应用衔接改进
    """
    return await analyze_transitions(request)


@router.post("/ai-suggest")
async def get_transition_suggestions(request: TransitionRequest):
    """
    Get AI suggestions for transition improvements
    获取AI衔接改进建议
    """
    # This would call LLM for semantic echo suggestions
    # For now, return analysis results
    return await analyze_transitions(request)
