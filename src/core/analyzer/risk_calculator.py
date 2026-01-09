"""
Risk Calculator Module
风险计算模块

Provides unified risk calculation functions for the multi-layer risk assessment framework.
为多层级风险评估框架提供统一的风险计算函数。

Based on plan Section 3.3: Scoring formulas
基于计划第3.3节：评分公式

Risk Level Thresholds:
- SAFE (0-9): Clear human features
- LOW (10-29): Slight AI tendency
- MEDIUM (30-59): Needs attention
- HIGH (60-100): Strong AI features
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classification / 风险等级分类"""
    SAFE = "safe"      # 0-9
    LOW = "low"        # 10-29
    MEDIUM = "medium"  # 30-59
    HIGH = "high"      # 60-100


class IndicatorStatus(str, Enum):
    """Indicator status classification / 指标状态分类"""
    AI_LIKE = "ai_like"
    BORDERLINE = "borderline"
    HUMAN_LIKE = "human_like"


# =============================================================================
# Risk Level Determination
# 风险等级判定
# =============================================================================

def determine_risk_level(score: int) -> RiskLevel:
    """
    Determine risk level from score
    根据分数判定风险等级

    Based on plan Section 3.2:
    - SAFE: 0-9
    - LOW: 10-29
    - MEDIUM: 30-59
    - HIGH: 60-100

    Args:
        score: Risk score 0-100

    Returns:
        RiskLevel enum value
    """
    if score < 10:
        return RiskLevel.SAFE
    elif score < 30:
        return RiskLevel.LOW
    elif score < 60:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.HIGH


def determine_indicator_status(
    value: float,
    threshold_ai: float,
    threshold_human: float,
    higher_is_riskier: bool = True
) -> IndicatorStatus:
    """
    Determine indicator status based on thresholds
    根据阈值判定指标状态

    Args:
        value: Current measured value
        threshold_ai: AI threshold (high risk)
        threshold_human: Human threshold (low risk)
        higher_is_riskier: If True, higher values are more AI-like

    Returns:
        IndicatorStatus enum value
    """
    if higher_is_riskier:
        if value >= threshold_ai:
            return IndicatorStatus.AI_LIKE
        elif value <= threshold_human:
            return IndicatorStatus.HUMAN_LIKE
        else:
            return IndicatorStatus.BORDERLINE
    else:
        # For metrics where lower is more AI-like (e.g., burstiness)
        if value <= threshold_ai:
            return IndicatorStatus.AI_LIKE
        elif value >= threshold_human:
            return IndicatorStatus.HUMAN_LIKE
        else:
            return IndicatorStatus.BORDERLINE


# =============================================================================
# Indicator Risk Contribution Calculation
# 指标风险贡献计算
# =============================================================================

def calculate_indicator_contribution(
    value: float,
    threshold_ai: float,
    threshold_human: float,
    max_contribution: int,
    higher_is_riskier: bool = True
) -> int:
    """
    Calculate risk contribution from a single indicator
    计算单个指标的风险贡献

    Based on plan Section 3.3:
    - If value exceeds AI threshold: full contribution
    - If value below human threshold: 0 contribution
    - Otherwise: linear interpolation

    Args:
        value: Current measured value
        threshold_ai: AI threshold (high risk)
        threshold_human: Human threshold (low risk)
        max_contribution: Maximum contribution this indicator can make
        higher_is_riskier: If True, higher values are more AI-like

    Returns:
        Risk contribution (0 to max_contribution)
    """
    if higher_is_riskier:
        if value >= threshold_ai:
            return max_contribution
        elif value <= threshold_human:
            return 0
        else:
            # Linear interpolation
            range_size = threshold_ai - threshold_human
            if range_size <= 0:
                return max_contribution // 2
            ratio = (value - threshold_human) / range_size
            return int(max_contribution * ratio)
    else:
        # For metrics where lower is more AI-like
        if value <= threshold_ai:
            return max_contribution
        elif value >= threshold_human:
            return 0
        else:
            range_size = threshold_human - threshold_ai
            if range_size <= 0:
                return max_contribution // 2
            ratio = (threshold_human - value) / range_size
            return int(max_contribution * ratio)


# =============================================================================
# Substep Risk Calculation
# 子步骤风险计算
# =============================================================================

