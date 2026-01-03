"""
Structure Analysis API Routes (Level 1 De-AIGC)
结构分析 API 路由（Level 1 De-AIGC）

Phase 4: Document structure analysis and restructuring endpoints
第4阶段：文档结构分析和重组端点
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from src.api.schemas import (
    StructureAnalysisRequest,
    StructureAnalysisResponse,
    StructureStrategy,
    StructureOption,
    LogicDiagnosisResponse,
    DocumentStructureRequest,
    ParagraphInfo,
    StructureIssue,
    BreakPoint,
    FlowRelation,
    RiskArea,
    StructureModification,
    StructureChange,
    SmartStructureResponse,
    SmartStructureIssue,
    SectionInfo,
    SmartParagraphInfo,
    ExplicitConnector,
    LogicBreak,
    # Enhanced schemas (Level 1 Enhancement)
    PredictabilityAnalysisRequest,
    PredictabilityAnalysisResponse,
    ProgressionAnalysisResult,
    FunctionDistributionResult,
    ClosureAnalysisResult,
    LexicalEchoResult,
    DisruptionRestructureRequest,
    DisruptionRestructureResponse,
    DisruptionLevel,
    # 7-Indicator Risk Card schemas
    StructuralIndicatorResponse,
    StructuralRiskCardResponse,
    CrossReferenceResult,
    RiskCardRequest,
    # Single paragraph suggestion schemas
    ParagraphSuggestionRequest,
    ParagraphSuggestionResponse,
)
from src.core.analyzer.structure import StructureAnalyzer
from src.core.analyzer.smart_structure import SmartStructureAnalyzer
from src.prompts.structure import DISRUPTION_LEVELS, DISRUPTION_STRATEGIES
from src.db.database import get_db
from src.db.models import Document

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize analyzers
# 初始化分析器
structure_analyzer = StructureAnalyzer()
smart_analyzer = SmartStructureAnalyzer()


@router.post("/", response_model=StructureAnalysisResponse)
async def analyze_structure(request: StructureAnalysisRequest):
    """
    Analyze document structure for AI patterns
    分析文档结构的AI模式

    Args:
        request: Structure analysis request 结构分析请求

    Returns:
        StructureAnalysisResponse with analysis results 包含分析结果的响应
    """
    try:
        # Perform analysis
        # 执行分析
        result = structure_analyzer.analyze(
            text=request.text,
            extract_thesis=request.extract_thesis
        )

        # Convert paragraph info to API format
        # 将段落信息转换为API格式
        paragraphs = [
            ParagraphInfo(
                index=p.index,
                first_sentence=p.first_sentence[:200] if len(p.first_sentence) > 200 else p.first_sentence,
                last_sentence=p.last_sentence[:200] if len(p.last_sentence) > 200 else p.last_sentence,
                word_count=p.word_count,
                sentence_count=p.sentence_count,
                has_topic_sentence=p.has_topic_sentence,
                has_summary_ending=p.has_summary_ending,
                connector_words=p.connector_words,
                function_type=p.function_type
            )
            for p in result.paragraphs
        ]

        # Convert issues
        # 转换问题
        issues = [
            StructureIssue(
                type=i.type,
                description=i.description,
                description_zh=i.description_zh,
                severity=i.severity,
                affected_paragraphs=i.affected_paragraphs,
                suggestion=i.suggestion,
                suggestion_zh=i.suggestion_zh
            )
            for i in result.issues
        ]

        # Convert break points
        # 转换断点
        break_points = [
            BreakPoint(
                position=bp.position,
                type=bp.type,
                description=bp.description,
                description_zh=bp.description_zh
            )
            for bp in result.break_points
        ]

        return StructureAnalysisResponse(
            total_paragraphs=result.total_paragraphs,
            total_sentences=result.total_sentences,
            total_words=result.total_words,
            avg_paragraph_length=result.avg_paragraph_length,
            paragraph_length_variance=result.paragraph_length_variance,
            structure_score=result.structure_score,
            risk_level=result.risk_level,
            paragraphs=paragraphs,
            issues=issues,
            break_points=break_points,
            core_thesis=result.core_thesis,
            key_arguments=result.key_arguments,
            has_linear_flow=result.has_linear_flow,
            has_repetitive_pattern=result.has_repetitive_pattern,
            has_uniform_length=result.has_uniform_length,
            has_predictable_order=result.has_predictable_order,
            message=result.message,
            message_zh=result.message_zh
        )

    except Exception as e:
        logger.error(f"Structure analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/with-suggestions", response_model=StructureAnalysisResponse)
async def analyze_structure_with_suggestions(request: StructureAnalysisRequest):
    """
    Analyze document structure and generate restructuring suggestions
    分析文档结构并生成重组建议

    Args:
        request: Structure analysis request 结构分析请求

    Returns:
        StructureAnalysisResponse with analysis and suggestions 包含分析和建议的响应
    """
    try:
        # Perform base analysis
        # 执行基础分析
        result = structure_analyzer.analyze(
            text=request.text,
            extract_thesis=request.extract_thesis
        )

        # Generate suggestions based on issues
        # 根据问题生成建议
        options = []

        # Only generate suggestions if there are issues
        # 仅在存在问题时生成建议
        if result.issues:
            # Option 1: Optimize Connection (gentle approach)
            # 选项1：优化连接（温和方法）
            optimize_modifications = []
            for p in result.paragraphs:
                if p.has_topic_sentence or p.connector_words:
                    optimize_modifications.append(
                        StructureModification(
                            paragraph_index=p.index,
                            change_type="rewrite_opening",
                            original=p.first_sentence[:100],
                            modified=None,  # Would be filled by LLM
                            explanation_zh="移除显式连接词，创建隐式逻辑流"
                        )
                    )

            options.append(StructureOption(
                strategy=StructureStrategy.OPTIMIZE_CONNECTION,
                strategy_name_zh="优化连接",
                modifications=optimize_modifications[:5],  # Limit to top 5
                outline=[f"段落{i+1}: {p.function_type}" for i, p in enumerate(result.paragraphs)],
                predicted_improvement=15,
                explanation_zh="保持段落顺序，优化段落之间的衔接方式"
            ))

            # Option 2: Deep Restructure (aggressive approach)
            # 选项2：深度重组（激进方法）
            if result.structure_score >= 40:
                # Suggest reordering based on function types
                # 根据功能类型建议重新排序
                new_order = list(range(len(result.paragraphs)))

                # Example: Move a body paragraph to front as hook
                # 示例：将正文段落移到前面作为钩子
                body_indices = [
                    i for i, p in enumerate(result.paragraphs)
                    if p.function_type in ["evidence", "body"]
                ]
                if body_indices and len(result.paragraphs) > 3:
                    # Move evidence paragraph after intro as hook
                    # 将证据段落移到引言后作为钩子
                    hook_idx = body_indices[0]
                    new_order = [0, hook_idx] + [
                        i for i in range(1, len(result.paragraphs))
                        if i != hook_idx
                    ]

                options.append(StructureOption(
                    strategy=StructureStrategy.DEEP_RESTRUCTURE,
                    strategy_name_zh="深度重组",
                    new_order=new_order,
                    restructure_type="hook_cycle",
                    restructure_type_zh="钩子循环",
                    changes=[
                        StructureChange(
                            type="reorder",
                            affected_paragraphs=new_order,
                            description="Reorganize to break linear flow",
                            description_zh="重新组织以打破线性流程"
                        )
                    ],
                    outline=[f"新位置{i+1}: 原段落{idx+1}" for i, idx in enumerate(new_order)],
                    predicted_improvement=25,
                    explanation_zh="重新排序段落，打破可预测的结构模式"
                ))

        # Convert to response format
        # 转换为响应格式
        paragraphs = [
            ParagraphInfo(
                index=p.index,
                first_sentence=p.first_sentence[:200] if len(p.first_sentence) > 200 else p.first_sentence,
                last_sentence=p.last_sentence[:200] if len(p.last_sentence) > 200 else p.last_sentence,
                word_count=p.word_count,
                sentence_count=p.sentence_count,
                has_topic_sentence=p.has_topic_sentence,
                has_summary_ending=p.has_summary_ending,
                connector_words=p.connector_words,
                function_type=p.function_type
            )
            for p in result.paragraphs
        ]

        issues = [
            StructureIssue(
                type=i.type,
                description=i.description,
                description_zh=i.description_zh,
                severity=i.severity,
                affected_paragraphs=i.affected_paragraphs,
                suggestion=i.suggestion,
                suggestion_zh=i.suggestion_zh
            )
            for i in result.issues
        ]

        break_points = [
            BreakPoint(
                position=bp.position,
                type=bp.type,
                description=bp.description,
                description_zh=bp.description_zh
            )
            for bp in result.break_points
        ]

        return StructureAnalysisResponse(
            total_paragraphs=result.total_paragraphs,
            total_sentences=result.total_sentences,
            total_words=result.total_words,
            avg_paragraph_length=result.avg_paragraph_length,
            paragraph_length_variance=result.paragraph_length_variance,
            structure_score=result.structure_score,
            risk_level=result.risk_level,
            paragraphs=paragraphs,
            issues=issues,
            break_points=break_points,
            core_thesis=result.core_thesis,
            key_arguments=result.key_arguments,
            has_linear_flow=result.has_linear_flow,
            has_repetitive_pattern=result.has_repetitive_pattern,
            has_uniform_length=result.has_uniform_length,
            has_predictable_order=result.has_predictable_order,
            options=options,
            message=result.message,
            message_zh=result.message_zh
        )

    except Exception as e:
        logger.error(f"Structure analysis with suggestions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest/{strategy}", response_model=StructureOption)
async def get_structure_suggestion(
    strategy: StructureStrategy,
    request: StructureAnalysisRequest
):
    """
    Get suggestion for a specific restructuring strategy
    获取特定重组策略的建议

    Args:
        strategy: Restructuring strategy 重组策略
        request: Structure analysis request 结构分析请求

    Returns:
        StructureOption with specific suggestion 包含特定建议的选项
    """
    try:
        # Perform analysis
        # 执行分析
        result = structure_analyzer.analyze(
            text=request.text,
            extract_thesis=request.extract_thesis
        )

        if strategy == StructureStrategy.OPTIMIZE_CONNECTION:
            # Generate optimize connection suggestion
            # 生成优化连接建议
            modifications = []
            for p in result.paragraphs:
                if p.has_topic_sentence or p.connector_words:
                    modifications.append(
                        StructureModification(
                            paragraph_index=p.index,
                            change_type="rewrite_opening",
                            original=p.first_sentence[:100],
                            modified=None,
                            explanation_zh="建议移除显式连接词"
                        )
                    )

            return StructureOption(
                strategy=StructureStrategy.OPTIMIZE_CONNECTION,
                strategy_name_zh="优化连接",
                modifications=modifications[:5],
                outline=[f"段落{i+1}: {p.function_type}" for i, p in enumerate(result.paragraphs)],
                predicted_improvement=15,
                explanation_zh="保持顺序，优化衔接"
            )

        elif strategy == StructureStrategy.DEEP_RESTRUCTURE:
            # Generate deep restructure suggestion
            # 生成深度重组建议
            new_order = list(range(len(result.paragraphs)))

            # Suggest moving evidence to front
            # 建议将证据移到前面
            body_indices = [
                i for i, p in enumerate(result.paragraphs)
                if p.function_type in ["evidence", "body"]
            ]
            if body_indices and len(result.paragraphs) > 3:
                hook_idx = body_indices[0]
                new_order = [0, hook_idx] + [
                    i for i in range(1, len(result.paragraphs))
                    if i != hook_idx
                ]

            return StructureOption(
                strategy=StructureStrategy.DEEP_RESTRUCTURE,
                strategy_name_zh="深度重组",
                new_order=new_order,
                restructure_type="hook_cycle",
                restructure_type_zh="钩子循环",
                changes=[
                    StructureChange(
                        type="reorder",
                        affected_paragraphs=new_order,
                        description="Reorganize paragraph order",
                        description_zh="重新组织段落顺序"
                    )
                ],
                outline=[f"新位置{i+1}: 原段落{idx+1}" for i, idx in enumerate(new_order)],
                predicted_improvement=25,
                explanation_zh="打破线性结构，创建钩子循环模式"
            )

    except Exception as e:
        logger.error(f"Get structure suggestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/diagnosis", response_model=LogicDiagnosisResponse)
async def get_logic_diagnosis(request: StructureAnalysisRequest):
    """
    Get logic diagnosis card for document
    获取文档的逻辑诊断卡

    Args:
        request: Structure analysis request 结构分析请求

    Returns:
        LogicDiagnosisResponse with diagnosis card data 包含诊断卡数据的响应
    """
    try:
        # Perform analysis
        # 执行分析
        result = structure_analyzer.analyze(
            text=request.text,
            extract_thesis=request.extract_thesis
        )

        # Generate flow map
        # 生成流程图
        flow_map = []
        for i in range(len(result.paragraphs) - 1):
            curr = result.paragraphs[i]
            next_para = result.paragraphs[i + 1]

            # Determine relationship
            # 确定关系
            if next_para.connector_words:
                relation = "continuation"
                symbol = "→"
            elif curr.function_type == "evidence" and next_para.function_type == "analysis":
                relation = "evidence"
                symbol = "⤵"
            elif curr.function_type == next_para.function_type:
                relation = "comparison"
                symbol = "↔"
            else:
                relation = "continuation"
                symbol = "→"

            # Check for gaps
            # 检查间隙
            for bp in result.break_points:
                if bp.position == i + 1:
                    relation = "gap"
                    symbol = "✗"
                    break

            flow_map.append(FlowRelation(
                **{"from": i, "to": i + 1},
                relation=relation,
                symbol=symbol
            ))

        # Determine structure pattern
        # 确定结构模式
        if result.has_linear_flow:
            pattern = "linear"
            pattern_zh = "线性"
        elif result.has_repetitive_pattern:
            pattern = "parallel"
            pattern_zh = "并列"
        else:
            pattern = "nested"
            pattern_zh = "嵌套"

        # Generate risk areas
        # 生成风险区域
        risk_areas = []
        for p in result.paragraphs:
            risk_level = "low"
            reason = ""
            reason_zh = ""

            if p.has_topic_sentence and p.connector_words:
                risk_level = "high"
                reason = "Topic sentence with explicit connectors"
                reason_zh = "主题句配合显式连接词"
            elif p.has_topic_sentence:
                risk_level = "medium"
                reason = "Topic sentence pattern detected"
                reason_zh = "检测到主题句模式"
            elif p.connector_words:
                risk_level = "medium"
                reason = "Explicit connectors detected"
                reason_zh = "检测到显式连接词"

            if risk_level != "low":
                risk_areas.append(RiskArea(
                    paragraph=p.index,
                    risk_level=risk_level,
                    reason=reason,
                    reason_zh=reason_zh
                ))

        # Determine recommended strategy
        # 确定推荐策略
        if result.structure_score >= 40:
            recommended = StructureStrategy.DEEP_RESTRUCTURE
            rec_reason = "High structure score requires significant reorganization"
            rec_reason_zh = "高结构分数需要显著重组"
        else:
            recommended = StructureStrategy.OPTIMIZE_CONNECTION
            rec_reason = "Moderate issues can be fixed with connection optimization"
            rec_reason_zh = "中等问题可以通过优化连接修复"

        return LogicDiagnosisResponse(
            flow_map=flow_map,
            structure_pattern=pattern,
            structure_pattern_zh=pattern_zh,
            pattern_description=f"Document follows a {pattern} structure pattern",
            pattern_description_zh=f"文档遵循{pattern_zh}结构模式",
            risk_areas=risk_areas,
            recommended_strategy=recommended,
            recommendation_reason=rec_reason,
            recommendation_reason_zh=rec_reason_zh
        )

    except Exception as e:
        logger.error(f"Logic diagnosis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document", response_model=SmartStructureResponse)
async def analyze_document_structure(
    request: DocumentStructureRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze structure of a document by ID using smart LLM analysis
    使用智能 LLM 分析按 ID 分析文档结构

    Features:
    - Filters non-paragraph content (titles, tables, figures)
    - Uses paper section numbering (1, 1.1, 2.3.1)
    - Generates meaningful content summaries
    - Labels each paragraph with position like "3.2(1)"
    - Caches results to avoid repeated LLM calls
    - 缓存结果以避免重复的 LLM 调用

    Args:
        request: Document structure request 文档结构请求
        db: Database session 数据库会话

    Returns:
        SmartStructureResponse with analysis results 包含分析结果的响应
    """
    try:
        # Get document
        # 获取文档
        document = await db.get(Document, request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if we have cached analysis result
        # 检查是否有缓存的分析结果
        if document.structure_analysis_cache:
            logger.info(f"Using cached structure analysis for document {request.document_id}")
            result = document.structure_analysis_cache
        else:
            # Use smart LLM-based analysis
            # 使用智能 LLM 分析
            logger.info(f"Starting smart structure analysis for document {request.document_id}")
            result = await smart_analyzer.analyze(document.original_text)
            logger.info(f"Smart analysis completed: {result.get('total_paragraphs', 0)} paragraphs found")

            # Cache the result in database
            # 将结果缓存到数据库
            document.structure_analysis_cache = result
            await db.commit()
            logger.info(f"Cached structure analysis for document {request.document_id}")

        # Convert to response format
        # 转换为响应格式
        sections = [
            SectionInfo(
                number=s.get("number", "?"),
                title=s.get("title", ""),
                paragraphs=[
                    SmartParagraphInfo(
                        position=p.get("position", "?"),
                        summary=p.get("summary", ""),
                        summary_zh=p.get("summary_zh", ""),
                        first_sentence=p.get("first_sentence", "")[:200],
                        last_sentence=p.get("last_sentence", "")[:200],
                        word_count=p.get("word_count", 0),
                        ai_risk=p.get("ai_risk", "unknown"),
                        ai_risk_reason=p.get("ai_risk_reason", ""),
                        # New fields for detailed rewrite suggestions
                        # 新字段：详细修改建议
                        rewrite_suggestion_zh=p.get("rewrite_suggestion_zh"),
                        rewrite_example=p.get("rewrite_example")
                    )
                    for p in s.get("paragraphs", [])
                ]
            )
            for s in result.get("sections", [])
        ]

        # Convert issues
        # 转换问题
        # Handle case where LLM returns "All" instead of a list
        # 处理LLM返回"All"而非列表的情况
        def ensure_list(val):
            if isinstance(val, list):
                return val
            elif isinstance(val, str):
                return [val] if val else []
            return []

        issues = [
            SmartStructureIssue(
                type=i.get("type", "unknown"),
                description=i.get("description", ""),
                description_zh=i.get("description_zh", ""),
                severity=i.get("severity", "low"),
                affected_positions=ensure_list(i.get("affected_positions", []))
            )
            for i in result.get("issues", [])
        ]

        # Build compatible paragraphs list for existing frontend
        # 构建与现有前端兼容的段落列表
        paragraphs = []
        idx = 0
        for section in sections:
            for p in section.paragraphs:
                paragraphs.append(ParagraphInfo(
                    index=idx,
                    first_sentence=p.first_sentence,
                    last_sentence=p.last_sentence,
                    word_count=p.word_count,
                    sentence_count=0,
                    has_topic_sentence=False,
                    has_summary_ending=False,
                    connector_words=[],
                    function_type="body",
                    position=p.position,
                    summary=p.summary,
                    summary_zh=p.summary_zh,
                    ai_risk=p.ai_risk,
                    ai_risk_reason=p.ai_risk_reason,
                    # New rewrite suggestion fields
                    # 新的修改建议字段
                    rewrite_suggestion_zh=p.rewrite_suggestion_zh,
                    rewrite_example=p.rewrite_example
                ))
                idx += 1

        # Extract pattern flags from score breakdown
        # 从分数分解中提取模式标志
        score_breakdown = result.get("score_breakdown", {})

        # Convert explicit connectors
        # 转换显性连接词
        explicit_connectors = [
            ExplicitConnector(
                word=c.get("word", ""),
                position=c.get("position", ""),
                location=c.get("location", "paragraph_start"),
                severity=c.get("severity", "high")
            )
            for c in result.get("explicit_connectors", [])
        ]

        # Convert logic breaks
        # 转换逻辑断裂点
        # Note: lb.get("key", "") returns None if key exists with null value
        # Pydantic v2 treats explicit None differently - always convert to empty string
        # 注意：当key存在但值为null时，lb.get("key", "")返回None
        # Pydantic v2 对显式 None 处理不同 - 始终转换为空字符串
        logic_breaks = [
            LogicBreak(
                from_position=lb.get("from_position") or "",
                to_position=lb.get("to_position") or "",
                transition_type=lb.get("transition_type") or "abrupt",
                issue=lb.get("issue") or "",
                issue_zh=lb.get("issue_zh") or "",
                suggestion=lb.get("suggestion") or "",  # Empty string if None/null
                suggestion_zh=lb.get("suggestion_zh") or ""  # Empty string if None/null
            )
            for lb in result.get("logic_breaks", [])
        ]

        return SmartStructureResponse(
            sections=sections,
            total_paragraphs=result.get("total_paragraphs", len(paragraphs)),
            total_sections=result.get("total_sections", len(sections)),
            structure_score=result.get("structure_score", 0),
            risk_level=result.get("risk_level", "low"),
            issues=issues,
            score_breakdown=score_breakdown,
            recommendation=result.get("recommendation", ""),
            recommendation_zh=result.get("recommendation_zh", ""),
            explicit_connectors=explicit_connectors,
            logic_breaks=logic_breaks,
            paragraphs=paragraphs,
            has_linear_flow=score_breakdown.get("linear_flow", 0) > 0,
            has_repetitive_pattern=score_breakdown.get("repetitive_pattern", 0) > 0,
            has_uniform_length=score_breakdown.get("uniform_length", 0) > 0,
            has_predictable_order=score_breakdown.get("predictable_order", 0) > 0,
            options=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document structure analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Step 1-1 and Step 1-2: Two-Phase Analysis Endpoints
# 步骤 1-1 和 1-2：两阶段分析端点
# =============================================================================

@router.post("/document/step1-1")
async def analyze_document_structure_step1(
    request: DocumentStructureRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1-1: Analyze document STRUCTURE only (global patterns)
    步骤 1-1：仅分析文档结构（全局模式）

    This endpoint performs the first phase of analysis:
    - Section structure identification
    - Paragraph identification
    - Global structural patterns (linear flow, symmetry, etc.)
    - Structure score calculation

    Args:
        request: Document structure request 文档结构请求
        db: Database session 数据库会话

    Returns:
        Structure analysis result 结构分析结果
    """
    try:
        # Get document
        # 获取文档
        document = await db.get(Document, request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if we have cached Step 1-1 result
        # 检查是否有缓存的步骤 1-1 结果
        cache_key = "step1_1_cache"
        if hasattr(document, 'structure_analysis_cache') and document.structure_analysis_cache:
            cached = document.structure_analysis_cache
            if cache_key in cached:
                logger.info(f"Using cached Step 1-1 result for document {request.document_id}")
                return cached[cache_key]

        # Perform Step 1-1 analysis
        # 执行步骤 1-1 分析
        logger.info(f"Starting Step 1-1 structure analysis for document {request.document_id}")
        result = await smart_analyzer.analyze_structure(document.original_text)

        # Cache the result
        # 缓存结果
        if not document.structure_analysis_cache:
            document.structure_analysis_cache = {}
        document.structure_analysis_cache[cache_key] = result
        await db.commit()

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Step 1-1 analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document/step1-2")
async def analyze_document_relationships_step2(
    request: DocumentStructureRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1-2: Analyze paragraph RELATIONSHIPS (connections, transitions)
    步骤 1-2：分析段落关系（连接、过渡）

    This endpoint performs the second phase of analysis:
    - Explicit connector word detection
    - Logic break points between paragraphs
    - AI risk assessment for each paragraph
    - Rewrite suggestions

    Requires Step 1-1 to be completed first.

    Args:
        request: Document structure request 文档结构请求
        db: Database session 数据库会话

    Returns:
        Relationship analysis result 关系分析结果
    """
    try:
        # Get document
        # 获取文档
        document = await db.get(Document, request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if Step 1-1 has been completed
        # 检查步骤 1-1 是否已完成
        step1_1_key = "step1_1_cache"
        step1_2_key = "step1_2_cache"

        if not document.structure_analysis_cache or step1_1_key not in document.structure_analysis_cache:
            raise HTTPException(
                status_code=400,
                detail="Step 1-1 (structure analysis) must be completed first"
            )

        # Check if we have cached Step 1-2 result
        # 检查是否有缓存的步骤 1-2 结果
        if step1_2_key in document.structure_analysis_cache:
            logger.info(f"Using cached Step 1-2 result for document {request.document_id}")
            return document.structure_analysis_cache[step1_2_key]

        # Get Step 1-1 result
        # 获取步骤 1-1 结果
        structure_result = document.structure_analysis_cache[step1_1_key]

        # Perform Step 1-2 analysis
        # 执行步骤 1-2 分析
        logger.info(f"Starting Step 1-2 relationship analysis for document {request.document_id}")
        result = await smart_analyzer.analyze_relationships(
            document.original_text,
            structure_result
        )

        # Cache the result
        # 缓存结果
        document.structure_analysis_cache[step1_2_key] = result
        await db.commit()

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Step 1-2 analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/document/{document_id}/cache")
async def clear_analysis_cache(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Clear analysis cache for a document (allows re-analysis)
    清除文档的分析缓存（允许重新分析）

    Args:
        document_id: Document ID 文档ID
        db: Database session 数据库会话

    Returns:
        Success message 成功消息
    """
    try:
        document = await db.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        document.structure_analysis_cache = None
        await db.commit()

        return {"message": "Cache cleared successfully", "document_id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies")
async def get_structure_strategies():
    """
    Get available structure strategies
    获取可用的结构策略

    Returns:
        List of strategy descriptions 策略描述列表
    """
    return {
        "strategies": [
            {
                "id": "optimize_connection",
                "name": "Optimize Connection",
                "name_zh": "优化连接",
                "description": "Improve paragraph connections without changing content order",
                "description_zh": "在不改变内容顺序的情况下改善段落连接"
            },
            {
                "id": "deep_restructure",
                "name": "Deep Restructure",
                "name_zh": "深度重组",
                "description": "Reorder and reorganize content for maximum naturalness",
                "description_zh": "重新排序和组织内容以获得最大自然度"
            }
        ]
    }


# =============================================================================
# Enhanced Structure Analysis Endpoints (Level 1 Enhancement)
# 增强结构分析端点（Level 1增强）
# =============================================================================

@router.post("/predictability", response_model=PredictabilityAnalysisResponse)
async def analyze_predictability(request: PredictabilityAnalysisRequest):
    """
    Analyze document structure predictability
    分析文档结构预测性

    This endpoint provides detailed analysis of:
    - Progression type (monotonic vs non-monotonic)
    - Function distribution (uniform vs asymmetric)
    - Closure pattern (strong vs weak/open)
    - Lexical echo (explicit connectors vs semantic bridges)

    Args:
        request: Predictability analysis request 预测性分析请求

    Returns:
        PredictabilityAnalysisResponse with detailed analysis 包含详细分析的响应
    """
    try:
        # Perform full structure analysis
        # 执行完整结构分析
        result = structure_analyzer.analyze(
            text=request.text,
            extract_thesis=True
        )

        # Convert progression analysis
        # 转换推进分析
        progression = None
        if result.progression_analysis:
            progression = ProgressionAnalysisResult(
                progression_type=result.progression_analysis.progression_type,
                progression_type_zh=result.progression_analysis.progression_type_zh,
                forward_transitions=result.progression_analysis.forward_transitions,
                backward_references=result.progression_analysis.backward_references,
                conditional_statements=result.progression_analysis.conditional_statements,
                score=result.progression_analysis.score
            )

        # Convert function distribution
        # 转换功能分布
        distribution = None
        if result.function_distribution:
            distribution = FunctionDistributionResult(
                distribution_type=result.function_distribution.distribution_type,
                distribution_type_zh=result.function_distribution.distribution_type_zh,
                function_counts=result.function_distribution.function_counts,
                depth_variance=result.function_distribution.depth_variance,
                longest_section_ratio=result.function_distribution.longest_section_ratio,
                score=result.function_distribution.score,
                asymmetry_opportunities=result.function_distribution.asymmetry_opportunities
            )

        # Convert closure analysis
        # 转换闭合分析
        closure = None
        if result.closure_analysis:
            closure = ClosureAnalysisResult(
                closure_type=result.closure_analysis.closure_type,
                closure_type_zh=result.closure_analysis.closure_type_zh,
                has_formulaic_ending=result.closure_analysis.has_formulaic_ending,
                has_complete_resolution=result.closure_analysis.has_complete_resolution,
                open_questions=result.closure_analysis.open_questions,
                hedging_in_conclusion=result.closure_analysis.hedging_in_conclusion,
                score=result.closure_analysis.score,
                detected_patterns=result.closure_analysis.detected_patterns
            )

        # Convert lexical echo analysis
        # 转换词汇回声分析
        lexical_echo = None
        if result.lexical_echo_analysis:
            lexical_echo = LexicalEchoResult(
                total_transitions=result.lexical_echo_analysis.total_transitions,
                echo_transitions=result.lexical_echo_analysis.echo_transitions,
                explicit_connector_transitions=result.lexical_echo_analysis.explicit_connector_transitions,
                echo_ratio=result.lexical_echo_analysis.echo_ratio,
                score=result.lexical_echo_analysis.score,
                transition_details=result.lexical_echo_analysis.transition_details
            )

        # Determine recommended disruption level based on score
        # 根据分数确定推荐的扰动等级
        if result.structure_score >= 60:
            recommended_level = "strong"
            recommended_strategies = ["inversion", "conflict_injection", "weak_closure", "asymmetry"]
        elif result.structure_score >= 35:
            recommended_level = "medium"
            recommended_strategies = ["lexical_echo", "asymmetry", "local_reorder"]
        else:
            recommended_level = "light"
            recommended_strategies = ["rewrite_opening", "remove_connector", "lexical_echo"]

        return PredictabilityAnalysisResponse(
            total_score=result.structure_score,
            risk_level=result.risk_level,
            progression_analysis=progression,
            function_distribution=distribution,
            closure_analysis=closure,
            lexical_echo_analysis=lexical_echo,
            recommended_disruption_level=recommended_level,
            recommended_strategies=recommended_strategies,
            message=result.message,
            message_zh=result.message_zh
        )

    except Exception as e:
        logger.error(f"Predictability analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disruption-levels")
async def get_disruption_levels():
    """
    Get available disruption levels and their configurations
    获取可用的扰动等级及其配置

    Returns:
        Dictionary of disruption levels 扰动等级字典
    """
    return {
        "levels": DISRUPTION_LEVELS,
        "strategies": DISRUPTION_STRATEGIES
    }


@router.get("/disruption-strategies")
async def get_disruption_strategies():
    """
    Get available disruption strategies
    获取可用的扰动策略

    Returns:
        List of strategy descriptions 策略描述列表
    """
    strategies = []
    for key, value in DISRUPTION_STRATEGIES.items():
        strategies.append({
            "id": key,
            "name": value["name"],
            "name_zh": value["name_zh"],
            "description": value["description"],
            "description_zh": value["description_zh"],
            "prompt_instruction": value["prompt_instruction"]
        })
    return {"strategies": strategies}


# =============================================================================
# 7-Indicator Structural Risk Card Endpoint
# 7指征结构风险卡片端点
# =============================================================================

@router.post("/risk-card", response_model=StructuralRiskCardResponse)
async def get_structural_risk_card(request: RiskCardRequest):
    """
    Get 7-indicator structural risk card for user visualization
    获取7指征结构风险卡片用于用户可视化

    Returns a visual risk card showing:
    - 7 AI structural indicators with emoji and color
    - Whether each indicator is triggered
    - Overall risk level and summary

    The 7 indicators are:
    1. ⚖️ Perfect Symmetry (逻辑推进对称) - ★★★
    2. 📊 Uniform Function (段落功能均匀) - ★★☆
    3. 🔗 Over-signaled Transitions (连接词依赖) - ★★★
    4. 📝 Linear Enumeration (单一线性推进) - ★★★
    5. 📏 Rhythmic Regularity (段落节奏均衡) - ★★☆
    6. 🔒 Over-conclusive Ending (结尾过度闭合) - ★★☆
    7. 🔄 No Cross-References (缺乏回指结构) - ★★☆

    Args:
        request: Risk card analysis request 风险卡片分析请求

    Returns:
        StructuralRiskCardResponse with 7 indicators 包含7个指征的响应
    """
    try:
        # Perform full structure analysis
        # 执行完整结构分析
        result = structure_analyzer.analyze(
            text=request.text,
            extract_thesis=True
        )

        # Get the risk card from the result
        # 从结果中获取风险卡片
        if not result.risk_card:
            raise HTTPException(status_code=500, detail="Failed to generate risk card")

        # Convert to response format
        # 转换为响应格式
        indicators = [
            StructuralIndicatorResponse(
                id=ind.id,
                name=ind.name,
                name_zh=ind.name_zh,
                triggered=ind.triggered,
                risk_level=ind.risk_level,
                emoji=ind.emoji,
                color=ind.color,
                description=ind.description,
                description_zh=ind.description_zh,
                details=ind.details,
                details_zh=ind.details_zh
            )
            for ind in result.risk_card.indicators
        ]

        return StructuralRiskCardResponse(
            indicators=indicators,
            triggered_count=result.risk_card.triggered_count,
            overall_risk=result.risk_card.overall_risk,
            overall_risk_zh=result.risk_card.overall_risk_zh,
            summary=result.risk_card.summary,
            summary_zh=result.risk_card.summary_zh,
            total_score=result.risk_card.total_score
        )

    except Exception as e:
        logger.error(f"Risk card generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicator-config")
async def get_indicator_config():
    """
    Get the 7-indicator configuration for UI display
    获取7指征配置用于UI显示

    Returns:
        Configuration for all 7 indicators with emoji, colors, and descriptions
    """
    from src.core.analyzer.structure import StructureAnalyzer

    return {
        "indicators": StructureAnalyzer.INDICATOR_CONFIG,
        "summary_text": "AI写作的最大特征不是语法完美，而是结构太完美。",
        "summary_text_en": "The biggest feature of AI writing is not perfect grammar, but perfect structure."
    }


# =============================================================================
# Single Paragraph Suggestion Endpoint
# 单个段落建议端点
# =============================================================================

# Prompt for generating single paragraph rewrite suggestions
# 生成单个段落改写建议的提示词
PARAGRAPH_SUGGESTION_PROMPT = """You are an expert De-AIGC consultant. Analyze this paragraph and provide specific rewriting advice to remove AI-writing patterns.

## PARAGRAPH TEXT:
{paragraph_text}

## PARAGRAPH POSITION: {paragraph_position}

## KNOWN AI RISK: {ai_risk} - {ai_risk_reason}

## CONTEXT (if available):
{context_hint}

## YOUR TASK:
Generate a SPECIFIC, ACTIONABLE Chinese rewriting suggestion for this paragraph. Focus on:
1. Identifying specific AI writing patterns (explicit connectors, formulaic structure, etc.)
2. Providing concrete strategies to humanize the text
3. Giving an example of how to rewrite key sentences

## OUTPUT FORMAT (JSON):
{{
  "rewrite_suggestion_zh": "【问题诊断】段首使用显性连接词'Furthermore'，属于典型AI写作痕迹。段落结构采用'问题-分析-结论'公式化模式。\\n【修改策略】1. 删除段首连接词，改用语义回声承接上段关键概念；2. 打散公式化结构，将结论提前或融入论述中。\\n【改写提示】可将开头改为直接承接上段内容，如'土壤盐分累积的这一趋势在...'",
  "rewrite_example": "The escalating trend of soil salinization poses new challenges to traditional agriculture. In the North China Plain, monitoring data from the past decade reveals...",
  "ai_risk": "high",
  "ai_risk_reason": "段首使用显性连接词'Furthermore'，采用公式化结构"
}}

CRITICAL RULES:
- The rewrite_suggestion_zh MUST be in Chinese
- The rewrite_suggestion_zh MUST include【问题诊断】【修改策略】【改写提示】sections
- Quote specific text from the paragraph in the diagnosis
- Provide concrete examples, not generic advice
- The rewrite_example should be in ENGLISH showing a better version of the first 1-2 sentences
- The ai_risk_reason should be in CHINESE (中文描述，引用原文时保留原语言)
"""


@router.post("/paragraph-suggestion", response_model=ParagraphSuggestionResponse)
async def get_paragraph_suggestion(request: ParagraphSuggestionRequest):
    """
    Get rewrite suggestion for a single paragraph
    获取单个段落的改写建议

    This endpoint generates specific, actionable rewriting advice
    for a single paragraph using LLM analysis.
    此端点使用 LLM 分析为单个段落生成具体可行的改写建议。

    Args:
        request: Paragraph suggestion request 段落建议请求

    Returns:
        ParagraphSuggestionResponse with rewrite suggestions 包含改写建议的响应
    """
    try:
        import httpx
        import json
        from src.config import get_settings

        settings = get_settings()

        # Build prompt
        # 构建提示词
        prompt = PARAGRAPH_SUGGESTION_PROMPT.format(
            paragraph_text=request.paragraph_text[:2000],  # Limit length
            paragraph_position=request.paragraph_position,
            ai_risk=request.ai_risk or "unknown",
            ai_risk_reason=request.ai_risk_reason or "Not yet analyzed",
            context_hint=request.context_hint or "No context provided"
        )

        # Call LLM API
        # 调用 LLM API
        response_text = await _call_llm_for_suggestion(prompt, settings)

        # Parse response
        # 解析响应
        result = _parse_suggestion_response(response_text)

        return ParagraphSuggestionResponse(
            paragraph_position=request.paragraph_position,
            rewrite_suggestion_zh=result.get("rewrite_suggestion_zh", "【问题诊断】分析失败\n【修改策略】请稍后重试\n【改写提示】无"),
            rewrite_example=result.get("rewrite_example"),
            ai_risk=result.get("ai_risk", request.ai_risk or "unknown"),
            ai_risk_reason=result.get("ai_risk_reason", request.ai_risk_reason or "")
        )

    except Exception as e:
        logger.error(f"Paragraph suggestion error: {e}")
        # Return a fallback response instead of error
        # 返回后备响应而不是错误
        return ParagraphSuggestionResponse(
            paragraph_position=request.paragraph_position,
            rewrite_suggestion_zh=f"【问题诊断】分析服务暂时不可用\n【修改策略】请稍后重试\n【改写提示】建议删除段首显性连接词，改用语义承接",
            rewrite_example=None,
            ai_risk=request.ai_risk or "unknown",
            ai_risk_reason=request.ai_risk_reason or ""
        )


async def _call_llm_for_suggestion(prompt: str, settings) -> str:
    """
    Call LLM API for paragraph suggestion
    调用 LLM API 获取段落建议
    """
    import httpx

    # Use Volcengine (preferred)
    # 使用火山引擎（首选）
    if settings.llm_provider == "volcengine" and settings.volcengine_api_key:
        async with httpx.AsyncClient(
            base_url=settings.volcengine_base_url,
            headers={
                "Authorization": f"Bearer {settings.volcengine_api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.volcengine_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2048,
                "temperature": 0.2
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    # Use DeepSeek
    # 使用 DeepSeek
    elif settings.llm_provider == "deepseek" and settings.deepseek_api_key:
        async with httpx.AsyncClient(
            base_url=settings.deepseek_base_url,
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2048,
                "temperature": 0.2
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    # Use Gemini
    # 使用 Gemini
    elif settings.llm_provider == "gemini" and settings.gemini_api_key:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
            config={"max_output_tokens": 2048, "temperature": 0.2}
        )
        return response.text

    else:
        raise ValueError("No LLM API configured")


def _parse_suggestion_response(response: str) -> dict:
    """
    Parse LLM response to JSON
    解析 LLM 响应为 JSON
    """
    import json

    # Clean response (remove markdown code blocks if present)
    # 清理响应
    response = response.strip()
    if response.startswith("```"):
        lines = response.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        response = "\n".join(lines)
    response = response.strip()

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        # 尝试从响应中提取 JSON
        import re
        match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        # Return default
        return {
            "rewrite_suggestion_zh": "【问题诊断】无法解析分析结果\n【修改策略】请重试\n【改写提示】建议检查段落结构",
            "rewrite_example": None,
            "ai_risk": "unknown",
            "ai_risk_reason": "分析失败"
        }
