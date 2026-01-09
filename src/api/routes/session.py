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
            colloquialism_level=sess.colloquialism_level or 4,
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
        "source_distribution": source_percent,
        "step_logs": session.config_json.get("step_logs", []) if session.config_json else []
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

    Valid steps:
    - Legacy: step1-1, step1-2, step2, step3, review
    - 5-Layer: term-lock, layer-document, layer-section, layer-paragraph, layer-sentence, layer-lexical
    """
    valid_steps = [
        # Legacy steps (旧版步骤)
        "step1-1", "step1-2", "step2", "step3", "review",
        # 5-Layer architecture steps (5层架构步骤)
        # Step 1.0: Term Locking (must be first)
        "term-lock",
        "layer-document", "layer-section", "layer-paragraph", "layer-sentence", "layer-lexical"
    ]
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


@router.post("/{session_id}/yolo-full-auto")
async def yolo_full_auto_process(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    YOLO Full Automation: Process all levels automatically from Step 1-1 to Step 3
    YOLO 全自动处理：从 Step 1-1 到 Step 3 自动处理所有层级

    This endpoint performs:
    1. Step 1-1: Structure analysis → Auto-select all issues → AI modify
    2. Step 1-2: Paragraph analysis → Auto-select all issues → AI modify
    3. Step 2: Transition analysis → Auto-select all issues → AI modify
    4. Step 3: Sentence-level processing (yolo-process)

    此端点执行：
    1. Step 1-1：结构分析 → 自动全选问题 → AI修改
    2. Step 1-2：段落分析 → 自动全选问题 → AI修改
    3. Step 2：衔接分析 → 自动全选问题 → AI修改
    4. Step 3：句子级处理（yolo-process）

    Returns progress logs for each step.
    返回每个步骤的进度日志。
    """
    import logging
    from src.core.analyzer.smart_structure import SmartStructureAnalyzer
    from src.core.analyzer.transition import TransitionAnalyzer

    logger = logging.getLogger(__name__)
    logs = []

    # Get session
    # 获取会话
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get document
    # 获取文档
    doc_result = await db.execute(
        select(Document).where(Document.id == session.document_id)
    )
    document = doc_result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    current_document_id = session.document_id
    current_text = document.original_text
    colloquialism_level = session.colloquialism_level or 4

    # Initialize analyzers
    # 初始化分析器
    smart_analyzer = SmartStructureAnalyzer()
    transition_analyzer = TransitionAnalyzer()

    try:
        # ============================================
        # Step 1-1: Structure Analysis + Auto Modify
        # 步骤 1-1：结构分析 + 自动修改
        # ============================================
        session.current_step = "step1-1"
        await db.commit()

        logs.append({
            "step": "step1-1",
            "action": "analyzing",
            "message": "正在分析文档结构... / Analyzing document structure..."
        })

        try:
            step1_1_result = await smart_analyzer.analyze_structure(
                current_text,
                target_colloquialism=colloquialism_level
            )

            structure_issues = step1_1_result.get("structure_issues", [])

            if structure_issues:
                logs.append({
                    "step": "step1-1",
                    "action": "found_issues",
                    "message": f"发现 {len(structure_issues)} 个结构问题 / Found {len(structure_issues)} structure issues",
                    "issues_count": len(structure_issues)
                })

                # Auto-apply AI modification for all issues
                # 自动为所有问题应用AI修改
                logs.append({
                    "step": "step1-1",
                    "action": "modifying",
                    "message": "正在自动修改结构问题... / Auto-modifying structure issues..."
                })

                # Call merge-modify apply internally
                # 内部调用合并修改应用
                from src.api.routes.structure import apply_merge_modify
                from src.api.schemas import MergeModifyRequest, SelectedIssue

                selected_issues = [
                    SelectedIssue(
                        type=issue.get("type", "unknown"),
                        description=issue.get("description", ""),
                        description_zh=issue.get("description_zh", issue.get("descriptionZh", "")),
                        severity=issue.get("severity", "medium"),
                        affected_positions=issue.get("affected_positions", issue.get("affectedPositions", []))
                    )
                    for issue in structure_issues
                ]

                modify_request = MergeModifyRequest(
                    document_id=current_document_id,
                    session_id=session_id,
                    selected_issues=selected_issues,
                    user_notes="YOLO全自动模式：自动修改所有结构问题 / YOLO auto mode: auto-modifying all structure issues",
                    mode="apply"
                )

                try:
                    modify_result = await apply_merge_modify(modify_request, db)

                    if modify_result.modified_text and modify_result.changes_count > 0:
                        # Create new document with modified text
                        # 用修改后的文本创建新文档
                        new_doc = Document(
                            filename=f"yolo_step1-1_{document.filename}",
                            original_text=modify_result.modified_text,
                            status="ready"
                        )
                        db.add(new_doc)
                        await db.flush()

                        current_document_id = new_doc.id
                        current_text = modify_result.modified_text

                        logs.append({
                            "step": "step1-1",
                            "action": "modified",
                            "message": f"已修改 {modify_result.changes_count} 处 / Modified {modify_result.changes_count} places",
                            "changes_count": modify_result.changes_count
                        })
                    else:
                        logs.append({
                            "step": "step1-1",
                            "action": "no_changes",
                            "message": "AI未做出修改 / No AI modifications made"
                        })
                except Exception as e:
                    logger.error(f"Step 1-1 modify error: {e}")
                    logs.append({
                        "step": "step1-1",
                        "action": "error",
                        "message": f"修改失败，继续处理 / Modify failed, continuing: {str(e)[:100]}"
                    })
            else:
                logs.append({
                    "step": "step1-1",
                    "action": "no_issues",
                    "message": "未发现结构问题 / No structure issues found"
                })

        except Exception as e:
            logger.error(f"Step 1-1 analysis error: {e}")
            logs.append({
                "step": "step1-1",
                "action": "error",
                "message": f"分析失败，继续处理 / Analysis failed, continuing: {str(e)[:100]}"
            })

        # ============================================
        # Step 1-2: Paragraph Relationship Analysis + Auto Modify
        # 步骤 1-2：段落关系分析 + 自动修改
        # ============================================
        session.current_step = "step1-2"
        await db.commit()

        logs.append({
            "step": "step1-2",
            "action": "analyzing",
            "message": "正在分析段落关系... / Analyzing paragraph relationships..."
        })

        try:
            # First need structure result for relationship analysis
            # 首先需要结构结果用于关系分析
            structure_result = await smart_analyzer.analyze_structure(
                current_text,
                target_colloquialism=colloquialism_level
            )
            step1_2_result = await smart_analyzer.analyze_relationships(
                current_text,
                structure_result
            )

            # Collect issues from step 1-2
            # 从 step 1-2 收集问题
            paragraph_risks = step1_2_result.get("paragraph_risks", [])
            explicit_connectors = step1_2_result.get("explicit_connectors", [])
            logic_breaks = step1_2_result.get("logic_breaks", [])

            # Convert to issues format
            # 转换为问题格式
            step1_2_issues = []

            # Add explicit connector issues
            # 添加显性连接词问题
            for conn in explicit_connectors:
                if conn.get("severity") in ["high", "medium"]:
                    step1_2_issues.append({
                        "type": "explicit_connector",
                        "description": f"Explicit connector '{conn.get('word')}' at {conn.get('position')}",
                        "description_zh": f"显性连接词 '{conn.get('word')}' 位于 {conn.get('position')}",
                        "severity": conn.get("severity", "medium"),
                        "affected_positions": [conn.get("position", "")]
                    })

            # Add paragraph risk issues
            # 添加段落风险问题
            for risk in paragraph_risks:
                if risk.get("ai_risk", risk.get("aiRisk")) in ["high", "medium"]:
                    step1_2_issues.append({
                        "type": "paragraph_risk",
                        "description": risk.get("ai_risk_reason", risk.get("aiRiskReason", "High AI risk paragraph")),
                        "description_zh": risk.get("ai_risk_reason", risk.get("aiRiskReason", "高AI风险段落")),
                        "severity": risk.get("ai_risk", risk.get("aiRisk", "medium")),
                        "affected_positions": [risk.get("position", "")]
                    })

            if step1_2_issues:
                logs.append({
                    "step": "step1-2",
                    "action": "found_issues",
                    "message": f"发现 {len(step1_2_issues)} 个段落关系问题 / Found {len(step1_2_issues)} paragraph issues",
                    "issues_count": len(step1_2_issues)
                })

                logs.append({
                    "step": "step1-2",
                    "action": "modifying",
                    "message": "正在自动修改段落关系问题... / Auto-modifying paragraph issues..."
                })

                selected_issues = [
                    SelectedIssue(
                        type=issue["type"],
                        description=issue["description"],
                        description_zh=issue["description_zh"],
                        severity=issue["severity"],
                        affected_positions=issue["affected_positions"]
                    )
                    for issue in step1_2_issues
                ]

                # Need to get current document
                # 需要获取当前文档
                current_doc = await db.get(Document, current_document_id)

                modify_request = MergeModifyRequest(
                    document_id=current_document_id,
                    session_id=session_id,
                    selected_issues=selected_issues,
                    user_notes="YOLO全自动模式：自动修改所有段落关系问题 / YOLO auto mode: auto-modifying all paragraph issues",
                    mode="apply"
                )

                try:
                    modify_result = await apply_merge_modify(modify_request, db)

                    if modify_result.modified_text and modify_result.changes_count > 0:
                        new_doc = Document(
                            filename=f"yolo_step1-2_{document.filename}",
                            original_text=modify_result.modified_text,
                            status="ready"
                        )
                        db.add(new_doc)
                        await db.flush()

                        current_document_id = new_doc.id
                        current_text = modify_result.modified_text

                        logs.append({
                            "step": "step1-2",
                            "action": "modified",
                            "message": f"已修改 {modify_result.changes_count} 处 / Modified {modify_result.changes_count} places",
                            "changes_count": modify_result.changes_count
                        })
                    else:
                        logs.append({
                            "step": "step1-2",
                            "action": "no_changes",
                            "message": "AI未做出修改 / No AI modifications made"
                        })
                except Exception as e:
                    logger.error(f"Step 1-2 modify error: {e}")
                    logs.append({
                        "step": "step1-2",
                        "action": "error",
                        "message": f"修改失败，继续处理 / Modify failed, continuing: {str(e)[:100]}"
                    })
            else:
                logs.append({
                    "step": "step1-2",
                    "action": "no_issues",
                    "message": "未发现段落关系问题 / No paragraph issues found"
                })

        except Exception as e:
            logger.error(f"Step 1-2 analysis error: {e}")
            logs.append({
                "step": "step1-2",
                "action": "error",
                "message": f"分析失败，继续处理 / Analysis failed, continuing: {str(e)[:100]}"
            })

        # ============================================
        # Step 2: Transition Analysis + Auto Modify
        # 步骤 2：衔接分析 + 自动修改
        # ============================================
        session.current_step = "step2"
        await db.commit()

        logs.append({
            "step": "step2",
            "action": "analyzing",
            "message": "正在分析段落衔接... / Analyzing paragraph transitions..."
        })

        try:
            # Split text into paragraphs for transition analysis
            # 将文本分割成段落进行衔接分析
            paragraphs = [p.strip() for p in current_text.split('\n\n') if p.strip()]

            if len(paragraphs) < 2:
                logs.append({
                    "step": "step2",
                    "action": "no_issues",
                    "message": "段落数量不足，跳过衔接分析 / Not enough paragraphs for transition analysis"
                })
                transition_issues = []
            else:
                # analyze_document_transitions returns List[TransitionAnalysisResult]
                # analyze_document_transitions 返回 List[TransitionAnalysisResult]
                transitions = transition_analyzer.analyze_document_transitions(paragraphs)

                # Collect high/medium risk transition issues
                # 收集高/中风险衔接问题
                transition_issues = []
                for idx, trans in enumerate(transitions):
                    # trans is a TransitionAnalysisResult dataclass
                    # trans 是 TransitionAnalysisResult dataclass
                    risk_level = trans.risk_level
                    if risk_level in ["high", "medium"]:
                        # Add explicit connectors
                        # 添加显性连接词
                        explicit_conns = getattr(trans, 'explicit_connectors', []) or []
                        for conn in explicit_conns:
                            transition_issues.append({
                                "type": "transition_connector",
                                "description": f"Transition {idx+1} uses explicit connector '{conn}'",
                                "description_zh": f"衔接 #{idx+1} 使用显性连接词 '{conn}'",
                                "severity": "high",
                                "affected_positions": [f"衔接 #{idx+1}"]
                            })

                        # Add general transition issues
                        # 添加通用衔接问题
                        for issue in trans.issues:
                            # issue is a TransitionIssue dataclass
                            # issue 是 TransitionIssue dataclass
                            transition_issues.append({
                                "type": issue.type,
                                "description": issue.description,
                                "description_zh": issue.description_zh,
                                "severity": issue.severity,
                                "affected_positions": [f"衔接 #{idx+1}"]
                            })

            if transition_issues:
                logs.append({
                    "step": "step2",
                    "action": "found_issues",
                    "message": f"发现 {len(transition_issues)} 个衔接问题 / Found {len(transition_issues)} transition issues",
                    "issues_count": len(transition_issues)
                })

                logs.append({
                    "step": "step2",
                    "action": "modifying",
                    "message": "正在自动修改衔接问题... / Auto-modifying transition issues..."
                })

                selected_issues = [
                    SelectedIssue(
                        type=issue["type"],
                        description=issue["description"],
                        description_zh=issue["description_zh"],
                        severity=issue["severity"],
                        affected_positions=issue["affected_positions"]
                    )
                    for issue in transition_issues
                ]

                modify_request = MergeModifyRequest(
                    document_id=current_document_id,
                    session_id=session_id,
                    selected_issues=selected_issues,
                    user_notes="YOLO全自动模式：自动修改所有衔接问题 / YOLO auto mode: auto-modifying all transition issues",
                    mode="apply"
                )

                try:
                    modify_result = await apply_merge_modify(modify_request, db)

                    if modify_result.modified_text and modify_result.changes_count > 0:
                        new_doc = Document(
                            filename=f"yolo_step2_{document.filename}",
                            original_text=modify_result.modified_text,
                            status="ready"
                        )
                        db.add(new_doc)
                        await db.flush()

                        current_document_id = new_doc.id
                        current_text = modify_result.modified_text

                        logs.append({
                            "step": "step2",
                            "action": "modified",
                            "message": f"已修改 {modify_result.changes_count} 处 / Modified {modify_result.changes_count} places",
                            "changes_count": modify_result.changes_count
                        })
                    else:
                        logs.append({
                            "step": "step2",
                            "action": "no_changes",
                            "message": "AI未做出修改 / No AI modifications made"
                        })
                except Exception as e:
                    logger.error(f"Step 2 modify error: {e}")
                    logs.append({
                        "step": "step2",
                        "action": "error",
                        "message": f"修改失败，继续处理 / Modify failed, continuing: {str(e)[:100]}"
                    })
            else:
                logs.append({
                    "step": "step2",
                    "action": "no_issues",
                    "message": "未发现衔接问题 / No transition issues found"
                })

        except Exception as e:
            logger.error(f"Step 2 analysis error: {e}")
            logs.append({
                "step": "step2",
                "action": "error",
                "message": f"分析失败，继续处理 / Analysis failed, continuing: {str(e)[:100]}"
            })

        # ============================================
        # Step 3: Sentence-level Processing (yolo-process)
        # 步骤 3：句子级处理（yolo-process）
        # ============================================
        session.current_step = "step3"

        # Update session to use the latest document
        # 更新会话使用最新文档
        session.document_id = current_document_id
        await db.commit()

        logs.append({
            "step": "step3",
            "action": "processing",
            "message": "正在进行句子级处理... / Processing sentences..."
        })

        try:
            # Re-analyze and segment the updated document
            # 重新分析和分句更新后的文档
            from src.core.preprocessor.segmenter import SentenceSegmenter
            from src.core.analyzer.scorer import RiskScorer

            segmenter = SentenceSegmenter()
            scorer = RiskScorer()
            whitelist = session.config_json.get("whitelist", [])
            whitelist_set = set(whitelist) if whitelist else None

            # Segment the current text
            # 分句当前文本
            sentences_data = segmenter.segment_with_paragraphs(current_text)

            # Create new sentence records
            # 创建新的句子记录
            # Note: segment_with_paragraphs returns Sentence dataclass objects, not dicts
            # 注意：segment_with_paragraphs 返回 Sentence dataclass 对象，不是字典
            new_sentence_ids = []
            for idx, sent_data in enumerate(sentences_data):
                # sent_data is a Sentence dataclass from preprocessor
                # sent_data 是来自 preprocessor 的 Sentence dataclass
                sentence_text = sent_data.text
                paragraph_idx = sent_data.paragraph_index or 0

                analysis = scorer.analyze(
                    sentence_text,
                    tone_level=colloquialism_level,
                    whitelist=whitelist_set
                )

                sent = Sentence(
                    document_id=current_document_id,
                    index=idx,
                    original_text=sentence_text,
                    risk_score=analysis.risk_score,
                    risk_level=analysis.risk_level,
                    should_process=True,
                    analysis_json={
                        "ppl": analysis.ppl,
                        "fingerprint_density": analysis.fingerprint_density,
                        "paragraph_index": paragraph_idx
                    }
                )
                db.add(sent)
                await db.flush()
                new_sentence_ids.append(sent.id)

            # Update session config with new sentence IDs
            # 更新会话配置使用新的句子ID
            session.config_json["sentence_ids"] = new_sentence_ids
            session.current_index = 0
            await db.commit()

            # Now run the yolo-process logic
            # 现在运行 yolo-process 逻辑
            from src.core.suggester.llm_track import LLMTrack
            from src.core.suggester.rule_track import RuleTrack
            from src.core.validator.quality_gate import QualityGate

            quality_gate = QualityGate()
            llm_track = LLMTrack(colloquialism_level=colloquialism_level)
            rule_track = RuleTrack(colloquialism_level=colloquialism_level)

            # Get new sentences
            # 获取新句子
            sentences_result = await db.execute(
                select(Sentence).where(Sentence.id.in_(new_sentence_ids)).order_by(Sentence.index)
            )
            sentences = sentences_result.scalars().all()

            processed_count = 0
            skipped_count = 0
            total_risk_reduction = 0

            for idx, sentence in enumerate(sentences):
                original_risk = sentence.risk_score or 0

                # YOLO mode: Try to improve ALL sentences, not just high-risk ones
                # YOLO模式：尝试改进所有句子，而不仅仅是高风险句子
                # Skip only very short sentences (< 10 chars) or pure numbers
                # 只跳过非常短的句子（< 10字符）或纯数字
                sentence_text = sentence.original_text.strip()
                if len(sentence_text) < 10 or sentence_text.replace('.', '').replace(',', '').isdigit():
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
                    continue

                # Try LLM suggestion
                # 尝试 LLM 建议
                best_text = None
                best_risk = original_risk
                best_source = "llm"

                try:
                    llm_result = await llm_track.generate_suggestion(
                        sentence=sentence.original_text,
                        issues=[],
                        locked_terms=sentence.locked_terms_json or [],
                        target_lang=session.target_lang or "zh",
                        is_paraphrase=False
                    )
                    if llm_result and llm_result.rewritten:
                        validation = quality_gate.verify_suggestion(
                            original=sentence.original_text,
                            suggestion=llm_result.rewritten,
                            colloquialism_level=colloquialism_level
                        )
                        if validation.passed:
                            llm_analysis = scorer.analyze(
                                llm_result.rewritten,
                                tone_level=colloquialism_level,
                                whitelist=whitelist_set
                            )
                            if llm_analysis.risk_score < best_risk:
                                best_text = llm_result.rewritten
                                best_risk = llm_analysis.risk_score
                                best_source = "llm"
                except Exception as e:
                    logger.error(f"LLM track error for sentence {idx + 1}: {e}")

                # Try rule-based suggestion
                # 尝试规则建议
                try:
                    rule_result = rule_track.generate_suggestion(
                        sentence=sentence.original_text,
                        issues=[],
                        locked_terms=sentence.locked_terms_json or []
                    )
                    if rule_result and rule_result.rewritten:
                        rule_validation = quality_gate.verify_suggestion(
                            original=sentence.original_text,
                            suggestion=rule_result.rewritten,
                            colloquialism_level=colloquialism_level
                        )
                        if rule_validation.passed:
                            rule_analysis = scorer.analyze(
                                rule_result.rewritten,
                                tone_level=colloquialism_level,
                                whitelist=whitelist_set
                            )
                            if rule_analysis.risk_score < best_risk:
                                best_text = rule_result.rewritten
                                best_risk = rule_analysis.risk_score
                                best_source = "rule"
                except Exception as e:
                    logger.error(f"Rule track error for sentence {idx + 1}: {e}")

                # Apply best suggestion
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
                else:
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

                session.current_index = idx + 1

            logs.append({
                "step": "step3",
                "action": "completed",
                "message": f"句子级处理完成：修改 {processed_count} 句，跳过 {skipped_count} 句 / Sentence processing completed: modified {processed_count}, skipped {skipped_count}",
                "processed": processed_count,
                "skipped": skipped_count,
                "avg_risk_reduction": round(total_risk_reduction / processed_count, 1) if processed_count > 0 else 0
            })

        except Exception as e:
            logger.error(f"Step 3 processing error: {e}")
            logs.append({
                "step": "step3",
                "action": "error",
                "message": f"处理失败 / Processing failed: {str(e)[:100]}"
            })

        # Mark session as completed
        # 标记会话为已完成
        session.status = "completed"
        session.current_step = "review"
        session.completed_at = datetime.utcnow()
        
        # Save step logs to config
        # 保存步骤日志到配置
        config = session.config_json or {}
        config["step_logs"] = logs
        session.config_json = config
        
        await db.commit()

        logs.append({
            "step": "complete",
            "action": "finished",
            "message": "YOLO全自动处理完成！/ YOLO full auto processing completed!"
        })

        return {
            "status": "completed",
            "session_id": session_id,
            "final_document_id": current_document_id,
            "logs": logs
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"YOLO full auto error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
