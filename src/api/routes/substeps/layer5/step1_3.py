"""
Step 1.3: Progression Pattern & Closure (推进模式与闭合)
Layer 5 Document Level

Uses LLM to detect and fix progression and closure issues
使用LLM检测和修复推进和闭合问题
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import time

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    LogicPatternResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer5.step1_3_handler import Step1_3Handler
from src.db.database import get_db
from src.db.models import Document, Session as SessionModel
from src.services.document_service import get_working_text, save_modified_text

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize handler
handler = Step1_3Handler()


@router.post("/analyze", response_model=LogicPatternResponse)
async def analyze_logic_pattern(request: SubstepBaseRequest):
    """
    Step 1.3: Analyze progression and closure patterns using LLM
    步骤 1.3：使用LLM分析推进和闭合模式

    Detects:
    - Monotonic progression (单调推进)
    - Too-strong closure (过度闭合)
    - Missing qualification (缺少条件限定)
    """
    start_time = time.time()

    try:
        # Call LLM analysis via handler
        # 通过handler调用LLM分析
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or [],
            parsed_statistics=""  # Can be enhanced to include pre-calculated stats
        )

        # Extract issues
        # 提取问题列表
        issues = result.get("issues", [])

        # Extract progression markers from LLM result
        # 从LLM结果中提取推进标记
        raw_markers = result.get("progression_markers", [])
        progression_markers = []

        for marker in raw_markers:
            progression_markers.append({
                "marker": marker.get("marker", ""),
                "category": marker.get("category", "unknown"),
                "paragraphIndex": marker.get("paragraph_index", 0),
                "isMonotonic": marker.get("is_monotonic", True),
                "context": marker.get("context", "")
            })

        # Get progression type and score directly from LLM result
        # 直接从LLM结果获取推进类型和分数
        progression_type = result.get("progression_type", "unknown")
        progression_score = result.get("progression_score", 50)
        closure_type = result.get("closure_type", "moderate")
        closure_score = result.get("closure_score", 0)

        # Fallback: Calculate from markers if LLM didn't provide scores
        # 后备：如果LLM没有提供分数，从标记计算
        if progression_markers and progression_score == 50:
            monotonic_count = sum(1 for m in progression_markers if m.get("isMonotonic", True))
            non_monotonic_count = len(progression_markers) - monotonic_count

            if len(progression_markers) > 0:
                monotonic_ratio = monotonic_count / len(progression_markers)
                # Score based on ratio: more monotonic = higher score = more AI-like
                progression_score = int(monotonic_ratio * 100)

                if monotonic_ratio > 0.7:
                    progression_type = "monotonic"
                elif monotonic_ratio < 0.3:
                    progression_type = "non_monotonic"
                else:
                    progression_type = "mixed"

        # Count monotonic vs non-monotonic markers
        # 统计单调和非单调标记数量
        sequential_markers_count = sum(1 for m in progression_markers if m.get("isMonotonic", True))

        # Calculate processing time
        # 计算处理时间
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build response
        # 构建响应
        return LogicPatternResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            # Step 1.3 specific fields / 步骤1.3特定字段
            progression_score=progression_score,
            progression_type=progression_type,
            closure_score=closure_score,
            closure_type=closure_type,
            sequential_markers_count=sequential_markers_count,
            progression_markers=progression_markers
        )

    except Exception as e:
        logger.error(f"Logic pattern analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_rewrite_prompt(request: MergeModifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a modification prompt for selected progression/closure issues
    为选定的推进/闭合问题生成修改提示词
    """
    try:
        # Convert SelectedIssue to dict format
        # 转换 SelectedIssue 为字典格式
        selected_issues_dict = [
            {
                "type": issue.type,
                "description": issue.description,
                "description_zh": issue.description_zh,
                "severity": issue.severity,
                "affected_positions": issue.affected_positions
            }
            for issue in request.selected_issues
        ]

        # Get working text (uses previous step's modified text if available)
        # 获取工作文本（如果有前一步骤的修改结果则使用）
        document_text, locked_terms = await get_working_text(
            db=db,
            session_id=request.session_id,
            current_step="step1-3",
            document_id=request.document_id
        )

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found in session or database")

        # Generate prompt via handler
        result = await handler.generate_rewrite_prompt(
            document_text=document_text,
            selected_issues=selected_issues_dict,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )

        return MergeModifyPromptResponse(
            prompt=result["prompt"],
            prompt_zh=result.get("prompt_zh", ""),
            issues_summary_zh=result.get("issues_summary_zh", ""),
            estimated_changes=result.get("estimated_changes", len(request.selected_issues))
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate prompt failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate prompt: {str(e)}")


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_rewrite(request: MergeModifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Apply AI modification directly for selected progression/closure issues
    为选定的推进/闭合问题直接应用AI修改
    """
    try:
        # Convert SelectedIssue to dict format
        # 转换 SelectedIssue 为字典格式
        selected_issues_dict = [
            {
                "type": issue.type,
                "description": issue.description,
                "description_zh": issue.description_zh,
                "severity": issue.severity,
                "affected_positions": issue.affected_positions
            }
            for issue in request.selected_issues
        ]

        # Get working text (uses previous step's modified text if available)
        # 获取工作文本（如果有前一步骤的修改结果则使用）
        document_text, locked_terms = await get_working_text(
            db=db,
            session_id=request.session_id,
            current_step="step1-3",
            document_id=request.document_id
        )

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found in session or database")

        # Apply rewrite via handler
        result = await handler.apply_rewrite(
            document_text=document_text,
            selected_issues=selected_issues_dict,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )

        # Save modified text for next step to use
        # 保存修改后的文本供下一步骤使用
        if request.session_id and result.get("modified_text"):
            await save_modified_text(
                db=db,
                session_id=request.session_id,
                step_name="step1-3",
                modified_text=result["modified_text"]
            )

        # Extract issues addressed
        # 提取已处理的问题
        issues_addressed = [issue.type for issue in request.selected_issues]

        return MergeModifyApplyResponse(
            modified_text=result["modified_text"],
            changes_summary_zh=result.get("changes_summary_zh", ""),
            changes_count=result.get("changes_count", 0),
            issues_addressed=issues_addressed
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apply rewrite failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to apply modification: {str(e)}")


@router.post("/process")
async def process_logic_pattern(request: SubstepBaseRequest):
    """
    Legacy endpoint - redirects to analyze
    """
    return await analyze_logic_pattern(request)
