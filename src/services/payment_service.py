"""
Payment Service for AcademicGuard
AcademicGuard 支付服务

This module provides payment interfaces for integrating with central platform.
此模块提供与中央平台集成的支付接口。

Reserved Interface Specification (for central platform):
预留接口规范（供中央平台参考）：

1. POST /api/v1/payments/create
   Headers: Authorization: Bearer {api_key}
   Request: {
       "app_id": "academicguard",
       "external_order_id": "task_xxx",
       "user_id": "platform_uid_xxx",
       "amount": 50.00,
       "currency": "CNY",
       "description": "AcademicGuard - 3200词文档处理",
       "notify_url": "https://yoursite.com/api/v1/payment/callback",
       "return_url": "https://yoursite.com/payment/success"
   }
   Response: {
       "success": true,
       "order_id": "platform_order_xxx",
       "payment_url": "https://pay.platform.com/xxx",
       "qr_code_url": "https://pay.platform.com/qr/xxx",
       "expires_at": "2024-01-01T12:00:00Z"
   }

2. GET /api/v1/payments/{order_id}/status
   Headers: Authorization: Bearer {api_key}
   Response: {
       "order_id": "platform_order_xxx",
       "status": "paid",
       "paid_at": "2024-01-01T10:30:00Z",
       "amount": 50.00
   }

3. POST /api/v1/payments/{order_id}/refund
   Headers: Authorization: Bearer {api_key}
   Request: { "amount": 50.00, "reason": "User requested cancellation" }
   Response: { "success": true, "refund_id": "refund_xxx" }

4. POST /api/v1/payment/callback (Local endpoint to receive callbacks)
   Request: {
       "order_id": "platform_order_xxx",
       "status": "paid",
       "paid_at": "2024-01-01T10:30:00Z",
       "amount": 50.00,
       "signature": "hmac_sha256_signature"
   }
   Response: { "status": "processed" }
"""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
import httpx


class PlatformOrderStatus(str, Enum):
    """
    Platform order status enumeration
    平台订单状态枚举
    """
    CREATED = "created"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderCreateResult(BaseModel):
    """
    Result of creating an order on platform
    平台订单创建结果
    """
    platform_order_id: str
    payment_url: Optional[str] = None      # Payment page URL
    qr_code_url: Optional[str] = None      # QR code URL
    expires_at: Optional[str] = None


class OrderStatusResult(BaseModel):
    """
    Result of querying order status
    订单状态查询结果
    """
    platform_order_id: str
    status: PlatformOrderStatus
    paid_at: Optional[str] = None
    amount: float


class IPaymentProvider(ABC):
    """
    Payment provider interface
    支付提供者接口

    This is a reserved interface for central platform payment integration.
    这是一个预留接口，用于中央平台支付集成。
    """

    @abstractmethod
    async def create_order(
        self,
        task_id: str,
        amount: float,
        user_id: str,
        description: str
    ) -> OrderCreateResult:
        """
        Create payment order on central platform
        在中央平台创建支付订单

        Args:
            task_id: Local task ID for reference
            amount: Amount in RMB
            user_id: Platform user ID
            description: Order description

        Returns:
            OrderCreateResult with platform order info
        """
        pass

    @abstractmethod
    async def check_status(self, platform_order_id: str) -> OrderStatusResult:
        """
        Check payment status from platform
        从平台检查支付状态

        Args:
            platform_order_id: Platform order ID

        Returns:
            OrderStatusResult with current status
        """
        pass

    @abstractmethod
    async def request_refund(
        self,
        platform_order_id: str,
        amount: float,
        reason: str
    ) -> bool:
        """
        Request refund for an order
        请求订单退款
        """
        pass


class DebugPaymentProvider(IPaymentProvider):
    """
    Debug mode payment provider - All payments auto-succeed
    调试模式支付提供者 - 所有支付自动成功

    In debug mode:
    调试模式下：
    - Orders are created with debug_ prefix
    - All payments are marked as immediately paid
    - No actual payment is required
    """

    async def create_order(
        self,
        task_id: str,
        amount: float,
        user_id: str,
        description: str
    ) -> OrderCreateResult:
        """
        In debug mode, create a fake order that auto-succeeds
        调试模式下，创建一个自动成功的模拟订单
        """
        return OrderCreateResult(
            platform_order_id=f"debug_order_{task_id}",
            payment_url=None,  # No payment needed in debug
            qr_code_url=None
        )

    async def check_status(self, platform_order_id: str) -> OrderStatusResult:
        """
        In debug mode, all orders are paid
        调试模式下，所有订单都已支付
        """
        return OrderStatusResult(
            platform_order_id=platform_order_id,
            status=PlatformOrderStatus.PAID,
            paid_at=datetime.utcnow().isoformat(),
            amount=0.0
        )

    async def request_refund(
        self,
        platform_order_id: str,
        amount: float,
        reason: str
    ) -> bool:
        """
        Always succeed in debug mode
        调试模式下始终成功
        """
        return True


