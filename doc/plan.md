# AcademicGuard 开发计划
# AcademicGuard Development Plan

> 版本 Version: v2.0
> 状态 Status: 实施中 / In Progress
> 更新日期 Last Updated: 2025-12-31
> 目标语言 Target Language: **English Academic Papers Only**

---

## 一、项目概述 | Project Overview

### 1.1 项目名称 | Project Name

**AcademicGuard: 英文论文 AIGC 检测与人源化协作引擎**
**AcademicGuard: Academic Paper AIGC Detection & Human-AI Collaborative Humanization Engine**

### 1.2 核心定位 | Core Positioning

| 定位 | 说明 |
|------|------|
| **产品类型** | 人机协作工具（非自动改写工具） |
| **Product Type** | Human-AI Collaboration Tool (Not Auto-rewriting) |
| **核心价值** | AI教你改，而非AI替你改 |
| **Core Value** | AI guides you to revise, not revise for you |
| **目标用户** | ESL研究者、学术论文作者 |
| **Target Users** | ESL researchers, academic paper authors |

### 1.3 核心功能 | Core Features

```
输入论文 → 逐句AIGC风险分析 → 双轨建议生成 → 用户选择/修改 → 验证通过 → 输出
Input   → Sentence-by-sentence Analysis → Dual-track Suggestions → User Choice → Validation → Output
```

---

## 二、三层级 De-AIGC 架构 | Three-Level De-AIGC Architecture

> 基于 `improve.md` 分析报告，采用三层级递进式架构

### 2.0 架构概览 | Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    三层级 De-AIGC 处理流程                            │
│                Three-Level De-AIGC Processing Flow                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Level 1: 骨架重组 (Macro Structure)                                 │
│  ├── 全文逻辑诊断                                                    │
│  ├── 识别线性结构问题                                                │
│  └── 提供两种重构方案                                                │
│                          ↓                                           │
│  Level 2: 关节润滑 (Paragraph Transition)                            │
│  ├── 滑动窗口检测段落接缝                                            │
│  ├── 消灭显性连接词                                                  │
│  └── 建立语义回声连接                                                │
│                          ↓                                           │
│  Level 3: 皮肤精修 (Sentence Polish) ✅ 已实现                       │
│  ├── 指纹词替换                                                      │
│  ├── 句式重构                                                        │
│  └── 主观噪声注入                                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.0.1 各层级实现状态 | Implementation Status

| 层级 Level | 名称 Name | 目标 Goal | 状态 Status |
|------------|-----------|-----------|-------------|
| **Level 1** | 骨架重组 Macro Structure | 打破线性结构，重构叙事逻辑 | ✅ 已实现 |
| **Level 2** | 关节润滑 Paragraph Transition | 消灭显性连接词，建立语义流 | ✅ 已实现 |
| **Level 3** | 皮肤精修 Sentence Polish | 指纹词替换、句式重构 | ✅ CAASS v2.0 已实现 |

### 2.0.2 处理顺序原则 | Processing Order Principle

> **重要**：必须按 Level 1 → 2 → 3 顺序处理
> **Important**: Must process in Level 1 → 2 → 3 order

**原因 Reason:**
- 如果先改句子(L3)再调结构(L1)，结构调整可能导致句子级修改失效
- If sentences (L3) are modified before structure (L1), structure changes may invalidate sentence edits

**产品策略 Product Strategy:**
- 用户上传文档后，系统先运行 Level 1 诊断
- After upload, system runs Level 1 diagnosis first
- 允许用户跳过 Level 1/2，但显示警告
- Allow users to skip Level 1/2, but show warnings

---

## 三、产品设计 | Product Design

### 3.1 双模式设计 | Dual Mode Design

> **重要**: 两种模式都从 Level 1 开始，遵循完整的三层级处理流程
> **Important**: Both modes start from Level 1, following the complete three-level processing flow

```
处理流程 Processing Flow:
┌────────────────────────────────────────────────────────────┐
│  Upload → Level 1 (结构) → Level 2 (衔接) → Level 3 (句子)  │
│           Structure     Transition     Sentence           │
│                                                            │
│  干预模式: 每一步手动选择方案                               │
│  Intervention: Manual selection at each step               │
│                                                            │
│  YOLO模式: 全自动处理，最后统一审核                         │
│  YOLO: Fully automatic, review at end                      │
└────────────────────────────────────────────────────────────┘
```

