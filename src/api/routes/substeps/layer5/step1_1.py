"""
Step 1.1: Structure Framework Detection (结构框架检测)
Layer 5 Document Level

Detects document structure for AI-like patterns:
- Section symmetry
- Predictable order
- Linear flow
检测文档结构中的AI模式特征
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import time

from src.db.database import get_db
from src.db.models import Session, Document
from src.services.document_service import get_working_text, save_modified_text
from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    StructureAnalysisResponse,
    RiskLevel,
    # Reuse merge-modify schemas from old code
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer5.step1_1_handler import Step1_1Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize handler
handler = Step1_1Handler()


@router.post("/analyze", response_model=StructureAnalysisResponse)
async def analyze_structure(request: SubstepBaseRequest):
    """
    Step 1.1: Analyze document structure for AI-like patterns using LLM
    步骤 1.1：使用LLM分析文档结构中的AI特征

    Detects:
    - Linear flow (First-Second-Third enumeration)
    - Repetitive pattern (copy-paste section structure)
    - Uniform length (CV < 0.30)
    - Predictable order (formulaic academic structure)
    - Symmetry (all sections have equal paragraphs)
    """
    start_time = time.time()

    try:
        # Call LLM analysis via handler
        result = await handler.analyze(
            document_text=request.text,
            locked_terms=request.locked_terms or []
        )

        # Extract issues from result
        issues = result.get("issues", [])

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build response
        return StructureAnalysisResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            # Step 1.1 specific fields
            symmetry_score=_extract_score_from_issues(issues, "symmetry"),
            predictability_score=_extract_score_from_issues(issues, "predictable_order"),
            linear_flow_score=_extract_score_from_issues(issues, "linear_flow"),
            progression_type=_infer_progression_type(issues),
            sections=[]  # LLM doesn't return detailed sections in analysis
        )

    except Exception as e:
        logger.error(f"Structure analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_rewrite_prompt(
    request: MergeModifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a modification prompt for selected structure issues
    为选定的结构问题生成修改提示词

    User can copy this prompt to use with other AI tools.
    用户可以复制此提示词用于其他AI工具。

    Args:
        request: Merge modify request with selected issues and user notes

    Returns:
        Prompt for user to copy
    """
    try:
        # Convert SelectedIssue to dict format
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
            current_step="step1-1",
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
            prompt_zh=result["prompt_zh"],
            issues_summary_zh=result["issues_summary_zh"],
            colloquialism_level=None,  # Not applicable for structure
            estimated_changes=result["estimated_changes"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate prompt failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generate prompt failed: {str(e)}")


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_rewrite(
    request: MergeModifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply AI modification to document structure directly
    直接应用AI修改到文档结构

    Args:
        request: Merge modify request with selected issues and user notes

    Returns:
        Modified document with changes summary
    """
    try:
        # Convert SelectedIssue to dict format
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
            current_step="step1-1",
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
                step_name="step1-1",
                modified_text=result["modified_text"]
            )

        # Extract issues addressed
        issues_addressed = [issue.type for issue in request.selected_issues]

        return MergeModifyApplyResponse(
            modified_text=result["modified_text"],
            changes_summary_zh=result["changes_summary_zh"],
            changes_count=result["changes_count"],
            issues_addressed=issues_addressed,
            remaining_attempts=3,
            colloquialism_level=None  # Not applicable for structure
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apply rewrite failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Apply rewrite failed: {str(e)}")


# =============================================================================
# Helper Functions
# 辅助函数
# =============================================================================

def _extract_score_from_issues(issues: List[Dict[str, Any]], issue_type: str) -> int:
    """
    Extract score for a specific issue type from issues list
    从问题列表中提取特定类型问题的分数
    """
    for issue in issues:
        if issue.get("type") == issue_type:
            severity = issue.get("severity", "medium")
            if severity == "high":
                return 80
            elif severity == "medium":
                return 60
            else:
                return 40
    return 0


def _infer_progression_type(issues: List[Dict[str, Any]]) -> str:
    """
    Infer progression type from issues
    从问题中推断推进类型
    """
    for issue in issues:
        if issue.get("type") == "linear_flow":
            return "monotonic"
        elif issue.get("type") == "predictable_order":
            return "formulaic"
    return "natural"
