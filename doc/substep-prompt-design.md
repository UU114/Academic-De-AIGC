# Sub-Step Prompt System Design
# 子步骤Prompt系统设计

> Created: 2026-01-09
> Purpose: Design LLM analysis and rewriting prompts for all substeps
> 目的：为所有子步骤设计LLM分析和改写prompt

---

## 一、旧代码工作流程总结 | Old Code Workflow Summary

### 1.1 完整流程 | Complete Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Old Code Workflow (structure analysis as example)              │
│  旧代码工作流程（以结构分析为例）                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: LLM Analysis 分析阶段                                    │
│  ├── POST /api/v1/structure/document/step1-1                    │
│  ├── Call SmartStructureAnalyzer.analyze_structure()            │
│  ├── LLM返回结构化JSON:                                          │
│  │   {                                                           │
│  │     "issues": [                                               │
│  │       {                                                       │
│  │         "type": "linear_flow",                                │
│  │         "description": "...",                                 │
│  │         "description_zh": "...",                              │
│  │         "severity": "high",                                   │
│  │         "affected_positions": ["1(1)", "1(2)"]                │
│  │       }                                                       │
│  │     ]                                                         │
│  │   }                                                           │
│  └── 缓存分析结果到 document.structure_analysis_cache            │
│                                                                  │
│  Step 2: Display Issues 展示问题                                 │
│  ├── 前端展示问题列表                                            │
│  ├── 用户点击问题，展开详细说明                                  │
│  └── 用户多选问题                                                │
│                                                                  │
│  Step 3A: Generate Prompt 生成Prompt（可选）                     │
│  ├── POST /api/v1/structure/merge-modify/prompt                 │
│  ├── 输入: {                                                     │
│  │     selected_issues: [...],                                  │
│  │     user_notes: "..."                                        │
│  │   }                                                           │
│  ├── LLM生成一个给用户复制的prompt                               │
│  └── 返回: { prompt: "...", prompt_zh: "..." }                  │
│                                                                  │
│  Step 3B: AI Modify 直接AI修改（可选）                           │
│  ├── POST /api/v1/structure/merge-modify/apply                  │
│  ├── 输入: {                                                     │
│  │     selected_issues: [...],                                  │
│  │     user_notes: "..."                                        │
│  │   }                                                           │
│  ├── LLM直接修改文档                                             │
│  └── 返回: { modified_text: "...", changes_summary_zh: "..." }  │
│                                                                  │
│  Step 4: Upload New Document or Accept 上传新文档或接受          │
│  ├── 用户可以上传新的docx/txt文件                                │
│  └── 或者接受AI修改的结果                                        │
│                                                                  │
│  Step 5: Pass to Next Substep 传递给下一个substep                │
│  └── 下一个substep基于修改后的文本进行分析                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 关键Schema | Key Schemas

```python
# 选中的问题 | Selected Issue
class SelectedIssue(BaseModel):
    type: str  # 问题类型
    description: str  # 英文描述
    description_zh: str  # 中文描述
    severity: str  # high/medium/low
    affected_positions: List[str]  # 受影响位置

# 合并修改请求 | Merge Modify Request
class MergeModifyRequest(BaseModel):
    document_id: str
    session_id: Optional[str]
    selected_issues: List[SelectedIssue]
    user_notes: Optional[str]  # 用户的额外指导意见
    mode: str  # "prompt" or "apply"

# 生成Prompt响应 | Generate Prompt Response
class MergeModifyPromptResponse(BaseModel):
    prompt: str  # 生成的prompt供用户复制
    prompt_zh: str  # 中文提示词描述
    issues_summary_zh: str
    colloquialism_level: int
    estimated_changes: int

# AI修改响应 | AI Modify Response
class MergeModifyApplyResponse(BaseModel):
    modified_text: str  # 修改后的文档
    changes_summary_zh: str  # 修改总结
    changes_count: int
    issues_addressed: List[str]
    remaining_attempts: int
```

---

## 二、通用Substep工作流程 | Generic Substep Workflow

### 2.1 每个Substep的标准流程 | Standard Flow for Each Substep

