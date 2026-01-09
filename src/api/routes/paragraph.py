"""
============================================
DEPRECATED: Legacy Paragraph Analysis API
已废弃：旧版段落分析API
============================================

This module uses the OLD API structure and is superseded by:
- New 5-Layer Analysis API: /api/v1/analysis/paragraph/*
- Located at: src/api/routes/analysis/paragraph.py

Frontend should use:
- LayerStep3_0.tsx through LayerStep3_5.tsx
- paragraphLayerApi from analysisApi.ts

DO NOT DELETE - kept for backward compatibility
请勿删除 - 保留用于向后兼容
============================================

Paragraph-level analysis and restructuring API
段落级分析与重组API

Provides endpoints for:
1. Analyzing paragraph logic patterns (subject repetition, length uniformity, etc.)
2. Restructuring paragraphs using various strategies (ANI, subject diversity, etc.)
"""

import json
import logging
from typing import List, Optional, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.analyzer.scorer import RiskScorer
from src.core.analyzer.paragraph_logic import (
    ParagraphLogicAnalyzer,
    analyze_paragraph_logic_framework
)
from src.prompts.paragraph_logic import (
    get_paragraph_logic_prompt,
    STRATEGY_DESCRIPTIONS,
)
from src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Global instances for reuse
# 全局实例以便重用
_scorer = RiskScorer()
_analyzer = ParagraphLogicAnalyzer()


# =============================================================================
# Request/Response Models
# 请求/响应模型
# =============================================================================

class ParagraphAnalysisRequest(BaseModel):
    """Request model for paragraph analysis"""
    paragraph: str = Field(..., description="The paragraph text to analyze")
    tone_level: int = Field(4, ge=0, le=10, description="Target tone level (0=formal, 10=casual)")


class LogicIssueResponse(BaseModel):
    """Response model for a single logic issue"""
    type: str
    description: str
    description_zh: str
    severity: str
    position: List[int]
    suggestion: str
    suggestion_zh: str
    details: dict = Field(default_factory=dict)


class ParagraphAnalysisResponse(BaseModel):
    """Response model for paragraph analysis"""
    issues: List[LogicIssueResponse]
    has_subject_repetition: bool
    has_uniform_length: bool
    has_linear_structure: bool
    has_first_person_overuse: bool
    subject_diversity_score: float
    length_variation_cv: float
    logic_structure: str
    first_person_ratio: float
    connector_density: float
    paragraph_risk_adjustment: int
    sentence_count: int
    sentences: List[str]


class ParagraphRestructureRequest(BaseModel):
    """Request model for paragraph restructuring"""
    paragraph: str = Field(..., description="The paragraph text to restructure")
    strategy: Literal["ani", "subject_diversity", "implicit_connector", "rhythm", "citation_entanglement", "document_aware", "sentence_fusion", "all"] = Field(
        ..., description="Restructuring strategy to apply"
    )
    tone_level: int = Field(4, ge=0, le=10, description="Target tone level")
    detected_issues: Optional[List[dict]] = Field(
        None, description="Pre-detected issues from analysis"
    )
    # Strategy-specific parameters
    # 策略特定参数
    repeated_subject: Optional[str] = Field(None, description="For subject_diversity: the repeated subject")
    subject_count: Optional[int] = Field(None, description="For subject_diversity: count of repetitions")
    connectors_found: Optional[List[dict]] = Field(None, description="For implicit_connector: detected connectors")
    lengths: Optional[List[int]] = Field(None, description="For rhythm: current sentence lengths")
    cv: Optional[float] = Field(None, description="For rhythm: coefficient of variation")
    citations_found: Optional[List[dict]] = Field(None, description="For citation_entanglement: detected citations")
    # Document-aware parameters
    # 全篇感知参数
    paragraph_index: Optional[int] = Field(None, description="For document_aware: 0-based index of paragraph in document")
    total_paragraphs: Optional[int] = Field(None, description="For document_aware: total number of paragraphs in document")


class RestructureChange(BaseModel):
    """Model for a single restructuring change"""
    type: str
    description: str
    original: Optional[str] = None
    result: Optional[str] = None


class ParagraphRestructureResponse(BaseModel):
    """Response model for paragraph restructuring"""
    original: str
    restructured: str
    strategy: str
    strategy_name: str
    strategy_name_zh: str
    changes: List[RestructureChange]
    explanation: str
    explanation_zh: str
    # Metrics for comparison
    # 用于比较的指标
    original_risk_adjustment: int
    new_risk_adjustment: int
    improvement: int


