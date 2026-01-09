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

---

## 十二、检测逻辑重构计划 | Detection Logic Refactoring Plan

> 状态 Status: ✅ 已完成 / Completed
> 详细文档 Detailed Document: `doc/refactoring-plan.md`
> 创建日期 Created: 2026-01-07
> 完成日期 Completed: 2026-01-07

### 12.1 重构目标 | Refactoring Goals

将当前分散的检测逻辑重构为统一的**5层架构**，实现从粗到细的颗粒度检测。

Refactor scattered detection logic into a unified **5-layer architecture** with coarse-to-fine granularity.

### 12.2 新5层架构 | New 5-Layer Architecture

```
Layer 5: Document (文章层)     → Step 1.x series
Layer 4: Section (章节层)      → Step 2.x series  [NEW]
Layer 3: Paragraph (段落层)    → Step 3.x series
Layer 2: Sentence (句子层)     → Step 4.x series
Layer 1: Lexical (词汇层)      → Step 5.x series  [NEW]
```

### 12.3 各层步骤分配 | Step Allocation by Layer

| 层级 Layer | 步骤 Steps | 主要功能 Main Functions |
|------------|-----------|-------------------------|
| Document | 1.1 结构分析, 1.2 全局风险 | 全文结构模式检测，风险评估 |
| Section | 2.1 逻辑流, 2.2 章节衔接, 2.3 长度分布 | 章节关系、过渡、均衡性 |
| Paragraph | 3.1 角色, 3.2 连贯性, 3.3 锚点, 3.4 句长分布 | 段落功能、内聚性、锚点密度 |
| Sentence | 4.1 模式, 4.2 空洞, 4.3 角色, 4.4 润色 | 句式检测、空洞检测、句子改写 |
| Lexical | 5.1 指纹词, 5.2 连接词, 5.3 词级风险 | 词汇级别检测与替换 |

### 12.4 关键设计原则 | Key Design Principles

1. **从粗到细 Coarse to Fine**: Document → Section → Paragraph → Sentence → Word
2. **句子段落化 Sentence-in-Paragraph**: 句子层分析必须在段落上下文中进行
3. **段落级句子指标**: 句子长度分布分析属于段落层（Step 3.4）而非句子层
4. **上下文传递 Context Passing**: 每层接收上层传递的上下文信息
5. **灵活步骤 Flexible Steps**: 层内步骤可根据检测问题动态调整

### 12.5 待集成模块 | Modules to Integrate

| 模块 Module | 目标层 Target Layer | 功能 Function |
|-------------|-------------------|---------------|
| `syntactic_void.py` | Sentence (4.2) | 句法空洞检测 (spaCy) |
| `structure_predictability.py` | Document (1.1) | 5维结构可预测性评分 |
| `anchor_density.py` | Paragraph (3.3) | 13类锚点密度分析 |

### 12.6 实施阶段 | Implementation Phases

| 阶段 Phase | 内容 Content | 状态 Status |
|------------|-------------|-------------|
| Phase 1 | 后端重构 Backend Restructure | ✅ 已完成 (2026-01-07) |
| Phase 2 | API重构 API Refactoring | ✅ 已完成 (2026-01-07) |
| Phase 3 | 前端重构 Frontend Refactoring | ✅ 已完成 (2026-01-07) |
| Phase 4 | 集成测试 Integration Testing | ✅ 已完成 (2026-01-07) |

**5层架构重构已全部完成！详见 `doc/refactoring-plan.md` 和 `doc/process.md`**
**5-Layer Architecture Refactoring Complete! See `doc/refactoring-plan.md` and `doc/process.md` for details**

---

## 十三、Layer 5 子步骤系统设计 | Layer 5 Sub-Step System Design

> 状态 Status: 🚧 设计完成，待实现 / Design Complete, Pending Implementation
> 详细文档 Detailed Document: `doc/layer5-substep-design.md`
> 创建日期 Created: 2026-01-07

