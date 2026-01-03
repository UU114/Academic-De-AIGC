"""
Structure Restructuring Prompts (Level 1 De-AIGC)
结构重组提示词（Level 1 De-AIGC）

Phase 4: Prompts for document structure analysis and restructuring
Two strategies: optimize_connection (gentle) and deep_restructure (aggressive)

Phase 4：文档结构分析和重组的提示词
两种策略：优化连接（温和）和深度重组（激进）

Enhanced with:
- Disruption level parameterization (light/medium/strong)
- Six disruption strategies (inversion, conflict, induction, asymmetry, weak_closure, lexical_echo)
- Human features allowlist (function overlap, unresolved tension, open endings)

增强功能：
- 扰动等级参数化（轻度/中度/强度）
- 六大扰动策略（倒置、冲突引入、归纳、非对称、弱闭合、词汇回声）
- 人类特征允许列表（功能重叠、未解决张力、开放式结尾）
"""

from typing import Optional, Dict, List

# =============================================================================
# Disruption Level Definitions (Core Enhancement)
# 扰动等级定义（核心增强）
# =============================================================================

DISRUPTION_LEVELS = {
    "light": {
        "name": "Light Disruption",
        "name_zh": "轻度扰动",
        "description": "Minimal changes: vary openings, remove explicit connectors, add lexical echo",
        "description_zh": "最小改动：变化开头，移除显性连接词，添加词汇回声",
        "allowed_strategies": ["rewrite_opening", "remove_connector", "lexical_echo"],
        "max_reorder": 0,  # No paragraph reordering
        "thesis_move": False,  # Keep thesis in original position
        "allow_weak_closure": False,  # Keep original closure
        "target_predictability_reduction": 15,  # Expected score reduction
    },
    "medium": {
        "name": "Medium Disruption",
        "name_zh": "中度扰动",
        "description": "Moderate changes: local reorder, add asymmetry, create non-monotonic flow",
        "description_zh": "适度改动：局部重排，增加非对称，创建非单调流",
        "allowed_strategies": ["rewrite_opening", "remove_connector", "lexical_echo",
                               "local_reorder", "asymmetry", "non_monotonic"],
        "max_reorder": 2,  # Reorder up to 2 paragraphs
        "thesis_move": False,
        "allow_weak_closure": True,  # Can suggest weaker closure
        "target_predictability_reduction": 25,
    },
    "strong": {
        "name": "Strong Disruption",
        "name_zh": "强度扰动",
        "description": "Aggressive changes: full reorder, structure inversion, conflict injection, open endings",
        "description_zh": "激进改动：完全重排，结构倒置，冲突引入，开放式结尾",
        "allowed_strategies": ["rewrite_opening", "remove_connector", "lexical_echo",
                               "full_reorder", "asymmetry", "non_monotonic",
                               "inversion", "conflict_injection", "induction", "weak_closure"],
        "max_reorder": None,  # Unlimited reordering
        "thesis_move": True,  # Can move thesis to middle or end
        "allow_weak_closure": True,
        "target_predictability_reduction": 40,
    },
}

# =============================================================================
# Six Disruption Strategies
# 六大扰动策略
# =============================================================================

DISRUPTION_STRATEGIES = {
    "inversion": {
        "name": "Structure Inversion",
        "name_zh": "结构倒置",
        "description": "Swap logical order: definition↔problem, method↔failure case",
        "description_zh": "交换逻辑顺序：定义↔问题，方法↔失败案例",
        "prompt_instruction": "Swap the order of problem statement and solution, or definition and application. Start with the concrete before the abstract.",
    },
    "conflict_injection": {
        "name": "Conflict Injection",
        "name_zh": "冲突引入",
        "description": "Introduce counter-arguments, limitations, or boundary conditions before main claims",
        "description_zh": "在主要论述前引入反对意见、局限性或边界条件",
        "prompt_instruction": "Insert a paragraph acknowledging limitations, counter-evidence, or boundary conditions BEFORE presenting the main argument. Create productive tension.",
    },
    "induction": {
        "name": "Inductive Progression",
        "name_zh": "归纳式推进",
        "description": "Start with specific observations/data, delay explicit conclusions",
        "description_zh": "从具体观察/数据切入，延迟显式结论",
        "prompt_instruction": "Restructure to start with specific data, examples, or observations. Delay the thesis statement until paragraph 3 or later. Let the conclusion emerge from evidence.",
    },
    "asymmetry": {
        "name": "Asymmetric Layout",
        "name_zh": "非对称布局",
        "description": "Deep-dive one argument (150%), briefly scan others (60%)",
        "description_zh": "深入展开一个论点（150%篇幅），简要扫过其他（60%篇幅）",
        "prompt_instruction": "Expand one key paragraph to 150% of its current length with deeper analysis. Compress 2-3 other paragraphs to 60% of their length. Create intentional imbalance.",
    },
    "weak_closure": {
        "name": "Weak Closure",
        "name_zh": "弱闭合",
        "description": "Replace definitive conclusions with open questions or unresolved tensions",
        "description_zh": "用开放问题或未解决张力替代明确结论",
        "prompt_instruction": "Rewrite the conclusion to avoid 'In conclusion' or 'This study demonstrates'. End with: open questions, implications for future work, or acknowledged uncertainties. Leave some tension unresolved.",
    },
    "lexical_echo": {
        "name": "Lexical Echo",
        "name_zh": "词汇回声",
        "description": "Use key concepts from paragraph end in next paragraph opening (implicit connection)",
        "description_zh": "在下段开头使用上段结尾的关键概念（隐性连接）",
        "prompt_instruction": "For each paragraph transition, identify 1-2 key concepts from the ending sentences and naturally incorporate them into the next paragraph's opening WITHOUT using explicit connectors like 'Furthermore' or 'Moreover'.",
    },
}

