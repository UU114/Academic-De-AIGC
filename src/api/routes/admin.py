"""
Admin API Routes for AcademicGuard
AcademicGuard 管理员API路由

This module provides admin statistics and dashboard endpoints.
此模块提供管理员统计和仪表板端点。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from src.db.database import get_db
from src.db.models import User, Task, Document, Session, Feedback, PaymentStatus, TaskStatus
from src.config import get_settings
from src.middleware.admin_middleware import get_admin_user, create_admin_token, verify_admin_secret


router = APIRouter()


# ==========================================
# Request/Response Models
# 请求/响应模型
# ==========================================

class AdminLoginRequest(BaseModel):
    """Admin login request 管理员登录请求"""
    secret_key: str = Field(..., description="Admin secret key | 管理员密钥")


class AdminLoginResponse(BaseModel):
    """Admin login response 管理员登录响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin_id: str
    message: str = "Login successful"
    message_zh: str = "登录成功"


class OverviewStatsResponse(BaseModel):
    """Overview statistics response 概览统计响应"""
    # Revenue statistics 营收统计
    total_revenue: float = Field(..., description="Total revenue | 总营收")
    today_revenue: float = Field(..., description="Today's revenue | 今日营收")
    this_week_revenue: float = Field(..., description="This week's revenue | 本周营收")
    this_month_revenue: float = Field(..., description="This month's revenue | 本月营收")

    # Task statistics 任务统计
    total_tasks: int = Field(..., description="Total tasks | 总任务数")
    paid_tasks: int = Field(..., description="Paid tasks | 已付款任务")
    pending_tasks: int = Field(..., description="Pending payment tasks | 待付款任务")
    completed_tasks: int = Field(..., description="Completed tasks | 已完成任务")
    failed_tasks: int = Field(..., description="Failed tasks | 失败任务")

    # User statistics 用户统计
    total_users: int = Field(..., description="Total users | 总用户数")
    active_users_today: int = Field(..., description="Active users today | 今日活跃用户")
    active_users_week: int = Field(..., description="Active users this week | 本周活跃用户")
    new_users_today: int = Field(..., description="New users today | 今日新增用户")

    # Usage statistics 使用量统计
    total_words_processed: int = Field(..., description="Total words processed | 总处理字数")
    total_documents: int = Field(..., description="Total documents | 总文档数")

    # Time range 时间范围
    data_from: str = Field(..., description="Data start time | 数据起始时间")
    data_to: str = Field(..., description="Data end time | 数据截止时间")


class RevenueDataPoint(BaseModel):
    """Revenue data point 营收数据点"""
    date: str
    revenue: float
    task_count: int
    avg_price: float


class RevenueStatsResponse(BaseModel):
    """Revenue statistics response 营收统计响应"""
    period: str = Field(..., description="Period type: daily/weekly/monthly")
    data: List[RevenueDataPoint] = Field(..., description="Time series data | 时间序列数据")
    total_revenue: float = Field(..., description="Total revenue in period | 期间总营收")
    total_tasks: int = Field(..., description="Total tasks in period | 期间总任务数")
    average_order_value: float = Field(..., description="Average order value | 平均订单金额")
    growth_rate: Optional[float] = Field(None, description="Growth rate vs previous period | 环比增长率")


class TaskStatusDistribution(BaseModel):
    """Task status distribution 任务状态分布"""
    status: str
    count: int
    percentage: float


class TaskStatsResponse(BaseModel):
    """Task statistics response 任务统计响应"""
    # Status distribution 状态分布
    status_distribution: List[TaskStatusDistribution]
    payment_distribution: List[TaskStatusDistribution]

    # Pricing statistics 定价统计
    avg_word_count: float = Field(..., description="Average word count | 平均字数")
    avg_price: float = Field(..., description="Average price | 平均价格")
    min_price: float = Field(..., description="Minimum price | 最低价格")
    max_price: float = Field(..., description="Maximum price | 最高价格")
    minimum_charge_count: int = Field(..., description="Tasks hitting minimum charge | 触发最低消费任务数")
    minimum_charge_ratio: float = Field(..., description="Ratio hitting minimum charge | 最低消费比例")

    # Time series 时间序列
    tasks_by_date: List[Dict[str, Any]]


