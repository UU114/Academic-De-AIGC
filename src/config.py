"""
Configuration management for AcademicGuard
AcademicGuard 配置管理
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache
from enum import Enum


class SystemMode(str, Enum):
    """
    System operation mode enumeration
    系统运行模式枚举

    DEBUG: No login/payment required, for development and testing
    调试模式：无需登录/支付，用于开发测试

    OPERATIONAL: Full login/payment flow, for production
    运营模式：完整登录/支付流程，用于生产环境
    """
    DEBUG = "debug"
    OPERATIONAL = "operational"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    从环境变量加载的应用配置
    """

    # Application
    # 应用配置
    app_name: str = "AcademicGuard"
    app_version: str = "1.0.0"
    debug: bool = False

    # API Server
    # API服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./academicguard.db"

    # Redis Cache
    # Redis缓存配置
    redis_url: str = "redis://redis:6379/0"
    cache_ttl: int = 3600  # 1 hour

    # LLM APIs
    # LLM API配置
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    # deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK-API-KEY")  # DeepSeek official (commented out)
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

    # Volcengine (火山引擎) DeepSeek API - faster than official
    # 火山引擎 DeepSeek API - 比官方更快
    volcengine_api_key: Optional[str] = Field(default=None, alias="VOLCENGINE_API_KEY")
    volcengine_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    volcengine_model: str = "deepseek-v3-2-251201"  # Volcengine model endpoint ID

    llm_provider: str = "volcengine"  # volcengine | deepseek | gemini | anthropic | openai
    llm_model: str = "deepseek-v3-2-251201"  # volcengine model or deepseek-chat | gemini-2.5-flash | etc.
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.7

    # DeepSeek API base URL (official - commented out, using Volcengine instead)
    # DeepSeek API 基础URL（官方 - 已注释，改用火山引擎）
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK-API-KEY")  # Keep for fallback

    # Analysis Settings
    # 分析配置
    ppl_threshold_high: float = 20.0  # Below this is high risk
    ppl_threshold_medium: float = 40.0  # Below this is medium risk
    fingerprint_density_threshold: float = 0.1  # 10% fingerprint words

    # Validation Settings
    # 验证配置
    semantic_similarity_threshold: float = 0.80
    max_retry_attempts: int = 3

    # Default Processing Settings
    # 默认处理配置
    default_colloquialism_level: int = 4
    default_target_lang: str = "zh"

    # ==========================================
    # System Mode Configuration
    # 系统模式配置
    # ==========================================
    system_mode: SystemMode = Field(
        default=SystemMode.DEBUG,
        description="System operation mode: debug or operational"
    )

    # ==========================================
    # Central Platform Configuration
    # 中央平台配置（运营模式需要）
    # ==========================================
    platform_base_url: Optional[str] = Field(
        default=None,
        description="Central platform API base URL"
    )
    platform_api_key: Optional[str] = Field(
        default=None,
        description="API key for central platform authentication"
    )
    platform_app_id: Optional[str] = Field(
        default=None,
        description="Application ID registered on central platform"
    )

    # ==========================================
    # Pricing Configuration
    # 定价配置
    # ==========================================
    price_per_100_words: float = Field(
        default=2.0,
        description="Price per 100 words in RMB"
    )
    minimum_charge: float = Field(
        default=50.0,
        description="Minimum charge threshold in RMB"
    )

    # ==========================================
    # Task Configuration
    # 任务配置
    # ==========================================
    task_expiry_hours: int = Field(
        default=24,
        description="Hours before unpaid task expires"
    )
    max_file_size_mb: int = Field(
        default=5,
        description="Maximum file size in MB"
    )
    text_cleaning_timeout: int = Field(
        default=5,
        description="Timeout for text cleaning in seconds"
    )

    # ==========================================
    # Security Configuration
    # 安全配置
    # ==========================================
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT token signing"
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    def is_debug_mode(self) -> bool:
        """
        Check if running in debug mode
        检查是否为调试模式
        """
        return self.system_mode == SystemMode.DEBUG

    def is_operational_mode(self) -> bool:
        """
        Check if running in operational mode
        检查是否为运营模式
        """
        return self.system_mode == SystemMode.OPERATIONAL

    def platform_configured(self) -> bool:
        """
        Check if central platform is properly configured
        检查中央平台是否已配置
        """
        return bool(
            self.platform_base_url and
            self.platform_api_key and
            self.platform_app_id
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True  # Allow both field name and alias


class RiskWeights(BaseSettings):
    """
    Risk scoring weights configuration
    风险评分权重配置

    Updated weights to prioritize structure detection (contains tiered fingerprints)
    since PPL is unreliable for short texts and original fingerprint detector
    doesn't include newer AI patterns.
    更新权重以优先结构检测（包含分级指纹词）
    因为PPL对短文本不可靠，且原指纹检测器不包含新AI模式
    """

    perplexity: float = 0.15      # Reduced: unreliable for short texts
    fingerprint: float = 0.20     # Reduced: limited word coverage
    burstiness: float = 0.15      # Slightly reduced
    structure: float = 0.50       # Increased: contains tiered fingerprints + patterns

    class Config:
        env_prefix = "RISK_WEIGHT_"


class ColloquialismConfig:
    """
    Colloquialism level configuration
    口语化等级配置
    """

    LEVELS = {
        0: {"name": "Most Academic", "name_zh": "最学术化", "description": "Journal paper level"},
        1: {"name": "Very Academic", "name_zh": "非常学术", "description": "Journal paper level"},
        2: {"name": "Academic", "name_zh": "学术化", "description": "Journal paper level"},
        3: {"name": "Thesis Level", "name_zh": "论文级", "description": "Thesis/Dissertation"},
        4: {"name": "Moderate Academic", "name_zh": "适度学术", "description": "Default thesis level"},
        5: {"name": "Semi-formal", "name_zh": "半正式", "description": "Conference paper"},
        6: {"name": "Conference Level", "name_zh": "会议级", "description": "Conference paper"},
        7: {"name": "Technical Blog", "name_zh": "技术博客", "description": "Professional blog"},
        8: {"name": "Casual Professional", "name_zh": "休闲专业", "description": "Technical blog"},
        9: {"name": "Casual", "name_zh": "休闲", "description": "Informal discussion"},
        10: {"name": "Most Casual", "name_zh": "最口语化", "description": "Casual discussion"},
    }

    @classmethod
    def get_level_info(cls, level: int) -> dict:
        """Get information for a specific level"""
        return cls.LEVELS.get(level, cls.LEVELS[4])

    @classmethod
    def get_level_range(cls, level: int) -> str:
        """Get the style range category"""
        if level <= 2:
            return "academic_strict"
        elif level <= 4:
            return "academic_moderate"
        elif level <= 6:
            return "semi_formal"
        elif level <= 8:
            return "casual_professional"
        else:
            return "casual_informal"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    获取缓存的配置实例
    """
    return Settings()


@lru_cache()
def get_risk_weights() -> RiskWeights:
    """
    Get cached risk weights instance
    获取缓存的风险权重实例
    """
    return RiskWeights()