# =============================================================================
# Human Features Allowlist (Do NOT over-correct)
# 人类特征允许列表（不要过度纠正）
# =============================================================================

HUMAN_FEATURES_ALLOWED = """
## Allowed Human Features (Do NOT over-correct these)
## 允许的人类特征（不要过度纠正）

The following patterns are INTENTIONAL and should be PRESERVED or INTRODUCED:

1. **Paragraph Function Overlap** (段落功能重叠)
   - Evidence and analysis CAN appear in the same paragraph
   - Introduction CAN contain arguments
   - Do NOT separate into rigid "one function per paragraph" structure

2. **Unresolved Tension** (未完全解决的张力)
   - Leave some questions open
   - Acknowledge limitations WITHOUT resolving them
   - Allow productive ambiguity

3. **Weak/Open Endings** (弱/开放式结尾)
   - AVOID formulaic "In conclusion, this study demonstrates..."
   - PREFER: "What remains unclear...", "Further investigation...", "The implications extend beyond..."
   - Questions at the end are ACCEPTABLE

4. **Asymmetric Depth** (非对称深度)
   - One argument CAN get 3x the space of others
   - Not all points need equal treatment
   - Brief mentions are acceptable for minor points

5. **Non-Linear References** (非线性引用)
   - Return to earlier points is GOOD
   - "As noted earlier...", "Revisiting the initial observation..."
   - Circular or recursive references show depth

6. **Conditional Statements** (条件陈述)
   - "If X, then Y" is more human than "X leads to Y"
   - Hedged claims show nuance
   - Uncertainty markers are VALUABLE, not weaknesses
"""

# =============================================================================
# Strategy descriptions (Original, kept for compatibility)
# 策略描述（原有，保持兼容性）
# =============================================================================

STRUCTURE_STRATEGY_DESCRIPTIONS = {
    "optimize_connection": {
        "name": "Optimize Connection",
        "name_zh": "优化连接",
        "description": "Improve paragraph connections without changing content order",
        "description_zh": "在不改变内容顺序的情况下改善段落连接"
    },
    "deep_restructure": {
        "name": "Deep Restructure",
        "name_zh": "深度重组",
        "description": "Reorder and reorganize content for maximum naturalness",
        "description_zh": "重新排序和组织内容以获得最大自然度"
    }
}


def get_structure_analysis_prompt(
    paragraphs: List[str],
    extracted_thesis: Optional[str] = None
) -> str:
    """
    Generate prompt for structure analysis
    生成结构分析提示词

    Args:
        paragraphs: List of paragraph texts 段落文本列表
        extracted_thesis: Extracted thesis statement 提取的论点陈述

    Returns:
        Prompt for structure analysis 结构分析提示词
    """
    numbered_paras = "\n\n".join([
        f"[Paragraph {i+1}]\n{p}" for i, p in enumerate(paragraphs)
    ])

    thesis_section = ""
    if extracted_thesis:
        thesis_section = f"""
Extracted Core Thesis:
{extracted_thesis}
"""

    return f"""You are an expert academic writing analyst specializing in detecting AI-generated structural patterns.

Analyze the following document structure for AI detection risks:

{numbered_paras}
{thesis_section}

Analyze for these AI-typical structural patterns:
1. **Linear Enumeration Flow**: "First...Second...Third" progression
2. **Repetitive Paragraph Structure**: Same opening patterns across paragraphs
3. **Uniform Paragraph Length**: Suspiciously similar word counts
4. **Predictable Order**: Formulaic introduction-body-conclusion structure
5. **Missing Logic Connections**: Gaps between evidence and conclusions

For each issue found, provide:
- Type of issue
- Severity (high/medium/low)
- Affected paragraph numbers
- Specific suggestion for improvement

Respond in JSON format:
{{
  "issues": [
    {{
      "type": "linear_flow|repetitive_pattern|uniform_length|predictable_order|logic_gap",
      "description": "English description",
      "description_zh": "中文描述",
      "severity": "high|medium|low",
      "affected_paragraphs": [1, 2, 3],
      "suggestion": "English suggestion",
      "suggestion_zh": "中文建议"
    }}
  ],
  "overall_risk": "high|medium|low",
  "logic_flow_summary": "Brief summary of document's logical flow",
  "logic_flow_summary_zh": "文档逻辑流程的简要总结"
}}"""


