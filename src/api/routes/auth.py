"""
Authentication API Routes for AcademicGuard
AcademicGuard 认证API路由

This module provides authentication endpoints.
此模块提供认证端点。

Registration uses phone + password + email (optional).
注册使用手机号 + 密码 + 邮箱（可选）。
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import hashlib
import secrets
import re

from src.db.database import get_db
from src.db.models import User
from src.config import get_settings
from src.services.auth_service import get_auth_provider, UserInfo
from src.middleware.auth_middleware import get_current_user, create_access_token
from src.middleware.mode_checker import get_system_mode_info

router = APIRouter()


# ==========================================
# Password Utility Functions
# 密码工具函数
# ==========================================

def hash_password(password: str) -> str:
    """
    Hash password using SHA-256 with salt
    使用SHA-256加盐哈希密码
    """
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify password against stored hash
    验证密码是否与存储的哈希匹配
    """
    try:
        salt, hashed = password_hash.split("$")
        return hashlib.sha256((password + salt).encode()).hexdigest() == hashed
    except (ValueError, AttributeError):
        return False


# ==========================================
# Request/Response Models
# 请求/响应模型
# ==========================================

class RegisterRequest(BaseModel):
    """
    Request for user registration
    用户注册请求
    """
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="Phone number (手机号)")
    password: str = Field(..., min_length=6, max_length=32, description="Password (密码)")
    password_confirm: str = Field(..., min_length=6, max_length=32, description="Password confirmation (确认密码)")
    email: Optional[str] = Field(None, description="Email for password recovery (邮箱，用于找回密码)")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        """Validate email format 验证邮箱格式"""
        if v is not None and v != "":
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, v):
                raise ValueError("Invalid email format / 邮箱格式无效")
        return v

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, v, info):
        """Validate passwords match 验证两次密码一致"""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match / 两次密码不一致")
        return v


class RegisterResponse(BaseModel):
    """Response for registration 注册响应"""
    success: bool
    message: str
    message_zh: str
    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    """
    Request for user login with phone and password
    用户登录请求（手机号+密码）
    """
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="Phone number (手机号)")
    password: str = Field(..., min_length=1, description="Password (密码)")


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

@router.post("/register", response_model=RegisterResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new user with phone, password and optional email
    使用手机号、密码和可选邮箱注册新用户

    - Phone must be unique 手机号必须唯一
    - Password must be 6-32 characters 密码必须6-32位
    - Email is optional (for password recovery) 邮箱可选（用于找回密码）
    """
    # Check if phone already exists
    # 检查手机号是否已存在
    result = await db.execute(
        select(User).where(User.phone == request.phone)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "phone_exists",
                "message": "Phone number already registered",
                "message_zh": "该手机号已注册"
            }
        )

    # Create new user
    # 创建新用户
    password_hashed = hash_password(request.password)
    platform_user_id = f"local_{request.phone}"

    new_user = User(
        platform_user_id=platform_user_id,
        phone=request.phone,
        email=request.email if request.email else None,
        password_hash=password_hashed,
        nickname=f"User_{request.phone[-4:]}"
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return RegisterResponse(
        success=True,
        message="Registration successful",
        message_zh="注册成功",
        user_id=new_user.id
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with phone and password
    使用手机号和密码登录
    """
    settings = get_settings()

    # Find user by phone
    # 通过手机号查找用户
    result = await db.execute(
        select(User).where(User.phone == request.phone)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_credentials",
                "message": "Invalid phone number or password",
                "message_zh": "手机号或密码错误"
            }
        )

    # Verify password
    # 验证密码
    if not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_credentials",
                "message": "Invalid phone number or password",
                "message_zh": "手机号或密码错误"
            }
        )

    # Update last login time
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # Generate JWT token
    # 生成JWT令牌
    access_token = create_access_token(user.id, user.platform_user_id)

    # Build user info response
    # 构建用户信息响应
    user_info = UserInfo(
        platform_user_id=user.platform_user_id,
        phone=user.phone,
        nickname=user.nickname
    )

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


