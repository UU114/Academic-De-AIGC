"""
Document Layer API Routes (Layer 5)
文档层API路由（第5层）

Endpoints:
- POST /structure - Step 1.1: Structure Analysis
- POST /risk - Step 1.2: Global Risk Assessment
- POST /analyze - Combined document analysis
- POST /connectors - Step 1.4: Connector & Transition Analysis
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
import logging
import time
import re

from src.api.routes.analysis.schemas import (
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
    DocumentSection,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
    IssueSeverity,
    ConnectorAnalysisRequest,
    ConnectorAnalysisResponse,
    TransitionResultSchema,
    TransitionIssueSchema,
    ParagraphLengthAnalysisRequest,
    ParagraphLengthAnalysisResponse,
    ParagraphLengthInfo,
    ParagraphLengthStrategy,
    ProgressionClosureRequest,
    ProgressionClosureResponse,
    ProgressionMarker,
    ProgressionType,
    ClosureType,
    ContentSubstantialityRequest,
    ContentSubstantialityResponse,
    ParagraphSubstantiality,
    SubstantialityLevel,
)
from src.core.analyzer.layers import DocumentOrchestrator, LayerContext
from src.core.analyzer.transition import TransitionAnalyzer
from src.core.analyzer.structure_predictability import StructurePredictabilityAnalyzer
import statistics

logger = logging.getLogger(__name__)
router = APIRouter()


def _convert_issue(issue) -> DetectionIssue:
    """Convert internal issue to API schema"""
    return DetectionIssue(
        type=issue.type,
        description=issue.description,
        description_zh=issue.description_zh,
        severity=IssueSeverity(issue.severity.value),
        layer=LayerLevel.DOCUMENT,
        position=issue.position,
        suggestion=issue.suggestion,
        suggestion_zh=issue.suggestion_zh,
        details=issue.details,
    )


@router.post("/structure", response_model=DocumentAnalysisResponse)
async def analyze_document_structure(request: DocumentAnalysisRequest):
    """
    Step 1.1: Structure Analysis
    步骤 1.1：结构分析

    Analyzes document structure including:
    - Progression predictability
    - Function uniformity
    - Closure strength
    - Length regularity
    - Connector explicitness
    """
    start_time = time.time()

    try:
        orchestrator = DocumentOrchestrator()

        # Create context with text
        context = LayerContext(full_text=request.text)

        # Run analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract structure-specific details
        structure_details = result.details.get("structure_analysis", {})
        predictability = structure_details.get("predictability", {})

        return DocumentAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=result.details,
            processing_time_ms=processing_time_ms,
            structure=structure_details,
            predictability_score=predictability,
            paragraph_count=structure_details.get("paragraph_count", 0),
            word_count=structure_details.get("total_word_count", 0),
        )

    except Exception as e:
        logger.error(f"Document structure analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk", response_model=DocumentAnalysisResponse)
async def analyze_document_risk(request: DocumentAnalysisRequest):
    """
    Step 1.2: Global Risk Assessment
    步骤 1.2：全局风险评估

    Calculate document-level AIGC risk score and determine
    which lower layers need attention.
    """
    start_time = time.time()

    try:
        orchestrator = DocumentOrchestrator()

        # Create context with text
        context = LayerContext(full_text=request.text)

        # Run full analysis (includes both structure and risk)
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Focus on risk assessment details
        risk_details = result.details.get("global_risk", {})
        structure_details = result.details.get("structure_analysis", {})

        return DocumentAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=risk_details,
            processing_time_ms=processing_time_ms,
            structure=structure_details,
            predictability_score=structure_details.get("predictability"),
            paragraph_count=risk_details.get("total_paragraphs", 0),
            word_count=risk_details.get("total_words", 0),
        )

    except Exception as e:
        logger.error(f"Document risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(request: DocumentAnalysisRequest):
    """
    Combined Document Analysis (Layer 5)
    综合文档分析（第5层）

    Runs all document-level analysis steps:
    - Step 1.1: Structure Analysis
    - Step 1.2: Global Risk Assessment

    Returns complete document-level analysis results with context
    for passing to lower layers.
    """
    start_time = time.time()

    try:
        orchestrator = DocumentOrchestrator()

        # Create context with text
        context = LayerContext(full_text=request.text)

        # Run full analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract all details
        structure_details = result.details.get("structure_analysis", {})
        predictability = structure_details.get("predictability", {})
        risk_details = result.details.get("global_risk", {})

        # Build sections from paragraphs (basic section detection)
        # 从段落构建章节（基础章节检测）
        paragraphs = result.updated_context.paragraphs or []
        sections = []
        if paragraphs:
            # Group paragraphs into logical sections based on paragraph count
            # 根据段落数量将段落分组为逻辑章节
            total_paras = len(paragraphs)
            if total_paras <= 3:
                # Small document - treat as single section
                sections = [DocumentSection(
                    index=0,
                    role="body",
                    title="Main Content",
                    paragraph_count=total_paras,
                    word_count=sum(len(p.split()) for p in paragraphs)
                )]
            else:
                # Larger document - basic intro/body/conclusion split
                intro_count = 1
                conclusion_count = 1
                body_count = total_paras - intro_count - conclusion_count

                intro_words = sum(len(paragraphs[i].split()) for i in range(intro_count))
                body_words = sum(len(paragraphs[i].split()) for i in range(intro_count, intro_count + body_count))
                conclusion_words = sum(len(paragraphs[i].split()) for i in range(total_paras - conclusion_count, total_paras))

                sections = [
                    DocumentSection(index=0, role="introduction", title="Introduction", paragraph_count=intro_count, word_count=intro_words),
                    DocumentSection(index=1, role="body", title="Body", paragraph_count=body_count, word_count=body_words),
                    DocumentSection(index=2, role="conclusion", title="Conclusion", paragraph_count=conclusion_count, word_count=conclusion_words),
                ]

        # Extract predictability dimension scores for frontend
        # 提取预测性维度分数供前端使用
        predictability_scores = {}
        if predictability:
            predictability_scores = {
                "Progression": predictability.get("progression_predictability", 0),
                "Uniformity": predictability.get("function_uniformity", 0),
                "Closure": predictability.get("closure_strength", 0),
                "Length": predictability.get("length_regularity", 0),
                "Connectors": predictability.get("connector_explicitness", 0),
            }

        # Extract global risk factors from issues
        # 从问题中提取全局风险因素
        global_risk_factors = []
        for issue in result.issues:
            if issue.severity.value in ["high", "medium"]:
                global_risk_factors.append(issue.description_zh or issue.description)

        # Determine structure pattern
        # 确定结构模式
        structure_pattern = "unknown"
        if predictability:
            prog_type = predictability.get("progression_type", "")
            func_dist = predictability.get("function_distribution", "")
            if prog_type == "monotonic" and func_dist == "uniform":
                structure_pattern = "AI-typical"
            elif prog_type == "non_monotonic" or func_dist == "asymmetric":
                structure_pattern = "Human-like"
            else:
                structure_pattern = "Mixed"

        return DocumentAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=result.details,
            processing_time_ms=processing_time_ms,
            structure=structure_details,
            predictability_score=predictability,
            paragraph_count=structure_details.get("paragraph_count", 0),
            word_count=structure_details.get("total_word_count", 0),
            # New fields for frontend / 前端需要的新字段
            structure_score=predictability.get("total_score", 0) if predictability else 0,
            structure_pattern=structure_pattern,
            sections=sections,
            global_risk_factors=global_risk_factors,
            predictability_scores=predictability_scores,
        )

    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context")
async def get_document_context(request: DocumentAnalysisRequest):
    """
    Get document context for passing to lower layers
    获取文档上下文以传递给下层

    Returns the updated LayerContext that can be used
    to initialize lower layer analysis.
    """
    try:
        orchestrator = DocumentOrchestrator()

        # Create context with text
        context = LayerContext(full_text=request.text)

        # Run analysis
        result = await orchestrator.analyze(context)

        # Return the updated context as dict
        return {
            "paragraphs": result.updated_context.paragraphs,
            "document_structure": result.updated_context.document_structure,
            "document_risk_score": result.updated_context.document_risk_score,
            "document_issues": [
                {
                    "type": i.type,
                    "description": i.description,
                    "severity": i.severity.value,
                }
                for i in (result.updated_context.document_issues or [])
            ],
        }

    except Exception as e:
        logger.error(f"Document context extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Step 1.4: Connector & Transition Analysis
# 步骤 1.4：连接词与衔接分析
# =============================================================================

def _split_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs by double newlines or single newlines
    按双换行或单换行将文本分割为段落
    """
    # Try double newline first
    paragraphs = re.split(r'\n\n+', text.strip())
    # If only one paragraph, try single newline
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    # Filter empty paragraphs
    return [p.strip() for p in paragraphs if p.strip()]


