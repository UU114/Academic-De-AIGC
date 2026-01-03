"""
Paragraph Logic Restructuring Prompts
段落内逻辑重组Prompt模板

For restructuring sentence relationships within a single paragraph to avoid AI detection.
用于重组单个段落内句子之间的关系以规避AI检测。

Strategies:
1. ANI Structure (Assertion-Nuance-Implication)
2. Subject Diversity
3. Implicit Connector
4. Rhythm Variation
"""

from typing import Optional, List, Dict, Any


# =============================================================================
# Strategy Descriptions
# 策略描述
# =============================================================================

STRATEGY_DESCRIPTIONS = {
    "ani": {
        "name": "ANI Structure",
        "name_zh": "ANI结构（断言-细微-深意）",
        "description": "Transform flat additive structure (A+B+C+D) into Assertion→Nuance→Deep Implication pattern. Places conclusion at start or end for emphasis.",
        "description_zh": "将平铺叠加结构(A+B+C+D)转化为 断言→细微差别→深层含义 模式。将结论放在段首或段尾以强调。",
    },
    "subject_diversity": {
        "name": "Subject Diversity",
        "name_zh": "主语多样性",
        "description": "Vary sentence subjects to avoid repetitive patterns. Transform first-person overuse to passive/impersonal constructions.",
        "description_zh": "变换句子主语以避免重复模式。将过度使用的第一人称转换为被动/非人称结构。",
    },
    "implicit_connector": {
        "name": "Implicit Connector",
        "name_zh": "隐性连接",
        "description": "Replace explicit connectors (Furthermore, However) with semantic echo, embedded contrast, or implicature flow.",
        "description_zh": "用语义回声、嵌入式转折或蕴含流替代显性连接词(Furthermore, However等)。",
    },
    "rhythm": {
        "name": "Rhythm Variation",
        "name_zh": "节奏变化",
        "description": "Vary sentence lengths to create human-like rhythm. Mix short punchy sentences with longer explanatory ones.",
        "description_zh": "变化句子长度以创造人类化节奏。混合使用简短有力的句子和较长的解释性句子。",
    },
    "citation_entanglement": {
        "name": "Citation Entanglement",
        "name_zh": "引用句法纠缠",
        "description": "Transform parenthetical citations into narrative citations to break AI pattern. Mix 'Statement (Author, Year)' with 'Author (Year) states...' forms.",
        "description_zh": "将括号引用转换为叙述引用以打破AI模式。混合使用 '陈述 (Author, Year)' 与 'Author (Year) 指出...' 形式。",
    },
}


# =============================================================================
# ANI Structure Prompt
# ANI结构Prompt
# =============================================================================

