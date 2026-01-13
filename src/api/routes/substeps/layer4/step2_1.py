"""
Step 2.1: Section Order & Structure (章节顺序与结构检测)
Layer 4 Section Level - NOW WITH LLM!

Analyze section order and template matching using LLM.
使用LLM分析章节顺序和模板匹配。
"""

from fastapi import APIRouter, HTTPException
from typing import List
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SectionOrderResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer4.step2_1_handler import Step2_1Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step2_1Handler()

# Expected order for reference
EXPECTED_ORDER = ["introduction", "literature_review", "methodology", "results", "discussion", "conclusion"]


@router.post("/analyze", response_model=SectionOrderResponse)
async def analyze_section_order(request: SubstepBaseRequest):
    """
    Step 2.1: Analyze section order and structure (NOW WITH LLM!)
    步骤 2.1：分析章节顺序和结构（现在使用LLM！）
    """
    start_time = time.time()

    try:
        # Use LLM handler for analysis
        logger.info("Calling Step2_1Handler for LLM-based section order analysis")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return SectionOrderResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            order_match_score=result.get("order_match_score", 0),
            missing_sections=result.get("missing_sections", []),
            function_fusion_score=result.get("function_fusion_score", 0),
            current_order=result.get("current_order", []),
            expected_order=EXPECTED_ORDER
        )

    except Exception as e:
        logger.error(f"Section order analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for section order issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的章节顺序问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
        )
    except Exception as e:
        logger.error(f"Prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_modification(request: MergeModifyRequest):
    """Apply AI modification for section order issues"""
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