def get_optimize_connection_prompt(
    paragraphs: List[str],
    issues: List[Dict],
    extracted_thesis: Optional[str] = None
) -> str:
    """
    Generate prompt for connection optimization strategy
    生成连接优化策略提示词

    This gentle approach maintains paragraph order but improves transitions
    这种温和的方法保持段落顺序但改善过渡

    Args:
        paragraphs: List of paragraph texts 段落文本列表
        issues: List of detected issues 检测到的问题列表
        extracted_thesis: Extracted thesis statement 提取的论点陈述

    Returns:
        Prompt for connection optimization 连接优化提示词
    """
    numbered_paras = "\n\n".join([
        f"[Paragraph {i+1}]\n{p}" for i, p in enumerate(paragraphs)
    ])

    issues_text = "\n".join([
        f"- {issue.get('type', 'unknown')}: {issue.get('description', '')}"
        for issue in issues
    ])

    thesis_section = ""
    if extracted_thesis:
        thesis_section = f"\nCore Thesis: {extracted_thesis}\n"

    return f"""You are an expert academic writing editor specializing in naturalizing document structure.

TASK: Optimize paragraph connections while preserving content order.

DOCUMENT:
{numbered_paras}
{thesis_section}
DETECTED ISSUES:
{issues_text}

STRATEGY: Optimize Connection (保持顺序，优化衔接)

Your goals:
1. Remove or replace explicit linear markers (First, Second, Third → varied transitions)
2. Add semantic bridges between paragraphs (echo key concepts from previous paragraph)
3. Vary paragraph openings to break repetitive patterns
4. Create implicit logical flow rather than explicit enumeration

For each paragraph, provide:
1. Modified opening sentence (first 1-2 sentences only)
2. Explanation of changes
3. Key concept to echo in the next paragraph

Respond in JSON format:
{{
  "strategy": "optimize_connection",
  "strategy_name_zh": "优化连接",
  "modifications": [
    {{
      "paragraph_index": 0,
      "original_opening": "Original text...",
      "modified_opening": "Improved text...",
      "explanation": "Why this change helps",
      "explanation_zh": "为什么这个改变有帮助",
      "echo_concept": "Key concept for next paragraph to reference"
    }}
  ],
  "new_outline": ["Brief summary of para 1", "Brief summary of para 2", ...],
  "predicted_improvement": 15,
  "explanation": "Overall explanation of changes",
  "explanation_zh": "整体改变说明"
}}"""


def get_deep_restructure_prompt(
    paragraphs: List[str],
    issues: List[Dict],
    extracted_thesis: Optional[str] = None,
    key_arguments: Optional[List[str]] = None
) -> str:
    """
    Generate prompt for deep restructuring strategy
    生成深度重组策略提示词

    This aggressive approach may reorder paragraphs for better flow
    这种激进的方法可能会重新排序段落以获得更好的流程

    Args:
        paragraphs: List of paragraph texts 段落文本列表
        issues: List of detected issues 检测到的问题列表
        extracted_thesis: Extracted thesis statement 提取的论点陈述
        key_arguments: Extracted key arguments 提取的关键论据

    Returns:
        Prompt for deep restructuring 深度重组提示词
    """
    numbered_paras = "\n\n".join([
        f"[Paragraph {i+1}]\n{p}" for i, p in enumerate(paragraphs)
    ])

    issues_text = "\n".join([
        f"- {issue.get('type', 'unknown')}: {issue.get('description', '')}"
        for issue in issues
    ])

    thesis_section = ""
    if extracted_thesis:
        thesis_section = f"\nCore Thesis: {extracted_thesis}\n"

    arguments_section = ""
    if key_arguments:
        arguments_section = "\nKey Arguments:\n" + "\n".join([
            f"- {arg}" for arg in key_arguments
        ])

    return f"""You are an expert academic writing architect specializing in non-linear document structure.

TASK: Propose a restructured organization that breaks AI-typical linear patterns.

DOCUMENT:
{numbered_paras}
{thesis_section}{arguments_section}

DETECTED ISSUES:
{issues_text}

STRATEGY: Deep Restructure (深度重组)

Your goals:
1. Break the predictable introduction-body-conclusion format
2. Consider alternative structures:
   - Problem-Solution-Implications
   - Compare-Contrast-Synthesize
   - Specific-to-General (inductive)
   - Hook-Context-Argument-Evidence cycle
3. Interleave evidence and analysis rather than separating them
4. Move the thesis to a non-typical position (middle or end)
5. Create "breathing room" with varied paragraph lengths

Propose a new structure with:
1. New paragraph order (by index)
2. Suggested splits or merges
3. New transition strategies between each pair

Respond in JSON format:
{{
  "strategy": "deep_restructure",
  "strategy_name_zh": "深度重组",
  "restructure_type": "problem_solution|compare_contrast|inductive|hook_cycle",
  "restructure_type_zh": "问题解决|对比对照|归纳推理|钩子循环",
  "new_order": [3, 1, 2, 4, 5],
  "changes": [
    {{
      "type": "reorder|split|merge|insert",
      "affected_paragraphs": [1, 2],
      "description": "Description of change",
      "description_zh": "改变描述"
    }}
  ],
  "new_outline": ["New para 1 summary", "New para 2 summary", ...],
  "thesis_position": "middle|end|embedded",
  "predicted_improvement": 25,
  "explanation": "Why this restructure breaks AI patterns",
  "explanation_zh": "为什么这种重组可以打破AI模式"
}}"""