### 13.1 设计目标 | Design Goals

将 Layer 5 (文档层) 的检测功能细化为5个有序的子步骤，整合所有已有和待集成的检测器。

Subdivide Layer 5 (Document Layer) detection into 5 ordered sub-steps, integrating all existing and pending detectors.

### 13.2 子步骤概览 | Sub-Step Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Layer 5: Document Level Analysis                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1.0: 词汇锁定 Term Locking ⭐ NEW                             │
│  ├── LLM提取专业名词和高频实义词 Extract Technical Terms            │
│  ├── 用户多选确认锁定词汇 User Multi-select Confirmation            │
│  └── 锁定词汇规则应用到后续所有LLM步骤                              │
│                          ↓                                           │
│  ═══════════════════════════════════════════════════════════════    │
│  ║  locked_terms 传递到所有后续步骤的LLM Prompt中  ║                │
│  ═══════════════════════════════════════════════════════════════    │
│                          ↓                                           │
│  Step 1.1: 结构框架检测 Structure Framework Detection               │
│  ├── 章节对称性 Section Symmetry                                    │
│  ├── 章节顺序可预测性 Section Order Predictability                  │
│  └── 全局逻辑流动 Global Logic Flow (linear_flow)                   │
│                          ↓                                           │
│  Step 1.2: 段落长度规律性 Paragraph Length Regularity               │
│  ├── 段落长度均匀性 Length Uniformity (CV analysis)                 │
│  ├── 章节内段落数量均匀性 Section Paragraph Count                   │
│  └── 段落功能均匀性 Function Uniformity                             │
│                          ↓                                           │
│  Step 1.3: 推进模式与闭合 Progression & Closure Detection           │
│  ├── 单调推进模式 Monotonic Progression Pattern                     │
│  ├── 重复结构模式 Repetitive Pattern                                │
│  └── 闭合强度 Closure Strength                                      │
│                          ↓                                           │
│  Step 1.4: 连接词与衔接 Connectors & Transitions                    │
│  ├── 显性连接词检测 Explicit Connector Detection                    │
│  ├── 连接词显性度分析 Connector Explicitness                        │
│  ├── 段落衔接模式 Transition Patterns                               │
│  └── 词汇回声分析 Lexical Echo Analysis                             │
│                          ↓                                           │
│  Step 1.5: 内容实质性 Content Substantiveness                       │
│  ├── 学术锚点密度 Anchor Density                                    │
│  └── 幻觉风险评估 Hallucination Risk                                │
│                          ↓                                           │
│              传递修改后的文本到 Layer 4 (Section)                    │
│              (locked_terms 继续传递到所有后续Layer)                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 13.3 检测器集成方案 | Detector Integration Plan

| 子步骤 Sub-Step | 检测器 Detectors | 集成状态 Status |
|----------------|-----------------|-----------------|
| **Step 1.0** | **LLM Term Extractor (新建)** | **⏳ 待开发** |
| Step 1.1 | SmartStructureAnalyzer + StructurePredictabilityAnalyzer | ⚠️ 部分集成 |
| Step 1.2 | ParagraphLengthAnalysis + StructurePredictabilityAnalyzer | ⚠️ 部分集成 |
| Step 1.3 | StructurePredictabilityAnalyzer | ⚠️ 待集成 |
| Step 1.4 | TransitionAnalyzer + StructurePredictabilityAnalyzer | ✅ 已集成 |
| Step 1.5 | AnchorDensityAnalyzer | ⚠️ 待集成 |

### 13.4 用户交互模式 | User Interaction Pattern

```
每个子步骤的交互流程 Interaction Flow for Each Sub-Step:
1. 检测 Detection → 显示问题列表 Display Issue List
2. 用户点击问题 User Clicks Issue → 触发AI分析 Trigger AI Analysis
3. AI提供 AI Provides:
   - 改进建议 Improvement Suggestions
   - 改写提示词 Rewrite Prompts
   - 合并处理选项 Batch Processing Options
4. 用户选择 User Chooses:
   - 接受AI建议自动修改 Accept AI Auto-modify
   - 手动修改 Manual Edit
   - 跳过 Skip
5. 完成后 After Completion → 传递给下一子步骤 Pass to Next Sub-Step
```

