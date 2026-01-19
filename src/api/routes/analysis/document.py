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
import json

from src.api.routes.analysis.schemas import (
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
    DocumentSection,  # ← Already imported, good!
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

# Import unified text parsing service
# 导入统一文本解析服务
from src.services.text_parsing_service import (
    TextParsingService,
    get_text_parsing_service,
    get_statistics,
    get_section_distribution,
    get_body_paragraphs,
)

# Import new LLM handlers
from src.api.routes.substeps.layer5.step1_1_handler import Step1_1Handler
from src.api.routes.substeps.layer5.step1_2_handler import Step1_2Handler
from src.api.routes.substeps.layer5.step1_3_handler import Step1_3Handler
from src.api.routes.substeps.layer5.step1_4_handler import Step1_4Handler
from src.api.routes.substeps.layer5.step1_5_handler import Step1_5Handler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM handlers
step1_1_handler = Step1_1Handler()
step1_2_handler = Step1_2Handler()
step1_3_handler = Step1_3Handler()
step1_4_handler = Step1_4Handler()
step1_5_handler = Step1_5Handler()


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
    Step 1.1: Structure Analysis (NOW WITH LLM!)
    步骤 1.1：结构分析（现在使用LLM！）

    Uses unified text parsing service + LLM analysis for accurate results.
    使用统一文本解析服务 + LLM分析，确保结果准确。
    """
    start_time = time.time()

    try:
        # =====================================================================
        # STEP 1: Get statistics from unified text parsing service (accurate data)
        # 第一步：从统一文本解析服务获取统计数据（准确数据）
        # =====================================================================
        stats = get_statistics(request.text)

        para_count = stats['paragraph_count']
        total_word_count = stats['total_word_count']
        lengths = stats['paragraph_lengths']
        mean_len = stats['mean_length']
        stdev_len = stats['stdev_length']
        cv = stats['cv']
        section_distribution = stats['section_distribution']

        # Check for symmetry (all sections have same paragraph count)
        # 检查对称性（所有章节段落数是否相同）
        section_para_counts = [s.get("paragraphCount", 0) for s in section_distribution]
        is_symmetric = len(set(section_para_counts)) == 1 if section_para_counts else False

        logger.info(f"Parsed statistics (unified service): paragraphs={para_count}, sections={len(section_distribution)}, cv={cv:.3f}, symmetric={is_symmetric}")

        # =====================================================================
        # STEP 2: Pass parsed statistics to LLM for analysis/decision
        # 第二步：将解析的统计数据传递给LLM进行分析/决策
        # =====================================================================
        parsed_statistics = {
            **stats,
            "is_symmetric": is_symmetric
        }

        logger.info("Calling Step1_1Handler with parsed statistics for LLM analysis")
        result = await step1_1_handler.analyze(
            document_text=request.text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step1-1",
            use_cache=True,
            parsed_statistics=json.dumps(parsed_statistics, indent=2, ensure_ascii=False),
            cv=round(cv, 3)
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # =====================================================================
        # STEP 3: Use CALCULATED section data (not LLM's)
        # 第三步：使用计算的章节数据（而非LLM的）
        # =====================================================================
        sections = []
        for idx, sec in enumerate(section_distribution):
            sections.append(DocumentSection(
                index=idx,
                role=sec.get("role", "body"),
                title=sec.get("title", f"Section {idx + 1}"),
                paragraph_count=sec.get("paragraphCount", 0),
                word_count=sec.get("wordCount", 0)
            ))

        # If no sections detected, create a simple body section
        # 如果没有检测到章节，创建简单的body章节
        if not sections:
            sections = [DocumentSection(
                index=0,
                role="body",
                title="Main Content",
                paragraph_count=para_count,
                word_count=total_word_count
            )]

        # Convert issues to API format (from LLM analysis)
        # 将问题转换为API格式（来自LLM分析）
        issues_converted = []
        for issue in result.get("issues", []):
            issues_converted.append(DetectionIssue(
                type=issue.get("type", "unknown"),
                description=issue.get("description", ""),
                description_zh=issue.get("description_zh", ""),
                severity=IssueSeverity(issue.get("severity", "medium")),
                layer=LayerLevel.DOCUMENT,
                position=", ".join(issue.get("affected_positions", [])),
                suggestion="\n".join(issue.get("fix_suggestions", [])),
                suggestion_zh="\n".join(issue.get("fix_suggestions_zh", [])),
                details=issue,
            ))

        return DocumentAnalysisResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=issues_converted,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            details={"llm_analysis": result, "parsed_statistics": parsed_statistics},
            processing_time_ms=processing_time_ms,
            structure={},
            predictability_score={},
            paragraph_count=para_count,  # Use calculated value
            word_count=total_word_count,  # Use calculated value
            structure_pattern=result.get("structure_pattern", "Unknown"),
            sections=sections,  # Use calculated sections
        )

    except Exception as e:
        logger.error(f"Document structure analysis failed: {e}", exc_info=True)
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

def _split_paragraphs(text: str, exclude_non_body: bool = True) -> List[str]:
    """
    Split text into paragraphs using unified text parsing service
    使用统一文本解析服务将文本分割为段落

    Args:
        text: Document text to split
        exclude_non_body: If True, exclude titles, headers, figure captions, etc.
                         如果为True，排除标题、表头、图名等非正文内容

    Note: This function now uses the unified TextParsingService for consistency.
    注意：此函数现在使用统一的TextParsingService以确保一致性。
    """
    service = get_text_parsing_service()

    if exclude_non_body:
        # Get only processable body paragraphs
        # 仅获取可处理的正文段落
        body_paragraphs = service.get_body_paragraphs(text)
        return [p.text for p in body_paragraphs]
    else:
        # Get all paragraphs including headers
        # 获取所有段落（包括标题）
        paragraphs, _, _ = service.parse_document(text)
        return [p.text for p in paragraphs]


def _calculate_section_distribution(text: str) -> List[dict]:
    """
    Calculate section distribution using unified text parsing service
    使用统一文本解析服务计算章节分布

    This function identifies sections based on:
    1. Explicit section headers (e.g., "1. Introduction", "Methods", etc.)
    2. Common academic section titles
    3. Paragraph grouping based on content

    Note: This function now uses the unified TextParsingService for consistency.
    注意：此函数现在使用统一的TextParsingService以确保一致性。

    Returns a list of sections with paragraph_count and word_count.
    """
    sections = get_section_distribution(text)
    logger.info(f"Section distribution: {[(s['title'], s['paragraphCount'], s['wordCount']) for s in sections]}")
    return sections


@router.post("/connectors", response_model=ConnectorAnalysisResponse)
async def analyze_connectors(request: ConnectorAnalysisRequest):
    """
    Step 1.4: Connector & Transition Analysis (NOW WITH LLM!)
    步骤 1.4：连接词与衔接分析（现在使用LLM！）

    Uses pre-calculated statistics + LLM analysis.
    使用预计算的统计数据 + LLM分析。
    """
    start_time = time.time()

    try:
        # =====================================================================
        # STEP 1: Calculate basic statistics
        # 第一步：计算基本统计数据
        # =====================================================================
        paragraphs = _split_paragraphs(request.text, exclude_non_body=True)
        para_count = len(paragraphs)
        num_transitions = max(0, para_count - 1)

        parsed_statistics = {
            "paragraph_count": para_count,
            "num_transitions": num_transitions
        }

        logger.info(f"Parsed statistics for Step 1.4: paragraphs={para_count}, transitions={num_transitions}")

        # =====================================================================
        # STEP 2: Pass to LLM for analysis
        # 第二步：传递给LLM进行分析
        # =====================================================================
        logger.info("Calling Step1_4Handler for LLM-based connector analysis")
        result = await step1_4_handler.analyze(
            document_text=request.text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step1-4",
            use_cache=True,
            parsed_statistics=json.dumps(parsed_statistics, indent=2, ensure_ascii=False)
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract issues
        issues = result.get("issues", [])

        # Convert issues to DetectionIssue format
        detection_issues = []
        for issue in issues:
            detection_issues.append(DetectionIssue(
                type=issue.get("type", "unknown"),
                description=issue.get("description", ""),
                description_zh=issue.get("description_zh", ""),
                severity=IssueSeverity(issue.get("severity", "medium")),
                layer=LayerLevel.DOCUMENT,
                # Convert int to str for join operation
                # 将整数转换为字符串以进行 join 操作
                position=", ".join(str(p) for p in issue.get("affected_positions", [])),
                suggestion="\n".join(str(s) for s in issue.get("fix_suggestions", [])),
                suggestion_zh="\n".join(str(s) for s in issue.get("fix_suggestions_zh", [])),
                details=issue,
            ))

        # Calculate basic stats
        paragraphs = _split_paragraphs(request.text)
        num_transitions = max(0, len(paragraphs) - 1)

        # Determine risk level from result
        risk_level = RiskLevel(result.get("risk_level", "low"))

        return ConnectorAnalysisResponse(
            total_transitions=num_transitions,
            problematic_transitions=len(issues),
            overall_smoothness_score=result.get("risk_score", 0),
            overall_risk_level=risk_level,
            total_explicit_connectors=sum(1 for i in issues if "explicit_connector" in i.get("type", "")),
            connector_density=0,
            connector_list=[],
            transitions=[],
            issues=detection_issues,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Connector analysis failed: {e}", exc_info=True)
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
    Step 1.2: Paragraph Length Regularity Analysis (NOW WITH LLM!)
    步骤 1.2：段落长度规律性分析（现在使用LLM！）

    Uses unified text parsing service + LLM analysis for accurate results.
    使用统一文本解析服务 + LLM分析，确保结果准确。
    """
    start_time = time.time()

    try:
        # =====================================================================
        # STEP 1: Get statistics from unified text parsing service (accurate data)
        # 第一步：从统一文本解析服务获取统计数据（准确数据）
        # =====================================================================
        stats = get_statistics(request.text)

        para_count = stats['paragraph_count']
        lengths = stats['paragraph_lengths']
        total_word_count = stats['total_word_count']
        mean_len = stats['mean_length']
        stdev_len = stats['stdev_length']
        cv = stats['cv']
        min_len = stats['min_length']
        max_len = stats['max_length']
        section_distribution = stats['section_distribution']

        logger.info(f"Parsed statistics (unified service): paragraphs={para_count}, mean={mean_len:.1f}, cv={cv:.3f}, sections={len(section_distribution)}")

        # =====================================================================
        # STEP 2: Pass parsed statistics to LLM for analysis/decision
        # 第二步：将解析的统计数据传递给LLM进行分析/决策
        # =====================================================================
        parsed_statistics_dict = stats

        # Format as readable JSON string for LLM prompt
        # 格式化为可读的JSON字符串用于LLM prompt
        parsed_statistics_str = json.dumps(parsed_statistics_dict, indent=2, ensure_ascii=False)

        logger.info("Calling Step1_2Handler with parsed statistics for LLM analysis")
        result = await step1_2_handler.analyze(
            document_text=request.text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step1-2",
            use_cache=True,
            parsed_statistics=parsed_statistics_str,  # Pass as formatted JSON string
            cv=round(cv, 3)  # Pass CV separately for placeholder in prompt
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract LLM analysis results (issues, recommendations - NOT statistics)
        # 提取LLM分析结果（问题、建议 - 不是统计数据）
        issues = result.get("issues", [])

        return ParagraphLengthAnalysisResponse(
            paragraph_count=para_count,
            total_word_count=total_word_count,
            mean_length=round(mean_len, 1),
            stdev_length=round(stdev_len, 1),
            cv=round(cv, 3),
            min_length=min_len,
            max_length=max_len,
            length_regularity_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            target_cv=0.4,
            paragraphs=[],  # LLM provides analysis instead
            merge_suggestions=[],
            split_suggestions=[],
            expand_suggestions=[],
            compress_suggestions=[],
            # LLM analysis results
            issues=issues,
            summary=result.get("summary", ""),
            summary_zh=result.get("summary_zh", ""),
            # Section distribution calculated from current text
            # 从当前文本计算的章节分布
            section_distribution=section_distribution,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Paragraph length analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Step 1.3: Progression & Closure Analysis
# 步骤 1.3：推进模式与闭合分析
# =============================================================================

@router.post("/progression-closure", response_model=ProgressionClosureResponse)
async def analyze_progression_closure(request: ProgressionClosureRequest):
    """
    Step 1.3: Progression & Closure Analysis (NOW WITH LLM!)
    步骤 1.3：推进模式与闭合分析（现在使用LLM！）

    Uses pre-calculated statistics + LLM semantic analysis.
    使用预计算的统计数据 + LLM语义分析。
    """
    start_time = time.time()

    try:
        # =====================================================================
        # STEP 1: Calculate basic statistics for context
        # 第一步：计算基本统计数据作为上下文
        # =====================================================================
        paragraphs = _split_paragraphs(request.text, exclude_non_body=True)
        para_count = len(paragraphs)
        section_distribution = _calculate_section_distribution(request.text)

        # Get last paragraph for closure analysis
        # 获取最后一段用于闭合分析
        last_paragraph = paragraphs[-1] if paragraphs else ""

        parsed_statistics = {
            "paragraph_count": para_count,
            "section_count": len(section_distribution),
            "section_distribution": section_distribution,
            "last_paragraph_preview": last_paragraph[:200] if last_paragraph else ""
        }

        logger.info(f"Parsed statistics for Step 1.3: paragraphs={para_count}, sections={len(section_distribution)}")

        # =====================================================================
        # STEP 2: Pass to LLM for semantic analysis
        # 第二步：传递给LLM进行语义分析
        # =====================================================================
        logger.info("Calling Step1_3Handler for LLM-based progression/closure analysis")
        result = await step1_3_handler.analyze(
            document_text=request.text,
            locked_terms=[],
            session_id=request.session_id,
            step_name="step1-3",
            use_cache=True,
            parsed_statistics=json.dumps(parsed_statistics, indent=2, ensure_ascii=False)
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract issues
        # 提取问题列表
        issues = result.get("issues", [])

        # =====================================================================
        # STEP 3: Extract progression markers from LLM result
        # 第三步：从LLM结果中提取推进标记
        # =====================================================================
        raw_markers = result.get("progression_markers", [])
        progression_markers = []

        for marker in raw_markers:
            progression_markers.append(ProgressionMarker(
                paragraph_index=marker.get("paragraph_index", 0),
                marker=marker.get("marker", ""),
                category=marker.get("category", "unknown"),
                is_monotonic=marker.get("is_monotonic", True)
            ))

        # Count monotonic vs non-monotonic markers
        # 统计单调和非单调标记数量
        monotonic_count = sum(1 for m in progression_markers if m.is_monotonic)
        non_monotonic_count = len(progression_markers) - monotonic_count

        # Get progression type and score from LLM result
        # 从LLM结果获取推进类型和分数
        progression_type_str = result.get("progression_type", "unknown")
        if progression_type_str == "monotonic":
            progression_type = ProgressionType.MONOTONIC
        elif progression_type_str == "non_monotonic":
            progression_type = ProgressionType.NON_MONOTONIC
        elif progression_type_str == "mixed":
            progression_type = ProgressionType.MIXED
        else:
            progression_type = ProgressionType.UNKNOWN

        # Get scores from LLM result
        # 从LLM结果获取分数
        progression_score = result.get("progression_score", 50)
        closure_score = result.get("closure_score", 0)

        # Get closure type from LLM result
        # 从LLM结果获取闭合类型
        closure_type_str = result.get("closure_type", "moderate")
        if closure_type_str == "strong":
            closure_type = ClosureType.STRONG
        elif closure_type_str == "weak":
            closure_type = ClosureType.WEAK
        elif closure_type_str == "open":
            closure_type = ClosureType.OPEN
        else:
            closure_type = ClosureType.MODERATE

        # Fallback: infer from issues if LLM didn't provide direct values
        # 后备：如果LLM没有提供直接值，从问题中推断
        if progression_type == ProgressionType.UNKNOWN:
            for issue in issues:
                if issue.get("type") == "monotonic_progression":
                    progression_type = ProgressionType.MONOTONIC
                    if progression_score == 50:
                        progression_score = 75
                elif issue.get("type") == "too_strong_closure":
                    closure_type = ClosureType.STRONG
                    if closure_score == 0:
                        closure_score = 70

        # Calculate combined score
        # 计算综合分数
        combined_score = (progression_score + closure_score) // 2

        # Count sequential markers specifically
        # 统计顺序标记
        sequential_markers_found = sum(1 for m in progression_markers if m.category == "sequential")

        return ProgressionClosureResponse(
            progression_score=progression_score,
            progression_type=progression_type,
            monotonic_count=monotonic_count,
            non_monotonic_count=non_monotonic_count,
            sequential_markers_found=sequential_markers_found,
            progression_markers=progression_markers,
            closure_score=closure_score,
            closure_type=closure_type,
            strong_closure_patterns=[],
            weak_closure_patterns=[],
            last_paragraph_preview=last_paragraph[:200] if last_paragraph else "",
            combined_score=combined_score,
            risk_level=RiskLevel(result.get("risk_level", "low")),
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Progression/closure analysis failed: {e}", exc_info=True)
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
    Step 1.5: Content Substantiality Analysis (LOCAL + LLM HYBRID)
    步骤 1.5：内容实质性分析（本地模型 + LLM混合）

    Uses local analysis for generic phrases and anchor density,
    then LLM for deeper content substantiality analysis.
    使用本地分析检测泛化短语和锚点密度，然后用LLM进行更深入的内容实质性分析。
    """
    start_time = time.time()

    try:
        # Step 1: Local analysis using existing functions
        # 步骤1：使用现有函数进行本地分析
        paragraphs = _split_paragraphs(request.text, exclude_non_body=True)
        logger.info(f"Analyzing {len(paragraphs)} paragraphs for content substantiality")

        # Analyze each paragraph locally
        # 本地分析每个段落
        paragraph_analyses = []
        total_generic_count = 0
        total_filler_count = 0
        total_specific_count = 0
        low_quality_indices = []
        all_generic_phrases = []

        for idx, para in enumerate(paragraphs):
            analysis = _analyze_paragraph_substantiality(para, idx)
            paragraph_analyses.append(analysis)

            total_generic_count += analysis.generic_phrase_count
            total_specific_count += analysis.specific_detail_count
            all_generic_phrases.extend(analysis.generic_phrases)

            # Count filler words
            # 统计填充词
            words = para.lower().split()
            filler_count = sum(1 for w in words if w.strip(".,!?;:") in FILLER_WORDS)
            total_filler_count += filler_count

            # Track low quality paragraphs
            # 跟踪低质量段落
            if analysis.substantiality_level == SubstantialityLevel.LOW:
                low_quality_indices.append(idx)

        # Calculate overall metrics
        # 计算整体指标
        total_words = sum(len(p.split()) for p in paragraphs)
        avg_filler_ratio = total_filler_count / total_words if total_words > 0 else 0

        # Calculate overall specificity score (weighted average)
        # 计算整体具体性分数（加权平均）
        if paragraph_analyses:
            total_weight = sum(p.word_count for p in paragraph_analyses)
            if total_weight > 0:
                overall_specificity = sum(
                    p.specificity_score * p.word_count for p in paragraph_analyses
                ) / total_weight
            else:
                overall_specificity = 70  # Default
        else:
            overall_specificity = 70

        # Determine overall substantiality level
        # 确定整体实质性等级
        if overall_specificity >= 60:
            overall_level = SubstantialityLevel.HIGH
        elif overall_specificity >= 35:
            overall_level = SubstantialityLevel.MEDIUM
        else:
            overall_level = SubstantialityLevel.LOW

        # Calculate risk score (inverse of specificity)
        # 计算风险分数（具体性的反面）
        local_risk_score = max(0, min(100, 100 - overall_specificity))

        # Determine risk level
        # 确定风险等级
        if local_risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif local_risk_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Step 2: Call LLM for deeper analysis (only if local analysis found issues)
        # 步骤2：调用LLM进行更深入的分析（仅当本地分析发现问题时）
        llm_issues = []
        llm_recommendations = []
        llm_recommendations_zh = []

        if total_generic_count > 0 or len(low_quality_indices) > 0 or local_risk_score >= 35:
            logger.info("Calling Step1_5Handler for LLM-based content substantiality analysis")
            try:
                llm_result = await step1_5_handler.analyze(
                    document_text=request.text,
                    locked_terms=[]
                )
                llm_issues = llm_result.get("issues", [])
                llm_recommendations = llm_result.get("recommendations", [])
                llm_recommendations_zh = llm_result.get("recommendations_zh", [])

                # Update counts from LLM if available
                # 如果LLM返回了数据则更新统计
                llm_generic = llm_result.get("total_generic_phrases", 0)
                llm_filler = llm_result.get("total_filler_words", 0)
                if llm_generic > total_generic_count:
                    total_generic_count = llm_generic
                if llm_filler > total_filler_count:
                    total_filler_count = llm_filler

            except Exception as llm_error:
                logger.warning(f"LLM analysis failed, using local results only: {llm_error}")
                # Generate local recommendations
                # 生成本地建议
                if total_generic_count > 0:
                    llm_recommendations.append(f"Found {total_generic_count} generic phrases. Replace with specific claims.")
                    llm_recommendations_zh.append(f"发现{total_generic_count}个泛化短语，请用具体论述替换。")
                if len(low_quality_indices) > 0:
                    llm_recommendations.append(f"{len(low_quality_indices)} paragraphs lack specific content. Add data, examples, or citations.")
                    llm_recommendations_zh.append(f"{len(low_quality_indices)}个段落缺乏具体内容，请添加数据、例子或引用。")
        else:
            # Good content, provide positive feedback
            # 内容良好，提供正面反馈
            llm_recommendations = ["Content substantiality is good. No major issues detected."]
            llm_recommendations_zh = ["内容实质性良好，未检测到空洞表述或缺乏具体细节的问题。"]

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Get most common generic phrases
        # 获取最常见的泛化短语
        from collections import Counter
        phrase_counts = Counter(all_generic_phrases)
        common_generic = [phrase for phrase, _ in phrase_counts.most_common(5)]

        return ContentSubstantialityResponse(
            paragraph_count=len(paragraphs),
            overall_specificity_score=round(overall_specificity, 1),
            overall_substantiality=overall_level,
            risk_level=risk_level,
            total_generic_phrases=total_generic_count,
            total_specific_details=total_specific_count,
            average_filler_ratio=round(avg_filler_ratio, 3),
            low_substantiality_paragraphs=low_quality_indices,
            paragraphs=paragraph_analyses,
            common_generic_phrases=common_generic,
            recommendations=llm_recommendations,
            recommendations_zh=llm_recommendations_zh,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Content substantiality analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Merge-Modify Endpoints for Layer 5 Steps
# Layer 5步骤的合并修改端点
# =============================================================================

from src.api.routes.substeps.schemas import (
    MergeModifyRequest,
    MergeModifyPromptResponse,
    MergeModifyApplyResponse,
)


@router.post("/step1-1/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_step1_1_prompt(request: MergeModifyRequest):
    """
    Step 1.1: Generate modification prompt for structure issues
    步骤 1.1：为结构问题生成修改提示词
    """
    try:
        # Get document text: prefer direct text from request, fallback to DB lookup
        # 获取文档文本：优先使用请求中直接提供的文本，后备方案从数据库查询
        document_text = ""
        locked_terms = []

        # Priority 1: Use document_text directly from request
        # 优先级1：直接使用请求中的document_text
        if request.document_text:
            document_text = request.document_text
        # Priority 2: Fetch from database by document_id
        # 优先级2：通过document_id从数据库获取
        elif request.document_id:
            document_text = await get_working_text(request.document_id)

        # Get locked terms from step1_0
        # 从step1_0获取锁定术语
        if request.session_id:
            from src.api.routes.substeps.layer5.step1_0 import get_session_locked_terms
            locked_terms = get_session_locked_terms(request.session_id)

        if not document_text:
            logger.warning("Document text not found, generating prompt without context")
            document_text = "[Document text not available - please paste your document here]"

        result = await step1_1_handler.generate_rewrite_prompt(
            document_text=document_text,
            selected_issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )
        return MergeModifyPromptResponse(
            prompt=result.get("prompt", ""),
            prompt_zh=result.get("prompt_zh", "根据选定的结构问题生成的修改提示词"),
            issues_summary_zh=result.get("issues_summary_zh", f"选中了{len(request.selected_issues)}个问题"),
            estimated_changes=result.get("estimated_changes", len(request.selected_issues))
        )
    except Exception as e:
        logger.error(f"Step 1.1 prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step1-1/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_step1_1_modification(request: MergeModifyRequest):
    """
    Step 1.1: Apply AI modification for structure issues
    步骤 1.1：应用AI修改结构问题
    """
    try:
        # Get the document text from session or request
        from src.services.session_service import SessionService
        session_service = SessionService()
        session_data = await session_service.get_session(request.session_id) if request.session_id else None
        document_text = session_data.get("document_text", "") if session_data else ""

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found in session")

        result = await step1_1_handler.apply_rewrite(
            document_text=document_text,
            issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=session_data.get("locked_terms", []) if session_data else []
        )
        return MergeModifyApplyResponse(
            modified_text=result.get("modified_text", ""),
            changes_summary_zh=result.get("changes_summary_zh", ""),
            changes_count=result.get("changes_count", 0),
            issues_addressed=[i.type for i in request.selected_issues],
            remaining_attempts=3
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Step 1.1 modification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step1-2/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_step1_2_prompt(request: MergeModifyRequest):
    """
    Step 1.2: Generate modification prompt for paragraph length issues
    步骤 1.2：为段落长度问题生成修改提示词
    """
    try:
        # Get document text: prefer direct text from request, fallback to DB lookup
        # 获取文档文本：优先使用请求中直接提供的文本，后备方案从数据库查询
        document_text = ""
        locked_terms = []

        # Priority 1: Use document_text directly from request
        # 优先级1：直接使用请求中的document_text
        if request.document_text:
            document_text = request.document_text
        # Priority 2: Fetch from database by document_id
        # 优先级2：通过document_id从数据库获取
        elif request.document_id:
            document_text = await get_working_text(request.document_id)

        # Get locked terms from step1_0
        # 从step1_0获取锁定术语
        if request.session_id:
            from src.api.routes.substeps.layer5.step1_0 import get_session_locked_terms
            locked_terms = get_session_locked_terms(request.session_id)

        if not document_text:
            logger.warning("Document text not found, generating prompt without context")
            document_text = "[Document text not available - please paste your document here]"

        result = await step1_2_handler.generate_rewrite_prompt(
            document_text=document_text,
            selected_issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )
        return MergeModifyPromptResponse(
            prompt=result.get("prompt", ""),
            prompt_zh=result.get("prompt_zh", "根据选定的段落长度问题生成的修改提示词"),
            issues_summary_zh=result.get("issues_summary_zh", f"选中了{len(request.selected_issues)}个问题"),
            estimated_changes=result.get("estimated_changes", len(request.selected_issues))
        )
    except Exception as e:
        logger.error(f"Step 1.2 prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step1-2/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_step1_2_modification(request: MergeModifyRequest):
    """
    Step 1.2: Apply AI modification for paragraph length issues
    步骤 1.2：应用AI修改段落长度问题
    """
    try:
        from src.services.session_service import SessionService
        session_service = SessionService()
        session_data = await session_service.get_session(request.session_id) if request.session_id else None
        document_text = session_data.get("document_text", "") if session_data else ""

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found in session")

        result = await step1_2_handler.apply_rewrite(
            document_text=document_text,
            issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=session_data.get("locked_terms", []) if session_data else []
        )
        return MergeModifyApplyResponse(
            modified_text=result.get("modified_text", ""),
            changes_summary_zh=result.get("changes_summary_zh", ""),
            changes_count=result.get("changes_count", 0),
            issues_addressed=[i.type for i in request.selected_issues],
            remaining_attempts=3
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Step 1.2 modification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step1-3/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_step1_3_prompt(request: MergeModifyRequest):
    """
    Step 1.3: Generate modification prompt for progression/closure issues
    步骤 1.3：为推进/闭合问题生成修改提示词
    """
    try:
        # Get document text: prefer direct text from request, fallback to DB lookup
        # 获取文档文本：优先使用请求中直接提供的文本，后备方案从数据库查询
        document_text = ""
        locked_terms = []

        # Priority 1: Use document_text directly from request
        # 优先级1：直接使用请求中的document_text
        if request.document_text:
            document_text = request.document_text
        # Priority 2: Fetch from database by document_id
        # 优先级2：通过document_id从数据库获取
        elif request.document_id:
            document_text = await get_working_text(request.document_id)

        # Get locked terms from step1_0
        # 从step1_0获取锁定术语
        if request.session_id:
            from src.api.routes.substeps.layer5.step1_0 import get_session_locked_terms
            locked_terms = get_session_locked_terms(request.session_id)

        if not document_text:
            logger.warning("Document text not found, generating prompt without context")
            document_text = "[Document text not available - please paste your document here]"

        result = await step1_3_handler.generate_rewrite_prompt(
            document_text=document_text,
            selected_issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )
        return MergeModifyPromptResponse(
            prompt=result.get("prompt", ""),
            prompt_zh=result.get("prompt_zh", "根据选定的推进/闭合问题生成的修改提示词"),
            issues_summary_zh=result.get("issues_summary_zh", f"选中了{len(request.selected_issues)}个问题"),
            estimated_changes=result.get("estimated_changes", len(request.selected_issues))
        )
    except Exception as e:
        logger.error(f"Step 1.3 prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step1-3/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_step1_3_modification(request: MergeModifyRequest):
    """
    Step 1.3: Apply AI modification for progression/closure issues
    步骤 1.3：应用AI修改推进/闭合问题
    """
    try:
        from src.services.session_service import SessionService
        session_service = SessionService()
        session_data = await session_service.get_session(request.session_id) if request.session_id else None
        document_text = session_data.get("document_text", "") if session_data else ""

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found in session")

        result = await step1_3_handler.apply_rewrite(
            document_text=document_text,
            issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=session_data.get("locked_terms", []) if session_data else []
        )
        return MergeModifyApplyResponse(
            modified_text=result.get("modified_text", ""),
            changes_summary_zh=result.get("changes_summary_zh", ""),
            changes_count=result.get("changes_count", 0),
            issues_addressed=[i.type for i in request.selected_issues],
            remaining_attempts=3
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Step 1.3 modification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step1-4/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_step1_4_prompt(request: MergeModifyRequest):
    """
    Step 1.4: Generate modification prompt for connector issues
    步骤 1.4：为连接词问题生成修改提示词
    """
    try:
        # Get document text: prefer direct text from request, fallback to DB lookup
        # 获取文档文本：优先使用请求中直接提供的文本，后备方案从数据库查询
        document_text = ""
        locked_terms = []

        # Priority 1: Use document_text directly from request
        # 优先级1：直接使用请求中的document_text
        if request.document_text:
            document_text = request.document_text
        # Priority 2: Fetch from database by document_id
        # 优先级2：通过document_id从数据库获取
        elif request.document_id:
            document_text = await get_working_text(request.document_id)

        # Get locked terms from step1_0
        # 从step1_0获取锁定术语
        if request.session_id:
            from src.api.routes.substeps.layer5.step1_0 import get_session_locked_terms
            locked_terms = get_session_locked_terms(request.session_id)

        if not document_text:
            logger.warning("Document text not found, generating prompt without context")
            document_text = "[Document text not available - please paste your document here]"

        result = await step1_4_handler.generate_rewrite_prompt(
            document_text=document_text,
            selected_issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )
        return MergeModifyPromptResponse(
            prompt=result.get("prompt", ""),
            prompt_zh=result.get("prompt_zh", "根据选定的连接词问题生成的修改提示词"),
            issues_summary_zh=result.get("issues_summary_zh", f"选中了{len(request.selected_issues)}个问题"),
            estimated_changes=result.get("estimated_changes", len(request.selected_issues))
        )
    except Exception as e:
        logger.error(f"Step 1.4 prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step1-4/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_step1_4_modification(request: MergeModifyRequest):
    """
    Step 1.4: Apply AI modification for connector issues
    步骤 1.4：应用AI修改连接词问题
    """
    try:
        from src.services.session_service import SessionService
        session_service = SessionService()
        session_data = await session_service.get_session(request.session_id) if request.session_id else None
        document_text = session_data.get("document_text", "") if session_data else ""

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found in session")

        result = await step1_4_handler.apply_rewrite(
            document_text=document_text,
            issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=session_data.get("locked_terms", []) if session_data else []
        )
        return MergeModifyApplyResponse(
            modified_text=result.get("modified_text", ""),
            changes_summary_zh=result.get("changes_summary_zh", ""),
            changes_count=result.get("changes_count", 0),
            issues_addressed=[i.type for i in request.selected_issues],
            remaining_attempts=3
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Step 1.4 modification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step1-5/merge-modify/prompt", response_model=MergeModifyPromptResponse)
async def generate_step1_5_prompt(request: MergeModifyRequest):
    """
    Step 1.5: Generate modification prompt for substantiality issues
    步骤 1.5：为实质性问题生成修改提示词
    """
    try:
        # Get document text: prefer direct text from request, fallback to DB lookup
        # 获取文档文本：优先使用请求中直接提供的文本，后备方案从数据库查询
        document_text = ""
        locked_terms = []

        # Priority 1: Use document_text directly from request
        # 优先级1：直接使用请求中的document_text
        if request.document_text:
            document_text = request.document_text
        # Priority 2: Fetch from database by document_id
        # 优先级2：通过document_id从数据库获取
        elif request.document_id:
            document_text = await get_working_text(request.document_id)

        # Get locked terms from step1_0
        # 从step1_0获取锁定术语
        if request.session_id:
            from src.api.routes.substeps.layer5.step1_0 import get_session_locked_terms
            locked_terms = get_session_locked_terms(request.session_id)

        if not document_text:
            # Fallback: generate prompt without document context
            # 后备方案：生成不包含文档上下文的prompt
            logger.warning("Document text not found, generating prompt without context")
            document_text = "[Document text not available - please paste your document here]"

        result = await step1_5_handler.generate_rewrite_prompt(
            document_text=document_text,
            selected_issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=locked_terms
        )
        return MergeModifyPromptResponse(
            prompt=result.get("prompt", ""),
            prompt_zh=result.get("prompt_zh", "根据选定的实质性问题生成的修改提示词"),
            issues_summary_zh=result.get("issues_summary_zh", f"选中了{len(request.selected_issues)}个问题"),
            estimated_changes=result.get("estimated_changes", len(request.selected_issues))
        )
    except Exception as e:
        logger.error(f"Step 1.5 prompt generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step1-5/merge-modify/apply", response_model=MergeModifyApplyResponse)
async def apply_step1_5_modification(request: MergeModifyRequest):
    """
    Step 1.5: Apply AI modification for substantiality issues
    步骤 1.5：应用AI修改实质性问题
    """
    try:
        from src.services.session_service import SessionService
        session_service = SessionService()
        session_data = await session_service.get_session(request.session_id) if request.session_id else None
        document_text = session_data.get("document_text", "") if session_data else ""

        if not document_text:
            raise HTTPException(status_code=400, detail="Document text not found in session")

        result = await step1_5_handler.apply_rewrite(
            document_text=document_text,
            issues=request.selected_issues,
            user_notes=request.user_notes,
            locked_terms=session_data.get("locked_terms", []) if session_data else []
        )
        return MergeModifyApplyResponse(
            modified_text=result.get("modified_text", ""),
            changes_summary_zh=result.get("changes_summary_zh", ""),
            changes_count=result.get("changes_count", 0),
            issues_addressed=[i.type for i in request.selected_issues],
            remaining_attempts=3
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Step 1.5 modification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
# Force reload