def get_ani_restructure_prompt(
    paragraph: str,
    detected_issues: Optional[List[Dict[str, Any]]] = None,
    tone_level: int = 4
) -> str:
    """
    Generate prompt for ANI (Assertion-Nuance-Implication) restructuring
    生成ANI结构重组的Prompt

    The ANI structure breaks AI-like linear patterns by:
    - Starting with a strong assertion (or placing it at end for emphasis)
    - Adding nuance/concession to show intellectual depth
    - Concluding with deeper implications beyond the obvious
    """
    issues_text = ""
    if detected_issues:
        issues_text = "\n## Detected Issues\n" + "\n".join([
            f"- {issue.get('type', 'unknown')}: {issue.get('description', '')}"
            for issue in detected_issues
        ])

    return f"""## Task: Restructure paragraph using ANI pattern (Assertion-Nuance-Implication)

You are an expert at making AI-generated academic text appear human-written.

## Original Paragraph (showing linear AI-like structure):
{paragraph}
{issues_text}

## ANI Pattern Explanation

Transform the flat "A + B + C + D" additive structure into a more sophisticated pattern:

**ASSERTION (断言)**: A strong, direct claim. NO hedging here.
- Place at paragraph START (conventional) or END (for emphasis/surprise)
- State the core finding/claim directly and confidently
- Example: "X fundamentally determines Y."
- Example: "The evidence points to a single conclusion: Z shapes everything."

**NUANCE (细微差别/让步)**: Acknowledge complexity, conditions, or counter-evidence.
- Shows intellectual honesty and depth
- Creates tension that makes the argument more compelling
- Example: "Yet this relationship holds only under condition Z."
- Example: "The mechanism, however, operates selectively—not all cases fit."
- Example: "A closer look reveals exceptions: when A occurs, B falters."

**DEEP IMPLICATION (深层含义)**: What this means beyond the obvious.
- Connect to broader significance, theory, or practice
- Move from specific finding to general principle
- Example: "The implication extends beyond X—it suggests a paradigm shift."
- Example: "Such patterns point to a deeper principle at work."
- Example: "What emerges is not just Y, but a fundamental rethinking of Z."

## Structure Options

Option A (Assertion First):
1. ASSERTION: Strong claim
2. NUANCE: Conditions/exceptions
3. IMPLICATION: Deeper meaning

Option B (Assertion Last - for emphasis):
1. Context/Setup
2. NUANCE: Complications discovered
3. ASSERTION: Surprising conclusion

## Constraints:
- REMOVE explicit connectors (Furthermore, Moreover, Additionally, However, Therefore)
- VARY sentence lengths (mix short 8-12 words with long 20-30 words)
- VARY subjects across sentences (avoid "The X... The X... The X...")
- MAINTAIN academic precision and meaning
- PRESERVE all technical terms and data
- Tone level: {tone_level}/10 (0=formal academic, 10=casual)

## Output (JSON only, no markdown):
{{
    "restructured": "The complete rewritten paragraph using ANI structure",
    "structure_map": ["assertion", "nuance", "implication"],
    "assertion_position": "start" or "end",
    "changes_made": [
        {{"type": "removed_connector", "original": "Furthermore,", "result": "This pattern..."}},
        {{"type": "added_nuance", "description": "Added concession about exceptions"}},
        {{"type": "reordered", "description": "Moved conclusion to paragraph end"}}
    ],
    "explanation": "Brief explanation of restructuring approach",
    "explanation_zh": "重组方法的简要解释"
}}"""


# =============================================================================
# Subject Diversity Prompt
# 主语多样性Prompt
# =============================================================================

def get_subject_diversity_prompt(
    paragraph: str,
    repeated_subject: str,
    count: int,
    total: int,
    positions: Optional[List[int]] = None
) -> str:
    """
    Generate prompt for subject diversity restructuring
    生成主语多样性重组的Prompt

    Addresses the AI pattern of repeating the same subject across sentences.
    """
    positions_text = f" (at positions: {positions})" if positions else ""

    return f"""## Task: Diversify sentence subjects to avoid AI-like repetition

You are an expert at making AI-generated academic text appear human-written.

## Original Paragraph with repetitive subjects:
{paragraph}

## Detected Issue:
Subject "{repeated_subject}" appears in {count}/{total} sentences ({count/total:.0%}){positions_text}

## Subject Variation Strategies

### 1. Demonstrative Reference (指示代词)
Transform repeated subject to demonstrative:
- "The model..." → "This approach...", "Such methods...", "These findings..."
- "The results..." → "This pattern...", "Such outcomes..."

### 2. Concept Nominalization (概念名词化)
Turn verbs/adjectives into noun subjects:
- "We found that X improves Y" → "The improvement in Y..."
- "The model is accurate" → "This accuracy..."
- "We analyzed the data" → "Analysis of the data..."

### 3. Passive Transformation (被动转换) - use sparingly (max 2 consecutive)
- "We analyzed X" → "X was analyzed" or "The analysis reveals..."
- "I believe X" → "Evidence suggests X" or "It appears that X"
- "We found that" → "The data reveals..." or "Findings indicate..."

### 4. Implication/Result Subjects (结果/含义主语)
Focus on consequences rather than actors:
- "The results show..." → "The implication of these results..."
- "We discovered..." → "What emerges from this analysis..."

### 5. Condition/Context Subjects (条件/背景主语)
Start with circumstances:
- "The method works..." → "Under these conditions, accuracy..."
- "We tested..." → "Testing across three datasets reveals..."

### 6. Aspect Subjects (方面主语)
Focus on specific aspects:
- "The model..." → "Its precision...", "This capability...", "Such robustness..."

## Constraints:
- KEEP meaning identical to original
- PRESERVE all technical terms and data
- DO NOT over-use passive voice (max 2 consecutive passive sentences)
- MAINTAIN academic register
- Aim for NO repeated subject in consecutive sentences

## Output (JSON only, no markdown):
{{
    "restructured": "Paragraph with varied subjects",
    "subject_sequence": ["The approach", "This capability", "Such precision", "Evidence", "The implication"],
    "transformations": [
        {{"sentence_index": 0, "from": "The model", "to": "This approach", "strategy": "demonstrative"}},
        {{"sentence_index": 2, "from": "We found", "to": "Evidence suggests", "strategy": "passive_alternative"}}
    ],
    "explanation": "Strategies applied for subject variation",
    "explanation_zh": "主语变换策略说明"
}}"""


