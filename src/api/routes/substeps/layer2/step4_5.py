"""
Step 4.5: Pattern Diversification (句式多样化改写)
Layer 2 Sentence Level - NOW WITH LLM!

Suggest and apply sentence pattern diversification using LLM.
使用LLM建议并应用句式多样化改写。
"""

from fastapi import APIRouter, HTTPException
import logging
import time

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SentenceRewriteResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer2.step4_5_handler import Step4_5Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step4_5Handler()


@router.post("/analyze", response_model=SentenceRewriteResponse)
async def analyze_diversification(request: SubstepBaseRequest):
    """
    Step 4.5: Analyze and suggest pattern diversification (NOW WITH LLM!)
    步骤 4.5：分析并建议句式多样化（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step4_5Handler for LLM-based diversification analysis")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SentenceRewriteResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            original_sentences=result.get("original_sentences", []),
            rewritten_sentences=result.get("rewritten_sentences", []),
            changes=result.get("changes", [])
        )

    except Exception as e:
        logger.error(f"Diversification analysis failed: {e}", exc_info=True)
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
    """Rewrite sentences for diversification (alias for analyze endpoint)"""
    return await analyze_diversification(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for diversification issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的句式多样化问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
        )
    except Exception as e:
        logger.error(f"Prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_modification(request: MergeModifyRequest):
    """Apply AI modification for diversification issues"""
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
