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

    Uses LLM to detect AI-like structural patterns:
    - Linear flow (First-Second-Third)
    - Repetitive patterns
    - Uniform length
    - Predictable order
    - Symmetry

    Supports caching: Returns cached results if available for this session.
    支持缓存：如果此会话有缓存结果，将直接返回。
    """
    start_time = time.time()

    try:
        # Use new LLM handler for analysis (with caching support)
        logger.info("Calling Step1_1Handler for LLM-based structure analysis")
        result = await step1_1_handler.analyze(
            document_text=request.text,
            locked_terms=[],  # No locked terms yet in Step 1.1
            session_id=request.session_id,  # Get session_id from request for caching
            step_name="layer5-step1-1",  # Unique step identifier for caching
            use_cache=True  # Enable caching
        )

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Convert issues to API format
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

        # Extract sections from LLM analysis result (TASK A output)
        # 从LLM分析结果中提取章节数据（任务A输出）
        paragraphs = [p.strip() for p in request.text.split('\n\n') if p.strip()]
        sections = []
        structure_pattern = result.get("structure_pattern", "Unknown")

        # Use LLM-detected sections if available
        # 如果LLM返回了章节数据，则使用它
        llm_sections = result.get("sections", [])
        if llm_sections:
            logger.info(f"Using LLM-detected sections: {len(llm_sections)} sections found")
            for idx, sec in enumerate(llm_sections):
                sections.append(DocumentSection(
                    index=sec.get("index", idx),
                    role=sec.get("role", "body"),
                    title=sec.get("title", f"Section {idx + 1}"),
                    paragraph_count=sec.get("paragraph_count", 1),
                    word_count=sec.get("word_count", 0)
                ))
        else:
            # Fallback: Simple section detection based on paragraph count
            # 回退：基于段落数量的简单章节检测
            logger.warning("LLM did not return sections, using fallback heuristic")
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

                intro_words = len(paragraphs[0].split()) if paragraphs else 0
                body_words = sum(len(paragraphs[i].split()) for i in range(intro_count, intro_count + body_count))
                conclusion_words = len(paragraphs[-1].split()) if paragraphs else 0

                sections = [
                    DocumentSection(index=0, role="introduction", title="Introduction", paragraph_count=intro_count, word_count=intro_words),
                    DocumentSection(index=1, role="body", title="Body", paragraph_count=body_count, word_count=body_words),
                    DocumentSection(index=2, role="conclusion", title="Conclusion", paragraph_count=conclusion_count, word_count=conclusion_words),
                ]

        return DocumentAnalysisResponse(
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "low")),
            issues=issues_converted,
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
            details={"llm_analysis": result},
            processing_time_ms=processing_time_ms,
            structure={},
            predictability_score={},
            paragraph_count=len(paragraphs),
            word_count=len(request.text.split()),
            # LLM-based section analysis / LLM章节分析
            structure_pattern=structure_pattern,
            sections=sections,
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
    Split text into paragraphs by double newlines or single newlines
    按双换行或单换行将文本分割为段落

    Args:
        text: Document text to split
        exclude_non_body: If True, exclude titles, headers, figure captions, etc.
                         如果为True，排除标题、表头、图名等非正文内容
    """
    # Try double newline first
    paragraphs = re.split(r'\n\n+', text.strip())
    # If only one paragraph, try single newline
    if len(paragraphs) == 1:
        paragraphs = re.split(r'\n', text.strip())
    # Filter empty paragraphs
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not exclude_non_body:
        return paragraphs

    # Filter out non-body content
    # 过滤非正文内容
    filtered = []
    for p in paragraphs:
        # Skip if too short (likely title/header)
        # 跳过太短的内容（可能是标题）
        word_count = len(p.split())
        if word_count < 5:
            continue

        # Skip common non-paragraph patterns
        # 跳过常见的非段落模式
        p_lower = p.lower().strip()

        # Skip section headers (numbered or common titles)
        # 跳过章节标题
        if re.match(r'^(\d+\.?\s+|[ivxlcdm]+\.?\s+|chapter\s+\d|section\s+\d)', p_lower):
            continue
        if re.match(r'^(abstract|introduction|methodology|methods|results|discussion|conclusion|references|acknowledgment|appendix)s?\s*$', p_lower):
            continue

        # Skip figure/table captions
        # 跳过图表标题
        if re.match(r'^(figure|fig\.?|table|tab\.?|图|表)\s*\d', p_lower):
            continue

        # Skip keywords line
        # 跳过关键词行
        if p_lower.startswith(('keywords:', 'key words:', '关键词', '关键字')):
            continue

        # Skip reference entries (usually start with [number] or author name followed by year)
        # 跳过参考文献条目
        if re.match(r'^\[\d+\]', p) or re.match(r'^[A-Z][a-z]+,?\s+[A-Z].*\(\d{4}\)', p):
            continue

        # Skip lines that are all caps (likely headers)
        # 跳过全大写行（可能是标题）
        if p.isupper() and word_count < 10:
            continue

        filtered.append(p)

    return filtered