#### YOLO模式 (自动处理模式) | YOLO Mode (Auto-processing)

| 项目 | 说明 |
|------|------|
| **适用场景** | 时间紧迫、长文档快速处理 |
| **Use Case** | Time-sensitive, quick processing of long documents |
| **处理流程** | L1结构分析 → L2衔接优化 → L3句子精修 → 自动应用最优建议 → 用户审核 |
| **Process** | L1 Structure → L2 Transition → L3 Sentence → Auto-apply best suggestions → User review |
| **用户控制** | 设置策略偏好，最后统一审核 |
| **User Control** | Set preferences; review at end |
| **警告提示** | 开始前弹窗提示：AI自动处理不保证结构/逻辑/语义完全可靠 |
| **Warning** | Pre-start dialog: AI auto-processing cannot guarantee complete reliability |

#### 干预模式 (逐步控制模式) | Intervention Mode (Step-by-step)

| 项目 | 说明 |
|------|------|
| **适用场景** | 重要论文、想学习AIGC特征、高质量要求 |
| **Use Case** | Important papers, learning AIGC patterns, high quality requirements |
| **处理流程** | L1手动选择 → L2手动选择 → L3逐句编辑 |
| **Process** | L1 manual selection → L2 manual selection → L3 sentence-by-sentence editing |
| **用户控制** | 每一步完全控制，可跳过、标记、自定义修改 |
| **User Control** | Full control at each step; skip, flag, or customize |

### 3.2 双轨建议系统 | Dual-track Suggestion System

这是核心功能，为每个风险句子提供两种来源的修改建议：
This is the core feature, providing two sources of suggestions for each risky sentence:

#### 轨道A: LLM智能建议 | Track A: LLM-powered Suggestions

| 项目 | 说明 |
|------|------|
| **技术基础** | Prompt Engineering + Claude/GPT-4 API |
| **Technology** | Prompt Engineering + Claude/GPT-4 API |
| **优势** | 语义理解深、改写自然流畅、可处理复杂句式 |
| **Strengths** | Deep semantic understanding, natural rewriting, handles complex sentences |
| **劣势** | 成本较高、输出有一定随机性 |
| **Weaknesses** | Higher cost, some output variability |
| **适用场景** | 复杂长句、需要重构逻辑的句子 |
| **Best For** | Complex sentences, sentences needing logical restructuring |

#### 轨道B: 规则建议 | Track B: Rule-based Suggestions

| 项目 | 说明 |
|------|------|
| **技术基础** | 同义词替换 + 句法重组 + BERT MLM |
| **Technology** | Synonym replacement + Syntactic restructuring + BERT MLM |
| **优势** | 速度快、成本低、可解释性强、确定性高 |
| **Strengths** | Fast, low cost, highly explainable, deterministic |
| **劣势** | 处理复杂句式能力有限 |
| **Weaknesses** | Limited capability for complex sentences |
| **适用场景** | 简单替换、指纹词清除、基础句式调整 |
| **Best For** | Simple replacements, fingerprint word removal, basic syntax adjustment |

#### 用户选择 | User Choice

```
展示界面 Display:
┌─────────────────────────────────────────┐
│ [A] LLM建议 - 预测风险: 25  语义: 94%   │  ← 用户可选
│ [B] 规则建议 - 预测风险: 40  语义: 98%  │  ← 用户可选
│ [C] 自定义输入 ___________________      │  ← 用户可自行修改
└─────────────────────────────────────────┘
```

### 3.3 口语化程度参数 | Colloquialism Level Parameter

用户可设置 0-10 的口语化程度，影响LLM改写风格和规则引擎的词汇选择：
Users can set a 0-10 colloquialism level affecting LLM style and rule engine word choices:

```
0 ─────────────────────────────────────────── 10
│                                              │
Most Academic                          Most Casual
(最学术化)                               (最口语化)
```

| 等级 Level | 名称 Name | 典型场景 Typical Use |
|------------|-----------|---------------------|
| 0-2 | 期刊论文级 Journal Paper | 顶刊投稿、正式出版 |
| 3-4 | 学位论文级 Thesis | 硕博论文、学位答辩 |
| 5-6 | 会议论文级 Conference | 会议投稿、技术报告 |
| 7-8 | 技术博客级 Tech Blog | 博客文章、内部文档 |
| 9-10 | 口语讨论级 Casual | 非正式讨论、草稿 |

