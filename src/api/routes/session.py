"""
Session management API routes
会话管理API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from src.db.database import get_db
from src.db.models import Session, Document, Sentence, Modification
from src.api.schemas import (
    SessionStartRequest,
    SessionState,
    SessionInfo,
    ProcessMode,
    SessionStatus,
    SentenceAnalysis,
    RiskLevel
)
from typing import List

router = APIRouter()


@router.get("/list", response_model=List[SessionInfo])
async def list_sessions(
    db: AsyncSession = Depends(get_db)
):
    """
    List all sessions with document info
    列出所有会话及文档信息
    """
    result = await db.execute(
        select(Session).order_by(Session.created_at.desc())
    )
    sessions = result.scalars().all()

    session_list = []
    for sess in sessions:
        # Get document info
        # 获取文档信息
        doc_result = await db.execute(
            select(Document).where(Document.id == sess.document_id)
        )
        doc = doc_result.scalar_one_or_none()
        doc_name = doc.filename if doc else "Unknown"

        # Count modifications
        # 统计修改
        mods_result = await db.execute(
            select(Modification).where(Modification.session_id == sess.id)
        )
        modifications = mods_result.scalars().all()
        processed = len([m for m in modifications if m.accepted])

        # Get total sentences from config
        # 从配置获取总句子数
        sentence_ids = sess.config_json.get("sentence_ids", []) if sess.config_json else []
        total = len(sentence_ids)
        progress = (processed / total * 100) if total > 0 else 0

        session_list.append(SessionInfo(
            session_id=sess.id,
            document_id=sess.document_id,
            document_name=doc_name,
            mode=ProcessMode(sess.mode),
            status=sess.status,
            total_sentences=total,
            processed=processed,
            progress_percent=progress,
            created_at=sess.created_at,
            completed_at=sess.completed_at
        ))

    return session_list


@router.post("/start", response_model=SessionState)
async def start_session(
    request: SessionStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new processing session
    启动新的处理会话
    """
    # Verify document exists and is ready
    # 验证文档存在且已就绪
    doc_result = await db.execute(
        select(Document).where(Document.id == request.document_id)
    )
    doc = doc_result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Document not ready for processing. Status: {doc.status}"
        )

    # Get sentences for processing (only those marked as should_process=True)
    # 获取要处理的句子（仅标记为should_process=True的）
    sentences_result = await db.execute(
        select(Sentence)
        .where(Sentence.document_id == request.document_id)
        .where(Sentence.should_process == True)  # Only processable sentences
        .order_by(Sentence.index)
    )
    sentences = sentences_result.scalars().all()

    # Filter by risk level
    # 按风险等级过滤
    process_levels = [level.value for level in request.process_levels]
    filtered_sentences = [
        s for s in sentences
        if s.risk_level in process_levels
    ]

    # Create session
    # 创建会话
    session = Session(
        document_id=request.document_id,
        mode=request.mode.value,
        colloquialism_level=request.colloquialism_level,
        target_lang=request.target_lang,
        config_json={
            "process_levels": process_levels,
            "sentence_ids": [s.id for s in filtered_sentences]
        },
        status="active",
        current_index=0
    )
    db.add(session)
    await db.flush()

    # Get first sentence
    # 获取第一个句子
    first_sentence = filtered_sentences[0] if filtered_sentences else None

    return SessionState(
        session_id=session.id,
        document_id=request.document_id,
        mode=ProcessMode(session.mode),
        total_sentences=len(filtered_sentences),
        processed=0,
        skipped=0,
        flagged=0,
        current_index=0,
        current_sentence=_build_sentence_analysis(first_sentence) if first_sentence else None,
        suggestions=None,
        progress_percent=0.0
    )


