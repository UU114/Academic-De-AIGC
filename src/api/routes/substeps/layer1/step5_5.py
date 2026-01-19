"""
Step 5.5: Rewrite Validation (改写结果验证)
Layer 1 Lexical Level - NOW WITH LLM!

Validate rewriting results for quality and compliance using LLM.
使用LLM验证改写结果的质量和合规性。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ValidationResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer1.step5_5_handler import Step5_5Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step5_5Handler()


class ValidationRequest(SubstepBaseRequest):
    """Validation request with original text"""
    original_text: str = ""


@router.post("/validate", response_model=ValidationResponse)
async def validate_rewrite(request: ValidationRequest):
    """
    Step 5.5: Validate rewriting results (NOW WITH LLM!)
    步骤 5.5：验证改写结果（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step5_5Handler for LLM-based validation")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ValidationResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            original_risk_score=result.get("original_risk_score", 0),
            final_risk_score=result.get("final_risk_score", 0),
            improvement=result.get("improvement", 0),
            locked_terms_check=result.get("locked_terms_check", True),
            semantic_similarity=result.get("semantic_similarity", 0),
            validation_passed=result.get("validation_passed", True)
        )

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_validation(request: SubstepBaseRequest):
    """Analyze without original text comparison"""
    val_request = ValidationRequest(
        text=request.text,
        original_text=request.text,
        session_id=request.session_id,
        locked_terms=request.locked_terms
    )
    return await validate_rewrite(val_request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for validation issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的验证问题生成的修改提示词",
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
    """Apply AI modification for validation issues"""
    try:
        # Use document_service to get working text
        # 使用 document_service 获取工作文本
        document_text, locked_terms = await get_working_text(
            db=db,
            session_id=request.session_id,
            current_step="step5-5",
            document_id=request.document_id
        )

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found")

        result = await handler.apply_rewrite(
            document_text=document_text,
            issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )

        # Save modified text to database
        # 保存修改后的文本到数据库
        if request.session_id and result.get("modified_text"):
            await save_modified_text(
                db=db,
                session_id=request.session_id,
                step_name="step5-5",
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