def get_paragraph_rewrite_prompt(
    paragraph: str,
    context_before: Optional[str] = None,
    context_after: Optional[str] = None,
    rewrite_type: str = "opening"
) -> str:
    """
    Generate prompt for rewriting a specific paragraph
    生成重写特定段落的提示词

    Args:
        paragraph: The paragraph to rewrite 要重写的段落
        context_before: Previous paragraph for context 上下文前段落
        context_after: Following paragraph for context 上下文后段落
        rewrite_type: Type of rewrite (opening, transition, full) 重写类型

    Returns:
        Prompt for paragraph rewriting 段落重写提示词
    """
    context_section = ""
    if context_before:
        context_section += f"\n[Previous Paragraph Ending]\n...{context_before[-200:]}\n"
    if context_after:
        context_section += f"\n[Following Paragraph Opening]\n{context_after[:200]}...\n"

    if rewrite_type == "opening":
        task = "Rewrite only the opening 1-2 sentences to be less AI-typical"
    elif rewrite_type == "transition":
        task = "Rewrite to better connect with surrounding paragraphs"
    else:
        task = "Rewrite the entire paragraph to feel more natural and human-written"

    return f"""You are an expert academic writer helping to naturalize document structure.

TASK: {task}
{context_section}
[Target Paragraph]
{paragraph}

Requirements:
- Maintain the core meaning and academic tone
- Remove explicit enumeration markers (First, Second, Moreover, Furthermore)
- Create implicit rather than explicit connections
- Vary sentence structure and length
- Keep the rewrite approximately the same length

Respond in JSON format:
{{
  "original": "First sentence or two...",
  "rewritten": "Improved version...",
  "changes_made": ["Change 1", "Change 2"],
  "changes_made_zh": ["改变1", "改变2"]
}}"""


def get_logic_diagnosis_prompt(
    paragraphs: List[str],
    document_type: str = "research_paper"
) -> str:
    """
    Generate prompt for comprehensive logic diagnosis
    生成综合逻辑诊断提示词

    This provides a visual "logic diagnosis card" for the user
    这为用户提供可视化的"逻辑诊断卡"

    Args:
        paragraphs: List of paragraph texts 段落文本列表
        document_type: Type of document 文档类型

    Returns:
        Prompt for logic diagnosis 逻辑诊断提示词
    """
    numbered_paras = "\n\n".join([
        f"[P{i+1}] {p[:100]}..." for i, p in enumerate(paragraphs)
    ])

    return f"""You are an expert academic writing analyst creating a "Logic Diagnosis Card" (逻辑诊断卡).

DOCUMENT TYPE: {document_type}

PARAGRAPHS (abbreviated):
{numbered_paras}

Create a comprehensive logic diagnosis with:

1. **Flow Visualization**: Identify the logical relationship between each pair of paragraphs:
   - → (continuation)
   - ↔ (comparison)
   - ⤵ (evidence support)
   - ⟳ (return to earlier point)
   - ✗ (logical gap)

2. **Structure Pattern**: Identify the overall structure pattern:
   - Linear (线性): A→B→C→D
   - Parallel (并列): A, B, C, D
   - Nested (嵌套): A(B(C))D
   - Circular (环形): A→B→C→A

3. **Risk Areas**: Identify specific paragraphs that are most AI-detectable

4. **Recommendation**: Whether to use optimize_connection or deep_restructure

Respond in JSON format:
{{
  "flow_map": [
    {{"from": 1, "to": 2, "relation": "continuation", "symbol": "→"}},
    {{"from": 2, "to": 3, "relation": "evidence", "symbol": "⤵"}}
  ],
  "structure_pattern": "linear|parallel|nested|circular",
  "structure_pattern_zh": "线性|并列|嵌套|环形",
  "pattern_description": "Brief description of detected pattern",
  "pattern_description_zh": "检测到的模式简要描述",
  "risk_areas": [
    {{
      "paragraph": 1,
      "risk_level": "high|medium|low",
      "reason": "Why this is risky",
      "reason_zh": "为什么有风险"
    }}
  ],
  "recommended_strategy": "optimize_connection|deep_restructure",
  "recommendation_reason": "Why this strategy is recommended",
  "recommendation_reason_zh": "为什么推荐这个策略"
}}"""