@router.post("/connectors", response_model=ConnectorAnalysisResponse)
async def analyze_connectors(request: ConnectorAnalysisRequest):
    """
    Step 1.4: Connector & Transition Analysis
    步骤 1.4：连接词与衔接分析

    Analyzes paragraph transitions for AI-like patterns including:
    - Explicit connectors at paragraph openings
    - Formulaic topic sentences
    - Summary endings
    - Too-smooth transitions

    分析段落衔接的AI风格模式，包括：
    - 段落开头的显性连接词
    - 公式化主题句
    - 总结性结尾
    - 过于平滑的过渡
    """
    start_time = time.time()

    try:
        # Split text into paragraphs
        # 将文本分割为段落
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 2:
            # Need at least 2 paragraphs to analyze transitions
            # 至少需要2个段落才能分析衔接
            return ConnectorAnalysisResponse(
                total_transitions=0,
                problematic_transitions=0,
                overall_smoothness_score=0,
                overall_risk_level=RiskLevel.LOW,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Initialize transition analyzer
        # 初始化衔接分析器
        analyzer = TransitionAnalyzer()

        # Analyze all transitions
        # 分析所有衔接
        transition_results = analyzer.analyze_document_transitions(paragraphs)

        # Convert to response format
        # 转换为响应格式
        transitions: List[TransitionResultSchema] = []
        all_issues: List[DetectionIssue] = []
        all_connectors: List[str] = []
        total_score = 0
        problematic_count = 0

        for idx, result in enumerate(transition_results):
            # Convert issues to schema format
            # 转换问题为模式格式
            issues = [
                TransitionIssueSchema(
                    type=issue.type,
                    description=issue.description,
                    description_zh=issue.description_zh,
                    severity=IssueSeverity(issue.severity),
                    position=issue.position,
                    word=issue.word
                )
                for issue in result.issues
            ]

            # Create transition result
            # 创建衔接结果
            transition = TransitionResultSchema(
                transition_index=idx,
                para_a_index=idx,
                para_b_index=idx + 1,
                para_a_ending=result.para_a_ending,
                para_b_opening=result.para_b_opening,
                smoothness_score=result.smoothness_score,
                risk_level=RiskLevel(result.risk_level),
                issues=issues,
                explicit_connectors=result.explicit_connectors,
                has_topic_sentence_pattern=result.has_topic_sentence_pattern,
                has_summary_ending=result.has_summary_ending,
                semantic_overlap=result.semantic_overlap
            )
            transitions.append(transition)

            # Aggregate statistics
            # 汇总统计
            total_score += result.smoothness_score
            if result.issues:
                problematic_count += 1

            # Collect all explicit connectors
            # 收集所有显性连接词
            all_connectors.extend(result.explicit_connectors)

            # Convert to unified issue format
            # 转换为统一问题格式
            for issue in result.issues:
                all_issues.append(DetectionIssue(
                    type=issue.type,
                    description=issue.description,
                    description_zh=issue.description_zh,
                    severity=IssueSeverity(issue.severity),
                    layer=LayerLevel.DOCUMENT,
                    position=f"transition_{idx}",
                    suggestion=f"Consider using semantic echo or logical hook instead of explicit connector",
                    suggestion_zh=f"考虑使用语义回声或逻辑设问代替显性连接词",
                    details={
                        "para_a_index": idx,
                        "para_b_index": idx + 1,
                        "word": issue.word
                    }
                ))

        # Calculate overall statistics
        # 计算总体统计
        num_transitions = len(transition_results)
        overall_score = total_score // num_transitions if num_transitions > 0 else 0
        connector_density = (len(all_connectors) / len(paragraphs)) * 100 if paragraphs else 0

        # Determine overall risk level
        # 确定总体风险等级
        if overall_score >= 50:
            overall_risk = RiskLevel.HIGH
        elif overall_score >= 25:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW

        # Generate recommendations
        # 生成建议
        recommendations = []
        recommendations_zh = []

        if connector_density > 30:
            recommendations.append("High connector density detected. Replace explicit connectors with semantic echoes.")
            recommendations_zh.append("检测到高连接词密度。建议用语义回声替换显性连接词。")

        if any(t.has_topic_sentence_pattern for t in transitions):
            recommendations.append("Formulaic topic sentences detected. Vary paragraph openings.")
            recommendations_zh.append("检测到公式化主题句。建议变化段落开头。")

        if any(t.has_summary_ending for t in transitions):
            recommendations.append("Summary endings detected. Consider using open-ended transitions.")
            recommendations_zh.append("检测到总结性结尾。建议使用开放式过渡。")

        if not recommendations:
            recommendations.append("Transitions look natural. No major issues detected.")
            recommendations_zh.append("衔接看起来自然。未检测到重大问题。")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ConnectorAnalysisResponse(
            total_transitions=num_transitions,
            problematic_transitions=problematic_count,
            overall_smoothness_score=overall_score,
            overall_risk_level=overall_risk,
            total_explicit_connectors=len(all_connectors),
            connector_density=connector_density,
            connector_list=list(set(all_connectors)),  # Deduplicate
            transitions=transitions,
            issues=all_issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Connector analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Step 1.2: Paragraph Length Regularity Analysis
# 步骤 1.2：段落长度规律性分析
# =============================================================================

def _count_sentences(text: str) -> int:
    """
    Count sentences in text (simple heuristic)
    计算文本中的句子数量（简单启发式）
    """
    # Simple sentence boundary detection
    # 简单的句子边界检测
    endings = re.findall(r'[.!?]+', text)
    return max(1, len(endings))


def _determine_strategy(
    word_count: int,
    mean: float,
    stdev: float,
    idx: int,
    total_paragraphs: int
) -> tuple:
    """
    Determine suggested strategy for a paragraph
    确定段落的建议策略
    """
    if stdev == 0:
        return (ParagraphLengthStrategy.NONE, "", "")

    deviation = (word_count - mean) / stdev if stdev > 0 else 0

    # Very short paragraph (more than 1.5 stddev below mean)
    # 非常短的段落（低于平均值1.5个标准差以上）
    if deviation < -1.5 and word_count < 80:
        # Suggest merge with next paragraph if not last
        if idx < total_paragraphs - 1:
            return (
                ParagraphLengthStrategy.MERGE,
                f"Short paragraph ({word_count} words). Consider merging with next paragraph.",
                f"短段落（{word_count}词）。建议与下一段合并。"
            )
        else:
            return (
                ParagraphLengthStrategy.EXPAND,
                f"Short paragraph ({word_count} words). Consider expanding with more details.",
                f"短段落（{word_count}词）。建议添加更多细节扩展。"
            )

    # Very long paragraph (more than 1.5 stddev above mean)
    # 非常长的段落（高于平均值1.5个标准差以上）
    if deviation > 1.5 and word_count > 200:
        return (
            ParagraphLengthStrategy.SPLIT,
            f"Long paragraph ({word_count} words). Consider splitting into 2-3 smaller paragraphs.",
            f"长段落（{word_count}词）。建议拆分为2-3个较小的段落。"
        )

    # Moderately long paragraph
    # 中等长度的长段落
    if deviation > 1.0 and word_count > 150:
        return (
            ParagraphLengthStrategy.COMPRESS,
            f"Moderately long paragraph ({word_count} words). Consider condensing.",
            f"中等偏长段落（{word_count}词）。建议适当压缩。"
        )

    # Moderately short paragraph
    # 中等长度的短段落
    if deviation < -1.0 and word_count < 100:
        return (
            ParagraphLengthStrategy.EXPAND,
            f"Moderately short paragraph ({word_count} words). Consider adding details.",
            f"中等偏短段落（{word_count}词）。建议添加细节。"
        )

    return (ParagraphLengthStrategy.NONE, "", "")


@router.post("/paragraph-length", response_model=ParagraphLengthAnalysisResponse)
async def analyze_paragraph_length(request: ParagraphLengthAnalysisRequest):
    """
    Step 1.2: Paragraph Length Regularity Analysis
    步骤 1.2：段落长度规律性分析

    Analyzes paragraph length distribution to detect AI-like uniformity:
    - CV (Coefficient of Variation) < 0.3 indicates too uniform (AI-like)
    - Target CV >= 0.4 for human-like writing
    - Provides merge/split/expand/compress suggestions

    分析段落长度分布以检测AI风格的均匀性：
    - CV（变异系数）< 0.3 表示过于均匀（AI风格）
    - 目标 CV >= 0.4 以达到人类写作风格
    - 提供合并/拆分/扩展/压缩建议
    """
    start_time = time.time()

    try:
        # Split text into paragraphs
        # 将文本分割为段落
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 2:
            # Not enough paragraphs for meaningful analysis
            # 段落数量不足，无法进行有意义的分析
            return ParagraphLengthAnalysisResponse(
                paragraph_count=len(paragraphs),
                total_word_count=len(request.text.split()),
                mean_length=len(request.text.split()),
                stdev_length=0,
                cv=0,
                min_length=len(request.text.split()),
                max_length=len(request.text.split()),
                length_regularity_score=50,
                risk_level=RiskLevel.LOW,
                target_cv=0.4,
                recommendations=["Document too short for paragraph length analysis."],
                recommendations_zh=["文档过短，无法进行段落长度分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Calculate length statistics
        # 计算长度统计
        lengths = [len(p.split()) for p in paragraphs]
        total_word_count = sum(lengths)
        mean_len = statistics.mean(lengths)
        stdev_len = statistics.stdev(lengths) if len(lengths) > 1 else 0
        cv = stdev_len / mean_len if mean_len > 0 else 0
        min_len = min(lengths)
        max_len = max(lengths)

        # Calculate length regularity score (higher = more uniform = more AI-like)
        # 计算长度规律性分数（越高越均匀，越像AI）
        if cv < 0.2:
            score = 90  # Very uniform
        elif cv < 0.3:
            score = 70  # Quite uniform
        elif cv < 0.4:
            score = 50  # Moderate
        elif cv < 0.5:
            score = 30  # Good variation
        else:
            score = 15  # High variation (human-like)

        # Determine risk level
        # 确定风险等级
        if score >= 60:
            risk_level = RiskLevel.HIGH
        elif score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Build per-paragraph info with strategies
        # 构建每个段落的信息和策略
        paragraph_infos: List[ParagraphLengthInfo] = []
        merge_suggestions: List[int] = []
        split_suggestions: List[int] = []
        expand_suggestions: List[int] = []
        compress_suggestions: List[int] = []

        for idx, (para, word_count) in enumerate(zip(paragraphs, lengths)):
            # Calculate deviation from mean
            deviation = (word_count - mean_len) / stdev_len if stdev_len > 0 else 0

            # Determine strategy
            strategy, reason, reason_zh = _determine_strategy(
                word_count, mean_len, stdev_len, idx, len(paragraphs)
            )

            # Track suggestions by category
            if strategy == ParagraphLengthStrategy.MERGE:
                merge_suggestions.append(idx)
            elif strategy == ParagraphLengthStrategy.SPLIT:
                split_suggestions.append(idx)
            elif strategy == ParagraphLengthStrategy.EXPAND:
                expand_suggestions.append(idx)
            elif strategy == ParagraphLengthStrategy.COMPRESS:
                compress_suggestions.append(idx)

            paragraph_infos.append(ParagraphLengthInfo(
                index=idx,
                word_count=word_count,
                char_count=len(para),
                sentence_count=_count_sentences(para),
                preview=para[:100] + "..." if len(para) > 100 else para,
                deviation_from_mean=round(deviation, 2),
                suggested_strategy=strategy,
                strategy_reason=reason,
                strategy_reason_zh=reason_zh
            ))

        # Generate recommendations
        # 生成建议
        recommendations = []
        recommendations_zh = []

        if cv < 0.3:
            recommendations.append(
                f"Paragraph lengths are too uniform (CV={cv:.2f}). "
                f"Target CV >= 0.40 for natural variation. "
                f"Mix short paragraphs (50-80 words) with longer ones (150-200 words)."
            )
            recommendations_zh.append(
                f"段落长度过于均匀（CV={cv:.2f}）。"
                f"目标CV >= 0.40以达到自然变化。"
                f"混合短段落（50-80词）和长段落（150-200词）。"
            )

        if merge_suggestions:
            recommendations.append(
                f"Consider merging paragraphs {', '.join(map(str, [i+1 for i in merge_suggestions]))} with adjacent paragraphs."
            )
            recommendations_zh.append(
                f"建议将第 {', '.join(map(str, [i+1 for i in merge_suggestions]))} 段与相邻段落合并。"
            )

        if split_suggestions:
            recommendations.append(
                f"Consider splitting paragraphs {', '.join(map(str, [i+1 for i in split_suggestions]))} into smaller sections."
            )
            recommendations_zh.append(
                f"建议将第 {', '.join(map(str, [i+1 for i in split_suggestions]))} 段拆分为较小的部分。"
            )

        if not recommendations:
            recommendations.append("Paragraph lengths show good variation. No major issues detected.")
            recommendations_zh.append("段落长度变化良好。未检测到重大问题。")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ParagraphLengthAnalysisResponse(
            paragraph_count=len(paragraphs),
            total_word_count=total_word_count,
            mean_length=round(mean_len, 1),
            stdev_length=round(stdev_len, 1),
            cv=round(cv, 3),
            min_length=min_len,
            max_length=max_len,
            length_regularity_score=score,
            risk_level=risk_level,
            target_cv=0.4,
            paragraphs=paragraph_infos,
            merge_suggestions=merge_suggestions,
            split_suggestions=split_suggestions,
            expand_suggestions=expand_suggestions,
            compress_suggestions=compress_suggestions,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Paragraph length analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Step 1.3: Progression & Closure Analysis
# 步骤 1.3：推进模式与闭合分析
# =============================================================================

@router.post("/progression-closure", response_model=ProgressionClosureResponse)
async def analyze_progression_closure(request: ProgressionClosureRequest):
    """
    Step 1.3: Progression & Closure Analysis
    步骤 1.3：推进模式与闭合分析

    Analyzes document progression patterns and closure strength:
    - Monotonic (AI-like): sequential, additive, one-directional flow
    - Non-monotonic (Human-like): returns, conditionals, reversals
    - Strong closure (AI-like): definitive conclusions
    - Weak closure (Human-like): open questions, unresolved tensions

    分析文档推进模式和闭合强度：
    - 单调（AI风格）：顺序、递进、单向流动
    - 非单调（人类风格）：回扣、条件、反转
    - 强闭合（AI风格）：明确结论
    - 弱闭合（人类风格）：开放问题、未解决的张力
    """
    start_time = time.time()

    try:
        # Split text into paragraphs
        # 将文本分割为段落
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) < 3:
            return ProgressionClosureResponse(
                progression_score=0,
                progression_type=ProgressionType.UNKNOWN,
                closure_score=0,
                closure_type=ClosureType.MODERATE,
                combined_score=0,
                risk_level=RiskLevel.LOW,
                recommendations=["Document too short for progression/closure analysis."],
                recommendations_zh=["文档过短，无法进行推进/闭合分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Use StructurePredictabilityAnalyzer for analysis
        # 使用结构预测性分析器进行分析
        analyzer = StructurePredictabilityAnalyzer()
        result = analyzer.analyze(paragraphs)

        # Extract progression details
        # 提取推进详情
        prog_details = result.details.get("progression", {})
        markers_data = prog_details.get("markers", {"monotonic": [], "non_monotonic": []})

        # Build progression markers list
        # 构建推进标记列表
        progression_markers: List[ProgressionMarker] = []
        for m in markers_data.get("monotonic", []):
            progression_markers.append(ProgressionMarker(
                paragraph_index=m.get("paragraph", 0),
                marker=m.get("marker", ""),
                category=m.get("category", "unknown"),
                is_monotonic=True
            ))
        for m in markers_data.get("non_monotonic", []):
            progression_markers.append(ProgressionMarker(
                paragraph_index=m.get("paragraph", 0),
                marker=m.get("marker", ""),
                category=m.get("category", "unknown"),
                is_monotonic=False
            ))

        # Extract closure details
        # 提取闭合详情
        closure_details = result.details.get("closure", {})
        last_para_preview = closure_details.get("last_paragraph_preview", "")

        # Map progression type
        # 映射推进类型
        prog_type_map = {
            "monotonic": ProgressionType.MONOTONIC,
            "non_monotonic": ProgressionType.NON_MONOTONIC,
            "mixed": ProgressionType.MIXED,
        }
        prog_type = prog_type_map.get(result.progression_type, ProgressionType.UNKNOWN)

        # Map closure type
        # 映射闭合类型
        closure_type_map = {
            "strong": ClosureType.STRONG,
            "moderate": ClosureType.MODERATE,
            "weak": ClosureType.WEAK,
            "open": ClosureType.OPEN,
        }
        closure_type = closure_type_map.get(result.closure_type, ClosureType.MODERATE)

        # Calculate combined score (average of progression and closure)
        # 计算综合分数（推进和闭合的平均值）
        combined_score = (result.progression_predictability + result.closure_strength) // 2

        # Determine risk level
        # 确定风险等级
        if combined_score >= 60:
            risk_level = RiskLevel.HIGH
        elif combined_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Generate recommendations
        # 生成建议
        recommendations = []
        recommendations_zh = []

        if result.progression_predictability > 60:
            recommendations.append(
                "Progression is too predictable (monotonic). Add returns to earlier points, "
                "conditionals, or local reversals to break the linear flow."
            )
            recommendations_zh.append(
                "推进过于可预测（单调）。添加回扣、条件触发或局部反转来打破线性流动。"
            )

        if result.closure_strength > 60:
            recommendations.append(
                "Closure is too strong. Consider ending with an open question or "
                "unresolved tension instead of a definitive summary."
            )
            recommendations_zh.append(
                "闭合过于强烈。考虑以开放问题或未解决的张力结尾，而非明确总结。"
            )

        if prog_details.get("sequential_markers", 0) >= 3:
            recommendations.append(
                "Multiple sequential markers detected (First, Second, Third...). "
                "This is a strong AI signal. Vary your transitions."
            )
            recommendations_zh.append(
                "检测到多个顺序标记（First, Second, Third...）。"
                "这是强烈的AI信号。请变化您的过渡方式。"
            )

        if not recommendations:
            recommendations.append("Progression and closure patterns look natural.")
            recommendations_zh.append("推进和闭合模式看起来自然。")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ProgressionClosureResponse(
            progression_score=result.progression_predictability,
            progression_type=prog_type,
            monotonic_count=prog_details.get("monotonic_count", 0),
            non_monotonic_count=prog_details.get("non_monotonic_count", 0),
            sequential_markers_found=prog_details.get("sequential_markers", 0),
            progression_markers=progression_markers,
            closure_score=result.closure_strength,
            closure_type=closure_type,
            strong_closure_patterns=closure_details.get("strong_patterns", []),
            weak_closure_patterns=closure_details.get("weak_patterns", []),
            last_paragraph_preview=last_para_preview,
            combined_score=combined_score,
            risk_level=risk_level,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Progression/closure analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Step 1.5: Content Substantiality Analysis
# 步骤 1.5：内容实质性分析
# =============================================================================

# Generic phrases that indicate AI-generated content
# 表示AI生成内容的泛泛短语
GENERIC_PHRASES = [
    "it is important to note",
    "it is worth mentioning",
    "plays a crucial role",
    "plays a vital role",
    "is of paramount importance",
    "in today's world",
    "in the modern era",
    "has become increasingly",
    "is becoming more and more",
    "a wide range of",
    "various aspects of",
    "different types of",
    "many people believe",
    "some experts say",
    "according to research",
    "studies have shown",
    "it can be argued",
    "there are many ways",
    "this highlights the importance",
    "this underscores the need",
    "this demonstrates that",
    "needless to say",
    "goes without saying",
    "as we all know",
    "it is well known",
    "generally speaking",
    "broadly speaking",
    "in essence",
    "fundamentally",
    "essentially",
    "significantly",
    "considerably",
    "substantially",
]

# Filler words that add no value
# 无实际价值的填充词
FILLER_WORDS = [
    "very", "really", "actually", "basically", "literally",
    "obviously", "clearly", "certainly", "definitely",
    "extremely", "incredibly", "remarkably", "quite",
    "rather", "somewhat", "fairly", "relatively",
]


def _analyze_paragraph_substantiality(para: str, idx: int) -> ParagraphSubstantiality:
    """
    Analyze substantiality of a single paragraph
    分析单个段落的实质性
    """
    words = para.lower().split()
    word_count = len(words)

    # Find generic phrases
    # 查找泛泛短语
    para_lower = para.lower()
    found_generic = [p for p in GENERIC_PHRASES if p in para_lower]

    # Find filler words
    # 查找填充词
    filler_count = sum(1 for w in words if w.strip(".,!?;:") in FILLER_WORDS)
    filler_ratio = filler_count / word_count if word_count > 0 else 0

    # Find specific details (numbers, dates, proper nouns)
    # 查找具体细节（数字、日期、专有名词）
    specific_details = []

    # Numbers and percentages
    numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', para)
    specific_details.extend([f"number: {n}" for n in numbers[:5]])

    # Dates
    dates = re.findall(r'\b(?:19|20)\d{2}\b', para)
    specific_details.extend([f"year: {d}" for d in dates[:3]])

    # Capitalized words (potential proper nouns, excluding sentence starts)
    sentences = re.split(r'[.!?]\s+', para)
    for sent in sentences:
        words_in_sent = sent.split()
        for i, w in enumerate(words_in_sent[1:], 1):  # Skip first word
            if w and w[0].isupper() and len(w) > 1:
                specific_details.append(f"name: {w}")

    specific_details = list(set(specific_details))[:10]  # Deduplicate and limit

    # Calculate specificity score
    # 计算具体性分数
    generic_penalty = len(found_generic) * 15
    filler_penalty = int(filler_ratio * 100)
    specific_bonus = len(specific_details) * 10

    specificity_score = max(0, min(100, 70 - generic_penalty - filler_penalty + specific_bonus))

    # Determine substantiality level
    # 确定实质性等级
    if specificity_score >= 60:
        level = SubstantialityLevel.HIGH
        suggestion = ""
        suggestion_zh = ""
    elif specificity_score >= 35:
        level = SubstantialityLevel.MEDIUM
        suggestion = "Consider adding more specific details, examples, or data."
        suggestion_zh = "考虑添加更多具体细节、例子或数据。"
    else:
        level = SubstantialityLevel.LOW
        suggestion = "This paragraph lacks specific content. Replace generic statements with concrete examples, data, or specific references."
        suggestion_zh = "此段落缺乏具体内容。将泛泛陈述替换为具体例子、数据或特定引用。"

    return ParagraphSubstantiality(
        index=idx,
        preview=para[:100] + "..." if len(para) > 100 else para,
        word_count=word_count,
        specificity_score=specificity_score,
        generic_phrase_count=len(found_generic),
        specific_detail_count=len(specific_details),
        filler_ratio=round(filler_ratio, 3),
        generic_phrases=found_generic,
        specific_details=specific_details,
        substantiality_level=level,
        suggestion=suggestion,
        suggestion_zh=suggestion_zh
    )


@router.post("/content-substantiality", response_model=ContentSubstantialityResponse)
async def analyze_content_substantiality(request: ContentSubstantialityRequest):
    """
    Step 1.5: Content Substantiality Analysis
    步骤 1.5：内容实质性分析

    Analyzes content for specificity vs. generic AI-like patterns:
    - Detects generic phrases common in AI text
    - Identifies filler words
    - Looks for specific details (numbers, names, dates)
    - Calculates overall substantiality score

    分析内容的具体性与泛泛的AI风格模式：
    - 检测AI文本中常见的泛泛短语
    - 识别填充词
    - 查找具体细节（数字、名称、日期）
    - 计算总体实质性分数
    """
    start_time = time.time()

    try:
        # Split text into paragraphs
        # 将文本分割为段落
        paragraphs = _split_paragraphs(request.text)

        if len(paragraphs) == 0:
            return ContentSubstantialityResponse(
                paragraph_count=0,
                overall_specificity_score=0,
                overall_substantiality=SubstantialityLevel.LOW,
                risk_level=RiskLevel.LOW,
                recommendations=["No content to analyze."],
                recommendations_zh=["没有内容可分析。"],
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Analyze each paragraph
        # 分析每个段落
        paragraph_results: List[ParagraphSubstantiality] = []
        all_generic_phrases: List[str] = []
        total_specific = 0
        total_generic = 0
        filler_ratios: List[float] = []

        for idx, para in enumerate(paragraphs):
            result = _analyze_paragraph_substantiality(para, idx)
            paragraph_results.append(result)

            all_generic_phrases.extend(result.generic_phrases)
            total_specific += result.specific_detail_count
            total_generic += result.generic_phrase_count
            filler_ratios.append(result.filler_ratio)

        # Calculate overall metrics
        # 计算总体指标
        avg_specificity = sum(p.specificity_score for p in paragraph_results) // len(paragraph_results)
        avg_filler = sum(filler_ratios) / len(filler_ratios) if filler_ratios else 0

        # Find low substantiality paragraphs
        # 查找低实质性段落
        low_sub_paragraphs = [
            p.index for p in paragraph_results
            if p.substantiality_level == SubstantialityLevel.LOW
        ]

        # Determine overall level
        # 确定总体等级
        if avg_specificity >= 60:
            overall_level = SubstantialityLevel.HIGH
            risk_level = RiskLevel.LOW
        elif avg_specificity >= 35:
            overall_level = SubstantialityLevel.MEDIUM
            risk_level = RiskLevel.MEDIUM
        else:
            overall_level = SubstantialityLevel.LOW
            risk_level = RiskLevel.HIGH

        # Count common generic phrases
        # 统计常见泛泛短语
        from collections import Counter
        phrase_counts = Counter(all_generic_phrases)
        common_generic = [p for p, _ in phrase_counts.most_common(5)]

        # Generate recommendations
        # 生成建议
        recommendations = []
        recommendations_zh = []

        if total_generic > len(paragraphs):
            recommendations.append(
                f"High density of generic phrases detected ({total_generic} total). "
                "Replace vague language with specific facts, data, or examples."
            )
            recommendations_zh.append(
                f"检测到高密度的泛泛短语（共{total_generic}个）。"
                "将模糊语言替换为具体事实、数据或例子。"
            )

        if avg_filler > 0.05:
            recommendations.append(
                f"Filler word ratio is high ({avg_filler:.1%}). "
                "Remove unnecessary qualifiers like 'very', 'really', 'quite'."
            )
            recommendations_zh.append(
                f"填充词比例较高（{avg_filler:.1%}）。"
                "删除不必要的修饰词如 'very', 'really', 'quite'。"
            )

        if low_sub_paragraphs:
            recommendations.append(
                f"Paragraphs {', '.join(str(i+1) for i in low_sub_paragraphs[:5])} "
                "have low substantiality. Add specific details."
            )
            recommendations_zh.append(
                f"第 {', '.join(str(i+1) for i in low_sub_paragraphs[:5])} 段"
                "实质性较低。请添加具体细节。"
            )

        if not recommendations:
            recommendations.append("Content appears to have good substantiality with specific details.")
            recommendations_zh.append("内容具有良好的实质性和具体细节。")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ContentSubstantialityResponse(
            paragraph_count=len(paragraphs),
            overall_specificity_score=avg_specificity,
            overall_substantiality=overall_level,
            risk_level=risk_level,
            total_generic_phrases=total_generic,
            total_specific_details=total_specific,
            average_filler_ratio=round(avg_filler, 3),
            low_substantiality_paragraphs=low_sub_paragraphs,
            paragraphs=paragraph_results,
            common_generic_phrases=common_generic,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Content substantiality analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
