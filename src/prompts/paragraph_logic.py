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

Analysis Features:
1. Sentence Role Analysis (句子角色分析)
2. Logic Framework Detection (逻辑框架检测)
3. Burstiness Analysis (爆发度分析)
"""

from typing import Optional, List, Dict, Any


# =============================================================================
# Sentence Role Analysis Prompt (Step 2 Enhancement)
# 句子角色分析Prompt（Step 2 增强）
# =============================================================================

SENTENCE_ROLE_ANALYSIS_PROMPT = """## Task: Analyze Sentence Roles and Logic Framework in Academic Paragraph
## 任务：分析学术段落中的句子角色与逻辑框架

You are an expert at analyzing academic writing structure. Analyze the given paragraph to identify the role of each sentence and detect any AI-like rigid framework patterns.

## Paragraph to Analyze:
{paragraph}

## Sentence List (for reference):
{sentence_list}

## STEP 1: Identify Each Sentence's Role (句子角色识别)

Classify each sentence into ONE of these roles:

| Role | English Name | 中文名 | Description |
|------|--------------|--------|-------------|
| CLAIM | Claim/Thesis | 论点/主张 | States the main argument or position |
| EVIDENCE | Evidence | 证据 | Presents data, citations, or factual support |
| ANALYSIS | Analysis | 分析 | Interprets data or explains relationships |
| CRITIQUE | Critique | 批判 | Challenges, questions, or identifies limitations |
| CONCESSION | Concession | 让步 | Acknowledges counter-arguments or complexity |
| SYNTHESIS | Synthesis | 综合 | Integrates multiple ideas or perspectives |
| TRANSITION | Transition | 过渡 | Bridges between ideas or sections |
| CONTEXT | Context | 背景 | Provides background or situates the topic |
| IMPLICATION | Implication | 含义推导 | Draws broader conclusions or significance |
| ELABORATION | Elaboration | 展开细化 | Adds details to a previous point |

## STEP 2: Detect Logic Framework Pattern (逻辑框架检测)

Identify the overall framework pattern:

### AI-Like Rigid Patterns (AI式刚性模式) - HIGH RISK:
- **LINEAR_TEMPLATE**: Context→Evidence→Analysis→Conclusion (线性模板)
- **ADDITIVE_STACK**: Point A + Point B + Point C + Point D (叠加堆砌)
- **UNIFORM_RHYTHM**: All sentences serve similar roles (角色均匀分布)

### Human-Like Dynamic Patterns (人类化动态模式) - LOW RISK:
- **ANI_STRUCTURE**: Assertion→Nuance→Implication (断言-细微-含义)
- **CRITICAL_DEPTH**: Claim↔Critique→Synthesis (批判深度)
- **NON_LINEAR**: Starts with critique/question, backtracks to evidence (非线性)
- **VARIED_RHYTHM**: Mix of short assertions and long elaborations (节奏变化)

## STEP 3: Analyze Burstiness (爆发度分析)

Evaluate sentence length variation pattern:
- Calculate length of each sentence (words)
- Identify rhythm pattern: Is there dramatic variation (long→short→long)?
- Human writing has HIGH burstiness (长短句交替明显)
- AI writing has LOW burstiness (句子长度均匀)

## STEP 4: Generate Improvement Suggestions (改进建议)

If AI-like patterns detected, suggest specific improvements:
1. Which sentences could be reordered?
2. Which roles are missing (e.g., no CRITIQUE)?
3. Where could non-linear thinking be injected?
4. How to increase length variation?

