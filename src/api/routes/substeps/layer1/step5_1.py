"""
Step 5.1: AIGC Fingerprint Detection (AIGC指纹词检测)
Layer 1 Lexical Level - NOW WITH LLM!

Detect AI fingerprint words and phrases using LLM.
使用LLM检测AI指纹词汇和短语。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from src.db.database import get_db
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    FingerprintDetectionResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer1.step5_1_handler import Step5_1Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handler
handler = Step5_1Handler()


@router.post("/analyze", response_model=FingerprintDetectionResponse)
async def detect_fingerprints(request: SubstepBaseRequest):
    """
    Step 5.1: Detect AIGC fingerprints (NOW WITH LLM!)
    步骤 5.1：检测AIGC指纹（现在使用LLM！）

    Supports caching: If this step was analyzed before for the same session,
    cached results will be returned instead of calling LLM again.
    支持缓存：如果此步骤已为同一会话分析过，将返回缓存结果而不是再次调用LLM。
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
        # Type A fingerprint words (dead giveaways)
        type_a_patterns = [
            "delve", "utilize", "facilitate", "leverage", "aforementioned",
            "plethora", "myriad", "pivotal", "paramount", "comprehensive",
            "robust", "intricate", "underscore", "showcase", "foster",
            "realm", "landscape", "navigate", "embark", "streamline"
        ]
        # Type B cliche phrases
        type_b_patterns = [
            r"plays a crucial role", r"is of paramount importance",
            r"it is worth noting", r"it is important to note",
            r"in today's world", r"in the modern era",
            r"a wide range of", r"various aspects of",
            r"this underscores the importance", r"has become increasingly",
            r"needless to say", r"it goes without saying"
        ]
        # Type C filler phrases
        type_c_patterns = [
            r"as previously mentioned", r"it can be argued that",
            r"in light of the above", r"with this in mind",
            r"taking into account"
        ]

        text_lower = document_text.lower()
        word_count = len(text_lower.split())

        # Detect Type A
        type_a_matches = []
        for word in type_a_patterns:
            count = len(re.findall(r'\b' + word + r'\b', text_lower))
            if count > 0:
                type_a_matches.append({
                    "word": word,
                    "count": count,
                    "severity": "high"
                })

        # Detect Type B
        type_b_matches = []
        for pattern in type_b_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                type_b_matches.append({
                    "phrase": pattern.replace(r'\b', ''),
                    "count": len(matches),
                    "severity": "high"
                })

        # Detect Type C
        type_c_matches = []
        for pattern in type_c_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                type_c_matches.append({
                    "phrase": pattern.replace(r'\b', ''),
                    "count": len(matches),
                    "severity": "medium"
                })

        total_fingerprints = (
            sum(m["count"] for m in type_a_matches) +
            sum(m["count"] for m in type_b_matches) +
            sum(m["count"] for m in type_c_matches)
        )
        fingerprint_density = (total_fingerprints / word_count * 100) if word_count > 0 else 0.0

        # Build pre-calculated statistics for LLM
        parsed_statistics = {
            "word_count": word_count,
            "type_a_count": sum(m["count"] for m in type_a_matches),
            "type_b_count": sum(m["count"] for m in type_b_matches),
            "type_c_count": sum(m["count"] for m in type_c_matches),
            "total_fingerprints": total_fingerprints,
            "fingerprint_density": round(fingerprint_density, 3),
            "type_a_matches": type_a_matches[:5],
            "type_b_matches": type_b_matches[:5],
            "type_c_matches": type_c_matches[:5]
        }
        parsed_statistics_str = json.dumps(parsed_statistics, indent=2, ensure_ascii=False)
        logger.info(f"Step 5.1 pre-calculated: total_fingerprints={total_fingerprints}, density={fingerprint_density:.3f}")

        # ================================================================
        # STEP 2: Call LLM handler with pre-calculated statistics
        # 步骤2：使用预计算统计数据调用LLM处理器
        # ================================================================
        logger.info("Calling Step5_1Handler for LLM-based fingerprint detection")
        result = await handler.analyze(
            document_text=document_text,
            locked_terms=request.locked_terms or [],
            session_id=request.session_id,
            step_name="step5-1",
            use_cache=True,
            parsed_statistics=parsed_statistics_str,
            fingerprint_density=f"{fingerprint_density:.3f}"
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # ================================================================
        # STEP 3: Return PRE-CALCULATED statistics (not LLM's)
        # 步骤3：返回预计算的统计数据（不是LLM的）
        # ================================================================
        # Calculate risk based on pre-calculated metrics
        risk_score = 0
        if fingerprint_density > 3.0:
            risk_score += 50
        elif fingerprint_density > 2.0:
            risk_score += 35
        elif fingerprint_density > 1.0:
            risk_score += 20
        if len(type_a_matches) > 3:
            risk_score += 20
        risk_score = max(risk_score, result.get("risk_score", 0))
        risk_score = min(risk_score, 100)
        risk_level = "high" if risk_score >= 60 else "medium" if risk_score >= 30 else "low"

        return FingerprintDetectionResponse(
            risk_score=risk_score,
            risk_level=RiskLevel(risk_level),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            type_a_words=type_a_matches,  # Pre-calculated
            type_b_words=type_b_matches,  # Pre-calculated
            type_c_phrases=type_c_matches,  # Pre-calculated
            total_fingerprints=total_fingerprints,  # Pre-calculated
            fingerprint_density=round(fingerprint_density, 3),  # Pre-calculated
            ppl_score=result.get("ppl_score"),
            ppl_risk_level=result.get("ppl_risk_level"),
            ppl_used_onnx=result.get("ppl_used_onnx", False),
            ppl_analysis=result.get("ppl_analysis", {})
        )

    except Exception as e:
        logger.error(f"Fingerprint detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggest")
async def get_fingerprint_suggestions(request: SubstepBaseRequest):
    """Get AI suggestions for fingerprint removal"""
    return await detect_fingerprints(request)


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_prompt(request: MergeModifyRequest):
    """Generate modification prompt for fingerprint issues"""
    try:
        prompt = await handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的指纹词问题生成的修改提示词",
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
    """Apply AI modification for fingerprint issues"""
    try:
        # Use document_service to get working text
        # 使用 document_service 获取工作文本
        document_text, locked_terms = await get_working_text(
            db=db,
            session_id=request.session_id,
            current_step="step5-1",
            document_id=request.document_id
        )

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found")

        # Convert Pydantic models to dicts
        issues_list = [issue.model_dump() for issue in request.selected_issues]

        result = await handler.apply_rewrite(
            document_text=document_text,
            selected_issues=issues_list,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )

        # Save modified text to database
        # 保存修改后的文本到数据库
        if request.session_id and result.get("modified_text"):
            await save_modified_text(
                db=db,
                session_id=request.session_id,
                step_name="step5-1",
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
