"""
Layer 1 (Lexical Level) API Routes - Enhanced Version
第1层（词汇级）API路由 - 增强版

Provides endpoints for Layer 1 sub-steps:
- Step 5.0: Context Preparation
- Step 5.1: AIGC Fingerprint Detection
- Step 5.2: Human Feature Analysis
- Step 5.3: Replacement Candidate Generation
- Step 5.4: LLM Paragraph-Level Rewriting
- Step 5.5: Result Validation
- Full Pipeline

提供Layer 1子步骤的端点：
- 步骤5.0：上下文准备
- 步骤5.1：AIGC指纹检测
- 步骤5.2：人类特征分析
- 步骤5.3：替换候选生成
- 步骤5.4：LLM段落级改写
- 步骤5.5：结果验证
- 完整流程
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.analyzer.layers.lexical.context_preparation import (
    LexicalContextPreparer,
    LexicalContext,
)
from src.core.analyzer.layers.lexical.fingerprint_detector import (
    EnhancedFingerprintDetector,
)
from src.core.analyzer.layers.lexical.human_feature_analyzer import (
    HumanFeatureAnalyzer,
)
from src.core.analyzer.layers.lexical.candidate_generator import (
    ReplacementCandidateGenerator,
)
from src.core.analyzer.layers.lexical.paragraph_rewriter import (
    LLMParagraphRewriter,
)
from src.core.analyzer.layers.lexical.result_validator import (
    RewriteResultValidator,
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


# ============== Request/Response Models ==============

class ContextRequest(BaseModel):
    """Request for Step 5.0 Context Preparation"""
    document_text: str = Field(..., description="Full document text")
    session_id: Optional[str] = Field(None, description="Session ID for locked terms")
    colloquialism_level: int = Field(4, ge=0, le=10, description="Target formality level")


class FingerprintRequest(BaseModel):
    """Request for Step 5.1 Fingerprint Detection"""
    document_text: str = Field(..., description="Full document text")
    session_id: Optional[str] = Field(None, description="Session ID for locked terms")
    colloquialism_level: int = Field(4, ge=0, le=10)


class HumanFeatureRequest(BaseModel):
    """Request for Step 5.2 Human Feature Analysis"""
    document_text: str = Field(..., description="Full document text")
    session_id: Optional[str] = Field(None, description="Session ID for locked terms")
    colloquialism_level: int = Field(4, ge=0, le=10)


class CandidateRequest(BaseModel):
    """Request for Step 5.3 Candidate Generation"""
    document_text: str = Field(..., description="Full document text")
    session_id: Optional[str] = Field(None, description="Session ID for locked terms")
    colloquialism_level: int = Field(4, ge=0, le=10)


class RewriteRequest(BaseModel):
    """Request for Step 5.4 LLM Rewriting"""
    document_text: str = Field(..., description="Full document text")
    session_id: Optional[str] = Field(None, description="Session ID for locked terms")
    colloquialism_level: int = Field(4, ge=0, le=10)
    paragraph_indices: Optional[List[int]] = Field(None, description="Specific paragraphs to rewrite")


class FullPipelineRequest(BaseModel):
    """Request for full Layer 1 pipeline"""
    document_text: str = Field(..., description="Full document text")
    session_id: Optional[str] = Field(None, description="Session ID for locked terms")
    colloquialism_level: int = Field(4, ge=0, le=10)
    skip_validation: bool = Field(False, description="Skip Step 5.5 validation")


# ============== Step 5.0: Context Preparation ==============

@router.post("/step5-0/context")
async def prepare_context(request: ContextRequest):
    """
    Step 5.0: Prepare lexical analysis context
    步骤5.0：准备词汇分析上下文
    """
    try:
        preparer = LexicalContextPreparer()
        context = preparer.prepare_context(
            document_text=request.document_text,
            session_id=request.session_id,
            colloquialism_level=request.colloquialism_level,
        )

        return {
            "success": True,
            "step": "5.0",
            "step_name": "Context Preparation",
            "step_name_zh": "上下文准备",
            "data": preparer.get_context_summary(context),
        }

    except Exception as e:
        logger.error(f"Step 5.0 failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Step 5.1: Fingerprint Detection ==============

def _split_paragraphs(text: str) -> list:
    """Split text into paragraphs for PPL analysis"""
    import re
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _calculate_ppl_analysis(text: str) -> dict:
    """
    Calculate PPL (Perplexity) for the text
    计算文本的困惑度

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
        high_risk_paragraphs = []

        for i, para in enumerate(paragraphs):
            if len(para.split()) >= 10:  # Minimum 10 words for meaningful PPL
                para_ppl, para_used_onnx = calculate_onnx_ppl(para)
                if para_used_onnx and para_ppl is not None:
                    if para_ppl < 20:
                        para_risk = "high"
                        high_risk_paragraphs.append(i)
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
            "high_risk_paragraphs": high_risk_paragraphs,
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


