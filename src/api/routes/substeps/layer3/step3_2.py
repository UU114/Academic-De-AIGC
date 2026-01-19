"""
Step 3.2: Internal Coherence Analysis (段落内部连贯性检测)
Layer 3 Paragraph Level - NOW WITH LLM!

Detect logical relationships between sentences within a paragraph using LLM.
使用LLM检测段落内句子间的逻辑关系。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    CoherenceAnalysisResponse,
    ParagraphCoherenceInfo,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer3.step3_2_handler import Step3_2Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step3_2Handler()


@router.post("/analyze", response_model=CoherenceAnalysisResponse)
async def analyze_internal_coherence(request: SubstepBaseRequest):
    """
    Step 3.2: Analyze internal coherence (NOW WITH LLM!)
    步骤 3.2：分析内部连贯性（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step3_2Handler for LLM-based coherence analysis")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build paragraph coherence info from result
        paragraph_coherence = []
        for coh_info in result.get("paragraph_coherence", []):
            if isinstance(coh_info, dict):
                paragraph_coherence.append(ParagraphCoherenceInfo(
                    paragraph_index=coh_info.get("paragraph_index", 0),
                    subject_diversity=coh_info.get("subject_diversity", 0.5),
                    length_variation_cv=coh_info.get("length_variation_cv", 0),
                    logic_structure=coh_info.get("logic_structure", "mixed"),
                    connector_density=coh_info.get("connector_density", 0),
                    first_person_ratio=coh_info.get("first_person_ratio", 0),
                    overall_score=coh_info.get("overall_score", 50)
                ))

        return CoherenceAnalysisResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            paragraph_coherence=paragraph_coherence,
            overall_coherence_score=result.get("overall_coherence_score", 50),
            high_risk_paragraphs=result.get("high_risk_paragraphs", [])
        )

    except Exception as e:
        logger.error(f"Coherence analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest")
async def get_coherence_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for coherence improvement"""
    return await analyze_internal_coherence(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for coherence issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的连贯性问题生成的修改提示词",
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
    """Apply AI modification for coherence issues"""
    try:
        # Get working text using document_service
        # 使用 document_service 获取工作文本
        document_text, locked_terms = await get_working_text(
            db, request.session_id, "step3-2", request.document_id
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
                db, request.session_id, "step3-2", modified_text
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
