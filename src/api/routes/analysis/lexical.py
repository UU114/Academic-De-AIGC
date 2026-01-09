"""
Lexical Layer API Routes (Layer 1)
词汇层API路由（第1层）

This is the finest granularity layer, analyzing individual words and phrases.
这是最细粒度的层，分析单个词和短语。

Endpoints:
- POST /fingerprint - Step 5.1: Fingerprint Detection
- POST /connector - Step 5.2: Connector Analysis
- POST /word-risk - Step 5.3: Word-Level Risk
- POST /analyze - Combined lexical analysis
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import logging
import time

from src.api.routes.analysis.schemas import (
    LexicalAnalysisRequest,
    LexicalAnalysisResponse,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
    IssueSeverity,
)
from src.core.analyzer.layers import LexicalOrchestrator, LayerContext

logger = logging.getLogger(__name__)
router = APIRouter()


def _convert_issue(issue) -> DetectionIssue:
    """Convert internal issue to API schema"""
    return DetectionIssue(
        type=issue.type,
        description=issue.description,
        description_zh=issue.description_zh,
        severity=IssueSeverity(issue.severity.value),
        layer=LayerLevel.LEXICAL,
        position=issue.position,
        suggestion=issue.suggestion,
        suggestion_zh=issue.suggestion_zh,
        details=issue.details,
    )


@router.post("/fingerprint", response_model=LexicalAnalysisResponse)
async def analyze_fingerprints(request: LexicalAnalysisRequest):
    """
    Step 5.1: Fingerprint Detection
    步骤 5.1：指纹词检测

    Consolidated fingerprint detection:
    - Type A: Dead Giveaways (+40 risk) - delve, tapestry, multifaceted, etc.
    - Type B: Academic Clichés (+5-25 risk) - crucial, robust, leverage, etc.
    - Type C: Connectors (+10-30 risk) - furthermore, moreover, etc.
    - Phrases: Multi-word AI patterns

    Returns matches with replacement suggestions.
    """
    start_time = time.time()

    try:
        orchestrator = LexicalOrchestrator()

        # Create context with text
        context = LayerContext(
            full_text=request.text,
            sentences=request.sentences,
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract fingerprint-specific details
        fingerprint_details = result.details.get("fingerprints", {})

        # Build fingerprint matches structure
        fingerprint_matches = {
            "type_a": fingerprint_details.get("type_a_matches", []),
            "type_b": fingerprint_details.get("type_b_matches", []),
            "phrases": fingerprint_details.get("phrase_matches", []),
        }

        return LexicalAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "fingerprint" in i.type or "density" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=fingerprint_details,
            processing_time_ms=processing_time_ms,
            fingerprint_matches=fingerprint_matches,
            fingerprint_density=fingerprint_details.get("fingerprint_density", 0),
            connector_matches=[],
            connector_ratio=0,
            replacement_suggestions=result.details.get("word_risk", {}).get("replacement_suggestions", {}),
        )

    except Exception as e:
        logger.error(f"Fingerprint analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connector", response_model=LexicalAnalysisResponse)
async def analyze_connectors(request: LexicalAnalysisRequest):
    """
    Step 5.2: Connector Analysis
    步骤 5.2：连接词分析

    Detects overuse of explicit connectors (AI pattern):
    - Furthermore, Moreover, Additionally
    - Consequently, Subsequently, Nevertheless
    - It is important to note that, etc.

    Analyzes connector usage at sentence starts.
    """
    start_time = time.time()

    try:
        orchestrator = LexicalOrchestrator()

        # Create context with text
        context = LayerContext(
            full_text=request.text,
            sentences=request.sentences,
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract connector-specific details
        connector_details = result.details.get("connectors", {})

        return LexicalAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "connector" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=connector_details,
            processing_time_ms=processing_time_ms,
            fingerprint_matches={},
            fingerprint_density=0,
            connector_matches=connector_details.get("connector_matches", []),
            connector_ratio=connector_details.get("sentence_start_connector_ratio", 0),
            replacement_suggestions=result.details.get("word_risk", {}).get("replacement_suggestions", {}),
        )

    except Exception as e:
        logger.error(f"Connector analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/word-risk", response_model=LexicalAnalysisResponse)
async def analyze_word_risk(request: LexicalAnalysisRequest):
    """
    Step 5.3: Word-Level Risk
    步骤 5.3：词级风险

    Calculates aggregate word-level risk:
    - Normalized risk score (0-100)
    - Per-word risk breakdown
    - Replacement suggestions for high-risk words
    """
    start_time = time.time()

    try:
        orchestrator = LexicalOrchestrator()

        # Create context with text
        context = LayerContext(
            full_text=request.text,
            sentences=request.sentences,
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract word risk-specific details
        word_risk_details = result.details.get("word_risk", {})
        fingerprint_details = result.details.get("fingerprints", {})
        connector_details = result.details.get("connectors", {})

        return LexicalAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues if "risk" in i.type or "lexical" in i.type],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=word_risk_details,
            processing_time_ms=processing_time_ms,
            fingerprint_matches={
                "type_a": fingerprint_details.get("type_a_matches", []),
                "type_b": fingerprint_details.get("type_b_matches", []),
                "phrases": fingerprint_details.get("phrase_matches", []),
            },
            fingerprint_density=fingerprint_details.get("fingerprint_density", 0),
            connector_matches=connector_details.get("connector_matches", []),
            connector_ratio=connector_details.get("sentence_start_connector_ratio", 0),
            replacement_suggestions=word_risk_details.get("replacement_suggestions", {}),
        )

    except Exception as e:
        logger.error(f"Word risk analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=LexicalAnalysisResponse)
async def analyze_lexical(request: LexicalAnalysisRequest):
    """
    Combined Lexical Analysis (Layer 1)
    综合词汇分析（第1层）

    Runs all lexical-level analysis steps:
    - Step 5.1: Fingerprint Detection (consolidated)
    - Step 5.2: Connector Analysis (consolidated)
    - Step 5.3: Word-Level Risk

    Returns complete lexical-level analysis with:
    - All fingerprint matches (Type A, B, C, and phrases)
    - Connector usage patterns
    - Normalized risk score
    - Replacement suggestions
    """
    start_time = time.time()

    try:
        orchestrator = LexicalOrchestrator()

        # Create context with text and optional sentence context
        context = LayerContext(
            full_text=request.text,
            sentences=request.sentences,
        )

        # Apply Layer 2 context if provided
        if request.sentence_context:
            context.sentence_roles = request.sentence_context.get("sentence_roles", [])

        # Run full analysis
        result = await orchestrator.analyze(context)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract all details
        fingerprint_details = result.details.get("fingerprints", {})
        connector_details = result.details.get("connectors", {})
        word_risk_details = result.details.get("word_risk", {})

        return LexicalAnalysisResponse(
            risk_score=result.risk_score,
            risk_level=RiskLevel(result.risk_level.value),
            issues=[_convert_issue(i) for i in result.issues],
            recommendations=result.recommendations,
            recommendations_zh=result.recommendations_zh,
            details=result.details,
            processing_time_ms=processing_time_ms,
            fingerprint_matches={
                "type_a": fingerprint_details.get("type_a_matches", []),
                "type_b": fingerprint_details.get("type_b_matches", []),
                "phrases": fingerprint_details.get("phrase_matches", []),
            },
            fingerprint_density=fingerprint_details.get("fingerprint_density", 0),
            connector_matches=connector_details.get("connector_matches", []),
            connector_ratio=connector_details.get("sentence_start_connector_ratio", 0),
            replacement_suggestions=word_risk_details.get("replacement_suggestions", {}),
        )

    except Exception as e:
        logger.error(f"Lexical analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/replacements")
async def get_replacement_suggestions(request: LexicalAnalysisRequest):
    """
    Get Replacement Suggestions for Flagged Words
    获取标记词的替换建议

    Returns a map of flagged words/phrases to their suggested replacements.
    This is useful for automated or semi-automated text rewriting.
    """
    try:
        orchestrator = LexicalOrchestrator()

        # Create context with text
        context = LayerContext(
            full_text=request.text,
            sentences=request.sentences,
        )

        # Run analysis
        result = await orchestrator.analyze(context)

        # Extract replacement suggestions
        word_risk_details = result.details.get("word_risk", {})
        fingerprint_details = result.details.get("fingerprints", {})
        connector_details = result.details.get("connectors", {})

        return {
            "replacement_suggestions": word_risk_details.get("replacement_suggestions", {}),
            "type_a_words": [m["word"] for m in fingerprint_details.get("type_a_matches", [])],
            "type_b_words": [m["word"] for m in fingerprint_details.get("type_b_matches", [])],
            "flagged_connectors": [m["connector"] for m in connector_details.get("connector_matches", [])[:5]],
            "fingerprint_density": fingerprint_details.get("fingerprint_density", 0),
        }

    except Exception as e:
        logger.error(f"Replacement suggestions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
