"""
Step 5.4: Paragraph Rewriting (LLM段落级改写)
Layer 1 Lexical Level - NOW WITH LLM!

Rewrite paragraphs to reduce AI fingerprints while preserving locked terms using LLM.
使用LLM改写段落以减少AI指纹同时保留锁定词汇。
"""

from fastapi import APIRouter, HTTPException
import logging
import time

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ParagraphRewriteResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer1.step5_4_handler import Step5_4Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step5_4Handler()


@router.post("/analyze", response_model=ParagraphRewriteResponse)
async def rewrite_paragraphs(request: SubstepBaseRequest):
    """
    Step 5.4: Rewrite paragraphs (NOW WITH LLM!)
    步骤 5.4：改写段落（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step5_4Handler for LLM-based paragraph rewriting")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ParagraphRewriteResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            original_text=request.text,
            rewritten_text=result.get("rewritten_text", ""),
            changes=result.get("changes", []),
            locked_terms_preserved=result.get("locked_terms_preserved", True)
        )

    except Exception as e:
        logger.error(f"Paragraph rewriting failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_rewrite_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for rewriting"""
    return await rewrite_paragraphs(request)


@router.post("/apply")
async def apply_rewrites(request: SubstepBaseRequest):
    """Apply paragraph rewrites"""
    return await rewrite_paragraphs(request)


@router.post("/rewrite", response_model=ParagraphRewriteResponse)
async def rewrite_paragraphs_endpoint(request: SubstepBaseRequest):
    """Rewrite paragraphs (alias for analyze endpoint)"""
    return await rewrite_paragraphs(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for rewriting issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的改写问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
        )
    except Exception as e:
        logger.error(f"Prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_modification(request: MergeModifyRequest):
    """Apply AI modification for rewriting issues"""
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
