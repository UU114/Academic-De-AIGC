"""
Step 1.4: Paragraph Length Uniformity (段落长度均匀性检测)
Layer 5 Document Level

Detects if paragraph lengths are too uniform (AI-like)
检测段落长度是否过于均匀
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import time
import re
import statistics

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ParagraphLengthRequest(SubstepBaseRequest):
    """Request for paragraph length analysis"""
    pass


class ParagraphLengthInfo(BaseModel):
    """Paragraph length information"""
    index: int
    word_count: int
    char_count: int
    sentence_count: int
    preview: str
    deviation_from_mean: float
    suggested_strategy: str
    strategy_reason: str
    strategy_reason_zh: str


class ParagraphLengthResponse(BaseModel):
    """Response for paragraph length analysis"""
    risk_score: int = Field(0)
    risk_level: RiskLevel = Field(RiskLevel.LOW)
    paragraph_count: int = Field(0)
    total_word_count: int = Field(0)
    mean_length: float = Field(0)
    stdev_length: float = Field(0)
    cv: float = Field(0)
    min_length: int = Field(0)
    max_length: int = Field(0)
    target_cv: float = Field(0.4)
    paragraphs: List[ParagraphLengthInfo] = Field(default_factory=list)
    merge_suggestions: List[int] = Field(default_factory=list)
    split_suggestions: List[int] = Field(default_factory=list)
    expand_suggestions: List[int] = Field(default_factory=list)
    compress_suggestions: List[int] = Field(default_factory=list)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    recommendations_zh: List[str] = Field(default_factory=list)
    processing_time_ms: int = Field(0)


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _count_sentences(text: str) -> int:
    """Count sentences in text"""
    endings = re.findall(r'[.!?]+', text)
    return max(1, len(endings))


@router.post("/analyze", response_model=ParagraphLengthResponse)
async def analyze_paragraph_length(request: ParagraphLengthRequest):
    """
    Step 1.4: Analyze paragraph length uniformity
    步骤 1.4：分析段落长度均匀性

    CV (Coefficient of Variation) < 0.3 indicates too uniform (AI-like)
    Target CV >= 0.4 for human-like writing
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 2:
            return ParagraphLengthResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                paragraph_count=len(paragraphs),
                total_word_count=len(request.text.split()),
                mean_length=len(request.text.split()),
                stdev_length=0,
                cv=0,
                min_length=len(request.text.split()),
                max_length=len(request.text.split()),
                target_cv=0.4,
                recommendations=["Document too short for paragraph length analysis."],
                recommendations_zh=["文档过短，无法进行段落长度分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Calculate statistics
        lengths = [len(p.split()) for p in paragraphs]
        total_word_count = sum(lengths)
        mean_len = statistics.mean(lengths)
        stdev_len = statistics.stdev(lengths) if len(lengths) > 1 else 0
        cv = stdev_len / mean_len if mean_len > 0 else 0
        min_len = min(lengths)
        max_len = max(lengths)

        # Calculate risk score
        if cv < 0.2:
            score = 90
        elif cv < 0.3:
            score = 70
        elif cv < 0.4:
            score = 50
        elif cv < 0.5:
            score = 30
        else:
            score = 15

        # Determine risk level
        if score >= 60:
            risk_level = RiskLevel.HIGH
        elif score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Build paragraph info and suggestions
        paragraph_infos = []
        merge_suggestions = []
        split_suggestions = []
        expand_suggestions = []
        compress_suggestions = []

        for idx, (para, word_count) in enumerate(zip(paragraphs, lengths)):
            deviation = (word_count - mean_len) / stdev_len if stdev_len > 0 else 0

            strategy = "none"
            reason = ""
            reason_zh = ""

            if deviation < -1.5 and word_count < 80:
                if idx < len(paragraphs) - 1:
                    strategy = "merge"
                    reason = f"Short paragraph ({word_count} words). Consider merging with next paragraph."
                    reason_zh = f"短段落（{word_count}词）。建议与下一段合并。"
                    merge_suggestions.append(idx)
                else:
                    strategy = "expand"
                    reason = f"Short paragraph ({word_count} words). Consider expanding with more details."
                    reason_zh = f"短段落（{word_count}词）。建议添加更多细节扩展。"
                    expand_suggestions.append(idx)
            elif deviation > 1.5 and word_count > 200:
                strategy = "split"
                reason = f"Long paragraph ({word_count} words). Consider splitting into 2-3 smaller paragraphs."
                reason_zh = f"长段落（{word_count}词）。建议拆分为2-3个较小的段落。"
                split_suggestions.append(idx)
            elif deviation > 1.0 and word_count > 150:
                strategy = "compress"
                reason = f"Moderately long paragraph ({word_count} words). Consider condensing."
                reason_zh = f"中等偏长段落（{word_count}词）。建议适当压缩。"
                compress_suggestions.append(idx)
            elif deviation < -1.0 and word_count < 100:
                strategy = "expand"
                reason = f"Moderately short paragraph ({word_count} words). Consider adding details."
                reason_zh = f"中等偏短段落（{word_count}词）。建议添加细节。"
                expand_suggestions.append(idx)

            paragraph_infos.append(ParagraphLengthInfo(
                index=idx,
                word_count=word_count,
                char_count=len(para),
                sentence_count=_count_sentences(para),
                preview=para[:100] + "..." if len(para) > 100 else para,
                deviation_from_mean=round(deviation, 2),
                suggested_strategy=strategy,
                strategy_reason=reason,
                strategy_reason_zh=reason_zh
            ))

        # Build issues
        issues = []
        if cv < 0.3:
            issues.append({
                "type": "uniform_length",
                "description": f"Paragraph lengths too uniform (CV={cv:.2f}). Target CV >= 0.40.",
                "description_zh": f"段落长度过于均匀（CV={cv:.2f}）。目标CV >= 0.40。",
                "severity": "high" if cv < 0.2 else "medium",
                "position": "document"
            })

        # Generate recommendations
        recommendations = []
        recommendations_zh = []

        if cv < 0.3:
            recommendations.append(
                f"Paragraph lengths are too uniform (CV={cv:.2f}). "
                f"Target CV >= 0.40. Mix short paragraphs (50-80 words) with longer ones (150-200 words)."
            )
            recommendations_zh.append(
                f"段落长度过于均匀（CV={cv:.2f}）。"
                f"目标CV >= 0.40。混合短段落（50-80词）和长段落（150-200词）。"
            )

        if merge_suggestions:
            recommendations.append(
                f"Consider merging paragraphs {', '.join(map(str, [i+1 for i in merge_suggestions]))} with adjacent paragraphs."
            )
            recommendations_zh.append(
                f"建议将第 {', '.join(map(str, [i+1 for i in merge_suggestions]))} 段与相邻段落合并。"
            )

        if split_suggestions:
            recommendations.append(
                f"Consider splitting paragraphs {', '.join(map(str, [i+1 for i in split_suggestions]))} into smaller sections."
            )
            recommendations_zh.append(
                f"建议将第 {', '.join(map(str, [i+1 for i in split_suggestions]))} 段拆分为较小的部分。"
            )

        if not issues:
            recommendations.append("Paragraph lengths show good variation. No major issues detected.")
            recommendations_zh.append("段落长度变化良好。未检测到重大问题。")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ParagraphLengthResponse(
            risk_score=score,
            risk_level=risk_level,
            paragraph_count=len(paragraphs),
            total_word_count=total_word_count,
            mean_length=round(mean_len, 1),
            stdev_length=round(stdev_len, 1),
            cv=round(cv, 3),
            min_length=min_len,
            max_length=max_len,
            target_cv=0.4,
            paragraphs=paragraph_infos,
            merge_suggestions=merge_suggestions,
            split_suggestions=split_suggestions,
            expand_suggestions=expand_suggestions,
            compress_suggestions=compress_suggestions,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Paragraph length analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_paragraph_length(request: ParagraphLengthRequest):
    """
    Process and apply paragraph length improvements
    处理并应用段落长度改进
    """
    return await analyze_paragraph_length(request)
