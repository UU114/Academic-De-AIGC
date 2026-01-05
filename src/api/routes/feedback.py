"""
Feedback API Routes for AcademicGuard
AcademicGuard 反馈API路由

This module provides feedback submission and management endpoints.
此模块提供反馈提交和管理端点。
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from src.db.database import get_db
from src.db.models import Feedback

router = APIRouter()


# ==========================================
# Request/Response Models
# 请求/响应模型
# ==========================================

class FeedbackSubmitRequest(BaseModel):
    """
    Request to submit feedback
    提交反馈请求
    """
    contact: Optional[str] = Field(
        None,
        max_length=200,
        description="Contact info (email/phone/wechat) 联系方式"
    )
    content: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Feedback content (5-2000 chars) 反馈内容"
    )


class FeedbackSubmitResponse(BaseModel):
    """
    Response for feedback submission
    反馈提交响应
    """
    success: bool
    message: str
    message_zh: str
    feedback_id: Optional[str] = None


class FeedbackItem(BaseModel):
    """
    Feedback item for listing (admin use)
    反馈项（管理员使用）
    """
    id: str
    contact: Optional[str]
    content: str
    status: str
    created_at: datetime
    ip_address: Optional[str]


class FeedbackListResponse(BaseModel):
    """
    Response for feedback list
    反馈列表响应
    """
    success: bool
    feedbacks: List[FeedbackItem]
    total: int


# ==========================================
# API Endpoints
# API端点
# ==========================================

@router.post("/submit", response_model=FeedbackSubmitResponse)
async def submit_feedback(
    request: Request,
    data: FeedbackSubmitRequest
):
    """
    Submit user feedback or issue report.
    提交用户反馈或问题报告。

    This endpoint allows users to submit feedback without authentication.
    此端点允许用户在未登录状态下提交反馈。
    """
    # Get client info for spam prevention
    # 获取客户端信息用于防垃圾
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:500]

    # Basic content validation
    # 基本内容验证
    content = data.content.strip()
    if len(content) < 5:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Feedback content too short",
                "message_zh": "反馈内容太短"
            }
        )

    # Create feedback record
    # 创建反馈记录
    async for db in get_db():
        try:
            feedback = Feedback(
                contact=data.contact.strip() if data.contact else None,
                content=content,
                ip_address=client_ip,
                user_agent=user_agent,
                status="pending"
            )
            db.add(feedback)
            await db.commit()
            await db.refresh(feedback)

            return FeedbackSubmitResponse(
                success=True,
                message="Feedback submitted successfully. Thank you!",
                message_zh="反馈提交成功，感谢您的反馈！",
                feedback_id=feedback.id
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Failed to submit feedback: {str(e)}",
                    "message_zh": f"反馈提交失败: {str(e)}"
                }
            )


@router.get("/list", response_model=FeedbackListResponse)
async def list_feedbacks(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List all feedbacks (admin endpoint).
    列出所有反馈（管理员端点）。

    TODO: Add admin authentication check.
    TODO: 添加管理员认证检查。
    """
    async for db in get_db():
        try:
            # Build query
            # 构建查询
            query = select(Feedback).order_by(Feedback.created_at.desc())

            if status:
                query = query.where(Feedback.status == status)

            query = query.limit(limit).offset(offset)

            # Execute query
            # 执行查询
            result = await db.execute(query)
            feedbacks = result.scalars().all()

            # Get total count
            # 获取总数
            count_query = select(Feedback)
            if status:
                count_query = count_query.where(Feedback.status == status)
            count_result = await db.execute(count_query)
            total = len(count_result.scalars().all())

            return FeedbackListResponse(
                success=True,
                feedbacks=[
                    FeedbackItem(
                        id=f.id,
                        contact=f.contact,
                        content=f.content,
                        status=f.status,
                        created_at=f.created_at,
                        ip_address=f.ip_address
                    )
                    for f in feedbacks
                ],
                total=total
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Failed to list feedbacks: {str(e)}",
                    "message_zh": f"获取反馈列表失败: {str(e)}"
                }
            )


@router.patch("/{feedback_id}/status")
async def update_feedback_status(
    feedback_id: str,
    status: str
):
    """
    Update feedback status (admin endpoint).
    更新反馈状态（管理员端点）。

    Valid statuses: pending, reviewed, resolved, spam
    有效状态: pending, reviewed, resolved, spam
    """
    valid_statuses = ["pending", "reviewed", "resolved", "spam"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Invalid status. Must be one of: {valid_statuses}",
                "message_zh": f"无效状态。必须是: {valid_statuses}"
            }
        )

    async for db in get_db():
        try:
            result = await db.execute(
                select(Feedback).where(Feedback.id == feedback_id)
            )
            feedback = result.scalar_one_or_none()

            if not feedback:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": "Feedback not found",
                        "message_zh": "反馈不存在"
                    }
                )

            feedback.status = status
            if status in ["reviewed", "resolved"]:
                feedback.reviewed_at = datetime.utcnow()

            await db.commit()

            return {
                "success": True,
                "message": "Status updated",
                "message_zh": "状态已更新"
            }
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Failed to update status: {str(e)}",
                    "message_zh": f"更新状态失败: {str(e)}"
                }
            )
