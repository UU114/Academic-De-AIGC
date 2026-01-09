"""
Step 2.4: Section Transition Detection (章节衔接与过渡检测)
Layer 4 Section Level

Detects:
- Explicit transition words between sections
- Transition strength classification (Strong/Moderate/Weak)
- Semantic echo between sections
- Section opener pattern diversity
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SectionTransitionResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Transition word patterns by strength
TRANSITION_PATTERNS = {
    "strong": [
        "building on", "having established", "given the", "based on the previous",
        "as discussed above", "in light of", "following the", "drawing from"
    ],
    "moderate": [
        "now", "next", "turning to", "moving to", "we now", "let us now",
        "the following", "this section", "in this section"
    ],
    "weak": [
        "however", "moreover", "furthermore", "additionally", "also",
        "meanwhile", "subsequently", "consequently"
    ]
}

# Common opener patterns (AI-like)
OPENER_PATTERNS = [
    r"^this section",
    r"^in this section",
    r"^the following",
    r"^we now",
    r"^as mentioned",
    r"^building on",
    r"^having established"
]


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _extract_section_openers(paragraphs: List[str], section_size: int = 3) -> List[Dict]:
    """Extract first paragraph of each section"""
    openers = []
    for i in range(0, len(paragraphs), section_size):
        if i < len(paragraphs):
            para = paragraphs[i]
            first_sentence = para.split('.')[0] if '.' in para else para[:100]
            openers.append({
                "section_index": i // section_size,
                "opener": first_sentence,
                "paragraph_index": i
            })
    return openers


def _detect_transition_words(text: str) -> List[Dict]:
    """Detect transition words and their strength"""
    text_lower = text.lower()
    found_transitions = []

    for strength, patterns in TRANSITION_PATTERNS.items():
        for pattern in patterns:
            if pattern in text_lower:
                # Find the position
                pos = text_lower.find(pattern)
                context_start = max(0, pos - 20)
                context_end = min(len(text), pos + len(pattern) + 50)
                context = text[context_start:context_end]

                found_transitions.append({
                    "phrase": pattern,
                    "strength": strength,
                    "context": context,
                    "position": pos
                })

    return found_transitions


def _calculate_semantic_echo(opener: str, prev_content: str) -> float:
    """Calculate semantic echo score between section opener and previous content"""
    # Extract keywords from previous content (simple approach)
    prev_words = set(re.findall(r'\b[a-z]{4,}\b', prev_content.lower()))
    opener_words = set(re.findall(r'\b[a-z]{4,}\b', opener.lower()))

    # Remove common stop words
    stop_words = {"this", "that", "with", "from", "have", "been", "were", "will", "would", "could", "should"}
    prev_words -= stop_words
    opener_words -= stop_words

    if not prev_words:
        return 0.0

    # Calculate overlap
    overlap = len(prev_words & opener_words)
    return min(1.0, overlap / min(len(prev_words), 5))


def _check_opener_pattern(opener: str) -> str:
    """Check if opener matches any AI-like pattern"""
    opener_lower = opener.lower().strip()
    for pattern in OPENER_PATTERNS:
        if re.match(pattern, opener_lower):
            return pattern
    return ""


@router.post("/analyze", response_model=SectionTransitionResponse)
async def analyze_section_transitions(request: SubstepBaseRequest):
    """
    Step 2.4: Analyze section transitions and connections
    步骤 2.4：分析章节衔接与过渡

    Detects:
    - Explicit transition words (strong/moderate/weak)
    - Semantic echo between sections
    - Section opener pattern diversity
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 2:
            return SectionTransitionResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for transition analysis."],
                recommendations_zh=["文档过短，无法进行衔接分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                transition_words=[],
                strength_distribution={"strong": 0, "moderate": 0, "weak": 0},
                semantic_echo_score=0.0,
                opener_patterns=[],
                explicit_transition_ratio=0.0
            )

        # Extract section openers
        section_openers = _extract_section_openers(paragraphs)

        # Detect transitions in openers
        all_transitions = []
        semantic_echo_scores = []
        opener_pattern_matches = []

        for i, opener_info in enumerate(section_openers):
            # Check for transitions in opener
            transitions = _detect_transition_words(opener_info["opener"])
            for t in transitions:
                t["section_index"] = opener_info["section_index"]
            all_transitions.extend(transitions)

            # Calculate semantic echo with previous section
            if i > 0:
                prev_section_start = (i - 1) * 3
                prev_section_end = min(i * 3, len(paragraphs))
                prev_content = " ".join(paragraphs[prev_section_start:prev_section_end])
                echo_score = _calculate_semantic_echo(opener_info["opener"], prev_content)
                semantic_echo_scores.append(echo_score)

            # Check opener pattern
            pattern = _check_opener_pattern(opener_info["opener"])
            if pattern:
                opener_pattern_matches.append({
                    "section_index": opener_info["section_index"],
                    "pattern": pattern,
                    "opener_text": opener_info["opener"][:80]
                })

        # Calculate strength distribution
        strength_dist = {"strong": 0, "moderate": 0, "weak": 0}
        for t in all_transitions:
            strength_dist[t["strength"]] += 1

        total_transitions = len(all_transitions)
        total_sections = len(section_openers)

        # Calculate explicit transition ratio
        explicit_ratio = total_transitions / max(1, total_sections - 1) if total_sections > 1 else 0

        # Calculate average semantic echo
        avg_echo = sum(semantic_echo_scores) / len(semantic_echo_scores) if semantic_echo_scores else 0

        # Calculate opener pattern repetition
        pattern_repeat_ratio = len(opener_pattern_matches) / max(1, total_sections)

        # Calculate risk score
        risk_score = 0

        # High strong transitions = high risk
        if strength_dist["strong"] >= 2:
            risk_score += 40
        elif strength_dist["strong"] >= 1:
            risk_score += 20

        # High explicit ratio = high risk
        if explicit_ratio > 0.7:
            risk_score += 30
        elif explicit_ratio > 0.5:
            risk_score += 15

        # Low semantic echo = medium risk
        if avg_echo < 0.3:
            risk_score += 15
        elif avg_echo < 0.4:
            risk_score += 10

        # High pattern repetition = high risk
        if pattern_repeat_ratio > 0.5:
            risk_score += 15

        # Determine risk level
        if risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Build issues
        issues = []

        if strength_dist["strong"] >= 2:
            issues.append({
                "type": "strong_transitions",
                "description": f"Too many strong transition phrases ({strength_dist['strong']} found)",
                "description_zh": f"强过渡词过多（发现 {strength_dist['strong']} 个）",
                "severity": "high"
            })

        if explicit_ratio > 0.7:
            issues.append({
                "type": "explicit_transitions",
                "description": f"Explicit transition ratio too high ({explicit_ratio:.0%})",
                "description_zh": f"显性过渡比例过高（{explicit_ratio:.0%}）",
                "severity": "high" if explicit_ratio > 0.8 else "medium"
            })

        if avg_echo < 0.3:
            issues.append({
                "type": "low_semantic_echo",
                "description": f"Low semantic echo between sections ({avg_echo:.0%})",
                "description_zh": f"章节间语义回声较低（{avg_echo:.0%}）",
                "severity": "medium"
            })

        if pattern_repeat_ratio > 0.5:
            issues.append({
                "type": "repetitive_openers",
                "description": f"Section openers follow similar patterns ({pattern_repeat_ratio:.0%})",
                "description_zh": f"章节开头模式相似（{pattern_repeat_ratio:.0%}）",
                "severity": "medium"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if strength_dist["strong"] >= 1:
            recommendations.append("Replace strong transition phrases with semantic echoes of key terms.")
            recommendations_zh.append("用关键词的语义回声替换强过渡词。")

        if avg_echo < 0.4:
            recommendations.append("Improve semantic connections by echoing keywords from previous sections.")
            recommendations_zh.append("通过回应前一章节的关键词来改善语义连接。")

        if pattern_repeat_ratio > 0.3:
            recommendations.append("Vary section opening patterns for more natural flow.")
            recommendations_zh.append("变化章节开头模式以获得更自然的流程。")

        if not issues:
            recommendations.append("Section transitions appear natural.")
            recommendations_zh.append("章节衔接看起来自然。")

        return SectionTransitionResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            transition_words=all_transitions,
            strength_distribution=strength_dist,
            semantic_echo_score=round(avg_echo, 3),
            opener_patterns=opener_pattern_matches,
            explicit_transition_ratio=round(explicit_ratio, 3)
        )

    except Exception as e:
        logger.error(f"Section transition analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_transition_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for transition improvements"""
    return await analyze_section_transitions(request)


@router.post("/apply")
async def apply_transition_changes(request: SubstepBaseRequest):
    """Apply transition modifications"""
    return await analyze_section_transitions(request)
