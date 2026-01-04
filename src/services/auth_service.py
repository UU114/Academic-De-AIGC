"""
Authentication Service for AcademicGuard
AcademicGuard 认证服务

This module provides authentication interfaces for integrating with central platform.
此模块提供与中央平台集成的认证接口。

Reserved Interface Specification (for central platform):
预留接口规范（供中央平台参考）：

1. POST /api/v1/auth/send-sms
   Request: { "phone": "13800138000", "app_id": "academicguard" }
   Response: { "success": true, "message": "sent" }

2. POST /api/v1/auth/verify-sms
   Request: { "phone": "13800138000", "code": "123456", "app_id": "academicguard" }
   Response: {
       "success": true,
       "user_id": "platform_uid_xxx",
       "access_token": "jwt_token",
       "refresh_token": "refresh_token",
       "expires_in": 86400
   }

3. GET /api/v1/users/{user_id}
   Headers: Authorization: Bearer {api_key}
   Response: { "user_id": "xxx", "phone": "138****8000", "nickname": "Name" }

4. POST /api/v1/auth/refresh
   Request: { "refresh_token": "xxx" }
   Response: { "access_token": "new_token", "expires_in": 86400 }
"""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import httpx


class UserInfo(BaseModel):
    """
    User information from platform
    平台用户信息
    """
    platform_user_id: str
    phone: Optional[str] = None
    nickname: Optional[str] = None


