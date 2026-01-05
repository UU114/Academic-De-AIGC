"""
Document management API routes
文档管理API路由

CAASS v2.0 Phase 2: Added paragraph context baseline and whitelist extraction
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Optional

from src.db.database import get_db
from src.db.models import Document, Sentence as SentenceModel
from src.api.schemas import DocumentInfo
from src.core.preprocessor.segmenter import SentenceSegmenter
from src.core.preprocessor.reference_handler import ReferenceHandler
from src.core.preprocessor.paraphrase_detector import ParaphraseDetector
from src.core.analyzer.scorer import RiskScorer, ParagraphContext, calculate_context_baseline
from src.core.preprocessor.whitelist_extractor import WhitelistExtractor

router = APIRouter()
segmenter = SentenceSegmenter()
ref_handler = ReferenceHandler()
paraphrase_detector = ParaphraseDetector()
scorer = RiskScorer()
whitelist_extractor = WhitelistExtractor()


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

    CAASS v2.0 Phase 2: Uses paragraph context baseline and whitelist extraction

    Security (安全措施):
    - File size limit: max_file_size_mb (default 5MB)
    - File type validation: .txt and .docx only
    """
    from src.config import get_settings
    settings = get_settings()

    # Security: Validate file type
    # 安全：验证文件类型
    filename = file.filename or "unnamed.txt"
    allowed_extensions = ['.txt', '.docx']
    file_ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_file_type",
                "message": f"Only {', '.join(allowed_extensions)} files are allowed",
                "message_zh": f"仅支持 {', '.join(allowed_extensions)} 格式文件"
            }
        )

    # Read file content
    # 读取文件内容
    content = await file.read()

    # Security: Validate file size (防止格式炸弹)
    # 安全：验证文件大小
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "file_too_large",
                "message": f"File size exceeds {settings.max_file_size_mb}MB limit",
                "message_zh": f"文件大小超过 {settings.max_file_size_mb}MB 限制"
            }
        )

    # Try to decode as UTF-8, fallback to latin-1
    # 尝试UTF-8解码，回退到latin-1
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    doc_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # CAASS v2.0 Phase 2: Extract whitelist from document
    # CAASS v2.0 第二阶段：从文档提取白名单
    whitelist_result = whitelist_extractor.extract_from_document(text)
    whitelist_terms = whitelist_result.terms

    # Create document record with status "analyzing"
    # 创建文档记录，状态为"analyzing"
    doc = Document(
        id=doc_id,
        filename=filename,
        original_text=text,
        status="analyzing"
    )
    db.add(doc)
    await db.commit()

    # Extract reference section
    # 提取参考文献部分
    body_text, ref_section = ref_handler.extract(text)

    # CAASS v2.0 Phase 2: Segment text with paragraph info
    # CAASS v2.0 第二阶段：带段落信息分割文本
    # Only segment the body text
    sentences = segmenter.segment_with_paragraphs(body_text)

    # Build paragraph contexts for context baseline calculation
    # 构建段落上下文用于计算上下文基准
    paragraph_contexts = _build_paragraph_contexts(sentences)

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
            # Get paragraph context for this sentence
            # 获取该句子的段落上下文
            para_ctx = paragraph_contexts.get(sent.paragraph_index)

            # Analyze sentence risk (CAASS v2.0 Phase 2)
            # 分析句子风险（CAASS v2.0 第二阶段）
            analysis = scorer.analyze(
                sent.text,
                tone_level=4,
                whitelist=whitelist_terms,
                paragraph_context=para_ctx
            )
            
            # Detect paraphrase
            # 检测释义
            para_info = paraphrase_detector.detect(sent.text)
            
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
                    "gptzero_score": analysis.gptzero_score,
                    "paragraph_index": sent.paragraph_index,
                    "context_baseline": para_ctx.baseline if para_ctx else 0,
                    # Phase 2: Enhanced metrics
                    "burstiness_value": getattr(analysis, 'burstiness_value', 0.0),
                    "burstiness_risk": getattr(analysis, 'burstiness_risk', 'unknown'),
                    "connector_count": getattr(analysis, 'connector_count', 0),
                    "connector_word": getattr(analysis, 'connector_match', None).connector if getattr(analysis, 'connector_match', None) else None,
                    # Paraphrase info
                    "is_paraphrase": para_info.is_paraphrase
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
                    "reason": f"Content type: {sent.content_type}",
                    "paragraph_index": sent.paragraph_index
                }
            )

        db.add(sentence_record)

    # Add reference section as a special sentence if it exists
    # 如果存在参考文献部分，将其作为特殊句子添加
    if ref_section:
        ref_sentence_id = str(uuid.uuid4())
        ref_sentence = SentenceModel(
            id=ref_sentence_id,
            document_id=doc_id,
            index=len(sentences),  # Append at the end
            original_text=ref_section,
            content_type="reference_section",
            should_process=False,
            risk_score=0,
            risk_level="safe",
            analysis_json={
                "filtered": True,
                "reason": "Reference Section",
                "is_reference_blob": True
            }
        )
        db.add(ref_sentence)

    # Update document status to "ready" and store whitelist
    # 更新文档状态为"ready"并存储白名单
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


