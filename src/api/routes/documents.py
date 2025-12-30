"""
Document management API routes
文档管理API路由
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.db.database import get_db
from src.db.models import Document, Sentence as SentenceModel
from src.api.schemas import DocumentInfo
from src.core.preprocessor.segmenter import SentenceSegmenter
from src.core.analyzer.scorer import RiskScorer

router = APIRouter()
segmenter = SentenceSegmenter()
scorer = RiskScorer()


@router.get("/", response_model=List[DocumentInfo])
async def list_documents(
    db: AsyncSession = Depends(get_db)
):
    """
    List all documents
    列出所有文档
    """
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()

    documents = []
    for doc in docs:
        # Count sentences by risk level
        # 按风险等级统计句子
        sentences_result = await db.execute(
            select(SentenceModel).where(SentenceModel.document_id == doc.id)
        )
        sentences = sentences_result.scalars().all()

        high_count = sum(1 for s in sentences if s.risk_level == "high")
        medium_count = sum(1 for s in sentences if s.risk_level == "medium")
        low_count = sum(1 for s in sentences if s.risk_level == "low")

        documents.append(DocumentInfo(
            id=doc.id,
            filename=doc.filename,
            status=doc.status,
            total_sentences=len(sentences),
            high_risk_count=high_count,
            medium_risk_count=medium_count,
            low_risk_count=low_count,
            created_at=doc.created_at
        ))

    return documents


@router.post("/upload", response_model=DocumentInfo)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document for processing
    上传文档进行处理
    """
    # Read file content
    # 读取文件内容
    content = await file.read()

    # Try to decode as UTF-8, fallback to latin-1
    # 尝试UTF-8解码，回退到latin-1
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    doc_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Create document record with status "analyzing"
    # 创建文档记录，状态为"analyzing"
    doc = Document(
        id=doc_id,
        filename=file.filename or "unnamed.txt",
        original_text=text,
        status="analyzing"
    )
    db.add(doc)
    await db.commit()

    # Segment text into sentences
    # 将文本分割为句子
    sentences = segmenter.segment(text)

    # Analyze each sentence and create records
    # 分析每个句子并创建记录
    high_count = 0
    medium_count = 0
    low_count = 0

    # Track processable sentence count for statistics
    # 跟踪可处理句子数量用于统计
    processable_count = 0

    for sent in sentences:
        sentence_id = str(uuid.uuid4())

        # Only analyze sentences that should be processed
        # 只分析应该处理的句子
        if sent.should_process:
            # Analyze sentence risk
            # 分析句子风险
            analysis = scorer.analyze(sent.text)
            processable_count += 1

            # Create sentence record with analysis
            # 创建带分析的句子记录
            sentence_record = SentenceModel(
                id=sentence_id,
                document_id=doc_id,
                index=sent.index,
                original_text=sent.text,
                content_type=sent.content_type,
                should_process=True,
                risk_score=analysis.risk_score,
                risk_level=analysis.risk_level,
                analysis_json={
                    "ppl": analysis.ppl,
                    "ppl_risk": analysis.ppl_risk,
                    "fingerprint_density": analysis.fingerprint_density,
                    "turnitin_score": analysis.turnitin_score,
                    "gptzero_score": analysis.gptzero_score
                }
            )

            # Count risk levels only for processable sentences
            # 只统计可处理句子的风险等级
            if analysis.risk_level == "high":
                high_count += 1
            elif analysis.risk_level == "medium":
                medium_count += 1
            else:
                low_count += 1
        else:
            # Create sentence record without analysis (filtered content)
            # 创建不带分析的句子记录（过滤内容）
            sentence_record = SentenceModel(
                id=sentence_id,
                document_id=doc_id,
                index=sent.index,
                original_text=sent.text,
                content_type=sent.content_type,
                should_process=False,
                risk_score=0,
                risk_level="safe",
                analysis_json={
                    "filtered": True,
                    "reason": f"Content type: {sent.content_type}"
                }
            )

        db.add(sentence_record)

    # Update document status to "ready"
    # 更新文档状态为"ready"
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    doc_to_update = result.scalar_one()
    doc_to_update.status = "ready"
    await db.commit()

    return DocumentInfo(
        id=doc_id,
        filename=file.filename or "unnamed.txt",
        status="ready",
        total_sentences=len(sentences),
        high_risk_count=high_count,
        medium_risk_count=medium_count,
        low_risk_count=low_count,
        created_at=now
    )


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get document information
    获取文档信息
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Count sentences by risk level
    # 按风险等级统计句子
    sentences_result = await db.execute(
        select(SentenceModel).where(SentenceModel.document_id == document_id)
    )
    sentences = sentences_result.scalars().all()

    high_count = sum(1 for s in sentences if s.risk_level == "high")
    medium_count = sum(1 for s in sentences if s.risk_level == "medium")
    low_count = sum(1 for s in sentences if s.risk_level == "low")

    return DocumentInfo(
        id=doc.id,
        filename=doc.filename,
        status=doc.status,
        total_sentences=len(sentences),
        high_risk_count=high_count,
        medium_risk_count=medium_count,
        low_risk_count=low_count,
        created_at=doc.created_at
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document
    删除文档
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.delete(doc)
    await db.commit()

    return {"message": "Document deleted successfully"}


@router.post("/new/text")
async def upload_text(
    text: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload text directly (alternative to file upload)
    直接上传文本（文件上传的替代方案）
    """
    doc_id = str(uuid.uuid4())

    # Create document with status "analyzing"
    # 创建文档，状态为"analyzing"
    doc = Document(
        id=doc_id,
        filename="direct_input.txt",
        original_text=text,
        status="analyzing"
    )
    db.add(doc)
    await db.commit()

    # Segment and analyze text
    # 分割并分析文本
    sentences = segmenter.segment(text)
    high_count = 0
    medium_count = 0
    low_count = 0

    for sent in sentences:
        sentence_id = str(uuid.uuid4())

        if sent.should_process:
            analysis = scorer.analyze(sent.text)
            sentence_record = SentenceModel(
                id=sentence_id,
                document_id=doc_id,
                index=sent.index,
                original_text=sent.text,
                content_type=sent.content_type,
                should_process=True,
                risk_score=analysis.risk_score,
                risk_level=analysis.risk_level,
                analysis_json={
                    "ppl": analysis.ppl,
                    "ppl_risk": analysis.ppl_risk,
                    "fingerprint_density": analysis.fingerprint_density
                }
            )

            if analysis.risk_level == "high":
                high_count += 1
            elif analysis.risk_level == "medium":
                medium_count += 1
            else:
                low_count += 1
        else:
            sentence_record = SentenceModel(
                id=sentence_id,
                document_id=doc_id,
                index=sent.index,
                original_text=sent.text,
                content_type=sent.content_type,
                should_process=False,
                risk_score=0,
                risk_level="safe",
                analysis_json={"filtered": True, "reason": f"Content type: {sent.content_type}"}
            )

        db.add(sentence_record)

    # Update document status to "ready"
    # 更新文档状态为"ready"
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    doc_to_update = result.scalar_one()
    doc_to_update.status = "ready"
    await db.commit()

    return {
        "id": doc_id,
        "status": "ready",
        "total_sentences": len(sentences),
        "high_risk_count": high_count,
        "medium_risk_count": medium_count,
        "low_risk_count": low_count
    }