### 13.5 实现优先级 | Implementation Priority

| 优先级 Priority | 子步骤 Sub-Step | 原因 Reason |
|----------------|----------------|-------------|
| **P0** | **Step 1.0 词汇锁定** | **必须首先完成，锁定词汇传递到所有后续LLM步骤** |
| P1 | Step 1.4 连接词与衔接 | TransitionAnalyzer 已有，用户感知最强 |
| P1 | Step 1.2 段落长度 | ParagraphLengthAnalysis 已有，实现简单 |
| P2 | Step 1.3 推进模式与闭合 | 需完整集成 StructurePredictabilityAnalyzer |
| P2 | Step 1.1 结构框架 | 需合并多个检测器 |
| P3 | Step 1.5 内容实质性 | 需集成 AnchorDensityAnalyzer |

> **Step 1.0 词汇锁定的核心功能**：
> - LLM提取专业术语、专有名词、缩写词、高频核心词、关键词组
> - 用户多选确认哪些词汇需要锁定
> - 锁定词汇自动注入到后续所有LLM调用的Prompt中
> - 支持跨Layer传递（Layer 5 → 4 → 3 → 2 → 1）

**详细设计请参考 `doc/layer5-substep-design.md`**
**For detailed design, see `doc/layer5-substep-design.md`**

---

## 十四、Layer 3 子步骤系统设计 | Layer 3 Sub-Step System Design

> 状态 Status: 📋 设计完成，待实现 / Design Complete, Pending Implementation
> 详细文档 Detailed Document: `doc/layer3-substep-design.md`
> 创建日期 Created: 2026-01-07

### 14.1 设计目标 | Design Goals

将 Layer 3 (段落层) 的检测功能细化为6个有序的子步骤，整合所有已有的段落级检测器。

Subdivide Layer 3 (Paragraph Layer) detection into 6 ordered sub-steps, integrating all existing paragraph-level detectors.

### 14.2 子步骤概览 | Sub-Step Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Layer 3: Paragraph Level Analysis                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 3.0: 段落识别与分割 Paragraph Identification & Segmentation   │
│  ├── 接收Section上下文 Receive section context from Layer 4        │
│  ├── 正确识别段落边界 Identify paragraph boundaries                 │
│  └── 过滤非正文内容 Filter non-body content                         │
│                          ↓                                           │
│  Step 3.1: 段落角色识别 Paragraph Role Detection                     │
│  ├── 识别每个段落的功能角色 Identify functional role                 │
│  └── 检测角色分布异常 Detect role distribution anomalies             │
│                          ↓                                           │
│  Step 3.2: 段落内部连贯性 Internal Coherence Analysis                │
│  ├── 主语多样性分析 Subject diversity analysis                       │
│  ├── 逻辑结构检测 Logic structure detection                          │
│  └── 连接词密度分析 Connector density analysis                       │
│                          ↓                                           │
│  Step 3.3: 锚点密度分析 Anchor Density Analysis                      │
│  ├── 13类学术锚点检测 Detect 13 types of academic anchors           │
│  └── 幻觉风险评估 Hallucination risk assessment                      │
│                          ↓                                           │
│  Step 3.4: 段内句长分布 Sentence Length Distribution                 │
│  ├── 计算段内句长变异系数 Calculate within-paragraph length CV       │
│  └── 突发性分析 Burstiness analysis                                  │
│                          ↓                                           │
│  Step 3.5: 段落间过渡检测 Paragraph Transition Analysis              │
│  ├── 相邻段落衔接分析 Adjacent paragraph transition analysis         │
│  └── 提供语义桥接建议 Provide semantic bridging suggestions          │
│                          ↓                                           │
│              传递段落上下文到 Layer 2 (Sentence)                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 14.3 检测器集成方案 | Detector Integration Plan

