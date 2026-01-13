"""
Substep State API Routes
子步骤状态API路由

Provides endpoints for saving and loading substep analysis results and user inputs.
This enables caching to avoid redundant LLM calls when navigating between steps.
提供保存和加载子步骤分析结果及用户输入的端点。
这使得在步骤间导航时可以缓存数据，避免重复调用LLM。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.db.database import get_db
from src.db.models import SubstepState, Session

router = APIRouter()


# ==========================================
# Request/Response Models
# 请求/响应模型
# ==========================================

class SaveSubstepStateRequest(BaseModel):
    """
    Request to save substep state
    保存子步骤状态的请求
    """
    session_id: str = Field(..., description="Session ID / 会话ID")
    step_name: str = Field(..., description="Step name, e.g., 'layer5-step1-1' / 步骤名称")
    analysis_result: Optional[Dict[str, Any]] = Field(None, description="LLM analysis result / LLM分析结果")
    user_inputs: Optional[Dict[str, Any]] = Field(None, description="User inputs/selections / 用户输入/选择")
    modified_text: Optional[str] = Field(None, description="Modified text if any / 修改后的文本")
    status: str = Field("pending", description="Step status: pending/completed/skipped / 步骤状态")


class SubstepStateResponse(BaseModel):
    """
    Response containing substep state
    包含子步骤状态的响应
    """
    id: str
    session_id: str
    step_name: str
    analysis_result: Optional[Dict[str, Any]] = None
    user_inputs: Optional[Dict[str, Any]] = None
    modified_text: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BatchSubstepStatesResponse(BaseModel):
    """
    Response containing multiple substep states
    包含多个子步骤状态的响应
    """
    session_id: str
    states: Dict[str, SubstepStateResponse]  # key is step_name
    total_count: int


# ==========================================
# API Endpoints
# API端点
# ==========================================

@router.post("/save", response_model=SubstepStateResponse)
async def save_substep_state(
    request: SaveSubstepStateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Save or update substep state
    保存或更新子步骤状态

    If state exists for this session+step, update it.
    Otherwise, create a new state record.
    如果此会话+步骤的状态已存在，则更新它。
    否则，创建新的状态记录。
    """
    # Verify session exists
    # 验证会话存在
    session_result = await db.execute(
        select(Session).where(Session.id == request.session_id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found / 会话未找到")

    # Check if state already exists
    # 检查状态是否已存在
    existing_result = await db.execute(
        select(SubstepState).where(
            SubstepState.session_id == request.session_id,
            SubstepState.step_name == request.step_name
        )
    )
    existing_state = existing_result.scalar_one_or_none()

    if existing_state:
        # Update existing state
        # 更新现有状态
        if request.analysis_result is not None:
            existing_state.analysis_result = request.analysis_result
        if request.user_inputs is not None:
            existing_state.user_inputs = request.user_inputs
        if request.modified_text is not None:
            existing_state.modified_text = request.modified_text
        existing_state.status = request.status
        await db.commit()
        await db.refresh(existing_state)
        state = existing_state
    else:
        # Create new state
        # 创建新状态
        state = SubstepState(
            session_id=request.session_id,
            step_name=request.step_name,
            analysis_result=request.analysis_result,
            user_inputs=request.user_inputs,
            modified_text=request.modified_text,
            status=request.status
        )
        db.add(state)
        await db.commit()
        await db.refresh(state)

    return SubstepStateResponse(
        id=state.id,
        session_id=state.session_id,
        step_name=state.step_name,
        analysis_result=state.analysis_result,
        user_inputs=state.user_inputs,
        modified_text=state.modified_text,
        status=state.status,
        created_at=state.created_at,
        updated_at=state.updated_at
    )


@router.get("/load/{session_id}/{step_name}", response_model=SubstepStateResponse)
async def load_substep_state(
    session_id: str,
    step_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Load substep state for a specific step
    加载特定步骤的子步骤状态

    Returns cached analysis result and user inputs if available.
    如果有缓存，返回分析结果和用户输入。
    """
    result = await db.execute(
        select(SubstepState).where(
            SubstepState.session_id == session_id,
            SubstepState.step_name == step_name
        )
    )
    state = result.scalar_one_or_none()

    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"No cached state for step {step_name} / 步骤 {step_name} 无缓存状态"
        )

    return SubstepStateResponse(
        id=state.id,
        session_id=state.session_id,
        step_name=state.step_name,
        analysis_result=state.analysis_result,
        user_inputs=state.user_inputs,
        modified_text=state.modified_text,
        status=state.status,
        created_at=state.created_at,
        updated_at=state.updated_at
    )


@router.get("/load-all/{session_id}", response_model=BatchSubstepStatesResponse)
async def load_all_substep_states(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Load all substep states for a session
    加载会话的所有子步骤状态

    Returns all cached states keyed by step_name.
    返回以step_name为键的所有缓存状态。
    """
    result = await db.execute(
        select(SubstepState).where(SubstepState.session_id == session_id)
    )
    states = result.scalars().all()

    states_dict = {}
    for state in states:
        states_dict[state.step_name] = SubstepStateResponse(
            id=state.id,
            session_id=state.session_id,
            step_name=state.step_name,
            analysis_result=state.analysis_result,
            user_inputs=state.user_inputs,
            modified_text=state.modified_text,
            status=state.status,
            created_at=state.created_at,
            updated_at=state.updated_at
        )

    return BatchSubstepStatesResponse(
        session_id=session_id,
        states=states_dict,
        total_count=len(states_dict)
    )


@router.get("/check/{session_id}/{step_name}")
async def check_substep_state_exists(
    session_id: str,
    step_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if substep state exists (without loading full data)
    检查子步骤状态是否存在（不加载完整数据）

    Useful for quickly determining if cache is available.
    用于快速判断缓存是否可用。
    """
    result = await db.execute(
        select(SubstepState.id, SubstepState.status, SubstepState.updated_at).where(
            SubstepState.session_id == session_id,
            SubstepState.step_name == step_name
        )
    )
    row = result.first()

    if not row:
        return {
            "exists": False,
            "session_id": session_id,
            "step_name": step_name
        }

    return {
        "exists": True,
        "session_id": session_id,
        "step_name": step_name,
        "status": row.status,
        "updated_at": row.updated_at
    }


@router.delete("/clear/{session_id}/{step_name}")
async def clear_substep_state(
    session_id: str,
    step_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Clear substep state for a specific step
    清除特定步骤的子步骤状态

    Use this when user wants to re-analyze a step.
    当用户想要重新分析某步骤时使用。
    """
    result = await db.execute(
        select(SubstepState).where(
            SubstepState.session_id == session_id,
            SubstepState.step_name == step_name
        )
    )
    state = result.scalar_one_or_none()

    if not state:
        return {
            "success": True,
            "message": "No state to clear / 无状态可清除",
            "session_id": session_id,
            "step_name": step_name
        }

    await db.delete(state)
    await db.commit()

    return {
        "success": True,
        "message": "State cleared successfully / 状态已成功清除",
        "session_id": session_id,
        "step_name": step_name
    }


@router.delete("/clear-all/{session_id}")
async def clear_all_substep_states(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Clear all substep states for a session
    清除会话的所有子步骤状态

    Use this when user wants to start fresh.
    当用户想要重新开始时使用。
    """
    result = await db.execute(
        select(SubstepState).where(SubstepState.session_id == session_id)
    )
    states = result.scalars().all()

    count = len(states)
    for state in states:
        await db.delete(state)
    await db.commit()

    return {
        "success": True,
        "message": f"Cleared {count} states / 已清除 {count} 个状态",
        "session_id": session_id,
        "cleared_count": count
    }


@router.post("/update-user-inputs/{session_id}/{step_name}")
async def update_user_inputs(
    session_id: str,
    step_name: str,
    user_inputs: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Update only user inputs for a substep (merge with existing)
    仅更新子步骤的用户输入（与现有合并）

    This is useful for incrementally saving user selections.
    用于增量保存用户选择。
    """
    result = await db.execute(
        select(SubstepState).where(
            SubstepState.session_id == session_id,
            SubstepState.step_name == step_name
        )
    )
    state = result.scalar_one_or_none()

    if not state:
        # Create new state with just user inputs
        # 创建仅包含用户输入的新状态
        state = SubstepState(
            session_id=session_id,
            step_name=step_name,
            user_inputs=user_inputs,
            status="pending"
        )
        db.add(state)
    else:
        # Merge user inputs
        # 合并用户输入
        existing_inputs = state.user_inputs or {}
        existing_inputs.update(user_inputs)
        state.user_inputs = existing_inputs

    await db.commit()
    await db.refresh(state)

    return {
        "success": True,
        "session_id": session_id,
        "step_name": step_name,
        "user_inputs": state.user_inputs
    }
