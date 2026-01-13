"""
Step 5.1: AIGC Fingerprint Detection (AIGC指纹词检测)
Layer 1 Lexical Level - NOW WITH LLM!

Detect AI fingerprint words and phrases using LLM.
使用LLM检测AI指纹词汇和短语。
"""

from fastapi import APIRouter, HTTPException
import logging
import time

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    FingerprintDetectionResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer1.step5_1_handler import Step5_1Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step5_1Handler()


@router.post("/analyze", response_model=FingerprintDetectionResponse)
async def detect_fingerprints(request: SubstepBaseRequest):
    """
    Step 5.1: Detect AIGC fingerprints (NOW WITH LLM!)
    步骤 5.1：检测AIGC指纹（现在使用LLM！）

    Supports caching: If this step was analyzed before for the same session,
    cached results will be returned instead of calling LLM again.
    支持缓存：如果此步骤已为同一会话分析过，将返回缓存结果而不是再次调用LLM。
    """
    start_time = time.time()

    try:
        logger.info("Calling Step5_1Handler for LLM-based fingerprint detection")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or [],
            session_id=request.session_id,
            step_name="layer1-step5-1",  # Unique step identifier for caching
            use_cache=True  # Enable caching
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return FingerprintDetectionResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            type_a_words=result.get("type_a_words", []),
            type_b_words=result.get("type_b_words", []),
            type_c_phrases=result.get("type_c_phrases", []),
            total_fingerprints=result.get("total_fingerprints", 0),
            fingerprint_density=result.get("fingerprint_density", 0),
            ppl_score=result.get("ppl_score"),
            ppl_risk_level=result.get("ppl_risk_level"),
            ppl_used_onnx=result.get("ppl_used_onnx", False),
            ppl_analysis=result.get("ppl_analysis", {})
        )

    except Exception as e:
        logger.error(f"Fingerprint detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_fingerprint_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for fingerprint removal"""
    return await detect_fingerprints(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for fingerprint issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的指纹词问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
        )
    except Exception as e:
        logger.error(f"Prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_modification(request: MergeModifyRequest):
    """Apply AI modification for fingerprint issues"""
    try:
        from src.services.session_service import SessionService
        session_service = SessionService()
        session_data = await session_service.get_session(request.session_id) if request.session_id else None
        document_text = session_data.get("document_text", "") if session_data else ""

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found in session")

        result = await handler.apply_rewrite(
            document_text=document_text,
            issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=session_data.get("locked_terms", []) if session_data else []
        )
        return MergeModifyApplyResponse(
            modified_text=result.get("modified_text", ""),
            changes_summary_zh=result.get("changes_summary_zh", ""),
            changes_count=result.get("changes_count", 0),
            issues_addressed=[i.type for i in request.selected_issues],
            remaining_attempts=3
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Modification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
