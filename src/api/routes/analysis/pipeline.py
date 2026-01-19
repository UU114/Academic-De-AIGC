"""
Pipeline Analysis API Routes
全流水线分析API路由

Orchestrates all 5 layers in sequence with context passing:
Layer 5: Document → Layer 4: Section → Layer 3: Paragraph →
Layer 2: Sentence → Layer 1: Lexical

Endpoints:
- POST /full - Full pipeline analysis (all layers)
- POST /partial - Partial pipeline (selected layers)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.services.task_service import TaskService
from src.api.routes.analysis.schemas import (
    PipelineAnalysisRequest,
    PipelineAnalysisResponse,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
    IssueSeverity,
    LayerAnalysisResult,
)
from src.core.analyzer.layers import (
    LayerContext,
    DocumentOrchestrator,
    SectionAnalyzer,
    ParagraphOrchestrator,
    SentenceOrchestrator,
    LexicalOrchestrator,
)
from src.services.word_counter import get_word_counter

logger = logging.getLogger(__name__)
router = APIRouter()


def _convert_issue(issue, layer: LayerLevel) -> DetectionIssue:
    """Convert internal issue to API schema"""
    return DetectionIssue(
        type=issue.type,
        description=issue.description,
        description_zh=issue.description_zh,
        severity=IssueSeverity(issue.severity.value),
        layer=layer,
        position=issue.position,
        suggestion=issue.suggestion,
        suggestion_zh=issue.suggestion_zh,
        details=issue.details,
    )


def _convert_layer_result(result, layer: LayerLevel) -> LayerAnalysisResult:
    """Convert internal layer result to API schema"""
    return LayerAnalysisResult(
        layer=layer,
        risk_score=result.risk_score,
        risk_level=RiskLevel(result.risk_level.value),
        issues=[_convert_issue(i, layer) for i in result.issues],
        recommendations=result.recommendations,
        recommendations_zh=result.recommendations_zh,
        details=result.details,
        processing_time_ms=getattr(result, 'processing_time_ms', None),
    )


@router.post("/full", response_model=PipelineAnalysisResponse)
async def analyze_full_pipeline(
    request: PipelineAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Full Pipeline Analysis
    全流水线分析

    Runs all 5 layers in sequence:
    1. Layer 5: Document (文章层) - structure analysis, global risk
    2. Layer 4: Section (章节层) - logic flow, transitions, length
    3. Layer 3: Paragraph (段落层) - roles, coherence, anchors, sentence lengths
    4. Layer 2: Sentence (句子层) - patterns, voids, roles, polish context
    5. Layer 1: Lexical (词汇层) - fingerprints, connectors, word risk

    Context is passed between layers for accurate, context-aware analysis.
    上下文在层之间传递，以进行准确的上下文感知分析。
    """
    start_time = time.time()

    try:
        layer_results: Dict[str, LayerAnalysisResult] = {}
        all_issues: List[DetectionIssue] = []
        layers_analyzed: List[LayerLevel] = []

        # Automatic Reference Stripping (Consistent with billing logic)
        # 自动剥离参考文献（与计费逻辑一致）
        word_counter = get_word_counter()
        clean_text, has_refs = word_counter._strip_references(request.text)
        
        if has_refs:
            logger.info("References stripped from analysis input")

        # Billing Verification (Capacity Check)
        # 计费校验（容量检查）
        if request.task_id:
            task_service = TaskService(db)
            task = await task_service.get_task(request.task_id)
            
            if task and task.word_count_billable:
                # Calculate current word count on CLEANED text (consistent with billing)
                current_count = word_counter._count_words(clean_text)
                paid_count = task.word_count_billable
                threshold = int(paid_count * 1.3)  # 130% threshold

                if current_count > threshold:
                    logger.warning(f"Word count limit exceeded: {current_count} > {threshold} (Paid: {paid_count})")
                    raise HTTPException(
                        status_code=402,  # Payment Required
                        detail={
                            "error": "word_count_exceeded",
                            "message": f"Text length ({current_count} words) exceeds the paid limit by more than 30%. Allowed: {threshold} words. Please add payment.",
                            "message_zh": f"文本长度 ({current_count} 词) 超过已支付额度 30% 以上。允许上限：{threshold} 词。请补充支付费用。"
                        }
                    )
                else:
                    logger.info(f"Billing check passed: {current_count}/{paid_count} words")

        # Initialize context with CLEANED text
        context = LayerContext(full_text=clean_text)

        # Layer 5: Document
        if LayerLevel.DOCUMENT in request.layers:
            logger.info("Running Layer 5: Document analysis")
            doc_orchestrator = DocumentOrchestrator()
            doc_result = await doc_orchestrator.analyze(context)

            layer_results["document"] = _convert_layer_result(doc_result, LayerLevel.DOCUMENT)
            all_issues.extend([_convert_issue(i, LayerLevel.DOCUMENT) for i in doc_result.issues])
            layers_analyzed.append(LayerLevel.DOCUMENT)

            # Update context with document results
            context = doc_result.updated_context

            # Early termination check
            if request.stop_on_low_risk and doc_result.risk_level.value == "low":
                logger.info("Document layer returned low risk, stopping early")
                return _build_response(
                    layer_results, all_issues, layers_analyzed,
                    start_time, request.layers, early_stop=True
                )

        # Layer 4: Section
        if LayerLevel.SECTION in request.layers:
            logger.info("Running Layer 4: Section analysis")
            section_analyzer = SectionAnalyzer()
            section_result = await section_analyzer.analyze(context)

            layer_results["section"] = _convert_layer_result(section_result, LayerLevel.SECTION)
            all_issues.extend([_convert_issue(i, LayerLevel.SECTION) for i in section_result.issues])
            layers_analyzed.append(LayerLevel.SECTION)

            # Update context with section results
            context = section_result.updated_context

            # Early termination check
            if request.stop_on_low_risk and section_result.risk_level.value == "low":
                logger.info("Section layer returned low risk, stopping early")
                return _build_response(
                    layer_results, all_issues, layers_analyzed,
                    start_time, request.layers, early_stop=True
                )

        # Layer 3: Paragraph
        if LayerLevel.PARAGRAPH in request.layers:
            logger.info("Running Layer 3: Paragraph analysis")
            para_orchestrator = ParagraphOrchestrator()
            para_result = await para_orchestrator.analyze(context)

            layer_results["paragraph"] = _convert_layer_result(para_result, LayerLevel.PARAGRAPH)
            all_issues.extend([_convert_issue(i, LayerLevel.PARAGRAPH) for i in para_result.issues])
            layers_analyzed.append(LayerLevel.PARAGRAPH)

            # Update context with paragraph results
            context = para_result.updated_context

            # Early termination check
            if request.stop_on_low_risk and para_result.risk_level.value == "low":
                logger.info("Paragraph layer returned low risk, stopping early")
                return _build_response(
                    layer_results, all_issues, layers_analyzed,
                    start_time, request.layers, early_stop=True
                )

        # Layer 2: Sentence (requires paragraph context)
        if LayerLevel.SENTENCE in request.layers:
            logger.info("Running Layer 2: Sentence analysis (with paragraph context)")
            sent_orchestrator = SentenceOrchestrator()
            sent_result = await sent_orchestrator.analyze(context)

            layer_results["sentence"] = _convert_layer_result(sent_result, LayerLevel.SENTENCE)
            all_issues.extend([_convert_issue(i, LayerLevel.SENTENCE) for i in sent_result.issues])
            layers_analyzed.append(LayerLevel.SENTENCE)

            # Update context with sentence results
            context = sent_result.updated_context

            # Early termination check
            if request.stop_on_low_risk and sent_result.risk_level.value == "low":
                logger.info("Sentence layer returned low risk, stopping early")
                return _build_response(
                    layer_results, all_issues, layers_analyzed,
                    start_time, request.layers, early_stop=True
                )

        # Layer 1: Lexical
        if LayerLevel.LEXICAL in request.layers:
            logger.info("Running Layer 1: Lexical analysis")
            lex_orchestrator = LexicalOrchestrator()
            lex_result = await lex_orchestrator.analyze(context)

            layer_results["lexical"] = _convert_layer_result(lex_result, LayerLevel.LEXICAL)
            all_issues.extend([_convert_issue(i, LayerLevel.LEXICAL) for i in lex_result.issues])
            layers_analyzed.append(LayerLevel.LEXICAL)

        return _build_response(
            layer_results, all_issues, layers_analyzed,
            start_time, request.layers, early_stop=False
        )

    except Exception as e:
        logger.error(f"Pipeline analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_response(
    layer_results: Dict[str, LayerAnalysisResult],
    all_issues: List[DetectionIssue],
    layers_analyzed: List[LayerLevel],
    start_time: float,
    requested_layers: List[LayerLevel],
    early_stop: bool = False,
) -> PipelineAnalysisResponse:
    """Build the pipeline response"""

    # Calculate overall risk score (weighted average of layer scores)
    if layer_results:
        layer_weights = {
            "document": 0.20,
            "section": 0.15,
            "paragraph": 0.25,
            "sentence": 0.25,
            "lexical": 0.15,
        }

        total_weight = 0
        weighted_score = 0

        for layer_name, result in layer_results.items():
            weight = layer_weights.get(layer_name, 0.2)
            weighted_score += result.risk_score * weight
            total_weight += weight

        overall_risk_score = int(weighted_score / total_weight) if total_weight > 0 else 0
    else:
        overall_risk_score = 0

    # Determine overall risk level
    if overall_risk_score >= 70:
        overall_risk_level = RiskLevel.HIGH
    elif overall_risk_score >= 40:
        overall_risk_level = RiskLevel.MEDIUM
    else:
        overall_risk_level = RiskLevel.LOW

    # Get priority issues (high severity from any layer)
    priority_issues = [i for i in all_issues if i.severity == IssueSeverity.HIGH]
    priority_issues = sorted(priority_issues, key=lambda x: x.layer.value)[:10]  # Top 10

    # Calculate processing time
    processing_time_ms = int((time.time() - start_time) * 1000)

    return PipelineAnalysisResponse(
        overall_risk_score=overall_risk_score,
        overall_risk_level=overall_risk_level,
        layers_analyzed=layers_analyzed,
        layer_results=layer_results,
        total_issues=len(all_issues),
        priority_issues=priority_issues,
        processing_time_ms=processing_time_ms,
        timestamp=datetime.utcnow(),
    )


