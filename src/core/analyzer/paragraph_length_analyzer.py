"""
Paragraph Length Analyzer
段落长度分析器

Step 1.2: Paragraph Length Regularity Analysis
步骤 1.2：段落长度规律性分析

Based on plan Section II - Layer 5 Step 1.2:
- length_cv: 长度变异系数 (AI<0.3, Human≥0.4)
- rhythm_variance: 节奏变化度 (AI<0.3, Human≥0.4)
- extreme_ratio: 极端长短段落比例 (AI<10%, Human>20%)

Key insight from documentation:
- AI tends to produce uniformly-sized paragraphs
- Human writing shows more variation ("burstiness") in paragraph lengths
- Documents with CV < 0.3 are suspicious
"""

import statistics
from typing import List, Dict, Tuple, Optional
import logging

from src.core.analyzer.risk_calculator import (
    determine_risk_level,
    create_dimension_score,
    calculate_cv,
    RiskLevel,
)

logger = logging.getLogger(__name__)


def analyze_paragraph_lengths(paragraphs: List[str]) -> Dict:
    """
    Analyze paragraph length distribution
    分析段落长度分布

    Args:
        paragraphs: List of paragraph texts

    Returns:
        Dictionary with length analysis results
    """
    if not paragraphs:
        return {
            "lengths": [],
            "mean": 0,
            "stdev": 0,
            "cv": 0,
            "min": 0,
            "max": 0,
            "range": 0,
            "extreme_short_count": 0,
            "extreme_long_count": 0,
            "extreme_ratio": 0,
            "rhythm_variance": 0,
        }

    # Calculate word counts for each paragraph
    lengths = [len(p.split()) for p in paragraphs]

    if len(lengths) < 2:
        return {
            "lengths": lengths,
            "mean": lengths[0] if lengths else 0,
            "stdev": 0,
            "cv": 0,
            "min": lengths[0] if lengths else 0,
            "max": lengths[0] if lengths else 0,
            "range": 0,
            "extreme_short_count": 0,
            "extreme_long_count": 0,
            "extreme_ratio": 0,
            "rhythm_variance": 0,
        }

    mean_len = statistics.mean(lengths)
    stdev_len = statistics.stdev(lengths)
    cv = stdev_len / mean_len if mean_len > 0 else 0

    # Calculate rhythm variance (variation in consecutive differences)
    # 计算节奏变化度（连续差异的变化）
    differences = []
    for i in range(1, len(lengths)):
        diff = abs(lengths[i] - lengths[i - 1])
        differences.append(diff)

    rhythm_variance = calculate_cv(differences) if differences else 0

    # Count extreme paragraphs
    # 统计极端段落
    # Short: < 50 words, Long: > 200 words
    extreme_short = sum(1 for l in lengths if l < 50)
    extreme_long = sum(1 for l in lengths if l > 200)
    extreme_ratio = (extreme_short + extreme_long) / len(lengths) if lengths else 0

    return {
        "lengths": lengths,
        "mean": mean_len,
        "stdev": stdev_len,
        "cv": cv,
        "min": min(lengths),
        "max": max(lengths),
        "range": max(lengths) - min(lengths),
        "extreme_short_count": extreme_short,
        "extreme_long_count": extreme_long,
        "extreme_ratio": extreme_ratio,
        "rhythm_variance": rhythm_variance,
    }


