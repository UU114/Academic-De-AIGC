"""
Session management API routes
会话管理API路由

CAASS v2.0 Phase 2: Added whitelist storage and context support
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
from src.core.preprocessor.whitelist_extractor import WhitelistExtractor
from typing import List

router = APIRouter()
whitelist_extractor = WhitelistExtractor()


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
            current_step=sess.current_step or "step1-1",
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

    CAASS v2.0 Phase 2: Extracts and stores whitelist for the session
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

    # CAASS v2.0 Phase 2: Extract whitelist from document
    # CAASS v2.0 第二阶段：从文档提取白名单
    try:
        whitelist_result = whitelist_extractor.extract_from_document(doc.original_text or "")
        whitelist_terms = list(whitelist_result.terms)  # Convert set to list for JSON storage
    except Exception as e:
        print(f"Error extracting whitelist: {e}")
        whitelist_terms = []

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

    # Create session with whitelist in config
    # 创建带白名单的会话配置
    session = Session(
        document_id=request.document_id,
        mode=request.mode.value,
        colloquialism_level=request.colloquialism_level,
        target_lang=request.target_lang,
        config_json={
            "process_levels": process_levels,
            "sentence_ids": [s.id for s in filtered_sentences],
            "whitelist": whitelist_terms,  # CAASS v2.0 Phase 2: Store whitelist
            "tone_level": request.colloquialism_level  # Map colloquialism to tone
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
        progress_percent=0.0,
        status=session.status
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
        progress_percent=progress,
        status=session.status
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
            # Add modification status and new risk score
            # 添加修改状态和新风险分数
            mod = modifications.get(sid)
            if mod:
                analysis.status = mod.source if mod.source in ["skip", "flag"] else ("processed" if mod.accepted else "pending")
                # Add new risk score/level if processed
                # 如果已处理，添加新风险分数/等级
                if mod.accepted and mod.new_risk_score is not None:
                    analysis.new_risk_score = mod.new_risk_score
                    # Calculate risk level from score
                    # 根据分数计算风险等级
                    if mod.new_risk_score < 10:
                        analysis.new_risk_level = RiskLevel.SAFE
                    elif mod.new_risk_score < 25:
                        analysis.new_risk_level = RiskLevel.LOW
                    elif mod.new_risk_score < 50:
                        analysis.new_risk_level = RiskLevel.MEDIUM
                    else:
                        analysis.new_risk_level = RiskLevel.HIGH
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


@router.get("/{session_id}/review-stats")
async def get_review_stats(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get review statistics for completed session
    获取已完成会话的审核统计数据
    """
    # Get all modifications for this session
    # 获取此会话的所有修改记录
    result = await db.execute(
        select(Modification).where(Modification.session_id == session_id)
    )
    modifications = result.scalars().all()

    # Get sentences to calculate original risk
    # 获取句子以计算原始风险
    result = await db.execute(
        select(Sentence).join(Session, Session.document_id == Sentence.document_id)
        .where(Session.id == session_id)
        .where(Sentence.should_process == True)
    )
    sentences = result.scalars().all()

    # Calculate statistics
    # 计算统计数据
    total_sentences = len(sentences)
    modified_count = len(modifications)

    # Source distribution
    # 来源分布
    source_counts = {"llm": 0, "rule": 0, "custom": 0}
    total_risk_reduction = 0

    for mod in modifications:
        source_counts[mod.source] = source_counts.get(mod.source, 0) + 1
        # Get original sentence risk
        # 获取原始句子风险分数
        sentence = next((s for s in sentences if s.id == mod.sentence_id), None)
        if sentence and mod.new_risk_score is not None:
            original_risk = sentence.risk_score or 0
            new_risk = mod.new_risk_score
            total_risk_reduction += (original_risk - new_risk)

    # Calculate averages
    # 计算平均值
    avg_risk_reduction = total_risk_reduction / modified_count if modified_count > 0 else 0

    # Calculate source percentages
    # 计算来源百分比
    source_percent = {}
    for source, count in source_counts.items():
        source_percent[source] = round(count / modified_count * 100) if modified_count > 0 else 0

    return {
        "total_sentences": total_sentences,
        "modified_count": modified_count,
        "avg_risk_reduction": round(avg_risk_reduction, 1),
        "source_distribution": source_percent
    }


@router.get("/{session_id}/config")
async def get_session_config(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get session configuration including whitelist
    获取会话配置，包括白名单

    CAASS v2.0 Phase 2: Returns whitelist and tone_level for suggestion scoring
    """
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    config = session.config_json or {}

    return {
        "session_id": session_id,
        "whitelist": config.get("whitelist", []),
        "tone_level": config.get("tone_level", session.colloquialism_level),
        "process_levels": config.get("process_levels", []),
        "colloquialism_level": session.colloquialism_level,
        "target_lang": session.target_lang
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
    session.current_step = "review"
    session.completed_at = datetime.utcnow()
    await db.commit()

    return {"status": "completed", "session_id": session_id}


@router.post("/{session_id}/step/{step}")
async def update_session_step(
    session_id: str,
    step: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Update current step for a session
    更新会话的当前步骤

    Valid steps: step1-1, step1-2, step2, step3, review
    """
    valid_steps = ["step1-1", "step1-2", "step2", "step3", "review"]
    if step not in valid_steps:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step. Valid steps: {', '.join(valid_steps)}"
        )

    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.current_step = step
    await db.commit()

    return {"session_id": session_id, "current_step": step}