class StrategyInfoResponse(BaseModel):
    """Response model for strategy information"""
    strategies: List[dict]


# =============================================================================
# API Endpoints
# API端点
# =============================================================================

@router.get("/strategies", response_model=StrategyInfoResponse)
async def get_available_strategies():
    """
    Get available restructuring strategies
    获取可用的重组策略
    """
    strategies = [
        {
            "key": key,
            "name": info["name"],
            "name_zh": info["name_zh"],
            "description": info["description"],
            "description_zh": info["description_zh"]
        }
        for key, info in STRATEGY_DESCRIPTIONS.items()
    ]

    return StrategyInfoResponse(strategies=strategies)


@router.post("/analyze", response_model=ParagraphAnalysisResponse)
async def analyze_paragraph_logic(request: ParagraphAnalysisRequest):
    """
    Analyze paragraph for logic issues
    分析段落的逻辑问题

    Detects:
    - Subject repetition (AI pattern)
    - Uniform sentence lengths (AI pattern)
    - Linear/additive structure (AI pattern)
    - First-person overuse
    - Explicit connector stacking
    """
    paragraph = request.paragraph.strip()

    if not paragraph:
        raise HTTPException(status_code=400, detail="Paragraph text is required")

    # Split paragraph into sentences
    # 将段落分割为句子
    sentences = _split_into_sentences(paragraph)

    if len(sentences) < 2:
        return ParagraphAnalysisResponse(
            issues=[],
            has_subject_repetition=False,
            has_uniform_length=False,
            has_linear_structure=False,
            has_first_person_overuse=False,
            subject_diversity_score=1.0,
            length_variation_cv=0.5,
            logic_structure="insufficient",
            first_person_ratio=0.0,
            connector_density=0.0,
            paragraph_risk_adjustment=0,
            sentence_count=len(sentences),
            sentences=sentences
        )

    # Analyze using scorer method
    # 使用评分器方法分析
    result = _scorer.analyze_paragraph_logic(sentences, request.tone_level)

    # Convert issues to response format
    # 将问题转换为响应格式
    issues = [
        LogicIssueResponse(
            type=i["type"],
            description=i["description"],
            description_zh=i["description_zh"],
            severity=i["severity"],
            position=i["position"],
            suggestion=i["suggestion"],
            suggestion_zh=i["suggestion_zh"],
            details=i.get("details", {})
        )
        for i in result.get("issues", [])
    ]

    return ParagraphAnalysisResponse(
        issues=issues,
        has_subject_repetition=result.get("has_subject_repetition", False),
        has_uniform_length=result.get("has_uniform_length", False),
        has_linear_structure=result.get("has_linear_structure", False),
        has_first_person_overuse=result.get("has_first_person_overuse", False),
        subject_diversity_score=result.get("subject_diversity_score", 1.0),
        length_variation_cv=result.get("length_variation_cv", 0.5),
        logic_structure=result.get("logic_structure", "unknown"),
        first_person_ratio=result.get("first_person_ratio", 0.0),
        connector_density=result.get("connector_density", 0.0),
        paragraph_risk_adjustment=result.get("paragraph_risk_adjustment", 0),
        sentence_count=len(sentences),
        sentences=sentences
    )