def get_all_strategies_prompt(
    paragraphs: List[str],
    issues: List[Dict],
    extracted_thesis: Optional[str] = None,
    key_arguments: Optional[List[str]] = None
) -> str:
    """
    Generate prompt for getting both strategy options
    生成获取两种策略选项的提示词

    Args:
        paragraphs: List of paragraph texts 段落文本列表
        issues: List of detected issues 检测到的问题列表
        extracted_thesis: Extracted thesis statement 提取的论点陈述
        key_arguments: Extracted key arguments 提取的关键论据

    Returns:
        Prompt for both strategies 两种策略的提示词
    """
    numbered_paras = "\n\n".join([
        f"[Paragraph {i+1}]\n{p}" for i, p in enumerate(paragraphs)
    ])

    issues_text = "\n".join([
        f"- {issue.get('type', 'unknown')}: {issue.get('description', '')}"
        for issue in issues
    ]) if issues else "No specific issues detected."

    thesis_section = ""
    if extracted_thesis:
        thesis_section = f"\nCore Thesis: {extracted_thesis}\n"

    arguments_section = ""
    if key_arguments:
        arguments_section = "\nKey Arguments:\n" + "\n".join([
            f"- {arg}" for arg in key_arguments[:3]
        ])

    return f"""You are an expert academic writing architect. Provide TWO restructuring strategies.

DOCUMENT:
{numbered_paras}
{thesis_section}{arguments_section}

DETECTED ISSUES:
{issues_text}

Provide both strategies:

1. **Optimize Connection** (优化连接): Gentle approach - keep order, improve transitions
2. **Deep Restructure** (深度重组): Aggressive approach - reorder for maximum naturalness

For each strategy, provide specific, actionable changes.

=== CRITICAL RULES FOR outline FIELD ===
You MUST follow these rules EXACTLY:

1. outline MUST contain CONTENT DESCRIPTIONS, describing what each paragraph talks about
2. FORBIDDEN WORDS in outline: "body", "evidence", "conclusion", "introduction", "argument", "support"
3. Each outline item MUST be 5-15 words describing the SPECIFIC TOPIC of that paragraph
4. Format: "段落N: [具体讨论的主题内容]"

CORRECT EXAMPLES:
- "段落1: 蛋白质二级结构预测的研究背景与挑战"
- "段落2: 提出的CNN-LSTM混合架构设计细节"
- "段落3: CB513数据集的预处理方法"
- "段落4: 与现有方法的准确率对比实验"

WRONG EXAMPLES (DO NOT USE):
- "段落1: body" ← FORBIDDEN
- "段落2: evidence" ← FORBIDDEN
- "段落3: conclusion" ← FORBIDDEN
- "段落4: introduction" ← FORBIDDEN

If you use forbidden words, your response will be rejected.

Respond in JSON format:
{{
  "optimize_connection": {{
    "strategy": "optimize_connection",
    "strategy_name_zh": "优化连接",
    "modifications": [
      {{
        "paragraph_index": 0,
        "change_type": "rewrite_opening",
        "original": "First sentence...",
        "modified": "Improved sentence...",
        "explanation_zh": "说明"
      }}
    ],
    "outline": ["段落1: 具体内容主题", "段落2: 具体内容主题", "..."],
    "predicted_improvement": 15,
    "explanation_zh": "整体说明"
  }},
  "deep_restructure": {{
    "strategy": "deep_restructure",
    "strategy_name_zh": "深度重组",
    "new_order": [3, 1, 2, 4],
    "restructure_type": "inductive",
    "restructure_type_zh": "归纳推理",
    "changes": [
      {{
        "type": "reorder",
        "description_zh": "将段落3移到开头作为引子"
      }}
    ],
    "outline": ["段落1: 具体内容主题 (原段落X)", "段落2: 具体内容主题 (原段落Y)", "..."],
    "predicted_improvement": 25,
    "explanation_zh": "整体说明"
  }}
}}"""


# =============================================================================
# Enhanced Disruption Restructure Prompt (P1 Enhancement)
# 增强扰动重组提示词（P1增强）
# =============================================================================