# =============================================================================
# Implicit Connector Prompt
# 隐性连接Prompt
# =============================================================================

def get_implicit_connector_prompt(
    paragraph: str,
    connectors_found: List[Dict[str, Any]],
    tone_level: int = 4
) -> str:
    """
    Generate prompt for implicit connector restructuring
    生成隐性连接重组的Prompt

    Replaces explicit connectors with semantic flow, embedded structures,
    and implicature.
    """
    connectors_text = ", ".join([
        f"'{c.get('connector', '')}' (sentence {c.get('index', '?')})"
        for c in connectors_found
    ])

    return f"""## Task: Replace explicit connectors with implicit semantic flow

You are an expert at making AI-generated academic text appear human-written.

## Original Paragraph with connector overuse:
{paragraph}

## Detected Explicit Connectors:
{connectors_text}

## Implicit Connection Strategies

### 1. Semantic Echo (语义回声)
Echo a key concept from the previous sentence instead of using a connector:

BAD (explicit): "X is effective. Furthermore, Y is also useful."
GOOD (echo): "X is effective. This effectiveness extends to Y as well."

BAD: "The model improves accuracy. Moreover, it reduces errors."
GOOD: "The model improves accuracy. Such precision gains translate to fewer errors."

### 2. Embedded Contrast (嵌入式转折)
Embed the contrast within the sentence structure instead of starting with "However":

BAD: "X works well. However, limitations exist."
GOOD: "X works well—though not without limitations."
GOOD: "Limitations, however, temper these gains." (connector mid-sentence)
GOOD: "X works well. Limitations do exist."

### 3. Implicature Flow (蕴含流)
Let the logical conclusion emerge naturally without "Therefore":

BAD: "X leads to Y. Therefore, we conclude Z."
GOOD: "X leads to Y. Such patterns point to Z."
GOOD: "X leads to Y. Z emerges as the logical consequence."
GOOD: "X leads to Y—and Z follows naturally."

### 4. Question-Answer Echo (问答呼应)
End one sentence with implicit question, start next with answer:

GOOD: "X raises questions about causation. The underlying mechanism involves..."
GOOD: "Why does X occur? The answer lies in Y."

### 5. Parallel Structure Without Connectors (无连接词并列)
Use punctuation and structure instead of additive connectors:

BAD: "A is true. Additionally, B is true. Furthermore, C is true."
GOOD: "A is true; B reinforces this; C confirms the pattern."
GOOD: "A is true. B amplifies it. C seals the case."

## Constraints:
- PRESERVE logical relationships (just make them implicit)
- MAINTAIN academic precision
- DO NOT change the meaning
- Tone level: {tone_level}/10
- Some connectors at mid-sentence position are acceptable

## Output (JSON only, no markdown):
{{
    "restructured": "Paragraph with implicit connections replacing explicit connectors",
    "connector_replacements": [
        {{"original": "Furthermore,", "strategy": "semantic_echo", "result": "This pattern extends to..."}},
        {{"original": "However,", "strategy": "embedded_contrast", "result": "Limitations, though, temper..."}}
    ],
    "preserved_connectors": ["list of any connectors kept and why"],
    "explanation": "How implicit connections were created",
    "explanation_zh": "隐性连接的创建方式"
}}"""


# =============================================================================
# Rhythm Variation Prompt
# 节奏变化Prompt
# =============================================================================

