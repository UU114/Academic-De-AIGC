"""
Step 5.1: AIGC Fingerprint Detection (AIGC指纹词检测)
Layer 1 Lexical Level

Detect AI fingerprint words and phrases.
检测AI指纹词汇和短语。

Now integrated with PPL (Perplexity) Calculator for enhanced detection.
现已集成 PPL（困惑度）计算器以增强检测能力。
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional, Tuple
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    FingerprintDetectionResponse,
    RiskLevel,
)

# Import PPL Calculator for true perplexity measurement
# 导入 PPL 计算器用于真实困惑度测量
try:
    from src.core.analyzer.ppl_calculator import (
        calculate_onnx_ppl,
        is_onnx_available,
        get_model_info
    )
    PPL_AVAILABLE = True
except ImportError:
    PPL_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter()


# Type A: Dead Giveaway words (very high risk)
TYPE_A_WORDS = {
    "delve": 99,
    "underscore": 95,
    "harness": 92,
    "unveil": 87,
    "pivotal": 98,
    "intricate": 96,
    "multifaceted": 94,
    "paramount": 88,
    "tapestry": 93,
    "realm": 95,
    "landscape": 97,
    "endeavor": 90,
    "embark": 88,
    "myriad": 85,
}

# Type B: Academic Clichés (medium risk)
TYPE_B_WORDS = {
    "comprehensive": 91,
    "robust": 89,
    "seamless": 86,
    "leverage": 90,
    "facilitate": 84,
    "utilize": 80,
    "crucial": 85,
    "holistic": 85,
    "transformative": 84,
    "innovative": 82,
    "synergy": 80,
}

# Type C: Fingerprint Phrases
TYPE_C_PHRASES = {
    "in conclusion": 99,
    "important to note": 96,
    "not only but also": 94,
    "ever-evolving": 95,
    "crucial role": 92,
    "in the realm of": 30,
    "a plethora of": 82,
    "pave the way": 88,
    "shed light on": 88,
    "it is worth noting": 90,
}


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _calculate_ppl_analysis(text: str) -> Dict[str, Any]:
    """
    Calculate PPL (Perplexity) for the entire text
    计算整个文本的困惑度

    Returns:
        Dict with ppl_score, ppl_risk_level, used_onnx, and per-paragraph analysis
    """
    if not PPL_AVAILABLE:
        logger.warning("PPL Calculator not available, skipping PPL analysis")
        return {
            "ppl_score": None,
            "ppl_risk_level": None,
            "used_onnx": False,
            "paragraphs": [],
            "available": False,
            "reason": "PPL module not imported"
        }

    if not is_onnx_available():
        logger.warning("ONNX model not available, skipping PPL analysis")
        return {
            "ppl_score": None,
            "ppl_risk_level": None,
            "used_onnx": False,
            "paragraphs": [],
            "available": False,
            "reason": "ONNX model not loaded"
        }

    try:
        # Calculate overall PPL
        # 计算整体困惑度
        overall_ppl, used_onnx = calculate_onnx_ppl(text)

        if not used_onnx or overall_ppl is None:
            return {
                "ppl_score": None,
                "ppl_risk_level": None,
                "used_onnx": False,
                "paragraphs": [],
                "available": True,
                "reason": "Calculation failed"
            }

        # Determine risk level based on PPL
        # 根据 PPL 确定风险级别
        # Lower PPL = more predictable = more AI-like
        # 较低 PPL = 更可预测 = 更像 AI
        if overall_ppl < 20:
            ppl_risk_level = "high"  # Very predictable, AI-like
        elif overall_ppl < 40:
            ppl_risk_level = "medium"  # Moderately predictable
        else:
            ppl_risk_level = "low"  # High perplexity, human-like

        # Calculate per-paragraph PPL for detailed analysis
        # 计算每段的 PPL 进行详细分析
        paragraphs = _split_paragraphs(text)
        paragraph_analysis = []

        for i, para in enumerate(paragraphs):
            if len(para.split()) >= 10:  # Minimum 10 words for meaningful PPL
                para_ppl, para_used_onnx = calculate_onnx_ppl(para)
                if para_used_onnx and para_ppl is not None:
                    if para_ppl < 20:
                        para_risk = "high"
                    elif para_ppl < 40:
                        para_risk = "medium"
                    else:
                        para_risk = "low"

                    paragraph_analysis.append({
                        "index": i,
                        "ppl": round(para_ppl, 2),
                        "risk_level": para_risk,
                        "word_count": len(para.split()),
                        "preview": para[:80] + "..." if len(para) > 80 else para
                    })

        logger.info(f"PPL Analysis: overall={overall_ppl:.2f}, risk={ppl_risk_level}")

        return {
            "ppl_score": round(overall_ppl, 2),
            "ppl_risk_level": ppl_risk_level,
            "used_onnx": True,
            "paragraphs": paragraph_analysis,
            "high_risk_paragraphs": [p["index"] for p in paragraph_analysis if p["risk_level"] == "high"],
            "available": True,
            "model_info": get_model_info()
        }

    except Exception as e:
        logger.error(f"PPL calculation failed: {e}")
        return {
            "ppl_score": None,
            "ppl_risk_level": None,
            "used_onnx": False,
            "paragraphs": [],
            "available": True,
            "reason": str(e)
        }


def _detect_fingerprints(text: str, locked_terms: List[str]) -> Dict[str, List[Dict]]:
    """Detect all types of fingerprints"""
    text_lower = text.lower()
    locked_lower = [t.lower() for t in locked_terms]

    results = {"type_a": [], "type_b": [], "type_c": []}

    # Detect Type A words
    for word, weight in TYPE_A_WORDS.items():
        if word in locked_lower:
            continue
        pattern = rf'\b{word}\b'
        matches = list(re.finditer(pattern, text_lower))
        for m in matches:
            context_start = max(0, m.start() - 30)
            context_end = min(len(text), m.end() + 30)
            results["type_a"].append({
                "word": word,
                "weight": weight,
                "position": m.start(),
                "context": text[context_start:context_end]
            })

    # Detect Type B words
    for word, weight in TYPE_B_WORDS.items():
        if word in locked_lower:
            continue
        pattern = rf'\b{word}\b'
        matches = list(re.finditer(pattern, text_lower))
        for m in matches:
            context_start = max(0, m.start() - 30)
            context_end = min(len(text), m.end() + 30)
            results["type_b"].append({
                "word": word,
                "weight": weight,
                "position": m.start(),
                "context": text[context_start:context_end]
            })

    # Detect Type C phrases
    for phrase, weight in TYPE_C_PHRASES.items():
        pattern = phrase.replace(" ", r"\s+")
        matches = list(re.finditer(pattern, text_lower))
        for m in matches:
            context_start = max(0, m.start() - 20)
            context_end = min(len(text), m.end() + 40)
            results["type_c"].append({
                "phrase": phrase,
                "weight": weight,
                "position": m.start(),
                "context": text[context_start:context_end]
            })

    return results


@router.post("/analyze", response_model=FingerprintDetectionResponse)
async def detect_fingerprints(request: SubstepBaseRequest):
    """
    Step 5.1: Detect AIGC fingerprints
    步骤 5.1：检测AIGC指纹

    - Type A: Dead giveaway words
    - Type B: Academic clichés
    - Type C: Fingerprint phrases
    """
    start_time = time.time()

    try:
        locked_terms = request.locked_terms or []
        fingerprints = _detect_fingerprints(request.text, locked_terms)

        type_a_count = len(fingerprints["type_a"])
        type_b_count = len(fingerprints["type_b"])
        type_c_count = len(fingerprints["type_c"])
        total_fingerprints = type_a_count + type_b_count + type_c_count

        # Calculate density
        word_count = len(request.text.split())
        fingerprint_density = (total_fingerprints / word_count) * 100 if word_count > 0 else 0

        # Calculate risk score
        risk_score = 0

        # Type A is critical
        if type_a_count >= 3:
            risk_score += 50
        elif type_a_count >= 1:
            risk_score += 30

        # Type B adds moderate risk
        if type_b_count >= 5:
            risk_score += 25
        elif type_b_count >= 2:
            risk_score += 15

        # Type C adds moderate risk
        if type_c_count >= 3:
            risk_score += 20
        elif type_c_count >= 1:
            risk_score += 10

        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        # Build issues
        issues = []

        if type_a_count > 0:
            issues.append({
                "type": "dead_giveaway",
                "description": f"{type_a_count} dead giveaway words found (delve, pivotal, etc.)",
                "description_zh": f"发现 {type_a_count} 个死证词（delve, pivotal 等）",
                "severity": "critical",
                "words": [f["word"] for f in fingerprints["type_a"]]
            })

        if type_b_count >= 3:
            issues.append({
                "type": "academic_cliches",
                "description": f"{type_b_count} academic clichés found",
                "description_zh": f"发现 {type_b_count} 个学术陈词",
                "severity": "high" if type_b_count >= 5 else "medium",
                "words": [f["word"] for f in fingerprints["type_b"]]
            })

        if type_c_count >= 1:
            issues.append({
                "type": "fingerprint_phrases",
                "description": f"{type_c_count} fingerprint phrases found",
                "description_zh": f"发现 {type_c_count} 个指纹短语",
                "severity": "high" if type_c_count >= 3 else "medium",
                "phrases": [f["phrase"] for f in fingerprints["type_c"]]
            })

        # Build recommendations
        recommendations = []
        recommendations_zh = []

        if type_a_count > 0:
            recommendations.append("CRITICAL: Remove or replace dead giveaway words immediately.")
            recommendations_zh.append("紧急：立即删除或替换死证词。")

        if type_b_count > 0:
            recommendations.append("Replace academic clichés with more specific, natural alternatives.")
            recommendations_zh.append("用更具体、自然的替代词替换学术陈词。")

        if type_c_count > 0:
            recommendations.append("Rewrite phrases to avoid AI detection patterns.")
            recommendations_zh.append("改写短语以避免AI检测模式。")

        if not issues:
            recommendations.append("No significant AI fingerprints detected.")
            recommendations_zh.append("未检测到明显的AI指纹。")

        # PPL Analysis Integration
        # PPL 分析集成
        ppl_analysis = _calculate_ppl_analysis(request.text)

        # Add PPL-related risk to overall score
        # 将 PPL 相关风险添加到总体分数
        if ppl_analysis.get("ppl_risk_level") == "high":
            risk_score = min(100, risk_score + 20)
            issues.append({
                "type": "low_perplexity",
                "description": f"Low perplexity detected (PPL: {ppl_analysis.get('ppl_score', 'N/A')})",
                "description_zh": f"检测到低困惑度（PPL: {ppl_analysis.get('ppl_score', 'N/A')}）",
                "severity": "high",
                "explanation": "Text is highly predictable, typical of AI-generated content",
                "explanation_zh": "文本高度可预测，是AI生成内容的典型特征"
            })
            recommendations.append("Increase text unpredictability by adding unique expressions and varied sentence structures.")
            recommendations_zh.append("通过添加独特表达和多样化句子结构来增加文本的不可预测性。")
        elif ppl_analysis.get("ppl_risk_level") == "medium":
            risk_score = min(100, risk_score + 10)
            issues.append({
                "type": "moderate_perplexity",
                "description": f"Moderate perplexity detected (PPL: {ppl_analysis.get('ppl_score', 'N/A')})",
                "description_zh": f"检测到中等困惑度（PPL: {ppl_analysis.get('ppl_score', 'N/A')}）",
                "severity": "medium"
            })

        # Recalculate risk level after PPL integration
        # 在集成 PPL 后重新计算风险级别
        risk_level = RiskLevel.HIGH if risk_score >= 60 else RiskLevel.MEDIUM if risk_score >= 35 else RiskLevel.LOW

        return FingerprintDetectionResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=int((time.time() - start_time) * 1000),
            type_a_words=fingerprints["type_a"],
            type_b_words=fingerprints["type_b"],
            type_c_phrases=fingerprints["type_c"],
            total_fingerprints=total_fingerprints,
            fingerprint_density=round(fingerprint_density, 3),
            # PPL Analysis Results
            # PPL 分析结果
            ppl_score=ppl_analysis.get("ppl_score"),
            ppl_risk_level=ppl_analysis.get("ppl_risk_level"),
            ppl_used_onnx=ppl_analysis.get("used_onnx", False),
            ppl_analysis=ppl_analysis
        )

    except Exception as e:
        logger.error(f"Fingerprint detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_fingerprint_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for fingerprint removal"""
    return await detect_fingerprints(request)