@router.post("/{session_id}/yolo-process")
async def yolo_auto_process(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    YOLO auto-processing: Automatically process all sentences using LLM
    YOLO 自动处理：使用 LLM 自动处理所有句子

    This endpoint processes sentences one by one, calling LLM for each,
    selecting the best suggestion, and applying it automatically.
    此端点逐句处理，为每个句子调用 LLM，选择最佳建议并自动应用。

    Returns a generator for streaming progress updates.
    返回生成器用于流式进度更新。
    """
    from src.core.suggester.llm_track import LLMTrack
    from src.core.suggester.rule_track import RuleTrack
    from src.core.analyzer.scorer import RiskScorer
    from src.core.validator.quality_gate import QualityGate
    import json
    import logging

    logger = logging.getLogger(__name__)
    quality_gate = QualityGate()

    # Get session
    # 获取会话
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all sentences for processing
    # 获取所有待处理的句子
    sentence_ids = session.config_json.get("sentence_ids", [])
    whitelist = session.config_json.get("whitelist", [])
    tone_level = session.colloquialism_level or 4

    sentences_result = await db.execute(
        select(Sentence).where(Sentence.id.in_(sentence_ids)).order_by(Sentence.index)
    )
    sentences = sentences_result.scalars().all()

    # Get existing modifications
    # 获取已有的修改记录
    mods_result = await db.execute(
        select(Modification).where(Modification.session_id == session_id)
    )
    existing_mods = {m.sentence_id: m for m in mods_result.scalars().all()}

    # Initialize components
    # 初始化组件
    llm_track = LLMTrack(colloquialism_level=tone_level)
    rule_track = RuleTrack(colloquialism_level=tone_level)
    scorer = RiskScorer()
    whitelist_set = set(whitelist) if whitelist else None

    # Process results
    # 处理结果
    processed_count = 0
    skipped_count = 0
    total_risk_reduction = 0
    logs = []

    for idx, sentence in enumerate(sentences):
        # Skip if already processed
        # 如果已处理则跳过
        if sentence.id in existing_mods:
            existing_mod = existing_mods[sentence.id]
            if existing_mod.accepted:
                skipped_count += 1
                logs.append({
                    "index": idx + 1,
                    "action": "already_processed",
                    "message": f"句子 {idx + 1} 已处理，跳过",
                    "original_risk": sentence.risk_score or 0,
                    "new_risk": existing_mod.new_risk_score or 0,
                })
                continue

        # Calculate original risk
        # 计算原始风险分数
        original_analysis = scorer.analyze(
            sentence.original_text,
            tone_level=tone_level,
            whitelist=whitelist_set
        )
        original_risk = original_analysis.risk_score

        # Skip low risk sentences (score < 25)
        # 跳过低风险句子 (分数 < 25)
        if original_risk < 25:
            # Record as skipped
            # 记录为跳过
            mod = Modification(
                sentence_id=sentence.id,
                session_id=session_id,
                source="skip",
                modified_text="",
                accepted=False,
                new_risk_score=original_risk
            )
            db.add(mod)
            skipped_count += 1
            logs.append({
                "index": idx + 1,
                "action": "skipped",
                "message": f"句子 {idx + 1} 风险较低 ({original_risk})，已跳过",
                "original_risk": original_risk,
                "new_risk": original_risk,
            })
            continue

        # Try LLM suggestion first
        # 首先尝试 LLM 建议
        best_text = None
        best_risk = original_risk
        best_source = "llm"

        # Check if paraphrase
        is_paraphrase = False
        if sentence.analysis_json and sentence.analysis_json.get("is_paraphrase"):
            is_paraphrase = True

        try:
            llm_result = await llm_track.generate_suggestion(
                sentence=sentence.original_text,
                issues=[],
                locked_terms=sentence.locked_terms_json or [],
                target_lang=session.target_lang or "zh",
                is_paraphrase=is_paraphrase
            )
            if llm_result and llm_result.rewritten:
                # DEAI Engine 2.0: Verify suggestion for P0 words and first-person pronouns
                # DEAI Engine 2.0: 验证建议是否包含P0词或第一人称代词
                validation = quality_gate.verify_suggestion(
                    original=sentence.original_text,
                    suggestion=llm_result.rewritten,
                    colloquialism_level=tone_level
                )

                if not validation.passed:
                    # Log validation failure and skip this LLM suggestion
                    # 记录验证失败并跳过此LLM建议
                    logger.warning(
                        f"[YOLO] Sentence {idx + 1} LLM suggestion rejected: {validation.message}"
                    )
                    # Don't use this LLM suggestion, will try rule-based instead
                    # 不使用此LLM建议，将尝试规则建议
                else:
                    llm_analysis = scorer.analyze(
                        llm_result.rewritten,
                        tone_level=tone_level,
                        whitelist=whitelist_set
                    )
                    if llm_analysis.risk_score < best_risk:
                        best_text = llm_result.rewritten
                        best_risk = llm_analysis.risk_score
                        best_source = "llm"
        except Exception as e:
            logger.error(f"LLM track error for sentence {idx + 1}: {e}")

        # Also try rule-based suggestion
        # 同时尝试规则建议
        try:
            rule_result = rule_track.generate_suggestion(
                sentence=sentence.original_text,
                issues=[],
                locked_terms=sentence.locked_terms_json or []
            )
            if rule_result and rule_result.rewritten:
                # DEAI Engine 2.0: Also validate rule-based suggestions
                # DEAI Engine 2.0: 同样验证规则建议
                rule_validation = quality_gate.verify_suggestion(
                    original=sentence.original_text,
                    suggestion=rule_result.rewritten,
                    colloquialism_level=tone_level
                )

                if rule_validation.passed:
                    rule_analysis = scorer.analyze(
                        rule_result.rewritten,
                        tone_level=tone_level,
                        whitelist=whitelist_set
                    )
                    if rule_analysis.risk_score < best_risk:
                        best_text = rule_result.rewritten
                        best_risk = rule_analysis.risk_score
                        best_source = "rule"
        except Exception as e:
            logger.error(f"Rule track error for sentence {idx + 1}: {e}")

        # Apply the best suggestion
        # 应用最佳建议
        if best_text and best_risk < original_risk:
            mod = Modification(
                sentence_id=sentence.id,
                session_id=session_id,
                source=best_source,
                modified_text=best_text,
                accepted=True,
                new_risk_score=best_risk
            )
            db.add(mod)
            risk_reduction = original_risk - best_risk
            total_risk_reduction += risk_reduction
            processed_count += 1
            logs.append({
                "index": idx + 1,
                "action": "modified",
                "message": f"句子 {idx + 1} 已应用{best_source.upper()}建议修改",
                "original_risk": original_risk,
                "new_risk": best_risk,
                "source": best_source,
            })
        else:
            # No improvement possible, skip
            # 无法改进，跳过
            mod = Modification(
                sentence_id=sentence.id,
                session_id=session_id,
                source="skip",
                modified_text="",
                accepted=False,
                new_risk_score=original_risk
            )
            db.add(mod)
            skipped_count += 1
            logs.append({
                "index": idx + 1,
                "action": "no_improvement",
                "message": f"句子 {idx + 1} 无法进一步降低风险，已跳过",
                "original_risk": original_risk,
                "new_risk": original_risk,
            })

        # Update session progress
        # 更新会话进度
        session.current_index = idx + 1

    # Mark session as completed
    # 标记会话为已完成
    session.status = "completed"
    session.current_step = "review"
    session.completed_at = datetime.utcnow()

    await db.commit()

    return {
        "status": "completed",
        "session_id": session_id,
        "total_sentences": len(sentences),
        "processed": processed_count,
        "skipped": skipped_count,
        "avg_risk_reduction": round(total_risk_reduction / processed_count, 1) if processed_count > 0 else 0,
        "logs": logs
    }


def _build_sentence_analysis(sentence: Sentence) -> SentenceAnalysis:
    """
    Build SentenceAnalysis from Sentence model
    从Sentence模型构建SentenceAnalysis
    """
    from src.core.analyzer.fingerprint import FingerprintDetector
    from src.api.schemas import FingerprintMatch

    analysis = sentence.analysis_json or {}

    # Detect fingerprints in the sentence text
    # 检测句子文本中的指纹词
    detector = FingerprintDetector()
    detected_fps = detector.detect(sentence.original_text)
    fingerprints = [
        FingerprintMatch(
            word=fp.word,
            position=fp.position,
            risk_weight=fp.risk_weight,
            category=fp.category,
            replacements=fp.replacements
        ) for fp in detected_fps
    ]

    return SentenceAnalysis(
        id=sentence.id,  # Include database ID for API calls
        index=sentence.index,
        text=sentence.original_text,
        risk_score=sentence.risk_score or 0,
        risk_level=RiskLevel(sentence.risk_level or "low"),
        ppl=analysis.get("ppl", 0),
        ppl_risk=RiskLevel(analysis.get("ppl_risk", "low")),
        fingerprints=fingerprints,
        fingerprint_density=analysis.get("fingerprint_density", 0),
        issues=[],
        locked_terms=sentence.locked_terms_json or [],
        # Phase 2: Enhanced metrics
        burstiness_value=analysis.get("burstiness_value", 0.0),
        burstiness_risk=analysis.get("burstiness_risk", "unknown"),
        connector_count=analysis.get("connector_count", 0),
        connector_word=analysis.get("connector_word"),
        context_baseline=analysis.get("context_baseline", 0),
        paragraph_index=analysis.get("paragraph_index", 0)
    )