#### 等级对词汇的影响示例 | Level Impact on Vocabulary

| 原词 Original | 0-2 | 3-4 | 5-6 | 7-10 |
|---------------|-----|-----|-----|------|
| utilize | utilize | use | use | use |
| demonstrate | demonstrate | show | show | show |
| subsequently | subsequently | then | then | after that |
| numerous | numerous | many | many | a lot of |
| commence | commence | begin | start | start |

### 3.4 ESL 辅助解释 | ESL Assistance

> **注意**: 本项目仅针对英文学术论文，不处理其他语言的论文
> **Note**: This project targets English academic papers only

为中文母语的ESL用户提供中文解释，帮助理解为什么要修改：
Provide Chinese explanations for ESL users to understand why changes are needed:

```
┌──────────────────────────────────────────────────────┐
│  English (Original):                                 │
│  "The methodology demonstrates significant efficacy" │
├──────────────────────────────────────────────────────┤
│  中文 (语义对照):                                     │
│  "该方法展示了显著的效果。"                           │
├──────────────────────────────────────────────────────┤
│  中文 (问题解释):                                     │
│  • "demonstrates significant efficacy" 是AI常用的     │
│    高级词堆砌模式，真人更可能写 "works well"          │
└──────────────────────────────────────────────────────┘
```

**目标用户 Target Users:**
- 中文母语的 ESL 研究者
- Chinese-speaking ESL researchers

---

## 四、检测分析设计 | Detection Analysis Design

### 4.1 双检测器视角 | Dual Detector Perspectives

针对主流检测器的不同侧重点，提供差异化分析：
Provide differentiated analysis targeting different detector focuses:

| 检测器 Detector | 核心逻辑 Core Logic | 重点检测 Focus Areas |
|-----------------|---------------------|---------------------|
| **Turnitin** | 基于训练数据的分类器 | 整体文风、段落结构、引用模式 |
| **GPTZero** | 困惑度 + 突发性 | 句子级PPL、长度变化、词汇选择 |

### 4.2 检测维度 | Detection Dimensions

#### 维度1: 用词分析 | Dimension 1: Vocabulary Analysis

| 指标 Metric | 说明 Description |
|-------------|------------------|
| **困惑度 PPL** | 使用LLaMA/Mistral计算，阈值<20为高风险 |
| **Perplexity** | Calculate using LLaMA/Mistral, threshold <20 is high risk |
| **AI指纹词密度** | 匹配"delve", "crucial", "paramount"等高频词库 |
| **Fingerprint Density** | Match high-frequency words like "delve", "crucial", "paramount" |
| **N-gram重复率** | 检测连续词组的重复模式 |
| **N-gram Repetition** | Detect repetitive patterns in word sequences |

#### 维度2: 结构分析 | Dimension 2: Structure Analysis

| 指标 Metric | 说明 Description |
|-------------|------------------|
| **突发性 Burstiness** | 句子长度标准差/平均值，AI文本此值偏低 |
| **Burstiness** | Std(sentence_length)/Mean, AI text has lower values |
| **段落均质性** | 检测段落长度是否过于整齐 |
| **Paragraph Homogeneity** | Detect if paragraph lengths are too uniform |
| **段落首句模式** | AI倾向每段用"总起句"开头 |
| **Opening Sentence Pattern** | AI tends to start paragraphs with topic sentences |

#### 维度3: 逻辑分析 | Dimension 3: Logic Analysis

| 指标 Metric | 说明 Description |
|-------------|------------------|
| **连接词频率** | 统计"However/Therefore/Moreover"使用频率 |
| **Connector Frequency** | Count usage of "However/Therefore/Moreover" |
| **过渡平滑度** | 检测过度平滑的段落过渡 |
| **Transition Smoothness** | Detect overly smooth paragraph transitions |

### 4.3 风险评分 | Risk Scoring

```
综合风险分数 = Σ(维度分数 × 权重)
Overall Risk Score = Σ(Dimension Score × Weight)

风险等级 Risk Levels:
- 0-30:  低风险 Low Risk     (绿色 Green)
- 31-60: 中风险 Medium Risk  (黄色 Yellow)
- 61-100: 高风险 High Risk   (红色 Red)
```

---

## 五、技术架构 | Technical Architecture

