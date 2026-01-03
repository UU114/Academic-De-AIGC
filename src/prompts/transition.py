"""
Transition Prompts for Level 2 De-AIGC
Level 2 De-AIGC 过渡策略Prompt

Phase 3: Three transition strategies to break AI-like paragraph connections
Phase 3：三种过渡策略，打破AI风格的段落衔接

Strategies:
1. Semantic Echo (语义回声) - Use key concepts from para_a in para_b opening
2. Logical Hook (逻辑设问) - Use question or problem-solution pattern
3. Rhythm Break (节奏打断) - Break uniform rhythm with varied structure
"""

from typing import Optional, Dict, Any

# Strategy descriptions for reference
# 策略描述供参考
STRATEGY_DESCRIPTIONS = {
    "semantic_echo": {
        "name": "Semantic Echo",
        "name_zh": "语义回声",
        "description": "Remove explicit connector and use a key concept or phrase from the previous paragraph naturally in the next paragraph's opening. This creates an implicit semantic link without formulaic connectors.",
        "description_zh": "移除显性连接词，在下一段开头自然地使用前一段的关键概念或短语。这样可以建立隐式语义链接，而不使用公式化连接词。",
    },
    "logical_hook": {
        "name": "Logical Hook",
        "name_zh": "逻辑设问",
        "description": "End the previous paragraph with an implicit question or tension, then start the next paragraph by addressing it. This creates reader curiosity and natural flow.",
        "description_zh": "在前一段末尾留下隐含问题或张力，然后在下一段开头进行回应。这样可以制造读者好奇心和自然的阅读流程。",
    },
    "rhythm_break": {
        "name": "Rhythm Break",
        "name_zh": "节奏打断",
        "description": "Vary sentence length and structure between paragraph ending and opening. Break the uniform AI rhythm by using different sentence patterns (short after long, simple after complex, etc.).",
        "description_zh": "在段落结尾和开头之间变化句子长度和结构。通过使用不同的句型模式（长句后短句、复杂后简单等）打破均匀的AI节奏。",
    },
}


def get_semantic_echo_prompt(
    para_a_ending: str,
    para_b_opening: str,
    context_hint: Optional[str] = None
) -> str:
    """
    Generate prompt for Semantic Echo strategy
    生成语义回声策略的Prompt

    This strategy removes explicit connectors and creates semantic continuity
    by echoing key concepts from paragraph A in paragraph B's opening.
    """
    context_section = f"""
## Core Thesis/Context (for reference)
{context_hint}
""" if context_hint else ""

    return f"""You are an academic writing advisor helping to improve paragraph transitions.

## Task: Semantic Echo Transition
Remove any explicit connectors (like "Furthermore", "Moreover", "However") and create a natural semantic link by echoing key concepts from the previous paragraph.

## Input
### Previous Paragraph Ending:
{para_a_ending}

### Current Paragraph Opening:
{para_b_opening}
{context_section}

## Strategy: Semantic Echo (语义回声)
1. Identify 1-2 key concepts from the previous paragraph ending
2. Remove explicit connectors from the current paragraph opening
3. Weave the key concepts naturally into the new opening
4. Maintain the original meaning and academic tone

## Constraints
- DO NOT use explicit transition words: Furthermore, Moreover, However, Additionally, Consequently, Therefore, Thus, Hence, Nevertheless, In addition, As a result
- The revised opening should flow naturally from the previous content
- Preserve all technical terms and domain-specific vocabulary
- Keep the academic register appropriate for journal papers

## Response Format (JSON)
{{
    "para_a_ending": "The original or slightly modified ending (only if needed for better flow)",
    "para_b_opening": "The revised opening without explicit connectors",
    "key_concepts_echoed": ["concept1", "concept2"],
    "changes_made": ["Removed 'Furthermore'", "Echoed 'statistical significance'"],
    "explanation_zh": "中文解释修改原因"
}}"""


def get_logical_hook_prompt(
    para_a_ending: str,
    para_b_opening: str,
    context_hint: Optional[str] = None
) -> str:
    """
    Generate prompt for Logical Hook strategy
    生成逻辑设问策略的Prompt

    This strategy creates reader curiosity by ending paragraph A with
    an implicit question or tension, then addressing it in paragraph B.
    """
    context_section = f"""
## Core Thesis/Context (for reference)
{context_hint}
""" if context_hint else ""

    return f"""You are an academic writing advisor helping to improve paragraph transitions.

## Task: Logical Hook Transition
Create reader curiosity by establishing an implicit question or tension at the end of the previous paragraph, then address it at the start of the next paragraph.

## Input
### Previous Paragraph Ending:
{para_a_ending}

### Current Paragraph Opening:
{para_b_opening}
{context_section}

## Strategy: Logical Hook (逻辑设问)
1. Modify the paragraph ending to hint at an unresolved question or tension
2. Remove explicit connectors from the current paragraph opening
3. Start the next paragraph by addressing or exploring that tension
4. The "hook" should be implicit, not an explicit question

## Techniques
- End with observation that implies "but why?" or "what does this mean?"
- Use phrases like "This raises an important consideration..." or "Yet the mechanism remains..."
- Start next paragraph by addressing the implied question naturally
- Avoid rhetorical questions - keep the academic tone

## Constraints
- DO NOT use explicit transition words: Furthermore, Moreover, However, Additionally, etc.
- The hook should be subtle, not an obvious cliffhanger
- Maintain academic formality and precision
- Preserve technical accuracy

## Response Format (JSON)
{{
    "para_a_ending": "Modified ending with subtle hook/tension",
    "para_b_opening": "Opening that naturally addresses the hook",
    "hook_type": "implication|observation|limitation|extension",
    "changes_made": ["Added implicit question about mechanism", "Removed 'However'"],
    "explanation_zh": "中文解释修改原因"
}}"""