## Output (JSON only, no markdown):
{{
    "sentence_roles": [
        {{"index": 0, "role": "CONTEXT", "role_zh": "背景", "confidence": 0.9, "brief": "Sets up the research problem"}},
        {{"index": 1, "role": "CLAIM", "role_zh": "论点", "confidence": 0.85, "brief": "States main argument"}},
        {{"index": 2, "role": "EVIDENCE", "role_zh": "证据", "confidence": 0.95, "brief": "Cites supporting data"}}
    ],
    "role_distribution": {{
        "CLAIM": 1,
        "EVIDENCE": 2,
        "ANALYSIS": 1,
        "CRITIQUE": 0,
        "other": 1
    }},
    "logic_framework": {{
        "pattern": "LINEAR_TEMPLATE",
        "pattern_zh": "线性模板",
        "is_ai_like": true,
        "risk_level": "high",
        "description": "Follows rigid Context→Evidence→Analysis→Conclusion structure",
        "description_zh": "遵循刚性的 背景→证据→分析→结论 结构"
    }},
    "burstiness_analysis": {{
        "sentence_lengths": [22, 25, 23, 21, 24],
        "mean_length": 23.0,
        "std_dev": 1.58,
        "cv": 0.07,
        "burstiness_level": "low",
        "burstiness_zh": "低（AI特征）",
        "has_dramatic_variation": false,
        "longest_sentence": {{"index": 1, "length": 25}},
        "shortest_sentence": {{"index": 3, "length": 21}}
    }},
    "missing_elements": {{
        "roles": ["CRITIQUE", "CONCESSION"],
        "description": "No critical perspective or acknowledgment of limitations",
        "description_zh": "缺少批判视角或对局限性的承认"
    }},
    "improvement_suggestions": [
        {{
            "type": "add_critique",
            "suggestion": "Add a sentence questioning the evidence or acknowledging limitations",
            "suggestion_zh": "添加质疑证据或承认局限性的句子",
            "priority": 1,
            "example": "However, these findings must be interpreted cautiously given the sample limitations."
        }},
        {{
            "type": "reorder",
            "suggestion": "Start with a provocative question or critique instead of context",
            "suggestion_zh": "以引发思考的问题或批判开头，而非背景",
            "priority": 2,
            "example": "Move sentence 3 (analysis) to the beginning, then backtrack to evidence"
        }},
        {{
            "type": "vary_length",
            "suggestion": "Add a short emphatic sentence after evidence",
            "suggestion_zh": "在证据后添加短促有力的强调句",
            "priority": 2,
            "example": "The pattern is clear."
        }}
    ],
    "overall_assessment": {{
        "ai_risk_score": 75,
        "main_issues": ["linear_structure", "low_burstiness", "missing_critique"],
        "summary": "Paragraph shows typical AI writing patterns: linear structure, uniform sentence lengths, and lacks critical depth",
        "summary_zh": "段落呈现典型AI写作特征：线性结构、句子长度均匀、缺乏批判深度"
    }}
}}
"""


# =============================================================================
# Paragraph Logic Analysis with Sentence Roles (New Function)
# 带句子角色的段落逻辑分析（新函数）
# =============================================================================

def get_sentence_role_analysis_prompt(
    paragraph: str,
    sentences: List[str]
) -> str:
    """
    Generate prompt for sentence role analysis and logic framework detection
    生成句子角色分析和逻辑框架检测的Prompt

    Args:
        paragraph: Full paragraph text
        sentences: List of individual sentences

    Returns:
        Formatted prompt for LLM
    """
    # Build numbered sentence list
    # 构建编号句子列表
    sentence_list = "\n".join([
        f"{i}. [{len(s.split())} words] {s}"
        for i, s in enumerate(sentences)
    ])

    return SENTENCE_ROLE_ANALYSIS_PROMPT.format(
        paragraph=paragraph,
        sentence_list=sentence_list
    )


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
    "document_aware": {
        "name": "Document-Aware Restructure",
        "name_zh": "全篇感知重组",
        "description": "Apply different structure patterns based on paragraph position in the full document (opening/body/closing).",
        "description_zh": "根据段落在全文中的位置（开篇/正文/结尾）应用不同的结构模式。",
    },
    "sentence_fusion": {
        "name": "Sentence Fusion",
        "name_zh": "句子融合",
        "description": "Analyze semantic relationships between sentences. Merge closely related sentences into complex forms (relative clauses, subordinate clauses) while adding short emphatic sentences. LLM judges autonomously.",
        "description_zh": "分析句子间的语义关系。将语义关系密切的句子合并为复杂句式（关系从句、从属从句等），同时添加短句用于强调。由LLM自主判断。",
    },
}


# =============================================================================
# Structure Mode Pool for Document-Aware Restructuring
# 全篇感知重组的结构模式池
# =============================================================================

STRUCTURE_MODES = {
    "opening": {
        "name": "Opening Paragraphs",
        "name_zh": "开篇段落",
        "patterns": ["CPA", "HBT"],  # Context-Problem-Approach, Hook-Background-Thesis
        "length_profile": {
            "mean": 20,
            "cv_target": 0.25,
            "first_sentence": "10-15",  # Hook sentence can be shorter
        },
        "subject_strategy": "domain_nouns",  # Use domain terms as subjects
        "forbidden": ["ANI"],  # Don't make strong assertions too early
        "required_features": ["hook_sentence"],
    },
    "method_body": {
        "name": "Method/Theory Paragraphs",
        "name_zh": "方法/理论段落",
        "patterns": ["DEE", "CME"],  # Definition-Elaboration-Example, Claim-Mechanism-Evidence
        "length_profile": {
            "mean": 25,
            "cv_target": 0.30,
            "min_long_sentences": 2,  # At least 2 sentences >30 words
        },
        "subject_strategy": "method_alternation",  # Alternate method/approach/mechanism
        "forbidden": [],
        "required_features": ["nested_clauses_for_definition"],
    },
    "result_body": {
        "name": "Result/Discussion Paragraphs",
        "name_zh": "结果/讨论段落",
        "patterns": ["ANI", "FCS"],  # Assertion-Nuance-Implication, Finding-Contrast-Synthesis
        "length_profile": {
            "mean": 20,
            "cv_target": 0.38,  # Higher variation
            "min_short_sentences": 1,  # At least 1 emphatic short sentence
        },
        "subject_strategy": "result_chain",  # Results → Data → Implications
        "forbidden": [],
        "required_features": ["emphatic_short_sentence"],
    },
    "closing": {
        "name": "Closing Paragraphs",
        "name_zh": "结尾段落",
        "patterns": ["SLF", "IBC"],  # Summary-Limitation-Future, Implication-Broader-Call
        "length_profile": {
            "mean": 22,
            "cv_target": 0.30,
            "last_sentence": "long",  # End with a long sentence
        },
        "subject_strategy": "abstraction_progression",  # Findings → Implications → Field
        "forbidden": ["end_with_short"],  # Don't end with a short sentence
        "required_features": ["progressive_lengthening"],
    },
}

# Keywords for detecting paragraph type within body
# 用于检测正文段落类型的关键词
BODY_TYPE_KEYWORDS = {
    "method": ["method", "procedure", "approach", "technique", "algorithm", "framework", "model", "design"],
    "result": ["result", "finding", "outcome", "show", "demonstrate", "reveal", "indicate", "observe"],
    "discussion": ["implication", "limitation", "future", "conclude", "suggest", "argue", "interpret"],
}


def _determine_position_type(paragraph_index: int, total_paragraphs: int, content: str) -> str:
    """
    Automatically determine paragraph position type based on index and content
    根据索引和内容自动确定段落位置类型

    Args:
        paragraph_index: 0-based index of current paragraph
        total_paragraphs: Total number of paragraphs in document
        content: Paragraph text content

    Returns:
        Position type: "opening", "method_body", "result_body", "closing"
    """
    content_lower = content.lower()

    # Opening paragraphs
    # 开篇段落
    if paragraph_index == 0:
        return "opening"
    if paragraph_index == 1 and total_paragraphs > 5:
        return "opening"

    # Closing paragraphs
    # 结尾段落
    if paragraph_index == total_paragraphs - 1:
        return "closing"
    if paragraph_index == total_paragraphs - 2 and total_paragraphs > 5:
        return "closing"

    # Body paragraphs - detect subtype by keywords
    # 正文段落 - 通过关键词检测子类型
    method_score = sum(1 for kw in BODY_TYPE_KEYWORDS["method"] if kw in content_lower)
    result_score = sum(1 for kw in BODY_TYPE_KEYWORDS["result"] if kw in content_lower)
    discussion_score = sum(1 for kw in BODY_TYPE_KEYWORDS["discussion"] if kw in content_lower)

    max_score = max(method_score, result_score, discussion_score)

    if max_score == 0:
        # Default to result_body if no clear signal
        # 如果没有明确信号，默认为结果段落
        return "result_body"

    if method_score == max_score:
        return "method_body"
    elif result_score == max_score:
        return "result_body"
    else:
        return "result_body"  # Discussion is treated as result_body


def _get_structure_mode_for_position(position_type: str) -> Dict[str, Any]:
    """
    Get structure mode configuration for a given position type
    获取给定位置类型的结构模式配置

    Args:
        position_type: One of "opening", "method_body", "result_body", "closing"

    Returns:
        Structure mode configuration dictionary
    """
    return STRUCTURE_MODES.get(position_type, STRUCTURE_MODES["result_body"])


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
    Generate prompt for logic-driven rhythm/length variation restructuring
    生成逻辑关系驱动的节奏/长度变化重组Prompt

    Creates human-like sentence length variation based on logical relationships.
    根据逻辑关系创建人类化的句子长度变化。
    """
    return f"""## Task: Plan sentence lengths based on logical relationships
## 任务：根据逻辑关系规划句子长度

You are an expert at making AI-generated academic text appear human-written.
你是让AI生成的学术文本看起来像人类写作的专家。

## Original Paragraph:
{paragraph}

## Current Statistics:
- Sentence lengths: {lengths}
- Coefficient of variation: {cv:.2f} (target CV > 0.30, ideal 0.35-0.45)
- Mean length: {sum(lengths)/len(lengths):.1f} words

## STEP 1: Analyze Logical Relationships (逻辑关系分析)

First, classify each sentence by its logical relationship type:
首先，按逻辑关系类型对每个句子进行分类：

| Type | Description | 描述 |
|------|-------------|------|
| QUALIFICATION_CHAIN | Multiple preconditions linked together | 多个前提条件关联 |
| NESTED_CAUSATION | Multi-level causal chains | 多层因果链 |
| DEFINITION_WITH_BOUNDARY | Definition + scope limitations | 定义+边界限制 |
| CONTRAST_SYNTHESIS | Compare viewpoints + synthesize | 对比观点+综合 |
| EVIDENCE_EXPLANATION | Claim + supporting evidence | 主张+支持证据 |
| TRANSITION_ELABORATION | Independent transition/detail | 独立过渡/细化 |
| CORE_ASSERTION | Simple conclusion/emphasis | 简单结论/强调 |
| THOUGHT_LEAP | Discontinuous logic pivot | 思维跳跃落点 |

## STEP 2: Logic-Length Mapping (逻辑-句长映射)

Apply these MANDATORY mappings based on logical relationship:
根据逻辑关系应用以下强制映射：

### EXTRA LONG (30-50 words) - 逻辑高度紧密
Use nested clauses to maintain conceptual coherence.
使用嵌套从句保持概念连贯。

**QUALIFICATION_CHAIN**: Multiple conditions must be linked
- Grammar: where/provided that/given that/assuming that
- Example: "Under condition A, where B holds and C is satisfied, X produces Y, provided that Z remains constant throughout the experimental procedure."

**NESTED_CAUSATION**: Multi-level causal relationships
- Grammar: which in turn/thereby/leading to/resulting in
- Example: "Because A triggers B, which in turn activates C through mechanism D, the final effect E emerges only when factor F is present in sufficient quantities."

**DEFINITION_WITH_BOUNDARY**: Definition requiring scope specification
- Grammar: defined as/whereby/in that/while
- Example: "X, defined as the process whereby A transforms into B under the influence of C, differs fundamentally from Y in that it requires D while explicitly excluding E."

**CONTRAST_SYNTHESIS**: Viewpoints that must be compared in one flow
- Grammar: while/yet/when considering
- Example: "While Smith argues A based on evidence B, Jones contends C using framework D, yet both ultimately converge on the conclusion that E when considering the broader context of F."

### LONG (20-30 words) - 逻辑中等紧密
Main claims requiring supporting context.
需要补充说明的主要观点。

**EVIDENCE_EXPLANATION**:
- Example: "The results demonstrate X, with effect sizes ranging from A to B across all conditions, suggesting that mechanism C operates through pathway D."

### MEDIUM (15-20 words) - 逻辑适度
Independent transitions or non-core elaborations.
独立过渡或非核心细化。

**TRANSITION_ELABORATION**:
- Example: "This pattern extends to related phenomena in adjacent research domains."
- Example: "The relationship holds primarily under controlled laboratory conditions."

### SHORT (8-14 words) - 逻辑简单/独立
Clear conclusions, emphasis, or pivot points.
清晰结论、强调或转折点。

**CORE_ASSERTION**:
- Example: "The hypothesis was confirmed."
- Example: "Results support this conclusion."
- Example: "This distinction matters."

### EXTRA SHORT (4-8 words) - 戏剧性效果
Maximum 1 per paragraph for critical emphasis.
每段最多1句用于关键强调。

**THOUGHT_LEAP**:
- Example: "The pattern held."
- Example: "A paradox emerges."

## STEP 3: Statistical Validation (统计学验证)

Your output MUST satisfy ALL of these criteria:
你的输出必须满足所有以下标准：

1. **CV Target**: > 0.30 (ideal 0.35-0.45)
2. **Long sentence ratio** (>25 words): 30-40%
3. **Extra long ratio** (>35 words): 10-15%
4. **Short sentence ratio** (<15 words): 20-25%
5. **FORBIDDEN**: 3+ consecutive sentences with similar length (差异<5词)
6. **REQUIRED**: At least one dramatic jump (差异>15词) per 4-5 sentences

## CRITICAL CONSTRAINTS:

### DO NOT SPLIT logically tight sentences (禁止拆分逻辑紧密句子):
- Keep QUALIFICATION_CHAIN, NESTED_CAUSATION, DEFINITION_WITH_BOUNDARY intact
- These MUST remain as extra-long sentences to preserve meaning

### DO MERGE short unrelated sentences when appropriate (适当合并短句):
- Prefer achieving CV through "keep long + add short" NOT "split long"
- 优先通过"保留长句+添加短句"实现CV，而非"拆分长句"

### Grammar tools for extra-long sentences (超长句语法工具):
- Nested relative clauses: which/that/where/whereby
- Participial phrases: involving/mediated by/resulting in
- Conditional chains: provided that/given that/assuming that
- Contrastive conjunctions: while/whereas/yet

## Output (JSON only, no markdown):
{{
    "logic_analysis": [
        {{"sentence_index": 0, "logic_type": "NESTED_CAUSATION", "recommended_length": "30-50"}},
        {{"sentence_index": 1, "logic_type": "CORE_ASSERTION", "recommended_length": "8-14"}}
    ],
    "restructured": "The complete rewritten paragraph with logic-based rhythm",
    "new_lengths": [38, 10, 22, 8, 35],
    "new_cv": 0.42,
    "logic_pattern": ["nested_causation", "core_assertion", "evidence_explanation", "thought_leap", "qualification_chain"],
    "techniques_used": [
        {{"type": "preserve_long", "description": "Kept causal chain sentence intact"}},
        {{"type": "merge_short", "description": "Combined 2 simple facts into one"}},
        {{"type": "add_emphatic", "description": "Added short assertion for emphasis"}}
    ],
    "explanation": "Logic-driven rhythm variation approach",
    "explanation_zh": "逻辑驱动的节奏变化方法"
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
# Document-Aware Restructure Prompt
# 全篇感知重组Prompt
# =============================================================================

def get_document_aware_restructure_prompt(
    paragraph: str,
    paragraph_index: int,
    total_paragraphs: int,
    detected_issues: Optional[List[Dict[str, Any]]] = None,
    tone_level: int = 4
) -> str:
    """
    Generate prompt for document-aware restructuring based on paragraph position
    生成基于段落位置的全篇感知重组Prompt

    Different paragraph positions require different structure patterns:
    - Opening: Context-Problem-Approach, Hook-Background-Thesis
    - Method/Theory: Definition-Elaboration-Example, Claim-Mechanism-Evidence
    - Result/Discussion: Assertion-Nuance-Implication, Finding-Contrast-Synthesis
    - Closing: Summary-Limitation-Future, Implication-Broader-Call
    """
    # Determine position type and get structure mode
    # 确定位置类型并获取结构模式
    position_type = _determine_position_type(paragraph_index, total_paragraphs, paragraph)
    mode = _get_structure_mode_for_position(position_type)

    issues_text = ""
    if detected_issues:
        issues_text = "\n## Detected Issues\n" + "\n".join([
            f"- {issue.get('type', 'unknown')}: {issue.get('description', '')}"
            for issue in detected_issues
        ])

    # Build position-specific instructions
    # 构建位置特定的指令
    position_instructions = _get_position_instructions(position_type, mode)

    return f"""## Task: Restructure paragraph based on document position