def analyze_step1_2_risk(paragraphs: List[str]) -> Dict:
    """
    Generate SubstepRiskAssessment format for Step 1.2: Paragraph Length Analysis
    为步骤1.2生成SubstepRiskAssessment格式的段落长度分析

    Based on plan Section II - Layer 5 Step 1.2:
    - length_cv: 长度变异系数 (AI<0.3, Human≥0.4)
    - rhythm_variance: 节奏变化度 (AI<0.3, Human≥0.4)
    - extreme_ratio: 极端长短段落比例 (AI<10%, Human>20%)

    Args:
        paragraphs: List of paragraph texts

    Returns:
        Dictionary compatible with SubstepRiskAssessment model
    """
    import time
    start_time = time.time()

    # Analyze paragraph lengths
    analysis = analyze_paragraph_lengths(paragraphs)

    # Build dimension scores
    dimension_scores = {}

    # 1. Length CV (Coefficient of Variation)
    # 长度变异系数
    # Lower CV = more uniform = more AI-like
    cv = analysis["cv"]
    dimension_scores["length_cv"] = create_dimension_score(
        dimension_id="length_cv",
        name="Length Coefficient of Variation",
        name_zh="长度变异系数",
        value=cv,
        threshold_ai=0.25,      # AI: CV < 0.25
        threshold_human=0.40,   # Human: CV >= 0.40
        weight=0.50,
        max_contribution=50,
        higher_is_riskier=False,  # Lower CV = more AI-like
        description="Measures variation in paragraph lengths (lower = more uniform = more AI-like)",
        description_zh="衡量段落长度的变化程度（越低越均匀，越像AI）"
    )

    # 2. Rhythm Variance
    # 节奏变化度
    rhythm_var = analysis["rhythm_variance"]
    dimension_scores["rhythm_variance"] = create_dimension_score(
        dimension_id="rhythm_variance",
        name="Rhythm Variance",
        name_zh="节奏变化度",
        value=rhythm_var,
        threshold_ai=0.30,      # AI: rhythm < 0.30
        threshold_human=0.45,   # Human: rhythm >= 0.45
        weight=0.25,
        max_contribution=25,
        higher_is_riskier=False,  # Lower rhythm = more AI-like
        description="Measures variation in paragraph-to-paragraph length changes",
        description_zh="衡量段落间长度变化的变化程度"
    )

    # 3. Extreme Ratio
    # 极端比例
    extreme_ratio = analysis["extreme_ratio"]
    dimension_scores["extreme_ratio"] = create_dimension_score(
        dimension_id="extreme_ratio",
        name="Extreme Paragraph Ratio",
        name_zh="极端段落比例",
        value=extreme_ratio,
        threshold_ai=0.10,      # AI: extreme < 10%
        threshold_human=0.20,   # Human: extreme > 20%
        weight=0.25,
        max_contribution=25,
        higher_is_riskier=False,  # Lower extreme ratio = more AI-like
        description="Ratio of very short (<50 words) or very long (>200 words) paragraphs",
        description_zh="极短(<50词)或极长(>200词)段落的比例"
    )

    # Calculate total risk score
    total_contribution = sum(
        dim["risk_contribution"] for dim in dimension_scores.values()
    )

    # Check for human features
    human_features = []
    human_features_zh = []

    # High CV (human feature)
    if cv >= 0.40:
        human_features.append(f"Good length variation (CV={cv:.2f})")
        human_features_zh.append(f"段落长度有良好变化 (CV={cv:.2f})")
        total_contribution = max(0, total_contribution - 5)

    # Extreme paragraphs present (human feature)
    if extreme_ratio >= 0.20:
        human_features.append("Has extreme-length paragraphs (natural variation)")
        human_features_zh.append("存在极端长度段落（自然变化）")
        total_contribution = max(0, total_contribution - 5)

    # High rhythm variance (human feature)
    if rhythm_var >= 0.45:
        human_features.append("Good rhythm variation between paragraphs")
        human_features_zh.append("段落间有良好的节奏变化")
        total_contribution = max(0, total_contribution - 5)

    risk_score = min(100, max(0, total_contribution))
    risk_level = determine_risk_level(risk_score)

    # Generate issues
    issues = []

    if cv < 0.30:
        issues.append({
            "type": "uniform_length",
            "description": f"Paragraph lengths too uniform (CV={cv:.2f}, target ≥0.40)",
            "description_zh": f"段落长度过于均匀 (CV={cv:.2f}，目标≥0.40)",
            "severity": "high" if cv < 0.20 else "medium",
            "layer": "document",
            "position": "global",
            "suggestion": "Mix short (50-80 words) with long (150-200 words) paragraphs",
            "suggestion_zh": "混合短段落(50-80词)和长段落(150-200词)",
            "details": {"cv": cv, "target_cv": 0.40}
        })

    if rhythm_var < 0.30:
        issues.append({
            "type": "monotonic_rhythm",
            "description": "Paragraph length changes are too regular",
            "description_zh": "段落长度变化过于规律",
            "severity": "medium",
            "layer": "document",
            "position": "global",
            "suggestion": "Introduce sudden length changes (short→long or long→short)",
            "suggestion_zh": "引入突然的长度变化（短→长或长→短）",
            "details": {"rhythm_variance": rhythm_var}
        })

    if extreme_ratio < 0.10:
        issues.append({
            "type": "no_extremes",
            "description": "No very short or very long paragraphs (too balanced)",
            "description_zh": "没有极短或极长段落（过于平衡）",
            "severity": "low",
            "layer": "document",
            "position": "global",
            "suggestion": "Add one very short (20-50 words) or very long (200+ words) paragraph",
            "suggestion_zh": "添加一个极短(20-50词)或极长(200+词)的段落",
            "details": {"extreme_ratio": extreme_ratio}
        })

    # Generate recommendations
    recommendations = []
    recommendations_zh = []

    if risk_score >= 30:
        if cv < 0.35:
            recommendations.append("Increase paragraph length variation by merging some short paragraphs and splitting long ones")
            recommendations_zh.append("通过合并短段落和拆分长段落来增加段落长度变化")

        if extreme_ratio < 0.15:
            recommendations.append("Add some intentionally short (impact) or long (detailed analysis) paragraphs")
            recommendations_zh.append("添加一些刻意的短段落（冲击力）或长段落（详细分析）")

        if rhythm_var < 0.35:
            recommendations.append("Vary the pattern of paragraph lengths to avoid predictable rhythm")
            recommendations_zh.append("改变段落长度的模式以避免可预测的节奏")
    else:
        recommendations.append("Paragraph length distribution appears human-like")
        recommendations_zh.append("段落长度分布已较为人类化")

    processing_time_ms = int((time.time() - start_time) * 1000)

    return {
        "substep_id": "step1_2",
        "substep_name": "Paragraph Length Analysis",
        "substep_name_zh": "段落长度分析",
        "layer": "document",
        "risk_score": risk_score,
        "risk_level": risk_level.value,
        "dimension_scores": dimension_scores,
        "issues": issues,
        "recommendations": recommendations,
        "recommendations_zh": recommendations_zh,
        "processing_time_ms": processing_time_ms,
        "human_features_detected": human_features,
        "human_features_detected_zh": human_features_zh,
        # Additional analysis details
        "details": {
            "paragraph_count": len(paragraphs),
            "lengths": analysis["lengths"],
            "mean": analysis["mean"],
            "stdev": analysis["stdev"],
            "cv": analysis["cv"],
            "min_length": analysis["min"],
            "max_length": analysis["max"],
            "range": analysis["range"],
            "extreme_short_count": analysis["extreme_short_count"],
            "extreme_long_count": analysis["extreme_long_count"],
            "extreme_ratio": analysis["extreme_ratio"],
            "rhythm_variance": analysis["rhythm_variance"],
        },
    }
