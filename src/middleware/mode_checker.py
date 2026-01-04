"""
Mode Checker Middleware for AcademicGuard
AcademicGuard 模式检查中间件

This middleware checks the system mode and adds mode information to requests.
此中间件检查系统模式并将模式信息添加到请求中。
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.config import get_settings, SystemMode


class ModeCheckerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check system mode and enforce restrictions
    检查系统模式并执行限制的中间件

    This middleware:
    此中间件：
    - Adds system mode info to request state (将系统模式信息添加到请求状态)
    - Returns mode info header in responses (在响应中返回模式信息头)
    - Handles payment-related routes in debug mode (在调试模式下处理支付相关路由)
    """

    # Routes that are payment-specific and behave differently in debug mode
    # 支付相关的路由，在调试模式下行为不同
    PAYMENT_ROUTES = [
        "/api/v1/payment/pay/",
    ]

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and add mode information
        处理请求并添加模式信息
        """
        settings = get_settings()
        path = request.url.path

        # Add mode info to request state for use in route handlers
        # 将模式信息添加到请求状态，供路由处理器使用
        request.state.system_mode = settings.system_mode
        request.state.is_debug = settings.is_debug_mode()
        request.state.is_operational = settings.is_operational_mode()

        # Process the request
        # 处理请求
        response = await call_next(request)

        # Add mode header to response for frontend awareness
        # 在响应中添加模式头，供前端感知
        response.headers["X-System-Mode"] = settings.system_mode.value
        response.headers["X-Debug-Mode"] = "true" if settings.is_debug_mode() else "false"

        return response


def get_system_mode_info() -> dict:
    """
    Get current system mode information
    获取当前系统模式信息

    Returns:
        Dict with mode details
    """
    settings = get_settings()

    return {
        "mode": settings.system_mode.value,
        "is_debug": settings.is_debug_mode(),
        "is_operational": settings.is_operational_mode(),
        "platform_configured": settings.platform_configured(),
        "features": {
            "require_login": settings.is_operational_mode(),
            "require_payment": settings.is_operational_mode(),
            "show_pricing": True,  # Always show pricing for transparency
            "payment_skipped": settings.is_debug_mode(),
        },
        "pricing": {
            "price_per_100_words": settings.price_per_100_words,
            "minimum_charge": settings.minimum_charge,
            "currency": "CNY"
        }
    }