```
┌─────────────────────────────────────────────────────────────────┐
│  Generic Substep Workflow                                        │
│  通用Substep工作流程                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: Analysis 分析阶段                                       │
│  ├── POST /api/v1/layer{X}/step{Y}-{Z}/analyze                  │
│  ├── 接收: { text, session_id, locked_terms }                   │
│  ├── 调用LLM: ANALYSIS_PROMPT（只分析当前步骤的问题）            │
│  └── 返回: { issues: [...], risk_score, recommendations }       │
│      ⚠️ IMPORTANT: issues数组包含所有详细信息，供展开时使用      │
│                                                                  │
│  Phase 2: User Selection 用户选择阶段                            │
│  ├── 前端展示问题列表（折叠状态）                                │
│  ├── 用户点击展开 → 前端直接显示缓存的详细信息（无需再次调用）   │
│  └── 用户多选问题 + 可选输入user_notes                           │
│                                                                  │
│  Phase 3A: Generate Rewrite Prompt 生成改写Prompt               │
│  ├── POST /api/v1/layer{X}/step{Y}-{Z}/merge-modify/prompt      │
│  ├── 接收: { selected_issues, user_notes, locked_terms }        │
│  ├── 调用LLM: REWRITE_PROMPT_GENERATION                         │
│  └── 返回: { prompt, prompt_zh, estimated_changes }             │
│                                                                  │
│  Phase 3B: Direct AI Modification AI直接修改                     │
│  ├── POST /api/v1/layer{X}/step{Y}-{Z}/merge-modify/apply       │
│  ├── 接收: { selected_issues, user_notes, locked_terms }        │
│  ├── 调用LLM: REWRITE_APPLY（基于选中问题+用户指导修改文档）     │
│  └── 返回: { modified_text, changes_summary, issues_addressed } │
│                                                                  │
│  Phase 4: Accept Modified Text 接受修改后文本                    │
│  └── 传递给下一个substep: next_substep(modified_text)           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 两类Prompt | Two Types of Prompts

每个substep需要2种prompt：

1. **ANALYSIS_PROMPT（分析prompt）**
   - 目的：只分析当前步骤的特定问题
   - 输入：文档文本
   - 输出：结构化JSON问题列表
   - ⚠️ **关键**：每个issue必须包含完整的详细信息，因为前端展开时不会再次调用LLM

2. **REWRITE_PROMPT（改写prompt）**
   - 目的：基于用户选中的问题和指导意见修改文档
   - 输入：原文档 + selected_issues + user_notes + locked_terms
   - 输出：修改后的文档 + 修改说明

### 2.3 Issue对象的标准结构 | Standard Issue Object Structure

每个issue必须包含以下字段（第一次分析时全部返回）：

```json
{
  "type": "issue_type_identifier",
  "description": "Brief 1-sentence description",
  "description_zh": "简短1句话描述",
  "severity": "high|medium|low",
  "affected_positions": ["positions"],
  "evidence": "Specific text excerpts (2-3 examples)",

  // 👇 展开时显示的详细信息（第一次分析时返回）
  "detailed_explanation": "Why this is AI-like and how it differs from human writing (2-3 sentences)",
  "detailed_explanation_zh": "为什么这是AI模式以及与人类写作的区别（2-3句）",
  "fix_suggestions": [
    "Actionable suggestion 1",
    "Actionable suggestion 2"
  ],
  "fix_suggestions_zh": [
    "可操作建议1",
    "可操作建议2"
  ]
}
```

**前端UX流程**：
1. 初始显示：`description`、`severity`、`affected_positions`
2. 用户点击"展开详情"：显示 `evidence`、`detailed_explanation`、`fix_suggestions`
3. **不需要再次调用API**

---

## 三、各Layer Substep的Prompt设计 | Prompt Design for Each Substep

### Layer 5 (Document Level) - 文档级

#### Step 1.0: Term Locking 词汇锁定

**已实现** ✅ - 使用 `TermExtractor.EXTRACTION_PROMPT`

#### Step 1.1: Structure Framework Detection 结构框架检测

**ANALYSIS_PROMPT:**
```
You are an academic document structure analyzer. Analyze the GLOBAL STRUCTURAL PATTERNS only.

## DOCUMENT TEXT:
{document_text}

## YOUR TASKS:

1. **Detect Linear Flow Pattern (线性流动)**
   - Look for "First...Second...Third" or "Initially...Subsequently...Finally" enumeration
   - Check if sections progress in a formulaic, step-by-step manner
   - AI-like: Predictable sequential progression
   - Human-like: Non-linear, with回溯, jumps, or conditional logic