def get_disruption_restructure_prompt(
    paragraphs: List[str],
    disruption_level: str = "medium",
    selected_strategies: Optional[List[str]] = None,
    predictability_score: Optional[Dict] = None,
    extracted_thesis: Optional[str] = None
) -> str:
    """
    Generate prompt for disruption-based restructuring (Core Enhancement)
    生成基于扰动的重组提示词（核心增强）

    This is the main entry point for Level 1 De-AIGC enhancement.
    Uses parameterized disruption levels and selected strategies.

    Args:
        paragraphs: List of paragraph texts 段落文本列表
        disruption_level: light/medium/strong 扰动等级
        selected_strategies: List of strategy names to apply 要应用的策略名称列表
        predictability_score: Output from StructurePredictabilityAnalyzer 预测性评分
        extracted_thesis: Extracted thesis statement 提取的论点陈述

    Returns:
        Prompt for disruption restructuring 扰动重组提示词
    """
    # Get level configuration
    level_config = DISRUPTION_LEVELS.get(disruption_level, DISRUPTION_LEVELS["medium"])

    # If no strategies specified, use all allowed by level
    if selected_strategies is None:
        selected_strategies = level_config["allowed_strategies"]

    # Build numbered paragraphs
    numbered_paras = "\n\n".join([
        f"[Paragraph {i+1}]\n{p}" for i, p in enumerate(paragraphs)
    ])

    # Build strategy instructions
    strategy_instructions = []
    for strategy_key in selected_strategies:
        if strategy_key in DISRUPTION_STRATEGIES:
            strategy = DISRUPTION_STRATEGIES[strategy_key]
            strategy_instructions.append(
                f"**{strategy['name']}** ({strategy['name_zh']}): {strategy['prompt_instruction']}"
            )

    strategies_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(strategy_instructions)])

    # Build predictability context if available
    predictability_section = ""
    if predictability_score:
        predictability_section = f"""
CURRENT PREDICTABILITY ANALYSIS:
- Total Score: {predictability_score.get('total_score', 'N/A')}/100 (higher = more AI-like)
- Progression Type: {predictability_score.get('progression_type', 'unknown')}
- Function Distribution: {predictability_score.get('function_distribution', 'unknown')}
- Closure Type: {predictability_score.get('closure_type', 'unknown')}
- Target Reduction: {level_config['target_predictability_reduction']}%
"""

    # Build thesis context
    thesis_section = ""
    if extracted_thesis:
        thesis_section = f"\nCORE THESIS: {extracted_thesis}\n"

    # Build level constraints
    constraints = []
    if level_config["max_reorder"] is not None:
        constraints.append(f"- Maximum paragraph reorder: {level_config['max_reorder']} paragraphs")
    if not level_config["thesis_move"]:
        constraints.append("- Keep thesis in its current position")
    if level_config["allow_weak_closure"]:
        constraints.append("- May suggest weaker/open conclusions")
    constraints_text = "\n".join(constraints) if constraints else "- No specific constraints"

    return f"""You are an expert academic writing architect specializing in breaking structural predictability.

TASK: Apply {level_config['name']} ({level_config['name_zh']}) to reduce AI detection risk.
{level_config['description']}

DOCUMENT:
{numbered_paras}
{thesis_section}{predictability_section}

LEVEL CONSTRAINTS:
{constraints_text}

STRATEGIES TO APPLY:
{strategies_text}

{HUMAN_FEATURES_ALLOWED}

=== CRITICAL RULES ===
1. Apply ONLY the strategies listed above
2. Maintain academic rigor and logical coherence
3. Preserve the core arguments and evidence
4. Create INTENTIONAL non-uniformity (this is the goal, not a mistake)
5. Do NOT create a new "perfect" structure - allow human-like imperfections

=== OUTPUT FORMAT ===
Provide detailed restructuring suggestions:

{{
  "disruption_level": "{disruption_level}",
  "applied_strategies": ["strategy1", "strategy2", ...],
  "modifications": [
    {{
      "strategy": "strategy_name",
      "paragraph_index": 0,
      "change_type": "rewrite_opening|add_conflict|delay_thesis|expand|compress|reorder",
      "original": "Original text fragment...",
      "modified": "Modified text fragment...",
      "explanation": "Why this change reduces predictability",
      "explanation_zh": "为什么这个改变能降低可预测性"
    }}
  ],
  "structure_changes": [
    {{
      "type": "reorder|merge|split|insert",
      "affected_paragraphs": [1, 2],
      "new_position": 3,
      "description": "Description of structural change",
      "description_zh": "结构变化描述"
    }}
  ],
  "new_outline": [
    "段落1: [具体内容描述]",
    "段落2: [具体内容描述]"
  ],
  "human_features_introduced": [
    "功能重叠: 段落2同时包含证据和分析",
    "弱闭合: 结论部分改为开放式问题"
  ],
  "predicted_score_reduction": {level_config['target_predictability_reduction']},
  "overall_explanation": "Summary of how these changes break AI patterns",
  "overall_explanation_zh": "这些改变如何打破AI模式的总结"
}}"""


