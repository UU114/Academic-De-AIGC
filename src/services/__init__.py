"""
Services layer for AcademicGuard
AcademicGuard 服务层

This module contains business logic services including:
此模块包含业务逻辑服务，包括：

- auth_service: Authentication service (platform integration)
  认证服务（平台集成）
- payment_service: Payment service (platform integration)
  支付服务（平台集成）
- word_counter: Word counting and billing calculation
  字数统计和计费计算
- task_service: Task management service
  任务管理服务
"""

from src.services.auth_service import (
    IAuthProvider,
    DebugAuthProvider,
    PlatformAuthProvider,
    get_auth_provider,
    UserInfo,
    AuthToken
)

from src.services.payment_service import (
    IPaymentProvider,
    DebugPaymentProvider,
    PlatformPaymentProvider,
    get_payment_provider,
    OrderCreateResult,
    OrderStatusResult,
    PlatformOrderStatus
)

from src.services.word_counter import (
    WordCounter,
    WordCountResult
)

__all__ = [
    # Auth
    "IAuthProvider",
    "DebugAuthProvider",
    "PlatformAuthProvider",
    "get_auth_provider",
    "UserInfo",
    "AuthToken",
    # Payment
    "IPaymentProvider",
    "DebugPaymentProvider",
    "PlatformPaymentProvider",
    "get_payment_provider",
    "OrderCreateResult",
    "OrderStatusResult",
    "PlatformOrderStatus",
    # Word Counter
    "WordCounter",
    "WordCountResult",
]