# ==========================================
# User Profile Endpoints
# 用户资料端点
# ==========================================

class UserProfileResponse(BaseModel):
    """User profile response 用户资料响应"""
    user_id: str
    platform_user_id: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None
    is_debug: bool
    total_tasks: int = 0
    total_spent: float = 0.0


class OrderItem(BaseModel):
    """Order item in list 订单列表项"""
    task_id: str
    document_name: Optional[str] = None
    word_count: int = 0
    price: float = 0.0
    status: str
    payment_status: str
    created_at: str
    paid_at: Optional[str] = None


class OrderListResponse(BaseModel):
    """Order list response 订单列表响应"""
    orders: List[OrderItem]
    total: int
    page: int
    page_size: int


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get detailed user profile
    获取详细用户资料
    """
    from src.db.models import Task
    from sqlalchemy import func as sql_func

    if user.get("is_debug"):
        return UserProfileResponse(
            user_id="debug_user",
            platform_user_id="debug_platform_user",
            nickname="Debug User",
            phone=None,
            created_at=None,
            last_login_at=None,
            is_debug=True,
            total_tasks=0,
            total_spent=0.0
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

    # Get task statistics
    # 获取任务统计
    stats_result = await db.execute(
        select(
            sql_func.count(Task.task_id).label("total_tasks"),
            sql_func.coalesce(sql_func.sum(Task.price_final), 0).label("total_spent")
        ).where(
            Task.user_id == db_user.id,
            Task.payment_status == "paid"
        )
    )
    stats = stats_result.first()

    # Mask phone number for privacy
    # 隐藏手机号以保护隐私
    masked_phone = None
    if db_user.phone:
        masked_phone = db_user.phone[:3] + "****" + db_user.phone[-4:]

    return UserProfileResponse(
        user_id=db_user.id,
        platform_user_id=db_user.platform_user_id,
        nickname=db_user.nickname,
        phone=masked_phone,
        created_at=db_user.created_at.isoformat() if db_user.created_at else None,
        last_login_at=db_user.last_login_at.isoformat() if db_user.last_login_at else None,
        is_debug=False,
        total_tasks=stats.total_tasks or 0,
        total_spent=float(stats.total_spent or 0)
    )


@router.get("/orders", response_model=OrderListResponse)
async def get_user_orders(
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get user's order history
    获取用户订单历史

    Returns paginated list of orders sorted by creation time (newest first).
    返回按创建时间排序的分页订单列表（最新在前）。
    """
    from src.db.models import Task, Document
    from sqlalchemy import func as sql_func, desc

    if user.get("is_debug"):
        return OrderListResponse(
            orders=[],
            total=0,
            page=page,
            page_size=page_size
        )

    # Get user record
    # 获取用户记录
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

    # Count total orders
    # 统计总订单数
    count_result = await db.execute(
        select(sql_func.count(Task.task_id)).where(Task.user_id == db_user.id)
    )
    total = count_result.scalar() or 0

    # Get paginated orders with document info
    # 获取分页订单及文档信息
    offset = (page - 1) * page_size
    orders_result = await db.execute(
        select(Task, Document.filename)
        .outerjoin(Document, Task.document_id == Document.id)
        .where(Task.user_id == db_user.id)
        .order_by(desc(Task.created_at))
        .offset(offset)
        .limit(page_size)
    )

    orders = []
    for task, filename in orders_result:
        orders.append(OrderItem(
            task_id=task.task_id,
            document_name=filename,
            word_count=task.word_count_billable or 0,
            price=task.price_final or 0.0,
            status=task.status,
            payment_status=task.payment_status,
            created_at=task.created_at.isoformat() if task.created_at else "",
            paid_at=task.paid_at.isoformat() if task.paid_at else None
        ))

    return OrderListResponse(
        orders=orders,
        total=total,
        page=page,
        page_size=page_size
    )