### 5.1 系统架构图 | System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 Frontend                         │
│                    React + TailwindCSS                       │
├─────────────────────────────────────────────────────────────┤
│                        API网关 Gateway                       │
│                         FastAPI                              │
├──────────────────────┬──────────────────────────────────────┤
│    分析引擎层        │           建议生成层                   │
│  Analysis Engine     │      Suggestion Generator             │
│  ┌────────────────┐  │  ┌─────────────┬─────────────┐       │
│  │ Turnitin模拟   │  │  │  轨道A      │  轨道B      │       │
│  │ Turnitin Sim   │  │  │  LLM Engine │  Rule Engine│       │
│  ├────────────────┤  │  │  Claude/GPT │  spaCy+BERT │       │
│  │ GPTZero模拟    │  │  └─────────────┴─────────────┘       │
│  │ GPTZero Sim    │  │                                      │
│  ├────────────────┤  │  ┌─────────────────────────────┐     │
│  │ 通用AIGC检测   │  │  │    多语言解释生成器          │     │
│  │ General AIGC   │  │  │  Multilingual Explainer     │     │
│  └────────────────┘  │  └─────────────────────────────┘     │
├──────────────────────┴──────────────────────────────────────┤
│                      数据层 Data Layer                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐     │
│  │ AI指纹词库   │ │ 同义词词典   │ │ 学术术语白名单   │     │
│  │ Fingerprint  │ │ Synonym Dict │ │ Term Whitelist   │     │
│  └──────────────┘ └──────────────┘ └──────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 技术栈 | Tech Stack

| 层级 Layer | 技术 Technology | 说明 Notes |
|------------|-----------------|------------|
| **前端 Frontend** | React + TailwindCSS | 复杂交互需要React |
| **后端 Backend** | FastAPI (Python) | 高性能，适合ML部署 |
| **NLP核心 NLP Core** | spaCy + Stanza | Stanza对学术文本更准 |
| **ML模型 ML Models** | Transformers (HuggingFace) | BERT MLM, Sentence-BERT |
| **LLM接口 LLM API** | Claude API / OpenAI API | 需设计fallback机制 |
| **语义相似度 Similarity** | Sentence-BERT | all-MiniLM-L6-v2 |
| **数据库 Database** | SQLite / PostgreSQL | MVP用SQLite |

### 5.3 核心模块 | Core Modules

```
src/
├── api/                    # FastAPI 路由
│   ├── routes/
│   └── middleware/
├── core/                   # 核心业务逻辑
│   ├── analyzer/           # 检测分析引擎
│   │   ├── perplexity.py   # PPL计算
│   │   ├── fingerprint.py  # 指纹词检测
│   │   ├── burstiness.py   # 突发性计算
│   │   └── scorer.py       # 综合评分
│   ├── humanizer/          # 人源化引擎
│   │   ├── llm_track.py    # 轨道A: LLM建议
│   │   ├── rule_track.py   # 轨道B: 规则建议
│   │   └── selector.py     # 建议选择器
│   ├── preprocessor/       # 预处理
│   │   ├── segmenter.py    # 分句
│   │   └── term_locker.py  # 术语锁定
│   └── validator/          # 质量验证
│       ├── semantic.py     # 语义相似度
│       └── risk_check.py   # 风险复检
├── data/                   # 数据资源
│   ├── fingerprint_words.json
│   ├── synonyms/
│   └── term_whitelist/
├── prompts/                # Prompt模板
│   ├── humanize.py
│   └── colloquialism.py
└── utils/                  # 工具函数
```

---

## 六、Prompt工程设计 | Prompt Engineering Design

### 6.1 主Prompt模板 | Main Prompt Template

```python
HUMANIZE_PROMPT = """
You are an academic writing advisor helping to make text sound more naturally human-written.

## Original Sentence
{sentence}

## Detected AIGC Issues
{issues}

## Protected Terms (DO NOT MODIFY)
{locked_terms}

## Target Colloquialism Level: {level}/10
{style_guide}

## Word Preferences for This Level
{word_preferences}

## Requirements
1. Preserve EXACT academic meaning
2. Address all detected AIGC issues
3. Match the specified colloquialism level precisely
4. Keep all protected terms unchanged
5. Output must be a single sentence (unless splitting is specifically requested)

## Response Format (JSON)
{
  "rewritten": "your rewritten sentence",
  "changes": [
    {"original": "word1", "replacement": "word2", "reason": "..."}
  ],
  "explanation_zh": "中文解释为什么这样改",
  "risk_reduction": "high/medium/low"
}
"""
```