@router.post("/partial", response_model=PipelineAnalysisResponse)
async def analyze_partial_pipeline(request: PipelineAnalysisRequest):
    """
    Partial Pipeline Analysis
    部分流水线分析

    Runs only the specified layers. Useful for:
    - Focused analysis on specific areas
    - Performance optimization
    - Incremental analysis

    Note: Some layers depend on context from upper layers.
    If upper layer context is missing, default values will be used.
    """
    return await analyze_full_pipeline(request)


@router.get("/layers")
async def get_available_layers():
    """
    Get Available Layers
    获取可用层级

    Returns information about each layer and their steps.
    """
    return {
        "layers": [
            {
                "level": LayerLevel.DOCUMENT.value,
                "name": "Document Layer | 文章层",
                "steps": [
                    {"id": "1.1", "name": "Structure Analysis | 结构分析"},
                    {"id": "1.2", "name": "Global Risk Assessment | 全局风险评估"},
                ],
                "weight": 0.20,
            },
            {
                "level": LayerLevel.SECTION.value,
                "name": "Section Layer | 章节层",
                "steps": [
                    {"id": "2.1", "name": "Section Logic Flow | 章节逻辑流"},
                    {"id": "2.2", "name": "Section Transitions | 章节衔接"},
                    {"id": "2.3", "name": "Section Length Distribution | 章节长度分布"},
                ],
                "weight": 0.15,
            },
            {
                "level": LayerLevel.PARAGRAPH.value,
                "name": "Paragraph Layer | 段落层",
                "steps": [
                    {"id": "3.1", "name": "Paragraph Role Detection | 段落角色识别"},
                    {"id": "3.2", "name": "Paragraph Internal Coherence | 段落内部连贯性"},
                    {"id": "3.3", "name": "Anchor Density Analysis | 锚点密度分析"},
                    {"id": "3.4", "name": "Sentence Length Distribution | 段内句子长度分布"},
                ],
                "weight": 0.25,
            },
            {
                "level": LayerLevel.SENTENCE.value,
                "name": "Sentence Layer | 句子层",
                "steps": [
                    {"id": "4.1", "name": "Sentence Pattern Detection | 句式模式检测"},
                    {"id": "4.2", "name": "Syntactic Void Detection | 句法空洞检测"},
                    {"id": "4.3", "name": "Sentence Role Classification | 句子角色分类"},
                    {"id": "4.4", "name": "Sentence Polish Context | 句子润色上下文"},
                ],
                "weight": 0.25,
                "note": "Requires paragraph context | 需要段落上下文",
            },
            {
                "level": LayerLevel.LEXICAL.value,
                "name": "Lexical Layer | 词汇层",
                "steps": [
                    {"id": "5.1", "name": "Fingerprint Detection | 指纹词检测"},
                    {"id": "5.2", "name": "Connector Analysis | 连接词分析"},
                    {"id": "5.3", "name": "Word-Level Risk | 词级风险"},
                ],
                "weight": 0.15,
            },
        ],
        "default_order": [
            LayerLevel.DOCUMENT.value,
            LayerLevel.SECTION.value,
            LayerLevel.PARAGRAPH.value,
            LayerLevel.SENTENCE.value,
            LayerLevel.LEXICAL.value,
        ],
        "context_flow": "Document → Section → Paragraph → Sentence → Lexical",
    }
