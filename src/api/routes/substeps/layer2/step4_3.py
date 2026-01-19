"""
Step 4.3: Sentence Merger Suggestions (句子合并建议)
Layer 2 Sentence Level - NOW WITH LLM!

Identify sentence pairs that can be merged for complexity using LLM.
使用LLM识别可以合并的句子对以增加复杂性。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SubstepBaseResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer2.step4_3_handler import Step4_3Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step4_3Handler()


@router.post("/analyze")
async def analyze_merge_candidates(request: SubstepBaseRequest):
    """
    Step 4.3: Identify sentence merge candidates (NOW WITH LLM!)
    步骤 4.3：识别可合并的句子（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step4_3Handler for LLM-based merge candidate analysis")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "risk_score": result.get("risk_score", 0),
            "risk_level": result.get("risk_level", "low"),
            "issues": result.get("issues", []),
            "recommendations": result.get("recommendations", []),
            "recommendations_zh": result.get("recommendations_zh", []),
            "processing_time_ms": processing_time_ms,
            "merge_candidates": result.get("merge_candidates", []),
            "total_pairs_analyzed": result.get("total_pairs_analyzed", 0),
            "mergeable_ratio": result.get("mergeable_ratio", 0)
        }

    except Exception as e:
        logger.error(f"Merge analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_merge_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for sentence merging"""
    return await analyze_merge_candidates(request)


@router.post("/apply")
async def apply_merges(request: SubstepBaseRequest):
    """Apply selected merges"""
    return await analyze_merge_candidates(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for merge issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的句子合并问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
        )
    except Exception as e:
        logger.error(f"Prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_modification(
    request: MergeModifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Apply AI modification for merge issues"""
    try:
        # Get working text from document_service
        document_text, locked_terms = await get_working_text(
            db=db,
            session_id=request.session_id,
            current_step="step4-3",
            document_id=request.document_id
        )

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found")

        # Convert Pydantic models to dicts
        issues_list = [issue.model_dump() for issue in request.selected_issues]

        result = await handler.apply_rewrite(
            document_text=document_text,
            selected_issues=issues_list,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )

        # Save modified text if session exists
        if request.session_id and result.get("modified_text"):
            await save_modified_text(
                db=db,
                session_id=request.session_id,
                step_name="step4-3",
                modified_text=result["modified_text"]
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
