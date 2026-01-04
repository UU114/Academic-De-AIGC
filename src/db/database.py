"""
Database connection and session management
数据库连接和会话管理
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import get_settings

settings = get_settings()

# Create async engine
# 创建异步引擎
# Note: SQLite doesn't support pool_size/max_overflow, so we use check_same_thread for SQLite
# 注意：SQLite不支持连接池配置，使用check_same_thread配置
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

# Create async session factory
# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
# 模型基类
Base = declarative_base()


async def init_db():
    """
    Initialize database tables
    初始化数据库表
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """
    Dependency for getting database session
    获取数据库会话的依赖
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