# ==========================================
# API Endpoints
# API端点
# ==========================================

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """
    Admin login with secret key
    使用密钥登录管理员

    Args:
        request: Login request with secret_key

    Returns:
        AdminLoginResponse with JWT token
    """
    settings = get_settings()

    # Check if admin is configured
    # 检查管理员是否已配置
    if not settings.is_admin_configured():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "admin_not_configured",
                "message": "Admin access is not configured. Please set ADMIN_SECRET_KEY environment variable.",
                "message_zh": "管理员访问未配置。请设置ADMIN_SECRET_KEY环境变量。"
            }
        )

    # Verify secret key using constant-time comparison
    # 使用常量时间比较验证密钥
    if not verify_admin_secret(request.secret_key):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_secret_key",
                "message": "Invalid admin secret key",
                "message_zh": "管理员密钥无效"
            }
        )

    # Create admin token
    # 创建管理员令牌
    token = create_admin_token()

    return AdminLoginResponse(
        access_token=token,
        expires_in=settings.admin_token_expire_minutes * 60,
        admin_id="admin"
    )


@router.get("/stats/overview", response_model=OverviewStatsResponse)
async def get_overview_stats(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_admin_user)
):
    """
    Get dashboard overview statistics
    获取仪表板概览统计

    Returns comprehensive statistics for the admin dashboard.
    返回管理员仪表板的综合统计数据。
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    # Revenue statistics
    # 营收统计
    revenue_query = select(
        func.coalesce(func.sum(Task.price_final), 0).label("total"),
        func.coalesce(func.sum(
            case((Task.paid_at >= today_start, Task.price_final), else_=0)
        ), 0).label("today"),
        func.coalesce(func.sum(
            case((Task.paid_at >= week_start, Task.price_final), else_=0)
        ), 0).label("week"),
        func.coalesce(func.sum(
            case((Task.paid_at >= month_start, Task.price_final), else_=0)
        ), 0).label("month")
    ).where(Task.payment_status == PaymentStatus.PAID.value)

    revenue_result = await db.execute(revenue_query)
    revenue_row = revenue_result.first()

    # Task statistics
    # 任务统计
    task_query = select(
        func.count(Task.task_id).label("total"),
        func.sum(case((Task.payment_status == PaymentStatus.PAID.value, 1), else_=0)).label("paid"),
        func.sum(case((Task.payment_status == PaymentStatus.UNPAID.value, 1), else_=0)).label("pending"),
        func.sum(case((Task.status == TaskStatus.COMPLETED.value, 1), else_=0)).label("completed"),
        func.sum(case((Task.status == TaskStatus.FAILED.value, 1), else_=0)).label("failed")
    )

    task_result = await db.execute(task_query)
    task_row = task_result.first()

    # User statistics
    # 用户统计
    user_query = select(
        func.count(User.id).label("total"),
        func.sum(case((User.last_login_at >= today_start, 1), else_=0)).label("active_today"),
        func.sum(case((User.last_login_at >= week_start, 1), else_=0)).label("active_week"),
        func.sum(case((User.created_at >= today_start, 1), else_=0)).label("new_today")
    )

    user_result = await db.execute(user_query)
    user_row = user_result.first()

    # Usage statistics
    # 使用量统计
    usage_query = select(
        func.coalesce(func.sum(Task.word_count_billable), 0).label("total_words")
    ).where(Task.payment_status == PaymentStatus.PAID.value)

    usage_result = await db.execute(usage_query)
    usage_row = usage_result.first()

    doc_count_result = await db.execute(select(func.count(Document.id)))
    doc_count = doc_count_result.scalar() or 0

    return OverviewStatsResponse(
        # Revenue
        total_revenue=float(revenue_row.total or 0),
        today_revenue=float(revenue_row.today or 0),
        this_week_revenue=float(revenue_row.week or 0),
        this_month_revenue=float(revenue_row.month or 0),
        # Tasks
        total_tasks=int(task_row.total or 0),
        paid_tasks=int(task_row.paid or 0),
        pending_tasks=int(task_row.pending or 0),
        completed_tasks=int(task_row.completed or 0),
        failed_tasks=int(task_row.failed or 0),
        # Users
        total_users=int(user_row.total or 0),
        active_users_today=int(user_row.active_today or 0),
        active_users_week=int(user_row.active_week or 0),
        new_users_today=int(user_row.new_today or 0),
        # Usage
        total_words_processed=int(usage_row.total_words or 0),
        total_documents=doc_count,
        # Time range
        data_from="2024-01-01",
        data_to=now.strftime("%Y-%m-%d %H:%M:%S")
    )


@router.get("/stats/revenue", response_model=RevenueStatsResponse)
async def get_revenue_stats(
    period: str = Query("daily", description="Period: daily/weekly/monthly"),
    days: int = Query(30, description="Number of days to look back | 回溯天数", ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_admin_user)
):
    """
    Get revenue statistics with time series data
    获取带时间序列数据的营收统计

    Args:
        period: Aggregation period (daily/weekly/monthly)
        days: Number of days to look back

    Returns:
        Revenue statistics with time series
    """
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    # Query revenue by date
    # 按日期查询营收
    if period == "daily":
        date_format = func.date(Task.paid_at)
    elif period == "weekly":
        # SQLite week grouping
        date_format = func.strftime('%Y-W%W', Task.paid_at)
    else:  # monthly
        date_format = func.strftime('%Y-%m', Task.paid_at)

    query = select(
        date_format.label("date"),
        func.sum(Task.price_final).label("revenue"),
        func.count(Task.task_id).label("task_count"),
        func.avg(Task.price_final).label("avg_price")
    ).where(
        and_(
            Task.payment_status == PaymentStatus.PAID.value,
            Task.paid_at >= start_date,
            Task.paid_at.isnot(None)
        )
    ).group_by(date_format).order_by(date_format.desc())

    result = await db.execute(query)
    rows = result.all()

    # Convert to data points
    # 转换为数据点
    data = []
    total_revenue = 0.0
    total_tasks = 0

    for row in rows:
        revenue = float(row.revenue or 0)
        task_count = int(row.task_count or 0)
        avg_price = float(row.avg_price or 0)

        total_revenue += revenue
        total_tasks += task_count

        data.append(RevenueDataPoint(
            date=str(row.date) if row.date else "",
            revenue=revenue,
            task_count=task_count,
            avg_price=round(avg_price, 2)
        ))

    # Reverse to show oldest first (for charts)
    # 反转以显示最旧的数据在前（用于图表）
    data.reverse()

    # Calculate average order value
    # 计算平均订单金额
    avg_order_value = total_revenue / total_tasks if total_tasks > 0 else 0

    return RevenueStatsResponse(
        period=period,
        data=data,
        total_revenue=round(total_revenue, 2),
        total_tasks=total_tasks,
        average_order_value=round(avg_order_value, 2),
        growth_rate=None  # TODO: Calculate growth rate vs previous period
    )


@router.get("/stats/tasks", response_model=TaskStatsResponse)
async def get_task_stats(
    days: int = Query(30, description="Number of days to look back | 回溯天数", ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_admin_user)
):
    """
    Get task statistics
    获取任务统计

    Args:
        days: Number of days to look back

    Returns:
        Task statistics with status distribution
    """
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    # Status distribution
    # 状态分布
    status_query = select(
        Task.status,
        func.count(Task.task_id).label("count")
    ).where(Task.created_at >= start_date).group_by(Task.status)

    status_result = await db.execute(status_query)
    status_rows = status_result.all()

    total_count = sum(row.count for row in status_rows)
    status_distribution = [
        TaskStatusDistribution(
            status=row.status or "unknown",
            count=row.count,
            percentage=round(row.count / total_count * 100, 1) if total_count > 0 else 0
        )
        for row in status_rows
    ]

    # Payment distribution
    # 支付状态分布
    payment_query = select(
        Task.payment_status,
        func.count(Task.task_id).label("count")
    ).where(Task.created_at >= start_date).group_by(Task.payment_status)

    payment_result = await db.execute(payment_query)
    payment_rows = payment_result.all()

    payment_distribution = [
        TaskStatusDistribution(
            status=row.payment_status or "unknown",
            count=row.count,
            percentage=round(row.count / total_count * 100, 1) if total_count > 0 else 0
        )
        for row in payment_rows
    ]

    # Pricing statistics
    # 定价统计
    pricing_query = select(
        func.avg(Task.word_count_billable).label("avg_words"),
        func.avg(Task.price_final).label("avg_price"),
        func.min(Task.price_final).label("min_price"),
        func.max(Task.price_final).label("max_price"),
        func.sum(case((Task.is_minimum_charge == True, 1), else_=0)).label("min_charge_count")
    ).where(
        and_(
            Task.created_at >= start_date,
            Task.price_final.isnot(None)
        )
    )

    pricing_result = await db.execute(pricing_query)
    pricing_row = pricing_result.first()

    min_charge_count = int(pricing_row.min_charge_count or 0)
    paid_count = sum(row.count for row in payment_rows if row.payment_status == PaymentStatus.PAID.value)

    # Tasks by date
    # 按日期统计任务
    date_query = select(
        func.date(Task.created_at).label("date"),
        func.count(Task.task_id).label("count")
    ).where(Task.created_at >= start_date).group_by(func.date(Task.created_at)).order_by(func.date(Task.created_at))

    date_result = await db.execute(date_query)
    date_rows = date_result.all()

    tasks_by_date = [
        {"date": str(row.date), "count": row.count}
        for row in date_rows
    ]

    return TaskStatsResponse(
        status_distribution=status_distribution,
        payment_distribution=payment_distribution,
        avg_word_count=round(float(pricing_row.avg_words or 0), 0),
        avg_price=round(float(pricing_row.avg_price or 0), 2),
        min_price=round(float(pricing_row.min_price or 0), 2),
        max_price=round(float(pricing_row.max_price or 0), 2),
        minimum_charge_count=min_charge_count,
        minimum_charge_ratio=round(min_charge_count / paid_count * 100, 1) if paid_count > 0 else 0,
        tasks_by_date=tasks_by_date
    )


@router.get("/stats/users")
async def get_user_stats(
    days: int = Query(30, description="Number of days to look back | 回溯天数", ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_admin_user)
):
    """
    Get user statistics
    获取用户统计

    Args:
        days: Number of days to look back

    Returns:
        User statistics with registration trend
    """
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    # User registration by date
    # 按日期统计用户注册
    reg_query = select(
        func.date(User.created_at).label("date"),
        func.count(User.id).label("count")
    ).where(User.created_at >= start_date).group_by(func.date(User.created_at)).order_by(func.date(User.created_at))

    reg_result = await db.execute(reg_query)
    reg_rows = reg_result.all()

    registrations_by_date = [
        {"date": str(row.date), "count": row.count}
        for row in reg_rows
    ]

    # Top users by spending
    # 按消费统计top用户
    top_users_query = select(
        User.id,
        User.phone,
        User.nickname,
        func.count(Task.task_id).label("task_count"),
        func.coalesce(func.sum(Task.price_final), 0).label("total_spent")
    ).outerjoin(Task, Task.user_id == User.id).where(
        Task.payment_status == PaymentStatus.PAID.value
    ).group_by(User.id).order_by(func.sum(Task.price_final).desc()).limit(10)

    top_result = await db.execute(top_users_query)
    top_rows = top_result.all()

    top_users = [
        {
            "user_id": row.id,
            "phone": row.phone[:3] + "****" + row.phone[-4:] if row.phone and len(row.phone) >= 7 else "***",
            "nickname": row.nickname or "匿名用户",
            "task_count": row.task_count,
            "total_spent": float(row.total_spent or 0)
        }
        for row in top_rows
    ]

    return {
        "registrations_by_date": registrations_by_date,
        "total_new_users": sum(row.count for row in reg_rows),
        "top_users": top_users,
        "period_days": days
    }


@router.get("/stats/feedback")
async def get_feedback_stats(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_admin_user)
):
    """
    Get feedback statistics
    获取反馈统计

    Returns:
        Feedback statistics with status distribution
    """
    # Status distribution
    # 状态分布
    status_query = select(
        Feedback.status,
        func.count(Feedback.id).label("count")
    ).group_by(Feedback.status)

    status_result = await db.execute(status_query)
    status_rows = status_result.all()

    total_count = sum(row.count for row in status_rows)
    status_distribution = {
        row.status: {
            "count": row.count,
            "percentage": round(row.count / total_count * 100, 1) if total_count > 0 else 0
        }
        for row in status_rows
    }

    # Recent feedbacks
    # 最近反馈
    recent_query = select(Feedback).order_by(Feedback.created_at.desc()).limit(20)
    recent_result = await db.execute(recent_query)
    recent_feedbacks = recent_result.scalars().all()

    recent_list = [
        {
            "id": f.id,
            "contact": f.contact,
            "content": f.content[:100] + "..." if len(f.content) > 100 else f.content,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None
        }
        for f in recent_feedbacks
    ]

    return {
        "total_feedbacks": total_count,
        "status_distribution": status_distribution,
        "pending_count": status_distribution.get("pending", {}).get("count", 0),
        "recent_feedbacks": recent_list
    }


# ==========================================
# Anomaly Detection Endpoints
# 异常检测端点
# ==========================================

import statistics


class OrderPoint(BaseModel):
    """Order data point for scatter chart 订单数据点（散点图用）"""
    task_id: str
    price: float
    calls: int
    is_anomaly: bool
    word_count: Optional[int] = None


class HistogramBin(BaseModel):
    """Histogram bin for distribution chart 直方图分组"""
    range_label: str
    range_min: int
    range_max: int
    count: int
    is_above_threshold: bool


class DistributionStats(BaseModel):
    """Distribution statistics 分布统计"""
    mean: float
    std: float
    threshold: float
    sigma: float
    total_count: int


class PriceRangeStats(BaseModel):
    """Statistics for a price range 价格区间统计"""
    range_label: str
    min_price: float
    max_price: float
    task_count: int
    mean_calls: float
    std_calls: float
    threshold: float
    anomaly_count: int


class AnomalyOrder(BaseModel):
    """Anomaly order detail 异常订单详情"""
    task_id: str
    user_id: Optional[str]
    price_final: float
    api_call_count: int
    expected_calls: float
    deviation: float
    word_count: Optional[int]
    created_at: str
    status: str


def calculate_stats(call_counts: List[int], sigma: float = 2.0) -> Optional[Dict[str, float]]:
    """
    Calculate mean, std, and threshold for anomaly detection
    计算均值、标准差和异常阈值
    """
    if len(call_counts) < 2:
        return None

    mean = statistics.mean(call_counts)
    std = statistics.stdev(call_counts) if len(call_counts) > 1 else 0
    threshold = mean + sigma * std

    return {
        "mean": round(mean, 2),
        "std": round(std, 2),
        "threshold": round(threshold, 2),
        "sigma": sigma
    }


@router.get("/anomaly/overview")
async def get_anomaly_overview(
    sigma: float = Query(2.0, description="Standard deviation multiplier | 标准差倍数", ge=1.0, le=4.0),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_admin_user)
):
    """
    Get anomaly detection overview
    获取异常检测概览

    Returns:
        Overview statistics with anomaly count and price range breakdown
    """
    # Get all tasks with price and api_call_count
    # 获取所有有价格和调用次数的任务
    query = select(Task).where(
        and_(
            Task.price_final.isnot(None),
            Task.price_final > 0
        )
    )
    result = await db.execute(query)
    tasks = result.scalars().all()

    if not tasks:
        return {
            "total_tasks": 0,
            "anomaly_count": 0,
            "anomaly_rate": 0,
            "price_ranges": []
        }

    # Define price ranges
    # 定义价格区间
    price_ranges_def = [
        (50, 100, "¥50-100"),
        (100, 200, "¥100-200"),
        (200, 500, "¥200-500"),
        (500, 1000, "¥500-1000"),
        (1000, float('inf'), "¥1000+")
    ]

    price_ranges_stats = []
    total_anomalies = 0

    for min_p, max_p, label in price_ranges_def:
        tasks_in_range = [
            t for t in tasks
            if min_p <= (t.price_final or 0) < max_p
        ]

        if not tasks_in_range:
            continue

        call_counts = [t.api_call_count or 0 for t in tasks_in_range]
        stats = calculate_stats(call_counts, sigma)

        if stats:
            threshold = stats["threshold"]
            anomalies = [t for t in tasks_in_range if (t.api_call_count or 0) > threshold]
            anomaly_count = len(anomalies)
            total_anomalies += anomaly_count

            price_ranges_stats.append(PriceRangeStats(
                range_label=label,
                min_price=min_p,
                max_price=min(max_p, 99999),
                task_count=len(tasks_in_range),
                mean_calls=stats["mean"],
                std_calls=stats["std"],
                threshold=stats["threshold"],
                anomaly_count=anomaly_count
            ))

    total_tasks = len(tasks)
    anomaly_rate = round(total_anomalies / total_tasks * 100, 2) if total_tasks > 0 else 0

    return {
        "total_tasks": total_tasks,
        "anomaly_count": total_anomalies,
        "anomaly_rate": anomaly_rate,
        "sigma": sigma,
        "price_ranges": [pr.model_dump() for pr in price_ranges_stats]
    }


@router.get("/anomaly/distribution")
async def get_anomaly_distribution(
    min_price: Optional[float] = Query(None, description="Minimum price filter | 最小金额"),
    max_price: Optional[float] = Query(None, description="Maximum price filter | 最大金额"),
    sigma: float = Query(2.0, description="Standard deviation multiplier | 标准差倍数", ge=1.0, le=4.0),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_admin_user)
):
    """
    Get order distribution data for charts
    获取订单分布数据（用于图表）

    Returns:
        Scatter plot data, histogram data, and statistics
    """
    # Build query with optional price filters
    # 构建带可选价格筛选的查询
    conditions = [
        Task.price_final.isnot(None),
        Task.price_final > 0
    ]

    if min_price is not None:
        conditions.append(Task.price_final >= min_price)
    if max_price is not None:
        conditions.append(Task.price_final <= max_price)

    query = select(Task).where(and_(*conditions))
    result = await db.execute(query)
    tasks = result.scalars().all()

    if not tasks:
        return {
            "scatter_data": [],
            "histogram_data": [],
            "stats": None
        }

    # Calculate statistics
    # 计算统计值
    call_counts = [t.api_call_count or 0 for t in tasks]
    stats = calculate_stats(call_counts, sigma)

    if not stats:
        return {
            "scatter_data": [],
            "histogram_data": [],
            "stats": None
        }

    threshold = stats["threshold"]

    # Build scatter plot data
    # 构建散点图数据
    scatter_data = [
        OrderPoint(
            task_id=t.task_id,
            price=float(t.price_final or 0),
            calls=t.api_call_count or 0,
            is_anomaly=(t.api_call_count or 0) > threshold,
            word_count=t.word_count_billable
        ).model_dump()
        for t in tasks
    ]

    # Build histogram data
    # 构建直方图数据
    max_calls = max(call_counts) if call_counts else 0
    bin_size = max(10, int(max_calls / 10)) if max_calls > 0 else 10

    histogram_bins = []
    for bin_start in range(0, max(int(max_calls) + bin_size, bin_size), bin_size):
        bin_end = bin_start + bin_size
        count = len([c for c in call_counts if bin_start <= c < bin_end])
        if count > 0 or bin_start == 0:
            histogram_bins.append(HistogramBin(
                range_label=f"{bin_start}-{bin_end}",
                range_min=bin_start,
                range_max=bin_end,
                count=count,
                is_above_threshold=bin_start >= threshold
            ).model_dump())

    return {
        "scatter_data": scatter_data,
        "histogram_data": histogram_bins,
        "stats": DistributionStats(
            mean=stats["mean"],
            std=stats["std"],
            threshold=stats["threshold"],
            sigma=sigma,
            total_count=len(tasks)
        ).model_dump()
    }


@router.get("/anomaly/orders")
async def get_anomaly_orders(
    min_price: Optional[float] = Query(None, description="Minimum price filter | 最小金额"),
    max_price: Optional[float] = Query(None, description="Maximum price filter | 最大金额"),
    sigma: float = Query(2.0, description="Standard deviation multiplier | 标准差倍数", ge=1.0, le=4.0),
    page: int = Query(1, description="Page number", ge=1),
    page_size: int = Query(20, description="Items per page", ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_admin_user)
):
    """
    Get list of anomaly orders with details
    获取异常订单列表及详情

    Returns:
        Paginated list of anomaly orders
    """
    # Build query with optional price filters
    # 构建带可选价格筛选的查询
    conditions = [
        Task.price_final.isnot(None),
        Task.price_final > 0
    ]

    if min_price is not None:
        conditions.append(Task.price_final >= min_price)
    if max_price is not None:
        conditions.append(Task.price_final <= max_price)

    query = select(Task).where(and_(*conditions))
    result = await db.execute(query)
    tasks = result.scalars().all()

    if not tasks:
        return {
            "orders": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "stats": None
        }

    # Calculate statistics
    # 计算统计值
    call_counts = [t.api_call_count or 0 for t in tasks]
    stats = calculate_stats(call_counts, sigma)

    if not stats:
        return {
            "orders": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "stats": None
        }

    threshold = stats["threshold"]
    mean = stats["mean"]

    # Filter anomaly orders
    # 筛选异常订单
    anomaly_tasks = [
        t for t in tasks
        if (t.api_call_count or 0) > threshold
    ]

    # Sort by deviation (highest first)
    # 按偏离程度排序（最高优先）
    anomaly_tasks.sort(
        key=lambda t: (t.api_call_count or 0) / max(mean, 1),
        reverse=True
    )

    # Paginate
    # 分页
    total = len(anomaly_tasks)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_tasks = anomaly_tasks[start_idx:end_idx]

    # Build response
    # 构建响应
    orders = [
        AnomalyOrder(
            task_id=t.task_id,
            user_id=t.user_id,
            price_final=float(t.price_final or 0),
            api_call_count=t.api_call_count or 0,
            expected_calls=mean,
            deviation=round((t.api_call_count or 0) / max(mean, 1), 2),
            word_count=t.word_count_billable,
            created_at=t.created_at.isoformat() if t.created_at else "",
            status=t.status or "unknown"
        ).model_dump()
        for t in paginated_tasks
    ]

    return {
        "orders": orders,
        "total": total,
        "page": page,
        "page_size": page_size,
        "stats": {
            "mean": mean,
            "std": stats["std"],
            "threshold": threshold,
            "sigma": sigma
        }
    }
