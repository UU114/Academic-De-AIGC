"""
Step 3.0: Paragraph Identification & Segmentation (段落识别与分割)
Layer 3 Paragraph Level - NOW WITH LLM!

Automatically identify paragraph boundaries and filter non-body content using LLM.
使用LLM自动识别段落边界并过滤非正文内容。
"""

from fastapi import APIRouter, HTTPException
import logging
import time

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ParagraphIdentifyResponse,
    ParagraphMeta,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer3.step3_0_handler import Step3_0Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step3_0Handler()


@router.post("/identify", response_model=ParagraphIdentifyResponse)
async def identify_paragraphs(request: SubstepBaseRequest):
    """
    Step 3.0: Identify and segment paragraphs (NOW WITH LLM!)
    步骤 3.0：识别和分割段落（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step3_0Handler for LLM-based paragraph identification")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build paragraph metadata from result
        paragraph_metadata = []
        paragraphs = result.get("paragraphs", [])
        for i, para in enumerate(paragraphs):
            if isinstance(para, dict):
                paragraph_metadata.append(ParagraphMeta(
                    index=para.get("index", i),
                    word_count=para.get("word_count", 0),
                    sentence_count=para.get("sentence_count", 0),
                    section_index=para.get("section_index", 0),
                    preview=para.get("preview", "")
                ))

        return ParagraphIdentifyResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            paragraphs=[p.get("preview", "") if isinstance(p, dict) else str(p) for p in paragraphs],
            paragraph_count=result.get("paragraph_count", len(paragraphs)),
            paragraph_metadata=paragraph_metadata,
            filtered_count=result.get("filtered_count", 0)
        )

    except Exception as e:
        logger.error(f"Paragraph identification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=ParagraphIdentifyResponse)
async def analyze_paragraphs(request: SubstepBaseRequest):
    """Alias for identify endpoint"""
    return await identify_paragraphs(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for paragraph identification issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的段落识别问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
        )
    except Exception as e:
        logger.error(f"Prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_modification(request: MergeModifyRequest):
    """Apply AI modification for paragraph identification issues"""
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