## 任务：根据文档位置重组段落

You are an expert at making AI-generated academic text appear human-written.
你是让AI生成的学术文本看起来像人类写作的专家。

## Document Context:
- Paragraph position: {paragraph_index + 1} of {total_paragraphs}
- Position type: {position_type} ({mode['name_zh']})
- Recommended patterns: {', '.join(mode['patterns'])}

## Original Paragraph:
{paragraph}
{issues_text}

{position_instructions}

## Length Profile for {position_type}:
- Target mean length: {mode['length_profile']['mean']} words
- Target CV: {mode['length_profile']['cv_target']}
{_format_length_requirements(mode['length_profile'])}

## Subject Strategy: {mode['subject_strategy']}
{_get_subject_strategy_instructions(mode['subject_strategy'])}

## Required Features:
{_format_required_features(mode['required_features'])}

## Forbidden Patterns:
{_format_forbidden_patterns(mode['forbidden'])}

## Constraints:
- MAINTAIN meaning and academic precision
- PRESERVE all technical terms and data
- VARY sentence lengths according to position profile
- REMOVE explicit connectors (Furthermore, Moreover, etc.)
- Tone level: {tone_level}/10

## Output (JSON only, no markdown):
{{
    "position_type": "{position_type}",
    "pattern_used": "selected pattern from {mode['patterns']}",
    "restructured": "The complete rewritten paragraph",
    "structure_map": ["component1", "component2", "component3"],
    "sentence_lengths": [20, 12, 28, 15, 35],
    "cv_achieved": 0.38,
    "subject_sequence": ["Domain concept", "This approach", "Such mechanisms"],
    "changes_made": [
        {{"type": "structure", "description": "Applied CPA pattern"}},
        {{"type": "subject", "description": "Varied subjects across sentences"}},
        {{"type": "length", "description": "Created hook sentence"}}
    ],
    "explanation": "How position-aware restructuring was applied",
    "explanation_zh": "位置感知重组的应用方式"
}}"""


def _get_position_instructions(position_type: str, mode: Dict[str, Any]) -> str:
    """
    Get position-specific restructuring instructions
    获取位置特定的重组指令
    """
    if position_type == "opening":
        return """## Opening Paragraph Instructions (开篇段落指令)

