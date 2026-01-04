"""
Middleware layer for AcademicGuard
AcademicGuard 中间件层

This module contains FastAPI middleware including:
此模块包含FastAPI中间件，包括：

- mode_checker: System mode checking middleware
  系统模式检查中间件
- auth_middleware: Authentication middleware and dependencies
  认证中间件和依赖
"""

from src.middleware.mode_checker import ModeCheckerMiddleware
from src.middleware.auth_middleware import (
    get_current_user,
    get_current_user_optional,
    require_auth,
    require_payment
)

__all__ = [
    "ModeCheckerMiddleware",
    "get_current_user",
    "get_current_user_optional",
    "require_auth",
    "require_payment",
]
