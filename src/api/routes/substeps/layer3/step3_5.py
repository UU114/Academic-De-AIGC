"""
Step 3.5: Paragraph Transition Analysis (段落间过渡检测)
Layer 3 Paragraph Level - NOW WITH LLM!

Analyze transition quality between adjacent paragraphs using LLM.
使用LLM分析相邻段落之间的过渡质量。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ParagraphTransitionResponse,
    TransitionInfo,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer3.step3_5_handler import Step3_5Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step3_5Handler()


@router.post("/analyze", response_model=ParagraphTransitionResponse)
async def analyze_paragraph_transitions(request: SubstepBaseRequest):
    """
    Step 3.5: Analyze paragraph transitions (NOW WITH LLM!)
    步骤 3.5：分析段落过渡（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step3_5Handler for LLM-based paragraph transition analysis")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build transition info from result
        transitions = []
        for trans_info in result.get("transitions", []):
            if isinstance(trans_info, dict):
                transitions.append(TransitionInfo(
                    from_paragraph=trans_info.get("from_paragraph", 0),
                    to_paragraph=trans_info.get("to_paragraph", 1),
                    has_explicit_connector=trans_info.get("has_explicit_connector", False),
                    connector_word=trans_info.get("connector_word"),
                    semantic_echo_score=trans_info.get("semantic_echo_score", 0),
                    transition_quality=trans_info.get("transition_quality", "acceptable")
                ))

        return ParagraphTransitionResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            transitions=transitions,
            explicit_connector_count=result.get("explicit_connector_count", 0),
            explicit_ratio=result.get("explicit_ratio", 0),
            avg_semantic_echo=result.get("avg_semantic_echo", 0),
            suggestions=result.get("suggestions", [])
        )

    except Exception as e:
        logger.error(f"Transition analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest")
async def get_transition_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for transition improvements"""
    return await analyze_paragraph_transitions(request)


@router.post("/apply")
async def apply_transition_changes(request: SubstepBaseRequest):
    """Apply transition modifications"""
    return await analyze_paragraph_transitions(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for transition issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的段落过渡问题生成的修改提示词",
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
    """Apply AI modification for transition issues"""
    try:
        # Get working text using document_service
        # 使用 document_service 获取工作文本
        document_text, locked_terms = await get_working_text(
            db, request.session_id, "step3-5", request.document_id
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
                db, request.session_id, "step3-5", modified_text
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
