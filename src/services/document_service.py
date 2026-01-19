"""
Document Service - Provides document text retrieval for substeps
文档服务 - 为子步骤提供文档文本获取功能

This service ensures each substep uses the correct "working text":
- If previous step has modified text, use that
- Otherwise, use original document text

此服务确保每个子步骤使用正确的"工作文本"：
- 如果前一步骤有修改后的文本，使用那个
- 否则，使用原始文档文本
"""

import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.db.models import Session, Document, SubstepState

logger = logging.getLogger(__name__)


# Step order definition (from Layer 5 to Layer 1)
# 步骤顺序定义（从 Layer 5 到 Layer 1）
STEP_ORDER = [
    # Layer 5 - Document Level
    "layer5-step1-0", "layer5-step1-1", "layer5-step1-2",
    "layer5-step1-3", "layer5-step1-4", "layer5-step1-5",
    # Layer 4 - Section Level
    "layer4-step2-0", "layer4-step2-1", "layer4-step2-2",
    "layer4-step2-3", "layer4-step2-4", "layer4-step2-5",
    # Layer 3 - Paragraph Level
    "layer3-step3-0", "layer3-step3-1", "layer3-step3-2",
    "layer3-step3-3", "layer3-step3-4", "layer3-step3-5",
    # Layer 2 - Sentence Level
    "layer2-step4-0", "layer2-step4-1", "layer2-step4-2",
    "layer2-step4-3", "layer2-step4-4", "layer2-step4-5",
    # Layer 1 - Lexical Level
    "layer1-step5-0", "layer1-step5-1", "layer1-step5-2",
    "layer1-step5-3", "layer1-step5-4", "layer1-step5-5",
]


def get_step_index(step_name: str) -> int:
    """
    Get the index of a step in the order
    获取步骤在顺序中的索引

    Args:
        step_name: Step name (e.g., "layer5-step1-1")

    Returns:
        Index in STEP_ORDER, or -1 if not found
    """
    try:
        return STEP_ORDER.index(step_name)
    except ValueError:
        return -1


def get_previous_steps(current_step: str) -> List[str]:
    """
    Get all steps before the current step (in reverse order, most recent first)
    获取当前步骤之前的所有步骤（倒序，最近的优先）

    Args:
        current_step: Current step name

    Returns:
        List of previous step names, most recent first
    """
    current_index = get_step_index(current_step)
    if current_index <= 0:
        return []
    return list(reversed(STEP_ORDER[:current_index]))


async def get_working_text(
    db: AsyncSession,
    session_id: str,
    current_step: str,
    document_id: Optional[str] = None
) -> Tuple[str, List[str]]:
    """
    Get the current working text for a substep
    获取子步骤的当前工作文本

    Logic:
    1. Find the most recent previous step that has modified_text
    2. If found, return that modified_text
    3. Otherwise, return the original document text

    逻辑：
    1. 找到最近的有 modified_text 的前一步骤
    2. 如果找到，返回那个 modified_text
    3. 否则，返回原始文档文本

    Args:
        db: Database session
        session_id: Session ID
        current_step: Current step name (e.g., "layer5-step1-1")
        document_id: Optional document ID (fallback)

    Returns:
        Tuple of (working_text, locked_terms)
    """
    locked_terms = []

    # First, get the session to find document_id and locked_terms
    # 首先，获取会话以找到 document_id 和锁定术语
    session = None
    if session_id:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            document_id = session.document_id
            if session.config_json:
                locked_terms = session.config_json.get("whitelist", [])

    if not document_id:
        logger.error(f"No document_id found for session {session_id}")
        return "", locked_terms

    # Get previous steps in reverse order
    # 获取前一步骤（倒序）
    previous_steps = get_previous_steps(current_step)

    # Look for the most recent step with modified_text
    # 查找最近的有 modified_text 的步骤
    if previous_steps and session_id:
        for prev_step in previous_steps:
            result = await db.execute(
                select(SubstepState).where(
                    and_(
                        SubstepState.session_id == session_id,
                        SubstepState.step_name == prev_step,
                        SubstepState.modified_text.isnot(None),
                        SubstepState.modified_text != ""
                    )
                )
            )
            substep_state = result.scalar_one_or_none()
            if substep_state and substep_state.modified_text:
                logger.info(f"Using modified text from {prev_step} for {current_step}")
                return substep_state.modified_text, locked_terms

    # No previous modification found, use original document
    # 没有找到前一步骤的修改，使用原始文档
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc:
        logger.info(f"Using original document text for {current_step}")
        return doc.original_text, locked_terms

    logger.error(f"Document {document_id} not found")
    return "", locked_terms


async def save_modified_text(
    db: AsyncSession,
    session_id: str,
    step_name: str,
    modified_text: str,
    analysis_result: Optional[dict] = None
) -> bool:
    """
    Save modified text to SubstepState
    保存修改后的文本到 SubstepState

    Args:
        db: Database session
        session_id: Session ID
        step_name: Step name
        modified_text: Modified text to save
        analysis_result: Optional analysis result to save

    Returns:
        True if saved successfully
    """
    try:
        # Check if state exists
        result = await db.execute(
            select(SubstepState).where(
                and_(
                    SubstepState.session_id == session_id,
                    SubstepState.step_name == step_name
                )
            )
        )
        state = result.scalar_one_or_none()

        if state:
            # Update existing state
            state.modified_text = modified_text
            state.status = "completed"
            if analysis_result:
                state.analysis_result = analysis_result
        else:
            # Create new state
            state = SubstepState(
                session_id=session_id,
                step_name=step_name,
                modified_text=modified_text,
                status="completed",
                analysis_result=analysis_result
            )
            db.add(state)

        await db.commit()
        logger.info(f"Saved modified text for {step_name} in session {session_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to save modified text: {e}")
        await db.rollback()
        return False
