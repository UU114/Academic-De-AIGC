"""
Internal Service Security Middleware
内网服务安全中间件

This middleware protects internal endpoints (like payment callbacks) from external access.
此中间件保护内部端点（如支付回调）免受外部访问。

Security measures:
- IP whitelist verification for internal endpoints
- Optional shared secret verification for service-to-service auth
"""

import os
import hmac
import ipaddress
import logging
from typing import List, Set, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class InternalServiceMiddleware(BaseHTTPMiddleware):
    """
    Verify that requests to internal endpoints come from allowed sources
    验证内部端点请求来自允许的来源
    """

    # Internal endpoint paths that require IP whitelist verification
    # 需要IP白名单验证的内部端点路径
    INTERNAL_PATHS = [
        "/api/v1/payment/callback",
        "/api/v1/internal/",
    ]

    # Default allowed IPs/networks
    # 默认允许的IP/网段
    DEFAULT_ALLOWED_IPS = [
        "127.0.0.1",
        "::1",  # IPv6 localhost
        "10.0.0.0/8",  # Private network Class A
        "172.16.0.0/12",  # Private network Class B
        "192.168.0.0/16",  # Private network Class C
    ]

    def __init__(self, app, allowed_ips: List[str] = None, require_secret: bool = False):
        """
        Initialize middleware

        Args:
            app: FastAPI application
            allowed_ips: List of allowed IP addresses or CIDR networks
            require_secret: If True, also require X-Service-Key header
        """
        super().__init__(app)

        # Get allowed IPs from environment or use defaults
        # 从环境变量获取允许的IP或使用默认值
        env_ips = os.getenv("INTERNAL_ALLOWED_IPS", "")
        if env_ips:
            ip_list = [ip.strip() for ip in env_ips.split(",") if ip.strip()]
        elif allowed_ips:
            ip_list = allowed_ips
        else:
            ip_list = self.DEFAULT_ALLOWED_IPS

        # Parse IP networks
        # 解析IP网段
        self.allowed_networks = []
        for ip in ip_list:
            try:
                self.allowed_networks.append(ipaddress.ip_network(ip, strict=False))
            except ValueError as e:
                logger.warning(f"Invalid IP/network in whitelist: {ip} - {e}")

        self.require_secret = require_secret
        self.service_secret = os.getenv("INTERNAL_SERVICE_SECRET", "")

        logger.info(
            f"InternalServiceMiddleware initialized with {len(self.allowed_networks)} "
            f"allowed networks, secret required: {require_secret}"
        )

    def _is_internal_endpoint(self, path: str) -> bool:
        """Check if the path is an internal endpoint"""
        return any(path.startswith(internal_path) for internal_path in self.INTERNAL_PATHS)

    def _get_client_ip(self, request: Request) -> str:
        """
        Get real client IP, considering proxy headers
        获取真实客户端IP，考虑代理头

        Priority: X-Real-IP > X-Forwarded-For > client.host
        """
        # Check X-Real-IP (set by Nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Check X-Forwarded-For (first IP is original client)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"

    def _is_ip_allowed(self, client_ip: str) -> bool:
        """Check if the IP is in the allowed list"""
        try:
            addr = ipaddress.ip_address(client_ip)
            return any(addr in network for network in self.allowed_networks)
        except ValueError:
            logger.warning(f"Invalid IP address: {client_ip}")
            return False

    def _verify_service_secret(self, request: Request) -> bool:
        """Verify the X-Service-Key header"""
        if not self.service_secret:
            # No secret configured, skip verification
            return True

        provided_key = request.headers.get("X-Service-Key", "")
        return hmac.compare_digest(provided_key, self.service_secret)

    async def dispatch(self, request: Request, call_next):
        """Process the request"""
        path = request.url.path

        # Only check internal endpoints
        # 只检查内部端点
        if self._is_internal_endpoint(path):
            client_ip = self._get_client_ip(request)

            # Verify IP whitelist
            # 验证IP白名单
            if not self._is_ip_allowed(client_ip):
                logger.warning(
                    f"Blocked internal endpoint access from unauthorized IP: {client_ip} "
                    f"to {path}"
                )
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "access_denied",
                        "message": "Access denied. IP not in whitelist.",
                        "message_zh": "访问被拒绝。IP不在白名单中。"
                    }
                )

            # Optionally verify service secret
            # 可选验证服务密钥
            if self.require_secret and not self._verify_service_secret(request):
                logger.warning(
                    f"Blocked internal endpoint access with invalid service key from {client_ip} "
                    f"to {path}"
                )
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "invalid_service_key",
                        "message": "Invalid or missing service key.",
                        "message_zh": "服务密钥无效或缺失。"
                    }
                )

            logger.debug(f"Allowed internal endpoint access from {client_ip} to {path}")

        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    为所有响应添加安全头
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        # 安全响应头
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # HSTS header is typically set by Nginx, but add here as backup
        # HSTS头通常由Nginx设置，这里作为备份添加
        # Only add if not already present (to avoid duplicate headers from Nginx)
        if 'Strict-Transport-Security' not in response.headers:
            # Note: Only effective over HTTPS, browsers ignore over HTTP
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response
