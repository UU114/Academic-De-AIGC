"""
Authentication API Routes for AcademicGuard
AcademicGuard 认证API路由

This module provides authentication endpoints.
此模块提供认证端点。
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from src.db.database import get_db
from src.db.models import User
from src.config import get_settings
from src.services.auth_service import get_auth_provider, UserInfo
from src.middleware.auth_middleware import get_current_user, create_access_token
from src.middleware.mode_checker import get_system_mode_info

router = APIRouter()


# ==========================================
# Request/Response Models
# 请求/响应模型
# ==========================================

class SendCodeRequest(BaseModel):
    """Request to send SMS verification code 发送验证码请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="Phone number (手机号)")


class SendCodeResponse(BaseModel):
    """Response for send code request 发送验证码响应"""
    success: bool
    message: str
    message_zh: str
    debug_hint: Optional[str] = None  # Only in debug mode


class VerifyCodeRequest(BaseModel):
    """Request to verify SMS code and login 验证码登录请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="Phone number (手机号)")
    code: str = Field(..., min_length=4, max_length=6, description="Verification code (验证码)")


class LoginResponse(BaseModel):
    """Response for successful login 登录成功响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo
    system_mode: str


class UserInfoResponse(BaseModel):
    """Current user info response 当前用户信息响应"""
    user_id: str
    platform_user_id: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    is_debug: bool


class SystemModeResponse(BaseModel):
    """System mode info response 系统模式信息响应"""
    mode: str
    is_debug: bool
    is_operational: bool
    platform_configured: bool
    features: dict
    pricing: dict


# ==========================================
# API Endpoints
# API端点
# ==========================================

@router.post("/send-code", response_model=SendCodeResponse)
async def send_verification_code(request: SendCodeRequest):
    """
    Send SMS verification code
    发送短信验证码

    DEBUG mode: Returns success immediately, use any code (e.g., 123456)
    调试模式：立即返回成功，使用任意验证码（如 123456）

    OPERATIONAL mode: Sends real SMS via central platform
    运营模式：通过中央平台发送真实短信
    """
    settings = get_settings()
    auth_provider = get_auth_provider()

    success = await auth_provider.send_sms_code(request.phone)

    if not success:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "sms_send_failed",
                "message": "Failed to send verification code",
                "message_zh": "发送验证码失败"
            }
        )

    return SendCodeResponse(
        success=True,
        message="Verification code sent" if settings.is_operational_mode() else "Debug mode: use any code",
        message_zh="验证码已发送" if settings.is_operational_mode() else "调试模式：使用任意验证码",
        debug_hint="123456" if settings.is_debug_mode() else None
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: VerifyCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with phone and verification code
    使用手机号和验证码登录

    DEBUG mode: Any code is accepted
    调试模式：接受任意验证码

    OPERATIONAL mode: Validates with central platform
    运营模式：通过中央平台验证
    """
    settings = get_settings()
    auth_provider = get_auth_provider()

    # Verify code with provider
    # 使用提供者验证验证码
    user_info = await auth_provider.verify_phone_code(request.phone, request.code)

    if not user_info:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_code",
                "message": "Invalid verification code",
                "message_zh": "验证码无效"
            }
        )

    # Get or create local user record
    # 获取或创建本地用户记录
    result = await db.execute(
        select(User).where(User.platform_user_id == user_info.platform_user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            platform_user_id=user_info.platform_user_id,
            phone=user_info.phone,
            nickname=user_info.nickname
        )
        db.add(user)
        await db.flush()

    user.last_login_at = datetime.utcnow()
    await db.commit()

    # Generate JWT token
    # 生成JWT令牌
    access_token = create_access_token(user.id, user.platform_user_id)

    return LoginResponse(
        access_token=access_token,
        expires_in=settings.jwt_expire_minutes * 60,
        user=user_info,
        system_mode=settings.system_mode.value
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get current user info
    获取当前用户信息
    """
    if user.get("is_debug"):
        return UserInfoResponse(
            user_id="debug_user",
            platform_user_id="debug_platform_user",
            nickname="Debug User",
            phone=None,
            is_debug=True
        )

    result = await db.execute(
        select(User).where(User.id == user["user_id"])
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "user_not_found",
                "message": "User not found",
                "message_zh": "用户未找到"
            }
        )

    # Mask phone number for privacy
    # 隐藏手机号以保护隐私
    masked_phone = None
    if db_user.phone:
        masked_phone = db_user.phone[:3] + "****" + db_user.phone[-4:]

    return UserInfoResponse(
        user_id=db_user.id,
        platform_user_id=db_user.platform_user_id,
        nickname=db_user.nickname,
        phone=masked_phone,
        is_debug=False
    )


@router.get("/mode", response_model=SystemModeResponse)
async def get_system_mode():
    """
    Get current system mode
    获取当前系统模式

    Used by frontend to determine whether to show login/payment UI.
    前端用于判断是否显示登录/支付UI。
    """
    mode_info = get_system_mode_info()

    return SystemModeResponse(
        mode=mode_info["mode"],
        is_debug=mode_info["is_debug"],
        is_operational=mode_info["is_operational"],
        platform_configured=mode_info["platform_configured"],
        features=mode_info["features"],
        pricing=mode_info["pricing"]
    )


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    Logout current user
    登出当前用户

    Note: JWT tokens are stateless, so this just returns success.
    Client should remove the token from local storage.
    注意：JWT令牌是无状态的，因此只返回成功。
    客户端应从本地存储中移除令牌。
    """
    return {
        "success": True,
        "message": "Logged out successfully",
        "message_zh": "登出成功"
    }
