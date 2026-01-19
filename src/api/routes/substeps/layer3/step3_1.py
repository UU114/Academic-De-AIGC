"""
Step 3.1: Paragraph Role Detection (段落角色识别)
Layer 3 Paragraph Level - NOW WITH LLM!

Identify the functional role of each paragraph using LLM.
使用LLM识别每个段落的功能角色。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ParagraphRoleResponse,
    ParagraphRoleInfo,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer3.step3_1_handler import Step3_1Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step3_1Handler()


@router.post("/analyze", response_model=ParagraphRoleResponse)
async def analyze_paragraph_roles(request: SubstepBaseRequest):
    """
    Step 3.1: Detect paragraph roles (NOW WITH LLM!)
    步骤 3.1：检测段落角色（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step3_1Handler for LLM-based paragraph role detection")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build paragraph role info from result
        paragraph_roles = []
        for role_info in result.get("paragraph_roles", []):
            if isinstance(role_info, dict):
                paragraph_roles.append(ParagraphRoleInfo(
                    paragraph_index=role_info.get("paragraph_index", 0),
                    role=role_info.get("role", "body"),
                    confidence=role_info.get("confidence", 0.5),
                    section_index=role_info.get("section_index", 0),
                    role_matches_section=role_info.get("role_matches_section", True),
                    keywords_found=role_info.get("keywords_found", [])
                ))

        return ParagraphRoleResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            paragraph_roles=paragraph_roles,
            role_distribution=result.get("role_distribution", {}),
            uniformity_score=result.get("uniformity_score", 0),
            missing_roles=result.get("missing_roles", [])
        )

    except Exception as e:
        logger.error(f"Paragraph role detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-role")
async def update_paragraph_role(request: SubstepBaseRequest):
    """Manually update paragraph role"""
    return await analyze_paragraph_roles(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for paragraph role issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的段落角色问题生成的修改提示词",
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
    """Apply AI modification for paragraph role issues"""
    try:
        # Get working text using document_service
        # 使用 document_service 获取工作文本
        document_text, locked_terms = await get_working_text(
            db, request.session_id, "step3-1", request.document_id
        )

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found in session or database")

        # Convert Pydantic models to dicts
        issues_list = [issue.model_dump() for issue in request.selected_issues]

        result = await handler.apply_rewrite(
            document_text=document_text,
            selected_issues=issues_list,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )

        modified_text = result.get("modified_text", "")

        # Save modified text to database
        # 保存修改后的文本到数据库
        if modified_text and request.session_id:
            await save_modified_text(
                db, request.session_id, "step3-1", modified_text
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