@router.post("/step5-1/fingerprint")
async def detect_fingerprints(request: FingerprintRequest):
    """
    Step 5.1: Detect AIGC fingerprint words and phrases
    步骤5.1：检测AIGC指纹词汇和短语

    Now includes PPL (Perplexity) analysis integration.
    现已集成PPL（困惑度）分析。
    """
    try:
        # Prepare context
        preparer = LexicalContextPreparer()
        context = preparer.prepare_context(
            document_text=request.document_text,
            session_id=request.session_id,
            colloquialism_level=request.colloquialism_level,
        )

        # Detect fingerprints
        detector = EnhancedFingerprintDetector()
        result = detector.detect(context)

        # Get detection summary
        detection_summary = detector.get_detection_summary(result)

        # PPL Analysis Integration
        # PPL 分析集成
        ppl_analysis = _calculate_ppl_analysis(request.document_text)
        detection_summary["ppl_score"] = ppl_analysis.get("ppl_score")
        detection_summary["ppl_risk_level"] = ppl_analysis.get("ppl_risk_level")
        detection_summary["ppl_used_onnx"] = ppl_analysis.get("used_onnx", False)
        detection_summary["ppl_analysis"] = ppl_analysis

        return {
            "success": True,
            "step": "5.1",
            "step_name": "AIGC Fingerprint Detection",
            "step_name_zh": "AIGC指纹检测",
            "data": detection_summary,
        }

    except Exception as e:
        logger.error(f"Step 5.1 failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Step 5.2: Human Feature Analysis ==============

@router.post("/step5-2/human-features")
async def analyze_human_features(request: HumanFeatureRequest):
    """
    Step 5.2: Analyze human academic writing feature coverage
    步骤5.2：分析人类学术写作特征覆盖率
    """
    try:
        # Prepare context
        preparer = LexicalContextPreparer()
        context = preparer.prepare_context(
            document_text=request.document_text,
            session_id=request.session_id,
            colloquialism_level=request.colloquialism_level,
        )

        # Analyze human features
        analyzer = HumanFeatureAnalyzer()
        result = analyzer.analyze(context)

        return {
            "success": True,
            "step": "5.2",
            "step_name": "Human Feature Analysis",
            "step_name_zh": "人类特征分析",
            "data": analyzer.get_analysis_summary(result),
        }

    except Exception as e:
        logger.error(f"Step 5.2 failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Step 5.3: Candidate Generation ==============

@router.post("/step5-3/candidates")
async def generate_candidates(request: CandidateRequest):
    """
    Step 5.3: Generate replacement candidates for fingerprints
    步骤5.3：为指纹词生成替换候选
    """
    try:
        # Prepare context
        preparer = LexicalContextPreparer()
        context = preparer.prepare_context(
            document_text=request.document_text,
            session_id=request.session_id,
            colloquialism_level=request.colloquialism_level,
        )

        # Detect fingerprints
        detector = EnhancedFingerprintDetector()
        fingerprint_result = detector.detect(context)

        # Analyze human features
        human_analyzer = HumanFeatureAnalyzer()
        human_result = human_analyzer.analyze(context)

        # Generate candidates
        generator = ReplacementCandidateGenerator()
        result = generator.generate(context, fingerprint_result, human_result)

        return {
            "success": True,
            "step": "5.3",
            "step_name": "Replacement Candidate Generation",
            "step_name_zh": "替换候选生成",
            "data": generator.get_candidates_summary(result),
        }

    except Exception as e:
        logger.error(f"Step 5.3 failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Step 5.4: LLM Rewriting ==============

@router.post("/step5-4/rewrite")
async def rewrite_paragraphs(request: RewriteRequest):
    """
    Step 5.4: Rewrite paragraphs using LLM
    步骤5.4：使用LLM改写段落
    """
    try:
        # Prepare context
        preparer = LexicalContextPreparer()
        context = preparer.prepare_context(
            document_text=request.document_text,
            session_id=request.session_id,
            colloquialism_level=request.colloquialism_level,
        )

        # Detect fingerprints
        detector = EnhancedFingerprintDetector()
        fingerprint_result = detector.detect(context)

        # Analyze human features
        human_analyzer = HumanFeatureAnalyzer()
        human_result = human_analyzer.analyze(context)

        # Generate candidates
        generator = ReplacementCandidateGenerator()
        candidate_result = generator.generate(context, fingerprint_result, human_result)

        # Rewrite
        rewriter = LLMParagraphRewriter()
        result = await rewriter.rewrite(
            context, fingerprint_result, human_result, candidate_result
        )

        return {
            "success": True,
            "step": "5.4",
            "step_name": "LLM Paragraph Rewriting",
            "step_name_zh": "LLM段落改写",
            "data": rewriter.get_rewrite_summary(result),
        }

    except Exception as e:
        logger.error(f"Step 5.4 failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Step 5.5: Validation ==============

@router.post("/step5-5/validate")
async def validate_results(request: RewriteRequest):
    """
    Step 5.5: Validate rewrite results
    步骤5.5：验证改写结果
    """
    try:
        # Run full pipeline up to rewriting
        preparer = LexicalContextPreparer()
        context = preparer.prepare_context(
            document_text=request.document_text,
            session_id=request.session_id,
            colloquialism_level=request.colloquialism_level,
        )

        detector = EnhancedFingerprintDetector()
        fingerprint_result = detector.detect(context)

        human_analyzer = HumanFeatureAnalyzer()
        human_result = human_analyzer.analyze(context)

        generator = ReplacementCandidateGenerator()
        candidate_result = generator.generate(context, fingerprint_result, human_result)

        rewriter = LLMParagraphRewriter()
        rewrite_result = await rewriter.rewrite(
            context, fingerprint_result, human_result, candidate_result
        )

        # Validate
        validator = RewriteResultValidator()
        result = validator.validate(
            context, fingerprint_result, human_result, rewrite_result
        )

        return {
            "success": True,
            "step": "5.5",
            "step_name": "Result Validation",
            "step_name_zh": "结果验证",
            "data": validator.get_validation_summary(result),
        }

    except Exception as e:
        logger.error(f"Step 5.5 failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Full Pipeline ==============

@router.post("/full-pipeline")
async def run_full_pipeline(request: FullPipelineRequest):
    """
    Run complete Layer 1 analysis and rewriting pipeline
    运行完整的Layer 1分析和改写流程
    """
    try:
        results = {}

        # Step 5.0: Prepare context
        preparer = LexicalContextPreparer()
        context = preparer.prepare_context(
            document_text=request.document_text,
            session_id=request.session_id,
            colloquialism_level=request.colloquialism_level,
        )
        results["step_5_0"] = {
            "name": "Context Preparation",
            "name_zh": "上下文准备",
            "summary": preparer.get_context_summary(context),
        }

        # Step 5.1: Detect fingerprints
        detector = EnhancedFingerprintDetector()
        fingerprint_result = detector.detect(context)
        results["step_5_1"] = {
            "name": "Fingerprint Detection",
            "name_zh": "指纹检测",
            "summary": detector.get_detection_summary(fingerprint_result),
        }

        # Step 5.2: Analyze human features
        human_analyzer = HumanFeatureAnalyzer()
        human_result = human_analyzer.analyze(context)
        results["step_5_2"] = {
            "name": "Human Feature Analysis",
            "name_zh": "人类特征分析",
            "summary": human_analyzer.get_analysis_summary(human_result),
        }

        # Step 5.3: Generate candidates
        generator = ReplacementCandidateGenerator()
        candidate_result = generator.generate(context, fingerprint_result, human_result)
        results["step_5_3"] = {
            "name": "Candidate Generation",
            "name_zh": "候选生成",
            "summary": generator.get_candidates_summary(candidate_result),
        }

        # Step 5.4: Rewrite
        rewriter = LLMParagraphRewriter()
        rewrite_result = await rewriter.rewrite(
            context, fingerprint_result, human_result, candidate_result
        )
        results["step_5_4"] = {
            "name": "LLM Rewriting",
            "name_zh": "LLM改写",
            "summary": rewriter.get_rewrite_summary(rewrite_result),
        }

        # Step 5.5: Validate (optional)
        if not request.skip_validation:
            validator = RewriteResultValidator()
            validation_result = validator.validate(
                context, fingerprint_result, human_result, rewrite_result
            )
            results["step_5_5"] = {
                "name": "Validation",
                "name_zh": "验证",
                "summary": validator.get_validation_summary(validation_result),
            }

        # Build final output
        final_paragraphs = [
            {
                "index": p.paragraph_index,
                "original": p.original_text,
                "rewritten": p.rewritten_text,
                "changes": [
                    {"original": c.original, "replacement": c.replacement, "reason": c.reason}
                    for c in p.changes
                ],
            }
            for p in rewrite_result.paragraphs
        ]

        # Reconstruct final document
        final_document = "\n\n".join(p.rewritten_text for p in rewrite_result.paragraphs)

        return {
            "success": True,
            "pipeline": "Layer 1 Full Pipeline",
            "pipeline_zh": "Layer 1 完整流程",
            "steps": results,
            "final_document": final_document,
            "final_paragraphs": final_paragraphs,
            "overall_metrics": {
                "original_fingerprints": fingerprint_result.total_fingerprints,
                "original_risk": fingerprint_result.overall_risk_score,
                "original_human_score": human_result.overall_human_score,
                "paragraphs_rewritten": rewrite_result.paragraphs_rewritten,
                "total_changes": rewrite_result.total_changes,
                "aigc_removed": rewrite_result.aigc_removed_count,
                "human_features_added": rewrite_result.human_features_added_count,
            },
        }

    except Exception as e:
        logger.error(f"Full pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Analysis Only (No Rewrite) ==============

@router.post("/analyze-only")
async def analyze_only(request: ContextRequest):
    """
    Run analysis steps only (5.0-5.3), no rewriting
    仅运行分析步骤（5.0-5.3），不改写
    """
    try:
        # Step 5.0: Prepare context
        preparer = LexicalContextPreparer()
        context = preparer.prepare_context(
            document_text=request.document_text,
            session_id=request.session_id,
            colloquialism_level=request.colloquialism_level,
        )

        # Step 5.1: Detect fingerprints
        detector = EnhancedFingerprintDetector()
        fingerprint_result = detector.detect(context)

        # Step 5.2: Analyze human features
        human_analyzer = HumanFeatureAnalyzer()
        human_result = human_analyzer.analyze(context)

        # Step 5.3: Generate candidates
        generator = ReplacementCandidateGenerator()
        candidate_result = generator.generate(context, fingerprint_result, human_result)

        return {
            "success": True,
            "mode": "Analysis Only",
            "mode_zh": "仅分析",
            "context": preparer.get_context_summary(context),
            "fingerprints": detector.get_detection_summary(fingerprint_result),
            "human_features": human_analyzer.get_analysis_summary(human_result),
            "candidates": generator.get_candidates_summary(candidate_result),
            "overall": {
                "aigc_risk_score": fingerprint_result.overall_risk_score,
                "aigc_risk_level": fingerprint_result.risk_level,
                "human_score": human_result.overall_human_score,
                "total_fingerprints": fingerprint_result.total_fingerprints,
                "replaceable_count": candidate_result.total_replaceable,
            },
        }

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
