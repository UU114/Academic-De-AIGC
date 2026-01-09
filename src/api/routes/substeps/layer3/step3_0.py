"""
Step 3.0: Paragraph Identification & Segmentation (段落识别与分割)
Layer 3 Paragraph Level

Automatically identify paragraph boundaries and filter non-body content.
自动识别段落边界并过滤非正文内容。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ParagraphIdentifyResponse,
    ParagraphMeta,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Patterns to identify non-body content
NON_BODY_PATTERNS = [
    r'^abstract\s*[:：]',           # Abstract header
    r'^keywords?\s*[:：]',          # Keywords
    r'^references?\s*$',            # References section
    r'^bibliography\s*$',
    r'^acknowledgments?\s*$',
    r'^figure\s+\d+',               # Figure captions
    r'^table\s+\d+',                # Table captions
    r'^\[?\d+\]?\s+[\w\s,]+\d{4}',  # Reference entries
]


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _is_body_paragraph(para: str) -> bool:
    """Check if paragraph is body content (not header, keywords, etc.)"""
    para_lower = para.lower().strip()

    # Check against non-body patterns
    for pattern in NON_BODY_PATTERNS:
        if re.match(pattern, para_lower, re.IGNORECASE):
            return False

    # Check minimum length (too short = likely header)
    if len(para.split()) < 5:
        return False

    return True


def _count_sentences(para: str) -> int:
    """Count sentences in a paragraph"""
    # Simple sentence counting
    sentences = re.split(r'[.!?]+\s+', para)
    return len([s for s in sentences if s.strip()])


def _assign_section_index(para_index: int, total_paras: int) -> int:
    """Assign section index based on paragraph position (simple heuristic)"""
    if total_paras <= 3:
        return 0
    section_size = max(3, total_paras // 5)
    return para_index // section_size


@router.post("/identify", response_model=ParagraphIdentifyResponse)
async def identify_paragraphs(request: SubstepBaseRequest):
    """
    Step 3.0: Identify and segment paragraphs
    步骤 3.0：识别和分割段落

    - Splits text into paragraphs
    - Filters non-body content (headers, keywords, references)
    - Extracts paragraph metadata
    """
    start_time = time.time()

    try:
        raw_paragraphs = _split_paragraphs(request.text)

        # Filter and collect paragraphs
        filtered_paragraphs = []
        paragraph_metadata = []
        filtered_count = 0

        for i, para in enumerate(raw_paragraphs):
            if _is_body_paragraph(para):
                word_count = len(para.split())
                sentence_count = _count_sentences(para)
                section_index = _assign_section_index(len(filtered_paragraphs), len(raw_paragraphs))

                paragraph_metadata.append(ParagraphMeta(
                    index=len(filtered_paragraphs),
                    word_count=word_count,
                    sentence_count=sentence_count,
                    section_index=section_index,
                    preview=para[:100] + "..." if len(para) > 100 else para
                ))
                filtered_paragraphs.append(para)
            else:
                filtered_count += 1

        # Calculate risk based on paragraph distribution
        paragraph_count = len(filtered_paragraphs)

        if paragraph_count < 3:
            risk_score = 50  # Too few paragraphs
        elif paragraph_count > 20:
            risk_score = 30  # Many paragraphs (normal)
        else:
            risk_score = 20  # Normal

        risk_level = RiskLevel.LOW if risk_score < 40 else RiskLevel.MEDIUM

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if paragraph_count < 3:
            recommendations.append("Document has very few paragraphs. Consider adding more structure.")
            recommendations_zh.append("文档段落过少。考虑增加更多结构。")

        if filtered_count > 0:
            recommendations.append(f"Filtered {filtered_count} non-body elements (headers, keywords, etc.)")
            recommendations_zh.append(f"过滤了 {filtered_count} 个非正文元素（标题、关键词等）")

        if not recommendations:
            recommendations.append(f"Identified {paragraph_count} paragraphs successfully.")
            recommendations_zh.append(f"成功识别 {paragraph_count} 个段落。")

        return ParagraphIdentifyResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=[],
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            paragraphs=filtered_paragraphs,
            paragraph_count=paragraph_count,
            paragraph_metadata=paragraph_metadata,
            filtered_count=filtered_count
        )

    except Exception as e:
        logger.error(f"Paragraph identification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_paragraphs(request: SubstepBaseRequest):
    """Alias for identify endpoint"""
    return await identify_paragraphs(request)