### Pattern: CPA (Context-Problem-Approach) or HBT (Hook-Background-Thesis)

**CPA Structure:**
1. CONTEXT: Establish the research area and its importance (1-2 sentences)
2. PROBLEM: Identify the gap or challenge (1 sentence)
3. APPROACH: Preview how this work addresses it (1-2 sentences)

**HBT Structure:**
1. HOOK: A compelling opening statement (short, 10-15 words)
2. BACKGROUND: Necessary context for the reader (1-2 longer sentences)
3. THESIS: The main argument or purpose (1 sentence)

**Length Pattern:**
- First sentence: Can be SHORT (10-15 words) as a hook
- Middle sentences: MEDIUM to LONG (18-25 words) for context
- Final sentence: MEDIUM (15-20 words) for thesis/approach

**FORBIDDEN for Opening:**
- Don't use ANI structure (too assertive for introduction)
- Don't start with "In recent years" or similar AI clichés
- Don't use too many short sentences (maintains gravitas)"""

    elif position_type == "method_body":
        return """## Method/Theory Paragraph Instructions (方法/理论段落指令)

### Pattern: DEE (Definition-Elaboration-Example) or CME (Claim-Mechanism-Evidence)

**DEE Structure:**
1. DEFINITION: Clear statement of concept (can be EXTRA LONG with nested clauses)
2. ELABORATION: Expand on components/properties (LONG sentences)
3. EXAMPLE: Concrete illustration (MEDIUM sentence)

**CME Structure:**
1. CLAIM: What the method/theory proposes (MEDIUM to LONG)
2. MECHANISM: How it works (EXTRA LONG with nested clauses)
3. EVIDENCE: Why it's valid (LONG with supporting details)

**Length Pattern:**
- Definition/Mechanism sentences: EXTRA LONG (30-50 words) with nested clauses
- Use: where/whereby/defined as/provided that/given that
- At least 2 sentences must be >30 words
- Example sentences: MEDIUM (15-20 words)

**REQUIRED for Method:**
- Use nested relative clauses for definitions
- Maintain logical tightness - don't split complex definitions
- Subject alternation: "The method... This approach... Such mechanisms..." """

    elif position_type == "result_body":
        return """## Result/Discussion Paragraph Instructions (结果/讨论段落指令)

### Pattern: ANI (Assertion-Nuance-Implication) or FCS (Finding-Contrast-Synthesis)

**ANI Structure:**
1. ASSERTION: Strong, direct claim without hedging (can be SHORT or MEDIUM)
2. NUANCE: Acknowledge complexity/conditions (LONG with qualifications)
3. IMPLICATION: Deeper meaning beyond the obvious (MEDIUM to LONG)

**FCS Structure:**
1. FINDING: What the data shows (MEDIUM)
2. CONTRAST: Compare to expectations/other work (LONG)
3. SYNTHESIS: What this means overall (can be SHORT for emphasis)

**Length Pattern:**
- High variation required: CV > 0.35
- Include at least 1 SHORT emphatic sentence (8-12 words)
- Mix LONG analysis with SHORT conclusions
- Example: "The effect was substantial." (SHORT emphasis)

**REQUIRED for Results:**
- At least one punchy, emphatic short sentence
- Clear subject chain: Results → Data → Implications
- Can use dramatic short sentences for key findings"""

    else:  # closing
        return """## Closing Paragraph Instructions (结尾段落指令)

### Pattern: SLF (Summary-Limitation-Future) or IBC (Implication-Broader-Call)

**SLF Structure:**
1. SUMMARY: Recap main findings (MEDIUM)
2. LIMITATION: Acknowledge constraints (MEDIUM to LONG)
3. FUTURE: Directions for further research (LONG, ends strongly)

**IBC Structure:**
1. IMPLICATION: What this means for the field (MEDIUM to LONG)
2. BROADER: Connect to larger context (LONG)
3. CALL: Final statement or call to action (LONG, impactful ending)

**Length Pattern:**
- Progressive lengthening toward the end
- DO NOT end with a short sentence (too abrupt)
- Final sentence should be LONG (20-30 words) and impactful
- Create sense of closure and completeness

**REQUIRED for Closing:**
- Must end with a substantial sentence
- Subject progression: Findings → Implications → Field
- Build toward a strong final statement"""


