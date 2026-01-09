"""
Payment API Routes for AcademicGuard
AcademicGuard 支付API路由

This module provides payment-related endpoints.
此模块提供支付相关端点。

Security Features:
- HMAC-SHA256 signature verification for payment callbacks
- Replay attack prevention with timestamp validation
"""

import hmac
import hashlib
import json
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from src.db.database import get_db
from src.db.models import Task, TaskStatus, PaymentStatus
from src.config import get_settings
from src.services.payment_service import get_payment_provider, PlatformOrderStatus
from src.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ==========================================
# Request/Response Models
# 请求/响应模型
# ==========================================

class QuoteResponse(BaseModel):
    """Price quote response 报价响应"""
    task_id: str
    word_count_raw: int
    word_count_billable: int
    billable_units: int
    calculated_price: float
    final_price: float
    is_minimum_charge: bool
    currency: str = "CNY"
    minimum_charge: float
    is_debug_mode: bool
    payment_required: bool


class PaymentInitResponse(BaseModel):
    """Payment initiation response 支付发起响应"""
    task_id: str
    platform_order_id: str
    payment_url: Optional[str] = None
    qr_code_url: Optional[str] = None
    amount: float
    expires_at: Optional[str] = None
    is_debug_mode: bool
    auto_paid: bool = False


class PaymentStatusResponse(BaseModel):
    """Payment status response 支付状态响应"""
    task_id: str
    status: str
    payment_status: str
    paid_at: Optional[str] = None
    can_process: bool


class PaymentCallbackRequest(BaseModel):
    """Payment callback request from platform 平台支付回调请求"""
    order_id: str
    status: str
    paid_at: Optional[str] = None
    amount: Optional[float] = None
    timestamp: Optional[int] = None  # Unix timestamp for replay attack prevention
    nonce: Optional[str] = None  # Random string for replay attack prevention
    signature: Optional[str] = None


def verify_payment_signature(payload: PaymentCallbackRequest, secret: str) -> bool:
    """
    Verify HMAC-SHA256 signature from payment platform
    验证支付平台的 HMAC-SHA256 签名

    Signature format: HMAC-SHA256(order_id|status|amount|timestamp|nonce, secret)
    签名格式: HMAC-SHA256(order_id|status|amount|timestamp|nonce, secret)
    """
    if not secret:
        logger.error("Payment webhook secret not configured!")
        return False

    if not payload.signature:
        logger.warning("Payment callback missing signature")
        return False

    # Check timestamp to prevent replay attacks (5 minute window)
    # 检查时间戳防止重放攻击（5分钟窗口）
    if payload.timestamp:
        current_time = int(datetime.utcnow().timestamp())
        time_diff = abs(current_time - payload.timestamp)
        if time_diff > 300:  # 5 minutes
            logger.warning(f"Payment callback timestamp too old: {time_diff}s")
            return False

    # Build signature string
    # 构建签名字符串
    sign_parts = [
        payload.order_id,
        payload.status,
        str(payload.amount or ""),
        str(payload.timestamp or ""),
        payload.nonce or ""
    ]
    sign_string = "|".join(sign_parts)

    # Calculate expected signature
    # 计算预期签名
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    # 常量时间比较防止时序攻击
    return hmac.compare_digest(expected_signature, payload.signature)


# ==========================================
# API Endpoints
# API端点
# ==========================================

