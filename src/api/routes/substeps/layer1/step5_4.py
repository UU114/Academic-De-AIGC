"""
Step 5.4: Paragraph Rewriting (LLM段落级改写)
Layer 1 Lexical Level - NOW WITH LLM!

Rewrite paragraphs to reduce AI fingerprints while preserving locked terms using LLM.
使用LLM改写段落以减少AI指纹同时保留锁定词汇。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ParagraphRewriteResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer1.step5_4_handler import Step5_4Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step5_4Handler()


@router.post("/analyze", response_model=ParagraphRewriteResponse)
async def rewrite_paragraphs(request: SubstepBaseRequest):
    """
    Step 5.4: Rewrite paragraphs (NOW WITH LLM!)
    步骤 5.4：改写段落（现在使用LLM！）
    """
    import json
    import re
    start_time = time.time()

    try:
        document_text = request.text

        # ================================================================
        # STEP 1: PRE-CALCULATE STATISTICS using rule-based parsing
        # 步骤1：使用规则解析预计算统计数据
        # ================================================================
        # Split into paragraphs
        paragraphs = [p.strip() for p in re.split(r'\n\n+', document_text) if p.strip()]

        # Fingerprint patterns for per-paragraph analysis
        type_a_patterns = [
            "delve", "utilize", "facilitate", "leverage", "plethora",
            "myriad", "pivotal", "paramount", "robust", "intricate"
        ]

        paragraph_stats = []
        paragraphs_to_rewrite = []
        total_fingerprints = 0

        for idx, para in enumerate(paragraphs):
            para_lower = para.lower()
            word_count = len(para_lower.split())

            # Count fingerprints in this paragraph
            para_fingerprints = 0
            for word in type_a_patterns:
                para_fingerprints += len(re.findall(r'\b' + word + r'\b', para_lower))

            # Calculate density per 100 words
            density = (para_fingerprints / word_count * 100) if word_count > 0 else 0.0
            total_fingerprints += para_fingerprints

            # Determine if needs rewrite
            needs_rewrite = density > 2.0

            paragraph_stats.append({
                "index": idx,
                "word_count": word_count,
                "fingerprint_count": para_fingerprints,
                "fingerprint_density": round(density, 3),
                "needs_rewrite": needs_rewrite
            })

            if needs_rewrite:
                paragraphs_to_rewrite.append(idx)

        total_words = sum(p["word_count"] for p in paragraph_stats)
        avg_fingerprint_density = (total_fingerprints / total_words * 100) if total_words > 0 else 0.0

        # Build pre-calculated statistics for LLM
        parsed_statistics = {
            "paragraph_count": len(paragraphs),
            "total_words": total_words,
            "total_fingerprints": total_fingerprints,
            "avg_fingerprint_density": round(avg_fingerprint_density, 3),
            "paragraphs_to_rewrite": paragraphs_to_rewrite,
            "paragraph_stats": paragraph_stats[:10]  # Sample for LLM
        }
        parsed_statistics_str = json.dumps(parsed_statistics, indent=2, ensure_ascii=False)
        logger.info(f"Step 5.4 pre-calculated: paragraphs_to_rewrite={len(paragraphs_to_rewrite)}, avg_density={avg_fingerprint_density:.3f}")

        # ================================================================
        # STEP 2: Call LLM handler with pre-calculated statistics
        # 步骤2：使用预计算统计数据调用LLM处理器
        # ================================================================
        logger.info("Calling Step5_4Handler for LLM-based paragraph rewriting")
        result = await handler.analyze(
            document_text=document_text,
            locked_terms=request.locked_terms or [],
            parsed_statistics=parsed_statistics_str,
            avg_fingerprint_density=f"{avg_fingerprint_density:.3f}"
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # ================================================================
        # STEP 3: Return PRE-CALCULATED statistics (not LLM's)
        # 步骤3：返回预计算的统计数据（不是LLM的）
        # ================================================================
        # Calculate risk based on pre-calculated metrics
        risk_score = 0
        if avg_fingerprint_density > 3.0:
            risk_score += 45
        elif avg_fingerprint_density > 2.0:
            risk_score += 30
        elif avg_fingerprint_density > 1.0:
            risk_score += 15
        if len(paragraphs_to_rewrite) > len(paragraphs) / 2:
            risk_score += 20
        risk_score = max(risk_score, result.get("risk_score", 0))
        risk_score = min(risk_score, 100)
        risk_level = "high" if risk_score >= 60 else "medium" if risk_score >= 30 else "low"

        return ParagraphRewriteResponse(
            risk_score=risk_score,
            risk_level=RiskLevel(risk_level),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            original_text=request.text,
            rewritten_text=result.get("rewritten_text", ""),
            changes=result.get("changes", []),
            locked_terms_preserved=result.get("locked_terms_preserved", True)
        )

    except Exception as e:
        logger.error(f"Paragraph rewriting failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_rewrite_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for rewriting"""
    return await rewrite_paragraphs(request)


@router.post("/apply")
async def apply_rewrites(request: SubstepBaseRequest):
    """Apply paragraph rewrites"""
    return await rewrite_paragraphs(request)


@router.post("/rewrite", response_model=ParagraphRewriteResponse)
async def rewrite_paragraphs_endpoint(request: SubstepBaseRequest):
    """Rewrite paragraphs (alias for analyze endpoint)"""
    return await rewrite_paragraphs(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for rewriting issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的改写问题生成的修改提示词",
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
    """Apply AI modification for rewriting issues"""
    try:
        # Use document_service to get working text
        # 使用 document_service 获取工作文本
        document_text, locked_terms = await get_working_text(
            db=db,
            session_id=request.session_id,
            current_step="step5-4",
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
                step_name="step5-4",
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