class PlatformPaymentProvider(IPaymentProvider):
    """
    Production payment provider - Connects to central platform
    生产环境支付提供者 - 对接中央平台

    ========================================
    Reserved Interface Implementation Notes
    预留接口实现说明
    ========================================

    Central platform needs to provide the following API endpoints:
    中央平台需要提供以下API端点：

    1. POST {base_url}/api/v1/payments/create
       Headers: Authorization: Bearer {api_key}
       Request: {
           "app_id": "academicguard",
           "external_order_id": "task_xxx",
           "user_id": "platform_uid_xxx",
           "amount": 50.00,
           "currency": "CNY",
           "description": "AcademicGuard - 文档处理",
           "notify_url": "https://yoursite.com/api/v1/payment/callback",
           "return_url": "https://yoursite.com/payment/success"
       }
       Response: {
           "success": true,
           "order_id": "platform_order_xxx",
           "payment_url": "https://pay.platform.com/xxx",
           "qr_code_url": "https://pay.platform.com/qr/xxx",
           "expires_at": "2024-01-01T12:00:00Z"
       }

    2. GET {base_url}/api/v1/payments/{order_id}/status
       Headers: Authorization: Bearer {api_key}
       Response: {
           "order_id": "platform_order_xxx",
           "status": "paid",  // created, pending, paid, failed, cancelled, refunded
           "paid_at": "2024-01-01T10:30:00Z",
           "amount": 50.00
       }

    3. POST {base_url}/api/v1/payments/{order_id}/refund
       Headers: Authorization: Bearer {api_key}
       Request: { "amount": 50.00, "reason": "User requested cancellation" }
       Response: { "success": true, "refund_id": "refund_xxx" }
    """

    def __init__(self, base_url: str, api_key: str, app_id: str, notify_url: Optional[str] = None):
        """
        Initialize platform payment provider
        初始化平台支付提供者

        Args:
            base_url: Central platform API base URL
            api_key: API key for authentication
            app_id: Application ID registered on platform
            notify_url: URL for payment callbacks
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.app_id = app_id
        self.notify_url = notify_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def create_order(
        self,
        task_id: str,
        amount: float,
        user_id: str,
        description: str
    ) -> OrderCreateResult:
        """
        Create payment order on central platform
        在中央平台创建支付订单
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/payments/create",
                json={
                    "app_id": self.app_id,
                    "external_order_id": task_id,
                    "user_id": user_id,
                    "amount": amount,
                    "currency": "CNY",
                    "description": description,
                    "notify_url": self.notify_url
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return OrderCreateResult(
                        platform_order_id=data.get("order_id"),
                        payment_url=data.get("payment_url"),
                        qr_code_url=data.get("qr_code_url"),
                        expires_at=data.get("expires_at")
                    )

            raise Exception(f"Failed to create order: {response.text}")
        except Exception as e:
            print(f"Platform payment error: {e}")
            raise

    async def check_status(self, platform_order_id: str) -> OrderStatusResult:
        """
        Check payment status from central platform
        从中央平台检查支付状态
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/payments/{platform_order_id}/status",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                return OrderStatusResult(
                    platform_order_id=data.get("order_id"),
                    status=PlatformOrderStatus(data.get("status", "pending")),
                    paid_at=data.get("paid_at"),
                    amount=data.get("amount", 0.0)
                )

            raise Exception(f"Failed to check status: {response.text}")
        except Exception as e:
            print(f"Platform status check error: {e}")
            raise

    async def request_refund(
        self,
        platform_order_id: str,
        amount: float,
        reason: str
    ) -> bool:
        """
        Request refund via central platform
        通过中央平台请求退款
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/payments/{platform_order_id}/refund",
                json={
                    "amount": amount,
                    "reason": reason
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("success", False)

            return False
        except Exception as e:
            print(f"Platform refund error: {e}")
            return False


def get_payment_provider() -> IPaymentProvider:
    """
    Factory function to get appropriate payment provider based on system mode
    根据系统模式获取适当的支付提供者的工厂函数
    """
    from src.config import get_settings

    settings = get_settings()

    if settings.is_debug_mode():
        return DebugPaymentProvider()

    if not settings.platform_configured():
        # Fallback to debug mode if platform not configured
        # 如果平台未配置，回退到调试模式
        print("WARNING: Platform not configured, falling back to debug payment")
        return DebugPaymentProvider()

    return PlatformPaymentProvider(
        base_url=settings.platform_base_url,
        api_key=settings.platform_api_key,
        app_id=settings.platform_app_id
    )
