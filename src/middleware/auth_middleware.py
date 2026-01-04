"""
Authentication Middleware for AcademicGuard
AcademicGuard 认证中间件

This module provides authentication dependencies for FastAPI routes.
此模块为FastAPI路由提供认证依赖。
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import hmac
import hashlib
import base64
from datetime import datetime, timedelta

from src.config import get_settings
from src.db.database import get_db
from src.db.models import Task, PaymentStatus


# Try to import python-jose, fallback to simple implementation
# 尝试导入python-jose，否则使用简单实现
try:
    from jose import jwt, JWTError
    USE_JOSE = True
except ImportError:
    USE_JOSE = False
    # Simple JWT error class for fallback
    # 简单JWT错误类用于回退
    class JWTError(Exception):
        pass


# HTTP Bearer token security scheme
# HTTP Bearer令牌安全方案
security = HTTPBearer(auto_error=False)


def _simple_jwt_encode(payload: dict, secret: str, algorithm: str = "HS256") -> str:
    """
    Simple JWT encode using hmac (fallback when jose not available)
    使用hmac的简单JWT编码（jose不可用时的回退）
    """
    header = {"alg": algorithm, "typ": "JWT"}

    # Base64 encode header and payload
    # Base64编码header和payload
    header_b64 = base64.urlsafe_b64encode(
        json.dumps(header, separators=(',', ':')).encode()
    ).rstrip(b'=').decode()

    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(',', ':'), default=str).encode()
    ).rstrip(b'=').decode()

    # Create signature
    # 创建签名
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _simple_jwt_decode(token: str, secret: str, algorithms: list = None) -> dict:
    """
    Simple JWT decode using hmac (fallback when jose not available)
    使用hmac的简单JWT解码（jose不可用时的回退）
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise JWTError("Invalid token format")

        header_b64, payload_b64, signature_b64 = parts

        # Verify signature
        # 验证签名
        message = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).rstrip(b'=').decode()

        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            raise JWTError("Invalid signature")

        # Decode payload (add padding if needed)
        # 解码payload（如需要添加填充）
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        # Check expiration
        # 检查过期
        if 'exp' in payload:
            exp = payload['exp']
            if isinstance(exp, str):
                exp = datetime.fromisoformat(exp.replace('Z', '+00:00')).timestamp()
            if datetime.utcnow().timestamp() > exp:
                raise JWTError("Token expired")

        return payload
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        raise JWTError(f"Invalid token: {e}")


def jwt_encode(payload: dict, secret: str, algorithm: str = "HS256") -> str:
    """
    Encode JWT token (uses jose if available, fallback to simple implementation)
    编码JWT令牌（如果可用使用jose，否则使用简单实现）
    """
    if USE_JOSE:
        return jwt.encode(payload, secret, algorithm=algorithm)
    else:
        return _simple_jwt_encode(payload, secret, algorithm)


def jwt_decode(token: str, secret: str, algorithms: list = None) -> dict:
    """
    Decode JWT token (uses jose if available, fallback to simple implementation)
    解码JWT令牌（如果可用使用jose，否则使用简单实现）
    """
    if USE_JOSE:
        return jwt.decode(token, secret, algorithms=algorithms or ["HS256"])
    else:
        return _simple_jwt_decode(token, secret, algorithms)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Get current user from JWT token (required)
    从JWT令牌获取当前用户（必需）

    In debug mode, returns a mock debug user.
    调试模式下返回模拟用户。

    In operational mode, requires valid JWT token.
    运营模式下需要有效的JWT令牌。

    Args:
        request: FastAPI request
        credentials: Bearer token credentials

    Returns:
        User info dict

    Raises:
        HTTPException: If authentication fails in operational mode
    """
    settings = get_settings()

    # In debug mode, allow anonymous access with debug user
    # 调试模式下，允许使用调试用户匿名访问
    if settings.is_debug_mode():
        return {
            "user_id": "debug_user",
            "platform_user_id": "debug_platform_user",
            "is_debug": True
        }

    # In operational mode, require valid token
    # 运营模式下需要有效令牌
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "authentication_required",
                "message": "Authentication required in operational mode",
                "message_zh": "运营模式下需要认证"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt_decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return {
            "user_id": payload.get("sub"),
            "platform_user_id": payload.get("platform_user_id"),
            "is_debug": False
        }
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_token",
                "message": "Invalid or expired token",
                "message_zh": "令牌无效或已过期"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current user from JWT token (optional)
    从JWT令牌获取当前用户（可选）

    Returns None if no token provided, instead of raising exception.
    如果未提供令牌则返回None，而不是抛出异常。

    Args:
        request: FastAPI request
        credentials: Bearer token credentials

    Returns:
        User info dict or None
    """
    settings = get_settings()

    # In debug mode, return debug user
    # 调试模式下返回调试用户
    if settings.is_debug_mode():
        return {
            "user_id": "debug_user",
            "platform_user_id": "debug_platform_user",
            "is_debug": True
        }

    # No credentials provided
    # 未提供凭证
    if not credentials:
        return None

    try:
        payload = jwt_decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return {
            "user_id": payload.get("sub"),
            "platform_user_id": payload.get("platform_user_id"),
            "is_debug": False
        }
    except JWTError:
        return None


def require_auth():
    """
    Dependency that requires authentication
    需要认证的依赖

    Use this as a dependency in routes that require authentication.
    在需要认证的路由中使用此依赖。

    Returns:
        Dependency function
    """
    return Depends(get_current_user)


async def require_payment(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
) -> bool:
    """
    Dependency that checks payment status for a task
    检查任务支付状态的依赖

    In debug mode, always returns True (payment not required).
    调试模式下始终返回True（不需要支付）。

    In operational mode, checks if task is paid.
    运营模式下检查任务是否已支付。

    Args:
        task_id: Task ID to check
        db: Database session
        user: Current user (from auth dependency)

    Returns:
        True if payment OK

    Raises:
        HTTPException: If payment required but not completed
    """
    settings = get_settings()

    # Skip payment check in debug mode
    # 调试模式下跳过支付检查
    if settings.is_debug_mode():
        return True

    # Check task payment status
    # 检查任务支付状态
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

    if task.payment_status != PaymentStatus.PAID.value:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "payment_required",
                "message": "Payment required before processing",
                "message_zh": "处理前需要支付",
                "task_id": task_id
            }
        )

    return True


def create_access_token(user_id: str, platform_user_id: str) -> str:
    """
    Create JWT access token for user
    为用户创建JWT访问令牌

    Args:
        user_id: Local user ID
        platform_user_id: Platform user ID

    Returns:
        JWT token string
    """
    settings = get_settings()

    token_data = {
        "sub": user_id,
        "platform_user_id": platform_user_id,
        "exp": (datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()
    }

    return jwt_encode(
        token_data,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
