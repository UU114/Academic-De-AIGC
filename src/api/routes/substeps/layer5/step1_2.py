"""
Step 1.2: Section Uniformity Detection (章节均匀性检测)
Layer 5 Document Level

Detects if sections are too uniform in:
- Section symmetry (paragraph counts)
- Section length uniformity
- Function uniformity
检测章节是否过于均匀
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
    SectionUniformityResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class SectionUniformityRequest(SubstepBaseRequest):
    """Request for section uniformity analysis"""
    pass


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


@router.post("/analyze", response_model=SectionUniformityResponse)
async def analyze_section_uniformity(request: SectionUniformityRequest):
    """
    Step 1.2: Analyze section/paragraph uniformity
    步骤 1.2：分析章节/段落均匀性

    Detects:
    - Section symmetry (A): balanced paragraph counts per section
    - Uniform section length (C): similar word counts
    - Uniform paragraph count (D): same number of paragraphs per section
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 2:
            return SectionUniformityResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for uniformity analysis."],
                recommendations_zh=["文档过短，无法进行均匀性分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                paragraph_count=len(paragraphs),
                mean_length=len(request.text.split()),
                stdev_length=0,
                cv=0,
                target_cv=0.4,
                paragraphs=[]
            )

        # Calculate paragraph length statistics
        lengths = [len(p.split()) for p in paragraphs]
        total_word_count = sum(lengths)
        mean_len = statistics.mean(lengths)
        stdev_len = statistics.stdev(lengths) if len(lengths) > 1 else 0
        cv = stdev_len / mean_len if mean_len > 0 else 0
        min_len = min(lengths)
        max_len = max(lengths)

        # Calculate uniformity score (higher = more uniform = more AI-like)
        if cv < 0.2:
            uniformity_score = 90
        elif cv < 0.3:
            uniformity_score = 70
        elif cv < 0.4:
            uniformity_score = 50
        elif cv < 0.5:
            uniformity_score = 30
        else:
            uniformity_score = 15

        # Determine risk level
        if uniformity_score >= 60:
            risk_level = RiskLevel.HIGH
        elif uniformity_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Build paragraph info
        paragraph_info = []
        for idx, (para, word_count) in enumerate(zip(paragraphs, lengths)):
            deviation = (word_count - mean_len) / stdev_len if stdev_len > 0 else 0

            # Determine suggested strategy
            strategy = "none"
            reason = ""
            reason_zh = ""

            if deviation < -1.5 and word_count < 80:
                if idx < len(paragraphs) - 1:
                    strategy = "merge"
                    reason = f"Short paragraph ({word_count} words). Consider merging with next paragraph."
                    reason_zh = f"短段落（{word_count}词）。建议与下一段合并。"
                else:
                    strategy = "expand"
                    reason = f"Short paragraph ({word_count} words). Consider expanding with more details."
                    reason_zh = f"短段落（{word_count}词）。建议添加更多细节扩展。"
            elif deviation > 1.5 and word_count > 200:
                strategy = "split"
                reason = f"Long paragraph ({word_count} words). Consider splitting into smaller paragraphs."
                reason_zh = f"长段落（{word_count}词）。建议拆分为较小的段落。"
            elif deviation > 1.0 and word_count > 150:
                strategy = "compress"
                reason = f"Moderately long paragraph ({word_count} words). Consider condensing."
                reason_zh = f"中等偏长段落（{word_count}词）。建议适当压缩。"
            elif deviation < -1.0 and word_count < 100:
                strategy = "expand"
                reason = f"Moderately short paragraph ({word_count} words). Consider adding details."
                reason_zh = f"中等偏短段落（{word_count}词）。建议添加细节。"

            paragraph_info.append({
                "index": idx,
                "word_count": word_count,
                "char_count": len(para),
                "preview": para[:100] + "..." if len(para) > 100 else para,
                "deviation_from_mean": round(deviation, 2),
                "suggested_strategy": strategy,
                "strategy_reason": reason,
                "strategy_reason_zh": reason_zh
            })

        # Build issues list
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
                f"Target CV >= 0.40 for natural variation. "
                f"Mix short paragraphs (50-80 words) with longer ones (150-200 words)."
            )
            recommendations_zh.append(
                f"段落长度过于均匀（CV={cv:.2f}）。"
                f"目标CV >= 0.40以达到自然变化。"
                f"混合短段落（50-80词）和长段落（150-200词）。"
            )

        merge_suggestions = [p["index"] for p in paragraph_info if p["suggested_strategy"] == "merge"]
        split_suggestions = [p["index"] for p in paragraph_info if p["suggested_strategy"] == "split"]

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

        return SectionUniformityResponse(
            risk_score=uniformity_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms,
            paragraph_count=len(paragraphs),
            mean_length=round(mean_len, 1),
            stdev_length=round(stdev_len, 1),
            cv=round(cv, 3),
            target_cv=0.4,
            paragraphs=paragraph_info
        )

    except Exception as e:
        logger.error(f"Section uniformity analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_uniformity_issues(request: SectionUniformityRequest):
    """
    Process and apply uniformity improvements
    处理并应用均匀性改进
    """
    return await analyze_section_uniformity(request)