def get_single_strategy_prompt(
    paragraph: str,
    strategy: str,
    paragraph_index: int,
    context_before: Optional[str] = None,
    context_after: Optional[str] = None
) -> str:
    """
    Generate prompt for applying a single disruption strategy to one paragraph
    生成将单个扰动策略应用于一个段落的提示词

    Args:
        paragraph: Target paragraph text 目标段落文本
        strategy: Strategy name from DISRUPTION_STRATEGIES 策略名称
        paragraph_index: Index of paragraph 段落索引
        context_before: Previous paragraph ending 上一段落结尾
        context_after: Next paragraph beginning 下一段落开头

    Returns:
        Prompt for single strategy application 单策略应用提示词
    """
    if strategy not in DISRUPTION_STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy}")

    strat = DISRUPTION_STRATEGIES[strategy]

    # Build context section
    context_section = ""
    if context_before:
        context_section += f"\n[Previous Paragraph Ending]\n...{context_before[-200:]}\n"
    if context_after:
        context_section += f"\n[Following Paragraph Opening]\n{context_after[:200]}...\n"

    return f"""You are an expert academic writer applying the "{strat['name']}" strategy.

STRATEGY: {strat['name']} ({strat['name_zh']})
INSTRUCTION: {strat['prompt_instruction']}

{context_section}
[Target Paragraph {paragraph_index + 1}]
{paragraph}

Apply this strategy while:
1. Maintaining academic tone and rigor
2. Preserving the core meaning
3. Creating natural, human-like flow

Respond in JSON format:
{{
  "strategy": "{strategy}",
  "paragraph_index": {paragraph_index},
  "original": "First few sentences...",
  "modified": "Rewritten version applying {strategy}...",
  "specific_changes": [
    "Change 1: description",
    "Change 2: description"
  ],
  "specific_changes_zh": [
    "改变1: 描述",
    "改变2: 描述"
  ]
}}"""


def get_lexical_echo_prompt(
    paragraph_ending: str,
    next_paragraph_opening: str,
    paragraph_indices: tuple
) -> str:
    """
    Generate prompt specifically for creating lexical echo between paragraphs
    生成专门用于创建段落间词汇回声的提示词

    Args:
        paragraph_ending: End of current paragraph 当前段落结尾
        next_paragraph_opening: Beginning of next paragraph 下一段落开头
        paragraph_indices: Tuple of (current_index, next_index) 段落索引元组

    Returns:
        Prompt for lexical echo creation 词汇回声创建提示词
    """
    return f"""You are an expert at creating implicit semantic connections between paragraphs.

TASK: Create a "lexical echo" between these paragraphs WITHOUT using explicit connectors.

[Paragraph {paragraph_indices[0] + 1} Ending]
{paragraph_ending}

[Paragraph {paragraph_indices[1] + 1} Opening]
{next_paragraph_opening}

LEXICAL ECHO TECHNIQUE:
1. Identify 1-2 key concepts/terms from the ending sentences
2. Naturally incorporate these concepts into the opening of the next paragraph
3. Do NOT use explicit connectors (Furthermore, Moreover, Additionally, However)
4. The connection should be semantic, not syntactic

FORBIDDEN OPENINGS:
- "Furthermore,..."
- "Moreover,..."
- "Additionally,..."
- "In addition,..."
- "However,..."
- "Nevertheless,..."
- "Consequently,..."

GOOD OPENINGS (examples):
- Echo a noun: "This limitation [echoing 'constraint' from above]..."
- Echo a concept: "The efficiency gains [echoing 'performance' from above]..."
- Echo a verb form: "Such restructuring [echoing 'reorganize' from above]..."

Respond in JSON format:
{{
  "key_concepts_identified": ["concept1 from ending", "concept2 from ending"],
  "original_opening": "Original next paragraph opening...",
  "modified_opening": "Opening with lexical echo...",
  "echo_technique": "Description of how the echo was created",
  "echo_technique_zh": "词汇回声创建方式描述"
}}"""


def get_weak_closure_prompt(
    conclusion_paragraph: str,
    document_topic: Optional[str] = None
) -> str:
    """
    Generate prompt for creating weak/open closure
    生成创建弱闭合/开放式结尾的提示词

    Args:
        conclusion_paragraph: The current conclusion paragraph 当前结论段落
        document_topic: Optional topic for context 可选主题用于上下文

    Returns:
        Prompt for weak closure creation 弱闭合创建提示词
    """
    topic_section = ""
    if document_topic:
        topic_section = f"\nDOCUMENT TOPIC: {document_topic}\n"

    return f"""You are an expert at creating academic conclusions that feel human-written.

TASK: Transform this formulaic conclusion into a more open, human-like ending.
{topic_section}
[Current Conclusion]
{conclusion_paragraph}

AI-TYPICAL PATTERNS TO AVOID:
- "In conclusion, this study demonstrates..."
- "To summarize, we have shown..."
- "In summary, the results indicate..."
- "This paper has shown that..."
- Perfect closure with no loose ends

HUMAN-LIKE PATTERNS TO USE:
- Open questions: "What remains to be explored is..."
- Acknowledged uncertainty: "While the evidence suggests X, the extent of Y remains unclear..."
- Future implications: "These findings open new questions about..."
- Productive tension: "The tension between X and Y points to..."
- Non-definitive hedging: "The data appears to support..., though further investigation..."

REQUIREMENTS:
1. Remove formulaic conclusion markers
2. Leave at least ONE question open or tension unresolved
3. Use hedging language appropriately
4. Maintain academic professionalism
5. Keep approximately the same length

Respond in JSON format:
{{
  "original_closure_type": "strong|moderate|already_weak",
  "ai_patterns_detected": ["pattern1", "pattern2"],
  "modified_conclusion": "The rewritten conclusion paragraph...",
  "open_elements_introduced": [
    "Open question: what about X?",
    "Unresolved tension: between A and B"
  ],
  "open_elements_introduced_zh": [
    "开放问题: 关于X的问题",
    "未解决张力: A和B之间"
  ],
  "closure_strength_after": "weak|open"
}}"""


