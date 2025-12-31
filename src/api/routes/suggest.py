"""
Suggestion generation API routes
建议生成API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.schemas import (
    SuggestRequest,
    SuggestResponse,
    Suggestion,
    SuggestionSource,
    ChangeDetail,
    ValidationResult,
    CustomInputRequest,
    RiskLevel,
    SentenceAnalysisRequest,
    SentenceAnalysisResponse,
    GrammarStructure,
    GrammarModifier,
    ClauseInfo,
    PronounReference,
    AIWordSuggestion,
    RewriteSuggestion,
)
from src.core.suggester.llm_track import LLMTrack
from src.core.suggester.rule_track import RuleTrack
from src.core.validator.semantic import SemanticValidator
from src.core.validator.quality_gate import QualityGate
from src.core.analyzer.scorer import RiskScorer

router = APIRouter()

# Global scorer instance for reuse
# 全局评分器实例以便重用
_scorer = RiskScorer()


@router.post("/", response_model=SuggestResponse)
async def get_suggestions(
    request: SuggestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get humanization suggestions for a sentence
    获取句子的人源化建议
    """
    # Initialize suggestion tracks
    # 初始化建议轨道
    llm_track = LLMTrack(colloquialism_level=request.colloquialism_level)
    rule_track = RuleTrack(colloquialism_level=request.colloquialism_level)

    # Calculate original risk score using actual scorer
    # 使用实际评分器计算原始风险分数
    original_analysis = _scorer.analyze(request.sentence)
    original_risk = original_analysis.risk_score

    # Generate LLM suggestion (Track A)
    # 生成LLM建议（轨道A）
    llm_suggestion = None
    try:
        llm_result = await llm_track.generate_suggestion(
            sentence=request.sentence,
            issues=request.issues,
            locked_terms=request.locked_terms,
            target_lang=request.target_lang
        )
        if llm_result:
            # Calculate actual risk score for rewritten text
            # 为改写文本计算实际风险分数
            llm_analysis = _scorer.analyze(llm_result.rewritten)
            actual_risk = llm_analysis.risk_score

            llm_suggestion = Suggestion(
                source=SuggestionSource.LLM,
                rewritten=llm_result.rewritten,
                changes=[
                    ChangeDetail(
                        original=c.original,
                        replacement=c.replacement,
                        reason=c.reason,
                        reason_zh=c.reason_zh
                    ) for c in llm_result.changes
                ],
                predicted_risk=actual_risk,  # Use actual calculated risk
                semantic_similarity=llm_result.semantic_similarity,
                explanation=llm_result.explanation,
                explanation_zh=llm_result.explanation_zh
            )
    except Exception as e:
        # Log error but continue with rule-based suggestion
        # 记录错误但继续使用规则建议
        print(f"LLM track error: {e}")

    # Generate rule-based suggestion (Track B)
    # 生成规则建议（轨道B）
    rule_result = rule_track.generate_suggestion(
        sentence=request.sentence,
        issues=request.issues,
        locked_terms=request.locked_terms
    )
    # Calculate actual risk score for rule-based rewrite
    # 为规则改写计算实际风险分数
    rule_analysis = _scorer.analyze(rule_result.rewritten)
    rule_actual_risk = rule_analysis.risk_score

    rule_suggestion = Suggestion(
        source=SuggestionSource.RULE,
        rewritten=rule_result.rewritten,
        changes=[
            ChangeDetail(
                original=c.original,
                replacement=c.replacement,
                reason=c.reason,
                reason_zh=c.reason_zh
            ) for c in rule_result.changes
        ],
        predicted_risk=rule_actual_risk,  # Use actual calculated risk
        semantic_similarity=rule_result.semantic_similarity,
        explanation=rule_result.explanation,
        explanation_zh=rule_result.explanation_zh
    )

    # Generate translation of original
    # 生成原文翻译
    translation = await _translate_sentence(request.sentence, request.target_lang)

    return SuggestResponse(
        original=request.sentence,
        original_risk=original_risk,  # Use actual calculated risk
        translation=translation,
        llm_suggestion=llm_suggestion,
        rule_suggestion=rule_suggestion,
        locked_terms=request.locked_terms
    )


