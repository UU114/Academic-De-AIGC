"""
Step 4.1: Sentence Pattern Analysis (句式结构分析)
Layer 2 Sentence Level

Analyze sentence pattern diversity and detect AI-like patterns.
分析句式多样性并检测AI特征模式。

Now integrated with Syntactic Void Detector for enhanced detection.
现已集成句法空洞检测器以增强检测能力。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import time
import re
from collections import Counter

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SentencePatternResponse,
    RiskLevel,
)

# Import Syntactic Void Detector for detecting semantically empty AI patterns
# 导入句法空洞检测器用于检测语义空洞的AI模式
try:
    from src.core.analyzer.syntactic_void import (
        SyntacticVoidDetector,
        detect_syntactic_voids,
        SyntacticVoidResult,
        VoidMatch,
        VoidPatternType
    )
    VOID_DETECTOR_AVAILABLE = True
except ImportError:
    VOID_DETECTOR_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter()


# AI-like opener patterns
AI_OPENERS = ["the", "this", "these", "it", "they", "furthermore", "moreover", "additionally"]


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _split_sentences(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip() and len(s.split()) >= 3]


def _detect_sentence_type(sentence: str) -> str:
    """Detect sentence type"""
    sent_lower = sentence.lower()

    subordinate_markers = ["although", "though", "while", "because", "since", "if", "when", "that", "which", "who"]
    coordinating = ["and", "but", "or", "nor", "for", "yet", "so"]

    has_subordinate = any(marker in sent_lower for marker in subordinate_markers)
    has_coordination = any(f" {conj} " in sent_lower for conj in coordinating)

    if has_subordinate and has_coordination:
        return "compound_complex"
    elif has_subordinate:
        return "complex"
    elif has_coordination:
        return "compound"
    return "simple"


def _get_opener(sentence: str) -> str:
    """Get opening word"""
    words = sentence.split()
    return words[0].lower().strip('.,;:!?"\'') if words else ""


def _detect_voice(sentence: str) -> str:
    """Detect voice"""
    passive_patterns = [r'\b(?:is|are|was|were|been|being)\s+\w+ed\b']
    for pattern in passive_patterns:
        if re.search(pattern, sentence.lower()):
            return "passive"
    return "active"


def _is_subject_opening(sentence: str) -> bool:
    """Check if sentence starts with subject"""
    opener = _get_opener(sentence)
    subject_starters = ["the", "this", "these", "that", "those", "it", "they", "we", "he", "she", "our", "their"]
    return opener in subject_starters


def _detect_syntactic_voids(text: str) -> Dict[str, Any]:
    """
    Detect syntactic void patterns (semantically empty but grammatically correct)
    检测句法空洞模式（语法正确但语义空洞）

    These patterns are characteristic of AI-generated text.
    这些模式是AI生成文本的特征。

    Returns:
        Dict with void_score, void_density, syntactic_voids list, and has_critical_void
    """
    if not VOID_DETECTOR_AVAILABLE:
        logger.warning("Syntactic Void Detector not available, skipping void analysis")
        return {
            "void_score": 0,
            "void_density": 0.0,
            "syntactic_voids": [],
            "has_critical_void": False,
            "available": False,
            "reason": "Syntactic Void module not imported"
        }

    try:
        # Run syntactic void detection (using fast regex mode, spaCy optional)
        # 运行句法空洞检测（使用快速正则模式，spaCy可选）
        result: SyntacticVoidResult = detect_syntactic_voids(text, use_spacy=False)

        # Convert VoidMatch objects to dicts for JSON serialization
        # 将 VoidMatch 对象转换为 dict 以便 JSON 序列化
        void_list = []
        for match in result.matches:
            void_list.append({
                "pattern_type": match.pattern_type.value if hasattr(match.pattern_type, 'value') else str(match.pattern_type),
                "matched_text": match.matched_text,
                "position": match.position,
                "end_position": match.end_position,
                "severity": match.severity,
                "abstract_words": match.abstract_words,
                "suggestion": match.suggestion,
                "suggestion_zh": match.suggestion_zh
            })

        logger.info(f"Syntactic Void Analysis: score={result.void_score}, matches={len(void_list)}, critical={result.has_critical_void}")

        return {
            "void_score": result.void_score,
            "void_density": round(result.void_density, 3),
            "syntactic_voids": void_list,
            "has_critical_void": result.has_critical_void,
            "void_sentence_count": result.void_sentence_count,
            "total_sentence_count": result.sentence_count,
            "available": True
        }

    except Exception as e:
        logger.error(f"Syntactic void detection failed: {e}")
        return {
            "void_score": 0,
            "void_density": 0.0,
            "syntactic_voids": [],
            "has_critical_void": False,
            "available": True,
            "reason": str(e)
        }


@router.post("/analyze", response_model=SentencePatternResponse)
async def analyze_sentence_patterns(request: SubstepBaseRequest):
    """
    Step 4.1: Analyze sentence patterns
    步骤 4.1：分析句式模式

    - Type distribution analysis
    - Opener repetition detection
    - Voice distribution
    """
    start_time = time.time()

    try:
        sentences = _split_sentences(request.text)

        if len(sentences) < 3:
            return SentencePatternResponse(
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                recommendations=["Document too short for pattern analysis."],
                recommendations_zh=["文档过短，无法进行模式分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000),
                patterns_detected=[],
                pattern_counts={}
            )

        # Analyze patterns
        type_counts = Counter()
        opener_counts = Counter()
        voice_counts = Counter()
        subject_opening_count = 0
        patterns_detected = []

        for i, sent in enumerate(sentences):
            sent_type = _detect_sentence_type(sent)
            opener = _get_opener(sent)
            voice = _detect_voice(sent)
            is_subject = _is_subject_opening(sent)

            type_counts[sent_type] += 1
            opener_counts[opener] += 1
            voice_counts[voice] += 1
            if is_subject:
                subject_opening_count += 1

            patterns_detected.append({
                "sentence_index": i,
                "sentence_preview": sent[:60] + "..." if len(sent) > 60 else sent,
                "type": sent_type,
                "opener": opener,
                "voice": voice,
                "is_subject_opening": is_subject
            })

        total = len(sentences)

        # Calculate metrics
        simple_ratio = type_counts.get("simple", 0) / total
        subject_ratio = subject_opening_count / total
        active_ratio = voice_counts.get("active", 0) / total

        # Find repeated openers
        repeated_openers = [op for op, count in opener_counts.items() if count >= 3]
        opener_repetition_rate = sum(c for c in opener_counts.values() if c >= 2) / total

        # Calculate risk score
        risk_score = 0

        if simple_ratio > 0.7:
            risk_score += 35
        elif simple_ratio > 0.6:
            risk_score += 20

        if subject_ratio > 0.8:
            risk_score += 25
        elif subject_ratio > 0.7:
            risk_score += 15

        if opener_repetition_rate > 0.4:
            risk_score += 20
        elif opener_repetition_rate > 0.3:
            risk_score += 10

        if active_ratio > 0.9:
            risk_score += 10

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []

        if simple_ratio > 0.6:
            issues.append({
                "type": "simple_dominance",
                "description": f"Simple sentences dominate ({simple_ratio:.0%})",
                "description_zh": f"简单句占主导（{simple_ratio:.0%}）",
                "severity": "high" if simple_ratio > 0.7 else "medium"
            })

        if subject_ratio > 0.7:
            issues.append({
                "type": "subject_opening",
                "description": f"Most sentences start with subjects ({subject_ratio:.0%})",
                "description_zh": f"大多数句子以主语开头（{subject_ratio:.0%}）",
                "severity": "high" if subject_ratio > 0.8 else "medium"
            })

        if repeated_openers:
            issues.append({
                "type": "opener_repetition",
                "description": f"Repeated openers: {', '.join(repeated_openers[:3])}",
                "description_zh": f"重复的开头词：{', '.join(repeated_openers[:3])}",
                "severity": "medium"
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if simple_ratio > 0.5:
            recommendations.append("Combine related simple sentences using subordinate clauses (while, although, because).")
            recommendations_zh.append("使用从句（while, although, because）组合相关的简单句。")

        if subject_ratio > 0.7:
            recommendations.append("Vary sentence openings with adverbs, prepositional phrases, or subordinate clauses.")
            recommendations_zh.append("用副词、介词短语或从句变化句子开头。")

        if active_ratio > 0.85:
            recommendations.append("Add passive voice sentences for variety (15-25% is ideal).")
            recommendations_zh.append("添加被动语态句子以增加多样性（15-25%为理想比例）。")

        if not issues:
            recommendations.append("Sentence patterns show good variety.")
            recommendations_zh.append("句式模式显示良好的多样性。")

        # Syntactic Void Detection Integration
        # 句法空洞检测集成
        void_analysis = _detect_syntactic_voids(request.text)

        # Add void-related risk to overall score
        # 将空洞相关风险添加到总体分数
        if void_analysis.get("has_critical_void"):
            risk_score = min(100, risk_score + 25)
            issues.append({
                "type": "syntactic_void_critical",
                "description": f"Critical syntactic voids detected ({len(void_analysis.get('syntactic_voids', []))} patterns)",
                "description_zh": f"检测到严重句法空洞（{len(void_analysis.get('syntactic_voids', []))} 个模式）",
                "severity": "critical",
                "explanation": "Flowery but semantically empty phrases typical of AI text",
                "explanation_zh": "华丽但语义空洞的短语，是AI文本的典型特征",
                "patterns": [v.get("matched_text") for v in void_analysis.get("syntactic_voids", [])[:5]]
            })
            recommendations.append("Remove or rewrite flowery empty phrases with concrete, specific language.")
            recommendations_zh.append("删除或改写华丽空洞的短语，使用具体、明确的语言。")
        elif void_analysis.get("void_score", 0) > 30:
            risk_score = min(100, risk_score + 15)
            issues.append({
                "type": "syntactic_void_moderate",
                "description": f"Moderate syntactic voids detected (score: {void_analysis.get('void_score')})",
                "description_zh": f"检测到中等句法空洞（分数：{void_analysis.get('void_score')}）",
                "severity": "medium"
            })

        # Recalculate risk level after void integration
        # 在集成空洞检测后重新计算风险级别
        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        return SentencePatternResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            patterns_detected=patterns_detected,
            pattern_counts={
                "type_distribution": dict(type_counts),
                "opener_counts": dict(opener_counts.most_common(10)),
                "voice_distribution": dict(voice_counts),
                "simple_ratio": round(simple_ratio, 3),
                "subject_opening_ratio": round(subject_ratio, 3),
                "opener_repetition_rate": round(opener_repetition_rate, 3)
            },
            # Syntactic Void Detection Results
            # 句法空洞检测结果
            syntactic_voids=void_analysis.get("syntactic_voids", []),
            void_score=void_analysis.get("void_score", 0),
            void_density=void_analysis.get("void_density", 0.0),
            has_critical_void=void_analysis.get("has_critical_void", False)
        )

    except Exception as e:
        logger.error(f"Pattern analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_pattern_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for pattern improvement"""
    return await analyze_sentence_patterns(request)