def _format_length_requirements(length_profile: Dict) -> str:
    """Format additional length requirements"""
    extras = []
    if "first_sentence" in length_profile:
        extras.append(f"- First sentence: {length_profile['first_sentence']} words (hook)")
    if "min_long_sentences" in length_profile:
        extras.append(f"- Minimum {length_profile['min_long_sentences']} sentences >30 words")
    if "min_short_sentences" in length_profile:
        extras.append(f"- Minimum {length_profile['min_short_sentences']} emphatic short sentence (<12 words)")
    if "last_sentence" in length_profile:
        extras.append(f"- Last sentence: {length_profile['last_sentence']} (no abrupt endings)")
    return "\n".join(extras) if extras else "- Standard variation"


def _get_subject_strategy_instructions(strategy: str) -> str:
    """Get instructions for subject diversity strategy"""
    strategies = {
        "domain_nouns": """Use domain terminology as subjects:
- "Machine learning models...", "The algorithm...", "This approach..."
- Avoid first-person and overly generic subjects""",
        "method_alternation": """Alternate between method-related subjects:
- "The method... This approach... Such mechanisms... The technique..."
- Show different facets of the same concept""",
        "result_chain": """Progress from results to implications:
- "The results... These findings... The data... Such patterns... The implications..."
- Build logical flow through subject changes""",
        "abstraction_progression": """Move from specific to abstract:
- "These findings... The implications... This research area... The field..."
- Create closing sense through abstraction""",
    }
    return strategies.get(strategy, "Vary subjects naturally")


