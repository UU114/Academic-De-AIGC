"""
SQLAlchemy ORM Models
数据库ORM模型
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.database import Base
import uuid
from enum import Enum


def generate_uuid():
    """Generate UUID string"""
    return str(uuid.uuid4())


# ==========================================
# Task and Payment Status Enums
# 任务和支付状态枚举
# ==========================================

class TaskStatus(str, Enum):
    """
    Task status enumeration
    任务状态枚举
    """
    CREATED = "created"        # Just created, not quoted
    QUOTED = "quoted"          # Quoted, awaiting payment
    PAYING = "paying"          # Payment in progress
    PAID = "paid"              # Paid, ready for processing
    PROCESSING = "processing"  # Processing in progress
    COMPLETED = "completed"    # Processing completed
    EXPIRED = "expired"        # Expired (unpaid timeout)
    FAILED = "failed"          # Processing failed


class PaymentStatus(str, Enum):
    """
    Payment status enumeration
    支付状态枚举
    """
    UNPAID = "unpaid"
    PENDING = "pending"        # Payment processing
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


# ==========================================
# User Model (for platform user local cache)
# 用户模型（平台用户本地缓存）
# ==========================================

class User(Base):
    """
    User model - Local user info storage
    用户模型 - 本地用户信息存储
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    platform_user_id = Column(String(64), unique=True, nullable=False)  # Central platform user ID
    phone = Column(String(20), unique=True, nullable=False)  # Phone number (used for login)
    email = Column(String(200), nullable=True)  # Email (for password recovery)
    password_hash = Column(String(256), nullable=True)  # Hashed password
    nickname = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")


# ==========================================
# Task Model (billing core)
# 任务模型（计费核心）
# ==========================================

class Task(Base):
    """
    Task model - Billable processing task
    任务模型 - 计费处理任务
    """
    __tablename__ = "tasks"

    task_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # DEBUG mode can be null
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=True)

    # File information for anti-tampering
    # 文件信息（防篡改）
    file_path_raw = Column(String(512), nullable=True)      # Original upload file path
    file_path_clean = Column(String(512), nullable=True)    # Cleaned file path
    content_hash = Column(String(64), nullable=True)        # SHA-256 hash for anti-tampering

    # Billing information
    # 计费信息
    word_count_raw = Column(Integer, nullable=True)         # Original word count
    word_count_billable = Column(Integer, nullable=True)    # Billable word count (excluding references)
    billable_units = Column(Integer, nullable=True)         # Billing units (100 words/unit)
    price_calculated = Column(Float, nullable=True)         # Calculated price
    price_final = Column(Float, nullable=True)              # Final price (>=50)
    is_minimum_charge = Column(Boolean, default=False)      # Whether minimum charge triggered

    # Status management
    # 状态管理
    status = Column(String(20), default=TaskStatus.CREATED.value)
    payment_status = Column(String(20), default=PaymentStatus.UNPAID.value)
    platform_order_id = Column(String(64), nullable=True)   # Central platform order ID

    # API call tracking for anomaly detection
    # API调用追踪（用于异常检测）
    api_call_count = Column(Integer, default=0, nullable=False)  # Number of LLM API calls

    # Timestamps
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    quoted_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)            # Expiry time for unpaid tasks

    # Relationships
    user = relationship("User", back_populates="tasks")
    document = relationship("Document", back_populates="task")
    session = relationship("Session", foreign_keys=[session_id])


class Document(Base):
    """
    Document model - stores uploaded documents
    文档模型 - 存储上传的文档
    """
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    original_text = Column(Text, nullable=False)
    processed_text = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, analyzing, ready, completed
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Analysis cache fields (避免重复LLM调用)
    # Analysis cache fields (avoid repeated LLM calls)
    structure_analysis_cache = Column(JSON, nullable=True)  # Step 1: Structure analysis cache
    transition_analysis_cache = Column(JSON, nullable=True)  # Step 2: Transition analysis cache

    # Relationships
    sentences = relationship("Sentence", back_populates="document", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="document", cascade="all, delete-orphan")
    task = relationship("Task", back_populates="document", uselist=False)  # One-to-one with Task


