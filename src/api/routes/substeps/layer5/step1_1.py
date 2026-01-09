"""
Step 1.1: Structure Framework Detection (结构框架检测)
Layer 5 Document Level

Detects document structure for AI-like patterns:
- Section symmetry
- Predictable order
- Linear flow
检测文档结构中的AI模式特征
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    StructureAnalysisResponse,
    RiskLevel,
)
from src.core.analyzer.structure_predictability import StructurePredictabilityAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter()


class StructureAnalyzeRequest(SubstepBaseRequest):
    """Request for structure analysis"""
    pass


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _detect_sections(paragraphs: List[str]) -> List[Dict[str, Any]]:
    """
    Detect sections from paragraphs (basic heuristic)
    从段落中检测章节（基础启发式方法）
    """
    sections = []
    current_section = {
        "index": 0,
        "role": "introduction",
        "paragraphs": [],
        "word_count": 0
    }

    # Section role keywords
    role_keywords = {
        "introduction": ["introduction", "background", "overview", "this paper", "this study"],
        "literature_review": ["literature", "review", "previous", "prior", "existing"],
        "methodology": ["method", "approach", "procedure", "experiment", "data collection"],
        "results": ["result", "finding", "outcome", "showed", "demonstrated"],
        "discussion": ["discussion", "implication", "analysis", "interpretation"],
        "conclusion": ["conclusion", "summary", "future", "in conclusion"]
    }

    for i, para in enumerate(paragraphs):
        para_lower = para.lower()
        word_count = len(para.split())

        # Check if this paragraph starts a new section
        detected_role = None
        for role, keywords in role_keywords.items():
            if any(kw in para_lower for kw in keywords):
                detected_role = role
                break

        # If significant role change, start new section
        if detected_role and detected_role != current_section["role"] and current_section["paragraphs"]:
            sections.append(current_section)
            current_section = {
                "index": len(sections),
                "role": detected_role,
                "paragraphs": [i],
                "word_count": word_count
            }
        else:
            current_section["paragraphs"].append(i)
            current_section["word_count"] += word_count

    # Add last section
    if current_section["paragraphs"]:
        sections.append(current_section)

    return sections


@router.post("/analyze", response_model=StructureAnalysisResponse)
async def analyze_structure(request: StructureAnalyzeRequest):
    """
    Step 1.1: Analyze document structure for AI-like patterns
    步骤 1.1：分析文档结构中的AI特征

    Detects:
    - Section symmetry (balanced section sizes)
    - Predictable order (template-like structure)
    - Linear flow (First-Second-Third patterns)
    - Progression predictability
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 3:
            return StructureAnalysisResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for structure analysis."],
                recommendations_zh=["文档过短，无法进行结构分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                symmetry_score=0,
                predictability_score=0,
                linear_flow_score=0,
                progression_type="unknown",
                sections=[]
            )

        # Analyze structure predictability
        analyzer = StructurePredictabilityAnalyzer()
        result = analyzer.analyze(paragraphs)

        # Detect sections
        sections = _detect_sections(paragraphs)

        # Calculate symmetry score (based on section size variance)
        section_sizes = [s["word_count"] for s in sections]
        if len(section_sizes) > 1:
            mean_size = sum(section_sizes) / len(section_sizes)
            variance = sum((s - mean_size) ** 2 for s in section_sizes) / len(section_sizes)
            cv = (variance ** 0.5) / mean_size if mean_size > 0 else 0
            # Lower CV = higher symmetry = higher AI risk
            symmetry_score = max(0, int(100 * (1 - cv)))
        else:
            symmetry_score = 50

        # Calculate predictability based on section order
        expected_order = ["introduction", "literature_review", "methodology", "results", "discussion", "conclusion"]
        actual_order = [s["role"] for s in sections]
        order_matches = sum(1 for i, role in enumerate(actual_order) if i < len(expected_order) and role == expected_order[i])
        predictability_score = int(100 * order_matches / len(expected_order)) if expected_order else 0

        # Linear flow from analyzer
        prog_details = result.details.get("progression", {})
        sequential_markers = prog_details.get("sequential_markers", 0)
        linear_flow_score = min(100, sequential_markers * 25)  # 4+ sequential markers = 100

        # Combined risk score
        risk_score = (symmetry_score * 0.3 + predictability_score * 0.4 + linear_flow_score * 0.3)
        risk_score = int(risk_score)

        # Determine risk level
        if risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Build issues list
        issues = []
        if symmetry_score >= 70:
            issues.append({
                "type": "section_symmetry",
                "description": f"Sections are too balanced in size (symmetry score: {symmetry_score})",
                "description_zh": f"章节大小过于平衡（对称分数：{symmetry_score}）",
                "severity": "high" if symmetry_score >= 80 else "medium",
                "position": "document"
            })

        if predictability_score >= 70:
            issues.append({
                "type": "predictable_order",
                "description": f"Section order follows academic template too closely ({predictability_score}% match)",
                "description_zh": f"章节顺序过于接近学术模板（{predictability_score}% 匹配）",
                "severity": "high" if predictability_score >= 80 else "medium",
                "position": "document"
            })

        if linear_flow_score >= 50:
            issues.append({
                "type": "linear_flow",
                "description": f"Detected First-Second-Third enumeration pattern ({sequential_markers} markers)",
                "description_zh": f"检测到 First-Second-Third 枚举模式（{sequential_markers}个标记）",
                "severity": "high" if linear_flow_score >= 75 else "medium",
                "position": "document"
            })

        # Generate recommendations
        recommendations = []
        recommendations_zh = []

        if symmetry_score >= 60:
            recommendations.append("Section sizes are too balanced. Expand core sections and condense background sections.")
            recommendations_zh.append("章节大小过于平衡。扩展核心章节，压缩背景章节。")

        if predictability_score >= 60:
            recommendations.append("Structure follows academic template too closely. Consider merging or reordering sections.")
            recommendations_zh.append("结构过于遵循学术模板。考虑合并或重新排列章节。")

        if linear_flow_score >= 50:
            recommendations.append("Replace sequential markers (First, Second, Third) with varied transitions.")
            recommendations_zh.append("将顺序标记（First, Second, Third）替换为多样化的过渡方式。")

        if not recommendations:
            recommendations.append("Structure appears natural. No major issues detected.")
            recommendations_zh.append("结构看起来自然。未检测到重大问题。")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return StructureAnalysisResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms,
            symmetry_score=symmetry_score,
            predictability_score=predictability_score,
            linear_flow_score=linear_flow_score,
            progression_type=result.progression_type,
            sections=sections
        )

    except Exception as e:
        logger.error(f"Structure analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_structure_issues(request: StructureAnalyzeRequest):
    """
    Process and apply structure improvements
    处理并应用结构改进
    """
    # This endpoint would be implemented to apply AI suggestions
    # For now, return analysis results
    return await analyze_structure(request)