2. **Detect Repetitive Pattern (重复模式)**
   - Check if multiple sections have identical structures
   - Example: All sections follow "Problem → Analysis → Solution" pattern
   - AI-like: Copy-paste section structure
   - Human-like: Varied section approaches based on content needs

3. **Detect Uniform Length (均匀长度)**
   - Calculate coefficient of variation (CV) of paragraph word counts
   - AI-like: CV < 0.30 (all paragraphs similar length)
   - Human-like: CV ≥ 0.40 (varied paragraph lengths)

4. **Detect Predictable Order (可预测顺序)**
   - Check if sections follow formulaic academic order
   - AI-like: Perfect Intro → Literature → Method → Results → Discussion → Conclusion
   - Human-like: Some sections merged, reordered, or unconventional structure

5. **Detect Symmetry (对称结构)**
   - Check if all sections have equal number of paragraphs
   - AI-like: All sections have exactly 3-4 paragraphs
   - Human-like: Asymmetric distribution based on content importance

## LOCKED TERMS:
{locked_terms}
Preserve these terms exactly as they appear. Do NOT modify them.

## OUTPUT FORMAT (JSON only):
{{
  "issues": [
    {{
      "type": "linear_flow|repetitive_pattern|uniform_length|predictable_order|symmetry",
      "description": "English description of the specific issue found",
      "description_zh": "中文问题描述",
      "severity": "high|medium|low",
      "affected_positions": ["section numbers or paragraph positions"],
      "evidence": "Brief evidence showing the pattern"
    }}
  ],
  "risk_score": 0-100,
  "risk_level": "high|medium|low",
  "recommendations": ["English recommendations"],
  "recommendations_zh": ["中文建议"]
}}
```

**REWRITE_PROMPT:**
```
You are an academic document restructuring expert. Apply the following modifications to DISRUPT AI-like structural patterns while PRESERVING content quality and locked terms.

## ORIGINAL DOCUMENT:
{document_text}

## SELECTED ISSUES TO FIX:
{selected_issues}

## USER'S ADDITIONAL GUIDANCE:
{user_notes}

## LOCKED TERMS (MUST PRESERVE):
{locked_terms}
These terms must appear EXACTLY as shown. Do NOT modify, rephrase, or translate them.

## MODIFICATION STRATEGIES:

**For Linear Flow:**
- Break "First...Second...Third" progression
- Introduce non-sequential logic (e.g., discuss outlier first, then general case)
- Add conditional transitions ("In certain contexts...", "However, when...")

**For Repetitive Pattern:**
- Vary section structures (some sections detailed, some concise)
- Use different organizational approaches per section

**For Uniform Length:**
- Create intentional length asymmetry
- Expand critical sections, compress routine content
- Target CV ≥ 0.40

**For Predictable Order:**
- Merge or reorder sections if logical
- Example: Combine Literature + Methodology, or present Results before Method rationale

**For Symmetry:**
- Redistribute paragraphs asymmetrically
- Key sections get more paragraphs, routine sections get fewer

## CONSTRAINTS:
1. Preserve all factual content and arguments
2. Maintain academic rigor and citation accuracy
3. Keep locked terms EXACTLY as listed
4. Output full modified document (not just changes)
5. Write in the same language as the original document

## OUTPUT FORMAT (JSON only):
{{
  "modified_text": "Full rewritten document with structural changes",
  "changes_summary_zh": "中文修改总结：列出具体做了哪些结构调整",
  "changes_count": number_of_structural_changes,
  "issues_addressed": ["issue types addressed"]
}}
```

#### Step 1.2: Paragraph Length Regularity 段落长度规律性

**ANALYSIS_PROMPT:**
```
You are an academic document paragraph length analyzer. Analyze PARAGRAPH LENGTH DISTRIBUTION only.

## DOCUMENT TEXT:
{document_text}

## YOUR TASK:

Calculate and analyze paragraph length distribution:

1. **Calculate CV (Coefficient of Variation)**
   - CV = (standard_deviation of word counts) / (mean word count)
   - AI-like: CV < 0.30 (too uniform)
   - Human-like: CV ≥ 0.40 (healthy variation)

