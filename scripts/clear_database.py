"""
Database cleanup script - Clear all historical tasks and related data
数据库清理脚本 - 清除所有历史任务和相关数据

This script clears:
- Tasks
- Documents
- Sessions
- Sentences
- Modifications
- SubstepStates
- Users (optional)

但保留系统配置数据:
- FingerprintWords
- TermWhitelist
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.db.database import AsyncSessionLocal, engine


async def clear_all_tasks():
    """
    Clear all historical tasks and related data
    清除所有历史任务和相关数据
    """
    async with AsyncSessionLocal() as session:
        try:
            # Delete in order respecting foreign key constraints
            # 按顺序删除以尊重外键约束

            print("Starting database cleanup...")
            print("开始数据库清理...")

            # 1. Delete modifications (depends on sentences, sessions)
            result = await session.execute(text("DELETE FROM modifications"))
            print(f"  - Deleted {result.rowcount} modifications / 删除了 {result.rowcount} 条修改记录")

            # 2. Delete substep_states (depends on sessions)
            result = await session.execute(text("DELETE FROM substep_states"))
            print(f"  - Deleted {result.rowcount} substep_states / 删除了 {result.rowcount} 条子步骤状态")

            # 3. Delete sentences (depends on documents)
            result = await session.execute(text("DELETE FROM sentences"))
            print(f"  - Deleted {result.rowcount} sentences / 删除了 {result.rowcount} 条句子")

            # 4. Delete sessions (depends on documents)
            result = await session.execute(text("DELETE FROM sessions"))
            print(f"  - Deleted {result.rowcount} sessions / 删除了 {result.rowcount} 个会话")

            # 5. Delete tasks (depends on documents, users)
            result = await session.execute(text("DELETE FROM tasks"))
            print(f"  - Deleted {result.rowcount} tasks / 删除了 {result.rowcount} 个任务")

            # 6. Delete documents
            result = await session.execute(text("DELETE FROM documents"))
            print(f"  - Deleted {result.rowcount} documents / 删除了 {result.rowcount} 个文档")

            # 7. Delete users (optional - uncomment if needed)
            result = await session.execute(text("DELETE FROM users"))
            print(f"  - Deleted {result.rowcount} users / 删除了 {result.rowcount} 个用户")

            # 8. Delete feedbacks
            result = await session.execute(text("DELETE FROM feedbacks"))
            print(f"  - Deleted {result.rowcount} feedbacks / 删除了 {result.rowcount} 条反馈")

            await session.commit()
            print("\nDatabase cleanup completed successfully!")
            print("数据库清理成功完成！")

        except Exception as e:
            await session.rollback()
            print(f"\nError during cleanup: {e}")
            print(f"清理过程中出错: {e}")
            raise


async def clear_redis_cache():
    """
    Clear Redis cache (optional)
    清除 Redis 缓存（可选）
    """
    try:
        import redis.asyncio as redis
        from src.config import get_settings

        settings = get_settings()
        client = redis.from_url(settings.redis_url)

        await client.flushdb()
        print("Redis cache cleared / Redis 缓存已清除")
        await client.close()
    except Exception as e:
        print(f"Redis cleanup skipped (not available or error): {e}")
        print(f"Redis 清理跳过（不可用或出错）: {e}")


async def main():
    """Main entry point"""
    print("=" * 50)
    print("Database Cleanup Script / 数据库清理脚本")
    print("=" * 50)
    print()

    # Clear database
    await clear_all_tasks()

    print()

    # Try to clear Redis cache
    await clear_redis_cache()

    print()
    print("=" * 50)
    print("All done! / 全部完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
