"""
Structure Guidance API Routes (Level 1 Guided Interaction)
结构指引 API 路由（Level 1 指引式交互）

This module provides endpoints for:
1. Getting categorized structure issue list (lightweight, no LLM)
2. Getting detailed guidance for specific issues (calls LLM on demand)
3. Applying structure fixes
4. Getting paragraph reorder suggestions
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from typing import Optional, Dict, Any, List
import logging
import json
import uuid
import httpx

from src.api.schemas import (
    StructureIssueItem,
    StructureIssueListRequest,
    StructureIssueListResponse,
    IssueGuidanceRequest,
    IssueGuidanceResponse,
    KeyConcepts,
    ApplyStructureFixRequest,
    ApplyStructureFixResponse,
    ReorderSuggestionRequest,
    ReorderSuggestionResponse,
    ReorderChange,
)
from src.prompts.structure_guidance import (
    STRUCTURE_ISSUE_GUIDANCE_PROMPT,
    ISSUE_SPECIFIC_PROMPTS,
    STRUCTURE_REORDER_PROMPT,
    REFERENCEABLE_ISSUES,
    ADVICE_ONLY_ISSUES,
    can_generate_reference,
    get_issue_specific_prompt,
)
from src.db.database import get_db
from src.db.models import Document
from src.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Issue Type Metadata
# 问题类型元数据
# =============================================================================

ISSUE_TYPE_METADATA = {
    "linear_flow": {
        "category": "structure",
        "severity": "high",
        "title_zh": "线性流程过于明显",
        "title_en": "Linear Flow Pattern Detected",
        "brief_zh": "文档遵循可预测的 A→B→C→D 线性结构，这是AI写作的典型特征",
        "can_reference": True,
    },
    "uniform_length": {
        "category": "structure",
        "severity": "medium",
        "title_zh": "段落长度分布均匀",
        "title_en": "Uniform Paragraph Lengths",
        "brief_zh": "段落长度过于一致，人类写作通常有更大的长度变化",
        "can_reference": False,
    },
    "predictable_structure": {
        "category": "structure",
        "severity": "medium",
        "title_zh": "结构可预测性高",
        "title_en": "Predictable Structure",
        "brief_zh": "文档结构遵循公式化模式，缺乏叙事变化",
        "can_reference": True,
    },
    "explicit_connector": {
        "category": "transition",
        "severity": "high",
        "title_zh": "使用显性连接词",
        "title_en": "Explicit Connector Word",
        "brief_zh": "段首使用 AI 高频连接词，建议改用语义回声",
        "can_reference": True,
    },
    "missing_semantic_echo": {
        "category": "transition",
        "severity": "medium",
        "title_zh": "缺少语义回声",
        "title_en": "Missing Semantic Echo",
        "brief_zh": "段落间缺乏语义连接，仅靠结构衔接",
        "can_reference": True,
    },
    "logic_gap": {
        "category": "transition",
        "severity": "medium",
        "title_zh": "逻辑断裂",
        "title_en": "Logic Gap",
        "brief_zh": "段落间存在逻辑跳跃，缺乏自然过渡",
        "can_reference": False,
    },
    "paragraph_too_short": {
        "category": "transition",
        "severity": "low",
        "title_zh": "段落过短",
        "title_en": "Paragraph Too Short",
        "brief_zh": "段落词数明显少于相邻段落，建议扩展或合并",
        "can_reference": False,
    },
    "paragraph_too_long": {
        "category": "transition",
        "severity": "low",
        "title_zh": "段落过长",
        "title_en": "Paragraph Too Long",
        "brief_zh": "段落词数过多，建议拆分或精简",
        "can_reference": False,
    },
    "formulaic_opening": {
        "category": "transition",
        "severity": "medium",
        "title_zh": "公式化开头",
        "title_en": "Formulaic Opening",
        "brief_zh": "段落开头使用公式化表达，如 'In this section...'",
        "can_reference": True,
    },
    "weak_transition": {
        "category": "transition",
        "severity": "low",
        "title_zh": "过渡薄弱",
        "title_en": "Weak Transition",
        "brief_zh": "段落过渡不够自然，可以加强衔接",
        "can_reference": True,
    },
}


# =============================================================================
# Endpoint: Get Structure Issue List
# 端点：获取结构问题列表
# =============================================================================

@router.post("/issues", response_model=StructureIssueListResponse)
async def get_structure_issues(
    request: StructureIssueListRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get categorized list of structure issues for a document
    获取文档的分类结构问题列表

    This endpoint performs lightweight analysis without calling LLM.
    Detailed guidance is fetched separately when user expands an issue.

    Args:
        request: Structure issue list request 结构问题列表请求
        db: Database session 数据库会话

    Returns:
        StructureIssueListResponse with categorized issues 包含分类问题的响应
    """
    try:
        # Get document
        # 获取文档
        document = await db.get(Document, request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get cached structure analysis or perform new analysis
        # 获取缓存的结构分析或执行新分析
        if document.structure_analysis_cache:
            analysis = document.structure_analysis_cache
        else:
            # Need to analyze first
            # 需要先分析
            from src.core.analyzer.smart_structure import SmartStructureAnalyzer
            smart_analyzer = SmartStructureAnalyzer()
            analysis = await smart_analyzer.analyze(document.original_text)

            # Cache the result to SQLite
            # 缓存结果到 SQLite
            document.structure_analysis_cache = analysis
            flag_modified(document, 'structure_analysis_cache')
            await db.commit()

        # Extract issues from analysis
        # 从分析中提取问题
        structure_issues = []
        transition_issues = []

        # Process score breakdown to detect structure-level issues
        # 处理分数分解以检测结构级问题
        score_breakdown = analysis.get("score_breakdown", {})

        # Linear flow issue
        # 线性流程问题
        if score_breakdown.get("linear_flow", 0) > 0:
            structure_issues.append(_create_issue_item(
                issue_type="linear_flow",
                affected_positions=["全文"],
                affected_text_preview="文档整体结构"
            ))

        # Uniform length issue
        # 均匀长度问题
        if score_breakdown.get("uniform_length", 0) > 0:
            structure_issues.append(_create_issue_item(
                issue_type="uniform_length",
                affected_positions=["全文"],
                affected_text_preview="段落长度分布"
            ))

        # Predictable structure issue
        # 可预测结构问题
        if score_breakdown.get("predictable_order", 0) > 0:
            structure_issues.append(_create_issue_item(
                issue_type="predictable_structure",
                affected_positions=["全文"],
                affected_text_preview="文档结构顺序"
            ))

        # Process explicit connectors
        # 处理显性连接词
        for connector in analysis.get("explicit_connectors", []):
            transition_issues.append(_create_issue_item(
                issue_type="explicit_connector",
                affected_positions=[connector.get("position", "")],
                affected_text_preview=f'"{connector.get("word", "")}" 开头',
                connector_word=connector.get("word")
            ))

        # Process logic breaks
        # 处理逻辑断裂
        for lb in analysis.get("logic_breaks", []):
            transition_type = lb.get("transition_type", "")
            if transition_type == "glue_word_only":
                # This is actually an explicit connector issue in disguise
                # 这实际上是变相的显性连接词问题
                pass  # Already handled above
            elif transition_type == "abrupt":
                transition_issues.append(_create_issue_item(
                    issue_type="logic_gap",
                    affected_positions=[lb.get("from_position", ""), lb.get("to_position", "")],
                    affected_text_preview=lb.get("issue_zh", lb.get("issue", ""))[:100]
                ))

        # Process paragraphs for length issues
        # 处理段落长度问题
        paragraphs = []
        for section in analysis.get("sections", []):
            for p in section.get("paragraphs", []):
                if p.get("word_count", 0) > 0:
                    paragraphs.append(p)

        if len(paragraphs) >= 3:
            avg_length = sum(p.get("word_count", 0) for p in paragraphs) / len(paragraphs)
            for p in paragraphs:
                wc = p.get("word_count", 0)
                position = p.get("position", "")

                # Check for too short (less than 50% of average)
                # 检查过短（小于平均值的50%）
                if wc < avg_length * 0.5 and wc < 80:
                    if request.include_low_severity or wc < avg_length * 0.3:
                        transition_issues.append(_create_issue_item(
                            issue_type="paragraph_too_short",
                            affected_positions=[position],
                            affected_text_preview=p.get("summary_zh", p.get("summary", ""))[:100],
                            word_count=wc,
                            neighbor_avg=int(avg_length)
                        ))

                # Check for too long (more than 200% of average)
                # 检查过长（超过平均值的200%）
                elif wc > avg_length * 2 and wc > 250:
                    if request.include_low_severity:
                        transition_issues.append(_create_issue_item(
                            issue_type="paragraph_too_long",
                            affected_positions=[position],
                            affected_text_preview=p.get("summary_zh", p.get("summary", ""))[:100],
                            word_count=wc,
                            neighbor_avg=int(avg_length)
                        ))

        # Calculate counts
        # 计算数量
        all_issues = structure_issues + transition_issues
        high_count = sum(1 for i in all_issues if i.severity == "high")
        medium_count = sum(1 for i in all_issues if i.severity == "medium")
        low_count = sum(1 for i in all_issues if i.severity == "low")

        return StructureIssueListResponse(
            structure_issues=structure_issues,
            transition_issues=transition_issues,
            total_issues=len(all_issues),
            high_severity_count=high_count,
            medium_severity_count=medium_count,
            low_severity_count=low_count,
            document_id=request.document_id,
            structure_score=analysis.get("structure_score", 0),
            risk_level=analysis.get("risk_level", "low")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get structure issues error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _create_issue_item(
    issue_type: str,
    affected_positions: List[str],
    affected_text_preview: str = "",
    connector_word: str = None,
    word_count: int = None,
    neighbor_avg: int = None
) -> StructureIssueItem:
    """
    Create a structure issue item from type and context
    从类型和上下文创建结构问题项
    """
    metadata = ISSUE_TYPE_METADATA.get(issue_type, {})

    # Generate unique ID
    # 生成唯一ID
    issue_id = f"{issue_type}_{uuid.uuid4().hex[:8]}"

    # Customize title for specific issues
    # 为特定问题定制标题
    title_zh = metadata.get("title_zh", issue_type)
    if issue_type == "explicit_connector" and connector_word:
        title_zh = f'{affected_positions[0]} 使用显性连接词 "{connector_word}"'
    elif issue_type == "paragraph_too_short" and word_count:
        title_zh = f'{affected_positions[0]} 段落过短（{word_count}词）'
    elif issue_type == "paragraph_too_long" and word_count:
        title_zh = f'{affected_positions[0]} 段落过长（{word_count}词）'

    return StructureIssueItem(
        id=issue_id,
        type=issue_type,
        category=metadata.get("category", "transition"),
        severity=metadata.get("severity", "medium"),
        title_zh=title_zh,
        title_en=metadata.get("title_en", issue_type),
        brief_zh=metadata.get("brief_zh", ""),
        affected_positions=affected_positions,
        affected_text_preview=affected_text_preview,
        can_generate_reference=metadata.get("can_reference", False),
        status="pending",
        connector_word=connector_word,
        word_count=word_count,
        neighbor_avg=neighbor_avg
    )


# =============================================================================
# Endpoint: Get Issue Guidance (Calls LLM)
# 端点：获取问题指引（调用 LLM）
# =============================================================================

@router.post("/guidance", response_model=IssueGuidanceResponse)
async def get_issue_guidance(
    request: IssueGuidanceRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed guidance for a specific issue (calls LLM)
    获取特定问题的详细指引（调用 LLM）

    This endpoint is called when user expands an issue card.
    It generates detailed guidance and optionally a reference version.

    Args:
        request: Issue guidance request 问题指引请求
        db: Database session 数据库会话

    Returns:
        IssueGuidanceResponse with detailed guidance 包含详细指引的响应
    """
    try:
        # Get document for context
        # 获取文档上下文
        document = await db.get(Document, request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get affected text and context from document
        # 从文档获取受影响的文本和上下文
        affected_text = request.affected_text or ""
        prev_paragraph = request.prev_paragraph or ""
        next_paragraph = request.next_paragraph or ""
        core_thesis = ""

        # Try to extract from cached analysis
        # 尝试从缓存的分析中提取
        if document.structure_analysis_cache:
            analysis = document.structure_analysis_cache
            core_thesis = analysis.get("core_thesis", "")

            # Collect all paragraphs
            # 收集所有段落
            paragraphs = []
            for section in analysis.get("sections", []):
                for p in section.get("paragraphs", []):
                    paragraphs.append(p)

            # Find the paragraph by position or provide document overview
            # 按位置查找段落或提供文档概览
            if request.affected_positions and not affected_text:
                target_pos = request.affected_positions[0]

                # For document-level issues (全文), provide overview of all paragraphs
                # 对于文档级问题，提供所有段落的概览
                if target_pos == "全文" and paragraphs:
                    # Build document structure overview
                    # 构建文档结构概览
                    overview_parts = []
                    for i, p in enumerate(paragraphs):
                        pos = p.get("position", f"P{i+1}")
                        summary = p.get("summary_zh", p.get("summary", ""))[:80]
                        word_count = p.get("word_count", 0)
                        overview_parts.append(f"{pos} ({word_count}词): {summary}")
                    affected_text = "【文档结构概览】\n" + "\n".join(overview_parts)

                    # Also provide first and last paragraphs as context
                    # 同时提供首尾段落作为上下文
                    if paragraphs:
                        prev_paragraph = f"首段: {paragraphs[0].get('first_sentence', '')}"
                        next_paragraph = f"末段: {paragraphs[-1].get('last_sentence', '')}"
                else:
                    # Find specific paragraph by position
                    # 按位置查找特定段落
                    for i, p in enumerate(paragraphs):
                        if p.get("position") == target_pos:
                            affected_text = p.get("first_sentence", "") + " ... " + p.get("last_sentence", "")
                            if i > 0:
                                prev_paragraph = paragraphs[i-1].get("first_sentence", "") + " ... " + paragraphs[i-1].get("last_sentence", "")
                            if i < len(paragraphs) - 1:
                                next_paragraph = paragraphs[i+1].get("first_sentence", "") + " ... " + paragraphs[i+1].get("last_sentence", "")
                            break

        # Determine if we can generate reference
        # 确定是否可以生成参考版本
        can_ref = can_generate_reference(request.issue_type)

        # Build context for prompt
        # 构建提示词上下文
        context = {
            "issue_type": request.issue_type,
            "issue_category": ISSUE_TYPE_METADATA.get(request.issue_type, {}).get("category", "transition"),
            "severity": ISSUE_TYPE_METADATA.get(request.issue_type, {}).get("severity", "medium"),
            "issue_description": ISSUE_TYPE_METADATA.get(request.issue_type, {}).get("brief_zh", ""),
            "affected_text": affected_text,
            "position": ", ".join(request.affected_positions) if request.affected_positions else "未知",
            "prev_paragraph": prev_paragraph,
            "next_paragraph": next_paragraph,
            "core_thesis": core_thesis or "未提取",
            "can_generate_reference": str(can_ref),
            "connector_word": request.connector_word or "",
            "prev_key_concepts": "",  # Will be extracted by LLM
        }

        # Get issue-specific prompt addition
        # 获取问题类型专用提示词补充
        specific_prompt = get_issue_specific_prompt(request.issue_type, context)

        # Build full prompt
        # 构建完整提示词
        full_prompt = STRUCTURE_ISSUE_GUIDANCE_PROMPT.format(**context)
        if specific_prompt:
            full_prompt += "\n\n" + specific_prompt

        # Call LLM
        # 调用 LLM
        settings = get_settings()
        llm_response = await _call_llm_for_guidance(full_prompt, settings)

        # Parse response
        # 解析响应
        result = _parse_guidance_response(llm_response)

        return IssueGuidanceResponse(
            issue_id=request.issue_id,
            issue_type=request.issue_type,
            guidance_zh=result.get("guidance_zh", "【问题分析】分析失败\n【改进策略】请稍后重试\n【具体建议】无"),
            guidance_en=result.get("guidance_en", ""),
            reference_version=result.get("reference_version") if can_ref else None,
            reference_explanation_zh=result.get("reference_explanation_zh"),
            why_no_reference=result.get("why_no_reference") if not can_ref else None,
            affected_text=affected_text,
            key_concepts=KeyConcepts(
                from_prev=result.get("key_concepts", {}).get("from_prev", []),
                from_next=result.get("key_concepts", {}).get("from_next", [])
            ),
            confidence=result.get("confidence", 0.8),
            can_generate_reference=can_ref
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get issue guidance error: {e}")
        # Return fallback response
        # 返回后备响应
        return IssueGuidanceResponse(
            issue_id=request.issue_id,
            issue_type=request.issue_type,
            guidance_zh=f"【问题分析】获取指引时发生错误\n【改进策略】请稍后重试或手动处理\n【具体建议】错误信息：{str(e)[:100]}",
            guidance_en="Error fetching guidance. Please retry.",
            affected_text=request.affected_text or "",
            key_concepts=KeyConcepts(),
            confidence=0.0,
            can_generate_reference=False
        )


async def _call_llm_for_guidance(prompt: str, settings) -> str:
    """
    Call LLM API for guidance generation
    调用 LLM API 生成指引
    """
    # Use DashScope (Aliyun)
    # 使用阿里云灵积
    if settings.llm_provider == "dashscope" and settings.dashscope_api_key:
        async with httpx.AsyncClient(
            base_url=settings.dashscope_base_url,
            headers={
                "Authorization": f"Bearer {settings.dashscope_api_key}",
                "Content-Type": "application/json"
            },
            timeout=90.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.dashscope_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
                "temperature": 0.3
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    # Use Volcengine
    # 使用火山引擎
    elif settings.llm_provider == "volcengine" and settings.volcengine_api_key:
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
                "max_tokens": 3000,
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
            timeout=90.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
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
            config={"max_output_tokens": 3000, "temperature": 0.3}
        )
        return response.text

    else:
        raise ValueError("No LLM API configured")


def _parse_guidance_response(response: str) -> dict:
    """
    Parse LLM response to JSON
    解析 LLM 响应为 JSON
    """
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
        # Match JSON object that may span multiple lines
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass

        # Return default
        return {
            "guidance_zh": "【问题分析】无法解析分析结果\n【改进策略】请重试\n【具体建议】建议手动检查此处",
            "guidance_en": "Failed to parse analysis result",
            "reference_version": None,
            "key_concepts": {"from_prev": [], "from_next": []},
            "confidence": 0.5
        }


# =============================================================================
# Endpoint: Apply Structure Fix
# 端点：应用结构修复
# =============================================================================

@router.post("/apply-fix", response_model=ApplyStructureFixResponse)
async def apply_structure_fix(
    request: ApplyStructureFixRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply a structure fix to the document
    应用结构修复到文档

    Args:
        request: Apply fix request 应用修复请求
        db: Database session 数据库会话

    Returns:
        ApplyStructureFixResponse with result 包含结果的响应
    """
    try:
        # Get document
        # 获取文档
        document = await db.get(Document, request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Handle different fix types
        # 处理不同的修复类型
        if request.fix_type == "skip":
            return ApplyStructureFixResponse(
                success=True,
                issue_id=request.issue_id,
                new_status="skipped",
                message="Issue skipped",
                message_zh="已跳过此问题"
            )

        if request.fix_type == "mark_done":
            return ApplyStructureFixResponse(
                success=True,
                issue_id=request.issue_id,
                new_status="fixed",
                message="Issue marked as done",
                message_zh="已标记为已处理"
            )

        if request.fix_type in ["use_reference", "custom"]:
            # For now, just record the fix - actual text replacement
            # would require more complex document manipulation
            # 目前只记录修复 - 实际文本替换需要更复杂的文档操作

            # Store the fix in a fixes cache (could be added to Document model)
            # 将修复存储在修复缓存中（可以添加到 Document 模型）
            updated_text = request.custom_text if request.fix_type == "custom" else None

            return ApplyStructureFixResponse(
                success=True,
                issue_id=request.issue_id,
                new_status="fixed",
                message=f"Fix applied using {request.fix_type}",
                message_zh=f"已应用修复（{'自定义' if request.fix_type == 'custom' else '参考版本'}）",
                updated_text=updated_text
            )

        return ApplyStructureFixResponse(
            success=False,
            issue_id=request.issue_id,
            new_status="pending",
            message=f"Unknown fix type: {request.fix_type}",
            message_zh=f"未知的修复类型：{request.fix_type}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apply structure fix error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Endpoint: Get Reorder Suggestion
# 端点：获取重排建议
# =============================================================================

@router.post("/reorder-suggestion", response_model=ReorderSuggestionResponse)
async def get_reorder_suggestion(
    request: ReorderSuggestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get paragraph reorder suggestion for the document
    获取文档的段落重排建议

    Args:
        request: Reorder suggestion request 重排建议请求
        db: Database session 数据库会话

    Returns:
        ReorderSuggestionResponse with reorder suggestion 包含重排建议的响应
    """
    try:
        # Get document
        # 获取文档
        document = await db.get(Document, request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get cached analysis
        # 获取缓存的分析
        if not document.structure_analysis_cache:
            raise HTTPException(
                status_code=400,
                detail="Document has not been analyzed yet. Please analyze first."
            )

        analysis = document.structure_analysis_cache

        # Build paragraph summaries for prompt
        # 为提示词构建段落摘要
        paragraph_summaries = []
        paragraphs = []
        for section in analysis.get("sections", []):
            for p in section.get("paragraphs", []):
                if p.get("word_count", 0) > 0:
                    paragraphs.append(p)
                    paragraph_summaries.append(
                        f"P{len(paragraphs)}: [{p.get('position', '')}] {p.get('summary_zh', p.get('summary', ''))[:80]}"
                    )

        # Build prompt
        # 构建提示词
        context = {
            "paragraph_summaries": "\n".join(paragraph_summaries),
            "has_linear_flow": str(analysis.get("score_breakdown", {}).get("linear_flow", 0) > 0),
            "has_uniform_length": str(analysis.get("score_breakdown", {}).get("uniform_length", 0) > 0),
            "has_predictable_order": str(analysis.get("score_breakdown", {}).get("predictable_order", 0) > 0),
            "structure_score": analysis.get("structure_score", 0),
            "core_thesis": analysis.get("core_thesis", "未提取"),
        }

        prompt = STRUCTURE_REORDER_PROMPT.format(**context)

        # Call LLM
        # 调用 LLM
        settings = get_settings()
        llm_response = await _call_llm_for_guidance(prompt, settings)

        # Parse response
        # 解析响应
        result = _parse_guidance_response(llm_response)

        # Build changes list
        # 构建变更列表
        changes = []
        for change in result.get("changes", []):
            changes.append(ReorderChange(
                action=change.get("action", "move"),
                paragraph_index=change.get("paragraph_index", 0),
                from_position=change.get("from_position", 0),
                to_position=change.get("to_position", 0),
                paragraph_summary=change.get("paragraph_summary", ""),
                reason_zh=change.get("reason_zh", ""),
                reason_en=change.get("reason_en", "")
            ))

        return ReorderSuggestionResponse(
            current_order=result.get("current_order", list(range(len(paragraphs)))),
            suggested_order=result.get("suggested_order", list(range(len(paragraphs)))),
            changes=changes,
            overall_guidance_zh=result.get("overall_guidance_zh", ""),
            warnings_zh=result.get("warnings_zh", []),
            preview_flow_zh=result.get("preview_flow_zh", ""),
            estimated_improvement=result.get("estimated_improvement", 0),
            confidence=result.get("confidence", 0.8)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get reorder suggestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
