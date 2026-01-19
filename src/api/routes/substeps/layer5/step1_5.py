"""
Step 1.5: Content Substantiality Analysis (内容实质性分析)
Layer 5 Document Level

Uses LLM to detect and fix content substantiality issues:
- Generic phrases detection (泛化短语检测)
- Filler words detection (填充词检测)
- Content specificity analysis (内容具体性分析)
- Hallucination risk assessment (幻觉风险评估)

使用LLM检测和修复内容实质性问题：
- 泛化短语检测
- 填充词检测
- 内容具体性分析
- 幻觉风险评估
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import time

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    ConnectorTransitionResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer5.step1_5_handler import Step1_5Handler
from src.db.database import get_db
from src.db.models import Document, Session as SessionModel
from src.services.document_service import get_working_text, save_modified_text

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize handler
handler = Step1_5Handler()


@router.post("/analyze", response_model=ConnectorTransitionResponse)
async def analyze_transitions(request: SubstepBaseRequest):
    """
    Step 1.5: Analyze transitions and connectors using LLM
    步骤 1.5：使用LLM分析过渡和连接词

    Detects:
    - Explicit connectors at paragraph openings
    - Formulaic topic sentences
    - Too-smooth transitions
    - Summary endings
    """
    start_time = time.time()

    try:
        # Call LLM analysis via handler
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        # Extract issues
        issues = result.get("issues", [])

        # Extract connector density from result
        connector_density_str = result.get("connector_density", "0 per 100 words")
        try:
            connector_density = float(connector_density_str.split()[0]) if connector_density_str else 0
        except:
            connector_density = 0

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build response
        return ConnectorTransitionResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            # Step 1.5 specific fields
            total_transitions=len([issue for issue in issues if "transition" in issue.get("type", "")]),
            problematic_transitions=len(issues),
            connector_density=connector_density,
            explicit_connectors=[issue.get("connector_word", "") for issue in issues if issue.get("connector_word")],
            transitions=[]
        )

    except Exception as e:
        logger.error(f"Transition analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_rewrite_prompt(request: MergeModifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a modification prompt for selected transition/connector issues
    为选定的过渡/连接词问题生成修改提示词
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
            current_step="step1-5",
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
    Apply AI modification directly for selected transition/connector issues
    为选定的过渡/连接词问题直接应用AI修改
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
            current_step="step1-5",
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
                step_name="step1-5",
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
async def process_transitions(request: SubstepBaseRequest):
    """
    Legacy endpoint - redirects to analyze
    """
    return await analyze_transitions(request)


@router.post("/ai-suggest")
async def get_transition_suggestions(request: SubstepBaseRequest):
    """
    Legacy endpoint for AI suggestions - redirects to analyze
    """
    return await analyze_transitions(request)
