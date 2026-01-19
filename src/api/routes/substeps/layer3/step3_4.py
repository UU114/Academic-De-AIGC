"""
Step 3.4: Sentence Length Distribution (段内句长分布分析)
Layer 3 Paragraph Level - NOW WITH LLM!

Analyze sentence length variation within paragraphs using LLM.
使用LLM分析段落内句子长度的变化模式。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.services.text_parsing_service import get_body_paragraphs
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    SentenceLengthDistributionResponse,
    ParagraphSentenceLengthInfo,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer3.step3_4_handler import Step3_4Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step3_4Handler()


def _get_paragraph_preview(text: str, max_words: int = 8) -> str:
    """
    Get preview of paragraph (first few words)
    获取段落预览（前几个单词）
    """
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]) + "..."


@router.post("/analyze", response_model=SentenceLengthDistributionResponse)
async def analyze_sentence_length_distribution(request: SubstepBaseRequest):
    """
    Step 3.4: Analyze sentence length distribution (NOW WITH LLM!)
    步骤 3.4：分析句子长度分布（现在使用LLM！）
    """
    start_time = time.time()

    try:
        logger.info("Calling Step3_4Handler for LLM-based sentence length analysis")
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Parse paragraphs to get preview text for each
        # 解析段落以获取每个段落的预览文本
        body_paragraphs = get_body_paragraphs(request.text)
        paragraph_previews = {p.index: _get_paragraph_preview(p.text) for p in body_paragraphs}

        # Build paragraph sentence length info from result
        paragraph_lengths = []
        for len_info in result.get("paragraph_lengths", []):
            if isinstance(len_info, dict):
                para_idx = len_info.get("paragraph_index", 0)
                # Get preview from parsed paragraphs, fallback to empty string
                # 从解析的段落获取预览，如果不存在则使用空字符串
                preview = paragraph_previews.get(para_idx, "")
                paragraph_lengths.append(ParagraphSentenceLengthInfo(
                    paragraph_index=para_idx,
                    sentence_count=len_info.get("sentence_count", 0),
                    sentence_lengths=len_info.get("sentence_lengths", []),
                    mean_length=len_info.get("mean_length", 0),
                    std_length=len_info.get("std_length", 0),
                    cv=len_info.get("cv", 0),
                    burstiness=len_info.get("burstiness", 0.5),
                    has_short_sentence=len_info.get("has_short_sentence", False),
                    has_long_sentence=len_info.get("has_long_sentence", False),
                    rhythm_score=len_info.get("rhythm_score", 0.5),
                    preview=preview
                ))

        return SentenceLengthDistributionResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            paragraph_lengths=paragraph_lengths,
            low_burstiness_paragraphs=result.get("low_burstiness_paragraphs", []),
            overall_cv=result.get("overall_cv", 0)
        )

    except Exception as e:
        logger.error(f"Sentence length analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_length_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for length variation"""
    return await analyze_sentence_length_distribution(request)


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
            prompt_zh="根据选定的句长分布问题生成的修改提示词",
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
    """Apply AI modification for sentence length issues"""
    try:
        # Get working text using document_service
        # 使用 document_service 获取工作文本
        document_text, locked_terms = await get_working_text(
            db, request.session_id, "step3-4", request.document_id
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
                db, request.session_id, "step3-4", modified_text
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
