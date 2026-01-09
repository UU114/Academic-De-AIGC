"""
Step 4.5: Pattern Diversification (句式多样化改写)
Layer 2 Sentence Level

Suggest and apply sentence pattern diversification.
建议并应用句式多样化改写。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SentenceRewriteResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _split_sentences(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip() and len(s.split()) >= 3]


def _get_opener(sentence: str) -> str:
    words = sentence.split()
    return words[0].lower().strip('.,;:!?"\'') if words else ""


def _detect_voice(sentence: str) -> str:
    passive_patterns = [r'\b(?:is|are|was|were|been|being)\s+\w+ed\b']
    for pattern in passive_patterns:
        if re.search(pattern, sentence.lower()):
            return "passive"
    return "active"


def _is_simple_sentence(sentence: str) -> bool:
    subordinate_markers = ["although", "though", "while", "because", "since", "if", "when", "that", "which"]
    coordinating = ["and", "but", "or", "nor", "yet", "so"]

    sent_lower = sentence.lower()
    has_subordinate = any(marker in sent_lower for marker in subordinate_markers)
    has_coordination = any(f" {conj} " in sent_lower for conj in coordinating)

    return not has_subordinate and not has_coordination


def _suggest_opener_transformation(sentence: str) -> Dict[str, Any]:
    """Suggest opener transformation"""
    opener = _get_opener(sentence)
    suggestion = None
    transform_type = None

    # AI-like openers that need transformation
    ai_openers = ["the", "this", "these", "it", "we", "our"]

    if opener in ai_openers:
        # Suggest prepositional phrase opener
        suggestion = f"In this context, {sentence[0].lower()}{sentence[1:]}"
        transform_type = "prepositional_opener"

        # Alternative: adverb opener
        alt_suggestion = f"Notably, {sentence[0].lower()}{sentence[1:]}"

    return {
        "original": sentence[:80] + "..." if len(sentence) > 80 else sentence,
        "opener": opener,
        "needs_transform": opener in ai_openers,
        "suggestion": suggestion,
        "transform_type": transform_type
    }


def _suggest_voice_transformation(sentence: str) -> Dict[str, Any]:
    """Suggest voice transformation"""
    voice = _detect_voice(sentence)

    # Only suggest transformation for active sentences
    if voice == "active" and len(sentence.split()) <= 25:
        # Simple passive transformation suggestion
        words = sentence.split()
        if len(words) >= 4:
            # Very simple heuristic: "X verbed Y" -> "Y was verbed by X"
            suggestion = f"[Passive version suggested] {sentence}"
            return {
                "original": sentence[:80] + "..." if len(sentence) > 80 else sentence,
                "current_voice": voice,
                "suggest_passive": True,
                "suggestion": suggestion
            }

    return {
        "original": sentence[:80] + "..." if len(sentence) > 80 else sentence,
        "current_voice": voice,
        "suggest_passive": False,
        "suggestion": None
    }


def _suggest_split(sentence: str) -> Dict[str, Any]:
    """Suggest splitting long sentences"""
    word_count = len(sentence.split())

    if word_count >= 35:
        # Look for natural split points
        split_points = [", and ", ", but ", ", which ", "; "]
        for sp in split_points:
            if sp in sentence:
                parts = sentence.split(sp, 1)
                if len(parts) == 2:
                    return {
                        "original": sentence[:80] + "..." if len(sentence) > 80 else sentence,
                        "word_count": word_count,
                        "suggest_split": True,
                        "split_point": sp,
                        "part1": parts[0] + ".",
                        "part2": parts[1][0].upper() + parts[1][1:] if parts[1] else ""
                    }

        return {
            "original": sentence[:80] + "..." if len(sentence) > 80 else sentence,
            "word_count": word_count,
            "suggest_split": True,
            "split_point": None,
            "part1": None,
            "part2": None
        }

    return {
        "original": sentence[:80] + "..." if len(sentence) > 80 else sentence,
        "word_count": word_count,
        "suggest_split": False
    }


@router.post("/analyze", response_model=SentenceRewriteResponse)
async def analyze_diversification(request: SubstepBaseRequest):
    """
    Step 4.5: Analyze and suggest pattern diversification
    步骤 4.5：分析并建议句式多样化

    - Opener transformations
    - Voice transformations
    - Split suggestions
    """
    start_time = time.time()

    try:
        sentences = _split_sentences(request.text)

        if len(sentences) < 3:
            return SentenceRewriteResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for diversification."],
                recommendations_zh=["文档过短，无法进行多样化分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                original_sentences=sentences,
                rewritten_sentences=[],
                changes=[]
            )

        changes = []
        opener_transforms = 0
        voice_transforms = 0
        split_suggestions = 0

        for i, sent in enumerate(sentences):
            # Check opener
            opener_result = _suggest_opener_transformation(sent)
            if opener_result["needs_transform"]:
                opener_transforms += 1
                changes.append({
                    "sentence_index": i,
                    "type": "opener_transform",
                    **opener_result
                })

            # Check voice (limit suggestions)
            if voice_transforms < 3:  # Suggest max 3 voice changes
                voice_result = _suggest_voice_transformation(sent)
                if voice_result["suggest_passive"]:
                    voice_transforms += 1
                    changes.append({
                        "sentence_index": i,
                        "type": "voice_transform",
                        **voice_result
                    })

            # Check split
            split_result = _suggest_split(sent)
            if split_result["suggest_split"]:
                split_suggestions += 1
                changes.append({
                    "sentence_index": i,
                    "type": "split_suggestion",
                    **split_result
                })

        # Calculate risk based on need for diversification
        total_changes = len(changes)
        risk_score = min(80, total_changes * 15)

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []

        if opener_transforms >= 3:
            issues.append({
                "type": "uniform_openers",
                "description": f"{opener_transforms} sentences need opener diversification",
                "description_zh": f"{opener_transforms} 个句子需要多样化开头",
                "severity": "high" if opener_transforms >= 5 else "medium"
            })

        if split_suggestions >= 2:
            issues.append({
                "type": "long_sentences",
                "description": f"{split_suggestions} sentences are too long and should be split",
                "description_zh": f"{split_suggestions} 个句子过长，应该拆分",
                "severity": "medium"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if opener_transforms > 0:
            recommendations.append("Transform sentence openers using prepositional phrases, adverbs, or subordinate clauses.")
            recommendations_zh.append("使用介词短语、副词或从句来变换句子开头。")

        if voice_transforms < len(sentences) * 0.1:
            recommendations.append("Add passive voice sentences for variety (target: 15-25%).")
            recommendations_zh.append("添加被动语态句子以增加多样性（目标：15-25%）。")

        if split_suggestions > 0:
            recommendations.append("Split long sentences at natural break points for better rhythm.")
            recommendations_zh.append("在自然断点处拆分长句以获得更好的节奏。")

        if not issues:
            recommendations.append("Sentence patterns show good diversity.")
            recommendations_zh.append("句式模式显示良好的多样性。")

        return SentenceRewriteResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            original_sentences=sentences,
            rewritten_sentences=[],  # Would be filled by LLM
            changes=changes
        )

    except Exception as e:
        logger.error(f"Diversification analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_diversification_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for diversification"""
    return await analyze_diversification(request)


@router.post("/apply")
async def apply_diversification(request: SubstepBaseRequest):
    """Apply diversification changes"""
    return await analyze_diversification(request)


@router.post("/rewrite", response_model=SentenceRewriteResponse)
async def rewrite_sentences(request: SubstepBaseRequest):
    """
    Rewrite sentences for diversification (alias for analyze endpoint)
    改写句子以实现多样化（analyze端点的别名）
    """
    return await analyze_diversification(request)
