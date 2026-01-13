"""
Step 1.4: Anchor Density (锚点密度)
Layer 5 Document Level

Uses LLM to detect and fix low anchor density issues
使用LLM检测和修复低锚点密度问题
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import time

from src.api.routes.substeps.schemas import (
    SubstepBaseRequest,
    AnchorDensityResponse,
    RiskLevel,
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.api.routes.substeps.layer5.step1_4_handler import Step1_4Handler
from src.db.database import get_db
from src.db.models import Document, Session as SessionModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize handler
handler = Step1_4Handler()


@router.post("/analyze", response_model=AnchorDensityResponse)
async def analyze_anchor_density(request: SubstepBaseRequest):
    """
    Step 1.4: Analyze anchor density using LLM
    步骤 1.4：使用LLM分析锚点密度

    Detects:
    - Low anchor density (< 5.0 per 100 words)
    - Missing anchor types (statistics, citations, measurements)
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

        # Extract overall density from result
        overall_density = result.get("overall_density", 0)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build response
        return AnchorDensityResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms,
            # Step 1.4 specific fields
            overall_density=overall_density,
            target_density=5.0,
            low_density_paragraphs=[],
            anchor_types_count={}
        )

    except Exception as e:
        logger.error(f"Anchor density analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_rewrite_prompt(request: MergeModifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a modification prompt for selected anchor density issues
    为选定的锚点密度问题生成修改提示词
    """
    try:
        # Get document from database
        result = await db.execute(select(Document).where(Document.id == request.document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get session for locked terms
        session_result = await db.execute(select(SessionModel).where(SessionModel.id == request.session_id))
        session = session_result.scalar_one_or_none() if request.session_id else None
        locked_terms = session.locked_terms if session and session.locked_terms else []

        # Generate prompt via handler
        result = await handler.generate_rewrite_prompt(
            document_text=doc.processed_text or doc.original_text,
            selected_issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )

        return MergeModifyPromptResponse(
            prompt=result["prompt"],
            prompt_zh=result.get("prompt_zh", ""),
            issues_summary_zh=result.get("issues_summary_zh", ""),
            estimated_changes=result.get("estimated_changes", len(request.selected_issues))
        )

    except Exception as e:
        logger.error(f"Generate prompt failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate prompt: {str(e)}")


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_rewrite(request: MergeModifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Apply AI modification directly for selected anchor density issues
    为选定的锚点密度问题直接应用AI修改
    """
    try:
        # Get document from database
        result = await db.execute(select(Document).where(Document.id == request.document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get session for locked terms
        session_result = await db.execute(select(SessionModel).where(SessionModel.id == request.session_id))
        session = session_result.scalar_one_or_none() if request.session_id else None
        locked_terms = session.locked_terms if session and session.locked_terms else []

        # Apply rewrite via handler
        result = await handler.apply_rewrite(
            document_text=doc.processed_text or doc.original_text,
            selected_issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )

        return MergeModifyApplyResponse(
            modified_text=result["modified_text"],
            changes_summary_zh=result.get("changes_summary_zh", ""),
            changes_count=result.get("changes_count", 0),
            issues_addressed=result.get("issues_addressed", [])
        )

    except Exception as e:
        logger.error(f"Apply rewrite failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply modification: {str(e)}")


@router.post("/process")
async def process_anchor_density(request: SubstepBaseRequest):
    """
    Legacy endpoint - redirects to analyze
    """
    return await analyze_anchor_density(request)