def calculate_substep_risk(
    indicators: Dict[str, Dict],
    human_feature_bonus: int = 0
) -> Tuple[int, Dict[str, int]]:
    """
    Calculate total risk score for a substep from its indicators
    从指标计算子步骤的总风险分数

    Based on plan Section 3.3:
    Substep Risk = Σ(indicator contribution × weight) - human_feature_bonus

    Args:
        indicators: Dictionary of indicator configs:
            {
                "indicator_id": {
                    "value": float,
                    "threshold_ai": float,
                    "threshold_human": float,
                    "weight": float (0-1),
                    "max_contribution": int,
                    "higher_is_riskier": bool (default True)
                }
            }
        human_feature_bonus: Points to subtract for detected human features

    Returns:
        Tuple of (total_risk_score, dict of individual contributions)
    """
    total_score = 0
    contributions = {}

    for indicator_id, config in indicators.items():
        value = config.get("value", 0)
        threshold_ai = config.get("threshold_ai", 80)
        threshold_human = config.get("threshold_human", 40)
        weight = config.get("weight", 1.0)
        max_contribution = config.get("max_contribution", 20)
        higher_is_riskier = config.get("higher_is_riskier", True)

        # Calculate raw contribution
        raw_contribution = calculate_indicator_contribution(
            value=value,
            threshold_ai=threshold_ai,
            threshold_human=threshold_human,
            max_contribution=max_contribution,
            higher_is_riskier=higher_is_riskier
        )

        # Apply weight
        weighted_contribution = int(raw_contribution * weight)
        contributions[indicator_id] = weighted_contribution
        total_score += weighted_contribution

    # Apply human feature bonus (subtract from score)
    total_score = max(0, total_score - human_feature_bonus)

    # Clamp to 0-100
    total_score = min(100, max(0, total_score))

    return total_score, contributions


# =============================================================================
# Layer Risk Aggregation
# 层级风险聚合
# =============================================================================

# Default substep weights for each layer
# 每层的默认子步骤权重
LAYER_SUBSTEP_WEIGHTS = {
    "document": {  # Layer 5
        "step1_1": 0.25,  # Structure Framework
        "step1_2": 0.15,  # Paragraph Length
        "step1_3": 0.25,  # Progression & Closure
        "step1_4": 0.20,  # Connectors
        "step1_5": 0.15,  # Content Substantiality
    },
    "section": {  # Layer 4
        "step2_0": 0.10,  # Section Identification
        "step2_1": 0.15,  # Section Order
        "step2_2": 0.15,  # Section Length
        "step2_3": 0.20,  # Internal Structure Similarity
        "step2_4": 0.20,  # Section Transition
        "step2_5": 0.20,  # Inter-Section Logic
    },
    "paragraph": {  # Layer 3
        "step3_0": 0.05,  # Paragraph Identification
        "step3_1": 0.15,  # Role Distribution
        "step3_2": 0.25,  # Internal Coherence
        "step3_3": 0.20,  # Anchor Density
        "step3_4": 0.20,  # Sentence Length (Burstiness)
        "step3_5": 0.15,  # Paragraph Transition
    },
    "sentence": {  # Layer 2
        "step4_0": 0.10,  # Sentence Identification
        "step4_1": 0.25,  # Pattern Analysis
        "step4_2": 0.20,  # Length Analysis
        "step4_3": 0.10,  # Merger Suggestions
        "step4_4": 0.20,  # Connector Optimization
        "step4_5": 0.15,  # Pattern Diversification
    },
    "lexical": {  # Layer 1
        "step5_1": 0.40,  # Fingerprint Detection
        "step5_2": 0.30,  # Connector Analysis
        "step5_3": 0.30,  # Word-Level Risk
    },
}


def aggregate_layer_risk(
    substep_scores: Dict[str, int],
    layer: str,
    custom_weights: Optional[Dict[str, float]] = None
) -> int:
    """
    Aggregate substep scores into layer risk score
    将子步骤分数聚合为层级风险分数

    Args:
        substep_scores: Dictionary of substep_id -> risk_score
        layer: Layer name (document, section, paragraph, sentence, lexical)
        custom_weights: Optional custom weights to override defaults

    Returns:
        Aggregated layer risk score (0-100)
    """
    weights = custom_weights or LAYER_SUBSTEP_WEIGHTS.get(layer, {})

    if not weights or not substep_scores:
        # If no weights, use simple average
        if substep_scores:
            return int(sum(substep_scores.values()) / len(substep_scores))
        return 0

    total_weight = 0
    weighted_sum = 0

    for substep_id, score in substep_scores.items():
        weight = weights.get(substep_id, 0.1)  # Default weight if not specified
        weighted_sum += score * weight
        total_weight += weight

    if total_weight > 0:
        return int(weighted_sum / total_weight)

    return 0


