"""
Task API Routes for AcademicGuard
AcademicGuard 任务API路由

This module provides task management endpoints for billing workflow.
此模块提供计费工作流的任务管理端点。
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from src.db.database import get_db
from src.db.models import Task, Document, TaskStatus, PaymentStatus
from src.config import get_settings
from src.services.task_service import TaskService
from src.middleware.auth_middleware import get_current_user, get_current_user_optional

router = APIRouter()


# ==========================================
# Request/Response Models
# 请求/响应模型
# ==========================================

class TaskCreateRequest(BaseModel):
    """Request to create a task for a document 为文档创建任务请求"""
    document_id: str = Field(..., description="Document ID")


class TaskResponse(BaseModel):
    """Task information response 任务信息响应"""
    task_id: str
    document_id: str
    user_id: Optional[str] = None

    # Word count and billing
    word_count_raw: Optional[int] = None
    word_count_billable: Optional[int] = None
    billable_units: Optional[int] = None
    price_calculated: Optional[float] = None
    price_final: Optional[float] = None
    is_minimum_charge: bool = False

    # Status
    status: str
    payment_status: str
    platform_order_id: Optional[str] = None

    # Timestamps
    created_at: datetime
    quoted_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Mode info
    is_debug_mode: bool


class TaskListResponse(BaseModel):
    """List of tasks response 任务列表响应"""
    tasks: List[TaskResponse]
    total: int


class TaskStatusUpdateRequest(BaseModel):
    """Request to update task status 更新任务状态请求"""
    status: str = Field(..., description="New status value")


# ==========================================
# API Endpoints
# API端点
# ==========================================

@router.post("/create", response_model=TaskResponse)
async def create_task(
    request: TaskCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Create a billing task for a document
    为文档创建计费任务

    This calculates word count and pricing for the document.
    此操作会计算文档的字数和定价。
    """
    settings = get_settings()
    task_service = TaskService(db)

    # Check if document exists
    # 检查文档是否存在
    result = await db.execute(
        select(Document).where(Document.id == request.document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "document_not_found",
                "message": "Document not found",
                "message_zh": "文档未找到"
            }
        )

    # Check if task already exists for this document
    # 检查此文档是否已有任务
    existing_task = await task_service.get_task_by_document(request.document_id)
    if existing_task:
        # Return existing task if not expired
        # 如果未过期则返回现有任务
        if existing_task.status != TaskStatus.EXPIRED.value:
            return _task_to_response(existing_task, settings.is_debug_mode())

    # Create new task
    # 创建新任务
    user_id = None if user.get("is_debug") else user.get("user_id")

    try:
        task = await task_service.create_task_for_document(
            document_id=request.document_id,
            user_id=user_id
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "task_creation_failed",
                "message": str(e),
                "message_zh": "创建任务失败"
            }
        )

    return _task_to_response(task, settings.is_debug_mode())


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get task information
    获取任务信息
    """
    settings = get_settings()
    task_service = TaskService(db)

    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "task_not_found",
                "message": "Task not found",
                "message_zh": "任务未找到"
            }
        )

    return _task_to_response(task, settings.is_debug_mode())


@router.get("/by-document/{document_id}", response_model=Optional[TaskResponse])
async def get_task_by_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_optional)
):
    """
    Get task for a document
    获取文档的任务
    """
    settings = get_settings()
    task_service = TaskService(db)

    task = await task_service.get_task_by_document(document_id)

    if not task:
        return None

    return _task_to_response(task, settings.is_debug_mode())


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Delete a task (only allowed for unpaid tasks)
    删除任务（仅允许删除未支付的任务）
    """
    task_service = TaskService(db)

    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "task_not_found",
                "message": "Task not found",
                "message_zh": "任务未找到"
            }
        )

    # Only allow deletion of unpaid tasks
    # 只允许删除未支付的任务
    if task.payment_status == PaymentStatus.PAID.value:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "cannot_delete_paid_task",
                "message": "Cannot delete a paid task",
                "message_zh": "无法删除已支付的任务"
            }
        )

    await db.delete(task)
    await db.commit()

    return {
        "success": True,
        "message": "Task deleted successfully",
        "message_zh": "任务删除成功"
    }


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    List tasks for current user
    列出当前用户的任务

    In debug mode, returns all tasks.
    调试模式下返回所有任务。
    """
    settings = get_settings()

    query = select(Task)

    # Filter by user in operational mode
    # 运营模式下按用户过滤
    if not user.get("is_debug"):
        query = query.where(Task.user_id == user.get("user_id"))

    # Filter by status if provided
    # 如果提供则按状态过滤
    if status:
        query = query.where(Task.status == status)

    # Order by creation time descending
    # 按创建时间降序排序
    query = query.order_by(Task.created_at.desc())

    # Get total count
    # 获取总数
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Apply pagination
    # 应用分页
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return TaskListResponse(
        tasks=[_task_to_response(t, settings.is_debug_mode()) for t in tasks],
        total=total
    )


@router.post("/{task_id}/check-can-process")
async def check_can_process(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Check if task can start processing
    检查任务是否可以开始处理

    This validates:
    - Task exists
    - Task not expired
    - Payment completed (in operational mode)
    - Task not already processing/completed
    """
    task_service = TaskService(db)

    can_start, reason = await task_service.can_start_processing(task_id)

    return {
        "can_process": can_start,
        "reason": reason
    }


# ==========================================
# Helper Functions
# 辅助函数
# ==========================================

def _task_to_response(task: Task, is_debug_mode: bool) -> TaskResponse:
    """
    Convert Task model to response
    将Task模型转换为响应
    """
    return TaskResponse(
        task_id=task.task_id,
        document_id=task.document_id,
        user_id=task.user_id,
        word_count_raw=task.word_count_raw,
        word_count_billable=task.word_count_billable,
        billable_units=task.billable_units,
        price_calculated=task.price_calculated,
        price_final=task.price_final if not is_debug_mode else 0.0,
        is_minimum_charge=task.is_minimum_charge or False,
        status=task.status,
        payment_status=task.payment_status,
        platform_order_id=task.platform_order_id,
        created_at=task.created_at,
        quoted_at=task.quoted_at,
        paid_at=task.paid_at,
        expires_at=task.expires_at,
        is_debug_mode=is_debug_mode
    )
