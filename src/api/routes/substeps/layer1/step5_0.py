"""
Step 5.0: Lexical Context Preparation (词汇环境准备)
Layer 1 Lexical Level - NOW WITH LLM!

Prepare lexical analysis context and load vocabulary databases using LLM.
使用LLM准备词汇分析上下文并加载词汇数据库。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    LexicalContextResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer1.step5_0_handler import Step5_0Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step5_0Handler()


@router.post("/prepare", response_model=LexicalContextResponse)
async def prepare_lexical_context(request: SubstepBaseRequest):
    """
    Step 5.0: Prepare lexical analysis context (NOW WITH LLM!)
    步骤 5.0：准备词汇分析上下文（现在使用LLM！）
    """
    import json
    import re
    from collections import Counter
    start_time = time.time()

    try:
        document_text = request.text

        # ================================================================
        # STEP 1: PRE-CALCULATE STATISTICS using rule-based parsing
        # 步骤1：使用规则解析预计算统计数据
        # ================================================================
        # Tokenize text
        words = re.findall(r'\b[a-zA-Z]+\b', document_text.lower())
        total_words = len(words)
        unique_words = len(set(words))
        vocabulary_richness = unique_words / total_words if total_words > 0 else 0.0

        # Count word frequencies
        word_freq = Counter(words)
        top_words = word_freq.most_common(20)

        # Find overused words (> 1% of total)
        threshold = total_words * 0.01
        overused_words = [word for word, count in word_freq.items() if count > threshold and word not in ['the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'to', 'of', 'and', 'in', 'that', 'it', 'for', 'on', 'with', 'as', 'at', 'by']]

        # Check locked terms
        locked_terms = request.locked_terms or []
        locked_terms_status = []
        for term in locked_terms:
            term_lower = term.lower()
            count = document_text.lower().count(term_lower)
            locked_terms_status.append({
                "term": term,
                "found": count > 0,
                "count": count
            })

        # Build vocabulary stats
        vocabulary_stats = {
            "total_words": total_words,
            "unique_words": unique_words,
            "vocabulary_richness": round(vocabulary_richness, 3),
            "ttr": round(vocabulary_richness, 3)  # Type-Token Ratio
        }

        # Build pre-calculated statistics for LLM
        parsed_statistics = {
            "vocabulary_stats": vocabulary_stats,
            "top_words": [{"word": w, "count": c, "percentage": round(c/total_words*100, 2)} for w, c in top_words],
            "overused_words": overused_words[:10],
            "locked_terms_status": locked_terms_status
        }
        parsed_statistics_str = json.dumps(parsed_statistics, indent=2, ensure_ascii=False)
        logger.info(f"Step 5.0 pre-calculated: total_words={total_words}, vocabulary_richness={vocabulary_richness:.3f}")

        # ================================================================
        # STEP 2: Call LLM handler with pre-calculated statistics
        # 步骤2：使用预计算统计数据调用LLM处理器
        # ================================================================
        logger.info("Calling Step5_0Handler for LLM-based lexical context preparation")
        result = await handler.analyze(
            document_text=document_text,
            locked_terms=locked_terms,
            parsed_statistics=parsed_statistics_str,
            vocabulary_richness=f"{vocabulary_richness:.3f}"
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # ================================================================
        # STEP 3: Return PRE-CALCULATED statistics (not LLM's)
        # 步骤3：返回预计算的统计数据（不是LLM的）
        # ================================================================
        # Calculate risk based on pre-calculated metrics
        risk_score = 0
        if vocabulary_richness < 0.30:
            risk_score += 40
        elif vocabulary_richness < 0.35:
            risk_score += 25
        elif vocabulary_richness < 0.40:
            risk_score += 10
        if len(overused_words) > 5:
            risk_score += 15
        risk_score = max(risk_score, result.get("risk_score", 0))
        risk_score = min(risk_score, 100)
        risk_level = "high" if risk_score >= 60 else "medium" if risk_score >= 30 else "low"

        return LexicalContextResponse(
            risk_score=risk_score,
            risk_level=RiskLevel(risk_level),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            tokens=result.get("tokens", []),
            vocabulary_stats=vocabulary_stats  # Pre-calculated
        )

    except Exception as e:
        logger.error(f"Lexical context preparation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_context(request: SubstepBaseRequest):
    """Alias for prepare endpoint"""
    return await prepare_lexical_context(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for lexical context issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的词汇问题生成的修改提示词",
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
    """Apply AI modification for lexical context issues"""
    try:
        # Get working text (uses previous step's modified text if available)
        # 获取工作文本（如果有前一步骤的修改结果则使用）
        document_text, locked_terms = await get_working_text(
            db=db,
            session_id=request.session_id,
            current_step="step5-0",
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

        # Save modified text for next step to use
        # 保存修改后的文本供下一步骤使用
        if request.session_id and result.get("modified_text"):
            await save_modified_text(
                db=db,
                session_id=request.session_id,
                step_name="step5-0",
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