@router.get("/quote/{task_id}", response_model=QuoteResponse)
async def get_task_quote(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get price quote for a task
    获取任务报价

    DEBUG mode: Shows price but marks as no payment required
    调试模式：显示价格但标记为无需支付

    OPERATIONAL mode: Returns actual price requiring payment
    运营模式：返回需要支付的实际价格
    """
    settings = get_settings()

    result = await db.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "task_not_found",
                "message": "Task not found",
                "message_zh": "任务未找到"
            }
        )

    # In debug mode, price is shown but payment not required
    # 调试模式下显示价格但不需要支付
    is_debug = settings.is_debug_mode()

    return QuoteResponse(
        task_id=task.task_id,
        word_count_raw=task.word_count_raw or 0,
        word_count_billable=task.word_count_billable or 0,
        billable_units=task.billable_units or 0,
        calculated_price=task.price_calculated or 0.0,
        final_price=task.price_final or 0.0 if not is_debug else 0.0,
        is_minimum_charge=task.is_minimum_charge or False,
        minimum_charge=settings.minimum_charge,
        is_debug_mode=is_debug,
        payment_required=not is_debug
    )


@router.post("/pay/{task_id}", response_model=PaymentInitResponse)
async def initiate_payment(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Initiate payment for a task
    发起任务支付

    DEBUG mode: Auto-marks task as paid without actual payment
    调试模式：自动标记任务为已支付，无需实际支付

    OPERATIONAL mode: Creates order on platform and returns payment info
    运营模式：在平台创建订单并返回支付信息
    """
    settings = get_settings()

    result = await db.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "task_not_found",
                "message": "Task not found",
                "message_zh": "任务未找到"
            }
        )

    # Check if task can be paid
    # 检查任务是否可以支付
    if task.status not in [TaskStatus.CREATED.value, TaskStatus.QUOTED.value]:
        if task.payment_status == PaymentStatus.PAID.value:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "already_paid",
                    "message": "Task is already paid",
                    "message_zh": "任务已支付"
                }
            )
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_status",
                "message": "Task cannot be paid in current status",
                "message_zh": "当前状态无法支付"
            }
        )

    # In debug mode, auto-mark as paid
    # 调试模式下自动标记为已支付
    if settings.is_debug_mode():
        task.status = TaskStatus.PAID.value
        task.payment_status = PaymentStatus.PAID.value
        task.paid_at = datetime.utcnow()
        task.platform_order_id = f"debug_order_{task_id}"
        await db.commit()

        return PaymentInitResponse(
            task_id=task_id,
            platform_order_id=task.platform_order_id,
            payment_url=None,
            qr_code_url=None,
            amount=0.0,
            expires_at=None,
            is_debug_mode=True,
            auto_paid=True
        )

    # Operational mode: Create platform order
    # 运营模式：创建平台订单
    payment_provider = get_payment_provider()

    try:
        order_result = await payment_provider.create_order(
            task_id=task_id,
            amount=task.price_final,
            user_id=user["platform_user_id"],
            description=f"AcademicGuard - {task.word_count_billable}词文档处理"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "payment_error",
                "message": f"Failed to create payment order: {str(e)}",
                "message_zh": f"创建支付订单失败：{str(e)}"
            }
        )

    # Update task
    # 更新任务
    task.status = TaskStatus.PAYING.value
    task.payment_status = PaymentStatus.PENDING.value
    task.platform_order_id = order_result.platform_order_id
    task.expires_at = datetime.utcnow() + timedelta(hours=settings.task_expiry_hours)
    await db.commit()

    return PaymentInitResponse(
        task_id=task_id,
        platform_order_id=order_result.platform_order_id,
        payment_url=order_result.payment_url,
        qr_code_url=order_result.qr_code_url,
        amount=task.price_final,
        expires_at=order_result.expires_at,
        is_debug_mode=False,
        auto_paid=False
    )