# =============================================================================
# Global Risk Aggregation
# 全局风险聚合
# =============================================================================

# Global layer weights from plan Section 8.1
# 来自计划第8.1节的全局层级权重
GLOBAL_LAYER_WEIGHTS = {
    "document": 0.15,   # 15%
    "section": 0.20,    # 20%
    "paragraph": 0.25,  # 25%
    "sentence": 0.25,   # 25%
    "lexical": 0.15,    # 15%
}


def aggregate_global_risk(
    layer_scores: Dict[str, int],
    custom_weights: Optional[Dict[str, float]] = None
) -> int:
    """
    Aggregate layer scores into global risk score
    将层级分数聚合为全局风险分数

    Based on plan Section 8.1:
    - Document (Layer 5): 15%
    - Section (Layer 4): 20%
    - Paragraph (Layer 3): 25%
    - Sentence (Layer 2): 25%
    - Lexical (Layer 1): 15%

    Args:
        layer_scores: Dictionary of layer -> risk_score
        custom_weights: Optional custom weights to override defaults

    Returns:
        Global aggregated risk score (0-100)
    """
    weights = custom_weights or GLOBAL_LAYER_WEIGHTS

    weighted_sum = 0
    total_weight = 0

    for layer, score in layer_scores.items():
        weight = weights.get(layer, 0.2)  # Default 20% if not specified
        weighted_sum += score * weight
        total_weight += weight

    if total_weight > 0:
        return int(weighted_sum / total_weight)

    return 0


# =============================================================================
# Convenience Functions
# 便捷函数
# =============================================================================

def create_dimension_score(
    dimension_id: str,
    name: str,
    name_zh: str,
    value: float,
    threshold_ai: float,
    threshold_human: float,
    weight: float = 1.0,
    max_contribution: int = 20,
    higher_is_riskier: bool = True,
    description: str = "",
    description_zh: str = ""
) -> Dict:
    """
    Create a dimension score dictionary ready for SubstepRiskAssessment
    创建用于SubstepRiskAssessment的维度分数字典

    Args:
        dimension_id: Unique identifier
        name: English name
        name_zh: Chinese name
        value: Current measured value
        threshold_ai: AI threshold
        threshold_human: Human threshold
        weight: Weight for this dimension (0-1)
        max_contribution: Maximum risk contribution
        higher_is_riskier: If True, higher values are more AI-like
        description: English description
        description_zh: Chinese description

    Returns:
        Dictionary compatible with DimensionScore model
    """
    # Calculate contribution
    contribution = calculate_indicator_contribution(
        value=value,
        threshold_ai=threshold_ai,
        threshold_human=threshold_human,
        max_contribution=max_contribution,
        higher_is_riskier=higher_is_riskier
    )

    # Determine status
    status = determine_indicator_status(
        value=value,
        threshold_ai=threshold_ai,
        threshold_human=threshold_human,
        higher_is_riskier=higher_is_riskier
    )

    return {
        "dimension_id": dimension_id,
        "dimension_name": name,
        "dimension_name_zh": name_zh,
        "value": value,
        "threshold_ai": threshold_ai,
        "threshold_human": threshold_human,
        "weight": weight,
        "risk_contribution": int(contribution * weight),
        "status": status.value,
        "description": description,
        "description_zh": description_zh
    }


def calculate_cv(values: List[float]) -> float:
    """
    Calculate coefficient of variation
    计算变异系数

    CV = std_dev / mean

    Args:
        values: List of numeric values

    Returns:
        Coefficient of variation (0 if mean is 0)
    """
    if not values:
        return 0.0

    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0

    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = variance ** 0.5

    return std_dev / mean


def calculate_entropy(distribution: Dict[str, int]) -> float:
    """
    Calculate Shannon entropy of a distribution
    计算分布的香农熵

    Higher entropy = more diverse (human-like)
    Lower entropy = more uniform (AI-like)

    Args:
        distribution: Dictionary of category -> count

    Returns:
        Entropy value
    """
    import math

    total = sum(distribution.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in distribution.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return entropy
