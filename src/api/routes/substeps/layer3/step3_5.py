"""
Step 3.5: Paragraph Transition Analysis (段落间过渡检测)
Layer 3 Paragraph Level

Analyze transition quality between adjacent paragraphs.
分析相邻段落之间的过渡质量。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ParagraphTransitionResponse,
    TransitionInfo,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Explicit paragraph connectors (AI-like when overused)
EXPLICIT_CONNECTORS = {
    "strong": ["furthermore", "moreover", "additionally", "in addition", "consequently"],
    "moderate": ["however", "meanwhile", "subsequently", "nevertheless", "therefore"],
    "weak": ["also", "then", "next", "now", "thus"]
}

# Formulaic opening patterns
FORMULAIC_PATTERNS = [
    r'^furthermore[,\s]',
    r'^moreover[,\s]',
    r'^additionally[,\s]',
    r'^in addition[,\s]',
    r'^as (?:mentioned|discussed|noted)',
    r'^building on',
    r'^given (?:the|this)',
    r'^having (?:established|demonstrated)'
]


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip() and len(p.split()) >= 10]


def _get_first_sentence(para: str) -> str:
    """Get first sentence of a paragraph"""
    sentences = re.split(r'(?<=[.!?])\s+', para.strip())
    return sentences[0] if sentences else para[:100]


def _get_last_sentence(para: str) -> str:
    """Get last sentence of a paragraph"""
    sentences = re.split(r'(?<=[.!?])\s+', para.strip())
    return sentences[-1] if sentences else para[-100:]


def _detect_explicit_connector(sentence: str) -> Optional[str]:
    """Detect if sentence starts with explicit connector"""
    sentence_lower = sentence.lower().strip()

    for strength, connectors in EXPLICIT_CONNECTORS.items():
        for conn in connectors:
            if sentence_lower.startswith(conn):
                return conn

    return None


def _check_formulaic_opening(sentence: str) -> bool:
    """Check if sentence uses formulaic opening"""
    sentence_lower = sentence.lower().strip()

    for pattern in FORMULAIC_PATTERNS:
        if re.match(pattern, sentence_lower):
            return True

    return False


def _calculate_semantic_echo(prev_last: str, curr_first: str) -> float:
    """
    Calculate semantic echo score between paragraphs
    Higher = better natural connection through shared concepts
    """
    # Extract content words (simple approach)
    def extract_words(text: str) -> set:
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        stop_words = {"this", "that", "with", "from", "have", "been", "were", "will", "would"}
        return set(words) - stop_words

    prev_words = extract_words(prev_last)
    curr_words = extract_words(curr_first)

    if not prev_words:
        return 0.0

    overlap = len(prev_words & curr_words)
    echo_score = min(1.0, overlap / min(len(prev_words), 3))

    return round(echo_score, 2)


def _assess_transition_quality(has_explicit: bool, is_formulaic: bool, echo_score: float) -> str:
    """Assess overall transition quality"""
    if is_formulaic:
        return "formulaic"  # AI-like
    elif has_explicit and echo_score < 0.3:
        return "abrupt"  # Forced connection
    elif echo_score >= 0.4 and not has_explicit:
        return "smooth"  # Natural human-like
    else:
        return "acceptable"


@router.post("/analyze", response_model=ParagraphTransitionResponse)
async def analyze_paragraph_transitions(request: SubstepBaseRequest):
    """
    Step 3.5: Analyze paragraph transitions
    步骤 3.5：分析段落过渡

    - Detects explicit connectors
    - Calculates semantic echo between paragraphs
    - Identifies formulaic transitions
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 2:
            return ParagraphTransitionResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for transition analysis."],
                recommendations_zh=["文档过短，无法进行过渡分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                transitions=[],
                explicit_connector_count=0,
                explicit_ratio=0,
                avg_semantic_echo=0,
                suggestions=[]
            )

        transitions = []
        explicit_count = 0
        total_echo = 0
        formulaic_count = 0

        for i in range(len(paragraphs) - 1):
            prev_para = paragraphs[i]
            curr_para = paragraphs[i + 1]

            prev_last = _get_last_sentence(prev_para)
            curr_first = _get_first_sentence(curr_para)

            # Check for explicit connector
            connector = _detect_explicit_connector(curr_first)
            has_explicit = connector is not None

            # Check for formulaic opening
            is_formulaic = _check_formulaic_opening(curr_first)

            # Calculate semantic echo
            echo_score = _calculate_semantic_echo(prev_last, curr_first)

            # Assess quality
            quality = _assess_transition_quality(has_explicit, is_formulaic, echo_score)

            if has_explicit:
                explicit_count += 1

            if is_formulaic:
                formulaic_count += 1

            total_echo += echo_score

            transitions.append(TransitionInfo(
                from_paragraph=i,
                to_paragraph=i + 1,
                has_explicit_connector=has_explicit,
                connector_word=connector,
                semantic_echo_score=echo_score,
                transition_quality=quality
            ))

        # Calculate metrics
        total_transitions = len(transitions)
        explicit_ratio = explicit_count / total_transitions if total_transitions > 0 else 0
        avg_echo = total_echo / total_transitions if total_transitions > 0 else 0

        # Calculate risk score
        risk_score = 0

        if explicit_ratio > 0.5:
            risk_score += 35
        elif explicit_ratio > 0.3:
            risk_score += 20

        if formulaic_count >= 2:
            risk_score += 25
        elif formulaic_count >= 1:
            risk_score += 15

        if avg_echo < 0.3:
            risk_score += 20
        elif avg_echo < 0.4:
            risk_score += 10

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []

        if explicit_ratio > 0.4:
            issues.append({
                "type": "excessive_connectors",
                "description": f"Too many explicit connectors ({explicit_ratio:.0%} of transitions)",
                "description_zh": f"显性连接词过多（{explicit_ratio:.0%}的过渡点）",
                "severity": "high" if explicit_ratio > 0.5 else "medium"
            })

        if formulaic_count >= 2:
            issues.append({
                "type": "formulaic_transitions",
                "description": f"{formulaic_count} transitions use formulaic patterns",
                "description_zh": f"{formulaic_count} 个过渡使用公式化模式",
                "severity": "high"
            })

        if avg_echo < 0.3:
            issues.append({
                "type": "low_semantic_echo",
                "description": f"Low semantic echo between paragraphs ({avg_echo:.0%})",
                "description_zh": f"段落间语义回声低（{avg_echo:.0%}）",
                "severity": "medium"
            })

        # Build suggestions
        suggestions = []
        for t in transitions:
            if t.transition_quality in ["formulaic", "abrupt"]:
                suggestions.append({
                    "from": t.from_paragraph,
                    "to": t.to_paragraph,
                    "issue": t.transition_quality,
                    "connector": t.connector_word,
                    "suggestion": "Replace with semantic echo of key concepts from previous paragraph",
                    "suggestion_zh": "用前一段关键概念的语义回声替换"
                })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if explicit_count > 0:
            recommendations.append("Replace explicit connectors with semantic echoes of key terms from previous paragraphs.")
            recommendations_zh.append("用前一段关键词的语义回声替换显性连接词。")

        if avg_echo < 0.4:
            recommendations.append("Improve paragraph connections by referencing concepts from the previous paragraph.")
            recommendations_zh.append("通过引用前一段的概念来改善段落连接。")

        if not issues:
            recommendations.append("Paragraph transitions appear natural.")
            recommendations_zh.append("段落过渡看起来自然。")

        return ParagraphTransitionResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            transitions=transitions,
            explicit_connector_count=explicit_count,
            explicit_ratio=round(explicit_ratio, 3),
            avg_semantic_echo=round(avg_echo, 3),
            suggestions=suggestions
        )

    except Exception as e:
        logger.error(f"Transition analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest")
async def get_transition_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for transition improvements"""
    return await analyze_paragraph_transitions(request)


@router.post("/apply")
async def apply_transition_changes(request: SubstepBaseRequest):
    """Apply transition modifications"""
    return await analyze_paragraph_transitions(request)