@router.get("/{session_id}/current", response_model=SessionState)
async def get_current_state(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current session state
    获取当前会话状态
    """
    # Get session
    # 获取会话
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get sentences
    # 获取句子
    sentence_ids = session.config_json.get("sentence_ids", [])
    sentences_result = await db.execute(
        select(Sentence).where(Sentence.id.in_(sentence_ids))
    )
    sentences = {s.id: s for s in sentences_result.scalars().all()}

    # Get current sentence
    # 获取当前句子
    current_sentence = None
    if session.current_index < len(sentence_ids):
        current_id = sentence_ids[session.current_index]
        current_sentence = sentences.get(current_id)

    # Count modifications
    # 统计修改
    mods_result = await db.execute(
        select(Modification).where(Modification.session_id == session_id)
    )
    modifications = mods_result.scalars().all()
    processed = len([m for m in modifications if m.accepted])
    skipped = len([m for m in modifications if not m.accepted and m.source == "skip"])
    flagged = len([m for m in modifications if m.source == "flag"])

    progress = (session.current_index / len(sentence_ids) * 100) if sentence_ids else 100

    return SessionState(
        session_id=session.id,
        document_id=session.document_id,
        mode=ProcessMode(session.mode),
        total_sentences=len(sentence_ids),
        processed=processed,
        skipped=skipped,
        flagged=flagged,
        current_index=session.current_index,
        current_sentence=_build_sentence_analysis(current_sentence) if current_sentence else None,
        suggestions=None,
        progress_percent=progress
    )


@router.post("/{session_id}/next", response_model=SessionState)
async def next_sentence(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Move to next sentence
    移动到下一个句子
    """
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    sentence_ids = session.config_json.get("sentence_ids", [])

    # Move to next
    # 移动到下一个
    if session.current_index < len(sentence_ids) - 1:
        session.current_index += 1
    else:
        session.status = "completed"
        session.completed_at = datetime.utcnow()

    await db.commit()

    return await get_current_state(session_id, db)


@router.post("/{session_id}/skip")
async def skip_sentence(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Skip current sentence (without auto-jumping to next)
    跳过当前句子（不自动跳转到下一句）
    """
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Record skip
    # 记录跳过
    sentence_ids = session.config_json.get("sentence_ids", [])
    if session.current_index < len(sentence_ids):
        current_id = sentence_ids[session.current_index]
        # Check if modification already exists for this sentence
        # 检查是否已存在该句子的修改记录
        existing = await db.execute(
            select(Modification).where(
                Modification.sentence_id == current_id,
                Modification.session_id == session_id
            )
        )
        existing_mod = existing.scalar_one_or_none()
        if existing_mod:
            # Update existing modification
            # 更新现有修改
            existing_mod.source = "skip"
            existing_mod.accepted = False
        else:
            # Create new modification
            # 创建新修改
            mod = Modification(
                sentence_id=current_id,
                session_id=session_id,
                source="skip",
                modified_text="",
                accepted=False
            )
            db.add(mod)
        await db.commit()

    # Return current state without jumping to next
    # 返回当前状态，不跳转到下一句
    return await get_current_state(session_id, db)


@router.post("/{session_id}/flag")
async def flag_sentence(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Flag current sentence for manual review (without auto-jumping to next)
    标记当前句子需要人工审核（不自动跳转到下一句）
    """
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Record flag
    # 记录标记
    sentence_ids = session.config_json.get("sentence_ids", [])
    if session.current_index < len(sentence_ids):
        current_id = sentence_ids[session.current_index]
        # Check if modification already exists for this sentence
        # 检查是否已存在该句子的修改记录
        existing = await db.execute(
            select(Modification).where(
                Modification.sentence_id == current_id,
                Modification.session_id == session_id
            )
        )
        existing_mod = existing.scalar_one_or_none()
        if existing_mod:
            # Update existing modification
            # 更新现有修改
            existing_mod.source = "flag"
            existing_mod.accepted = False
        else:
            # Create new modification
            # 创建新修改
            mod = Modification(
                sentence_id=current_id,
                session_id=session_id,
                source="flag",
                modified_text="",
                accepted=False
            )
            db.add(mod)
        await db.commit()

    # Return current state without jumping to next
    # 返回当前状态，不跳转到下一句
    return await get_current_state(session_id, db)


@router.get("/{session_id}/sentences", response_model=List[SentenceAnalysis])
async def get_all_sentences(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all sentences for a session
    获取会话的所有句子
    """
    # Get session
    # 获取会话
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get sentences
    # 获取句子
    sentence_ids = session.config_json.get("sentence_ids", [])
    sentences_result = await db.execute(
        select(Sentence).where(Sentence.id.in_(sentence_ids))
    )
    sentences = {s.id: s for s in sentences_result.scalars().all()}

    # Get modifications to determine status
    # 获取修改以确定状态
    mods_result = await db.execute(
        select(Modification).where(Modification.session_id == session_id)
    )
    modifications = {m.sentence_id: m for m in mods_result.scalars().all()}

    # Build ordered list
    # 构建有序列表
    result_list = []
    for idx, sid in enumerate(sentence_ids):
        sent = sentences.get(sid)
        if sent:
            analysis = _build_sentence_analysis(sent)
            # Add modification status
            # 添加修改状态
            mod = modifications.get(sid)
            if mod:
                analysis.status = mod.source if mod.source in ["skip", "flag"] else ("processed" if mod.accepted else "pending")
            else:
                analysis.status = "current" if idx == session.current_index else "pending"
            result_list.append(analysis)

    return result_list


@router.post("/{session_id}/goto/{index}")
async def goto_sentence(
    session_id: str,
    index: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Jump to a specific sentence
    跳转到特定句子
    """
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    sentence_ids = session.config_json.get("sentence_ids", [])

    if index < 0 or index >= len(sentence_ids):
        raise HTTPException(status_code=400, detail="Invalid sentence index")

    session.current_index = index
    await db.commit()

    return await get_current_state(session_id, db)


@router.get("/{session_id}/progress")
async def get_progress(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get session progress
    获取会话进度
    """
    state = await get_current_state(session_id, db)
    return {
        "total": state.total_sentences,
        "processed": state.processed,
        "skipped": state.skipped,
        "flagged": state.flagged,
        "current_index": state.current_index,
        "progress_percent": state.progress_percent,
        "status": "completed" if state.progress_percent >= 100 else "in_progress"
    }


@router.post("/{session_id}/complete")
async def complete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark session as completed
    标记会话为已完成
    """
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "completed"
    session.completed_at = datetime.utcnow()
    await db.commit()

    return {"status": "completed", "session_id": session_id}


def _build_sentence_analysis(sentence: Sentence) -> SentenceAnalysis:
    """
    Build SentenceAnalysis from Sentence model
    从Sentence模型构建SentenceAnalysis
    """
    analysis = sentence.analysis_json or {}
    return SentenceAnalysis(
        id=sentence.id,  # Include database ID for API calls
        index=sentence.index,
        text=sentence.original_text,
        risk_score=sentence.risk_score or 0,
        risk_level=RiskLevel(sentence.risk_level or "low"),
        ppl=analysis.get("ppl", 0),
        ppl_risk=RiskLevel(analysis.get("ppl_risk", "low")),
        fingerprints=[],
        fingerprint_density=analysis.get("fingerprint_density", 0),
        issues=[],
        locked_terms=sentence.locked_terms_json or []
    )