@router.post("/apply")
async def apply_suggestion(
    session_id: str,
    sentence_id: str,
    source: SuggestionSource,
    modified_text: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply a suggestion to a sentence (does NOT advance to next sentence)
    将建议应用到句子（不自动跳转到下一句）
    """
    from src.db.models import Modification, Sentence
    from sqlalchemy import select

    # Get the original sentence to get the original text if modified_text not provided
    # 获取原句以便在没有提供modified_text时使用原文
    sentence_result = await db.execute(
        select(Sentence).where(Sentence.id == sentence_id)
    )
    sentence = sentence_result.scalar_one_or_none()
    if not sentence:
        raise HTTPException(status_code=404, detail=f"Sentence not found: {sentence_id}")

    # Determine the text to calculate risk for
    # 确定用于计算风险的文本
    text_for_risk = modified_text if modified_text else sentence.original_text

    # Calculate new risk score using RiskScorer
    # 使用RiskScorer计算新风险分数
    new_risk_score = 0
    if text_for_risk:
        analysis = _scorer.analyze(text_for_risk)
        new_risk_score = analysis.risk_score

    # Check if modification already exists for this sentence
    # 检查该句子是否已有修改
    existing = await db.execute(
        select(Modification).where(
            Modification.session_id == session_id,
            Modification.sentence_id == sentence_id
        )
    )
    existing_mod = existing.scalar_one_or_none()

    if existing_mod:
        # Update existing modification
        # 更新现有修改
        existing_mod.source = source.value
        existing_mod.modified_text = modified_text or ""
        existing_mod.accepted = True
        existing_mod.new_risk_score = new_risk_score
    else:
        # Create new modification record
        # 创建新的修改记录
        mod = Modification(
            sentence_id=sentence_id,
            session_id=session_id,
            source=source.value,
            modified_text=modified_text or "",
            accepted=True,
            new_risk_score=new_risk_score
        )
        db.add(mod)

    await db.commit()

    # NOTE: Do NOT update session.current_index here
    # User will click on sidebar to navigate to next sentence
    # 注意：这里不更新 session.current_index
    # 用户将点击侧边栏导航到下一句

    return {"status": "applied", "sentence_id": sentence_id, "source": source.value, "new_risk_score": new_risk_score}


@router.post("/custom", response_model=ValidationResult)
async def validate_custom(
    request: CustomInputRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate user's custom modification
    验证用户的自定义修改
    """
    from src.db.models import Sentence
    from sqlalchemy import select

    # Get original sentence from database
    # 从数据库获取原句
    sentence_result = await db.execute(
        select(Sentence).where(Sentence.id == request.sentence_id)
    )
    sentence = sentence_result.scalar_one_or_none()

    if not sentence:
        raise HTTPException(status_code=404, detail=f"Sentence not found: {request.sentence_id}")

    original_text = sentence.original_text
    locked_terms = sentence.locked_terms_json or []

    # Initialize validators
    # 初始化验证器
    quality_gate = QualityGate()

    # Validate custom input against original
    # 验证自定义输入与原文对比
    result = await quality_gate.validate(
        original=original_text,
        modified=request.custom_text,
        locked_terms=locked_terms,
        target_risk=40
    )

    return ValidationResult(
        passed=result.passed,
        semantic_similarity=result.semantic_similarity,
        terms_intact=result.terms_intact,
        new_risk_score=result.new_risk_score,
        new_risk_level=RiskLevel(result.new_risk_level),
        message=result.message,
        message_zh=result.message_zh
    )


@router.post("/hints")
async def get_writing_hints(
    sentence: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get 3 writing hints for custom modification based on suggestions.md
    根据suggestions.md获取自定义修改的3个写作提示
    """
    hints = []
    sentence_lower = sentence.lower()

    # 1. Check for AI fingerprint words
    # 检查AI指纹词
    fingerprint_words = {
        "delve": "explore/examine",
        "crucial": "important/key",
        "paramount": "important",
        "pivotal": "key/central",
        "utilize": "use",
        "facilitate": "help/enable",
        "comprehensive": "full/complete",
        "multifaceted": "complex",
        "subsequently": "then/after",
        "realm": "area/field",
        "tapestry": "mix/blend",
        "underscore": "highlight/show",
        "foster": "encourage/build",
        "nuanced": "subtle/detailed",
        "inextricably": "closely",
        "furthermore": "[remove or use 'Also,']",
        "moreover": "[remove or use 'Also,']",
        "additionally": "[remove or use semantic flow]",
        "consequently": "so/as a result",
        "therefore": "so/thus",
    }

    found_fingerprints = []
    for word, replacement in fingerprint_words.items():
        if word in sentence_lower:
            found_fingerprints.append(f"'{word}' → {replacement}")

    if found_fingerprints:
        hints.append({
            "type": "fingerprint",
            "title": "替换AI高频词 / Replace AI Words",
            "titleZh": "替换AI高频词",
            "description": f"Found: {', '.join(found_fingerprints[:3])}",
            "descriptionZh": f"发现: {', '.join(found_fingerprints[:3])}"
        })

    # 2. Check for AI sentence templates
    # 检查AI句式模板
    templates_found = []
    if "not only" in sentence_lower and "but also" in sentence_lower:
        templates_found.append("'Not only X but also Y' → 'X. Also, Y.' or 'Beyond X, Y.'")
    if "it is crucial" in sentence_lower or "it is important" in sentence_lower or "it is essential" in sentence_lower:
        templates_found.append("'It is crucial/important to...' → 'We must...' or direct statement")
    if "serves as" in sentence_lower:
        templates_found.append("'serves as' → 'acts as' or 'is' or 'forms'")
    if sentence_lower.startswith("in conclusion") or sentence_lower.startswith("in summary"):
        templates_found.append("'In conclusion/summary' → 'Ultimately' or 'Findings suggest'")

    if templates_found:
        hints.append({
            "type": "template",
            "title": "改变AI句式模板 / Break AI Templates",
            "titleZh": "改变AI句式模板",
            "description": templates_found[0],
            "descriptionZh": templates_found[0]
        })

    # 3. Check for connector word overuse / passive voice
    # 检查连接词过度使用/被动语态
    connector_starts = ["furthermore", "moreover", "additionally", "consequently", "therefore", "thus", "notably", "importantly"]
    if any(sentence_lower.strip().startswith(c) for c in connector_starts):
        hints.append({
            "type": "connector",
            "title": "使用语义衔接 / Use Semantic Flow",
            "titleZh": "使用语义衔接",
            "description": "Avoid starting with connector words. Use 'This X...', 'Such Y...', or refer to previous content directly.",
            "descriptionZh": "避免以连接词开头。使用 'This X...', 'Such Y...' 或直接引用上文内容。"
        })

    # 4. Check for passive voice overuse
    # 检查被动语态过度使用
    passive_patterns = ["it is", "it was", "has been", "have been", "was found", "were found", "is shown", "are shown"]
    if any(p in sentence_lower for p in passive_patterns):
        if len(hints) < 3:
            hints.append({
                "type": "voice",
                "title": "使用主动语态 / Use Active Voice",
                "titleZh": "使用主动语态",
                "description": "'It was found that...' → 'We found...' or 'Results show...'",
                "descriptionZh": "'It was found that...' → 'We found...' 或 'Results show...'"
            })

    # 5. Check for vague academic padding
    # 检查模糊的学术填充
    padding_phrases = ["complex dynamics", "intricate interplay", "evolving landscape", "holistic approach", "comprehensive framework"]
    if any(p in sentence_lower for p in padding_phrases):
        if len(hints) < 3:
            hints.append({
                "type": "padding",
                "title": "删除空洞修饰 / Remove Padding",
                "titleZh": "删除空洞修饰",
                "description": "Replace vague phrases like 'complex dynamics' with specific descriptions of what happens.",
                "descriptionZh": "将 'complex dynamics' 等模糊短语替换为具体描述实际发生的情况。"
            })

    # If no specific issues found, give general tips
    # 如果没有发现具体问题，给出一般建议
    if len(hints) == 0:
        hints = [
            {
                "type": "general",
                "title": "增加句长变化 / Vary Sentence Length",
                "titleZh": "增加句长变化",
                "description": "Mix short punchy sentences with longer explanatory ones for natural rhythm.",
                "descriptionZh": "混合使用简短有力的句子和较长的解释性句子，形成自然节奏。"
            },
            {
                "type": "general",
                "title": "使用具体数据 / Be Specific",
                "titleZh": "使用具体数据",
                "description": "Replace 'significant increase' with specific numbers like '35% increase'.",
                "descriptionZh": "将 'significant increase' 替换为具体数字如 '35% increase'。"
            },
            {
                "type": "general",
                "title": "添加人类写作标记 / Add Human Markers",
                "titleZh": "添加人类写作标记",
                "description": "Use hedging ('appears to', 'suggests') or conviction ('clearly shows').",
                "descriptionZh": "使用缓和语气 ('appears to', 'suggests') 或确信语气 ('clearly shows')。"
            }
        ]

    return {"hints": hints[:3]}


@router.post("/analyze", response_model=SentenceAnalysisResponse)
async def analyze_sentence(
    request: SentenceAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform detailed grammatical and stylistic analysis of a sentence
    对句子进行详细的语法和风格分析
    """
    from src.config import get_settings
    import httpx
    import json
    import logging

    settings = get_settings()
    logger = logging.getLogger(__name__)

    # Build analysis prompt
    # 构建分析提示词
    analysis_prompt = f"""Analyze this English sentence in detail. Return a JSON object with the following structure:

Sentence: "{request.sentence}"

Required JSON structure:
{{
  "grammar": {{
    "subject": "the main subject (noun/noun phrase)",
    "subject_zh": "主语的中文说明",
    "predicate": "the main verb/verb phrase",
    "predicate_zh": "谓语的中文说明",
    "object": "the object if exists, null if none",
    "object_zh": "宾语的中文说明，无则null",
    "modifiers": [
      {{
        "type": "attributive|adverbial|complement",
        "type_zh": "定语|状语|补语",
        "text": "the modifier text",
        "modifies": "what it modifies"
      }}
    ]
  }},
  "clauses": [
    {{
      "type": "relative|noun|adverbial|conditional",
      "type_zh": "关系从句|名词从句|状语从句|条件从句",
      "text": "the clause text",
      "function": "what role it plays",
      "function_zh": "从句的作用说明"
    }}
  ],
  "pronouns": [
    {{
      "pronoun": "it/this/they/etc",
      "reference": "what it refers to",
      "reference_zh": "指代对象的中文说明",
      "context": "brief context"
    }}
  ],
  "ai_words": [
    {{
      "word": "the AI-typical word found",
      "level": 1 or 2,
      "level_desc": "Level 1: Dead giveaway | Level 2: AI tendency",
      "alternatives": ["alt1", "alt2", "alt3"],
      "context_suggestion": "how to use alternatives in this context"
    }}
  ],
  "rewrite_suggestions": [
    {{
      "type": "passive_to_active|split_sentence|simplify|vary_structure|remove_padding",
      "type_zh": "被动转主动|拆分长句|简化表达|变换句式|删除填充词",
      "description": "what change to make",
      "description_zh": "改动说明",
      "example": "example of rewritten version"
    }}
  ]
}}

AI-typical words to look for (Level 1 - dead giveaways): delve, tapestry, multifaceted, realm, testament, plethora, myriad, elucidate, underscore, pivotal, paramount, nuanced, intricate, holistic
AI-typical words to look for (Level 2 - AI tendencies): crucial, comprehensive, facilitate, utilize, furthermore, moreover, additionally, consequently, therefore, subsequently, notably, significantly

Colloquialism level for suggestions: {request.colloquialism_level}/10 (0=formal academic, 10=very casual)

Important:
1. If no clauses exist, return empty array for clauses
2. If no pronouns need clarification, return empty array for pronouns
3. Always check for AI words even if sentence seems natural
4. Provide at least 1-2 rewrite suggestions based on sentence structure
5. For alternatives, consider the colloquialism level

Return ONLY the JSON object, no other text."""

    try:
        content = None
        if settings.llm_provider == "gemini" and settings.gemini_api_key:
            # Call Gemini API
            # 调用Gemini API
            from google import genai
            client = genai.Client(api_key=settings.gemini_api_key)
            response = await client.aio.models.generate_content(
                model=settings.llm_model,
                contents=analysis_prompt,
                config={
                    "max_output_tokens": 2000,
                    "temperature": 0.3
                }
            )
            content = response.text.strip()
        elif settings.llm_provider == "deepseek" or settings.deepseek_api_key:
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
                    "model": settings.llm_model if settings.llm_provider == "deepseek" else "deepseek-chat",
                    "messages": [{"role": "user", "content": analysis_prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.3
                })
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
        else:
            # No LLM configured, use fallback
            # 没有配置LLM，使用备用方案
            return _get_fallback_analysis(request.sentence, request.colloquialism_level)

        if content:
            # Parse JSON from response
            # 从响应中解析JSON
            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            try:
                analysis = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}, content: {content[:500]}")
                # Return fallback response
                return _get_fallback_analysis(request.sentence, request.colloquialism_level)

            # Build response object
            # 构建响应对象
            grammar = GrammarStructure(
                subject=analysis.get("grammar", {}).get("subject", ""),
                subject_zh=analysis.get("grammar", {}).get("subject_zh", ""),
                predicate=analysis.get("grammar", {}).get("predicate", ""),
                predicate_zh=analysis.get("grammar", {}).get("predicate_zh", ""),
                object=analysis.get("grammar", {}).get("object"),
                object_zh=analysis.get("grammar", {}).get("object_zh"),
                modifiers=[
                    GrammarModifier(
                        type=m.get("type", ""),
                        type_zh=m.get("type_zh", ""),
                        text=m.get("text", ""),
                        modifies=m.get("modifies", "")
                    ) for m in analysis.get("grammar", {}).get("modifiers", [])
                ]
            )

            clauses = [
                ClauseInfo(
                    type=c.get("type", ""),
                    type_zh=c.get("type_zh", ""),
                    text=c.get("text", ""),
                    function=c.get("function", ""),
                    function_zh=c.get("function_zh", "")
                ) for c in analysis.get("clauses", [])
            ]

            pronouns = [
                PronounReference(
                    pronoun=p.get("pronoun", ""),
                    reference=p.get("reference", ""),
                    reference_zh=p.get("reference_zh", ""),
                    context=p.get("context", "")
                ) for p in analysis.get("pronouns", [])
            ]

            ai_words = [
                AIWordSuggestion(
                    word=w.get("word", ""),
                    level=w.get("level", 2),
                    level_desc=w.get("level_desc", ""),
                    alternatives=w.get("alternatives", []),
                    context_suggestion=w.get("context_suggestion", "")
                ) for w in analysis.get("ai_words", [])
            ]

            rewrite_suggestions = [
                RewriteSuggestion(
                    type=r.get("type", ""),
                    type_zh=r.get("type_zh", ""),
                    description=r.get("description", ""),
                    description_zh=r.get("description_zh", ""),
                    example=r.get("example")
                ) for r in analysis.get("rewrite_suggestions", [])
            ]

            return SentenceAnalysisResponse(
                original=request.sentence,
                grammar=grammar,
                clauses=clauses,
                pronouns=pronouns,
                ai_words=ai_words,
                rewrite_suggestions=rewrite_suggestions
            )

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return _get_fallback_analysis(request.sentence, request.colloquialism_level)


def _get_fallback_analysis(sentence: str, colloquialism_level: int) -> SentenceAnalysisResponse:
    """
    Return fallback analysis when LLM fails
    当LLM失败时返回备用分析
    """
    # Basic fingerprint detection
    # 基本指纹词检测
    level1_words = {"delve", "tapestry", "multifaceted", "realm", "testament", "plethora", "myriad", "elucidate", "underscore", "pivotal", "paramount", "nuanced", "intricate", "holistic"}
    level2_words = {"crucial", "comprehensive", "facilitate", "utilize", "furthermore", "moreover", "additionally", "consequently", "therefore", "subsequently", "notably", "significantly"}

    # Word replacements based on colloquialism level
    # 根据口语化程度的词汇替换
    replacements = {
        "delve": ["explore", "look into", "examine"] if colloquialism_level >= 5 else ["investigate", "examine"],
        "tapestry": ["mix", "blend", "combination"] if colloquialism_level >= 5 else ["array", "collection"],
        "multifaceted": ["complex", "varied"] if colloquialism_level >= 5 else ["diverse", "varied"],
        "crucial": ["key", "important", "vital"],
        "comprehensive": ["full", "complete", "thorough"],
        "facilitate": ["help", "enable", "make easier"],
        "utilize": ["use", "employ"],
        "furthermore": ["also", "plus"] if colloquialism_level >= 5 else ["additionally", "also"],
        "moreover": ["also", "and"] if colloquialism_level >= 5 else ["additionally"],
        "pivotal": ["key", "central", "important"],
        "paramount": ["top", "main", "key"] if colloquialism_level >= 5 else ["primary", "chief"],
    }

    sentence_lower = sentence.lower()
    ai_words = []

    for word in level1_words:
        if word in sentence_lower:
            ai_words.append(AIWordSuggestion(
                word=word,
                level=1,
                level_desc="一级词：AI典型标记",
                alternatives=replacements.get(word, ["[需要上下文替换]"]),
                context_suggestion="此词是AI生成文本的明显标志，建议替换"
            ))

    for word in level2_words:
        if word in sentence_lower:
            ai_words.append(AIWordSuggestion(
                word=word,
                level=2,
                level_desc="二级词：AI倾向用词",
                alternatives=replacements.get(word, ["[需要上下文替换]"]),
                context_suggestion="此词AI使用频率较高，可考虑替换"
            ))

    # Basic rewrite suggestions
    # 基本改写建议
    rewrite_suggestions = []

    if " is " in sentence_lower or " are " in sentence_lower or " was " in sentence_lower or " were " in sentence_lower:
        if "by " in sentence_lower or "it is" in sentence_lower or "it was" in sentence_lower:
            rewrite_suggestions.append(RewriteSuggestion(
                type="passive_to_active",
                type_zh="被动转主动",
                description="Convert passive voice to active voice for more direct expression",
                description_zh="将被动语态转为主动语态，表达更直接",
                example=None
            ))

    if len(sentence.split()) > 25:
        rewrite_suggestions.append(RewriteSuggestion(
            type="split_sentence",
            type_zh="拆分长句",
            description="Consider breaking this long sentence into shorter ones",
            description_zh="考虑将这个长句拆分成较短的句子",
            example=None
        ))

    if any(word in sentence_lower for word in ["not only", "both...and", "either...or"]):
        rewrite_suggestions.append(RewriteSuggestion(
            type="vary_structure",
            type_zh="变换句式",
            description="Replace parallel structures with simpler alternatives",
            description_zh="将并列结构替换为更简单的表达",
            example=None
        ))

    if not rewrite_suggestions:
        rewrite_suggestions.append(RewriteSuggestion(
            type="simplify",
            type_zh="简化表达",
            description="Look for opportunities to use simpler words and shorter phrases",
            description_zh="寻找机会使用更简单的词汇和更短的短语",
            example=None
        ))

    return SentenceAnalysisResponse(
        original=sentence,
        grammar=GrammarStructure(
            subject="[需要详细分析]",
            subject_zh="需要LLM进行详细分析",
            predicate="[需要详细分析]",
            predicate_zh="需要LLM进行详细分析",
            object=None,
            object_zh=None,
            modifiers=[]
        ),
        clauses=[],
        pronouns=[],
        ai_words=ai_words,
        rewrite_suggestions=rewrite_suggestions
    )


async def _translate_sentence(sentence: str, target_lang: str) -> str:
    """
    Translate sentence to target language using LLM
    使用LLM将句子翻译成目标语言
    """
    from src.config import get_settings
    import httpx
    import logging

    settings = get_settings()
    logger = logging.getLogger(__name__)

    # Map language codes to full names
    # 将语言代码映射到完整名称
    lang_names = {
        "zh": "Chinese (Simplified)",
        "en": "English",
        "ja": "Japanese",
        "ko": "Korean",
        "fr": "French",
        "de": "German",
        "es": "Spanish"
    }
    target_name = lang_names.get(target_lang, target_lang)

    prompt = f"""Translate the following academic English sentence to {target_name}.
Keep technical terms accurate. Only output the translation, nothing else.

Sentence: {sentence}

Translation:"""

    try:
        if settings.llm_provider == "gemini" and settings.gemini_api_key:
            # Call Gemini API for translation
            # 使用Gemini API翻译
            from google import genai
            client = genai.Client(api_key=settings.gemini_api_key)
            response = await client.aio.models.generate_content(
                model=settings.llm_model,
                contents=prompt,
                config={
                    "max_output_tokens": 500,
                    "temperature": 0.3
                }
            )
            return response.text.strip()
        elif settings.llm_provider == "deepseek" or settings.deepseek_api_key:
            async with httpx.AsyncClient(
                base_url=settings.deepseek_base_url,
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0,
                trust_env=False
            ) as client:
                response = await client.post("/chat/completions", json={
                    "model": settings.llm_model if settings.llm_provider == "deepseek" else "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.3
                })
                response.raise_for_status()
                data = response.json()
                translation = data["choices"][0]["message"]["content"].strip()
                return translation
        else:
            # No LLM configured
            # 没有配置LLM
            return f"[Translation to {target_lang} not available]"
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return f"[翻译失败 Translation failed]"


def _calculate_original_risk(issues: list) -> int:
    """
    Calculate original risk score from issues
    从问题列表计算原始风险分数
    """
    if not issues:
        return 30
    # Simple calculation based on issue count
    # 基于问题数量的简单计算
    return min(100, 30 + len(issues) * 15)