| 子步骤 Sub-Step | 检测器 Detectors | 集成状态 Status |
|----------------|-----------------|-----------------|
| Step 3.0 | SentenceSegmenter (content type detection) | ✅ 已有 |
| Step 3.1 | LLM Role Classifier + Keyword patterns | ⚠️ 部分集成 |
| Step 3.2 | ParagraphLogicAnalyzer | ✅ 已集成 |
| Step 3.3 | AnchorDensityAnalyzer | ✅ 已集成 |
| Step 3.4 | Statistical CV + BurstinessAnalyzer | ✅ 已集成 |
| Step 3.5 | TransitionAnalyzer + LLM suggestions | ✅ 已集成 |

### 14.4 与Layer 5/Layer 4的对比 | Comparison

| 层级 Layer | 基础步骤 (X.0) | 主要步骤 | 关注点 Focus |
|-----------|---------------|---------|-------------|
| **Layer 5** | 1.0 词汇锁定 | 1.1-1.5 | 全文结构、章节顺序、段落长度、连接词 |
| **Layer 4** | 2.0 章节识别 | 2.1-2.5 | 章节顺序、长度分布、相似性、过渡、逻辑 |
| **Layer 3** | 3.0 段落识别 | 3.1-3.5 | 段落角色、连贯性、锚点、句长、过渡 |

### 14.5 实现优先级 | Implementation Priority

| 优先级 Priority | 子步骤 Sub-Step | 原因 Reason |
|----------------|----------------|-------------|
| **P0** | Step 3.0 段落识别 | 基础步骤，所有后续步骤依赖 |
| **P1** | Step 3.2 内部连贯性 | ParagraphLogicAnalyzer已有 |
| **P1** | Step 3.3 锚点密度 | AnchorDensityAnalyzer已有 |
| **P2** | Step 3.4 句长分布 | 统计计算简单 |
| **P2** | Step 3.1 段落角色 | 需要LLM支持 |
| **P3** | Step 3.5 过渡检测 | TransitionAnalyzer已有 |

**详细设计请参考 `doc/layer3-substep-design.md`**
**For detailed design, see `doc/layer3-substep-design.md`**

---

## 十五、Layer 2 子步骤系统设计 | Layer 2 Sub-Step System Design

> 状态 Status: 📋 设计完成，待实现 / Design Complete, Pending Implementation
> 详细文档 Detailed Document: `doc/layer2-substep-design.md`
> 创建日期 Created: 2026-01-08

### 15.1 设计目标 | Design Goals

将 Layer 2 (句子层) 的检测与改写功能细化为6个有序的子步骤。**核心理念**：不是单独分析某一个句子，而是在**段落尺度**上分析每个句子的句式、逻辑、长短、框架等，实现句子级的合并、拆分、多样化改写。

Subdivide Layer 2 (Sentence Layer) detection and rewriting into 6 ordered sub-steps. **Core Philosophy**: Analyze each sentence within the **paragraph context**, not in isolation. Perform sentence merging, splitting, and diversification to reduce AIGC detection.