class AuthToken(BaseModel):
    """
    Authentication token
    认证令牌
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user_info: UserInfo


class IAuthProvider(ABC):
    """
    Authentication provider interface
    认证提供者接口

    This is a reserved interface for central platform integration.
    这是一个预留接口，用于中央平台集成。
    """

    @abstractmethod
    async def verify_phone_code(self, phone: str, code: str) -> Optional[UserInfo]:
        """
        Verify phone number with SMS code
        验证手机号和短信验证码

        Args:
            phone: Phone number (手机号)
            code: SMS verification code (短信验证码)

        Returns:
            UserInfo if verified, None otherwise
        """
        pass

    @abstractmethod
    async def send_sms_code(self, phone: str) -> bool:
        """
        Send SMS verification code
        发送短信验证码

        Args:
            phone: Phone number to send code to

        Returns:
            True if sent successfully
        """
        pass

    @abstractmethod
    async def get_user_info(self, platform_user_id: str) -> Optional[UserInfo]:
        """
        Get user info from platform
        从平台获取用户信息

        Args:
            platform_user_id: Platform user ID

        Returns:
            UserInfo if found, None otherwise
        """
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Optional[AuthToken]:
        """
        Refresh authentication token
        刷新认证令牌
        """
        pass


class DebugAuthProvider(IAuthProvider):
    """
    Debug mode authentication provider - Always allows access
    调试模式认证提供者 - 始终允许访问

    In debug mode:
    调试模式下：
    - Any verification code works (建议使用 123456)
    - Phone numbers are accepted as-is
    - User IDs are generated from phone numbers
    """

    async def verify_phone_code(self, phone: str, code: str) -> Optional[UserInfo]:
        """
        In debug mode, any code works
        调试模式下，任意验证码都通过
        """
        return UserInfo(
            platform_user_id=f"debug_{phone}",
            phone=phone,
            nickname=f"Debug User ({phone[-4:]})"
        )

    async def send_sms_code(self, phone: str) -> bool:
        """
        In debug mode, always succeed
        调试模式下，始终成功
        """
        return True

    async def get_user_info(self, platform_user_id: str) -> Optional[UserInfo]:
        """
        In debug mode, return mock user info
        调试模式下，返回模拟用户信息
        """
        return UserInfo(
            platform_user_id=platform_user_id,
            nickname="Debug User"
        )

    async def refresh_token(self, refresh_token: str) -> Optional[AuthToken]:
        """
        Not implemented for debug mode
        调试模式下不实现
        """
        return None


class PlatformAuthProvider(IAuthProvider):
    """
    Production authentication provider - Connects to central platform
    生产环境认证提供者 - 对接中央平台

    ========================================
    Reserved Interface Implementation Notes
    预留接口实现说明
    ========================================

    Central platform needs to provide the following API endpoints:
    中央平台需要提供以下API端点：

    1. POST {base_url}/api/v1/auth/send-sms
       Request: { "phone": "13800138000", "app_id": "xxx" }
       Response: { "success": true, "message": "sent" }

    2. POST {base_url}/api/v1/auth/verify-sms
       Request: { "phone": "13800138000", "code": "123456", "app_id": "xxx" }
       Response: {
           "success": true,
           "user_id": "platform_uid_xxx",
           "access_token": "jwt_token",
           "refresh_token": "refresh_token",
           "expires_in": 86400
       }

    3. GET {base_url}/api/v1/users/{user_id}
       Headers: Authorization: Bearer {api_key}
       Response: {
           "user_id": "platform_uid_xxx",
           "phone": "138****8000",
           "nickname": "User Name"
       }

    4. POST {base_url}/api/v1/auth/refresh
       Request: { "refresh_token": "xxx" }
       Response: { "access_token": "new_token", "expires_in": 86400 }
    """

    def __init__(self, base_url: str, api_key: str, app_id: str):
        """
        Initialize platform auth provider
        初始化平台认证提供者

        Args:
            base_url: Central platform API base URL
            api_key: API key for authentication
            app_id: Application ID registered on platform
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.app_id = app_id
        self.client = httpx.AsyncClient(timeout=30.0)

    async def verify_phone_code(self, phone: str, code: str) -> Optional[UserInfo]:
        """
        Verify phone code with central platform
        向中央平台验证手机验证码
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/verify-sms",
                json={
                    "phone": phone,
                    "code": code,
                    "app_id": self.app_id
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return UserInfo(
                        platform_user_id=data.get("user_id"),
                        phone=phone,
                        nickname=data.get("nickname")
                    )

            return None
        except Exception as e:
            print(f"Platform auth error: {e}")
            return None

    async def send_sms_code(self, phone: str) -> bool:
        """
        Send SMS code via central platform
        通过中央平台发送短信验证码
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/send-sms",
                json={
                    "phone": phone,
                    "app_id": self.app_id
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("success", False)

            return False
        except Exception as e:
            print(f"Platform SMS error: {e}")
            return False

    async def get_user_info(self, platform_user_id: str) -> Optional[UserInfo]:
        """
        Get user info from central platform
        从中央平台获取用户信息
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/users/{platform_user_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                return UserInfo(
                    platform_user_id=data.get("user_id"),
                    phone=data.get("phone"),
                    nickname=data.get("nickname")
                )

            return None
        except Exception as e:
            print(f"Platform user info error: {e}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[AuthToken]:
        """
        Refresh token via central platform
        通过中央平台刷新令牌
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                return AuthToken(
                    access_token=data.get("access_token"),
                    expires_in=data.get("expires_in", 86400),
                    user_info=UserInfo(platform_user_id="")  # Will be filled by caller
                )

            return None
        except Exception as e:
            print(f"Platform token refresh error: {e}")
            return None


def get_auth_provider() -> IAuthProvider:
    """
    Factory function to get appropriate auth provider based on system mode
    根据系统模式获取适当的认证提供者的工厂函数
    """
    from src.config import get_settings

    settings = get_settings()

    if settings.is_debug_mode():
        return DebugAuthProvider()

    if not settings.platform_configured():
        # Fallback to debug mode if platform not configured
        # 如果平台未配置，回退到调试模式
        print("WARNING: Platform not configured, falling back to debug auth")
        return DebugAuthProvider()

    return PlatformAuthProvider(
        base_url=settings.platform_base_url,
        api_key=settings.platform_api_key,
        app_id=settings.platform_app_id
    )
