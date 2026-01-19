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
import re

from src.db.database import get_db
from src.db.models import Document, Session, Sentence, Modification, SubstepState
from src.api.schemas import ExportResult

# Import python-docx for Word document export
# 导入python-docx用于Word文档导出
try:
    from docx import Document as DocxDocument
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

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

    # First, try to get modified text from SubstepState (5-layer analysis)
    # 首先尝试从SubstepState获取修改后的文本（5层分析）
    final_text = None

    # Steps to check for modified text (from last to first)
    # 检查修改文本的步骤顺序（从最后到最先）
    STEP_ORDER = [
        'step5-5', 'step5-4', 'step5-3', 'step5-2', 'step5-1', 'step5-0',  # Layer 1
        'step4-console', 'step4-5', 'step4-4', 'step4-3', 'step4-2', 'step4-1', 'step4-0',  # Layer 2
        'step3-5', 'step3-4', 'step3-3', 'step3-2', 'step3-1', 'step3-0',  # Layer 3
        'step2-5', 'step2-4', 'step2-3', 'step2-2', 'step2-1', 'step2-0',  # Layer 4
        'step1-5', 'step1-4', 'step1-3', 'step1-2', 'step1-1',  # Layer 5
    ]

    # Query all substep states for this session
    # 查询此会话的所有子步骤状态
    substep_result = await db.execute(
        select(SubstepState)
        .where(SubstepState.session_id == session_id)
        .where(SubstepState.modified_text.isnot(None))
    )
    substep_states = {s.step_name: s for s in substep_result.scalars().all()}

    # Find the last step with modified text
    # 找到最后一个有修改文本的步骤
    for step_name in STEP_ORDER:
        if step_name in substep_states and substep_states[step_name].modified_text:
            final_text = substep_states[step_name].modified_text
            print(f"[Export] Using modified text from {step_name}")
            break

    # If no substep state found, fall back to old method (Sentence/Modification)
    # 如果没有找到子步骤状态，回退到旧方法
    if not final_text:
        print("[Export] No substep state found, falling back to Sentence/Modification method")

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

        # Build final text with paragraph breaks
        # 构建带段落分隔的最终文本
        paragraphs_dict = {}  # Group sentences by paragraph
        for sentence in sentences:
            # Get paragraph index from analysis_json
            # 从analysis_json获取段落索引
            para_idx = 0
            if sentence.analysis_json:
                para_idx = sentence.analysis_json.get("paragraph_index", 0) or 0

            if para_idx not in paragraphs_dict:
                paragraphs_dict[para_idx] = []

            # Get sentence text (modified or original)
            # 获取句子文本（已修改或原始）
            if sentence.id in modifications:
                paragraphs_dict[para_idx].append(modifications[sentence.id].modified_text)
            else:
                paragraphs_dict[para_idx].append(sentence.original_text)

        # Join sentences within paragraphs with space, paragraphs with double newline
        # 段落内句子用空格连接，段落间用双换行
        final_paragraphs = []
        for para_idx in sorted(paragraphs_dict.keys()):
            para_text = " ".join(paragraphs_dict[para_idx])
            final_paragraphs.append(para_text)

        final_text = "\n\n".join(final_paragraphs)

    # If still no text, use original document text
    # 如果仍然没有文本，使用原始文档文本
    if not final_text:
        final_text = doc.original_text or ""
        print("[Export] Using original document text")

    # Create export file
    # 创建导出文件
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Clean up filename: remove yolo_step prefixes recursively
    # 清理文件名：递归移除yolo_step前缀
    base_name = doc.filename.rsplit('.', 1)[0]
    clean_name = base_name
    while clean_name.startswith('yolo_step') or clean_name.startswith('yolo_'):
        clean_name = re.sub(r'^(yolo_)?step[\d\-]+_', '', clean_name)
        # Also handle bare 'yolo_' prefix just in case
        if clean_name.startswith('yolo_') and not clean_name.startswith('yolo_step'):
             clean_name = clean_name[5:]

    if not clean_name:
        clean_name = "document"

    # Add prefix based on status
    # 根据状态添加前缀
    prefix = "processed" if session.status == "completed" else "partial"
    final_filename_base = f"{prefix}_{clean_name}_{timestamp}"

    # Handle docx format with python-docx
    # 使用python-docx处理docx格式
    if format == "docx":
        if not DOCX_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="python-docx library not installed. Please install it with: pip install python-docx"
            )

        filename = f"{final_filename_base}.docx"
        filepath = os.path.join(export_dir, filename)

        # Create Word document with proper paragraph formatting
        # 创建带有正确段落格式的Word文档
        docx_doc = DocxDocument()

        # Set default font style
        # 设置默认字体样式
        style = docx_doc.styles['Normal']
        font = style.font
        font.size = Pt(12)

        # Add each paragraph as a separate Word paragraph
        # 将每个段落添加为单独的Word段落
        for para_text in final_paragraphs:
            if para_text.strip():
                docx_doc.add_paragraph(para_text.strip())

        docx_doc.save(filepath)
    else:
        # Text format (txt or other)
        # 文本格式（txt或其他）
        filename = f"{final_filename_base}.{format}"
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
