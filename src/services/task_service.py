"""
Task Service for AcademicGuard
AcademicGuard 任务管理服务

This module provides task management services for billing workflow.
此模块提供计费工作流的任务管理服务。

Task Lifecycle (任务生命周期):
1. CREATED - Task created after document upload (文档上传后创建任务)
2. QUOTED - Price calculated and presented to user (计算价格并展示给用户)
3. PAYING - User initiated payment (用户发起支付)
4. PAID - Payment confirmed (支付确认)
5. PROCESSING - Analysis in progress (分析处理中)
6. COMPLETED - Analysis finished (分析完成)
7. EXPIRED - Unpaid task expired (未支付任务过期)
8. FAILED - Processing failed (处理失败)
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.models import Task, Document, User, TaskStatus, PaymentStatus
from src.services.word_counter import WordCounter, WordCountResult, PriceResult, get_word_counter
from src.services.payment_service import get_payment_provider, OrderCreateResult


class TaskService:
    """
    Task management service
    任务管理服务
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize task service with database session
        使用数据库会话初始化任务服务

        Args:
            db: Async database session
        """
        self.db = db
        self.word_counter = get_word_counter()

    async def create_task_for_document(
        self,
        document_id: str,
        user_id: Optional[str] = None
    ) -> Task:
        """
        Create a new billing task for a document
        为文档创建新的计费任务

        Args:
            document_id: Document ID
            user_id: User ID (optional in debug mode)

        Returns:
            Created Task instance
        """
        from src.config import get_settings
        settings = get_settings()

        # Get document
        # 获取文档
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Count words and calculate price
        # 统计字数并计算价格
        count_result, price_result = self.word_counter.count_and_price(document.original_text)

        # Create task
        # 创建任务
        task = Task(
            document_id=document_id,
            user_id=user_id,
            word_count_raw=count_result.raw_word_count,
            word_count_billable=count_result.clean_word_count,
            billable_units=count_result.billable_units,
            price_calculated=price_result.calculated_price,
            price_final=price_result.final_price,
            is_minimum_charge=price_result.is_minimum_charge,
            content_hash=count_result.content_hash,
            status=TaskStatus.CREATED.value,
            payment_status=PaymentStatus.UNPAID.value,
            expires_at=datetime.utcnow() + timedelta(hours=settings.task_expiry_hours)
        )

        self.db.add(task)
        await self.db.flush()

        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get task by ID
        根据ID获取任务

        Args:
            task_id: Task ID

        Returns:
            Task instance or None
        """
        result = await self.db.execute(
            select(Task).where(Task.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_task_by_document(self, document_id: str) -> Optional[Task]:
        """
        Get task by document ID
        根据文档ID获取任务

        Args:
            document_id: Document ID

        Returns:
            Task instance or None
        """
        result = await self.db.execute(
            select(Task).where(Task.document_id == document_id)
        )
        return result.scalar_one_or_none()

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        payment_status: Optional[PaymentStatus] = None
    ) -> Task:
        """
        Update task status
        更新任务状态

        Args:
            task_id: Task ID
            status: New task status
            payment_status: New payment status (optional)

        Returns:
            Updated Task instance
        """
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        task.status = status.value

        if payment_status:
            task.payment_status = payment_status.value

        # Update timestamps based on status
        # 根据状态更新时间戳
        if status == TaskStatus.QUOTED:
            task.quoted_at = datetime.utcnow()
        elif status == TaskStatus.PAID:
            task.paid_at = datetime.utcnow()
        elif status == TaskStatus.COMPLETED:
            task.processed_at = datetime.utcnow()

        await self.db.flush()
        return task

    async def mark_as_quoted(self, task_id: str) -> Task:
        """
        Mark task as quoted (price calculated)
        标记任务为已报价

        Args:
            task_id: Task ID

        Returns:
            Updated Task instance
        """
        return await self.update_task_status(task_id, TaskStatus.QUOTED)

    async def mark_as_paid(self, task_id: str, platform_order_id: str) -> Task:
        """
        Mark task as paid
        标记任务为已支付

        Args:
            task_id: Task ID
            platform_order_id: Platform order ID

        Returns:
            Updated Task instance
        """
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        task.status = TaskStatus.PAID.value
        task.payment_status = PaymentStatus.PAID.value
        task.platform_order_id = platform_order_id
        task.paid_at = datetime.utcnow()

        await self.db.flush()
        return task

    async def mark_as_processing(self, task_id: str) -> Task:
        """
        Mark task as processing (analysis started)
        标记任务为处理中

        Args:
            task_id: Task ID

        Returns:
            Updated Task instance
        """
        return await self.update_task_status(task_id, TaskStatus.PROCESSING)

    async def mark_as_completed(self, task_id: str) -> Task:
        """
        Mark task as completed
        标记任务为已完成

        Args:
            task_id: Task ID

        Returns:
            Updated Task instance
        """
        return await self.update_task_status(task_id, TaskStatus.COMPLETED)

    async def mark_as_expired(self, task_id: str) -> Task:
        """
        Mark task as expired
        标记任务为已过期

        Args:
            task_id: Task ID

        Returns:
            Updated Task instance
        """
        return await self.update_task_status(task_id, TaskStatus.EXPIRED)

    async def check_payment_required(self, task_id: str) -> bool:
        """
        Check if payment is required for task
        检查任务是否需要支付

        In debug mode, payment is never required.
        调试模式下，不需要支付。

        Args:
            task_id: Task ID

        Returns:
            True if payment required, False otherwise
        """
        from src.config import get_settings
        settings = get_settings()

        if settings.is_debug_mode():
            return False

        task = await self.get_task(task_id)
        if not task:
            return True

        return task.payment_status != PaymentStatus.PAID.value

    async def can_start_processing(self, task_id: str) -> Tuple[bool, str]:
        """
        Check if task can start processing
        检查任务是否可以开始处理

        Validates:
        - Task exists
        - Task not expired
        - Payment confirmed (in operational mode)
        - Task not already processing/completed

        Args:
            task_id: Task ID

        Returns:
            Tuple of (can_start, reason)
        """
        from src.config import get_settings
        settings = get_settings()

        task = await self.get_task(task_id)

        if not task:
            return False, "Task not found"

        if task.status == TaskStatus.EXPIRED.value:
            return False, "Task has expired"

        if task.status == TaskStatus.PROCESSING.value:
            return False, "Task is already processing"

        if task.status == TaskStatus.COMPLETED.value:
            return False, "Task is already completed"

        # In operational mode, require payment
        # 运营模式下需要支付
        if settings.is_operational_mode():
            if task.payment_status != PaymentStatus.PAID.value:
                return False, "Payment required"

        return True, "OK"

    async def expire_old_tasks(self) -> int:
        """
        Expire tasks that have not been paid within the expiry time
        将超时未支付的任务标记为过期

        Returns:
            Number of tasks expired
        """
        result = await self.db.execute(
            select(Task).where(
                Task.status.in_([TaskStatus.CREATED.value, TaskStatus.QUOTED.value, TaskStatus.PAYING.value]),
                Task.payment_status == PaymentStatus.UNPAID.value,
                Task.expires_at < datetime.utcnow()
            )
        )
        tasks = result.scalars().all()

        count = 0
        for task in tasks:
            task.status = TaskStatus.EXPIRED.value
            count += 1

        if count > 0:
            await self.db.flush()

        return count
