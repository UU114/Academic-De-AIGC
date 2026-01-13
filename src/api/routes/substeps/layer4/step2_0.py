"""
Step 2.0: Section Identification (章节识别与角色标注)
Layer 4 Section Level - NOW WITH LLM!

Automatically detect section boundaries and identify functional roles using LLM.
使用LLM自动检测章节边界并识别功能角色。
"""

from fastapi import APIRouter, HTTPException
from typing import List
import logging
import time
import re

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SectionIdentifyResponse,
    SectionInfo,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer4.step2_0_handler import Step2_0Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step2_0Handler()


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\n+', text.strip())
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


@router.post("/identify", response_model=SectionIdentifyResponse)
async def identify_sections(request: SubstepBaseRequest):
    """
    Step 2.0: Identify sections and their roles (NOW WITH LLM!)
    步骤 2.0：识别章节及其角色（现在使用LLM！）
    """
    start_time = time.time()

    try:
        # Use LLM handler for analysis
        logger.info("Calling Step2_0Handler for LLM-based section identification")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract sections from result
        sections_data = result.get("sections", [])
        sections = [
            SectionInfo(
                index=s.get("index", i),
                role=s.get("role", "body"),
                start_paragraph=s.get("start_paragraph", 0),
                end_paragraph=s.get("end_paragraph", 0),
                word_count=s.get("word_count", 0),
                confidence=s.get("confidence", 0.5)
            )
            for i, s in enumerate(sections_data)
        ]

        paragraphs = _split_paragraphs(request.text)

        return SectionIdentifyResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            sections=sections,
            section_boundaries=[0, len(paragraphs)],
            total_sections=len(sections),
            total_paragraphs=len(paragraphs)
        )

    except Exception as e:
        logger.error(f"Section identification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=SectionIdentifyResponse)
async def analyze_sections(request: SubstepBaseRequest):
    """Step 2.0: Analyze sections (alias for identify)"""
    return await identify_sections(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for section issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的章节问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
        )
    except Exception as e:
        logger.error(f"Prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_modification(request: MergeModifyRequest):
    """Apply AI modification for section issues"""
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
