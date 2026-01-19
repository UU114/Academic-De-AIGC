"""
Step 2.3: Internal Structure Similarity (章节内部结构相似性检测)
Layer 4 Section Level - NOW WITH LLM!

Analyze internal structure similarity using LLM.
使用LLM分析章节内部结构相似性。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    InternalSimilarityResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer4.step2_3_handler import Step2_3Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step2_3Handler()


@router.post("/analyze", response_model=InternalSimilarityResponse)
async def analyze_internal_similarity(request: SubstepBaseRequest):
    """
    Step 2.3: Analyze internal structure similarity (NOW WITH LLM!)
    步骤 2.3：分析章节内部结构相似性（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step2_3Handler for LLM-based internal similarity analysis")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return InternalSimilarityResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            similarity_score=result.get("similarity_score", 0),
            function_patterns=result.get("function_patterns", []),
            pattern_count=result.get("pattern_count", 0),
            unique_patterns=result.get("unique_patterns", 0)
        )

    except Exception as e:
        logger.error(f"Internal similarity analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for internal similarity issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的内部相似性问题生成的修改提示词",
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
    """Apply AI modification for internal similarity issues"""
    try:
        # Get working text using document_service
        document_text, locked_terms = await get_working_text(
            db, request.session_id, "step2-3", request.document_id
        )

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found in session")

        result = await handler.apply_rewrite(
            document_text=document_text,
            issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )

        # Save modified text to database
        modified_text = result.get("modified_text", "")
        if modified_text and request.session_id:
            await save_modified_text(
                db, request.session_id, "step2-3", modified_text
            )

        return MergeModifyApplyResponse(
            modified_text=modified_text,
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