class Session(Base):
    """
    Session model - stores processing sessions
    会话模型 - 存储处理会话
    """
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    mode = Column(String(20), nullable=False)  # intervention, yolo
    colloquialism_level = Column(Integer, default=4)
    target_lang = Column(String(10), default="zh")
    config_json = Column(JSON, nullable=True)
    status = Column(String(20), default="active")  # active, paused, completed
    current_step = Column(String(20), default="step1-1")  # step1-1, step1-2, step2, step3, review
    current_index = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="sessions")
    modifications = relationship("Modification", back_populates="session", cascade="all, delete-orphan")
    substep_states = relationship("SubstepState", back_populates="session", cascade="all, delete-orphan")


class Sentence(Base):
    """
    Sentence model - stores individual sentences from documents
    句子模型 - 存储文档中的单个句子
    """
    __tablename__ = "sentences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    index = Column(Integer, nullable=False)
    original_text = Column(Text, nullable=False)
    analysis_json = Column(JSON, nullable=True)
    risk_score = Column(Integer, nullable=True)
    risk_level = Column(String(10), nullable=True)  # safe, low, medium, high
    content_type = Column(String(20), default="sentence")  # sentence, title, section, table_header, figure, reference, metadata, fragment
    should_process = Column(Boolean, default=True)  # Whether this sentence should be processed for AIGC detection
    locked_terms_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="sentences")
    modifications = relationship("Modification", back_populates="sentence", cascade="all, delete-orphan")


class Modification(Base):
    """
    Modification model - stores sentence modifications
    修改模型 - 存储句子的修改记录
    """
    __tablename__ = "modifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sentence_id = Column(String(36), ForeignKey("sentences.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    source = Column(String(10), nullable=False)  # llm, rule, custom
    modified_text = Column(Text, nullable=False)
    changes_json = Column(JSON, nullable=True)
    validation_json = Column(JSON, nullable=True)
    semantic_similarity = Column(Float, nullable=True)
    new_risk_score = Column(Integer, nullable=True)
    accepted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    sentence = relationship("Sentence", back_populates="modifications")
    session = relationship("Session", back_populates="modifications")


class FingerprintWord(Base):
    """
    Fingerprint word model - stores AI fingerprint vocabulary
    指纹词模型 - 存储AI指纹词汇
    """
    __tablename__ = "fingerprint_words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=True)  # high_freq, phrase, academic
    risk_weight = Column(Float, default=1.0)
    replacements_json = Column(JSON, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TermWhitelist(Base):
    """
    Term whitelist model - stores protected academic terms
    术语白名单模型 - 存储受保护的学术术语
    """
    __tablename__ = "term_whitelist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(200), nullable=False)
    domain = Column(String(50), nullable=True)  # cs, biology, physics, etc.
    user_defined = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


# ==========================================
# Feedback Model (user feedback collection)
# 反馈模型（用户反馈收集）
# ==========================================

class Feedback(Base):
    """
    Feedback model - stores user feedback and issue reports
    反馈模型 - 存储用户反馈和问题报告
    """
    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contact = Column(String(200), nullable=True)  # Contact info (email/phone/wechat)
    content = Column(Text, nullable=False)  # Feedback content
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Optional logged-in user
    ip_address = Column(String(50), nullable=True)  # Client IP for spam prevention
    user_agent = Column(String(500), nullable=True)  # Browser info
    status = Column(String(20), default="pending")  # pending, reviewed, resolved, spam
    admin_notes = Column(Text, nullable=True)  # Admin notes for internal use
    created_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime, nullable=True)


# ==========================================
# Substep State Model (substep cache)
# 子步骤状态模型（子步骤缓存）
# ==========================================

class SubstepState(Base):
    """
    Substep state model - caches substep analysis results and user inputs
    子步骤状态模型 - 缓存子步骤分析结果和用户输入

    This avoids redundant LLM calls when user navigates back to previous steps.
    当用户返回上一步骤时，避免重复调用LLM。
    """
    __tablename__ = "substep_states"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    step_name = Column(String(50), nullable=False)  # e.g., "layer5-step1-1", "layer4-step2-0"

    # Analysis result from LLM (cached)
    # LLM分析结果（缓存）
    analysis_result = Column(JSON, nullable=True)

    # User inputs/selections for this step
    # 用户在此步骤的输入/选择
    user_inputs = Column(JSON, nullable=True)  # e.g., {"selectedIssues": [...], "userNotes": "..."}

    # Modified text (if any modification was applied)
    # 修改后的文本（如果应用了修改）
    modified_text = Column(Text, nullable=True)

    # Step completion status
    # 步骤完成状态
    status = Column(String(20), default="pending")  # pending, completed, skipped

    # Timestamps
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    session = relationship("Session", back_populates="substep_states")
