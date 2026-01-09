"""
Step 4.2: Sentence Length Analysis (段内句长分析与优化)
Layer 2 Sentence Level

Analyze sentence length distribution within paragraphs.
分析段落内句子长度分布。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re
import statistics

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SentenceLengthDiversityResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip() and len(p.split()) >= 10]


def _split_sentences(para: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', para.strip())
    return [s.strip() for s in sentences if s.strip() and len(s.split()) >= 3]


def _calculate_burstiness(lengths: List[int]) -> float:
    """Calculate burstiness of length sequence"""
    if len(lengths) < 3:
        return 0.5

    diffs = [abs(lengths[i+1] - lengths[i]) for i in range(len(lengths) - 1)]
    if not diffs:
        return 0.5

    mean_diff = statistics.mean(diffs)
    max_len = max(lengths)

    return min(1.0, mean_diff / (max_len * 0.5))


@router.post("/analyze", response_model=SentenceLengthDiversityResponse)
async def analyze_sentence_lengths(request: SubstepBaseRequest):
    """
    Step 4.2: Analyze sentence length distribution
    步骤 4.2：分析句子长度分布

    - Per-paragraph CV calculation
    - Burstiness analysis
    - Merge/split candidate identification
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 1:
            return SentenceLengthDiversityResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for length analysis."],
                recommendations_zh=["文档过短，无法进行长度分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                sentences=[],
                cv=0,
                burstiness=0,
                target_cv=0.4
            )

        all_sentences = []
        all_lengths = []
        low_cv_paras = []
        no_short_paras = []
        no_long_paras = []

        for para_idx, para in enumerate(paragraphs):
            sentences = _split_sentences(para)
            if len(sentences) < 2:
                continue

            lengths = [len(s.split()) for s in sentences]
            all_lengths.extend(lengths)

            # Calculate para-level CV
            mean_len = statistics.mean(lengths)
            stdev_len = statistics.stdev(lengths) if len(lengths) > 1 else 0
            cv = stdev_len / mean_len if mean_len > 0 else 0

            burstiness = _calculate_burstiness(lengths)

            has_short = any(l <= 10 for l in lengths)
            has_long = any(l >= 30 for l in lengths)

            if cv < 0.25:
                low_cv_paras.append(para_idx)
            if not has_short:
                no_short_paras.append(para_idx)
            if not has_long:
                no_long_paras.append(para_idx)

            for sent_idx, sent in enumerate(sentences):
                all_sentences.append({
                    "paragraph_index": para_idx,
                    "sentence_index": sent_idx,
                    "text": sent[:80] + "..." if len(sent) > 80 else sent,
                    "word_count": lengths[sent_idx],
                    "cv": round(cv, 3),
                    "burstiness": round(burstiness, 3),
                    "is_short": lengths[sent_idx] <= 10,
                    "is_long": lengths[sent_idx] >= 30,
                    "can_merge": lengths[sent_idx] <= 12 and sent_idx < len(sentences) - 1,
                    "can_split": lengths[sent_idx] >= 35
                })

        # Calculate overall CV
        if len(all_lengths) > 1:
            overall_mean = statistics.mean(all_lengths)
            overall_stdev = statistics.stdev(all_lengths)
            overall_cv = overall_stdev / overall_mean if overall_mean > 0 else 0
        else:
            overall_cv = 0

        overall_burstiness = _calculate_burstiness(all_lengths) if len(all_lengths) >= 3 else 0.5

        # Calculate risk score
        risk_score = 0

        if overall_cv < 0.25:
            risk_score += 40
        elif overall_cv < 0.30:
            risk_score += 25

        if overall_burstiness < 0.3:
            risk_score += 25
        elif overall_burstiness < 0.4:
            risk_score += 15

        if len(low_cv_paras) >= 2:
            risk_score += 15

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []

        if overall_cv < 0.30:
            issues.append({
                "type": "low_cv",
                "description": f"Sentence lengths too uniform (CV={overall_cv:.2f})",
                "description_zh": f"句子长度过于均匀（CV={overall_cv:.2f}）",
                "severity": "high" if overall_cv < 0.25 else "medium"
            })

        if overall_burstiness < 0.35:
            issues.append({
                "type": "low_burstiness",
                "description": f"Low length variation rhythm (Burstiness={overall_burstiness:.2f})",
                "description_zh": f"长度变化节奏低（突发性={overall_burstiness:.2f}）",
                "severity": "medium"
            })

        if no_short_paras and len(no_short_paras) > len(paragraphs) * 0.5:
            issues.append({
                "type": "no_short_sentences",
                "description": f"{len(no_short_paras)} paragraphs lack short emphatic sentences",
                "description_zh": f"{len(no_short_paras)} 个段落缺少短强调句",
                "severity": "medium"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if overall_cv < 0.35:
            recommendations.append("Add variety by mixing short (8-12 words) and long (30+ words) sentences.")
            recommendations_zh.append("通过混合短句（8-12词）和长句（30词以上）增加变化。")

        if no_short_paras:
            recommendations.append("Add short emphatic sentences to create rhythm and emphasis.")
            recommendations_zh.append("添加短强调句以创造节奏和强调效果。")

        if not issues:
            recommendations.append("Sentence length distribution appears natural.")
            recommendations_zh.append("句子长度分布看起来自然。")

        return SentenceLengthDiversityResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            sentences=all_sentences,
            cv=round(overall_cv, 3),
            burstiness=round(overall_burstiness, 3),
            target_cv=0.4
        )

    except Exception as e:
        logger.error(f"Length analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_length_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for length adjustment"""
    return await analyze_sentence_lengths(request)
