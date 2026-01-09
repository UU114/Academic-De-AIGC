"""
Step 2.0: Section Identification (章节识别与角色标注)
Layer 4 Section Level

Automatically detect section boundaries and identify functional roles
自动检测章节边界并识别功能角色
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SectionIdentifyResponse,
    SectionInfo,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class SectionIdentifyRequest(SubstepBaseRequest):
    """Request for section identification"""
    pass


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _detect_section_role(text: str) -> tuple:
    """
    Detect section role from text content
    Returns (role, confidence)
    """
    text_lower = text.lower()

    # Role keyword patterns with weights
    role_patterns = {
        "introduction": {
            "keywords": ["introduction", "background", "overview", "this paper", "this study", "we present"],
            "weight": 1.0
        },
        "literature_review": {
            "keywords": ["literature", "review", "previous", "prior", "existing research", "related work"],
            "weight": 1.0
        },
        "methodology": {
            "keywords": ["method", "approach", "procedure", "experiment", "data collection", "participants", "materials"],
            "weight": 1.0
        },
        "results": {
            "keywords": ["result", "finding", "outcome", "showed", "demonstrated", "analysis", "data"],
            "weight": 1.0
        },
        "discussion": {
            "keywords": ["discussion", "implication", "interpretation", "consistent with", "contrary to"],
            "weight": 1.0
        },
        "conclusion": {
            "keywords": ["conclusion", "summary", "future", "in conclusion", "in summary", "finally"],
            "weight": 1.0
        }
    }

    best_role = "body"
    best_score = 0
    best_confidence = 0.5

    for role, config in role_patterns.items():
        score = sum(1 for kw in config["keywords"] if kw in text_lower)
        if score > best_score:
            best_score = score
            best_role = role
            best_confidence = min(0.95, 0.5 + score * 0.15)

    return best_role, best_confidence


@router.post("/identify", response_model=SectionIdentifyResponse)
async def identify_sections(request: SectionIdentifyRequest):
    """
    Step 2.0: Identify sections and their roles
    步骤 2.0：识别章节及其角色

    Automatically detects:
    - Section boundaries
    - Section roles (introduction, methodology, results, etc.)
    - Section statistics
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 2:
            return SectionIdentifyResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for section identification."],
                recommendations_zh=["文档过短，无法进行章节识别。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                sections=[],
                section_boundaries=[0, len(paragraphs)],
                total_sections=1,
                total_paragraphs=len(paragraphs)
            )

        # Identify sections
        sections = []
        current_section = None
        section_boundaries = [0]

        for i, para in enumerate(paragraphs):
            role, confidence = _detect_section_role(para)
            word_count = len(para.split())

            # Check if this starts a new section
            if current_section is None:
                current_section = {
                    "index": 0,
                    "role": role,
                    "start_paragraph": i,
                    "end_paragraph": i,
                    "word_count": word_count,
                    "confidence": confidence
                }
            elif role != current_section["role"] and confidence > 0.6:
                # End current section and start new one
                sections.append(SectionInfo(
                    index=current_section["index"],
                    role=current_section["role"],
                    start_paragraph=current_section["start_paragraph"],
                    end_paragraph=current_section["end_paragraph"],
                    word_count=current_section["word_count"],
                    confidence=current_section["confidence"]
                ))
                section_boundaries.append(i)

                current_section = {
                    "index": len(sections),
                    "role": role,
                    "start_paragraph": i,
                    "end_paragraph": i,
                    "word_count": word_count,
                    "confidence": confidence
                }
            else:
                # Continue current section
                current_section["end_paragraph"] = i
                current_section["word_count"] += word_count

        # Add last section
        if current_section:
            sections.append(SectionInfo(
                index=current_section["index"],
                role=current_section["role"],
                start_paragraph=current_section["start_paragraph"],
                end_paragraph=current_section["end_paragraph"],
                word_count=current_section["word_count"],
                confidence=current_section["confidence"]
            ))
            section_boundaries.append(len(paragraphs))

        # Calculate risk score based on section count
        if len(sections) < 3:
            risk_score = 30  # Too few sections
        elif len(sections) > 8:
            risk_score = 40  # Too many sections
        else:
            risk_score = 20  # Normal

        risk_level = RiskLevel.LOW

        # Build issues
        issues = []
        if len(sections) < 3:
            issues.append({
                "type": "few_sections",
                "description": f"Only {len(sections)} sections detected. Consider adding more structure.",
                "description_zh": f"仅检测到 {len(sections)} 个章节。考虑增加更多结构。",
                "severity": "low"
            })

        recommendations = []
        recommendations_zh = []

        if not issues:
            recommendations.append(f"Identified {len(sections)} sections. Review and adjust if needed.")
            recommendations_zh.append(f"识别到 {len(sections)} 个章节。请检查并根据需要调整。")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SectionIdentifyResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms,
            sections=sections,
            section_boundaries=section_boundaries,
            total_sections=len(sections),
            total_paragraphs=len(paragraphs)
        )

    except Exception as e:
        logger.error(f"Section identification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=SectionIdentifyResponse)
async def analyze_sections(request: SectionIdentifyRequest):
    """
    Step 2.0: Analyze sections (alias for identify)
    步骤 2.0：分析章节（identify的别名）
    """
    return await identify_sections(request)


@router.post("/adjust")
async def adjust_sections(request: SectionIdentifyRequest):
    """
    Adjust section boundaries (user-triggered)
    调整章节边界（用户触发）
    """
    return await identify_sections(request)