### 15.2 子步骤概览 | Sub-Step Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Layer 2: Sentence Level Analysis                   │
│                    句子级分析（基于段落上下文，非孤立分析）            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 4.0: 句子识别与标注 Sentence Identification & Labeling        │
│  ├── 接收段落上下文 Receive paragraph context from Layer 3          │
│  ├── 分割段落为句子 Split paragraphs into sentences                 │
│  └── 标注句子类型和功能 Label sentence type and function            │
│                          ↓                                           │
│  Step 4.1: 句式结构分析 Sentence Pattern Analysis                    │
│  ├── 分析句式类型分布 Analyze sentence type distribution            │
│  ├── 检测句首词汇重复 Detect sentence opener repetition             │
│  ├── 分析语态分布 Analyze voice distribution (active/passive)       │
│  └── 检测从句嵌套深度 Detect subordinate clause depth               │
│                          ↓                                           │
│  Step 4.2: 段内句长分析 In-Paragraph Length Analysis                 │
│  ├── 计算每段内的句长分布 Calculate length distribution per para    │
│  ├── 检测句长均匀性 Detect length uniformity (CV < 0.25)           │
│  └── 生成合并/拆分候选 Generate merge/split candidates              │
│                          ↓                                           │
│  Step 4.3: 句子合并建议 Sentence Merger Suggestions                  │
│  ├── 识别语义相近的相邻句子 Identify semantically related pairs     │
│  ├── 生成嵌套从句合并方案 Generate nested clause combinations       │
│  └── 评估合并后的可读性 Evaluate readability after merge            │
│                          ↓                                           │
│  Step 4.4: 句间连接词优化 Inter-Sentence Connector Optimization      │
│  ├── 检测句间显性连接词 Detect explicit sentence connectors         │
│  ├── 提供隐性连接替代方案 Provide implicit alternatives             │
│  └── 删除冗余连接词 Remove redundant connectors                     │
│                          ↓                                           │
│  Step 4.5: 句式多样化改写 Pattern Diversification & Rewriting        │
│  ├── 变换句子开头 Transform sentence openers                        │
│  ├── 调整语态 Switch voice (active↔passive)                         │
│  ├── 添加倒装/强调结构 Add inversion/emphasis structures            │
│  └── 综合改写建议 Comprehensive rewrite suggestions                 │
│                          ↓                                           │
│              传递句子上下文到 Layer 1 (Lexical)                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 15.3 检测维度与阈值 | Detection Dimensions & Thresholds

| 检测维度 Dimension | AI特征阈值 | 人类特征目标 | 说明 |
|-------------------|-----------|-------------|------|
| 简单句比例 | > 60% | 40-60% | 句式类型分布 |
| 句长CV (段内) | < 0.25 | ≥ 0.35 | 句长变异系数 |
| 句首词重复率 | > 30% | < 20% | 同一开头词频率 |
| "The" 开头比例 | > 40% | < 25% | 定冠词开头 |
| 显性连接词比例 | > 40% | < 25% | Furthermore等 |
| 被动句比例 | < 10% | 15-30% | 语态平衡 |
| 从句嵌套深度 | < 1.2 | ≥ 1.5 | 句式复杂度 |

### 15.4 核心操作 | Core Operations

| 操作类型 Operation | 说明 Description | 目标 Goal |
|-------------------|-----------------|----------|
| **增加句式多样性** | 打破 SVO 单一模式 | 降低句式检测率 |
| **调整句子** | 变换句子开头、语态、语序 | 增加随机性 |
| **合并句子** | 将语义相近的短句合并为复杂长句（嵌套从句） | 增加句长变异 |
| **拆分句子** | 将过长的句子拆分为短句 | 增加节奏变化 |
| **修正显性连接词** | 删除或替换 Furthermore/Moreover 等 | 降低连接词检测 |

### 15.5 合并策略 | Merge Strategies

| 合并类型 Merge Type | 使用从句 Subordinate | 示例 Example |
|--------------------|---------------------|--------------|
| 因果关系 Causal | because, since, as | "A happens. B results." → "Since A happens, B results." |
| 对比关系 Contrast | although, while, whereas | "A is true. B differs." → "Although A is true, B differs." |
| 时序关系 Temporal | when, after, before | "A occurred. Then B." → "After A occurred, B happened." |
| 补充关系 Addition | which, that, where | "A exists. A has property." → "A, which has property, exists." |
| 条件关系 Conditional | if, provided, unless | "A is needed. B follows." → "If A is provided, B follows." |

### 15.6 实现优先级 | Implementation Priority