def get_rhythm_variation_prompt(
    paragraph: str,
    lengths: List[int],
    cv: float,
    tone_level: int = 4
) -> str:
    """
    Generate prompt for rhythm/length variation restructuring
    生成节奏/长度变化重组的Prompt

    Creates human-like sentence length variation to break AI uniformity.
    """
    return f"""## Task: Vary sentence length and rhythm for human-like flow

You are an expert at making AI-generated academic text appear human-written.

## Original Paragraph with uniform sentence lengths:
{paragraph}

## Detected Issue:
Current sentence lengths: {lengths}
Coefficient of variation: {cv:.2f} (too uniform, target CV > 0.30)
Mean length: {sum(lengths)/len(lengths):.1f} words

## Rhythm Pattern Targets

### Target Pattern: LONG → SHORT → MEDIUM (repeat with variation)

**LONG sentences (20-30 words)**: Build context, explain mechanisms, establish background
- Use for: introducing topics, explaining processes, providing evidence
- May contain subclauses, em-dashes, semicolons
- Example: "The experimental results, spanning three datasets and two methodologies, consistently demonstrate significant improvements in both precision and recall metrics."

**SHORT sentences (8-12 words)**: Deliver punch, state key findings, create emphasis
- Use for: conclusions, key claims, transitions
- Simple structure, no subclauses
- Example: "Precision matters here."
- Example: "The pattern holds."
- Example: "This changes everything."

**MEDIUM sentences (15-20 words)**: Develop nuance, provide transitions, add detail
- Use for: elaboration, qualifications, linking ideas
- Example: "These gains, however, diminish when noise levels exceed the critical threshold."

## Techniques for Length Variation

### 1. Sentence Splitting (拆分长句)
BAD: "X is important because of Y which leads to Z and ultimately results in W."
GOOD: "X is important. Y drives this. Z follows—and W results."

### 2. Sentence Merging (合并短句)
BAD: "X exists. Y exists. Both are related."
GOOD: "X and Y coexist, each reinforcing the other through shared mechanisms."

### 3. Emphatic Fragments (强调性短句)
Add short punchy sentences for emphasis:
- "This matters."
- "The key insight: X."
- "Not so for Y."

### 4. Complex Context Sentences (复杂背景句)
Create longer sentences with multiple elements:
- Use em-dashes for parenthetical additions
- Use semicolons to link related clauses
- Include prepositional phrases for detail

## Constraints:
- MAINTAIN meaning and accuracy
- PRESERVE technical terms
- Target CV > 0.30 in output
- Tone level: {tone_level}/10
- Avoid creating grammatically awkward sentences for length's sake

## Output (JSON only, no markdown):
{{
    "restructured": "Paragraph with varied sentence rhythm",
    "new_lengths": [23, 8, 17, 12, 25],
    "new_cv": 0.35,
    "rhythm_pattern": ["long", "short", "medium", "short", "long"],
    "techniques_used": [
        {{"type": "split", "description": "Split sentence 2 into two shorter sentences"}},
        {{"type": "merge", "description": "Combined sentences 4 and 5"}},
        {{"type": "emphatic", "description": "Added short emphatic sentence after main claim"}}
    ],
    "explanation": "How rhythm variation was achieved",
    "explanation_zh": "节奏变化的实现方式"
}}"""


# =============================================================================
# Combined/All Strategies Prompt
# 综合策略Prompt
# =============================================================================