2. **Detect Uniform Paragraph Length Pattern**
   - Check if most paragraphs fall within a narrow range (e.g., all 80-120 words)
   - AI-like: 80%+ paragraphs within ±20% of mean
   - Human-like: Wide range from very short (30 words) to very long (200+ words)

3. **Identify Paragraphs Needing Adjustment**
   - Mark paragraphs that should be split (too long and monotonous)
   - Mark paragraphs that should be expanded (too short and underdeveloped)
   - Mark paragraphs that should be merged (fragmented logic)

## LOCKED TERMS:
{locked_terms}
Context: These terms will not be modified in rewriting.

## OUTPUT FORMAT (JSON only):
{{
  "issues": [
    {{
      "type": "uniform_length",
      "description": "Paragraph length variance too low (CV={cv_value})",
      "description_zh": "段落长度过于均匀（变异系数={cv_value}）",
      "severity": "high|medium|low",
      "affected_positions": ["paragraph indices with uniform length"],
      "current_cv": 0.xx,
      "target_cv": 0.40,
      "split_candidates": ["para_index: reason"],
      "expand_candidates": ["para_index: reason"],
      "merge_candidates": [["para1_index", "para2_index", "reason"]]
    }}
  ],
  "risk_score": 0-100,
  "risk_level": "high|medium|low",
  "recommendations": ["English recommendations"],
  "recommendations_zh": ["中文建议"]
}}
```

**REWRITE_PROMPT:**
```
You are an academic document paragraph length optimizer. Apply paragraph length adjustments to achieve natural variation while preserving content quality and locked terms.

## ORIGINAL DOCUMENT:
{document_text}

## SELECTED ISSUES TO FIX:
{selected_issues}

## USER'S ADDITIONAL GUIDANCE:
{user_notes}

## LOCKED TERMS (MUST PRESERVE):
{locked_terms}

## MODIFICATION STRATEGIES:

**Split Strategy (拆分):**
- Break long paragraphs at natural topic shifts
- Create varied lengths: one long parent → one short + one medium child

**Expand Strategy (扩展):**
- Add concrete examples, case studies, or elaborations
- Avoid generic filler; add substantive content

**Merge Strategy (合并):**
- Combine fragmented paragraphs that discuss the same subtopic
- Create longer, cohesive paragraphs for key sections

**Target Distribution:**
- Short paragraphs: 30-60 words (10-20%)
- Medium paragraphs: 80-120 words (50-60%)
- Long paragraphs: 150-250 words (20-30%)
- Target CV ≥ 0.40

## CONSTRAINTS:
1. Preserve all factual content
2. Maintain logical flow
3. Keep locked terms EXACTLY as listed
4. Output full modified document

## OUTPUT FORMAT (JSON only):
{{
  "modified_text": "Full document with adjusted paragraph lengths",
  "changes_summary_zh": "中文修改总结：描述拆分/扩展/合并的具体操作",
  "changes_count": number_of_paragraphs_modified,
  "issues_addressed": ["uniform_length"],
  "new_cv": 0.xx
}}
```

#### Step 1.3: Progression Pattern & Closure 推进模式与闭合

**ANALYSIS_PROMPT:**
```
You are an academic document progression analyzer. Analyze PROGRESSION PATTERN and CLOSURE STRENGTH only.

## DOCUMENT TEXT:
{document_text}

## YOUR TASKS:

1. **Detect Monotonic Progression (单调推进)**
   - Check for linear, step-by-step topic advancement without回溯
   - AI-like: Topic A → Topic B → Topic C (never revisits A or B)
   - Human-like: Topic A → Topic B → back to A with new insight → Topic C

2. **Detect Too-Strong Closure (过度闭合)**
   - Check for formulaic conclusion patterns
   - AI-like: "In conclusion, this study has shown...", "To summarize..."
   - Human-like: Open questions, unresolved tensions, future research needs

3. **Detect Missing Conditional/Qualification (缺少条件限定)**
   - AI tends to make absolute statements
   - Human-like: "In certain contexts...", "Under these conditions...", "However..."

## LOCKED TERMS:
{locked_terms}

