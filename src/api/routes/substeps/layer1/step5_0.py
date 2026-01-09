"""
Step 5.0: Lexical Context Preparation (词汇环境准备)
Layer 1 Lexical Level

Prepare lexical analysis context and load vocabulary databases.
准备词汇分析上下文并加载词汇数据库。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    LexicalContextResponse,
    RiskLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip() and len(p.split()) >= 5]


def _tokenize(text: str) -> List[str]:
    """Simple tokenization"""
    return re.findall(r'\b[a-z]+\b', text.lower())


def _build_vocabulary_stats(paragraphs: List[str]) -> Dict[str, Any]:
    """Build vocabulary statistics"""
    all_words = []
    unique_words = set()
    word_freq = {}

    for para in paragraphs:
        words = _tokenize(para)
        all_words.extend(words)
        unique_words.update(words)
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

    return {
        "total_words": len(all_words),
        "unique_words": len(unique_words),
        "vocabulary_richness": len(unique_words) / len(all_words) if all_words else 0,
        "top_words": sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
    }


@router.post("/prepare", response_model=LexicalContextResponse)
async def prepare_lexical_context(request: SubstepBaseRequest):
    """
    Step 5.0: Prepare lexical analysis context
    步骤 5.0：准备词汇分析上下文

    - Receives text and locked terms
    - Builds paragraph-word mapping
    - Calculates vocabulary statistics
    """
    start_time = time.time()

    try:
        paragraphs = _split_paragraphs(request.text)
        locked_terms = request.locked_terms or []

        # Build tokens for each paragraph
        tokens = []
        for para_idx, para in enumerate(paragraphs):
            para_words = _tokenize(para)
            for word_idx, word in enumerate(para_words):
                tokens.append({
                    "word": word,
                    "paragraph_index": para_idx,
                    "position": word_idx,
                    "is_locked": word in [t.lower() for t in locked_terms]
                })

        # Build vocabulary statistics
        vocab_stats = _build_vocabulary_stats(paragraphs)

        # Calculate risk based on vocabulary richness
        if vocab_stats["vocabulary_richness"] < 0.3:
            risk_score = 60  # Low vocabulary diversity
        elif vocab_stats["vocabulary_richness"] < 0.4:
            risk_score = 40
        else:
            risk_score = 20

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if vocab_stats["vocabulary_richness"] < 0.35:
            recommendations.append("Consider diversifying vocabulary to reduce AI detection risk.")
            recommendations_zh.append("考虑多样化词汇以降低AI检测风险。")

        if len(locked_terms) > 0:
            recommendations.append(f"{len(locked_terms)} terms are locked and will be preserved during rewriting.")
            recommendations_zh.append(f"{len(locked_terms)} 个术语已锁定，将在改写过程中保留。")

        if not recommendations:
            recommendations.append("Lexical context prepared successfully.")
            recommendations_zh.append("词汇上下文准备成功。")

        return LexicalContextResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=[],
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            tokens=tokens,
            vocabulary_stats=vocab_stats
        )

    except Exception as e:
        logger.error(f"Lexical context preparation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_context(request: SubstepBaseRequest):
    """Alias for prepare endpoint"""
    return await prepare_lexical_context(request)
