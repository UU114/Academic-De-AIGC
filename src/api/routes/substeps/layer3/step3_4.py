"""
Step 3.4: Sentence Length Distribution (段内句长分布分析)
Layer 3 Paragraph Level

Analyze sentence length variation within paragraphs.
分析段落内句子长度的变化模式。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re
import statistics

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SentenceLengthDistributionResponse,
    ParagraphSentenceLengthInfo,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip() and len(p.split()) >= 10]


def _split_sentences(para: str) -> List[str]:
    """Split paragraph into sentences"""
    sentences = re.split(r'(?<=[.!?])\s+', para.strip())
    return [s.strip() for s in sentences if s.strip() and len(s.split()) >= 3]


def _calculate_burstiness(lengths: List[int]) -> float:
    """
    Calculate burstiness (variation in consecutive differences)
    Higher burstiness = more human-like variation
    """
    if len(lengths) < 3:
        return 0.5

    # Calculate consecutive differences
    diffs = [abs(lengths[i+1] - lengths[i]) for i in range(len(lengths) - 1)]

    if not diffs:
        return 0.5

    mean_diff = statistics.mean(diffs)
    max_len = max(lengths)

    # Normalize burstiness
    burstiness = min(1.0, mean_diff / (max_len * 0.5))

    return round(burstiness, 3)


def _calculate_rhythm_score(lengths: List[int]) -> float:
    """
    Calculate rhythm score based on length variation patterns
    Good rhythm = mix of short and long sentences
    """
    if len(lengths) < 3:
        return 0.5

    has_short = any(l <= 10 for l in lengths)
    has_medium = any(10 < l <= 25 for l in lengths)
    has_long = any(l > 25 for l in lengths)

    score = 0
    if has_short:
        score += 0.3
    if has_medium:
        score += 0.3
    if has_long:
        score += 0.2

    # Bonus for variation
    if len(set(lengths)) >= len(lengths) * 0.7:
        score += 0.2

    return min(1.0, score)


@router.post("/analyze", response_model=SentenceLengthDistributionResponse)
async def analyze_sentence_length_distribution(request: SubstepBaseRequest):
    """
    Step 3.4: Analyze sentence length distribution
    步骤 3.4：分析句子长度分布

    - Calculates within-paragraph length CV
    - Analyzes burstiness (length variation pattern)
    - Identifies monotonous length patterns
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 1:
            return SentenceLengthDistributionResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for length analysis."],
                recommendations_zh=["文档过短，无法进行长度分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                paragraph_lengths=[],
                low_burstiness_paragraphs=[],
                overall_cv=0
            )

        paragraph_lengths = []
        low_burstiness_paragraphs = []
        all_lengths = []

        for i, para in enumerate(paragraphs):
            sentences = _split_sentences(para)
            sentence_count = len(sentences)

            if sentence_count < 2:
                continue

            lengths = [len(s.split()) for s in sentences]
            all_lengths.extend(lengths)

            mean_length = statistics.mean(lengths)
            std_length = statistics.stdev(lengths) if len(lengths) > 1 else 0
            cv = std_length / mean_length if mean_length > 0 else 0

            burstiness = _calculate_burstiness(lengths)
            rhythm_score = _calculate_rhythm_score(lengths)

            has_short = any(l <= 10 for l in lengths)
            has_long = any(l > 25 for l in lengths)

            if burstiness < 0.3 or cv < 0.25:
                low_burstiness_paragraphs.append(i)

            paragraph_lengths.append(ParagraphSentenceLengthInfo(
                paragraph_index=i,
                sentence_count=sentence_count,
                sentence_lengths=lengths,
                mean_length=round(mean_length, 1),
                std_length=round(std_length, 1),
                cv=round(cv, 3),
                burstiness=burstiness,
                has_short_sentence=has_short,
                has_long_sentence=has_long,
                rhythm_score=rhythm_score
            ))

        # Calculate overall CV
        if len(all_lengths) > 1:
            overall_mean = statistics.mean(all_lengths)
            overall_stdev = statistics.stdev(all_lengths)
            overall_cv = overall_stdev / overall_mean if overall_mean > 0 else 0
        else:
            overall_cv = 0

        # Calculate risk score
        low_cv_count = sum(1 for pl in paragraph_lengths if pl.cv < 0.25)
        low_burst_count = len(low_burstiness_paragraphs)
        total_paras = len(paragraph_lengths)

        if total_paras == 0:
            risk_score = 0
        else:
            risk_ratio = (low_cv_count + low_burst_count) / (total_paras * 2)
            risk_score = int(risk_ratio * 80 + 10)

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []

        if low_cv_count >= 2:
            issues.append({
                "type": "uniform_length",
                "description": f"{low_cv_count} paragraphs have too uniform sentence lengths (CV < 0.25)",
                "description_zh": f"{low_cv_count} 个段落句子长度过于均匀（CV < 0.25）",
                "severity": "high" if low_cv_count >= 3 else "medium"
            })

        if low_burst_count >= 2:
            issues.append({
                "type": "low_burstiness",
                "description": f"{low_burst_count} paragraphs have low burstiness (monotonous rhythm)",
                "description_zh": f"{low_burst_count} 个段落突发性低（节奏单调）",
                "severity": "medium"
            })

        no_short = sum(1 for pl in paragraph_lengths if not pl.has_short_sentence)
        if no_short >= total_paras * 0.7 and total_paras >= 3:
            issues.append({
                "type": "no_short_sentences",
                "description": "Most paragraphs lack short emphatic sentences",
                "description_zh": "大多数段落缺少短强调句",
                "severity": "medium"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if low_cv_count > 0:
            recommendations.append("Add variety to sentence lengths. Mix short (8-12 words) with long (25+ words) sentences.")
            recommendations_zh.append("增加句子长度的变化。混合使用短句（8-12词）和长句（25词以上）。")

        if low_burst_count > 0:
            recommendations.append("Create rhythm by alternating between short punchy sentences and longer complex ones.")
            recommendations_zh.append("通过交替使用短促有力的句子和较长复杂的句子来创造节奏。")

        if not issues:
            recommendations.append("Sentence length distribution appears natural.")
            recommendations_zh.append("句子长度分布看起来自然。")

        return SentenceLengthDistributionResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            paragraph_lengths=paragraph_lengths,
            low_burstiness_paragraphs=low_burstiness_paragraphs,
            overall_cv=round(overall_cv, 3)
        )

    except Exception as e:
        logger.error(f"Sentence length analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_length_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for length variation"""
    return await analyze_sentence_length_distribution(request)
