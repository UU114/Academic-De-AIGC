"""
Step 5.2: Human Feature Analysis (人类特征词汇分析)
Layer 1 Lexical Level

Analyze human writing feature vocabulary coverage.
分析人类写作特征词汇覆盖率。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    HumanFeatureResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Human academic verbs
HUMAN_VERBS = {
    "examine": 95,
    "argue": 92,
    "suggest": 90,
    "demonstrate": 87,
    "observe": 86,
    "identify": 84,
    "investigate": 88,
    "analyze": 88,
    "validate": 82,
    "assess": 84,
    "consider": 80,
    "note": 75,
    "report": 78,
}

# Human academic adjectives
HUMAN_ADJECTIVES = {
    "significant": 98,
    "associated": 96,
    "specific": 94,
    "empirical": 92,
    "consistent": 90,
    "preliminary": 85,
    "quantitative": 90,
    "qualitative": 90,
    "limited": 88,
    "apparent": 82,
}

# Human academic phrases
HUMAN_PHRASES = {
    "results indicate": 95,
    "in contrast to": 94,
    "to our knowledge": 92,
    "data suggest": 89,
    "consistent with": 88,
    "future research": 87,
    "standard deviation": 90,
    "account for": 82,
    "it appears that": 80,
    "we found that": 85,
}


def _count_human_features(text: str) -> Dict[str, Any]:
    """Count human feature vocabulary"""
    text_lower = text.lower()
    word_count = len(text.split())

    verb_found = {}
    for verb, weight in HUMAN_VERBS.items():
        pattern = rf'\b{verb}\w*\b'  # Allow verb forms
        count = len(re.findall(pattern, text_lower))
        if count > 0:
            verb_found[verb] = {"count": count, "weight": weight}

    adj_found = {}
    for adj, weight in HUMAN_ADJECTIVES.items():
        pattern = rf'\b{adj}\w*\b'
        count = len(re.findall(pattern, text_lower))
        if count > 0:
            adj_found[adj] = {"count": count, "weight": weight}

    phrase_found = {}
    for phrase, weight in HUMAN_PHRASES.items():
        pattern = phrase.replace(" ", r"\s+")
        count = len(re.findall(pattern, text_lower))
        if count > 0:
            phrase_found[phrase] = {"count": count, "weight": weight}

    # Calculate coverage
    verb_coverage = len(verb_found) / len(HUMAN_VERBS) if HUMAN_VERBS else 0
    adj_coverage = len(adj_found) / len(HUMAN_ADJECTIVES) if HUMAN_ADJECTIVES else 0
    phrase_coverage = len(phrase_found) / len(HUMAN_PHRASES) if HUMAN_PHRASES else 0

    return {
        "verbs": verb_found,
        "adjectives": adj_found,
        "phrases": phrase_found,
        "verb_coverage": verb_coverage,
        "adjective_coverage": adj_coverage,
        "phrase_coverage": phrase_coverage,
        "total_verb_count": sum(v["count"] for v in verb_found.values()),
        "total_adjective_count": sum(v["count"] for v in adj_found.values()),
        "total_phrase_count": sum(v["count"] for v in phrase_found.values()),
    }


@router.post("/analyze", response_model=HumanFeatureResponse)
async def analyze_human_features(request: SubstepBaseRequest):
    """
    Step 5.2: Analyze human feature vocabulary
    步骤 5.2：分析人类特征词汇

    - Human academic verb coverage
    - Human adjective coverage
    - Human phrase occurrence
    """
    start_time = time.time()

    try:
        features = _count_human_features(request.text)

        # Calculate feature score (higher = more human-like)
        feature_score = (
            features["verb_coverage"] * 40 +
            features["adjective_coverage"] * 30 +
            features["phrase_coverage"] * 30
        )

        # Risk is inverse of human features (less human features = higher risk)
        risk_score = int(100 - feature_score)

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build human features list for response
        human_features = []

        for verb, info in features["verbs"].items():
            human_features.append({
                "type": "verb",
                "word": verb,
                "count": info["count"],
                "weight": info["weight"]
            })

        for adj, info in features["adjectives"].items():
            human_features.append({
                "type": "adjective",
                "word": adj,
                "count": info["count"],
                "weight": info["weight"]
            })

        for phrase, info in features["phrases"].items():
            human_features.append({
                "type": "phrase",
                "phrase": phrase,
                "count": info["count"],
                "weight": info["weight"]
            })

        # Build issues
        issues = []

        if features["verb_coverage"] < 0.15:
            issues.append({
                "type": "low_verb_coverage",
                "description": f"Human academic verb coverage is low ({features['verb_coverage']:.0%})",
                "description_zh": f"人类学术动词覆盖率低（{features['verb_coverage']:.0%}）",
                "severity": "high" if features["verb_coverage"] < 0.1 else "medium"
            })

        if features["adjective_coverage"] < 0.1:
            issues.append({
                "type": "low_adjective_coverage",
                "description": f"Human adjective coverage is low ({features['adjective_coverage']:.0%})",
                "description_zh": f"人类形容词覆盖率低（{features['adjective_coverage']:.0%}）",
                "severity": "medium"
            })

        if features["phrase_coverage"] < 0.05:
            issues.append({
                "type": "low_phrase_coverage",
                "description": f"Human academic phrase usage is low ({features['phrase_coverage']:.0%})",
                "description_zh": f"人类学术短语使用率低（{features['phrase_coverage']:.0%}）",
                "severity": "medium"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if features["verb_coverage"] < 0.2:
            missing_verbs = [v for v in HUMAN_VERBS.keys() if v not in features["verbs"]][:5]
            recommendations.append(f"Add academic verbs like: {', '.join(missing_verbs)}")
            recommendations_zh.append(f"添加学术动词如：{', '.join(missing_verbs)}")

        if features["adjective_coverage"] < 0.15:
            missing_adjs = [a for a in HUMAN_ADJECTIVES.keys() if a not in features["adjectives"]][:5]
            recommendations.append(f"Add academic adjectives like: {', '.join(missing_adjs)}")
            recommendations_zh.append(f"添加学术形容词如：{', '.join(missing_adjs)}")

        if features["phrase_coverage"] < 0.1:
            missing_phrases = [p for p in HUMAN_PHRASES.keys() if p not in features["phrases"]][:3]
            recommendations.append(f"Add academic phrases like: {', '.join(missing_phrases)}")
            recommendations_zh.append(f"添加学术短语如：{', '.join(missing_phrases)}")

        if not issues:
            recommendations.append("Human feature vocabulary coverage is good.")
            recommendations_zh.append("人类特征词汇覆盖率良好。")

        return HumanFeatureResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            human_features=human_features,
            feature_score=round(feature_score, 1)
        )

    except Exception as e:
        logger.error(f"Human feature analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_feature_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for human feature improvement"""
    return await analyze_human_features(request)
