"""
Export API routes
导出API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import json
from datetime import datetime

from src.db.database import get_db
from src.db.models import Document, Session, Sentence, Modification
from src.api.schemas import ExportResult

router = APIRouter()


@router.post("/document", response_model=ExportResult)
async def export_document(
    session_id: str,
    format: str = "txt",
    db: AsyncSession = Depends(get_db)
):
    """
    Export processed document
    导出处理后的文档
    """
    # Get session
    # 获取会话
    session_result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get document
    # 获取文档
    doc_result = await db.execute(
        select(Document).where(Document.id == session.document_id)
    )
    doc = doc_result.scalar_one_or_none()

    # Get all sentences with modifications
    # 获取所有句子及其修改
    sentences_result = await db.execute(
        select(Sentence)
        .where(Sentence.document_id == session.document_id)
        .order_by(Sentence.index)
    )
    sentences = sentences_result.scalars().all()

    # Get accepted modifications
    # 获取已接受的修改
    mods_result = await db.execute(
        select(Modification)
        .where(Modification.session_id == session_id)
        .where(Modification.accepted == True)
    )
    modifications = {m.sentence_id: m for m in mods_result.scalars().all()}

    # Build final text
    # 构建最终文本
    final_sentences = []
    for sentence in sentences:
        if sentence.id in modifications:
            final_sentences.append(modifications[sentence.id].modified_text)
        else:
            final_sentences.append(sentence.original_text)

    final_text = " ".join(final_sentences)

    # Create export file
    # 创建导出文件
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{doc.filename.rsplit('.', 1)[0]}_{timestamp}.{format}"
    filepath = os.path.join(export_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_text)

    file_size = os.path.getsize(filepath)

    return ExportResult(
        filename=filename,
        format=format,
        size=file_size,
        download_url=f"/api/v1/export/download/{filename}"
    )


@router.post("/report", response_model=ExportResult)
async def export_report(
    session_id: str,
    format: str = "json",
    db: AsyncSession = Depends(get_db)
):
    """
    Export analysis and modification report
    导出分析和修改报告
    """
    # Get session
    # 获取会话
    session_result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all sentences
    # 获取所有句子
    sentences_result = await db.execute(
        select(Sentence)
        .where(Sentence.document_id == session.document_id)
        .order_by(Sentence.index)
    )
    sentences = sentences_result.scalars().all()

    # Get all modifications
    # 获取所有修改
    mods_result = await db.execute(
        select(Modification).where(Modification.session_id == session_id)
    )
    modifications = {m.sentence_id: m for m in mods_result.scalars().all()}

    # Build report
    # 构建报告
    report = {
        "session_id": session_id,
        "document_id": session.document_id,
        "mode": session.mode,
        "colloquialism_level": session.colloquialism_level,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "statistics": {
            "total_sentences": len(sentences),
            "high_risk": len([s for s in sentences if s.risk_level == "high"]),
            "medium_risk": len([s for s in sentences if s.risk_level == "medium"]),
            "low_risk": len([s for s in sentences if s.risk_level == "low"]),
            "modified": len([m for m in modifications.values() if m.accepted]),
            "skipped": len([m for m in modifications.values() if m.source == "skip"]),
            "flagged": len([m for m in modifications.values() if m.source == "flag"])
        },
        "sentences": []
    }

    for sentence in sentences:
        sentence_report = {
            "index": sentence.index,
            "original": sentence.original_text,
            "risk_score": sentence.risk_score,
            "risk_level": sentence.risk_level,
            "analysis": sentence.analysis_json
        }

        if sentence.id in modifications:
            mod = modifications[sentence.id]
            sentence_report["modification"] = {
                "source": mod.source,
                "modified_text": mod.modified_text,
                "changes": mod.changes_json,
                "semantic_similarity": mod.semantic_similarity,
                "new_risk_score": mod.new_risk_score,
                "accepted": mod.accepted
            }

        report["sentences"].append(sentence_report)

    # Create export file
    # 创建导出文件
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{session_id[:8]}_{timestamp}.{format}"
    filepath = os.path.join(export_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        if format == "json":
            json.dump(report, f, ensure_ascii=False, indent=2)
        else:
            # Simple text format
            # 简单文本格式
            f.write(f"AcademicGuard Report\n")
            f.write(f"=" * 50 + "\n\n")
            f.write(f"Session: {session_id}\n")
            f.write(f"Total Sentences: {report['statistics']['total_sentences']}\n")
            f.write(f"Modified: {report['statistics']['modified']}\n\n")

    file_size = os.path.getsize(filepath)

    return ExportResult(
        filename=filename,
        format=format,
        size=file_size,
        download_url=f"/api/v1/export/download/{filename}"
    )


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download exported file
    下载导出的文件
    """
    filepath = os.path.join("exports", filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/octet-stream"
    )