## OUTPUT FORMAT (JSON only):
{{
  "issues": [
    {{
      "type": "monotonic_progression|too_strong_closure|missing_qualification",
      "description": "English description",
      "description_zh": "中文描述",
      "severity": "high|medium|low",
      "affected_positions": ["section or paragraph indices"],
      "evidence": "Specific text showing the pattern"
    }}
  ],
  "risk_score": 0-100,
  "risk_level": "high|medium|low",
  "recommendations": ["English recommendations"],
  "recommendations_zh": ["中文建议"]
}}
```

**REWRITE_PROMPT:**
```
You are an academic document progression optimizer. Apply the following modifications to create more human-like argumentation flow while preserving locked terms.

## ORIGINAL DOCUMENT:
{document_text}

## SELECTED ISSUES TO FIX:
{selected_issues}

## USER'S ADDITIONAL GUIDANCE:
{user_notes}

## LOCKED TERMS (MUST PRESERVE):
{locked_terms}

## MODIFICATION STRATEGIES:

**For Monotonic Progression:**
- Add回溯: After introducing Topic B, revisit Topic A with new perspective
- Add conditional logic: "In contrast to X, when Y conditions apply..."
- Introduce non-sequential discussion

**For Too-Strong Closure:**
- Soften conclusions: Replace "This proves..." with "This suggests..."
- Add open questions: "Future research should explore..."
- Leave some tensions unresolved

**For Missing Qualification:**
- Add hedging: "may", "appears to", "in most cases"
- Add contextual conditions: "Under these specific conditions..."
- Add counter-examples or exceptions

## CONSTRAINTS:
1. Preserve all core arguments and evidence
2. Maintain academic credibility
3. Keep locked terms EXACTLY as listed
4. Output full modified document

## OUTPUT FORMAT (JSON only):
{{
  "modified_text": "Full document with improved progression logic",
  "changes_summary_zh": "中文修改总结",
  "changes_count": number_of_modifications,
  "issues_addressed": ["issue types"]
}}
```

#### Step 1.4: Anchor Density 锚点密度

**ANALYSIS_PROMPT:**
```
You are an academic document anchor density analyzer. Analyze CONCRETE ANCHOR DENSITY only.

## DOCUMENT TEXT:
{document_text}

## YOUR TASK:

Count the density of concrete anchors (evidence that LLMs can't fabricate):

**Anchor Types:**
1. Decimal numbers: 14.2, 3.56, 0.82 (weight: 1.0)
2. Percentages: 50%, 14.2% (weight: 1.2)
3. Statistical values: p < 0.05, r = 0.82, t-test (weight: 1.5)
4. Citations: [1], (Smith, 2020), et al. (weight: 1.5)
5. Units/measurements: 5mL, 20°C, 3kg (weight: 1.3)
6. Chemical formulas: H2O, CO2, C6H12O6 (weight: 1.2)

**Density Calculation:**
- Weighted anchor count per 100 words
- AI hallucination risk:
  - Density < 5.0: High risk (vague, abstract)
  - Density 5.0-10.0: Medium risk
  - Density > 10.0: Low risk (具体、可验证)

**Identify Low-Density Paragraphs:**
- Mark paragraphs with density < 3.0 as high-risk AI filler

## LOCKED TERMS:
{locked_terms}

## OUTPUT FORMAT (JSON only):
{{
  "issues": [
    {{
      "type": "low_anchor_density",
      "description": "Paragraph {X} has very low anchor density ({density}), suggesting abstract AI filler",
      "description_zh": "段落{X}锚点密度过低（{density}），疑似AI生成的抽象填充内容",
      "severity": "high|medium|low",
      "affected_positions": ["paragraph indices"],
      "current_density": 0.xx,
      "target_density": 5.0,
      "missing_anchor_types": ["statistical_values", "citations"]
    }}
  ],
  "overall_density": 0.xx,
  "risk_score": 0-100,
  "risk_level": "high|medium|low",
  "recommendations": ["English recommendations"],
  "recommendations_zh": ["中文建议"]
}}
```

**REWRITE_PROMPT:**
```
You are an academic document anchor enhancement expert. Add concrete, verifiable anchors to low-density paragraphs while preserving locked terms.

## ORIGINAL DOCUMENT:
{document_text}

## SELECTED ISSUES TO FIX:
{selected_issues}

## USER'S ADDITIONAL GUIDANCE:
{user_notes}

## LOCKED TERMS (MUST PRESERVE):
{locked_terms}

## MODIFICATION STRATEGIES:

**For Low Anchor Density:**
- Add specific numbers: Replace "many" with "73%", "most" with "85%"
- Add citations: Reference existing literature (user must verify)
- Add statistical evidence: p-values, correlation coefficients
- Add measurements: Specific quantities, temperatures, concentrations
- Replace vague statements with concrete examples

**WARNING:**
- Do NOT fabricate data or citations
- If specific values are unknown, use placeholders like "[AUTHOR, YEAR]" or "[XX%]"
- User must fill in real values

**Target Density:** ≥ 5.0 anchors per 100 words

## CONSTRAINTS:
1. Do NOT invent false data or citations
2. Use placeholders if specific values are unknown
3. Keep locked terms EXACTLY as listed
4. Output full modified document

## OUTPUT FORMAT (JSON only):
{{
  "modified_text": "Full document with added concrete anchors (use placeholders if needed)",
  "changes_summary_zh": "中文修改总结：描述添加的锚点类型",
  "changes_count": number_of_anchors_added,
  "issues_addressed": ["low_anchor_density"],
  "new_overall_density": 0.xx,
  "placeholders_needing_verification": ["list of placeholders user must replace"]
}}
```

#### Step 1.5: Transitions & Connectors 衔接与连接词

**ANALYSIS_PROMPT:**
```
You are an academic document transition analyzer. Analyze PARAGRAPH TRANSITIONS and CONNECTOR USAGE only.

## DOCUMENT TEXT:
{document_text}

## YOUR TASKS:

1. **Detect Explicit Connectors at Paragraph Openings (显性连接词)**
   - AI-like: "Furthermore, ...", "Moreover, ...", "Additionally, ...", "However, ..."
   - Human-like: Implicit semantic connection, lexical echoes

2. **Detect Formulaic Topic Sentences (公式化主题句)**
   - AI-like: Every paragraph starts with "This study...", "The results show..."
   - Human-like: Varied sentence openers

3. **Detect Too-Smooth Transitions (过度平滑过渡)**
   - AI-like: Every paragraph seamlessly connects with perfect logical flow
   - Human-like: Some abrupt topic shifts are natural

4. **Detect Summary Endings (公式化总结结尾)**
   - AI-like: Paragraphs end with "Thus, ...", "Therefore, ...", "In summary, ..."
   - Human-like: Varied endings, some abrupt

## LOCKED TERMS:
{locked_terms}

## OUTPUT FORMAT (JSON only):
{{
  "issues": [
    {{
      "type": "explicit_connector|formulaic_topic_sentence|too_smooth_transition|summary_ending",
      "description": "English description",
      "description_zh": "中文描述",
      "severity": "high|medium|low",
      "affected_positions": ["paragraph indices or transition points"],
      "connector_word": "Furthermore|Moreover|...",
      "suggestion": "Replace with lexical echo or implicit connection"
    }}
  ],
  "connector_density": "X connectors per 100 words",
  "risk_score": 0-100,
  "risk_level": "high|medium|low",
  "recommendations": ["English recommendations"],
  "recommendations_zh": ["中文建议"]
}}
```

**REWRITE_PROMPT:**
```
You are an academic document transition optimizer. Remove explicit connectors and create implicit semantic connections while preserving locked terms.

## ORIGINAL DOCUMENT:
{document_text}

## SELECTED ISSUES TO FIX:
{selected_issues}

## USER'S ADDITIONAL GUIDANCE:
{user_notes}

## LOCKED TERMS (MUST PRESERVE):
{locked_terms}

## MODIFICATION STRATEGIES:

**For Explicit Connectors:**
- Remove "Furthermore", "Moreover", "Additionally"
- Replace with lexical echoes: Repeat key term from previous paragraph
- Example:
  - Before: "Para 1 discusses X. Furthermore, para 2 discusses Y."
  - After: "Para 1 discusses X. The concept of X also applies to Y."

**For Formulaic Topic Sentences:**
- Vary sentence openers: Some start with prepositional phrases, adverbs, or subordinate clauses
- Avoid repetitive patterns like "This study...", "The results..."

**For Too-Smooth Transitions:**
- Allow some abrupt topic shifts (natural in human writing)
- Not every paragraph needs explicit connection

**For Summary Endings:**
- Remove "Thus", "Therefore", "In summary"
- Use varied endings or even abrupt stops

## CONSTRAINTS:
1. Preserve all arguments and logic
2. Maintain paragraph meaning
3. Keep locked terms EXACTLY as listed
4. Output full modified document

## OUTPUT FORMAT (JSON only):
{{
  "modified_text": "Full document with improved transitions",
  "changes_summary_zh": "中文修改总结：描述删除的连接词和使用的语义回声",
  "changes_count": number_of_transitions_modified,
  "issues_addressed": ["issue types"],
  "connectors_removed": ["list of removed connectors"]
}}
```

---

### Layer 4 (Section Level) - 章节级

#### Step 2.0: Section Identification 章节识别

**ANALYSIS_PROMPT:**
```
You are an academic document section analyzer. Identify sections and their roles.

## DOCUMENT TEXT:
{document_text}

## YOUR TASKS:

1. **Identify Section Boundaries**
   - Detect section headers (e.g., "1. Introduction", "2.1 Methods")
   - If no explicit headers, infer sections based on topic shifts

2. **Label Section Roles**
   - introduction, literature_review, methodology, results, discussion, conclusion
   - Or custom roles if non-standard structure

3. **Count Paragraphs Per Section**

4. **Detect Issues**
   - All sections have same number of paragraphs (symmetry issue)
   - Missing critical sections
   - Unconventional section order

## LOCKED TERMS:
{locked_terms}

## OUTPUT FORMAT (JSON only):
{{
  "sections": [
    {{
      "number": "1",
      "title": "Introduction",
      "role": "introduction",
      "paragraph_count": 3,
      "paragraph_indices": [0, 1, 2]
    }}
  ],
  "issues": [...],
  "risk_score": 0-100,
  "risk_level": "high|medium|low",
  "recommendations": ["English"],
  "recommendations_zh": ["中文"]
}}
```

**REWRITE_PROMPT:**
```
You are an academic document section organizer. Reorganize sections to address identified issues while preserving locked terms.

## ORIGINAL DOCUMENT:
{document_text}

## SELECTED ISSUES TO FIX:
{selected_issues}

## USER'S ADDITIONAL GUIDANCE:
{user_notes}

## LOCKED TERMS (MUST PRESERVE):
{locked_terms}

## MODIFICATION STRATEGIES:

**For Section Symmetry:**
- Redistribute paragraphs asymmetrically
- Key sections get more content, routine sections get less

**For Missing Sections:**
- Add placeholder or merge with existing sections

**For Unconventional Order:**
- Reorder if user requests, but preserve logical flow

## CONSTRAINTS:
1. Preserve all content
2. Keep locked terms EXACTLY as listed
3. Output full modified document with clear section headers

## OUTPUT FORMAT (JSON only):
{{
  "modified_text": "Full document with reorganized sections",
  "changes_summary_zh": "中文修改总结",
  "changes_count": number_of_sections_modified,
  "issues_addressed": ["issue types"]
}}
```

#### Step 2.1-2.5: Other Section-Level Substeps

（类似设计，分析章节顺序、章节长度、章节内逻辑等）

---

### Layer 3 (Paragraph Level) - 段落级

#### Step 3.0: Paragraph Identification 段落识别

**ANALYSIS_PROMPT:**
```
You are an academic document paragraph analyzer. Identify paragraphs and filter non-body content.

## DOCUMENT TEXT:
{document_text}

## YOUR TASKS:

1. **Split Text into Paragraphs**
   - Use double newline as delimiter

2. **Filter Non-Body Content**
   - Remove: Abstract headers, Keywords, Figure captions, Table content, References
   - Keep: Only real prose paragraphs

3. **Label Each Paragraph**
   - paragraph_index
   - word_count
   - sentence_count
   - is_body_content: true/false

4. **Detect Issues**
   - Too many non-body paragraphs (needs cleaning)

## OUTPUT FORMAT (JSON only):
{{
  "paragraphs": [
    {{
      "index": 0,
      "text": "paragraph text...",
      "word_count": 120,
      "sentence_count": 5,
      "is_body_content": true
    }}
  ],
  "body_paragraph_count": 15,
  "filtered_paragraph_count": 3,
  "issues": [...],
  "risk_score": 0-100
}}
```

**REWRITE_PROMPT:**
（段落识别不需要改写，只需要清理）

#### Step 3.1-3.5: Other Paragraph-Level Substeps

（段落角色标注、段内连贯性、锚点密度、句长分布、段落过渡等）

---

### Layer 2 (Sentence Level) - 句子级

#### Step 4.0: Sentence Identification 句子识别

**ANALYSIS_PROMPT:**
```
Identify sentences within paragraphs and label their types (simple, complex, compound, compound-complex).

Detect issues:
- Too many simple sentences
- Too few complex sentences
- Repetitive sentence openers
```

#### Step 4.1-4.5: Other Sentence-Level Substeps

（句长分析、句子合并、连接词优化、句式多样化改写等）

---

### Layer 1 (Lexical Level) - 词汇级

#### Step 5.0: Lexical Context Preparation 词汇环境准备

**ANALYSIS_PROMPT:**
```
Analyze vocabulary richness and word frequency distribution.

Detect issues:
- Low vocabulary diversity (vocabulary_richness < 0.3)
- Over-use of certain words
```

#### Step 5.1: AIGC Fingerprint Detection AIGC指纹检测

**ANALYSIS_PROMPT:**
```
Detect AI fingerprint words and phrases.

AI fingerprint categories:
- Overused words: delve, underscore, leverage, harness, pivotal
- Formulaic phrases: "In the realm of", "It is worth noting that"
- Absolute modifiers: "comprehensive", "robust", "significant"
```

#### Step 5.2-5.5: Other Lexical-Level Substeps

（人类特征分析、替换候选生成、LLM段落级改写、改写结果验证）

---

## 四、通用Prompt模板变量 | Generic Prompt Template Variables

所有prompt都应该支持以下变量：

```python
# 分析Prompt变量 | Analysis Prompt Variables
{
    "document_text": str,  # 当前文档文本（可能是前一步的修改结果）
    "locked_terms": List[str],  # Step 1.0锁定的术语
    "session_id": str,  # 会话ID
    "colloquialism_level": int  # 口语化级别（某些步骤需要）
}

# 改写Prompt变量 | Rewrite Prompt Variables
{
    "document_text": str,
    "selected_issues": List[SelectedIssue],  # 用户选中的问题
    "user_notes": str,  # 用户的额外指导意见
    "locked_terms": List[str],
    "colloquialism_level": int,
    "previous_modifications": str  # 前面步骤的修改历史（可选）
}
```

---

## 五、Implementation Plan 实施计划

### Phase 1: 复用旧代码schemas ✅
- [x] 使用 `SelectedIssue`, `MergeModifyRequest` 等旧schemas
- [x] 每个substep只需要定义自己的issue types

### Phase 2: 实现通用substep API框架
- [ ] 创建 `BaseSubstepHandler` 基类
- [ ] 定义3个标准端点：
  - `POST /analyze` - 分析
  - `POST /merge-modify/prompt` - 生成prompt
  - `POST /merge-modify/apply` - AI修改

### Phase 3: 为每个substep编写prompts
- [ ] Layer 5: Steps 1.1-1.5
- [ ] Layer 4: Steps 2.0-2.5
- [ ] Layer 3: Steps 3.0-3.5
- [ ] Layer 2: Steps 4.0-4.5
- [ ] Layer 1: Steps 5.0-5.5

### Phase 4: 测试端到端流程
- [ ] 测试完整5层流程
- [ ] 验证locked_terms在所有步骤中被保留
- [ ] 验证每一步基于上一步的修改结果

---

## 六、关键设计原则 | Key Design Principles

1. **职责单一**: 每个substep的分析prompt只分析当前步骤的特定问题
2. **传递修改**: 每个substep接收上一步的modified_text作为输入
3. **保护锁定词**: 所有改写prompt必须包含locked_terms保护
4. **结构化输出**: 所有LLM输出必须是JSON格式，便于前端解析
5. **双语支持**: description和description_zh都要有
6. **用户可控**: 用户可选择问题、输入指导意见、上传新文件

---

## 七、下一步 | Next Steps

1. **创建BaseSubstepHandler基类**
2. **实现Layer 5 Step 1.1作为pilot**
3. **测试完整流程**
4. **复制模板到其他substeps**

---

**END OF DOCUMENT**