| 优先级 Priority | 子步骤 Sub-Step | 原因 Reason |
|----------------|----------------|-------------|
| **P0** | Step 4.0 句子识别 | 基础步骤，所有后续步骤依赖 |
| **P1** | Step 4.1 句式结构分析 | 核心检测，用户感知强 |
| **P1** | Step 4.2 段内句长分析 | 与Layer 3关联，数据可复用 |
| **P2** | Step 4.4 连接词优化 | 规则明确，实现简单 |
| **P2** | Step 4.3 句子合并 | 需要LLM支持，复杂度高 |
| **P3** | Step 4.5 多样化改写 | 综合步骤，依赖前面所有步骤 |

### 15.7 与Layer 3的关键区别 | Key Differences from Layer 3

| 特点 Feature | Layer 3 (段落) | Layer 2 (句子) |
|-------------|---------------|---------------|
| **分析单元** | 段落作为整体 | 段落内的每个句子 |
| **上下文** | 章节上下文 | 段落上下文 |
| **操作类型** | 检测+建议 | 检测+合并/拆分/改写 |
| **LLM使用** | 分析+建议 | 分析+改写+生成 |
| **用户交互** | 确认问题 | 确认改写结果 |

**详细设计请参考 `doc/layer2-substep-design.md`**
**For detailed design, see `doc/layer2-substep-design.md`**

---

## 十六、Layer 1 子步骤系统设计 | Layer 1 Sub-Step System Design

> 状态 Status: 📋 设计完成，待实现 / Design Complete, Pending Implementation
> 详细文档 Detailed Document: `doc/layer1-substep-design.md`
> 创建日期 Created: 2026-01-08

### 16.1 设计目标 | Design Goals

将 Layer 1 (词汇层) 的检测与改写功能细化为6个有序的子步骤。**核心理念**：在**段落尺度上**综合分析词汇问题，先分析后改写，同时消除AIGC指纹和增加人类写作特征。

Subdivide Layer 1 (Lexical Layer) detection and rewriting into 6 ordered sub-steps. **Core Philosophy**: Analyze vocabulary issues at the **paragraph level**, analyze first then rewrite, eliminating AIGC fingerprints while adding human writing features.

### 16.2 子步骤概览 | Sub-Step Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Layer 1: Lexical Level Analysis                   │
│                    词汇级分析（先分析后改写，段落为单位）              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 5.0: 词汇环境准备 (Lexical Context Preparation)               │
│  ├── 接收句子层上下文 Receive sentence context from Layer 2        │
│  ├── 继承锁定词汇列表 Inherit locked terms from Step 1.0           │
│  └── 建立段落-词汇映射 Build paragraph-term mapping                │
│                          ↓                                           │
│  Step 5.1: AIGC指纹词检测 (AIGC Fingerprint Detection)              │
│  ├── Type A死证词检测 Detect Dead Giveaway words                   │
│  ├── Type B学术陈词检测 Detect Academic Cliché words               │
│  ├── Type C指纹短语检测 Detect Fingerprint phrases                 │
│  └── 按段落统计分布 Per-paragraph distribution statistics          │
│                          ↓                                           │
│  Step 5.2: 人类特征词汇分析 (Human Feature Vocabulary Analysis)     │
│  ├── 检测人类学术动词覆盖 Detect human academic verb coverage      │
│  ├── 检测人类形容词覆盖 Detect human adjective coverage            │
│  ├── 计算人类特征得分 Calculate human feature score                │
│  └── 识别可注入人类特征的位置 Identify injection points            │
│                          ↓                                           │
│  Step 5.3: 替换候选生成 (Replacement Candidate Generation)          │
│  ├── 为每个AIGC指纹词生成候选 Generate candidates per fingerprint  │
│  ├── 考虑上下文语义适配 Consider contextual semantic fitness        │
│  ├── 优先选择人类特征词 Prefer human feature words                 │
│  └── 生成规则建议(Track B) Generate rule-based suggestions         │
│                          ↓                                           │
│  Step 5.4: LLM段落级改写 (LLM Paragraph-Level Rewriting)            │
│  ├── 按段落为单位批量改写 Batch rewrite by paragraph               │
│  ├── 传入AIGC问题分析 Pass AIGC issue analysis                     │
│  ├── 传入人类特征目标 Pass human feature targets                   │
│  ├── 保护锁定词汇 Protect locked terms                             │
│  └── 应用学术写作规范 Apply academic writing norms                 │
│                          ↓                                           │
│  Step 5.5: 改写结果验证 (Rewrite Result Validation)                 │
│  ├── 语义相似度验证 Semantic similarity validation (≥0.85)        │
│  ├── AIGC风险降低评估 AIGC risk reduction assessment               │
│  ├── 人类特征提升评估 Human feature improvement assessment         │
│  └── 学术规范检查 Academic norm verification                       │
│                          ↓                                           │
│              输出最终文本和分析报告 Output final text & report       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 16.3 AIGC与人类词汇特征库 | AIGC vs Human Vocabulary Database