@router.post("/restructure", response_model=ParagraphRestructureResponse)
async def restructure_paragraph(request: ParagraphRestructureRequest):
    """
    Restructure paragraph using specified strategy
    使用指定策略重组段落

    Strategies:
    - ani: Assertion-Nuance-Implication structure
    - subject_diversity: Vary sentence subjects
    - implicit_connector: Replace explicit connectors with semantic flow
    - rhythm: Logic-driven sentence length variation (逻辑关系驱动的句长规划)
    - citation_entanglement: Transform citations to break AI pattern
    - document_aware: Position-aware restructuring (全篇感知重组)
    - all: Apply all relevant strategies
    """
    paragraph = request.paragraph.strip()

    if not paragraph:
        raise HTTPException(status_code=400, detail="Paragraph text is required")

    # Split into sentences for analysis
    # 分割为句子以便分析
    sentences = _split_into_sentences(paragraph)

    # Get original risk adjustment
    # 获取原始风险调整值
    original_analysis = _scorer.analyze_paragraph_logic(sentences, request.tone_level)
    original_risk = original_analysis.get("paragraph_risk_adjustment", 0)

    # Build prompt based on strategy
    # 根据策略构建Prompt
    try:
        prompt_kwargs = {
            "tone_level": request.tone_level,
        }

        if request.strategy == "ani":
            prompt_kwargs["detected_issues"] = request.detected_issues or original_analysis.get("issues", [])
        elif request.strategy == "subject_diversity":
            # Find repeated subject from analysis if not provided
            # 如果未提供，从分析中找到重复主语
            if request.repeated_subject:
                prompt_kwargs["repeated_subject"] = request.repeated_subject
                prompt_kwargs["count"] = request.subject_count or 3
                prompt_kwargs["total"] = len(sentences)
            else:
                # Extract from issues
                # 从问题中提取
                for issue in original_analysis.get("issues", []):
                    if issue.get("type") == "subject_repetition":
                        details = issue.get("details", {})
                        prompt_kwargs["repeated_subject"] = details.get("subject", "unknown")
                        prompt_kwargs["count"] = details.get("count", 3)
                        prompt_kwargs["total"] = len(sentences)
                        prompt_kwargs["positions"] = details.get("positions")
                        break
                else:
                    prompt_kwargs["repeated_subject"] = "the subject"
                    prompt_kwargs["count"] = 3
                    prompt_kwargs["total"] = len(sentences)
        elif request.strategy == "implicit_connector":
            if request.connectors_found:
                prompt_kwargs["connectors_found"] = request.connectors_found
            else:
                # Extract from issues
                # 从问题中提取
                for issue in original_analysis.get("issues", []):
                    if issue.get("type") in ["linear_structure", "connector_overuse"]:
                        details = issue.get("details", {})
                        prompt_kwargs["connectors_found"] = details.get("connectors", [])
                        break
                else:
                    prompt_kwargs["connectors_found"] = []
        elif request.strategy == "rhythm":
            if request.lengths:
                prompt_kwargs["lengths"] = request.lengths
                prompt_kwargs["cv"] = request.cv or 0.2
            else:
                # Calculate lengths
                # 计算长度
                lengths = [len(s.split()) for s in sentences]
                prompt_kwargs["lengths"] = lengths
                prompt_kwargs["cv"] = original_analysis.get("length_variation_cv", 0.2)
        elif request.strategy == "citation_entanglement":
            if request.citations_found:
                prompt_kwargs["citations_found"] = request.citations_found
            else:
                # Extract citations from analysis
                # 从分析中提取引用
                citations = _analyzer.get_citations_for_entanglement(sentences)
                prompt_kwargs["citations_found"] = citations
        elif request.strategy == "document_aware":
            # Document-aware restructuring based on paragraph position
            # 基于段落位置的全篇感知重组
            prompt_kwargs["paragraph_index"] = request.paragraph_index or 0
            prompt_kwargs["total_paragraphs"] = request.total_paragraphs or 1
            prompt_kwargs["detected_issues"] = request.detected_issues or original_analysis.get("issues", [])
        elif request.strategy == "sentence_fusion":
            # Sentence fusion - LLM autonomously judges semantic relationships
            # 句子融合 - LLM自主判断语义关系
            # Only needs tone_level, already set in prompt_kwargs
            pass
        elif request.strategy == "all":
            prompt_kwargs["detected_issues"] = request.detected_issues or original_analysis.get("issues", [])

        prompt = get_paragraph_logic_prompt(
            strategy=request.strategy,
            paragraph=paragraph,
            **prompt_kwargs
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Call LLM to restructure
    # 调用LLM进行重组
    try:
        restructured, changes, explanation, explanation_zh = await _call_llm_for_restructure(
            prompt, request.strategy
        )
    except Exception as e:
        logger.error(f"LLM restructuring failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Restructuring failed: {str(e)}"
        )

    # Calculate new risk adjustment
    # 计算新的风险调整值
    new_sentences = _split_into_sentences(restructured)
    new_analysis = _scorer.analyze_paragraph_logic(new_sentences, request.tone_level)
    new_risk = new_analysis.get("paragraph_risk_adjustment", 0)

    # Get strategy info
    # 获取策略信息
    strategy_info = STRATEGY_DESCRIPTIONS.get(request.strategy, {})

    return ParagraphRestructureResponse(
        original=paragraph,
        restructured=restructured,
        strategy=request.strategy,
        strategy_name=strategy_info.get("name", request.strategy),
        strategy_name_zh=strategy_info.get("name_zh", request.strategy),
        changes=changes,
        explanation=explanation,
        explanation_zh=explanation_zh,
        original_risk_adjustment=original_risk,
        new_risk_adjustment=new_risk,
        improvement=original_risk - new_risk
    )


# =============================================================================
# Helper Functions
# 辅助函数
# =============================================================================

def _split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences (simple implementation)
    将文本分割为句子（简单实现）
    """
    import re

    # Handle common abbreviations
    # 处理常见缩写
    text = text.replace("Dr.", "Dr").replace("Mr.", "Mr").replace("Mrs.", "Mrs")
    text = text.replace("Prof.", "Prof").replace("vs.", "vs").replace("etc.", "etc")
    text = text.replace("e.g.", "eg").replace("i.e.", "ie")

    # Split on sentence-ending punctuation
    # 按句末标点分割
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Clean up and filter
    # 清理和过滤
    sentences = [s.strip() for s in sentences if s.strip()]

    # Restore abbreviations
    # 恢复缩写
    for i, s in enumerate(sentences):
        sentences[i] = s.replace("Dr", "Dr.").replace("Mr", "Mr.").replace("Mrs", "Mrs.")
        sentences[i] = sentences[i].replace("Prof", "Prof.").replace("vs", "vs.").replace("etc", "etc.")
        sentences[i] = sentences[i].replace("eg", "e.g.").replace("ie", "i.e.")

    return sentences


async def _call_llm_for_restructure(
    prompt: str,
    strategy: str
) -> tuple:
    """
    Call LLM to restructure paragraph
    调用LLM重组段落

    Returns:
        (restructured_text, changes_list, explanation, explanation_zh)
    """
    import httpx

    content = None

    try:
        if settings.llm_provider == "dashscope" and settings.dashscope_api_key:
            # Call DashScope (阿里云灵积) API - Qwen models
            # 调用阿里云灵积 API - 通义千问模型
            async with httpx.AsyncClient(
                base_url=settings.dashscope_base_url,
                headers={
                    "Authorization": f"Bearer {settings.dashscope_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=120.0,
                trust_env=False
            ) as client:
                response = await client.post("/chat/completions", json={
                    "model": settings.dashscope_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.4
                })
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

        elif settings.llm_provider == "volcengine" and settings.volcengine_api_key:
            # Call Volcengine (火山引擎) DeepSeek API - faster
            # 调用火山引擎 DeepSeek API - 更快
            async with httpx.AsyncClient(
                base_url=settings.volcengine_base_url,
                headers={
                    "Authorization": f"Bearer {settings.volcengine_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=120.0,
                trust_env=False
            ) as client:
                response = await client.post("/chat/completions", json={
                    "model": settings.volcengine_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.4
                })
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

        elif settings.llm_provider == "gemini" and settings.gemini_api_key:
            # Call Gemini API
            # 调用Gemini API
            from google import genai
            client = genai.Client(api_key=settings.gemini_api_key)
            response = await client.aio.models.generate_content(
                model=settings.llm_model,
                contents=prompt,
                config={
                    "max_output_tokens": 2000,
                    "temperature": 0.4
                }
            )
            content = response.text.strip()

        elif settings.llm_provider == "deepseek" or settings.deepseek_api_key:
            # Call DeepSeek API (official - slower)
            # 调用DeepSeek API（官方 - 较慢）
            async with httpx.AsyncClient(
                base_url=settings.deepseek_base_url,
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=120.0,
                trust_env=False
            ) as client:
                response = await client.post("/chat/completions", json={
                    "model": settings.llm_model if settings.llm_provider == "deepseek" else "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.4
                })
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

        else:
            raise Exception("No LLM configured. Set VOLCENGINE_API_KEY or other LLM API key.")

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise

    # Parse JSON response
    # 解析JSON响应
    if content:
        # Clean potential markdown code blocks
        # 清理可能的markdown代码块
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, content: {content[:500]}")
            raise Exception(f"Failed to parse LLM response: {e}")

        # Extract fields based on strategy
        # 根据策略提取字段
        restructured = result.get("restructured", "")

        # Build changes list
        # 构建变更列表
        changes = []
        if strategy == "ani":
            changes_raw = result.get("changes_made", [])
            for c in changes_raw:
                if isinstance(c, dict):
                    changes.append(RestructureChange(
                        type=c.get("type", "change"),
                        description=c.get("description", str(c)),
                        original=c.get("original"),
                        result=c.get("result")
                    ))
                else:
                    changes.append(RestructureChange(type="change", description=str(c)))
        elif strategy == "subject_diversity":
            for t in result.get("transformations", []):
                changes.append(RestructureChange(
                    type="subject_transform",
                    description=f"{t.get('from', '')} → {t.get('to', '')}",
                    original=t.get("from"),
                    result=t.get("to")
                ))
        elif strategy == "implicit_connector":
            for r in result.get("connector_replacements", []):
                changes.append(RestructureChange(
                    type="connector_replace",
                    description=f"Strategy: {r.get('strategy', 'unknown')}",
                    original=r.get("original"),
                    result=r.get("result")
                ))
        elif strategy == "rhythm":
            for t in result.get("techniques_used", []):
                changes.append(RestructureChange(
                    type=t.get("type", "rhythm"),
                    description=t.get("description", "")
                ))
        elif strategy == "citation_entanglement":
            for t in result.get("transformations", []):
                changes.append(RestructureChange(
                    type="citation_transform",
                    description=f"Strategy: {t.get('strategy', 'narrative')}",
                    original=t.get("original"),
                    result=t.get("new_form")
                ))
        elif strategy == "sentence_fusion":
            # Parse fusion_applied array
            # 解析融合应用数组
            for f in result.get("fusion_applied", []):
                changes.append(RestructureChange(
                    type=f.get("type", "fusion"),
                    description=f.get("result", f.get("content", "")),
                    original=str(f.get("original_sentences", [])),
                    result=f.get("result", f.get("content", ""))
                ))
            # Also include semantic analysis summary
            # 也包含语义分析摘要
            for sa in result.get("semantic_analysis", [])[:3]:  # First 3 only
                if sa.get("decision") == "merge":
                    changes.append(RestructureChange(
                        type="semantic_merge",
                        description=f"{sa.get('relationship', 'unknown')}: {sa.get('reason', '')}"
                    ))
        elif strategy == "all":
            for c in result.get("changes_summary", []):
                changes.append(RestructureChange(
                    type=c.get("category", "change"),
                    description=c.get("change", "")
                ))

        explanation = result.get("explanation", "")
        explanation_zh = result.get("explanation_zh", "")

        return (restructured, changes, explanation, explanation_zh)

    raise Exception("Empty LLM response")


# =============================================================================
# Paragraph Logic Framework Analysis (Step 2 Enhancement)
# 段落逻辑框架分析（Step 2 增强）
# =============================================================================

class SentenceRoleItem(BaseModel):
    """Response model for a single sentence role"""
    index: int
    role: str
    roleZh: str
    confidence: float
    brief: str


class LogicFrameworkItem(BaseModel):
    """Response model for logic framework detection"""
    pattern: str
    patternZh: str
    isAiLike: bool
    riskLevel: str
    description: str
    descriptionZh: str


class BurstinessAnalysisItem(BaseModel):
    """Response model for burstiness analysis"""
    sentenceLengths: List[int]
    meanLength: float
    stdDev: float
    cv: float
    burstinessLevel: str
    burstinessZh: str
    hasDramaticVariation: bool
    longestSentence: dict
    shortestSentence: dict


class ImprovementSuggestionItem(BaseModel):
    """Response model for improvement suggestion"""
    type: str
    suggestion: str = Field(default="")
    suggestionZh: str = Field(alias="suggestion_zh", default="")
    priority: int = Field(default=3)
    example: Optional[str] = None

    class Config:
        populate_by_name = True


class ParagraphLogicFrameworkRequest(BaseModel):
    """Request model for paragraph logic framework analysis"""
    paragraph: str = Field(..., description="The paragraph text to analyze")
    paragraphPosition: Optional[str] = Field(None, description="Position in document e.g. '1(2)'")


class ParagraphLogicFrameworkResponse(BaseModel):
    """Response model for paragraph logic framework analysis (Step 2 enhancement)"""
    sentenceRoles: List[SentenceRoleItem]
    roleDistribution: dict
    logicFramework: LogicFrameworkItem
    burstinessAnalysis: BurstinessAnalysisItem
    missingElements: dict
    improvementSuggestions: List[dict]
    overallAssessment: dict
    basicAnalysis: dict
    sentences: List[str]


@router.post("/analyze-logic-framework", response_model=ParagraphLogicFrameworkResponse)
async def analyze_paragraph_logic_framework_endpoint(request: ParagraphLogicFrameworkRequest):
    """
    Analyze paragraph logic framework with sentence role detection (Step 2 Enhancement)
    分析段落逻辑框架和句子角色检测（Step 2 增强）

    This endpoint provides:
    此端点提供：
    - Sentence role analysis (论点/证据/分析/批判/让步/综合等)
    - Logic framework pattern detection (linear/dynamic)
    - Burstiness analysis (sentence length variation)
    - Missing element identification
    - Improvement suggestions

    Used in Step 2 to help users understand and improve paragraph structure.
    在 Step 2 中使用，帮助用户理解和改进段落结构。
    """
    paragraph = request.paragraph.strip()

    if not paragraph:
        raise HTTPException(status_code=400, detail="Paragraph text is required")

    # Split paragraph into sentences
    # 将段落分割为句子
    sentences = _split_into_sentences(paragraph)

    if len(sentences) < 2:
        # Return minimal result for very short paragraphs
        # 为非常短的段落返回最小结果
        return ParagraphLogicFrameworkResponse(
            sentenceRoles=[
                SentenceRoleItem(
                    index=0,
                    role="UNKNOWN",
                    roleZh="未知",
                    confidence=0.0,
                    brief="Paragraph too short"
                )
            ] if sentences else [],
            roleDistribution={},
            logicFramework=LogicFrameworkItem(
                pattern="INSUFFICIENT_DATA",
                patternZh="数据不足",
                isAiLike=False,
                riskLevel="unknown",
                description="Paragraph too short for framework analysis",
                descriptionZh="段落过短，无法进行框架分析"
            ),
            burstinessAnalysis=BurstinessAnalysisItem(
                sentenceLengths=[len(s.split()) for s in sentences],
                meanLength=0.0,
                stdDev=0.0,
                cv=0.0,
                burstinessLevel="unknown",
                burstinessZh="未知",
                hasDramaticVariation=False,
                longestSentence={"index": 0, "length": 0},
                shortestSentence={"index": 0, "length": 0}
            ),
            missingElements={"roles": [], "description": "", "descriptionZh": ""},
            improvementSuggestions=[],
            overallAssessment={
                "aiRiskScore": 0,
                "mainIssues": [],
                "summary": "Paragraph too short",
                "summaryZh": "段落过短"
            },
            basicAnalysis={},
            sentences=sentences
        )

    try:
        # Call the comprehensive analysis function
        # 调用综合分析函数
        result = await analyze_paragraph_logic_framework(
            paragraph=paragraph,
            sentences=sentences,
            paragraph_position=request.paragraphPosition
        )

        # Convert to response format
        # 转换为响应格式
        result_dict = result.to_dict()

        return ParagraphLogicFrameworkResponse(
            sentenceRoles=[
                SentenceRoleItem(
                    index=sr["index"],
                    role=sr["role"],
                    roleZh=sr["roleZh"],
                    confidence=sr["confidence"],
                    brief=sr["brief"]
                )
                for sr in result_dict["sentenceRoles"]
            ],
            roleDistribution=result_dict["roleDistribution"],
            logicFramework=LogicFrameworkItem(
                pattern=result_dict["logicFramework"]["pattern"],
                patternZh=result_dict["logicFramework"]["patternZh"],
                isAiLike=result_dict["logicFramework"]["isAiLike"],
                riskLevel=result_dict["logicFramework"]["riskLevel"],
                description=result_dict["logicFramework"]["description"],
                descriptionZh=result_dict["logicFramework"]["descriptionZh"]
            ),
            burstinessAnalysis=BurstinessAnalysisItem(
                sentenceLengths=result_dict["burstinessAnalysis"]["sentenceLengths"],
                meanLength=result_dict["burstinessAnalysis"]["meanLength"],
                stdDev=result_dict["burstinessAnalysis"]["stdDev"],
                cv=result_dict["burstinessAnalysis"]["cv"],
                burstinessLevel=result_dict["burstinessAnalysis"]["burstinessLevel"],
                burstinessZh=result_dict["burstinessAnalysis"]["burstinessZh"],
                hasDramaticVariation=result_dict["burstinessAnalysis"]["hasDramaticVariation"],
                longestSentence=result_dict["burstinessAnalysis"]["longestSentence"],
                shortestSentence=result_dict["burstinessAnalysis"]["shortestSentence"]
            ),
            missingElements=result_dict["missingElements"],
            improvementSuggestions=result_dict["improvementSuggestions"],
            overallAssessment=result_dict["overallAssessment"],
            basicAnalysis=result_dict["basicAnalysis"],
            sentences=sentences
        )

    except Exception as e:
        logger.error(f"Paragraph logic framework analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