def get_all_strategies_prompt(
    paragraph: str,
    detected_issues: List[Dict[str, Any]],
    tone_level: int = 4
) -> str:
    """
    Generate prompt to apply all relevant strategies at once
    生成一次性应用所有相关策略的Prompt

    More efficient when paragraph has multiple issues.
    """
    issues_text = "\n".join([
        f"- [{issue.get('type', 'unknown')}] {issue.get('description', '')} (Severity: {issue.get('severity', 'unknown')})"
        for issue in detected_issues
    ])

    return f"""## Task: Comprehensively restructure paragraph to pass AI detection

You are an expert at making AI-generated academic text appear human-written.

## Original Paragraph:
{paragraph}

## Detected Issues:
{issues_text}

## Apply ALL Relevant Strategies:

### 1. ANI Structure (if linear_structure issue detected)
Transform: A + B + C + D → Assertion → Nuance → Implication
- Strong assertion (start or end)
- Acknowledge complexity/conditions
- Deeper implications

### 2. Subject Diversity (if subject_repetition issue detected)
Strategies:
- Demonstratives: "This approach...", "Such methods..."
- Nominalizations: "The improvement...", "This accuracy..."
- Passive alternatives: "Evidence suggests...", "The data reveals..."

### 3. Implicit Connectors (if connector_overuse/linear_structure detected)
Replace:
- "Furthermore" → "This pattern extends to..."
- "However" → embedded contrast: "X, though, complicates..."
- "Therefore" → "Such evidence points to..."

### 4. Rhythm Variation (if uniform_length detected)
Create:
- LONG (20-30 words): context/explanation
- SHORT (8-12 words): punch/emphasis
- MEDIUM (15-20 words): nuance/transition

### 5. Hedging/Conviction Balance
Mix:
- Hedging: "may contribute", "appears to", "suggests"
- Conviction: "clearly demonstrates", "definitively shows"

### 6. Intentional Imperfection (有意的不完美)
Human writers are NOT perfect. Add these human-like markers:

**Conjunction Starters** (偶尔连词开头 - 10-15% of sentences):
- Start some sentences with And, But, Or, So for rhythmic effect
- Example: "And this changes the picture entirely."
- Example: "But the data tells a different story."

**Em-Dash Interruptions** (破折号打断):
- Insert abrupt thoughts using em-dashes (—)
- Example: "The model performs well—surprisingly well, actually—under stress."
- Example: "Results indicate—and this was unexpected—a reversal."

**Slight Grammatical Looseness** (略松散的语法):
- Use sentence fragments for emphasis occasionally
- Start with "Which is why..." or "Because..." as standalone sentences
- Example: "Which is why this matters."
- Example: "A significant finding. One that changes everything."

**Avoid Textbook Perfection** (避免教科书式完美):
- Mix sentence structures irregularly
- Allow occasional informal phrasing within academic context
- Example: "The results are, frankly, remarkable."
- Example: "This, to put it simply, works."

## Constraints:
- REMOVE all sentence-initial explicit connectors
- NO repeated subjects in consecutive sentences
- Target sentence length CV > 0.30
- PRESERVE meaning, technical terms, and data
- Tone level: {tone_level}/10

## Output (JSON only, no markdown):
{{
    "restructured": "The complete rewritten paragraph",
    "strategies_applied": ["ani", "subject_diversity", "implicit_connector", "rhythm"],
    "structure_summary": {{
        "logic_pattern": "assertion→nuance→implication",
        "subject_sequence": ["The approach", "This capability", "Evidence"],
        "length_pattern": [25, 10, 18, 8, 22],
        "connectors_removed": ["Furthermore", "However"]
    }},
    "changes_summary": [
        {{"category": "structure", "change": "Reordered to ANI pattern"}},
        {{"category": "subject", "change": "Varied subjects across sentences"}},
        {{"category": "connector", "change": "Replaced 3 explicit connectors"}},
        {{"category": "rhythm", "change": "Created long→short→medium pattern"}}
    ],
    "explanation": "Comprehensive explanation of all changes",
    "explanation_zh": "所有改动的综合说明"
}}"""


# =============================================================================
# Citation Entanglement Strategy
# 引用句法纠缠策略
# =============================================================================