def _format_required_features(features: List[str]) -> str:
    """Format required features for the prompt"""
    feature_descriptions = {
        "hook_sentence": "- Include a compelling opening hook (can be shorter)",
        "nested_clauses_for_definition": "- Use nested clauses (which/where/whereby) for definitions",
        "emphatic_short_sentence": "- Include at least one punchy short sentence for emphasis",
        "progressive_lengthening": "- Sentences should progressively lengthen toward the end",
    }
    return "\n".join([feature_descriptions.get(f, f"- {f}") for f in features]) if features else "- No special requirements"


def _format_forbidden_patterns(forbidden: List[str]) -> str:
    """Format forbidden patterns for the prompt"""
    pattern_descriptions = {
        "ANI": "- Do NOT use strong assertions (save for result paragraphs)",
        "end_with_short": "- Do NOT end with a short sentence (too abrupt)",
    }
    return "\n".join([pattern_descriptions.get(f, f"- Avoid: {f}") for f in forbidden]) if forbidden else "- No specific restrictions"


# =============================================================================
# Sentence Fusion Prompt
# 句子融合Prompt
# =============================================================================

def get_sentence_fusion_prompt(
    paragraph: str,
    tone_level: int = 4
) -> str:
    """
    Generate prompt for sentence fusion - LLM autonomously judges semantic relationships
    生成句子融合的Prompt - LLM自主判断语义关系

    Key principles:
    1. LLM analyzes semantic relationships between adjacent sentences
    2. Closely related sentences can be merged into complex forms
    3. Short emphatic sentences are added for rhythm
    4. Semantics must be preserved
    """
    return f"""## Task: Sentence Fusion - Analyze and Restructure Based on Semantic Relationships
## 任务：句子融合 - 基于语义关系分析并重构

You are an expert at restructuring academic paragraphs to appear human-written.
你是重构学术段落使其看起来像人类写作的专家。

## Original Paragraph:
{paragraph}

## Your Task: Autonomous Semantic Analysis and Restructuring
## 你的任务：自主语义分析与重构

Analyze the semantic relationships between adjacent sentences in this paragraph. Based on your analysis:

### Step 1: Identify Semantic Relationships (识别语义关系)

For each pair of adjacent sentences, determine their relationship:

**TIGHT RELATIONSHIPS (语义紧密 → Consider MERGING):**
- CAUSE_EFFECT: One sentence causes/explains the other
- ELABORATION: One sentence elaborates/specifies the other
- DEFINITION_EXAMPLE: One defines, the other exemplifies
- CONDITION_RESULT: One is the condition, the other is the result
- PARALLEL_CONCEPT: Two closely related parallel ideas

**LOOSE RELATIONSHIPS (语义松散 → Keep SEPARATE):**
- TOPIC_SHIFT: Different aspects or sub-topics
- CONTRAST: Opposing or contrasting ideas
- TEMPORAL_SEQUENCE: Time-ordered but independent events
- INDEPENDENT: Loosely related statements

### Step 2: Apply Fusion Strategies (应用融合策略)

**For TIGHT relationships - MERGE into complex sentences:**

1. **Relative Clause Fusion (关系从句融合)**
   - Use: which, that, where, whereby, whose
   - Example: "The model performs well. It uses attention mechanisms."
   → "The model, which uses attention mechanisms, performs well."

2. **Subordinate Clause Fusion (从属从句融合)**
   - Use: because, since, although, while, when, if, as
   - Example: "Results improved. We increased the sample size."
   → "Results improved because we increased the sample size."

3. **Participial Phrase Fusion (分词短语融合)**
   - Use: -ing/-ed phrases
   - Example: "The algorithm processes data. It identifies patterns."
   → "Processing data, the algorithm identifies patterns."

4. **Appositive Fusion (同位语融合)**
   - Example: "Smith proposed a theory. The theory explains X."
   → "Smith proposed a theory explaining X." OR "Smith's theory, which explains X, has gained acceptance."

5. **Conditional Fusion (条件融合)**
   - Use: provided that, given that, assuming that
   - Example: "The method works. Certain conditions must be met."
   → "The method works provided that certain conditions are met."

**For LOOSE relationships - ADD VARIETY:**

1. **Add Short Emphatic Sentences (添加短句强调)**
   - 8-14 words for key conclusions or emphasis
   - Example: "This distinction matters." / "The evidence is clear."

2. **Keep as Separate Sentences with Implicit Connection**
   - Remove explicit connectors (Furthermore, However, Additionally)
   - Let semantic flow create the connection

### Step 3: Balance Requirements (平衡要求)

Your restructured paragraph MUST have:

1. **Sentence Length Variety:**
   - At least 1-2 LONG complex sentences (25-40+ words) from merging
   - At least 1-2 SHORT emphatic sentences (8-14 words)
   - Remaining MEDIUM sentences (15-24 words)
   - Target CV (coefficient of variation) > 0.30

2. **Semantic Preservation:**
   - ALL original meaning must be preserved
   - NO information loss from merging
   - Technical terms and data remain intact

3. **Natural Flow:**
   - Merged sentences must read naturally
   - Avoid over-complex nested structures (max 2 levels of nesting)
   - Short sentences provide breathing room

## Critical Rules (关键规则):

1. **YOU DECIDE** which sentences to merge based on YOUR semantic analysis
2. **NOT ALL sentences should be merged** - maintain variety
3. **Preserve ALL meaning** - merging should not lose information
4. **Use diverse clause types** - don't repeat the same fusion pattern
5. **Add short sentences** for rhythm and emphasis (at least 1-2)
6. Tone level: {tone_level}/10 (0=formal academic, 10=casual)

## Output (JSON only, no markdown):
{{
    "semantic_analysis": [
        {{"sentence_pair": [0, 1], "relationship": "CAUSE_EFFECT", "decision": "merge", "reason": "Sentence 1 explains cause of sentence 0"}},
        {{"sentence_pair": [1, 2], "relationship": "TOPIC_SHIFT", "decision": "keep_separate", "reason": "Different aspects discussed"}},
        {{"sentence_pair": [2, 3], "relationship": "ELABORATION", "decision": "merge", "reason": "Sentence 3 elaborates on sentence 2"}}
    ],
    "restructured": "The complete rewritten paragraph with fused sentences and short emphatic sentences",
    "fusion_applied": [
        {{"type": "relative_clause", "original_sentences": [0, 1], "result": "Combined sentence using 'which'"}},
        {{"type": "short_emphasis", "position": "after_fusion_1", "content": "This finding matters."}}
    ],
    "sentence_lengths": [35, 10, 22, 28, 12],
    "cv_achieved": 0.42,
    "explanation": "How semantic relationships guided the restructuring",
    "explanation_zh": "语义关系如何指导重构"
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
    "document_aware": get_document_aware_restructure_prompt,
    "sentence_fusion": get_sentence_fusion_prompt,
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
    elif strategy == "document_aware":
        return prompt_generator(
            paragraph,
            paragraph_index=kwargs.get("paragraph_index", 0),
            total_paragraphs=kwargs.get("total_paragraphs", 1),
            detected_issues=kwargs.get("detected_issues"),
            tone_level=kwargs.get("tone_level", 4)
        )
    elif strategy == "sentence_fusion":
        return prompt_generator(
            paragraph,
            tone_level=kwargs.get("tone_level", 4)
        )
    elif strategy == "all":
        return prompt_generator(
            paragraph,
            detected_issues=kwargs.get("detected_issues", []),
            tone_level=kwargs.get("tone_level", 4)
        )

    return prompt_generator(paragraph, **kwargs)
