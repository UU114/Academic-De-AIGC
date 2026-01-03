"""
Transition Analysis API Routes (Level 2 De-AIGC)
衔接分析API路由（Level 2 De-AIGC）

Phase 3: Paragraph transition analysis and repair suggestions
Phase 3：段落衔接分析和修复建议
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import json
import os

from src.db.database import get_db
from src.db.models import Document
from src.api.schemas import (
    TransitionAnalysisRequest,
    TransitionAnalysisResponse,
    TransitionOption,
    TransitionIssue,
    TransitionStrategy,
    DocumentTransitionAnalysisRequest,
    DocumentTransitionSummary,
)
from src.core.analyzer.transition import TransitionAnalyzer, TransitionAnalysisResult
from src.prompts.transition import get_transition_prompt, STRATEGY_DESCRIPTIONS

router = APIRouter()
transition_analyzer = TransitionAnalyzer()


def _convert_analysis_to_response(
    analysis: TransitionAnalysisResult,
    options: Optional[List[TransitionOption]] = None
) -> TransitionAnalysisResponse:
    """
    Convert internal analysis result to API response
    将内部分析结果转换为API响应
    """
    return TransitionAnalysisResponse(
        para_a_ending=analysis.para_a_ending,
        para_b_opening=analysis.para_b_opening,
        smoothness_score=analysis.smoothness_score,
        risk_level=analysis.risk_level,
        issues=[
            TransitionIssue(
                type=issue.type,
                description=issue.description,
                description_zh=issue.description_zh,
                severity=issue.severity,
                position=issue.position,
                word=issue.word
            )
            for issue in analysis.issues
        ],
        explicit_connectors=analysis.explicit_connectors,
        has_topic_sentence_pattern=analysis.has_topic_sentence_pattern,
        has_summary_ending=analysis.has_summary_ending,
        semantic_overlap=analysis.semantic_overlap,
        options=options or [],
        message=analysis.message,
        message_zh=analysis.message_zh
    )


@router.post("/", response_model=TransitionAnalysisResponse)
async def analyze_transition(request: TransitionAnalysisRequest):
    """
    Analyze transition between two paragraphs
    分析两个段落之间的衔接

    Returns analysis with detected issues and smoothness score.
    返回分析结果，包括检测到的问题和平滑度分数。
    """
    # Perform analysis
    # 执行分析
    analysis = transition_analyzer.analyze(
        para_a=request.para_a,
        para_b=request.para_b,
        context_hint=request.context_hint
    )

    # Convert to response
    # 转换为响应
    return _convert_analysis_to_response(analysis)


@router.post("/with-suggestions", response_model=TransitionAnalysisResponse)
async def analyze_transition_with_suggestions(request: TransitionAnalysisRequest):
    """
    Analyze transition and generate repair suggestions
    分析衔接并生成修复建议

    Returns analysis with three strategy options for fixing the transition.
    返回分析结果，包含三种修复策略选项。

    Note: In production, this would call the LLM to generate actual suggestions.
    For now, we return placeholder suggestions based on the analysis.
    注意：在生产环境中，这将调用LLM生成实际建议。
    目前我们基于分析返回占位符建议。
    """
    # Perform analysis
    # 执行分析
    analysis = transition_analyzer.analyze(
        para_a=request.para_a,
        para_b=request.para_b,
        context_hint=request.context_hint
    )

    # Generate options for each strategy
    # 为每种策略生成选项
    options = _generate_placeholder_options(analysis, request.context_hint)

    # Convert to response with options
    # 转换为带选项的响应
    return _convert_analysis_to_response(analysis, options)


@router.post("/suggest/{strategy}", response_model=TransitionOption)
async def get_transition_suggestion(
    strategy: TransitionStrategy,
    request: TransitionAnalysisRequest
):
    """
    Get transition suggestion for a specific strategy
    获取特定策略的衔接建议

    This endpoint generates a single suggestion using the specified strategy.
    此端点使用指定策略生成单个建议。
    """
    # Perform analysis first
    # 首先执行分析
    analysis = transition_analyzer.analyze(
        para_a=request.para_a,
        para_b=request.para_b,
        context_hint=request.context_hint
    )

    # Generate option for the specific strategy
    # 为特定策略生成选项
    option = _generate_strategy_option(
        strategy=strategy,
        analysis=analysis,
        context_hint=request.context_hint
    )

    return option


@router.get("/strategies")
async def list_strategies():
    """
    List available transition strategies
    列出可用的过渡策略
    """
    return {
        "strategies": [
            {
                "id": strategy_id,
                "name": info["name"],
                "name_zh": info["name_zh"],
                "description": info["description"],
                "description_zh": info["description_zh"]
            }
            for strategy_id, info in STRATEGY_DESCRIPTIONS.items()
        ]
    }


@router.post("/document", response_model=DocumentTransitionSummary)
async def analyze_document_transitions(
    request: DocumentTransitionAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze all paragraph transitions in a document
    分析文档中所有段落衔接

    Features:
    - Caches results to avoid repeated analysis
    - 缓存结果以避免重复分析
    """
    import logging
    logger = logging.getLogger(__name__)

    # Get document
    # 获取文档
    result = await db.execute(
        select(Document).where(Document.id == request.document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if we have cached transition analysis
    # 检查是否有缓存的衔接分析
    if doc.transition_analysis_cache:
        logger.info(f"Using cached transition analysis for document {request.document_id}")
        cached = doc.transition_analysis_cache
        # Reconstruct response from cache
        # 从缓存重建响应
        transitions = [
            TransitionAnalysisResponse(
                para_a_ending=t.get("para_a_ending", ""),
                para_b_opening=t.get("para_b_opening", ""),
                smoothness_score=t.get("smoothness_score", 0),
                risk_level=t.get("risk_level", "low"),
                issues=[
                    TransitionIssue(
                        type=i.get("type", ""),
                        description=i.get("description", ""),
                        description_zh=i.get("description_zh", ""),
                        severity=i.get("severity", "low"),
                        position=i.get("position"),
                        word=i.get("word")
                    )
                    for i in t.get("issues", [])
                ],
                explicit_connectors=t.get("explicit_connectors", []),
                has_topic_sentence_pattern=t.get("has_topic_sentence_pattern", False),
                has_summary_ending=t.get("has_summary_ending", False),
                semantic_overlap=t.get("semantic_overlap", 0.0),
                options=[],
                message=t.get("message", ""),
                message_zh=t.get("message_zh", "")
            )
            for t in cached.get("transitions", [])
        ]
        return DocumentTransitionSummary(
            document_id=request.document_id,
            total_transitions=cached.get("total_transitions", 0),
            high_risk_count=cached.get("high_risk_count", 0),
            medium_risk_count=cached.get("medium_risk_count", 0),
            low_risk_count=cached.get("low_risk_count", 0),
            avg_smoothness_score=cached.get("avg_smoothness_score", 0.0),
            common_issues=cached.get("common_issues", []),
            transitions=transitions
        )

    # Split document into paragraphs
    # 将文档分割为段落
    paragraphs = _split_into_paragraphs(doc.original_text)

    if len(paragraphs) < 2:
        return DocumentTransitionSummary(
            document_id=request.document_id,
            total_transitions=0,
            high_risk_count=0,
            medium_risk_count=0,
            low_risk_count=0,
            avg_smoothness_score=0.0,
            common_issues=[],
            transitions=[]
        )

    # Analyze all transitions
    # 分析所有衔接
    logger.info(f"Starting transition analysis for document {request.document_id}")
    analyses = transition_analyzer.analyze_document_transitions(
        paragraphs=paragraphs,
        context_hint=request.context_hint
    )

    # Convert to responses
    # 转换为响应
    transitions = [_convert_analysis_to_response(a) for a in analyses]

    # Calculate summary statistics
    # 计算摘要统计
    high_count = sum(1 for t in transitions if t.risk_level == "high")
    medium_count = sum(1 for t in transitions if t.risk_level == "medium")
    low_count = sum(1 for t in transitions if t.risk_level == "low")

    scores = [t.smoothness_score for t in transitions]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    # Find common issues
    # 找出常见问题
    issue_types = {}
    for t in transitions:
        for issue in t.issues:
            issue_types[issue.type] = issue_types.get(issue.type, 0) + 1

    common_issues = sorted(issue_types.keys(), key=lambda x: issue_types[x], reverse=True)[:5]

    # Cache the result
    # 缓存结果
    cache_data = {
        "total_transitions": len(transitions),
        "high_risk_count": high_count,
        "medium_risk_count": medium_count,
        "low_risk_count": low_count,
        "avg_smoothness_score": avg_score,
        "common_issues": common_issues,
        "transitions": [
            {
                "para_a_ending": t.para_a_ending,
                "para_b_opening": t.para_b_opening,
                "smoothness_score": t.smoothness_score,
                "risk_level": t.risk_level,
                "issues": [
                    {
                        "type": i.type,
                        "description": i.description,
                        "description_zh": i.description_zh,
                        "severity": i.severity,
                        "position": i.position,
                        "word": i.word
                    }
                    for i in t.issues
                ],
                "explicit_connectors": t.explicit_connectors,
                "has_topic_sentence_pattern": t.has_topic_sentence_pattern,
                "has_summary_ending": t.has_summary_ending,
                "semantic_overlap": t.semantic_overlap,
                "message": t.message,
                "message_zh": t.message_zh
            }
            for t in transitions
        ]
    }
    doc.transition_analysis_cache = cache_data
    await db.commit()
    logger.info(f"Cached transition analysis for document {request.document_id}")

    return DocumentTransitionSummary(
        document_id=request.document_id,
        total_transitions=len(transitions),
        high_risk_count=high_count,
        medium_risk_count=medium_count,
        low_risk_count=low_count,
        avg_smoothness_score=avg_score,
        common_issues=common_issues,
        transitions=transitions
    )


def _split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs
    将文本分割为段落
    """
    # Split by double newlines or more
    # 按双换行符或更多分割
    import re
    paragraphs = re.split(r'\n\s*\n', text.strip())

    # Filter out empty paragraphs
    # 过滤空段落
    return [p.strip() for p in paragraphs if p.strip()]


def _generate_placeholder_options(
    analysis: TransitionAnalysisResult,
    context_hint: Optional[str] = None
) -> List[TransitionOption]:
    """
    Generate placeholder options for all strategies
    为所有策略生成占位符选项

    In production, this would call the LLM with the prompts.
    在生产环境中，这将使用prompts调用LLM。
    """
    options = []

    # Calculate predicted improvements based on analysis
    # 基于分析计算预测改进
    base_improvement = analysis.smoothness_score // 2

    # Strategy 1: Semantic Echo
    # 策略1：语义回声
    options.append(TransitionOption(
        strategy=TransitionStrategy.SEMANTIC_ECHO,
        strategy_name_zh="语义回声",
        para_a_ending=analysis.para_a_ending,  # Placeholder - would be modified by LLM
        para_b_opening=_remove_connectors(analysis.para_b_opening),
        key_concepts=_extract_key_concepts(analysis.para_a_ending),
        explanation="Remove explicit connectors and echo key concepts from the previous paragraph.",
        explanation_zh="移除显性连接词，回应前一段的关键概念。",
        predicted_improvement=base_improvement + 10
    ))

    # Strategy 2: Logical Hook
    # 策略2：逻辑设问
    options.append(TransitionOption(
        strategy=TransitionStrategy.LOGICAL_HOOK,
        strategy_name_zh="逻辑设问",
        para_a_ending=analysis.para_a_ending,  # Placeholder - would be modified by LLM
        para_b_opening=_remove_connectors(analysis.para_b_opening),
        hook_type="implication",
        explanation="Create implicit tension at paragraph end, then address it at the start.",
        explanation_zh="在段落末尾制造隐含问题或张力，在开头进行回应。",
        predicted_improvement=base_improvement + 15
    ))

    # Strategy 3: Rhythm Break
    # 策略3：节奏打断
    options.append(TransitionOption(
        strategy=TransitionStrategy.RHYTHM_BREAK,
        strategy_name_zh="节奏打断",
        para_a_ending=analysis.para_a_ending,  # Placeholder - would be modified by LLM
        para_b_opening=_remove_connectors(analysis.para_b_opening),
        rhythm_change="varied",
        explanation="Vary sentence length and structure to break uniform AI rhythm.",
        explanation_zh="变化句子长度和结构，打破均匀的AI节奏。",
        predicted_improvement=base_improvement + 12
    ))

    return options


def _generate_strategy_option(
    strategy: TransitionStrategy,
    analysis: TransitionAnalysisResult,
    context_hint: Optional[str] = None
) -> TransitionOption:
    """
    Generate option for a specific strategy
    为特定策略生成选项
    """
    base_improvement = analysis.smoothness_score // 2

    if strategy == TransitionStrategy.SEMANTIC_ECHO:
        return TransitionOption(
            strategy=TransitionStrategy.SEMANTIC_ECHO,
            strategy_name_zh="语义回声",
            para_a_ending=analysis.para_a_ending,
            para_b_opening=_remove_connectors(analysis.para_b_opening),
            key_concepts=_extract_key_concepts(analysis.para_a_ending),
            explanation="Remove explicit connectors and echo key concepts from the previous paragraph.",
            explanation_zh="移除显性连接词，回应前一段的关键概念。",
            predicted_improvement=base_improvement + 10
        )
    elif strategy == TransitionStrategy.LOGICAL_HOOK:
        return TransitionOption(
            strategy=TransitionStrategy.LOGICAL_HOOK,
            strategy_name_zh="逻辑设问",
            para_a_ending=analysis.para_a_ending,
            para_b_opening=_remove_connectors(analysis.para_b_opening),
            hook_type="implication",
            explanation="Create implicit tension at paragraph end, then address it at the start.",
            explanation_zh="在段落末尾制造隐含问题或张力，在开头进行回应。",
            predicted_improvement=base_improvement + 15
        )
    else:  # RHYTHM_BREAK
        return TransitionOption(
            strategy=TransitionStrategy.RHYTHM_BREAK,
            strategy_name_zh="节奏打断",
            para_a_ending=analysis.para_a_ending,
            para_b_opening=_remove_connectors(analysis.para_b_opening),
            rhythm_change="varied",
            explanation="Vary sentence length and structure to break uniform AI rhythm.",
            explanation_zh="变化句子长度和结构，打破均匀的AI节奏。",
            predicted_improvement=base_improvement + 12
        )


def _remove_connectors(text: str) -> str:
    """
    Remove explicit connectors from text (simple placeholder)
    从文本中移除显性连接词（简单占位符）
    """
    import re

    connectors = [
        r"^Furthermore,?\s*",
        r"^Moreover,?\s*",
        r"^Additionally,?\s*",
        r"^In addition,?\s*",
        r"^However,?\s*",
        r"^Nevertheless,?\s*",
        r"^Consequently,?\s*",
        r"^Therefore,?\s*",
        r"^Thus,?\s*",
        r"^Hence,?\s*",
    ]

    result = text
    for pattern in connectors:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)

    return result.strip()


def _extract_key_concepts(text: str) -> List[str]:
    """
    Extract key concepts from text (simple placeholder)
    从文本中提取关键概念（简单占位符）
    """
    import re

    # Simple extraction: find nouns and noun phrases
    # 简单提取：找到名词和名词短语
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[a-z]+)*\b', text)

    # Filter common words
    # 过滤常见词
    common = {"This", "That", "These", "Those", "The", "However", "Therefore"}
    concepts = [w for w in words if w not in common]

    return concepts[:3] if concepts else ["key concept"]