def _build_paragraph_contexts(sentences) -> Dict[int, ParagraphContext]:
    """
    Build paragraph contexts from sentences
    从句子构建段落上下文

    Groups sentences by paragraph_index and creates ParagraphContext for each.
    按 paragraph_index 分组句子并为每个创建 ParagraphContext。
    """
    # Group sentences by paragraph
    # 按段落分组句子
    paragraphs: Dict[int, List[str]] = {}
    for sent in sentences:
        para_idx = sent.paragraph_index or 0
        if para_idx not in paragraphs:
            paragraphs[para_idx] = []
        if sent.should_process:
            paragraphs[para_idx].append(sent.text)

    # Build context for each paragraph
    # 为每个段落构建上下文
    contexts = {}
    for para_idx, sent_texts in paragraphs.items():
        if sent_texts:
            contexts[para_idx] = ParagraphContext.from_sentences(sent_texts)

    return contexts


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

    CAASS v2.0 Phase 2: Uses paragraph context baseline and whitelist extraction
    """
    doc_id = str(uuid.uuid4())

    # CAASS v2.0 Phase 2: Extract whitelist from text
    # CAASS v2.0 第二阶段：从文本提取白名单
    whitelist_result = whitelist_extractor.extract_from_document(text)
    whitelist_terms = whitelist_result.terms

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

    # Extract reference section
    # 提取参考文献部分
    body_text, ref_section = ref_handler.extract(text)

    # CAASS v2.0 Phase 2: Segment text with paragraph info
    # CAASS v2.0 第二阶段：带段落信息分割文本
    sentences = segmenter.segment_with_paragraphs(body_text)

    # Build paragraph contexts for context baseline calculation
    # 构建段落上下文用于计算上下文基准
    paragraph_contexts = _build_paragraph_contexts(sentences)

    high_count = 0
    medium_count = 0
    low_count = 0

    for sent in sentences:
        sentence_id = str(uuid.uuid4())

        if sent.should_process:
            # Get paragraph context for this sentence
            # 获取该句子的段落上下文
            para_ctx = paragraph_contexts.get(sent.paragraph_index)

            # CAASS v2.0 Phase 2: Use paragraph context and whitelist
            # CAASS v2.0 第二阶段：使用段落上下文和白名单
            analysis = scorer.analyze(
                sent.text,
                tone_level=4,
                whitelist=whitelist_terms,
                paragraph_context=para_ctx
            )
            
            # Detect paraphrase
            # 检测释义
            para_info = paraphrase_detector.detect(sent.text)
            
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
                    "paragraph_index": sent.paragraph_index,
                    "context_baseline": para_ctx.baseline if para_ctx else 0,
                    # Phase 2: Enhanced metrics
                    "burstiness_value": getattr(analysis, 'burstiness_value', 0.0),
                    "burstiness_risk": getattr(analysis, 'burstiness_risk', 'unknown'),
                    "connector_count": getattr(analysis, 'connector_count', 0),
                    "connector_word": getattr(analysis, 'connector_match', None).connector if getattr(analysis, 'connector_match', None) else None,
                    # Paraphrase info
                    "is_paraphrase": para_info.is_paraphrase
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
                analysis_json={
                    "filtered": True,
                    "reason": f"Content type: {sent.content_type}",
                    "paragraph_index": sent.paragraph_index
                }
            )

        db.add(sentence_record)

    # Add reference section as a special sentence if it exists
    # 如果存在参考文献部分，将其作为特殊句子添加
    if ref_section:
        ref_sentence_id = str(uuid.uuid4())
        ref_sentence = SentenceModel(
            id=ref_sentence_id,
            document_id=doc_id,
            index=len(sentences),
            original_text=ref_section,
            content_type="reference_section",
            should_process=False,
            risk_score=0,
            risk_level="safe",
            analysis_json={
                "filtered": True,
                "reason": "Reference Section",
                "is_reference_blob": True
            }
        )
        db.add(ref_sentence)

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
