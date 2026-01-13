"""
Step 5.3: Replacement Candidate Generation (替换候选生成)
Layer 1 Lexical Level - NOW WITH LLM!

Generate replacement candidates for fingerprint words using LLM.
使用LLM为指纹词生成替换候选。
"""

from fastapi import APIRouter, HTTPException
import logging
import time

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ReplacementGenerationResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer1.step5_3_handler import Step5_3Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step5_3Handler()


@router.post("/analyze", response_model=ReplacementGenerationResponse)
async def generate_replacements(request: SubstepBaseRequest):
    """
    Step 5.3: Generate replacement candidates (NOW WITH LLM!)
    步骤 5.3：生成替换候选（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step5_3Handler for LLM-based replacement generation")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ReplacementGenerationResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            replacements=result.get("replacements", []),
            replacement_count=result.get("replacement_count", 0)
        )

    except Exception as e:
        logger.error(f"Replacement generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_replacement_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for replacements"""
    return await generate_replacements(request)


@router.post("/apply")
async def apply_replacements(request: SubstepBaseRequest):
    """Apply selected replacements"""
    return await generate_replacements(request)


@router.post("/generate", response_model=ReplacementGenerationResponse)
async def generate_replacement_candidates(request: SubstepBaseRequest):
    """Generate replacement candidates (alias for analyze endpoint)"""
    return await generate_replacements(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for replacement issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的替换问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
        )
    except Exception as e:
        logger.error(f"Prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_modification(request: MergeModifyRequest):
    """Apply AI modification for replacement issues"""
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
