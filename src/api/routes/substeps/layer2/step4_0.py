"""
Step 4.0: Sentence Identification & Labeling (句子识别与标注)
Layer 2 Sentence Level - NOW WITH LLM!

Receive paragraph context, split into sentences, label type and function using LLM.
使用LLM接收段落上下文，分割句子，标注类型和功能。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SentenceContextResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer2.step4_0_handler import Step4_0Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step4_0Handler()


@router.post("/identify", response_model=SentenceContextResponse)
async def identify_sentences(request: SubstepBaseRequest):
    """
    Step 4.0: Identify and label sentences (NOW WITH LLM!)
    步骤 4.0：识别和标注句子（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step4_0Handler for LLM-based sentence identification")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SentenceContextResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            sentences=result.get("sentences", []),
            sentence_count=result.get("sentence_count", 0),
            paragraph_context=result.get("paragraph_context", [])
        )

    except Exception as e:
        logger.error(f"Sentence identification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_sentences(request: SubstepBaseRequest):
    """Alias for identify endpoint"""
    return await identify_sentences(request)


@router.post("/prepare", response_model=SentenceContextResponse)
async def prepare_sentence_context(request: SubstepBaseRequest):
    """Prepare sentence context (alias for identify endpoint)"""
    return await identify_sentences(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for sentence identification issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的句子识别问题生成的修改提示词",
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
    """Apply AI modification for sentence identification issues"""
    try:
        # Get working text from document_service
        document_text, locked_terms = await get_working_text(
            db=db,
            session_id=request.session_id,
            current_step="step4-0",
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
                step_name="step4-0",
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
