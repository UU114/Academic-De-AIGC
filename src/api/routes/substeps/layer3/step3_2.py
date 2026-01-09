"""
Step 3.2: Internal Coherence Analysis (段落内部连贯性检测)
Layer 3 Paragraph Level

Detect logical relationships between sentences within a paragraph.
检测段落内句子间的逻辑关系。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re
import statistics

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    CoherenceAnalysisResponse,
    ParagraphCoherenceInfo,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Connector words that indicate AI-like explicit transitions
EXPLICIT_CONNECTORS = [
    "furthermore", "moreover", "additionally", "consequently", "therefore",
    "thus", "hence", "subsequently", "accordingly", "in addition"
]

# First person pronouns
FIRST_PERSON = ["we", "our", "us", "i", "my"]


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip() and len(p.split()) >= 10]


def _split_sentences(para: str) -> List[str]:
    """Split paragraph into sentences"""
    sentences = re.split(r'(?<=[.!?])\s+', para.strip())
    return [s.strip() for s in sentences if s.strip()]


def _extract_subject(sentence: str) -> str:
    """Extract the main subject (first noun phrase) - simplified"""
    words = sentence.split()
    if len(words) < 2:
        return ""

    # Simple heuristic: take first 1-3 words as potential subject
    first_words = " ".join(words[:3]).lower()

    # Common subject patterns
    subject_patterns = [
        r'^the \w+',
        r'^this \w+',
        r'^these \w+',
        r'^we\b',
        r'^our \w+',
        r'^it\b',
        r'^\w+s?\b'  # Single word
    ]

    for pattern in subject_patterns:
        match = re.match(pattern, first_words)
        if match:
            return match.group()

    return words[0].lower() if words else ""


def _calculate_subject_diversity(sentences: List[str]) -> float:
    """Calculate subject diversity (0-1, higher = more diverse = human-like)"""
    if len(sentences) <= 1:
        return 1.0

    subjects = [_extract_subject(s) for s in sentences]
    subjects = [s for s in subjects if s]

    if not subjects:
        return 0.5

    unique_subjects = len(set(subjects))
    diversity = unique_subjects / len(subjects)

    return round(diversity, 2)


def _calculate_length_cv(sentences: List[str]) -> float:
    """Calculate sentence length coefficient of variation"""
    if len(sentences) <= 1:
        return 0

    lengths = [len(s.split()) for s in sentences]
    mean_len = statistics.mean(lengths)
    stdev_len = statistics.stdev(lengths) if len(lengths) > 1 else 0

    cv = stdev_len / mean_len if mean_len > 0 else 0
    return round(cv, 3)


def _detect_logic_structure(para: str) -> str:
    """Detect paragraph logic structure type"""
    para_lower = para.lower()

    # Check for contrastive markers
    contrastive = ["however", "but", "on the other hand", "in contrast", "conversely"]
    has_contrast = any(c in para_lower for c in contrastive)

    # Check for hierarchical markers
    hierarchical = ["specifically", "in particular", "for example", "namely"]
    has_hierarchy = any(h in para_lower for h in hierarchical)

    # Check for purely additive markers
    additive_count = sum(1 for c in EXPLICIT_CONNECTORS if c in para_lower)

    if has_contrast:
        return "contrastive"
    elif has_hierarchy:
        return "hierarchical"
    elif additive_count >= 2:
        return "linear"  # AI-like pure addition
    else:
        return "mixed"


def _calculate_connector_density(para: str) -> float:
    """Calculate explicit connector density"""
    para_lower = para.lower()
    word_count = len(para.split())

    if word_count == 0:
        return 0

    connector_count = sum(1 for c in EXPLICIT_CONNECTORS if c in para_lower)
    density = connector_count / (word_count / 100)  # per 100 words

    return round(min(1.0, density / 5), 2)  # Normalize


def _calculate_first_person_ratio(para: str) -> float:
    """Calculate first person pronoun usage ratio"""
    words = para.lower().split()
    if not words:
        return 0

    first_person_count = sum(1 for w in words if w in FIRST_PERSON)
    ratio = first_person_count / len(words)

    return round(ratio, 3)


def _calculate_coherence_score(coherence: ParagraphCoherenceInfo) -> float:
    """Calculate overall coherence score (0-100, higher = more human-like)"""
    score = 50  # Base score

    # Subject diversity (higher = better)
    if coherence.subject_diversity >= 0.6:
        score += 15
    elif coherence.subject_diversity >= 0.4:
        score += 5
    else:
        score -= 10

    # Length CV (higher = better, more natural)
    if coherence.length_variation_cv >= 0.35:
        score += 15
    elif coherence.length_variation_cv >= 0.25:
        score += 5
    else:
        score -= 10

    # Logic structure (non-linear = better)
    if coherence.logic_structure in ["hierarchical", "contrastive"]:
        score += 10
    elif coherence.logic_structure == "mixed":
        score += 5
    else:  # linear
        score -= 10

    # Connector density (lower = better)
    if coherence.connector_density <= 0.2:
        score += 10
    elif coherence.connector_density <= 0.4:
        score += 5
    else:
        score -= 10

    return max(0, min(100, score))


@router.post("/analyze", response_model=CoherenceAnalysisResponse)
async def analyze_internal_coherence(request: SubstepBaseRequest):
    """
    Step 3.2: Analyze internal coherence
    步骤 3.2：分析内部连贯性

    - Subject diversity analysis
    - Sentence length variation
    - Logic structure detection
    - Connector density analysis
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 1:
            return CoherenceAnalysisResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for coherence analysis."],
                recommendations_zh=["文档过短，无法进行连贯性分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                paragraph_coherence=[],
                overall_coherence_score=0,
                high_risk_paragraphs=[]
            )

        paragraph_coherence = []
        high_risk_paragraphs = []
        total_score = 0

        for i, para in enumerate(paragraphs):
            sentences = _split_sentences(para)

            subject_diversity = _calculate_subject_diversity(sentences)
            length_cv = _calculate_length_cv(sentences)
            logic_structure = _detect_logic_structure(para)
            connector_density = _calculate_connector_density(para)
            first_person_ratio = _calculate_first_person_ratio(para)

            coherence_info = ParagraphCoherenceInfo(
                paragraph_index=i,
                subject_diversity=subject_diversity,
                length_variation_cv=length_cv,
                logic_structure=logic_structure,
                connector_density=connector_density,
                first_person_ratio=first_person_ratio,
                overall_score=0  # Will be calculated
            )

            # Calculate overall score
            overall_score = _calculate_coherence_score(coherence_info)
            coherence_info.overall_score = overall_score
            total_score += overall_score

            if overall_score < 50:
                high_risk_paragraphs.append(i)

            paragraph_coherence.append(coherence_info)

        # Calculate overall document coherence
        overall_coherence_score = total_score / len(paragraphs) if paragraphs else 0

        # Calculate risk score (inverse of coherence)
        risk_score = int(100 - overall_coherence_score)

        if risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Build issues
        issues = []

        linear_count = sum(1 for pc in paragraph_coherence if pc.logic_structure == "linear")
        if linear_count >= len(paragraphs) * 0.5:
            issues.append({
                "type": "linear_structure",
                "description": f"{linear_count}/{len(paragraphs)} paragraphs have linear structure",
                "description_zh": f"{linear_count}/{len(paragraphs)} 个段落使用线性结构",
                "severity": "high"
            })

        low_diversity = sum(1 for pc in paragraph_coherence if pc.subject_diversity < 0.4)
        if low_diversity >= 2:
            issues.append({
                "type": "low_subject_diversity",
                "description": f"{low_diversity} paragraphs have repetitive subjects",
                "description_zh": f"{low_diversity} 个段落主语重复",
                "severity": "medium"
            })

        high_connector = sum(1 for pc in paragraph_coherence if pc.connector_density > 0.5)
        if high_connector >= 2:
            issues.append({
                "type": "high_connector_density",
                "description": f"{high_connector} paragraphs have excessive connectors",
                "description_zh": f"{high_connector} 个段落连接词过多",
                "severity": "medium"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if linear_count > 0:
            recommendations.append("Vary paragraph structures. Use contrast, examples, or hierarchical organization.")
            recommendations_zh.append("变化段落结构。使用对比、例证或层次组织。")

        if low_diversity > 0:
            recommendations.append("Vary sentence subjects to avoid repetitive patterns.")
            recommendations_zh.append("变化句子主语以避免重复模式。")

        if not issues:
            recommendations.append("Paragraph coherence appears natural.")
            recommendations_zh.append("段落连贯性看起来自然。")

        return CoherenceAnalysisResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            paragraph_coherence=paragraph_coherence,
            overall_coherence_score=round(overall_coherence_score, 1),
            high_risk_paragraphs=high_risk_paragraphs
        )

    except Exception as e:
        logger.error(f"Coherence analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest")
async def get_coherence_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for coherence improvement"""
    return await analyze_internal_coherence(request)