### 6.2 口语化等级Prompt | Colloquialism Level Prompts

```python
STYLE_GUIDES = {
    "0-2": """
    Style: Most Academic (Journal Paper Level)
    - Use formal academic register exclusively
    - Prefer Latinate vocabulary (utilize, demonstrate, indicate)
    - Use passive voice where appropriate
    - Avoid contractions entirely
    - Use hedging language (it appears that, evidence suggests)
    - Complex sentence structures with subordinate clauses
    """,

    "3-4": """
    Style: Academic Moderate (Thesis Level)
    - Use formal academic vocabulary
    - First person plural acceptable (we found, our results)
    - Avoid contractions in main text
    - Balance passive and active voice
    - Clear but sophisticated sentence structures
    """,

    "5-6": """
    Style: Semi-formal (Conference Paper Level)
    - Mix of academic and common vocabulary
    - Contractions acceptable occasionally
    - Prefer active voice for clarity
    - Varied sentence length
    - Direct statements preferred
    """,

    "7-8": """
    Style: Casual Professional (Tech Blog Level)
    - Prefer common words over academic jargon
    - Contractions encouraged
    - Active voice strongly preferred
    - Short, punchy sentences
    - Conversational but professional
    """,

    "9-10": """
    Style: Casual Informal (Discussion Level)
    - Everyday conversational language
    - Contractions always preferred
    - Informal expressions acceptable
    - Very short sentences, fragments okay
    - Colloquialisms and mild slang okay
    """
}
```

---

## 七、规则引擎设计 | Rule Engine Design

### 7.1 同义词替换模块 | Synonym Replacement Module

```python
# AI指纹词 → 人类常用词 映射表
# AI Fingerprint → Human-preferred Word Mapping
FINGERPRINT_REPLACEMENTS = {
    "delve": ["explore", "examine", "look at", "investigate"],
    "paramount": ["important", "key", "main", "central"],
    "utilize": ["use", "apply", "employ"],
    "facilitate": ["help", "enable", "support"],
    "comprehensive": ["full", "complete", "thorough"],
    "subsequently": ["then", "later", "after that"],
    "aforementioned": ["these", "this", "the above"],
    "pertaining to": ["about", "regarding", "on"],
    "in order to": ["to"],
    "due to the fact that": ["because", "since"],
    "it is important to note that": ["note that", "importantly"],
    "a wide range of": ["many", "various"],
    "in the context of": ["in", "for", "regarding"],
    "plays a crucial role": ["is important", "matters", "helps"],
}
```

### 7.2 句法重组模块 | Syntactic Restructuring Module

| 重组类型 Type | 说明 Description | 示例 Example |
|--------------|------------------|--------------|
| **主动↔被动** Active↔Passive | 语态转换 | "We analyzed..." ↔ "The data was analyzed..." |
| **句子拆分** Split | 长句变短句 | 30+词句子拆为两句 |
| **句子合并** Merge | 短句变复合句 | 两个相关短句合并 |
| **从句移位** Clause Move | 调整从句位置 | 后置从句移到句首 |
| **插入语添加** Parenthetical | 增加节奏变化 | 添加"in fact", "arguably" |

### 7.3 BERT MLM上下文感知替换 | BERT MLM Context-aware Replacement

```python
def context_aware_synonym(sentence: str, target_word: str) -> list:
    """
    Use BERT MLM to find contextually appropriate synonyms
    使用BERT MLM找到上下文合适的同义词
    """
    # 1. Mask target word
    masked = sentence.replace(target_word, "[MASK]")

    # 2. Get BERT predictions
    predictions = bert_mlm(masked, top_k=10)

    # 3. Filter: keep only human-preferred words
    filtered = [p for p in predictions
                if p not in AI_FINGERPRINT_WORDS]

    return filtered[:5]
```

---

## 八、质量控制 | Quality Control

### 8.1 多层验证 | Multi-layer Validation

| 层级 Layer | 检查内容 Check | 阈值 Threshold |
|------------|---------------|----------------|
| **语义层** Semantic | Sentence-BERT相似度 | ≥ 0.80 |
| **事实层** Factual | 关键实体保留检查 | 100% |
| **术语层** Term | 锁定术语完整性 | 100% |
| **风险层** Risk | 改写后风险评分 | 目标值以下 |

### 8.2 回滚机制 | Rollback Mechanism

