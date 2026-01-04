"""
Structure Analysis API Routes (Level 1 De-AIGC)
结构分析 API 路由（Level 1 De-AIGC）

Phase 4: Document structure analysis and restructuring endpoints
第4阶段：文档结构分析和重组端点
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
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
    # Detailed improvement suggestions schemas
    SectionSuggestion,
    DetailedImprovementSuggestions,
    # Merge modify schemas
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)
from src.core.analyzer.structure import StructureAnalyzer
from src.core.analyzer.smart_structure import SmartStructureAnalyzer
from src.prompts.structure import DISRUPTION_LEVELS, DISRUPTION_STRATEGIES
from src.db.database import get_db
from src.db.models import Document, Session

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
            flag_modified(document, 'structure_analysis_cache')
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

        # Parse detailed suggestions if available
        # 解析详细建议（如果有）
        detailed_suggestions = None
        raw_suggestions = result.get("detailed_suggestions")
        if raw_suggestions and isinstance(raw_suggestions, dict):
            section_suggestions = []
            for s in raw_suggestions.get("section_suggestions", []):
                section_suggestions.append(SectionSuggestion(
                    section_number=s.get("section_number", "?"),
                    section_title=s.get("section_title", ""),
                    severity=s.get("severity", "medium"),
                    suggestion_type=s.get("suggestion_type", "restructure"),
                    suggestion_zh=s.get("suggestion_zh", ""),
                    suggestion_en=s.get("suggestion_en", ""),
                    details=s.get("details", []),
                    affected_paragraphs=s.get("affected_paragraphs", [])
                ))
            detailed_suggestions = DetailedImprovementSuggestions(
                abstract_suggestions=raw_suggestions.get("abstract_suggestions", []),
                logic_suggestions=raw_suggestions.get("logic_suggestions", []),
                section_suggestions=section_suggestions,
                priority_order=raw_suggestions.get("priority_order", []),
                overall_assessment_zh=raw_suggestions.get("overall_assessment_zh", ""),
                overall_assessment_en=raw_suggestions.get("overall_assessment_en", "")
            )

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
            detailed_suggestions=detailed_suggestions,
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
    - Style/formality analysis with mismatch detection

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

        # Get colloquialism_level from session if provided
        # 如果提供了 session_id，从 session 获取 colloquialism_level
        target_colloquialism = None
        if request.session_id:
            session = await db.get(Session, request.session_id)
            if session:
                target_colloquialism = session.colloquialism_level
                logger.info(f"Using colloquialism_level={target_colloquialism} from session {request.session_id}")

        # Check if we have cached Step 1-1 result with same colloquialism level
        # 检查是否有缓存的步骤 1-1 结果（且口语化级别相同）
        cache_key = "step1_1_cache"
        if hasattr(document, 'structure_analysis_cache') and document.structure_analysis_cache:
            cached = document.structure_analysis_cache
            if cache_key in cached:
                # Check if cached result was analyzed with same colloquialism level
                # 检查缓存结果是否使用相同的口语化级别分析
                cached_style = cached[cache_key].get("style_analysis", {})
                cached_target = cached_style.get("target_colloquialism")
                if cached_target == target_colloquialism or (cached_target is None and target_colloquialism is None):
                    logger.info(f"Using cached Step 1-1 result for document {request.document_id}")
                    return cached[cache_key]
                else:
                    logger.info(f"Cached result has different colloquialism level, re-analyzing")

        # Perform Step 1-1 analysis with colloquialism level
        # 使用口语化级别执行步骤 1-1 分析
        logger.info(f"Starting Step 1-1 structure analysis for document {request.document_id} (target_colloquialism={target_colloquialism})")
        result = await smart_analyzer.analyze_structure(document.original_text, target_colloquialism=target_colloquialism)

        # Cache the result to SQLite
        # 缓存结果到 SQLite
        if not document.structure_analysis_cache:
            document.structure_analysis_cache = {}
        document.structure_analysis_cache[cache_key] = result
        flag_modified(document, 'structure_analysis_cache')
        await db.commit()
        logger.info(f"Step 1-1 cache saved to SQLite for document {request.document_id}")

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

        # Cache the result to SQLite
        # 缓存结果到 SQLite
        document.structure_analysis_cache[step1_2_key] = result
        flag_modified(document, 'structure_analysis_cache')
        await db.commit()
        logger.info(f"Step 1-2 cache saved to SQLite for document {request.document_id}")

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
        flag_modified(document, 'structure_analysis_cache')
        await db.commit()
        logger.info(f"Cache cleared for document {document_id}")

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


# =============================================================================
# Issue-Specific Suggestion Endpoint (Step 1-1 Click-to-Expand)
# 针对特定问题的建议端点（Step 1-1 点击展开）
# =============================================================================

@router.post("/issue-suggestion")
async def get_issue_suggestion(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed suggestion for a specific structure issue
    获取针对特定结构问题的详细建议

    This endpoint uses LLM with comprehensive De-AIGC knowledge to generate:
    - Detailed diagnosis of the issue
    - Multiple modification strategies
    - A complete modification prompt for other AI tools
    - Priority tips and cautions

    Args:
        request: Issue suggestion request dict 问题建议请求字典
        db: Database session 数据库会话

    Returns:
        Dict with detailed suggestions 包含详细建议的字典
    """
    import json
    import httpx
    import re
    from src.config import get_settings
    from src.prompts.structure_deaigc import format_issue_prompt

    try:
        settings = get_settings()

        # Extract request fields
        # 提取请求字段
        document_id = request.get("documentId", "")
        issue_type = request.get("issueType", "unknown")
        issue_description = request.get("issueDescription", "")
        issue_description_zh = request.get("issueDescriptionZh", "")
        severity = request.get("severity", "medium")
        affected_positions = request.get("affectedPositions", [])
        quick_mode = request.get("quickMode", False)

        # Get document for context
        # 获取文档作为上下文
        document = await db.get(Document, document_id) if document_id else None
        document_excerpt = ""
        total_sections = 0
        total_paragraphs = 0
        structure_score = 50
        risk_level = "medium"

        if document:
            document_excerpt = document.original_text[:3000] if document.original_text else ""
            # Get cached analysis if available
            # 获取缓存的分析结果（如果有）
            if document.structure_analysis_cache:
                cache = document.structure_analysis_cache
                if "step1_1_cache" in cache:
                    step1_cache = cache["step1_1_cache"]
                    total_sections = step1_cache.get("totalSections", len(step1_cache.get("sections", [])))
                    total_paragraphs = step1_cache.get("totalParagraphs", 0)
                    structure_score = step1_cache.get("structureScore", 50)
                    risk_level = step1_cache.get("riskLevel", "medium")

        # Build prompt
        # 构建提示词
        prompt = format_issue_prompt(
            issue_type=issue_type,
            issue_description=issue_description,
            issue_description_zh=issue_description_zh,
            severity=severity,
            affected_positions=affected_positions,
            total_sections=total_sections,
            total_paragraphs=total_paragraphs,
            structure_score=structure_score,
            risk_level=risk_level,
            document_excerpt=document_excerpt,
            use_quick_mode=quick_mode
        )

        # Call LLM API
        # 调用 LLM API
        response_text = ""

        # Use Volcengine (preferred)
        # 使用火山引擎（首选）
        if settings.llm_provider == "volcengine" and settings.volcengine_api_key:
            async with httpx.AsyncClient(
                base_url=settings.volcengine_base_url,
                headers={
                    "Authorization": f"Bearer {settings.volcengine_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=90.0,
                trust_env=False
            ) as client:
                response = await client.post("/chat/completions", json={
                    "model": settings.volcengine_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4096,
                    "temperature": 0.3
                })
                response.raise_for_status()
                data = response.json()
                response_text = data["choices"][0]["message"]["content"]

        # Use DeepSeek
        # 使用 DeepSeek
        elif settings.llm_provider == "deepseek" and settings.deepseek_api_key:
            async with httpx.AsyncClient(
                base_url=settings.deepseek_base_url,
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=90.0,
                trust_env=False
            ) as client:
                response = await client.post("/chat/completions", json={
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4096,
                    "temperature": 0.3
                })
                response.raise_for_status()
                data = response.json()
                response_text = data["choices"][0]["message"]["content"]

        # Use Gemini
        # 使用 Gemini
        elif settings.llm_provider == "gemini" and settings.gemini_api_key:
            from google import genai
            client = genai.Client(api_key=settings.gemini_api_key)
            gen_response = await client.aio.models.generate_content(
                model=settings.llm_model,
                contents=prompt,
                config={"max_output_tokens": 4096, "temperature": 0.3}
            )
            response_text = gen_response.text

        else:
            raise ValueError("No LLM API configured")

        # Parse response
        # 解析响应
        response_text = response_text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            response_text = "\n".join(lines)
        response_text = response_text.strip()

        result = {}
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON
            # 尝试提取 JSON
            match = re.search(r'\{[\s\S]*\}', response_text)
            if match:
                try:
                    result = json.loads(match.group())
                except:
                    pass

        # Return response
        # 返回响应
        if quick_mode:
            return {
                "diagnosisZh": result.get("diagnosis_zh", "分析结果解析失败"),
                "quickFixZh": result.get("quick_fix_zh", "建议移除显性连接词"),
                "detailedStrategyZh": result.get("detailed_strategy_zh", ""),
                "promptSnippet": result.get("prompt_snippet", ""),
                "estimatedImprovement": result.get("estimated_improvement", 10)
            }

        return {
            "diagnosisZh": result.get("diagnosis_zh", "分析失败，请稍后重试"),
            "strategies": result.get("strategies", []),
            "modificationPrompt": result.get("modification_prompt", ""),
            "priorityTipsZh": result.get("priority_tips_zh", ""),
            "cautionZh": result.get("caution_zh", "请确保修改后仍符合学术规范")
        }

    except Exception as e:
        logger.error(f"Issue suggestion error: {e}")
        return {
            "diagnosisZh": f"【分析失败】服务暂时不可用，请稍后重试",
            "strategies": [],
            "modificationPrompt": "",
            "priorityTipsZh": "建议：删除段首显性连接词，使用语义回声承接",
            "cautionZh": "请确保修改后仍符合学术规范"
        }


# =============================================================================
# Merge Modify Endpoints (Step 1-1 Combined Issue Modification)
# 合并修改端点（Step 1-1 多问题合并修改）
# =============================================================================

# Prompt template for generating merge modification prompt
# 生成合并修改提示词的模板
MERGE_MODIFY_PROMPT_TEMPLATE = """You are a professional academic writing editor. Generate a modification prompt that can be used to fix the following issues in a document.

## TARGET STYLE LEVEL: {colloquialism_level}/10
(0 = Most Academic/Formal, 10 = Most Casual/Conversational)
{style_description}

{previous_improvements}

{semantic_echo_context}

## ISSUES TO ADDRESS:
{issues_list}

## USER'S ADDITIONAL NOTES:
{user_notes}

## YOUR TASK:
Generate a comprehensive, ACTIONABLE prompt that another AI can use to modify the document.
The prompt should:
1. Address ALL selected issues
2. Maintain the target style level ({colloquialism_level}/10)
3. Preserve the original meaning and content
4. Be specific about what to change (remove connectors, restructure sentences, etc.)
5. Be written in the SAME LANGUAGE as the document
6. IMPORTANT: Preserve all previous improvements from Step 1-1 (if any)
7. **For connector issues: Include the specific semantic echo replacements provided above**

## OUTPUT FORMAT (JSON):
{{
  "prompt": "Your detailed modification prompt here...",
  "prompt_zh": "简要说明这个提示词的作用",
  "issues_summary_zh": "已选问题摘要：...",
  "estimated_changes": 5
}}

CRITICAL: The prompt must be actionable and specific. Include examples of patterns to remove/change.
CRITICAL: The generated prompt MUST explicitly mention preserving previous improvements to avoid reverting changes.
CRITICAL: If semantic echo replacements are provided, the generated prompt MUST include these specific replacements.
"""

# Prompt template for direct modification
# 直接修改的提示词模板
MERGE_MODIFY_APPLY_TEMPLATE = """You are a professional academic writing editor specializing in De-AIGC (removing AI-writing patterns).

## DOCUMENT TO MODIFY:
{document_text}

## TARGET STYLE LEVEL: {colloquialism_level}/10
(0 = Most Academic/Formal, 10 = Most Casual/Conversational)
{style_description}

{previous_improvements}

{semantic_echo_context}

## ISSUES TO FIX:
{issues_list}

## USER'S ADDITIONAL NOTES:
{user_notes}

## YOUR TASK:
Modify the document to address ALL the listed issues while:
1. Maintaining the target style level ({colloquialism_level}/10)
2. Preserving the original meaning and structure
3. Keeping the output in the SAME LANGUAGE as the input
4. Making natural-sounding changes that a human would write
5. **CRITICAL: Preserve all improvements from previous steps (Step 1-1) - DO NOT revert any changes already made**
6. **For connector issues: USE the specific semantic echo replacements provided above**

## MODIFICATION GUIDELINES:
- Remove explicit connector words (Furthermore, Moreover, Additionally, 此外, 另外, etc.)
- Use semantic echo (repeat key concepts from previous paragraph) instead of connectors
- **When semantic echo replacements are provided above, USE THEM DIRECTLY**
- Break up formulaic sentence patterns
- Vary sentence length and structure
- Avoid AI-typical patterns like "First... Second... Third..."
- **Keep all previous improvements intact - only add new improvements, never revert**

## OUTPUT FORMAT (JSON):
{{
  "modified_text": "Your complete modified document here...",
  "changes_summary_zh": "修改摘要：1. ...; 2. ...; 3. ...",
  "changes_count": 5,
  "issues_addressed": ["connector_overuse", "linear_flow"]
}}

CRITICAL: Output the COMPLETE modified document, not just the changed parts. Preserve all content not related to the issues.
CRITICAL: If previous improvements exist, you MUST maintain them. Only make additional improvements, never revert to original patterns.
CRITICAL: If semantic echo replacements are provided, you MUST use these exact replacements in the modified text.
"""

# Style level descriptions
# 风格级别描述
STYLE_LEVEL_DESCRIPTIONS = {
    0: "Extremely formal academic writing. Use precise terminology, complex sentence structures, passive voice, and formal transitions.",
    1: "Very formal academic style. Maintain scholarly tone with occasional active voice.",
    2: "Formal academic writing. Standard academic conventions with clear, professional language.",
    3: "Academic with moderate formality. Clear and professional but not overly stiff.",
    4: "Semi-formal academic. Accessible academic writing with some conversational elements.",
    5: "Balanced style. Mix of academic precision and readable prose.",
    6: "Semi-casual professional. Clear, direct language with minimal jargon.",
    7: "Casual professional. Conversational but still professional.",
    8: "Casual writing. Friendly, conversational tone.",
    9: "Very casual. Informal, personal writing style.",
    10: "Most casual. Highly conversational, like talking to a friend."
}


@router.post("/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_merge_modify_prompt(
    request: MergeModifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a modification prompt for selected issues
    为选定的问题生成修改提示词

    User can copy this prompt to use with other AI tools.
    用户可以复制此提示词用于其他AI工具。

    Args:
        request: Merge modify request 合并修改请求
        db: Database session 数据库会话

    Returns:
        MergeModifyPromptResponse with generated prompt 包含生成提示词的响应
    """
    import json
    import httpx
    import re
    from src.config import get_settings

    try:
        settings = get_settings()

        # Get document to access Step 1-1 cache
        # 获取文档以访问 Step 1-1 缓存
        document = await db.get(Document, request.document_id)

        # Get colloquialism level from session
        # 从会话获取口语化级别
        colloquialism_level = 3  # Default to semi-formal
        if request.session_id:
            session = await db.get(Session, request.session_id)
            if session and session.colloquialism_level is not None:
                colloquialism_level = session.colloquialism_level

        style_description = STYLE_LEVEL_DESCRIPTIONS.get(colloquialism_level, STYLE_LEVEL_DESCRIPTIONS[3])

        # Build previous improvements context from Step 1-1 cache
        # 从 Step 1-1 缓存构建之前的改进上下文
        previous_improvements = _build_previous_improvements_context(document)

        # Build semantic echo context from Step 1-2 cache
        # 从 Step 1-2 缓存构建语义回声上下文
        semantic_echo_context = _build_semantic_echo_context(document)

        # Build issues list
        # 构建问题列表
        issues_list = ""
        for i, issue in enumerate(request.selected_issues, 1):
            issues_list += f"{i}. [{issue.severity.upper()}] {issue.description_zh}\n"
            if issue.affected_positions:
                issues_list += f"   Affected positions: {', '.join(issue.affected_positions)}\n"

        # Build prompt for LLM
        # 构建 LLM 提示词
        prompt = MERGE_MODIFY_PROMPT_TEMPLATE.format(
            colloquialism_level=colloquialism_level,
            style_description=style_description,
            previous_improvements=previous_improvements,
            semantic_echo_context=semantic_echo_context,
            issues_list=issues_list,
            user_notes=request.user_notes or "No additional notes"
        )

        # Call LLM
        # 调用 LLM
        response_text = await _call_llm_for_merge_modify(prompt, settings, max_tokens=2048)

        # Parse response
        # 解析响应
        result = _parse_json_response(response_text)

        return MergeModifyPromptResponse(
            prompt=result.get("prompt", "生成提示词失败，请重试"),
            prompt_zh=result.get("prompt_zh", "修改提示词"),
            issues_summary_zh=result.get("issues_summary_zh", f"已选择 {len(request.selected_issues)} 个问题"),
            colloquialism_level=colloquialism_level,
            estimated_changes=result.get("estimated_changes", len(request.selected_issues))
        )

    except Exception as e:
        logger.error(f"Generate merge modify prompt error: {e}")
        # Return a fallback prompt
        # 返回后备提示词
        fallback_prompt = _generate_fallback_prompt(request.selected_issues, request.user_notes)
        return MergeModifyPromptResponse(
            prompt=fallback_prompt,
            prompt_zh="已生成基础修改提示词",
            issues_summary_zh=f"已选择 {len(request.selected_issues)} 个问题",
            colloquialism_level=3,
            estimated_changes=len(request.selected_issues)
        )


@router.post("/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_merge_modify(
    request: MergeModifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply AI modification to document directly
    直接应用AI修改到文档

    Args:
        request: Merge modify request 合并修改请求
        db: Database session 数据库会话

    Returns:
        MergeModifyApplyResponse with modified document 包含修改后文档的响应
    """
    import json
    import httpx
    import re
    from src.config import get_settings

    try:
        settings = get_settings()

        # Get document
        # 获取文档
        document = await db.get(Document, request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get colloquialism level from session
        # 从会话获取口语化级别
        colloquialism_level = 3  # Default to semi-formal
        if request.session_id:
            session = await db.get(Session, request.session_id)
            if session and session.colloquialism_level is not None:
                colloquialism_level = session.colloquialism_level

        style_description = STYLE_LEVEL_DESCRIPTIONS.get(colloquialism_level, STYLE_LEVEL_DESCRIPTIONS[3])

        # Build previous improvements context from Step 1-1 cache
        # 从 Step 1-1 缓存构建之前的改进上下文
        previous_improvements = _build_previous_improvements_context(document)

        # Build semantic echo context from Step 1-2 cache
        # 从 Step 1-2 缓存构建语义回声上下文
        semantic_echo_context = _build_semantic_echo_context(document)

        # Build issues list
        # 构建问题列表
        issues_list = ""
        for i, issue in enumerate(request.selected_issues, 1):
            issues_list += f"{i}. [{issue.severity.upper()}] {issue.description_zh}\n"
            if issue.affected_positions:
                issues_list += f"   Affected: {', '.join(issue.affected_positions)}\n"

        # Build prompt for LLM
        # 构建 LLM 提示词
        prompt = MERGE_MODIFY_APPLY_TEMPLATE.format(
            document_text=document.original_text[:15000],  # Limit to avoid token overflow
            colloquialism_level=colloquialism_level,
            style_description=style_description,
            previous_improvements=previous_improvements,
            semantic_echo_context=semantic_echo_context,
            issues_list=issues_list,
            user_notes=request.user_notes or "No additional notes"
        )

        # Call LLM with longer timeout for document modification
        # 调用 LLM，文档修改需要更长超时
        response_text = await _call_llm_for_merge_modify(prompt, settings, max_tokens=8192, timeout=120.0)

        # Parse response
        # 解析响应
        result = _parse_json_response(response_text)

        return MergeModifyApplyResponse(
            modified_text=result.get("modified_text", document.original_text),
            changes_summary_zh=result.get("changes_summary_zh", "修改已完成"),
            changes_count=result.get("changes_count", 0),
            issues_addressed=result.get("issues_addressed", []),
            remaining_attempts=2,  # 3 total, 1 used
            colloquialism_level=colloquialism_level
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apply merge modify error: {e}")
        raise HTTPException(status_code=500, detail=f"修改失败: {str(e)}")


async def _call_llm_for_merge_modify(prompt: str, settings, max_tokens: int = 4096, timeout: float = 90.0) -> str:
    """
    Call LLM API for merge modification
    调用 LLM API 进行合并修改
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
            timeout=timeout,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.volcengine_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.3
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
            timeout=timeout,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.3
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
            config={"max_output_tokens": max_tokens, "temperature": 0.3}
        )
        return response.text

    else:
        raise ValueError("No LLM API configured")


def _parse_json_response(response: str) -> dict:
    """
    Parse LLM response to JSON
    解析 LLM 响应为 JSON
    """
    import json
    import re

    # Clean response
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
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return {}


def _build_previous_improvements_context(document) -> str:
    """
    Build context about previous improvements from Step 1-1 analysis.
    从 Step 1-1 分析结果构建之前改进的上下文。

    This helps LLM understand what changes were already suggested/made
    so it doesn't revert them in subsequent modifications.
    这帮助 LLM 了解已经建议/完成的改进，避免在后续修改中撤销它们。

    Args:
        document: Document model with structure_analysis_cache

    Returns:
        Formatted string describing previous improvements
    """
    if not document or not document.structure_analysis_cache:
        return ""

    cache = document.structure_analysis_cache
    improvements = []

    # Extract Step 1-1 issues that were identified
    # 提取 Step 1-1 中识别的问题
    step1_1_cache = cache.get("step1_1_cache", {})
    if step1_1_cache:
        structure_issues = step1_1_cache.get("structureIssues") or step1_1_cache.get("structure_issues", [])
        if structure_issues:
            for issue in structure_issues[:5]:  # Limit to top 5 to avoid prompt bloat
                desc = issue.get("descriptionZh") or issue.get("description_zh") or issue.get("description", "")
                if desc:
                    improvements.append(f"- {desc}")

        # Include style analysis context
        # 包含风格分析上下文
        style_analysis = step1_1_cache.get("styleAnalysis") or step1_1_cache.get("style_analysis", {})
        if style_analysis:
            style_name = style_analysis.get("styleNameZh") or style_analysis.get("style_name_zh", "")
            if style_name:
                improvements.append(f"- 文档原始风格: {style_name}")

    # Extract Step 1-2 issues if available
    # 提取 Step 1-2 的问题（如果有）
    step1_2_cache = cache.get("step1_2_cache", {})
    if step1_2_cache:
        # Include relationship issues context
        # 包含关系问题上下文
        relationship_issues = step1_2_cache.get("relationshipIssues") or step1_2_cache.get("relationship_issues", [])
        if relationship_issues:
            for issue in relationship_issues[:3]:  # Limit to top 3
                desc = issue.get("descriptionZh") or issue.get("description_zh") or issue.get("description", "")
                if desc:
                    improvements.append(f"- {desc}")

    if not improvements:
        return ""

    # Build the context block
    # 构建上下文块
    improvements_text = "\n".join(improvements)
    return f"""## ⚠️ PREVIOUS ANALYSIS CONTEXT (MUST PRESERVE):
The document has been analyzed in previous steps. The following issues/improvements were identified:
在之前的步骤中已对文档进行了分析，识别出以下问题/改进点：

{improvements_text}

**CRITICAL INSTRUCTION 关键指令:**
- You MUST preserve any improvements already made based on these issues
- DO NOT revert the document to patterns that were flagged as problematic
- Only make NEW improvements for the current issues, while keeping previous changes intact
- 必须保留已根据这些问题所做的改进
- 不要将文档恢复到被标记为有问题的模式
- 仅对当前问题进行新的改进，同时保持之前的更改不变
"""


def _build_semantic_echo_context(document) -> str:
    """
    Build semantic echo replacement context from Step 1-2 analysis.
    从 Step 1-2 分析结果构建语义回声替换上下文。

    This provides LLM with specific replacement examples for explicit connectors.
    这为 LLM 提供显性连接词的具体替换示例。

    Args:
        document: Document model with structure_analysis_cache

    Returns:
        Formatted string with semantic echo replacements
    """
    if not document or not document.structure_analysis_cache:
        return ""

    cache = document.structure_analysis_cache
    replacements = []

    # Extract semantic echo replacements from Step 1-2 cache
    # 从 Step 1-2 缓存提取语义回声替换
    step1_2_cache = cache.get("step1_2_cache", {})
    if step1_2_cache:
        # Get explicit connectors with replacements
        # 获取带有替换的显性连接词
        explicit_connectors = step1_2_cache.get("explicit_connectors") or step1_2_cache.get("explicitConnectors", [])
        for conn in explicit_connectors:
            word = conn.get("word", "")
            position = conn.get("position", "")
            current_opening = conn.get("current_opening") or conn.get("currentOpening", "")
            replacement = conn.get("semantic_echo_replacement") or conn.get("semanticEchoReplacement", "")
            prev_concepts = conn.get("prev_key_concepts") or conn.get("prevKeyConcepts", [])
            explanation = conn.get("replacement_explanation_zh") or conn.get("replacementExplanationZh", "")

            if current_opening and replacement:
                concepts_str = ", ".join(prev_concepts) if prev_concepts else "N/A"
                replacements.append(f"""
### 位置 {position}: "{word}"
- **原文**: {current_opening}
- **前段关键概念**: {concepts_str}
- **语义回声替换**: {replacement}
- **说明**: {explanation}""")

    # Also check Step 1-1 for any connector issues with replacements
    # 同时检查 Step 1-1 是否有带替换的连接词问题
    step1_1_cache = cache.get("step1_1_cache", {})
    if step1_1_cache:
        structure_issues = step1_1_cache.get("structureIssues") or step1_1_cache.get("structure_issues", [])
        for issue in structure_issues:
            issue_type = issue.get("type", "")
            if issue_type == "explicit_connector":
                original = issue.get("originalText") or issue.get("original_text", "")
                replacement = issue.get("semanticEchoReplacement") or issue.get("semantic_echo_replacement", "")
                if original and replacement and len(replacements) < 10:  # Limit total
                    replacements.append(f"""
### 连接词问题
- **原文**: {original}
- **语义回声替换**: {replacement}""")

    if not replacements:
        return ""

    # Build the context block
    # 构建上下文块
    replacements_text = "\n".join(replacements)
    return f"""## 🔄 SEMANTIC ECHO REPLACEMENTS (语义回声替换 - 必须使用):
The following specific replacements have been generated for explicit connector words.
**YOU MUST use these exact replacements in the modified text.**
以下是针对显性连接词生成的具体替换方案。**您必须在修改后的文本中使用这些替换。**

{replacements_text}

**HOW TO USE 使用方法:**
1. Find each original text in the document
2. Replace it with the semantic echo replacement
3. The replacement uses key concepts from the previous paragraph to create natural flow
4. Do NOT add back any explicit connectors

1. 在文档中找到每个原文
2. 用语义回声替换进行替换
3. 替换使用前一段的关键概念来创建自然的衔接
4. 不要再添加任何显性连接词
"""


def _generate_fallback_prompt(selected_issues: list, user_notes: str = None) -> str:
    """
    Generate a fallback prompt when LLM fails
    当 LLM 失败时生成后备提示词
    """
    issues_text = "\n".join([
        f"- {issue.description_zh}" for issue in selected_issues
    ])

    prompt = f"""请修改以下文档，解决这些问题：

{issues_text}

修改要求：
1. 删除显性连接词（如：Furthermore, Moreover, 此外, 另外等）
2. 使用语义回声承接上下文
3. 打破公式化的句子结构
4. 保持原文的专业性和准确性
5. 输出语言与原文保持一致

"""
    if user_notes:
        prompt += f"用户注意事项：{user_notes}\n"

    return prompt
