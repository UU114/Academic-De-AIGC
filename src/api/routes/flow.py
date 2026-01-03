"""
Three-Level Flow API Routes
三层级流程 API 路由

Phase 5: Full flow integration endpoints
第5阶段：全流程整合端点
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import logging

from src.db.database import get_db
from src.db.models import Document, Session
from src.core.coordinator import (
    flow_coordinator,
    FlowContext,
    LevelResult,
    ProcessingLevel,
    ProcessingMode,
    StepStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory flow context storage (would use Redis in production)
# 内存流程上下文存储（生产环境使用Redis）
_flow_contexts: Dict[str, FlowContext] = {}


# ============================================================================
# Request/Response Models
# 请求/响应模型
# ============================================================================


class FlowStartRequest(BaseModel):
    """Request to start a new processing flow 开始新处理流程的请求"""
    document_id: str = Field(..., description="Document ID to process")
    mode: str = Field("deep", description="Processing mode: quick or deep")
    colloquialism_level: int = Field(4, ge=1, le=5, description="Target tone level 1-5")
    whitelist: List[str] = Field(default_factory=list, description="Terms to whitelist")


class FlowStartResponse(BaseModel):
    """Response for flow start 流程启动响应"""
    flow_id: str
    session_id: str
    mode: str
    current_level: str
    levels: List[Dict]


class LevelCompleteRequest(BaseModel):
    """Request to complete a level 完成层级的请求"""
    flow_id: str = Field(..., description="Flow ID")
    level: str = Field(..., description="Level that was completed")
    score_before: int = Field(0, description="Score before processing")
    score_after: int = Field(0, description="Score after processing")
    issues_found: int = Field(0, description="Number of issues found")
    issues_fixed: int = Field(0, description="Number of issues fixed")
    changes: List[Dict] = Field(default_factory=list, description="Changes made")
    updated_text: Optional[str] = Field(None, description="Updated document text")


class FlowProgressResponse(BaseModel):
    """Response for flow progress 流程进度响应"""
    flow_id: str
    mode: str
    current_level: str
    overall_status: str
    levels: List[Dict]
    summary: Dict


class LevelContextResponse(BaseModel):
    """Response containing context for a level 包含层级上下文的响应"""
    flow_id: str
    level: str
    context: Dict


# ============================================================================
# API Endpoints
# API 端点
# ============================================================================


@router.post("/start", response_model=FlowStartResponse)
async def start_flow(
    request: FlowStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new three-level processing flow
    开始新的三层级处理流程

    Args:
        request: Flow start request 流程启动请求
        db: Database session 数据库会话

    Returns:
        FlowStartResponse with flow details 包含流程详情的响应
    """
    try:
        # Get document
        # 获取文档
        document = await db.get(Document, request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Determine processing mode
        # 确定处理模式
        mode = ProcessingMode.DEEP if request.mode == "deep" else ProcessingMode.QUICK

        # Create a session for this flow
        # 为此流程创建会话
        session = Session(
            document_id=request.document_id,
            mode="intervention",
            colloquialism_level=request.colloquialism_level,
            target_lang="en",
        )
        db.add(session)
        await db.flush()

        # Create flow context
        # 创建流程上下文
        context = flow_coordinator.create_context(
            document_id=request.document_id,
            session_id=str(session.id),
            text=document.content,
            mode=mode,
            whitelist=request.whitelist,
            colloquialism_level=request.colloquialism_level
        )

        # Store context with session ID as flow ID
        # 使用会话ID作为流程ID存储上下文
        flow_id = str(session.id)
        _flow_contexts[flow_id] = context

        # Get initial progress
        # 获取初始进度
        progress = flow_coordinator.get_flow_progress(context)

        return FlowStartResponse(
            flow_id=flow_id,
            session_id=str(session.id),
            mode=mode.value,
            current_level=context.current_level.value,
            levels=progress["levels"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{flow_id}/progress", response_model=FlowProgressResponse)
async def get_flow_progress(flow_id: str):
    """
    Get current flow progress
    获取当前流程进度

    Args:
        flow_id: Flow identifier 流程标识

    Returns:
        FlowProgressResponse with progress details 包含进度详情的响应
    """
    context = _flow_contexts.get(flow_id)
    if not context:
        raise HTTPException(status_code=404, detail="Flow not found")

    progress = flow_coordinator.get_flow_progress(context)

    return FlowProgressResponse(
        flow_id=flow_id,
        mode=progress["mode"],
        current_level=progress["current_level"],
        overall_status=progress["overall_status"],
        levels=progress["levels"],
        summary=progress["summary"]
    )


@router.post("/{flow_id}/complete-level")
async def complete_level(flow_id: str, request: LevelCompleteRequest):
    """
    Mark a level as complete and advance to next
    标记层级为完成并进入下一层级

    Args:
        flow_id: Flow identifier 流程标识
        request: Level completion request 层级完成请求

    Returns:
        Updated flow progress 更新后的流程进度
    """
    context = _flow_contexts.get(flow_id)
    if not context:
        raise HTTPException(status_code=404, detail="Flow not found")

    try:
        # Parse level
        # 解析层级
        level = ProcessingLevel(request.level)

        # Verify it's the current level
        # 验证是否是当前层级
        if context.current_level != level:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot complete {level.value}, current level is {context.current_level.value}"
            )

        # Create result
        # 创建结果
        result = LevelResult(
            level=level,
            status=StepStatus.COMPLETED,
            score_before=request.score_before,
            score_after=request.score_after,
            issues_found=request.issues_found,
            issues_fixed=request.issues_fixed,
            changes=request.changes,
            message=f"Level {level.value} completed",
            message_zh=f"层级 {level.value} 已完成"
        )

        # Update text if provided
        # 如果提供则更新文本
        if request.updated_text:
            context.update_text(request.updated_text)

        # Advance to next level
        # 进入下一层级
        next_level = flow_coordinator.advance_level(context, result)

        # Get updated progress
        # 获取更新后的进度
        progress = flow_coordinator.get_flow_progress(context)

        return {
            "flow_id": flow_id,
            "completed_level": level.value,
            "next_level": next_level.value if next_level else None,
            "progress": progress
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid level: {request.level}")
    except Exception as e:
        logger.error(f"Failed to complete level: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{flow_id}/skip-level")
async def skip_level(flow_id: str, level: str):
    """
    Skip a level and move to next
    跳过层级并进入下一层级

    Args:
        flow_id: Flow identifier 流程标识
        level: Level to skip 要跳过的层级

    Returns:
        Updated flow progress 更新后的流程进度
    """
    context = _flow_contexts.get(flow_id)
    if not context:
        raise HTTPException(status_code=404, detail="Flow not found")

    try:
        # Parse level
        # 解析层级
        proc_level = ProcessingLevel(level)

        # Create skip result
        # 创建跳过结果
        result = LevelResult(
            level=proc_level,
            status=StepStatus.SKIPPED,
            score_before=0,
            score_after=0,
            issues_found=0,
            issues_fixed=0,
            message=f"Level {proc_level.value} skipped by user",
            message_zh=f"用户跳过层级 {proc_level.value}"
        )

        # Advance
        # 前进
        next_level = flow_coordinator.advance_level(context, result)

        # Get progress
        # 获取进度
        progress = flow_coordinator.get_flow_progress(context)

        return {
            "flow_id": flow_id,
            "skipped_level": level,
            "next_level": next_level.value if next_level else None,
            "progress": progress
        }

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid level: {level}")
    except Exception as e:
        logger.error(f"Failed to skip level: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{flow_id}/context/{level}", response_model=LevelContextResponse)
async def get_level_context(flow_id: str, level: str):
    """
    Get context for a specific level
    获取特定层级的上下文

    Args:
        flow_id: Flow identifier 流程标识
        level: Level to get context for 要获取上下文的层级

    Returns:
        LevelContextResponse with context data 包含上下文数据的响应
    """
    context = _flow_contexts.get(flow_id)
    if not context:
        raise HTTPException(status_code=404, detail="Flow not found")

    try:
        proc_level = ProcessingLevel(level)

        if proc_level == ProcessingLevel.LEVEL_2:
            level_context = flow_coordinator.get_level_context_for_l2(context)
        elif proc_level == ProcessingLevel.LEVEL_3:
            level_context = flow_coordinator.get_level_context_for_l3(context)
        else:
            level_context = {
                "current_text": context.current_text,
                "paragraphs": context.get_current_paragraphs(),
            }

        return LevelContextResponse(
            flow_id=flow_id,
            level=level,
            context=level_context
        )

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid level: {level}")


@router.post("/{flow_id}/update-context")
async def update_context(
    flow_id: str,
    updates: Dict
):
    """
    Update flow context with level-specific data
    使用层级特定数据更新流程上下文

    Args:
        flow_id: Flow identifier 流程标识
        updates: Context updates 上下文更新

    Returns:
        Confirmation 确认
    """
    context = _flow_contexts.get(flow_id)
    if not context:
        raise HTTPException(status_code=404, detail="Flow not found")

    try:
        # Update L1 context
        # 更新L1上下文
        if "core_thesis" in updates:
            context.core_thesis = updates["core_thesis"]
        if "key_arguments" in updates:
            context.key_arguments = updates["key_arguments"]
        if "structure_issues" in updates:
            context.structure_issues = updates["structure_issues"]
        if "new_paragraph_order" in updates:
            context.new_paragraph_order = updates["new_paragraph_order"]

        # Update L2 context
        # 更新L2上下文
        if "paragraph_pairs" in updates:
            context.paragraph_pairs = updates["paragraph_pairs"]
        if "transition_repairs" in updates:
            context.transition_repairs = updates["transition_repairs"]

        # Update text
        # 更新文本
        if "current_text" in updates:
            context.update_text(updates["current_text"])

        return {
            "flow_id": flow_id,
            "status": "updated",
            "updated_fields": list(updates.keys())
        }

    except Exception as e:
        logger.error(f"Failed to update context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{flow_id}/current-text")
async def get_current_text(flow_id: str):
    """
    Get the current document text
    获取当前文档文本

    Args:
        flow_id: Flow identifier 流程标识

    Returns:
        Current text 当前文本
    """
    context = _flow_contexts.get(flow_id)
    if not context:
        raise HTTPException(status_code=404, detail="Flow not found")

    return {
        "flow_id": flow_id,
        "current_level": context.current_level.value,
        "text": context.current_text,
        "paragraph_count": len(context.get_current_paragraphs()),
    }


@router.delete("/{flow_id}")
async def cancel_flow(flow_id: str):
    """
    Cancel and cleanup a flow
    取消并清理流程

    Args:
        flow_id: Flow identifier 流程标识

    Returns:
        Confirmation 确认
    """
    if flow_id in _flow_contexts:
        del _flow_contexts[flow_id]
        return {"status": "cancelled", "flow_id": flow_id}

    raise HTTPException(status_code=404, detail="Flow not found")
