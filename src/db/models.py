"""
SQLAlchemy ORM Models
数据库ORM模型
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.database import Base
import uuid


def generate_uuid():
    """Generate UUID string"""
    return str(uuid.uuid4())


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

    # Relationships
    sentences = relationship("Sentence", back_populates="document", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="document", cascade="all, delete-orphan")


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
    current_index = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="sessions")
    modifications = relationship("Modification", back_populates="session", cascade="all, delete-orphan")


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