@router.get("/status/{task_id}", response_model=PaymentStatusResponse)
async def check_payment_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Check payment status for a task
    检查任务支付状态

    Frontend should poll this endpoint to wait for payment confirmation.
    前端应轮询此端点等待支付确认。
    """
    settings = get_settings()

    result = await db.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "task_not_found",
                "message": "Task not found",
                "message_zh": "任务未找到"
            }
        )

    # In debug mode, always return paid
    # 调试模式下始终返回已支付
    if settings.is_debug_mode():
        return PaymentStatusResponse(
            task_id=task_id,
            status=TaskStatus.PAID.value,
            payment_status=PaymentStatus.PAID.value,
            paid_at=datetime.utcnow().isoformat(),
            can_process=True
        )

    # If pending, check with platform
    # 如果待处理，查询平台
    if task.payment_status == PaymentStatus.PENDING.value and task.platform_order_id:
        payment_provider = get_payment_provider()
        try:
            status_result = await payment_provider.check_status(task.platform_order_id)

            if status_result.status == PlatformOrderStatus.PAID:
                task.status = TaskStatus.PAID.value
                task.payment_status = PaymentStatus.PAID.value
                task.paid_at = datetime.utcnow()
                await db.commit()
        except Exception as e:
            # Log error but don't fail the request
            # 记录错误但不使请求失败
            print(f"Payment status check error: {e}")

    return PaymentStatusResponse(
        task_id=task_id,
        status=task.status,
        payment_status=task.payment_status,
        paid_at=task.paid_at.isoformat() if task.paid_at else None,
        can_process=task.payment_status == PaymentStatus.PAID.value
    )


@router.post("/callback")
async def payment_callback(
    request: PaymentCallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Payment callback from central platform
    来自中央平台的支付回调

    ========================================
    Security: HMAC-SHA256 Signature Required
    安全: 需要 HMAC-SHA256 签名验证
    ========================================

    Central platform calls this endpoint after payment status change.
    中央平台在支付状态变更后调用此端点。

    Expected request format:
    {
        "order_id": "platform_order_xxx",
        "status": "paid",
        "paid_at": "2024-01-01T10:30:00Z",
        "amount": 50.00,
        "timestamp": 1704067800,  # Unix timestamp
        "nonce": "random_string_123",  # Random string
        "signature": "hmac_sha256_signature"  # HMAC-SHA256(order_id|status|amount|timestamp|nonce, secret)
    }

    Signature Generation (for payment platform):
    签名生成方式（供支付平台参考）:
        sign_string = f"{order_id}|{status}|{amount}|{timestamp}|{nonce}"
        signature = hmac.new(secret.encode(), sign_string.encode(), hashlib.sha256).hexdigest()
    """
    settings = get_settings()

    # Skip in debug mode
    # 调试模式下跳过
    if settings.is_debug_mode():
        logger.warning("Payment callback received in DEBUG mode - skipping signature verification")
        return {"status": "skipped", "reason": "debug_mode"}

    # CRITICAL: Verify signature - DO NOT trust IP whitelist alone!
    # 关键: 验证签名 - 不要仅依赖IP白名单!
    webhook_secret = settings.payment_webhook_secret
    if not webhook_secret:
        logger.error("PAYMENT_WEBHOOK_SECRET not configured! Rejecting callback.")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "configuration_error",
                "message": "Payment webhook not properly configured",
                "message_zh": "支付回调未正确配置"
            }
        )

    if not verify_payment_signature(request, webhook_secret):
        logger.warning(f"Invalid payment callback signature for order: {request.order_id}")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_signature",
                "message": "Invalid or missing signature",
                "message_zh": "签名无效或缺失"
            }
        )

    logger.info(f"Payment callback signature verified for order: {request.order_id}")
    order_id = request.order_id

    result = await db.execute(
        select(Task).where(Task.platform_order_id == order_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "task_not_found",
                "message": "Task not found for order",
                "message_zh": "未找到对应订单的任务"
            }
        )

    # Update status based on callback
    # 根据回调更新状态
    if request.status == "paid":
        task.status = TaskStatus.PAID.value
        task.payment_status = PaymentStatus.PAID.value
        task.paid_at = datetime.utcnow()
        await db.commit()
    elif request.status == "failed":
        task.payment_status = PaymentStatus.FAILED.value
        await db.commit()
    elif request.status == "refunded":
        task.payment_status = PaymentStatus.REFUNDED.value
        await db.commit()

    return {"status": "processed", "task_id": task.task_id}
