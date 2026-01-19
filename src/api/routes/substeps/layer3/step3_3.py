"""
Step 3.3: Anchor Density Analysis (锚点密度分析)
Layer 3 Paragraph Level - NOW WITH LLM!

Detect academic anchors (data, citations, evidence) and identify AI filler content using LLM.
使用LLM检测学术锚点（数据、引用、证据）并识别AI填充内容。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    AnchorDensityResponse,
    ParagraphAnchorInfo,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer3.step3_3_handler import Step3_3Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step3_3Handler()


@router.post("/analyze", response_model=AnchorDensityResponse)
async def analyze_anchor_density(request: SubstepBaseRequest):
    """
    Step 3.3: Analyze anchor density (NOW WITH LLM!)
    步骤 3.3：分析锚点密度（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step3_3Handler for LLM-based anchor density analysis")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build paragraph anchor info from result
        paragraph_densities = []
        for anchor_info in result.get("paragraph_densities", []):
            if isinstance(anchor_info, dict):
                paragraph_densities.append(ParagraphAnchorInfo(
                    paragraph_index=anchor_info.get("paragraph_index", 0),
                    word_count=anchor_info.get("word_count", 0),
                    anchor_count=anchor_info.get("anchor_count", 0),
                    density=anchor_info.get("density", 0),
                    has_hallucination_risk=anchor_info.get("has_hallucination_risk", False),
                    risk_level=anchor_info.get("risk_level", "low"),
                    anchor_types=anchor_info.get("anchor_types", {})
                ))

        return AnchorDensityResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            overall_density=result.get("overall_density", 0),
            paragraph_densities=paragraph_densities,
            high_risk_paragraphs=result.get("high_risk_paragraphs", []),
            anchor_type_distribution=result.get("anchor_type_distribution", {}),
            document_hallucination_risk=result.get("document_hallucination_risk", "low")
        )

    except Exception as e:
        logger.error(f"Anchor density analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_anchor_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for adding anchors"""
    return await analyze_anchor_density(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for anchor density issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的锚点密度问题生成的修改提示词",
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
    """Apply AI modification for anchor density issues"""
    try:
        # Get working text using document_service
        # 使用 document_service 获取工作文本
        document_text, locked_terms = await get_working_text(
            db, request.session_id, "step3-3", request.document_id
        )

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found in session")

        result = await handler.apply_rewrite(
            document_text=document_text,
            issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )

        modified_text = result.get("modified_text", "")

        # Save modified text to database
        # 保存修改后的文本到数据库
        if modified_text and request.session_id:
            await save_modified_text(
                db, request.session_id, "step3-3", modified_text
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
