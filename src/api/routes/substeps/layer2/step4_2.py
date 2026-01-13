"""
Step 4.2: Sentence Length Analysis (段内句长分析与优化)
Layer 2 Sentence Level - NOW WITH LLM!

Analyze sentence length distribution within paragraphs using LLM.
使用LLM分析段落内句子长度分布。
"""

from fastapi import APIRouter, HTTPException
import logging
import time

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SentenceLengthDiversityResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer2.step4_2_handler import Step4_2Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step4_2Handler()


@router.post("/analyze", response_model=SentenceLengthDiversityResponse)
async def analyze_sentence_lengths(request: SubstepBaseRequest):
    """
    Step 4.2: Analyze sentence length distribution (NOW WITH LLM!)
    步骤 4.2：分析句子长度分布（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step4_2Handler for LLM-based sentence length analysis")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SentenceLengthDiversityResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            sentences=result.get("sentences", []),
            cv=result.get("cv", 0),
            burstiness=result.get("burstiness", 0),
            target_cv=result.get("target_cv", 0.4)
        )

    except Exception as e:
        logger.error(f"Length analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_length_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for length adjustment"""
    return await analyze_sentence_lengths(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for sentence length issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的句子长度问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
        )
    except Exception as e:
        logger.error(f"Prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_modification(request: MergeModifyRequest):
    """Apply AI modification for sentence length issues"""
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
