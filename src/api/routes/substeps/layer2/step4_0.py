"""
Step 4.0: Sentence Identification & Labeling (句子识别与标注)
Layer 2 Sentence Level

Receive paragraph context, split into sentences, label type and function.
接收段落上下文，分割句子，标注类型和功能。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SentenceContextResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Sentence type patterns (simplified detection)
SUBORDINATE_MARKERS = [
    "although", "though", "while", "whereas", "because", "since", "if", "unless",
    "when", "whenever", "before", "after", "until", "as", "that", "which", "who"
]

COORDINATING_CONJUNCTIONS = ["and", "but", "or", "nor", "for", "yet", "so"]


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip() and len(p.split()) >= 5]


def _split_sentences(para: str) -> List[str]:
    """Split paragraph into sentences"""
    sentences = re.split(r'(?<=[.!?])\s+', para.strip())
    return [s.strip() for s in sentences if s.strip() and len(s.split()) >= 3]


def _detect_sentence_type(sentence: str) -> tuple:
    """Detect sentence type and metadata"""
    sent_lower = sentence.lower()
    words = sent_lower.split()

    # Check for subordinate clauses
    has_subordinate = any(marker in sent_lower for marker in SUBORDINATE_MARKERS)

    # Check for coordinating conjunctions
    has_coordination = any(f" {conj} " in sent_lower for conj in COORDINATING_CONJUNCTIONS)

    # Estimate clause depth
    clause_depth = sum(1 for marker in SUBORDINATE_MARKERS if marker in sent_lower)

    # Determine type
    if has_subordinate and has_coordination:
        sent_type = "compound_complex"
    elif has_subordinate:
        sent_type = "complex"
    elif has_coordination:
        sent_type = "compound"
    else:
        sent_type = "simple"

    return sent_type, has_subordinate, clause_depth


def _detect_voice(sentence: str) -> str:
    """Detect sentence voice (active/passive)"""
    # Simple heuristic: look for passive patterns
    passive_patterns = [
        r'\b(?:is|are|was|were|been|being)\s+\w+ed\b',
        r'\b(?:is|are|was|were|been|being)\s+\w+en\b',
        r'\bby\s+(?:the|a|an)\b'
    ]

    for pattern in passive_patterns:
        if re.search(pattern, sentence.lower()):
            return "passive"

    return "active"


def _get_opener_word(sentence: str) -> str:
    """Get the opening word of a sentence"""
    words = sentence.split()
    if words:
        return words[0].lower().strip('.,;:!?"\'')
    return ""


def _detect_function_role(sentence: str, position: int, total: int) -> str:
    """Detect sentence function role based on content and position"""
    sent_lower = sentence.lower()

    # Position-based hints
    if position == 0:
        if any(w in sent_lower for w in ["this paper", "this study", "we present", "aims to"]):
            return "topic"

    if position == total - 1:
        if any(w in sent_lower for w in ["in conclusion", "therefore", "thus", "overall"]):
            return "conclusion"

    # Content-based detection
    if any(w in sent_lower for w in ["found", "showed", "demonstrated", "results"]):
        return "evidence"

    if any(w in sent_lower for w in ["suggests", "implies", "indicates", "because"]):
        return "analysis"

    if any(w in sent_lower for w in ["however", "moreover", "furthermore", "additionally"]):
        return "transition"

    return "body"


@router.post("/identify", response_model=SentenceContextResponse)
async def identify_sentences(request: SubstepBaseRequest):
    """
    Step 4.0: Identify and label sentences
    步骤 4.0：识别和标注句子

    - Splits paragraphs into sentences
    - Labels sentence type (simple/compound/complex/compound-complex)
    - Detects voice and clause depth
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)

        sentences = []
        paragraph_context = []
        sentence_index = 0
        type_counts = {"simple": 0, "compound": 0, "complex": 0, "compound_complex": 0}
        voice_counts = {"active": 0, "passive": 0}

        for para_idx, para in enumerate(paragraphs):
            para_sentences = _split_sentences(para)
            para_sentence_indices = []

            for sent_pos, sent in enumerate(para_sentences):
                sent_type, has_sub, clause_depth = _detect_sentence_type(sent)
                voice = _detect_voice(sent)
                opener = _get_opener_word(sent)
                function_role = _detect_function_role(sent, sent_pos, len(para_sentences))

                sentences.append({
                    "index": sentence_index,
                    "text": sent,
                    "paragraph_index": para_idx,
                    "word_count": len(sent.split()),
                    "sentence_type": sent_type,
                    "function_role": function_role,
                    "has_subordinate": has_sub,
                    "clause_depth": clause_depth,
                    "voice": voice,
                    "opener_word": opener
                })

                type_counts[sent_type] += 1
                voice_counts[voice] += 1
                para_sentence_indices.append(sentence_index)
                sentence_index += 1

            paragraph_context.append({
                "paragraph_index": para_idx,
                "sentence_indices": para_sentence_indices,
                "sentence_count": len(para_sentences)
            })

        # Calculate risk based on type distribution
        total_sentences = len(sentences)
        simple_ratio = type_counts["simple"] / total_sentences if total_sentences > 0 else 0

        if simple_ratio > 0.7:
            risk_score = 75
        elif simple_ratio > 0.6:
            risk_score = 55
        elif simple_ratio > 0.5:
            risk_score = 35
        else:
            risk_score = 20

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []
        if simple_ratio > 0.6:
            issues.append({
                "type": "simple_sentence_dominance",
                "description": f"Simple sentences dominate ({simple_ratio:.0%})",
                "description_zh": f"简单句占主导（{simple_ratio:.0%}）",
                "severity": "high" if simple_ratio > 0.7 else "medium"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if simple_ratio > 0.6:
            recommendations.append("Increase sentence complexity by adding subordinate clauses and combining related ideas.")
            recommendations_zh.append("通过添加从句和组合相关想法来增加句子复杂性。")

        if voice_counts["passive"] < total_sentences * 0.1:
            recommendations.append("Consider adding more passive voice sentences for variety.")
            recommendations_zh.append("考虑添加更多被动语态句子以增加多样性。")

        if not issues:
            recommendations.append("Sentence structure shows good variety.")
            recommendations_zh.append("句子结构显示良好的多样性。")

        return SentenceContextResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            sentences=sentences,
            sentence_count=total_sentences,
            paragraph_context=paragraph_context
        )

    except Exception as e:
        logger.error(f"Sentence identification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_sentences(request: SubstepBaseRequest):
    """Alias for identify endpoint"""
    return await identify_sentences(request)


@router.post("/prepare", response_model=SentenceContextResponse)
async def prepare_sentence_context(request: SubstepBaseRequest):
    """
    Prepare sentence context (alias for identify endpoint)
    准备句子上下文（identify端点的别名）
    """
    return await identify_sentences(request)