```
如果验证失败 If validation fails:
1. 语义相似度 < 0.80 → 使用规则建议替代 / Use rule suggestion instead
2. 仍然失败 → 标记为"需人工处理" / Flag as "needs manual review"
3. 最多重试3次 → 超过则跳过 / Max 3 retries, then skip
```

---

## 九、开发阶段 | Development Phases

> 基于三层级架构分析报告更新 Updated based on three-level architecture analysis

### Phase 1: Level 3 核心闭环 ✅ 已完成 | Level 3 Core Loop (Completed)

**目标 Goal:** 跑通"输入→检测→建议→验证→输出"基础流程
**Run through basic "input→detect→suggest→validate→output" flow**

| 任务 Task | 状态 Status |
|-----------|-------------|
| 文本分句模块 Text segmentation | ✅ 已完成 |
| AI指纹词检测 Fingerprint detection | ✅ 已完成 |
| CAASS v2.0 风险评分 Risk scoring | ✅ 已完成 |
| LLM建议生成(轨道A) LLM suggestions (Track A) | ✅ 已完成 |
| 规则替换(轨道B) Rule-based replacement (Track B) | ✅ 已完成 |
| 语义相似度验证 Semantic similarity validation | ✅ 已完成 |
| 干预模式UI Intervention mode UI | ✅ 已完成 |
| 白名单提取 Whitelist extraction | ✅ 已完成 |

### Phase 2: Level 3 增强 | Level 3 Enhancement ✅

**目标 Goal:** 增强 Level 3，为 Level 2 做准备
**Enhance Level 3, prepare for Level 2**

| 任务 Task | 优先级 Priority | 状态 Status |
|-----------|-----------------|-------------|
| Burstiness 检测 Burstiness detection | P1 | ✅ 已完成 |
| 显性连接词检测 Explicit connector detection | P1 | ✅ 已完成 |
| 结构问题预警 Structure issue warning | P1 | ✅ 已完成 |
| Session 配置扩展（核心论点字段） | P1 | ⏳ 待开发 |
| YOLO模式优化 YOLO mode enhancement | P2 | ⏳ 待开发 |

### Phase 3: Level 2 实现 | Level 2 Implementation ✅

**目标 Goal:** 实现段落衔接分析与优化
**Implement paragraph transition analysis and optimization**

| 任务 Task | 优先级 Priority | 状态 Status |
|-----------|-----------------|-------------|
| 滑动窗口段落分析 API | P1 | ✅ 已完成 |
| 过渡策略 Prompt (语义回声/逻辑设问/节奏打断) | P1 | ✅ 已完成 |
| "接缝修补" UI 组件 Transition repair UI | P1 | ✅ 已完成 |
| 批量处理支持 Batch processing | P2 | ✅ 已完成 |

**API 设计 | API Design:**
```python
# POST /api/v1/analyze/transition
class TransitionAnalysisRequest(BaseModel):
    para_a: str  # Previous paragraph
    para_b: str  # Next paragraph
    context_hint: Optional[str]  # Core thesis from Level 1

class TransitionOption(BaseModel):
    strategy: Literal["semantic_echo", "logical_hook", "rhythm_break"]
    para_a_ending: str   # Modified ending of paragraph A
    para_b_opening: str  # Modified opening of paragraph B
```

### Phase 4: Level 1 实现 | Level 1 Implementation ✅ 已完成 Completed

**目标 Goal:** 实现全文逻辑诊断与重构
**Implement full-text logic diagnosis and restructuring**

| 任务 Task | 优先级 Priority | 状态 Status |
|-----------|-----------------|-------------|
| 全文逻辑诊断 API | P1 | ✅ 完成 |
| 两种重构策略 Prompt (优化连接/深度重组) | P1 | ✅ 完成 |
| "逻辑诊断卡" UI 组件 | P1 | ✅ 完成 |
| 新大纲生成与应用 | P2 | ✅ 完成 |

**已实现文件 Implemented Files:**
- `src/core/analyzer/structure.py` - 结构分析器
- `src/prompts/structure.py` - 重组策略 Prompts
- `src/api/routes/structure.py` - API 端点
- `src/api/schemas.py:504-711` - API Schemas
- `frontend/src/types/index.ts:343-493` - 前端类型
- `frontend/src/services/api.ts:572-667` - 前端 API
- `frontend/src/components/editor/StructurePanel.tsx` - UI 组件