@router.post("/connectors", response_model=ConnectorAnalysisResponse)
async def analyze_connectors(request: ConnectorAnalysisRequest):
    """
    Step 1.4: Connector & Transition Analysis (NOW WITH LLM!)
    步骤 1.4：连接词与衔接分析（现在使用LLM！）

    Uses LLM to analyze paragraph transitions for AI-like patterns.
    使用LLM分析段落衔接的AI风格模式。
    """
    start_time = time.time()

    try:
        # Use LLM handler for analysis
        logger.info("Calling Step1_4Handler for LLM-based connector analysis")
        result = await step1_4_handler.analyze(
            document_text=request.text,
            locked_terms=[]
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

    Uses LLM to analyze paragraph length distribution for AI-like uniformity.
    使用LLM分析段落长度分布中的AI特征。
    """
    start_time = time.time()

    try:
        # Use LLM handler for analysis with caching support
        logger.info("Calling Step1_2Handler for LLM-based paragraph length analysis")
        result = await step1_2_handler.analyze(
            document_text=request.text,
            locked_terms=[],
            session_id=request.session_id,  # Pass session_id for caching
            step_name="layer5-step1-2",     # Unique step identifier
            use_cache=True                   # Enable caching
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract LLM analysis data
        # 提取LLM分析数据
        issues = result.get("issues", [])
        statistics_data = result.get("statistics", {})
        paragraph_analysis = result.get("paragraph_analysis", {})

        # Use LLM statistics if available, otherwise calculate from text
        # 优先使用LLM统计数据，否则从文本计算
        if statistics_data:
            mean_len = statistics_data.get("mean_length", 0)
            stdev_len = statistics_data.get("stdev_length", 0)
            cv = statistics_data.get("cv", 0)
            min_len = statistics_data.get("min_length", 0)
            max_len = statistics_data.get("max_length", 0)
            para_count = paragraph_analysis.get("total_body_paragraphs", 0)
            lengths = paragraph_analysis.get("paragraph_lengths", [])
            total_word_count = sum(lengths) if lengths else 0
        else:
            # Fallback: Calculate from text (with filtering)
            # 回退：从文本计算（带过滤）
            paragraphs = _split_paragraphs(request.text, exclude_non_body=True)
            lengths = [len(p.split()) for p in paragraphs] if paragraphs else [0]
            para_count = len(paragraphs)
            total_word_count = sum(lengths)
            mean_len = statistics.mean(lengths) if lengths else 0
            stdev_len = statistics.stdev(lengths) if len(lengths) > 1 else 0
            cv = stdev_len / mean_len if mean_len > 0 else 0
            min_len = min(lengths) if lengths else 0
            max_len = max(lengths) if lengths else 0

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

    Uses LLM to analyze document progression patterns and closure strength.
    使用LLM分析文档推进模式和闭合强度。
    """
    start_time = time.time()

    try:
        # Use LLM handler for analysis
        logger.info("Calling Step1_3Handler for LLM-based progression/closure analysis")
        result = await step1_3_handler.analyze(
            document_text=request.text,
            locked_terms=[]
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract issues and infer types
        issues = result.get("issues", [])
        progression_type = ProgressionType.UNKNOWN
        closure_type = ClosureType.MODERATE
        progression_score = result.get("risk_score", 0)
        closure_score = 0

        for issue in issues:
            if issue.get("type") == "monotonic_progression":
                progression_type = ProgressionType.MONOTONIC
            elif issue.get("type") == "too_strong_closure":
                closure_type = ClosureType.STRONG
                closure_score = 70

        combined_score = (progression_score + closure_score) // 2

        return ProgressionClosureResponse(
            progression_score=progression_score,
            progression_type=progression_type,
            monotonic_count=sum(1 for i in issues if "monotonic" in i.get("type", "")),
            non_monotonic_count=0,
            sequential_markers_found=0,
            progression_markers=[],
            closure_score=closure_score,
            closure_type=closure_type,
            strong_closure_patterns=[],
            weak_closure_patterns=[],
            last_paragraph_preview="",
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
    Step 1.5: Content Substantiality Analysis (NOW WITH LLM!)
    步骤 1.5：内容实质性分析（现在使用LLM！）

    Uses LLM to analyze content for specificity vs. generic AI-like patterns.
    使用LLM分析内容的具体性与泛泛的AI风格模式。
    """
    start_time = time.time()

    try:
        # Use LLM handler for analysis
        logger.info("Calling Step1_5Handler for LLM-based content substantiality analysis")
        result = await step1_5_handler.analyze(
            document_text=request.text,
            locked_terms=[]
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract issues
        issues = result.get("issues", [])

        # Count from issues
        total_generic = sum(1 for i in issues if "generic" in i.get("type", ""))
        total_specific = 0

        # Determine overall level based on risk score
        risk_score = result.get("risk_score", 0)
        if risk_score < 35:
            overall_level = SubstantialityLevel.HIGH
        elif risk_score < 60:
            overall_level = SubstantialityLevel.MEDIUM
        else:
            overall_level = SubstantialityLevel.LOW

        # Calculate paragraph count
        paragraphs = _split_paragraphs(request.text)

        return ContentSubstantialityResponse(
            paragraph_count=len(paragraphs),
            overall_specificity_score=max(0, 100 - risk_score),
            overall_substantiality=overall_level,
            risk_level=RiskLevel(result.get("risk_level", "low")),
            total_generic_phrases=total_generic,
            total_specific_details=total_specific,
            average_filler_ratio=0,
            low_substantiality_paragraphs=[],
            paragraphs=[],
            common_generic_phrases=[],
            recommendations=result.get("recommendations", []),
            recommendations_zh=result.get("recommendations_zh", []),
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
        prompt = await step1_1_handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的结构问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
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
        prompt = await step1_2_handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的段落长度问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
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
        prompt = await step1_3_handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的推进/闭合问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
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
        prompt = await step1_4_handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的连接词问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
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
        prompt = await step1_5_handler.generate_rewrite_prompt(
            issues=request.selected_issues,
            user_notes=request.user_notes
        )
        return MergeModifyPromptResponse(
            prompt=prompt,
            prompt_zh="根据选定的实质性问题生成的修改提示词",
            issues_summary_zh=f"选中了{len(request.selected_issues)}个问题",
            estimated_changes=len(request.selected_issues)
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