def get_asymmetry_prompt(
    paragraphs: List[str],
    expand_index: int,
    compress_indices: List[int]
) -> str:
    """
    Generate prompt for creating asymmetric paragraph depth
    生成创建非对称段落深度的提示词

    Args:
        paragraphs: All paragraph texts 所有段落文本
        expand_index: Index of paragraph to expand 要扩展的段落索引
        compress_indices: Indices of paragraphs to compress 要压缩的段落索引

    Returns:
        Prompt for asymmetry creation 非对称创建提示词
    """
    expand_para = paragraphs[expand_index]
    compress_paras = [(i, paragraphs[i]) for i in compress_indices if i < len(paragraphs)]

    compress_text = "\n\n".join([
        f"[Paragraph {i+1} to COMPRESS]\n{p}" for i, p in compress_paras
    ])

    return f"""You are an expert at creating intentional asymmetry in academic writing.

TASK: Create asymmetric depth - expand one key paragraph and compress others.

[Paragraph {expand_index + 1} to EXPAND (target: 150% of current length)]
{expand_para}

{compress_text}

EXPANSION STRATEGIES for Paragraph {expand_index + 1}:
1. Add deeper analysis of implications
2. Include a concrete example or case
3. Discuss edge cases or boundary conditions
4. Add comparison with alternative approaches
5. Elaborate on mechanism or process

COMPRESSION STRATEGIES for marked paragraphs (target: 60% of current length):
1. Merge redundant sentences
2. Remove obvious elaborations
3. Keep only essential claims
4. Use more concise academic phrasing

REQUIREMENTS:
1. Expanded paragraph should add SUBSTANTIVE content, not padding
2. Compressed paragraphs should retain core meaning
3. Create INTENTIONAL imbalance (this is the goal!)
4. Maintain academic tone throughout

Respond in JSON format:
{{
  "expanded_paragraph": {{
    "index": {expand_index},
    "original_word_count": ...,
    "new_word_count": ...,
    "content": "The expanded paragraph...",
    "additions": ["What was added"]
  }},
  "compressed_paragraphs": [
    {{
      "index": ...,
      "original_word_count": ...,
      "new_word_count": ...,
      "content": "The compressed paragraph...",
      "removals": ["What was removed"]
    }}
  ],
  "asymmetry_ratio": "e.g., 2.5:1 between longest and shortest",
  "explanation_zh": "非对称处理的说明"
}}"""


def get_structure_prompt(
    strategy: str,
    paragraphs: List[str],
    issues: List[Dict],
    extracted_thesis: Optional[str] = None,
    key_arguments: Optional[List[str]] = None,
    disruption_level: Optional[str] = None,
    predictability_score: Optional[Dict] = None
) -> str:
    """
    Get the appropriate prompt for a given strategy (Enhanced Router)
    获取给定策略的适当提示词（增强路由器）

    Args:
        strategy: Strategy name 策略名称
        paragraphs: List of paragraph texts 段落文本列表
        issues: List of detected issues 检测到的问题列表
        extracted_thesis: Extracted thesis statement 提取的论点陈述
        key_arguments: Extracted key arguments 提取的关键论据
        disruption_level: Optional disruption level for enhanced mode 增强模式的扰动等级
        predictability_score: Optional predictability analysis result 预测性分析结果

    Returns:
        Appropriate prompt for the strategy 策略的适当提示词
    """
    # New enhanced mode with disruption levels
    if strategy == "disruption" or disruption_level:
        return get_disruption_restructure_prompt(
            paragraphs=paragraphs,
            disruption_level=disruption_level or "medium",
            predictability_score=predictability_score,
            extracted_thesis=extracted_thesis
        )

    # Original strategies for backward compatibility
    if strategy == "optimize_connection":
        return get_optimize_connection_prompt(paragraphs, issues, extracted_thesis)
    elif strategy == "deep_restructure":
        return get_deep_restructure_prompt(paragraphs, issues, extracted_thesis, key_arguments)
    elif strategy == "all":
        return get_all_strategies_prompt(paragraphs, issues, extracted_thesis, key_arguments)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
