"""
Step 4.4: Connector Optimization (句间连接词优化)
Layer 2 Sentence Level

Detect and optimize explicit sentence connectors.
检测和优化显性句子连接词。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SentenceConnectorResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Connector categories by strength
CONNECTORS = {
    "strong_ai": {
        "words": ["furthermore", "moreover", "additionally", "in addition", "consequently"],
        "replacement": "Consider removing or using implicit connection",
        "risk": "high"
    },
    "moderate_ai": {
        "words": ["however", "therefore", "thus", "hence", "nevertheless"],
        "replacement": "Use sparingly, consider implicit alternatives",
        "risk": "medium"
    },
    "acceptable": {
        "words": ["but", "and", "so", "yet", "also", "then"],
        "replacement": None,
        "risk": "low"
    },
    "good_variation": {
        "words": ["although", "while", "whereas", "despite", "unless"],
        "replacement": None,
        "risk": "low"
    }
}


def _split_sentences(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip() and len(s.split()) >= 3]


def _get_opener_word(sentence: str) -> str:
    """Get opening word"""
    words = sentence.split()
    return words[0].lower().strip('.,;:!?"\'') if words else ""


def _detect_connector_category(opener: str) -> tuple:
    """Detect which category the connector belongs to"""
    for category, config in CONNECTORS.items():
        if opener in config["words"]:
            return category, config["replacement"], config["risk"]
    return None, None, None


def _starts_with_connector(sentence: str) -> tuple:
    """Check if sentence starts with a connector"""
    opener = _get_opener_word(sentence)

    for category, config in CONNECTORS.items():
        for word in config["words"]:
            if sentence.lower().startswith(word):
                return True, word, category, config["risk"]

    return False, None, None, None


@router.post("/analyze", response_model=SentenceConnectorResponse)
async def analyze_connectors(request: SubstepBaseRequest):
    """
    Step 4.4: Analyze sentence connectors
    步骤 4.4：分析句子连接词

    - Detects explicit sentence-initial connectors
    - Classifies connector types
    - Suggests replacements
    """
    start_time = time.time()

    try:
        sentences = _split_sentences(request.text)

        if len(sentences) < 3:
            return SentenceConnectorResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for connector analysis."],
                recommendations_zh=["文档过短，无法进行连接词分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                connector_sentences=[],
                connector_types={},
                connector_density=0
            )

        connector_sentences = []
        type_counts = {"strong_ai": 0, "moderate_ai": 0, "acceptable": 0, "good_variation": 0}
        connector_list = []

        for i, sent in enumerate(sentences):
            has_conn, word, category, risk = _starts_with_connector(sent)

            if has_conn:
                type_counts[category] += 1
                connector_list.append(word)

                connector_sentences.append({
                    "sentence_index": i,
                    "sentence_preview": sent[:80] + "..." if len(sent) > 80 else sent,
                    "connector_word": word,
                    "category": category,
                    "risk_level": risk,
                    "suggestion": CONNECTORS[category]["replacement"]
                })

        total_sentences = len(sentences)
        connector_count = len(connector_sentences)
        connector_density = connector_count / total_sentences if total_sentences > 0 else 0

        # Calculate risk score
        risk_score = 0

        strong_ai_count = type_counts["strong_ai"]
        moderate_ai_count = type_counts["moderate_ai"]

        if strong_ai_count >= 3:
            risk_score += 40
        elif strong_ai_count >= 2:
            risk_score += 25
        elif strong_ai_count >= 1:
            risk_score += 15

        if moderate_ai_count >= 4:
            risk_score += 20
        elif moderate_ai_count >= 2:
            risk_score += 10

        if connector_density > 0.4:
            risk_score += 20
        elif connector_density > 0.3:
            risk_score += 10

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []

        if strong_ai_count >= 1:
            issues.append({
                "type": "strong_ai_connectors",
                "description": f"{strong_ai_count} strong AI connectors found (Furthermore, Moreover, etc.)",
                "description_zh": f"发现 {strong_ai_count} 个强AI连接词（Furthermore, Moreover等）",
                "severity": "high" if strong_ai_count >= 2 else "medium"
            })

        if connector_density > 0.35:
            issues.append({
                "type": "high_connector_density",
                "description": f"High connector density ({connector_density:.0%})",
                "description_zh": f"连接词密度高（{connector_density:.0%}）",
                "severity": "high" if connector_density > 0.4 else "medium"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if strong_ai_count >= 1:
            recommendations.append("Remove or replace strong AI connectors (Furthermore, Moreover, Additionally).")
            recommendations_zh.append("删除或替换强AI连接词（Furthermore, Moreover, Additionally）。")

        if connector_density > 0.3:
            recommendations.append("Reduce explicit connectors. Let ideas flow naturally without signposting.")
            recommendations_zh.append("减少显性连接词。让想法自然流动，无需路标式过渡。")

        if type_counts["good_variation"] < 2:
            recommendations.append("Add subordinate clause starters (Although, While, Despite) for variety.")
            recommendations_zh.append("添加从句开头（Although, While, Despite）以增加多样性。")

        if not issues:
            recommendations.append("Connector usage appears balanced.")
            recommendations_zh.append("连接词使用看起来平衡。")

        return SentenceConnectorResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            connector_sentences=connector_sentences,
            connector_types=type_counts,
            connector_density=round(connector_density, 3)
        )

    except Exception as e:
        logger.error(f"Connector analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_connector_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for connector optimization"""
    return await analyze_connectors(request)


@router.post("/apply")
async def apply_connector_changes(request: SubstepBaseRequest):
    """Apply connector modifications"""
    return await analyze_connectors(request)