**API 设计 | API Design:**
```python
# POST /api/v1/structure/
class StructureAnalysisResponse(BaseModel):
    structure_score: int  # 0-100, higher = more AI-like
    risk_level: str  # low, medium, high
    issues: List[StructureIssue]
    break_points: List[BreakPoint]  # Logic break points
    options: List[StructureOption]  # Two restructuring options
```

### Phase 5: 全流程整合 | Full Flow Integration ✅ 已完成 Completed

**目标 Goal:** 整合三层级处理流程
**Integrate three-level processing flow**

| 任务 Task | 优先级 Priority | 状态 Status |
|-----------|-----------------|-------------|
| 强制流程引导 (L1 → L2 → L3) | P1 | ✅ 完成 |
| 上下文传递机制 Context passing | P1 | ✅ 完成 |
| 处理结果持久化 Result persistence | P2 | ✅ 完成 |
| 快速/深度模式切换 Quick/Deep mode | P2 | ✅ 完成 |

**已实现文件 Implemented Files:**
- `src/core/coordinator/__init__.py` - 模块初始化
- `src/core/coordinator/flow_coordinator.py` - 流程协调器
- `src/api/routes/flow.py` - API 端点
- `frontend/src/types/index.ts:495-573` - 前端类型
- `frontend/src/services/api.ts:669-837` - 前端 API

### Phase 6: 测试与部署 | Testing & Deployment ✅ 已完成 Completed

**目标 Goal:** 系统测试，部署上线
**System testing, deployment**

| 任务 Task | 优先级 Priority | 状态 Status |
|-----------|-----------------|-------------|
| 三层级集成测试 Three-level integration test | P3 | ✅ 完成 |
| 前端构建测试 Frontend build test | P3 | ✅ 完成 |
| API模块导入测试 API module import test | P3 | ✅ 完成 |
| 流程协调器测试 Flow coordinator test | P3 | ✅ 完成 |

### 开发周期预估 | Development Timeline Estimate

| 阶段 Phase | 工作量 Effort | 累计 Cumulative |
|------------|---------------|-----------------|
| Phase 2: L3增强 | 3-5天 | 3-5天 |
| Phase 3: L2实现 | 7-11天 | 10-16天 |
| Phase 4: L1实现 | 7-11天 | 17-27天 |
| Phase 5: 整合 | 4-6天 | 21-33天 |
| Phase 6: 测试部署 | 5-7天 | 26-40天 |

---

## 十、风险与应对 | Risks & Mitigation

| 风险 Risk | 等级 Level | 应对策略 Mitigation |
|-----------|-----------|---------------------|
| LLM输出不稳定 LLM output instability | 高 High | 规则建议作为fallback |
| API成本过高 High API cost | 中 Medium | 优先规则建议，LLM按需调用 |
| 检测器更新导致失效 Detector updates | 中 Medium | 定期更新指纹词库 |
| 术语误改 Term modification errors | 高 High | 强制术语锁定机制 |
| 语义漂移 Semantic drift | 中 Medium | 严格语义相似度阈值 |

---

## 十一、成功指标 | Success Metrics

| 指标 Metric | 目标 Target |
|-------------|-------------|
| 高风险句转低风险率 High→Low risk conversion | ≥ 80% |
| 平均语义保持度 Average semantic similarity | ≥ 85% |
| 单句处理时间 Per-sentence processing time | ≤ 3s |
| 用户满意度 User satisfaction | ≥ 4.0/5.0 |

---

## 附录 | Appendix

### A. AI指纹词库(部分) | AI Fingerprint Words (Partial)

```
高频词 High-frequency:
delve, crucial, paramount, utilize, facilitate, comprehensive,
subsequently, aforementioned, pertaining, realm, tapestry,
multifaceted, leverage, robust, seamless, cutting-edge

高频短语 High-frequency phrases:
"it is important to note", "plays a crucial role",
"in the context of", "a wide range of", "due to the fact that",
"in order to", "as a result of", "with respect to"
```

### B. 参考资源 | References

- GPTZero Detection Methodology
- Turnitin AI Writing Detection
- Perplexity and Burstiness in AI Text Detection
- Academic Writing Style Guides

---

> 文档维护 Document Maintenance:
> 本文档为项目唯一计划文档，所有规划变更需同步更新此文件。
> This is the sole planning document. All planning changes must be synced here.