def get_rhythm_break_prompt(
    para_a_ending: str,
    para_b_opening: str,
    context_hint: Optional[str] = None
) -> str:
    """
    Generate prompt for Rhythm Break strategy
    生成节奏打断策略的Prompt

    This strategy varies sentence length and structure to break
    the uniform AI rhythm typically found in generated text.
    """
    context_section = f"""
## Core Thesis/Context (for reference)
{context_hint}
""" if context_hint else ""

    return f"""You are an academic writing advisor helping to improve paragraph transitions.

## Task: Rhythm Break Transition
Break the uniform AI-like rhythm by varying sentence structure and length between the paragraph ending and opening.

## Input
### Previous Paragraph Ending:
{para_a_ending}

### Current Paragraph Opening:
{para_b_opening}
{context_section}

## Strategy: Rhythm Break (节奏打断)
1. Analyze the current sentence patterns (length, complexity, structure)
2. Create variation: if ending is long → start short; if complex → start simple
3. Remove explicit connectors and formulaic openers
4. Vary sentence structure (active/passive, simple/compound, etc.)

## Rhythm Patterns to Create
- Long sentence (20+ words) → Short sentence (8-12 words)
- Complex with clauses → Simple declarative
- Passive voice → Active voice
- Abstract statement → Concrete example or data
- General claim → Specific instance

## Constraints
- DO NOT use explicit transition words: Furthermore, Moreover, However, Additionally, etc.
- DO NOT start with "It is..." or "This section..."
- The variation should feel natural, not abrupt
- Maintain academic precision and meaning

## Response Format (JSON)
{{
    "para_a_ending": "Ending (modified only if needed for rhythm)",
    "para_b_opening": "Opening with varied rhythm",
    "rhythm_change": "long→short|complex→simple|passive→active|abstract→concrete",
    "original_pattern": "description of original pattern",
    "new_pattern": "description of new pattern",
    "changes_made": ["Shortened first sentence", "Changed passive to active"],
    "explanation_zh": "中文解释修改原因"
}}"""


def get_all_strategies_prompt(
    para_a_ending: str,
    para_b_opening: str,
    context_hint: Optional[str] = None
) -> str:
    """
    Generate prompt to get all three strategies at once
    生成一次性获取三种策略的Prompt

    This is more efficient when we want to show all options to the user.
    """
    context_section = f"""
## Core Thesis/Context
{context_hint}
""" if context_hint else ""

    return f"""You are an academic writing advisor helping to improve paragraph transitions to avoid AI-detection patterns.

## Task: Generate Three Transition Options
Provide three different strategies to improve the paragraph transition, removing AI-like explicit connectors and formulaic patterns.

## Input
### Previous Paragraph Ending:
{para_a_ending}

### Current Paragraph Opening:
{para_b_opening}
{context_section}

## Three Strategies to Apply:

### Strategy 1: Semantic Echo (语义回声)
- Remove explicit connectors
- Echo 1-2 key concepts from paragraph A naturally in paragraph B opening
- Create implicit semantic link

### Strategy 2: Logical Hook (逻辑设问)
- End paragraph A with subtle tension or implication
- Start paragraph B by addressing that tension
- Create reader curiosity

### Strategy 3: Rhythm Break (节奏打断)
- Vary sentence length and structure
- If ending is long/complex, make opening short/simple (or vice versa)
- Break uniform AI rhythm

## Constraints for ALL strategies
- NEVER use: Furthermore, Moreover, However, Additionally, Consequently, Therefore, Thus, Hence, Nevertheless, In addition, As a result, It is important to note
- NEVER start with: "This section", "It should be noted", "Having discussed"
- Maintain academic tone and precision
- Preserve all technical terms and meaning

## Response Format (JSON)
{{
    "semantic_echo": {{
        "para_a_ending": "modified ending if needed",
        "para_b_opening": "revised opening",
        "key_concepts": ["concept1"],
        "explanation_zh": "解释"
    }},
    "logical_hook": {{
        "para_a_ending": "ending with subtle hook",
        "para_b_opening": "opening addressing hook",
        "hook_type": "implication|observation|limitation",
        "explanation_zh": "解释"
    }},
    "rhythm_break": {{
        "para_a_ending": "ending if modified",
        "para_b_opening": "opening with varied rhythm",
        "rhythm_change": "long→short|complex→simple",
        "explanation_zh": "解释"
    }},
    "recommended_strategy": "semantic_echo|logical_hook|rhythm_break",
    "recommendation_reason_zh": "推荐原因"
}}"""


# Mapping of strategy types to prompt generators
# 策略类型到Prompt生成器的映射
STRATEGY_PROMPTS = {
    "semantic_echo": get_semantic_echo_prompt,
    "logical_hook": get_logical_hook_prompt,
    "rhythm_break": get_rhythm_break_prompt,
    "all": get_all_strategies_prompt,
}


def get_transition_prompt(
    strategy: str,
    para_a_ending: str,
    para_b_opening: str,
    context_hint: Optional[str] = None
) -> str:
    """
    Get the appropriate prompt for the specified strategy
    获取指定策略的Prompt

    Args:
        strategy: One of "semantic_echo", "logical_hook", "rhythm_break", "all"
        para_a_ending: Last 1-2 sentences of paragraph A
        para_b_opening: First 1-2 sentences of paragraph B
        context_hint: Optional core thesis from Level 1

    Returns:
        Formatted prompt string
    """
    prompt_generator = STRATEGY_PROMPTS.get(strategy)
    if not prompt_generator:
        raise ValueError(f"Unknown strategy: {strategy}. Must be one of: {list(STRATEGY_PROMPTS.keys())}")

    return prompt_generator(para_a_ending, para_b_opening, context_hint)