基于 `words.csv` 和 `AIGC_vs_Human_Academic_Lexicon.xlsx` 的统计规律：

| 类别 Category | 词汇示例 Examples | 权重 Weight |
|--------------|------------------|-------------|
| **AIGC Type A (死证词)** | delve, tapestry, multifaceted, pivotal, realm | 99-93 |
| **AIGC Type B (学术陈词)** | comprehensive, robust, leverage, facilitate | 91-84 |
| **AIGC Phrases (指纹短语)** | "plays a crucial role", "in the realm of" | 92-75 |
| **Human Verbs (人类动词)** | examine, argue, suggest, demonstrate, identify | 95-82 |
| **Human Adjectives (人类形容词)** | significant, empirical, specific, consistent | 98-85 |
| **Human Phrases (人类短语)** | "results indicate", "in contrast to", "data suggest" | 95-82 |

### 16.4 检测指标阈值 | Detection Metric Thresholds

| 指标 Metric | AI特征阈值 | 人类特征目标 | 说明 |
|------------|-----------|-------------|------|
| Type A指纹词数量 | > 0 | = 0 | 死证词必须清除 |
| Type B指纹词密度 | > 2% | < 1% | 每100词中的占比 |
| 人类动词覆盖率 | < 10% | ≥ 15% | 目标词汇覆盖 |
| 人类形容词覆盖率 | < 5% | ≥ 10% | 目标词汇覆盖 |
| 人类短语出现率 | < 2% | ≥ 5% | 目标短语出现 |

### 16.5 实现优先级 | Implementation Priority

| 优先级 Priority | 子步骤 Sub-Step | 原因 Reason |
|----------------|----------------|-------------|
| **P0** | Step 5.0 词汇环境准备 | 基础步骤，所有后续步骤依赖 |
| **P0** | Step 5.1 AIGC指纹检测 | 核心检测，已有基础实现 |
| **P1** | Step 5.4 LLM段落级改写 | 核心改写功能，用户感知最强 |
| **P1** | Step 5.5 改写结果验证 | 质量保障，必须与改写同步 |
| **P2** | Step 5.2 人类特征分析 | 增强功能，提升改写质量 |
| **P2** | Step 5.3 替换候选生成 | 支持双轨建议，可渐进实现 |

### 16.6 与现有系统的关系 | Relationship with Existing System

| 组件 Component | 集成方式 Integration |
|----------------|---------------------|
| `lexical_orchestrator.py` | Step 5.1 复用现有指纹检测逻辑 |
| `llm_track.py` | Step 5.4 使用 LLMTrack 生成建议 |
| `rule_track.py` | Step 5.3/5.4 使用 RuleTrack 生成候选 |
| 锁定词汇系统 | 从 `get_locked_terms_from_session()` 获取 |

**详细设计请参考 `doc/layer1-substep-design.md`**
**For detailed design, see `doc/layer1-substep-design.md`**
