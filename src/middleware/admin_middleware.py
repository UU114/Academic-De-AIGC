"""
Admin Authentication Middleware for AcademicGuard
AcademicGuard 管理员认证中间件

This module provides admin authentication dependencies for FastAPI routes.
此模块为FastAPI路由提供管理员认证依赖。
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timedelta
import hmac

from src.config import get_settings
from src.middleware.auth_middleware import jwt_encode, jwt_decode, JWTError


# HTTP Bearer token security scheme for admin
# 管理员HTTP Bearer令牌安全方案
admin_security = HTTPBearer(auto_error=False)


async def get_admin_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(admin_security)
) -> dict:
    """
    Verify admin JWT token
    验证管理员JWT令牌

    Args:
        request: FastAPI request
        credentials: Bearer token credentials

    Returns:
        Admin info dict with admin_id and is_admin=True

    Raises:
        HTTPException: If admin authentication fails
    """
    settings = get_settings()

    # Check if admin is configured
    # 检查管理员是否已配置
    if not settings.is_admin_configured():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "admin_not_configured",
                "message": "Admin access is not configured",
                "message_zh": "管理员访问未配置"
            }
        )

    # Check credentials
    # 检查凭证
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "admin_auth_required",
                "message": "Admin authentication required",
                "message_zh": "需要管理员认证"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt_decode(
            credentials.credentials,
            settings.admin_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        # Verify this is an admin token
        # 验证这是管理员令牌
        if payload.get("type") != "admin":
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_admin_token",
                    "message": "Invalid admin token type",
                    "message_zh": "无效的管理员令牌类型"
                }
            )

        return {
            "admin_id": payload.get("sub"),
            "is_admin": True
        }
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "admin_token_invalid",
                "message": "Admin token invalid or expired",
                "message_zh": "管理员令牌无效或已过期"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )


def create_admin_token(admin_id: str = "admin") -> str:
    """
    Create JWT admin access token
    创建JWT管理员访问令牌

    Args:
        admin_id: Admin identifier (default: "admin")

    Returns:
        JWT token string
    """
    settings = get_settings()

    token_data = {
        "sub": admin_id,
        "type": "admin",
        "exp": (datetime.utcnow() + timedelta(
            minutes=settings.admin_token_expire_minutes
        )).timestamp()
    }

    return jwt_encode(
        token_data,
        settings.admin_secret_key,
        algorithm=settings.jwt_algorithm
    )


def verify_admin_secret(secret_key: str) -> bool:
    """
    Verify admin secret key using constant-time comparison
    使用常量时间比较验证管理员密钥

    Args:
        secret_key: The secret key to verify

    Returns:
        True if secret key matches, False otherwise
    """
    settings = get_settings()

    if not settings.is_admin_configured():
        return False

    # Use constant-time comparison to prevent timing attacks
    # 使用常量时间比较防止时序攻击
    return hmac.compare_digest(
        secret_key.encode(),
        settings.admin_secret_key.encode()
    )