def get_citation_entanglement_prompt(
    paragraph: str,
    citations_found: List[Dict[str, Any]],
    tone_level: int = 4
) -> str:
    """
    Generate prompt for citation entanglement restructuring
    生成引用句法纠缠重组的Prompt

    Transforms parenthetical citations into narrative citations
    to break the AI pattern of "Statement + (Citation)"
    将括号引用转换为叙述引用以打破AI的"陈述+(引用)"模式

    Args:
        paragraph: Text with citations
        citations_found: List of detected citations, each with 'original' and 'position'
        tone_level: Writing style level (0-10)

    Returns:
        Formatted prompt for LLM
    """
    citations_text = "\n".join([
        f"- \"{c.get('original', '')}\" at position {c.get('position', '?')}"
        for c in citations_found
    ]) if citations_found else "No specific citations detected"

    return f"""## Task: Transform citations to break AI pattern

You are an expert at making AI-generated academic text appear human-written.

## Original Paragraph:
{paragraph}

## Detected Parenthetical Citations:
{citations_text}

## Citation Entanglement Strategies

### 1. Narrative Citation Transformation (叙述引用转换)
Transform parenthetical citations into sentence subjects:

BEFORE (AI pattern): "This phenomenon has been observed in multiple studies (Smith, 2023)."
AFTER (human pattern): "Smith (2023) observed this phenomenon across multiple studies."

BEFORE: "The framework is widely adopted (Jones et al., 2022; Wang, 2021)."
AFTER: "As Jones et al. (2022) noted, and Wang (2021) subsequently confirmed, the framework..."

### 2. Citation as Authority (引用作为权威)
Let the citation drive the sentence:
- "According to Smith (2023), this behavior..."
- "Smith (2023) argues that..."
- "Following Wang's (2021) framework,..."
- "As demonstrated by Chen et al. (2022),..."

### 3. Embedded Citation (嵌入式引用)
Weave citations naturally into sentences:
- "Smith's (2023) groundbreaking study revealed..."
- "The methodology proposed by Jones et al. (2022) suggests..."
- "In their seminal work, Wang and Chen (2021) established..."

### 4. Citation Dialogue (引用对话)
Create scholarly conversation:
- "While Smith (2023) proposed X, Jones (2022) offered an alternative..."
- "Building on Chen's (2020) foundation, recent work by Wang (2023)..."

## Rules:
- Transform approximately 30% of parenthetical citations to narrative form
- Preserve ALL citation information (authors, year, page numbers if any)
- Maintain academic accuracy and proper citation format
- Mix citation styles for natural variation
- Keep some parenthetical citations (do NOT transform all)
- Tone level: {tone_level}/10

## Output (JSON only, no markdown):
{{
    "restructured": "Paragraph with varied citation styles",
    "transformations": [
        {{"original": "(Smith, 2023)", "new_form": "Smith (2023) argues that", "strategy": "narrative"}},
        {{"original": "(Jones et al., 2022)", "new_form": "As Jones et al. (2022) demonstrated", "strategy": "authority"}}
    ],
    "citations_transformed": 2,
    "citations_kept_parenthetical": 3,
    "explanation": "How citations were restructured",
    "explanation_zh": "引用重组方式说明"
}}"""


# =============================================================================
# Prompt Selector
# Prompt选择器
# =============================================================================

STRATEGY_PROMPTS = {
    "ani": get_ani_restructure_prompt,
    "subject_diversity": get_subject_diversity_prompt,
    "implicit_connector": get_implicit_connector_prompt,
    "rhythm": get_rhythm_variation_prompt,
    "citation_entanglement": get_citation_entanglement_prompt,
    "all": get_all_strategies_prompt,
}


def get_paragraph_logic_prompt(
    strategy: str,
    paragraph: str,
    **kwargs
) -> str:
    """
    Get the appropriate prompt for the specified strategy
    获取指定策略的Prompt

    Args:
        strategy: One of "ani", "subject_diversity", "implicit_connector", "rhythm", "all"
        paragraph: The paragraph text to restructure
        **kwargs: Additional arguments for specific strategies

    Returns:
        Formatted prompt string
    """
    if strategy not in STRATEGY_PROMPTS:
        raise ValueError(
            f"Unknown strategy: {strategy}. "
            f"Must be one of: {list(STRATEGY_PROMPTS.keys())}"
        )

    prompt_generator = STRATEGY_PROMPTS[strategy]

    # Handle different argument patterns for each strategy
    # 处理每个策略的不同参数模式
    if strategy == "ani":
        return prompt_generator(
            paragraph,
            detected_issues=kwargs.get("detected_issues"),
            tone_level=kwargs.get("tone_level", 4)
        )
    elif strategy == "subject_diversity":
        return prompt_generator(
            paragraph,
            repeated_subject=kwargs.get("repeated_subject", "unknown"),
            count=kwargs.get("count", 0),
            total=kwargs.get("total", 0),
            positions=kwargs.get("positions")
        )
    elif strategy == "implicit_connector":
        return prompt_generator(
            paragraph,
            connectors_found=kwargs.get("connectors_found", []),
            tone_level=kwargs.get("tone_level", 4)
        )
    elif strategy == "rhythm":
        return prompt_generator(
            paragraph,
            lengths=kwargs.get("lengths", []),
            cv=kwargs.get("cv", 0.0),
            tone_level=kwargs.get("tone_level", 4)
        )
    elif strategy == "citation_entanglement":
        return prompt_generator(
            paragraph,
            citations_found=kwargs.get("citations_found", []),
            tone_level=kwargs.get("tone_level", 4)
        )
    elif strategy == "all":
        return prompt_generator(
            paragraph,
            detected_issues=kwargs.get("detected_issues", []),
            tone_level=kwargs.get("tone_level", 4)
        )

    return prompt_generator(paragraph, **kwargs)
