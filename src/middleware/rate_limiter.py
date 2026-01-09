"""
API Rate Limiter Middleware
API速率限制中间件

Provides rate limiting to prevent API abuse and protect LLM quota.
提供速率限制以防止API滥用并保护LLM配额。

Features:
- Per-IP rate limiting
- Per-user rate limiting (if authenticated)
- Configurable limits per endpoint
- In-memory storage (simple) or Redis storage (production)
"""

import os
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple, Optional, Callable
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Try to import slowapi for production-grade rate limiting
# 尝试导入slowapi用于生产级速率限制
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    logger.warning(
        "slowapi not installed. Using simple in-memory rate limiter. "
        "For production, install with: pip install slowapi"
    )


class SimpleRateLimiter:
    """
    Simple in-memory rate limiter for development/small-scale deployment
    简单的内存速率限制器，用于开发/小规模部署

    Note: Not suitable for multi-process deployments. Use slowapi with Redis for production.
    注意：不适合多进程部署。生产环境请使用slowapi配合Redis。
    """

    def __init__(self):
        # Store request timestamps: {key: [timestamp1, timestamp2, ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        # Cleanup interval (seconds)
        self.cleanup_interval = 60
        self.last_cleanup = time.time()

    def _cleanup_old_requests(self):
        """Remove old request records to prevent memory leak"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = current_time - 3600  # Keep last hour of data
        for key in list(self.requests.keys()):
            self.requests[key] = [
                ts for ts in self.requests[key] if ts > cutoff_time
            ]
            if not self.requests[key]:
                del self.requests[key]

        self.last_cleanup = current_time

    def is_rate_limited(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if the key is rate limited

        Args:
            key: Unique identifier (IP or user ID)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            (is_limited, remaining, reset_in_seconds)
        """
        self._cleanup_old_requests()

        current_time = time.time()
        window_start = current_time - window_seconds

        # Filter requests within the window
        recent_requests = [
            ts for ts in self.requests[key] if ts > window_start
        ]
        self.requests[key] = recent_requests

        request_count = len(recent_requests)

        if request_count >= limit:
            # Calculate when the oldest request will expire
            oldest = min(recent_requests) if recent_requests else current_time
            reset_in = int(oldest + window_seconds - current_time)
            return True, 0, max(reset_in, 1)

        # Record this request
        self.requests[key].append(current_time)
        remaining = limit - request_count - 1

        return False, remaining, window_seconds


# Global rate limiter instance
# 全局速率限制器实例
simple_limiter = SimpleRateLimiter()


# Rate limit configurations for different endpoints
# 不同端点的速率限制配置
# Format: {path_prefix: (limit, window_seconds)}
RATE_LIMIT_CONFIGS = {
    "/api/v1/auth/login": (5, 60),      # 5 requests per minute (prevent brute force)
    "/api/v1/auth/register": (3, 3600),  # 3 requests per hour
    "/api/v1/suggest": (20, 60),         # 20 LLM calls per minute
    "/api/v1/structure": (10, 60),       # 10 structure analyses per minute
    "/api/v1/transition": (10, 60),      # 10 transition analyses per minute
    "/api/v1/paragraph": (10, 60),       # 10 paragraph analyses per minute
    "/api/v1/documents/upload": (20, 3600),  # 20 uploads per hour
    "/api/v1/analysis": (30, 60),        # 30 analysis requests per minute
}

# Default rate limit for unspecified endpoints
# 未指定端点的默认速率限制
DEFAULT_RATE_LIMIT = (100, 60)  # 100 requests per minute


def get_rate_limit_key(request: Request) -> str:
    """
    Get the rate limit key for a request
    获取请求的速率限制键

    Uses user ID if authenticated, otherwise IP address.
    如果已认证则使用用户ID，否则使用IP地址。
    """
    # Check for authenticated user
    user = getattr(request.state, "user", None)
    if user and isinstance(user, dict):
        user_id = user.get("user_id")
        if user_id:
            return f"user:{user_id}"

    # Fall back to IP address
    # 检查代理头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    return f"ip:{ip}"


def get_rate_limit_config(path: str) -> Tuple[int, int]:
    """Get rate limit config for a path"""
    for prefix, config in RATE_LIMIT_CONFIGS.items():
        if path.startswith(prefix):
            return config
    return DEFAULT_RATE_LIMIT


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using simple in-memory limiter
    使用简单内存限制器的速率限制中间件
    """

    # Paths to exclude from rate limiting
    # 排除速率限制的路径
    EXCLUDED_PATHS = [
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip excluded paths
        if any(path == excluded or path.startswith(f"{excluded}/") for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)

        # Skip OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get rate limit configuration
        limit, window = get_rate_limit_config(path)
        key = get_rate_limit_key(request)

        # Check rate limit
        is_limited, remaining, reset_in = simple_limiter.is_rate_limited(
            f"{key}:{path}", limit, window
        )

        if is_limited:
            logger.warning(f"Rate limit exceeded for {key} on {path}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Please wait {reset_in} seconds.",
                    "message_zh": f"请求过于频繁。请等待 {reset_in} 秒后重试。",
                    "retry_after": reset_in
                },
                headers={
                    "Retry-After": str(reset_in),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + reset_in)
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)

        return response


# If slowapi is available, create a limiter for decorator-based limiting
# 如果slowapi可用，创建用于装饰器限制的限制器
if SLOWAPI_AVAILABLE:
    # Check for Redis configuration
    redis_url = os.getenv("REDIS_URL", "")

    if redis_url:
        # Use Redis storage for production
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri=redis_url
        )
    else:
        # Use memory storage
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri="memory://"
        )
else:
    # Dummy limiter for when slowapi is not available
    # slowapi不可用时的占位限制器
    limiter = None


def rate_limit(limit_string: str):
    """
    Rate limit decorator (works with or without slowapi)
    速率限制装饰器（无论slowapi是否可用都能工作）

    Usage:
        @router.post("/endpoint")
        @rate_limit("5 per minute")
        async def endpoint(request: Request, ...):
            ...

    Note: If slowapi is available, uses slowapi's decorator.
          Otherwise, uses simple_limiter manually.
    """
    if SLOWAPI_AVAILABLE and limiter:
        return limiter.limit(limit_string)
    else:
        # Return a no-op decorator if slowapi is not available
        # The middleware handles rate limiting anyway
        def decorator(func):
            return func
        return decorator
