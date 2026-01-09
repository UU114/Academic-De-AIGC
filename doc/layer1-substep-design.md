# Layer 1 (Lexical Level) Sub-Step System Design
# 第1层（词汇级）子步骤系统设计

> Version: 1.0
> Date: 2026-01-08
> Purpose: Design comprehensive sub-step workflow for lexical-level De-AIGC processing with paragraph context
> 目的：设计在段落上下文中进行词汇级De-AIGC处理的完整子步骤工作流程

---

## 一、设计概述 | Design Overview

### 1.1 层级定位 | Layer Positioning

```
Layer 5: Document (文章层)     → Step 1.x series ✅ 已实现
Layer 4: Section (章节层)      → Step 2.x series ✅ 已实现
Layer 3: Paragraph (段落层)    → Step 3.x series ✅ 已实现
Layer 2: Sentence (句子层)     → Step 4.x series ✅ 已设计
Layer 1: Lexical (词汇层)      → Step 5.x series 📋 本文档设计
```

### 1.2 Layer 1 核心设计理念 | Core Design Philosophy

**重要原则**：Layer 1 **不是**简单地替换单个词汇，而是**在段落尺度上**综合分析词汇问题：
- 按段落为单位统计AIGC指纹词分布
- 分析人类写作词汇的覆盖率
- 在保护锁定词汇的前提下进行改写
- 先分析问题，再利用AI进行de-AIGC改写
- 改写同时增加人类写作特征
- 确保学术写作的严谨性

**核心操作**：
| 操作类型 | 说明 Description | 目标 Goal |
|---------|-----------------|----------|
| **检测AIGC指纹** | 识别AI特征词汇和短语 | 定位风险点 |
| **分析人类特征缺失** | 检测人类写作特征词汇缺失 | 识别提升空间 |
| **生成替换候选** | 为指纹词生成上下文适配的替换方案 | 准备改写素材 |
| **LLM段落级改写** | 按段落为单位，综合改写降低AI特征 | 消除指纹 |
| **增加人类特征** | 注入人类学术写作特征词汇 | 增强自然度 |
| **验证学术严谨性** | 确保改写保持学术规范 | 质量保障 |

### 1.3 与相邻层的关系 | Relationship with Adjacent Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Layer 2 (Sentence)                           │
│  ├── 传入: sentences[], sentence_contexts[]                        │
│  ├── 传入: sentence_roles[], paragraph_sentence_map                │
│  └── 传入: pattern_issues[], connector_issues[]                    │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌───────────────────────────────────────────────────────────────────────┐
│                        Layer 1 (Lexical)                              │
│  ├── 接收: 句子上下文 (roles, patterns, positions)                  │
│  ├── 接收: 锁定词汇 (locked_terms from Step 1.0)                    │
│  ├── 分析: 段落内的AIGC指纹词分布                                    │
│  ├── 分析: 人类写作特征词汇覆盖                                      │
│  ├── 操作: 生成替换候选、LLM改写、人类特征注入                       │
│  └── 传出: final_text + analysis_report                             │
└───────────────────────────────────────────────────────────────────────┘
                                ↓
                        最终输出 Final Output
```

---

## 二、AIGC与人类词汇特征库 | AIGC vs Human Vocabulary Feature Database

### 2.1 AIGC指纹词汇分类 | AIGC Fingerprint Word Categories

基于 `words.csv` 和 `AIGC_vs_Human_Academic_Lexicon.xlsx` 的统计规律：

#### 2.1.1 Type A: 死证词 (Dead Giveaways) - 风险权重 +40

| 词汇 Word | 权重 Weight | 类型 Type | 典型上下文 Context |
|-----------|-------------|-----------|-------------------|
| delve (into) | 99 | Verb | 常用于Introduction |
| underscore | 95 | Verb | 用于过度强调 |
| harness | 92 | Verb | "harnessing power/potential" |
| unveil | 87 | Verb | 揭示新概念 |
| pivotal | 98 | Adjective | "至关重要" |
| intricate | 96 | Adjective | "复杂的细节" |
| multifaceted | 94 | Adjective | "多方面的" |
| paramount | 88 | Adjective | "最重要的" |
| tapestry | 93 | Noun | 抽象组合比喻 |
| realm | 95 | Noun | "领域" |
| landscape | 97 | Noun | 环境比喻 |

#### 2.1.2 Type B: 学术陈词 (Academic Clichés) - 风险权重 +5-25

| 词汇 Word | 权重 Weight | 类型 Type | 人类替代 Human Alternative |
|-----------|-------------|-----------|---------------------------|
| comprehensive | 91 | Adjective | thorough, full, complete |
| robust | 89 | Adjective | strong, reliable, solid |
| seamless | 86 | Adjective | smooth, integrated |
| leverage | 90 | Verb | use, apply, employ |
| facilitate | 84 | Verb | help, enable, support |
| utilize | - | Verb | use, apply |
| crucial | 85 | Adjective | important, key, essential |
| holistic | 85 | Adjective | complete, whole, integrated |
| transformative | 84 | Adjective | significant, major |

#### 2.1.3 Type C: 指纹短语 (Fingerprint Phrases) - 风险权重 +15-35

| 短语 Phrase | 权重 Weight | 人类替代 Human Alternative |
|-------------|-------------|---------------------------|
| In conclusion | 99 | To conclude, Ultimately, Finally |
| Important to note | 96 | Notably, Note that |
| Not only...but also | 94 | Beyond X, Y. / X. Also, Y. |
| Ever-evolving | 95 | Changing, Developing |
| Crucial role | 92 | Important role, Key function |
| In the realm of | 30 | In, Within, Regarding |
| A plethora of | 82 | Many, Numerous, Various |
| Pave the way | 88 | Enable, Allow, Facilitate |
| Shed light on | 88 | Explain, Clarify, Reveal |

### 2.2 人类学术写作特征词汇 | Human Academic Writing Features

基于 `words.csv` 中 Human 类别的统计：

#### 2.2.1 高频动词 (High-frequency Verbs) - 目标覆盖率 ≥15%

| 词汇 Word | 权重 Weight | 用法 Usage |
|-----------|-------------|-----------|
| examine | 95 | 具体研究 |
| argue | 92 | 陈述立场 |
| suggest | 90 | 谨慎结论 |
| demonstrate | 87 | 展示证据 |
| observe | 86 | 记录数据 |
| identify | 84 | 精确定位 |
| investigate | 88 | 深入研究 |
| analyze | 88 | 数据分析 |
| validate | 82 | 验证确认 |
| assess | 84 | 评估判断 |

#### 2.2.2 学术形容词 (Academic Adjectives) - 目标覆盖率 ≥10%

| 词汇 Word | 权重 Weight | 用法 Usage |
|-----------|-------------|-----------|
| significant | 98 | 统计意义 |
| associated (with) | 96 | 相关性 |
| specific | 94 | 精确的 |
| empirical | 92 | 基于数据 |
| consistent | 90 | 一致的 |
| preliminary | 85 | 初步阶段 |
| quantitative | 90 | 定量的 |
| qualitative | 90 | 定性的 |
| limited | 88 | 范围限制 |

#### 2.2.3 学术短语 (Academic Phrases) - 目标覆盖率 ≥5%

| 短语 Phrase | 权重 Weight | 用法 Usage |
|-------------|-------------|-----------|
| Results indicate | 95 | 数据驱动 |
| In contrast to | 94 | 对比 |
| To our knowledge | 92 | 范围限定 |
| Data suggest | 89 | 证据支持 |
| Consistent with | 88 | 文献对齐 |
| Future research | 87 | 下一步 |
| Standard deviation | 90 | 统计术语 |
| Account for | 82 | 解释原因 |

### 2.3 检测指标阈值 | Detection Metric Thresholds

| 指标 Metric | AI特征阈值 | 人类特征目标 | 说明 |
|------------|-----------|-------------|------|
| Type A指纹词数量 | > 0 | = 0 | 死证词必须清除 |
| Type B指纹词密度 | > 2% | < 1% | 每100词中的占比 |
| Type C短语数量 | > 3 | ≤ 1 | 每1000词 |
| 人类动词覆盖率 | < 10% | ≥ 15% | 目标词汇覆盖 |
| 人类形容词覆盖率 | < 5% | ≥ 10% | 目标词汇覆盖 |
| 人类短语出现率 | < 2% | ≥ 5% | 目标短语出现 |

---

## 三、子步骤设计方案 | Sub-Step Design Proposal

### 3.0 执行流程图 | Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Layer 1: Lexical Level Analysis                           │
│                    词汇级分析（基于段落上下文，先分析后改写）                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 5.0: 词汇环境准备 (Lexical Context Preparation)              │     │
│  │  ├── 接收句子层上下文 Receive sentence context from Layer 2        │     │
│  │  ├── 继承锁定词汇列表 Inherit locked terms from Step 1.0           │     │
│  │  ├── 建立段落-词汇映射 Build paragraph-term mapping                │     │
│  │  └── 加载词汇特征库 Load vocabulary feature database               │     │
│  │                                                                     │     │
│  │  检测器：ContextLoader                                              │     │
│  │  输出：paragraph_term_map{}, locked_terms[], feature_db             │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 5.1: AIGC指纹词检测 (AIGC Fingerprint Detection)             │     │
│  │  ├── Type A死证词检测 Detect Dead Giveaway words                   │     │
│  │  ├── Type B学术陈词检测 Detect Academic Cliché words               │     │
│  │  ├── Type C指纹短语检测 Detect Fingerprint phrases                 │     │
│  │  ├── 按段落统计分布 Per-paragraph distribution statistics          │     │
│  │  └── 排除锁定词汇 Exclude locked terms from detection              │     │
│  │                                                                     │     │
│  │  检测器：FingerprintDetector (Enhanced)                            │     │
│  │  输出：fingerprint_issues[], density_per_para{}, risk_score        │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 5.2: 人类特征词汇分析 (Human Feature Vocabulary Analysis)    │     │
│  │  ├── 检测人类学术动词覆盖 Detect human academic verb coverage      │     │
│  │  ├── 检测人类形容词覆盖 Detect human adjective coverage            │     │
│  │  ├── 检测人类短语出现率 Detect human phrase occurrence             │     │
│  │  ├── 计算人类特征得分 Calculate human feature score                │     │
│  │  └── 识别可注入人类特征的位置 Identify injection points            │     │
│  │                                                                     │     │
│  │  检测器：HumanFeatureAnalyzer (NEW)                                │     │
│  │  输出：human_coverage{}, feature_score, injection_points[]         │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 5.3: 替换候选生成 (Replacement Candidate Generation)         │     │
│  │  ├── 为每个AIGC指纹词生成候选 Generate candidates per fingerprint  │     │
│  │  ├── 考虑上下文语义适配 Consider contextual semantic fitness        │     │
│  │  ├── 考虑口语化等级 Consider colloquialism level                   │     │
│  │  ├── 优先选择人类特征词 Prefer human feature words                 │     │
│  │  └── 生成规则建议(Track B) Generate rule-based suggestions         │     │
│  │                                                                     │     │
│  │  检测器：ReplacementCandidateGenerator                             │     │
│  │  输出：replacement_candidates{}, rule_suggestions[]                │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 5.4: LLM段落级改写 (LLM Paragraph-Level Rewriting)           │     │
│  │  ├── 按段落为单位批量改写 Batch rewrite by paragraph               │     │
│  │  ├── 传入AIGC问题分析 Pass AIGC issue analysis                     │     │
│  │  ├── 传入人类特征目标 Pass human feature targets                   │     │
│  │  ├── 保护锁定词汇 Protect locked terms                             │     │
│  │  ├── 应用学术写作规范 Apply academic writing norms                 │     │
│  │  └── 生成LLM建议(Track A) Generate LLM suggestions                 │     │
│  │                                                                     │     │
│  │  检测器：LLMParagraphRewriter                                      │     │
│  │  输出：rewritten_paragraphs[], llm_suggestions[], changes[]        │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 5.5: 改写结果验证 (Rewrite Result Validation)                │     │
│  │  ├── 语义相似度验证 Semantic similarity validation (≥0.85)        │     │
│  │  ├── AIGC风险降低评估 AIGC risk reduction assessment               │     │
│  │  ├── 人类特征提升评估 Human feature improvement assessment         │     │
│  │  ├── 学术规范检查 Academic norm verification                       │     │
│  │  └── 锁定词汇完整性检查 Locked term integrity check                │     │
│  │                                                                     │     │
│  │  检测器：RewriteValidator                                          │     │
│  │  输出：validation_results{}, final_paragraphs[], quality_report    │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│                     输出最终文本和分析报告 Output final text & report        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、各子步骤详细设计 | Detailed Design for Each Sub-Step

### Step 5.0: 词汇环境准备 (Lexical Context Preparation)

**目的 Purpose**：作为Layer 1的基础步骤，接收上层上下文，准备词汇分析所需的环境。

**核心功能**：
| 功能 Function | 说明 Description |
|--------------|------------------|
| 接收句子层上下文 | 从Layer 2接收句子及段落映射 |
| 继承锁定词汇 | 从Step 1.0获取用户确认的锁定词汇列表 |
| 建立段落-词汇映射 | 为每个段落建立词汇索引 |
| 加载词汇特征库 | 加载AIGC指纹库和人类特征库 |

**输入数据结构**：
```python
class LexicalContextRequest(BaseModel):
    document_text: str
    session_id: str  # Required for locked terms
    sentence_context: Optional[Dict]  # From Layer 2
        # sentences: List[SentenceInfo]
        # sentence_roles: List[str]
        # paragraph_sentence_map: Dict[int, List[int]]
    colloquialism_level: int = 4  # 0-10
```

**输出数据结构**：
```python
class LexicalContextResponse(BaseModel):
    paragraphs: List[ParagraphLexicalInfo]
    locked_terms: List[str]
    total_words: int
    feature_db_loaded: bool

class ParagraphLexicalInfo(BaseModel):
    index: int
    text: str
    word_count: int
    sentences: List[str]
    word_positions: Dict[str, List[int]]  # word → [positions]
```

---

### Step 5.1: AIGC指纹词检测 (AIGC Fingerprint Detection)

**目的 Purpose**：检测文档中的AIGC指纹词汇和短语，按段落统计分布，排除锁定词汇。

**检测类型**：
| 类型 Type | 风险权重 Risk | 检测方法 Method |
|----------|--------------|-----------------|
| Type A: 死证词 | +40/match | 精确匹配词典 |
| Type B: 学术陈词 | +5-25/match | 精确匹配词典 |
| Type C: 指纹短语 | +15-35/match | 正则表达式匹配 |

**检测项**：
| 检测项 Detection | 触发条件 Trigger | 风险等级 Risk |
|-----------------|-----------------|---------------|
| 死证词出现 | Type A count > 0 | Critical |
| 指纹词密度高 | density > 2% | High |
| 指纹短语过多 | phrase count > 3/1000词 | High |
| 段落指纹集中 | 单段密度 > 5% | Medium |

**锁定词汇处理**：
```python
# Locked terms are NEVER flagged as fingerprints
# Example: If "delve" is locked (technical term), skip detection
for fingerprint in detected_fingerprints:
    if any(locked.lower() in fingerprint.lower()
           for locked in locked_terms):
        continue  # Skip this fingerprint
```

**输出数据结构**：
```python
class FingerprintDetectionResponse(BaseModel):
    total_fingerprints: int
    type_a_matches: List[FingerprintMatch]
    type_b_matches: List[FingerprintMatch]
    phrase_matches: List[PhraseMatch]
    density_per_paragraph: Dict[int, float]
    overall_density: float
    risk_score: int  # 0-100
    issues: List[DetectionIssue]

class FingerprintMatch(BaseModel):
    word: str
    count: int
    risk_weight: int
    paragraph_indices: List[int]
    positions: List[MatchPosition]
    is_locked: bool  # True if overlaps with locked term
```

**用户界面设计**：
```
┌─────────────────────────────────────────────────────────────────┐
│ Step 5.1: AIGC指纹词检测 AIGC Fingerprint Detection              │
├─────────────────────────────────────────────────────────────────┤
│ 检测结果 Detection Results:                                      │
│                                                                  │
│ 整体指纹密度: 3.2% [高风险] ⚠️                                   │
│ 整体风险分数: 72/100 [高风险]                                    │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Type A 死证词 (Dead Giveaways):                     4 个    │ │
│ │ ├── "delve" × 2 (Para 1, Para 5) [+80]                     │ │
│ │ ├── "tapestry" × 1 (Para 3) [+40]                          │ │
│ │ └── "multifaceted" × 1 (Para 7) [+40]                      │ │
│ │                                                             │ │
│ │ Type B 学术陈词 (Academic Clichés):                 8 个    │ │
│ │ ├── "comprehensive" × 3 [+30]                              │ │
│ │ ├── "robust" × 2 [+30]                                     │ │
│ │ └── "leverage" × 3 [+45]                                   │ │
│ │                                                             │ │
│ │ Type C 指纹短语 (Fingerprint Phrases):              3 个    │ │
│ │ ├── "plays a crucial role" × 2 [+60]                       │ │
│ │ └── "in the realm of" × 1 [+30]                            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ 🔒 锁定词汇已排除: "methodology", "framework" (不计入风险)       │
│                                                                  │
│ 段落分布 Paragraph Distribution:                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Para 1:  ████████████░░░░░░░░  4.5% ⚠️ High                │ │
│ │ Para 2:  ██████░░░░░░░░░░░░░░  2.1%                        │ │
│ │ Para 3:  ████████████████░░░░  5.8% ⚠️⚠️ Critical          │ │
│ │ Para 4:  ████░░░░░░░░░░░░░░░░  1.2% ✅ Low                 │ │
│ │ Para 5:  ██████████░░░░░░░░░░  3.5% ⚠️ High                │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ [查看详情] [继续下一步 →]                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

### Step 5.2: 人类特征词汇分析 (Human Feature Vocabulary Analysis)

**目的 Purpose**：分析文档中人类学术写作特征词汇的覆盖率，识别可以增强人类特征的位置。

**检测维度**：
| 维度 Dimension | 目标词汇 Target | 目标覆盖率 Target |
|---------------|----------------|------------------|
| 学术动词 | examine, argue, suggest, demonstrate... | ≥15% |
| 学术形容词 | significant, empirical, specific... | ≥10% |
| 学术短语 | "results indicate", "in contrast to"... | ≥5% |
| 谨慎表述 | "may", "could", "suggests", "appears"... | ≥8% |

**输出数据结构**：
```python
class HumanFeatureAnalysisResponse(BaseModel):
    verb_coverage: CoverageStats
    adjective_coverage: CoverageStats
    phrase_coverage: CoverageStats
    hedging_coverage: CoverageStats
    overall_human_score: int  # 0-100
    feature_gaps: List[FeatureGap]
    injection_points: List[InjectionPoint]

class CoverageStats(BaseModel):
    target_words: List[str]
    found_words: List[str]
    found_count: int
    coverage_rate: float
    target_rate: float
    is_sufficient: bool

class InjectionPoint(BaseModel):
    paragraph_index: int
    sentence_index: int
    suggested_features: List[str]
    reason: str
    reason_zh: str
```

**用户界面设计**：
```
┌─────────────────────────────────────────────────────────────────┐
│ Step 5.2: 人类特征词汇分析 Human Feature Vocabulary Analysis     │
├─────────────────────────────────────────────────────────────────┤
│ 人类特征得分 Human Feature Score: 38/100 [需改进]                │
│                                                                  │
│ 特征覆盖率 Coverage Analysis:                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 类别        │ 当前  │ 目标  │ 状态                          │ │
│ │─────────────│───────│───────│──────────────────────────────│ │
│ │ 学术动词    │ 8%    │ ≥15%  │ ⚠️ 不足 (缺少examine,argue)  │ │
│ │ 学术形容词  │ 6%    │ ≥10%  │ ⚠️ 不足 (缺少empirical)      │ │
│ │ 学术短语    │ 2%    │ ≥5%   │ ⚠️ 不足 (缺少对比表述)       │ │
│ │ 谨慎表述    │ 4%    │ ≥8%   │ ⚠️ 不足 (缺少hedging)        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ 已检测到的人类特征词:                                            │
│ • 动词: "suggest" × 2, "demonstrate" × 1, "identify" × 1        │
│ • 形容词: "significant" × 3, "consistent" × 1                   │
│ • 短语: "results indicate" × 1                                  │
│                                                                  │
│ 建议增加的人类特征 Suggested Additions:                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Para 1: 建议增加 "examine", "investigate"                   │ │
│ │ Para 3: 建议增加 "in contrast to", "data suggest"          │ │
│ │ Para 5: 建议增加谨慎表述 "may", "appears to"               │ │
│ │ Para 7: 建议增加 "empirical", "quantitative"               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ [查看详情] [继续下一步 →]                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

### Step 5.3: 替换候选生成 (Replacement Candidate Generation)

**目的 Purpose**：为每个检测到的AIGC指纹词生成上下文适配的替换候选，优先选择人类特征词汇。

**生成策略**：
| 策略 Strategy | 说明 Description | 优先级 Priority |
|--------------|-----------------|-----------------|
| 人类特征词优先 | 用人类特征词替换 | P0 |
| 口语化等级适配 | 根据设定等级选择 | P1 |
| 上下文语义适配 | 考虑前后文语义 | P1 |
| 学术规范适配 | 确保替换后符合学术规范 | P2 |

**替换映射示例**：
```python
REPLACEMENT_MAP = {
    # Type A → Human feature words
    "delve": {
        "academic": ["examine", "investigate", "explore"],
        "moderate": ["study", "look at", "analyze"],
        "casual": ["look into", "check out", "dig into"]
    },
    "tapestry": {
        "academic": ["combination", "array", "synthesis"],
        "moderate": ["mix", "collection", "range"],
        "casual": ["mix", "combo", "blend"]
    },
    # Type B → Simpler alternatives
    "comprehensive": {
        "academic": ["thorough", "complete", "extensive"],
        "moderate": ["full", "detailed", "complete"],
        "casual": ["full", "complete", "detailed"]
    },
    "leverage": {
        "academic": ["employ", "use", "apply"],
        "moderate": ["use", "apply", "build on"],
        "casual": ["use", "take advantage of"]
    },
    # Phrases → Academic alternatives
    "plays a crucial role": {
        "academic": "is essential to",
        "moderate": "is important for",
        "casual": "matters for"
    },
    "in the realm of": {
        "academic": "within",
        "moderate": "in",
        "casual": "in"
    }
}
```

**输出数据结构**：
```python
class ReplacementCandidateResponse(BaseModel):
    candidates: List[ReplacementCandidate]
    rule_suggestions: List[RuleSuggestion]  # Track B
    total_replaceable: int

class ReplacementCandidate(BaseModel):
    original: str
    original_type: str  # type_a, type_b, phrase
    candidates: List[CandidateOption]
    paragraph_index: int
    sentence_index: int
    context: str  # surrounding text

class CandidateOption(BaseModel):
    replacement: str
    is_human_feature: bool
    colloquialism_level: str
    confidence: float
    reason: str
    reason_zh: str
```

---

### Step 5.4: LLM段落级改写 (LLM Paragraph-Level Rewriting)

**目的 Purpose**：核心改写步骤，按段落为单位进行综合改写，消除AIGC指纹并增加人类特征。

**改写原则**：
| 原则 Principle | 说明 Description |
|---------------|------------------|
| 段落整体性 | 保持段落内部逻辑和语义连贯 |
| 锁定词保护 | 锁定词汇不得修改，在Prompt中明确标注 |
| AIGC消除 | 替换所有Type A词汇，降低Type B/C密度 |
| 人类特征注入 | 在适当位置增加人类学术写作特征 |
| 学术严谨性 | 保持学术写作规范，避免口语化过度 |
| 语义保持 | 改写后语义相似度 ≥ 0.85 |

**Prompt设计**：
```python
PARAGRAPH_REWRITE_PROMPT = """
## TASK: Rewrite paragraph to reduce AI detection while maintaining academic rigor

## Original Paragraph
{paragraph_text}

## AIGC Issues Detected (MUST FIX):
{aigc_issues}

## Human Feature Injection Targets:
{human_feature_targets}

## PROTECTED TERMS (DO NOT MODIFY - these are technical terms):
{locked_terms}

## Colloquialism Level: {level}/10
{style_guide}

## CRITICAL RULES:
1. **AIGC Elimination**:
   - Replace ALL Type A words: {type_a_list}
   - Replace Type B words where possible: {type_b_list}
   - Rewrite Type C phrases: {phrase_list}

2. **Human Feature Enhancement**:
   - Inject academic verbs: examine, investigate, demonstrate, identify
   - Use hedging language: suggests, may, appears to, could potentially
   - Add academic phrases: "results indicate", "in contrast to", "data suggest"

3. **Locked Term Protection**:
   - The following terms MUST remain UNCHANGED: {locked_terms}
   - Do not replace, paraphrase, or modify these terms

4. **Academic Rigor**:
   - Maintain formal academic register (for level 0-5)
   - Preserve logical flow and argumentation
   - Keep citation formats intact
   - Use precise, specific language (avoid vague generalizations)

5. **Semantic Preservation**:
   - Maintain the EXACT same meaning
   - Do not add new claims or information
   - Do not remove important qualifications

## Response Format (JSON):
{{
  "rewritten_paragraph": "...",
  "changes": [
    {{"original": "...", "replacement": "...", "reason": "...", "reason_zh": "..."}}
  ],
  "aigc_removed": ["delve", "tapestry"],
  "human_features_added": ["examine", "suggests"],
  "locked_terms_preserved": true,
  "semantic_similarity_estimate": 0.92
}}
"""
```

**批量处理策略**：
```python
async def batch_rewrite_paragraphs(
    paragraphs: List[str],
    aigc_issues_per_para: Dict[int, List],
    human_targets_per_para: Dict[int, List],
    locked_terms: List[str],
    colloquialism_level: int
) -> List[RewriteResult]:
    """
    Process paragraphs in batches to optimize LLM calls
    按批次处理段落以优化LLM调用
    """
    results = []

    # Group paragraphs by risk level for prioritization
    high_risk = [i for i, issues in aigc_issues_per_para.items()
                 if len(issues) > 3]
    medium_risk = [i for i, issues in aigc_issues_per_para.items()
                   if 1 <= len(issues) <= 3]
    low_risk = [i for i, issues in aigc_issues_per_para.items()
                if len(issues) == 0]

    # Process high-risk paragraphs with full LLM attention
    for para_idx in high_risk:
        result = await rewrite_paragraph_llm(
            paragraphs[para_idx],
            aigc_issues_per_para[para_idx],
            human_targets_per_para.get(para_idx, []),
            locked_terms,
            colloquialism_level
        )
        results.append(result)

    # Process medium-risk with hybrid approach
    for para_idx in medium_risk:
        # Try rule-based first, fallback to LLM if needed
        result = await rewrite_paragraph_hybrid(...)
        results.append(result)

    # Low-risk paragraphs: rule-based only
    for para_idx in low_risk:
        result = rewrite_paragraph_rules(...)
        results.append(result)

    return results
```

**用户界面设计**：
```
┌─────────────────────────────────────────────────────────────────┐
│ Step 5.4: LLM段落级改写 LLM Paragraph-Level Rewriting           │
├─────────────────────────────────────────────────────────────────┤
│ 改写进度 Rewriting Progress:                                     │
│                                                                  │
│ [████████████████████░░░░░░░░░░] 60% (6/10 paragraphs)          │
│                                                                  │
│ 当前段落 Current Paragraph (Para 3 - High Risk):                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 原文 Original:                                              │ │
│ │ "This study delves into the multifaceted tapestry of       │ │
│ │  machine learning, leveraging comprehensive datasets..."    │ │
│ │                                                             │ │
│ │ 改写后 Rewritten:                                           │ │
│ │ "This study examines the complex interactions within       │ │
│ │  machine learning, using extensive datasets..."            │ │
│ │                                                             │ │
│ │ 变更 Changes:                                               │ │
│ │ • "delves into" → "examines" [AIGC消除+人类特征]           │ │
│ │ • "multifaceted tapestry" → "complex interactions" [消除]  │ │
│ │ • "leveraging" → "using" [降低AI特征]                      │ │
│ │ • "comprehensive" → "extensive" [降低AI特征]               │ │
│ │                                                             │ │
│ │ 🔒 保护词汇完好: "machine learning", "datasets"            │ │
│ │ 📊 语义相似度: 94%                                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ 双轨建议 Dual-Track Suggestions:                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [A] LLM建议 - 风险: 25 | 语义: 94% | 人类特征: +3          │ │
│ │ [B] 规则建议 - 风险: 35 | 语义: 98% | 人类特征: +1          │ │
│ │ [C] 自定义 ___________________________________________      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ [接受A] [接受B] [手动修改] [跳过] [下一段 →]                     │
└─────────────────────────────────────────────────────────────────┘
```

---

### Step 5.5: 改写结果验证 (Rewrite Result Validation)

**目的 Purpose**：验证改写结果的质量，确保语义保持、AIGC风险降低、人类特征提升、学术规范符合。

**验证维度**：
| 维度 Dimension | 阈值 Threshold | 验证方法 Method |
|---------------|---------------|-----------------|
| 语义相似度 | ≥ 0.85 | Sentence-BERT |
| AIGC风险降低 | 降低 ≥ 30% | 重新检测 |
| 人类特征提升 | 提升 ≥ 10% | 重新分析 |
| 锁定词完整 | 100% | 精确匹配 |
| 学术规范 | 通过 | 规则检查 |

**学术规范检查项**：
```python
ACADEMIC_NORM_CHECKS = {
    "no_contractions": {
        "pattern": r"\b(don't|won't|can't|isn't|aren't|wasn't|weren't)\b",
        "level_threshold": 5,  # Only check for level 0-5
        "message": "Academic writing should avoid contractions"
    },
    "no_first_person": {
        "pattern": r"\b(I|we|my|our|us|me)\b",
        "level_threshold": 5,
        "message": "Academic writing should avoid first-person pronouns"
    },
    "no_informal_language": {
        "pattern": r"\b(kind of|sort of|basically|actually|really|pretty much)\b",
        "level_threshold": 6,
        "message": "Academic writing should avoid informal language"
    },
    "citation_preserved": {
        "check": "citation_format_unchanged",
        "message": "Citations must remain in original format"
    }
}
```

**输出数据结构**：
```python
class ValidationResponse(BaseModel):
    overall_pass: bool
    semantic_similarity: float
    aigc_risk_before: int
    aigc_risk_after: int
    risk_reduction: float
    human_feature_before: int
    human_feature_after: int
    feature_improvement: float
    locked_terms_preserved: bool
    academic_norm_violations: List[NormViolation]
    final_paragraphs: List[ValidatedParagraph]
    quality_report: QualityReport

class ValidatedParagraph(BaseModel):
    index: int
    original: str
    rewritten: str
    accepted: bool
    validation_scores: Dict[str, float]
    issues: List[str]

class QualityReport(BaseModel):
    total_paragraphs: int
    paragraphs_improved: int
    paragraphs_unchanged: int
    paragraphs_failed: int
    overall_quality_score: int
    recommendations: List[str]
```

**用户界面设计**：
```
┌─────────────────────────────────────────────────────────────────┐
│ Step 5.5: 改写结果验证 Rewrite Result Validation                 │
├─────────────────────────────────────────────────────────────────┤
│ 整体验证结果 Overall Validation: ✅ 通过                         │
│                                                                  │
│ 质量指标 Quality Metrics:                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 指标              │ 改写前 │ 改写后 │ 变化   │ 状态          │ │
│ │───────────────────│────────│────────│────────│───────────────│ │
│ │ AIGC风险分数      │ 72     │ 28     │ -61%   │ ✅ 大幅降低   │ │
│ │ 人类特征得分      │ 38     │ 65     │ +71%   │ ✅ 显著提升   │ │
│ │ 平均语义相似度    │ -      │ 91%    │ -      │ ✅ ≥85%      │ │
│ │ 锁定词汇完整性    │ -      │ 100%   │ -      │ ✅ 全部保留   │ │
│ │ 学术规范符合      │ -      │ 98%    │ -      │ ✅ 通过       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ 段落验证详情 Paragraph Validation Details:                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Para 1: ✅ 通过 (语义:93%, 风险:72→25, 人类:+15)           │ │
│ │ Para 2: ✅ 通过 (语义:95%, 风险:45→20, 人类:+8)            │ │
│ │ Para 3: ✅ 通过 (语义:89%, 风险:85→30, 人类:+22)           │ │
│ │ Para 4: ⚠️ 警告 (语义:84%, 接近阈值)                       │ │
│ │ Para 5: ✅ 通过 (语义:92%, 风险:60→28, 人类:+12)           │ │
│ │ ...                                                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ 学术规范问题 Academic Norm Issues (1):                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Para 4: 检测到缩写 "don't" → 建议改为 "do not"             │ │
│ │         [自动修复] [忽略]                                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ [导出报告] [返回修改] [确认完成 ✓]                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 五、API设计 | API Design

### 5.1 端点设计 | Endpoint Design

```python
# Step 5.0: Prepare context
@router.post("/api/v1/analysis/layer1/context")
async def prepare_lexical_context(
    request: LexicalContextRequest
) -> LexicalContextResponse:
    """Prepare lexical analysis context"""
    pass

# Step 5.1: Fingerprint detection
@router.post("/api/v1/analysis/layer1/fingerprint")
async def detect_fingerprints(
    request: FingerprintDetectionRequest
) -> FingerprintDetectionResponse:
    """Detect AIGC fingerprint words and phrases"""
    pass

# Step 5.2: Human feature analysis
@router.post("/api/v1/analysis/layer1/human-features")
async def analyze_human_features(
    request: HumanFeatureAnalysisRequest
) -> HumanFeatureAnalysisResponse:
    """Analyze human academic writing feature coverage"""
    pass

# Step 5.3: Generate replacement candidates
@router.post("/api/v1/analysis/layer1/candidates")
async def generate_replacement_candidates(
    request: ReplacementCandidateRequest
) -> ReplacementCandidateResponse:
    """Generate replacement candidates for fingerprint words"""
    pass

# Step 5.4: LLM paragraph rewriting
@router.post("/api/v1/analysis/layer1/rewrite")
async def rewrite_paragraphs(
    request: ParagraphRewriteRequest
) -> ParagraphRewriteResponse:
    """Rewrite paragraphs to reduce AIGC and enhance human features"""
    pass

# Step 5.5: Validate results
@router.post("/api/v1/analysis/layer1/validate")
async def validate_results(
    request: ValidationRequest
) -> ValidationResponse:
    """Validate rewrite results"""
    pass

# Combined endpoint for full Layer 1 processing
@router.post("/api/v1/analysis/layer1/full")
async def process_layer1_full(
    request: Layer1FullRequest
) -> Layer1FullResponse:
    """Run complete Layer 1 analysis and rewriting pipeline"""
    pass
```

### 5.2 数据流设计 | Data Flow Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Layer 1 Data Flow                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Input from Layer 2                                                  │
│  ├── sentences[]                                                     │
│  ├── sentence_contexts[]                                             │
│  ├── paragraph_sentence_map{}                                        │
│  └── locked_terms[] (from Step 1.0)                                 │
│                                                                      │
│        ↓ Step 5.0                                                    │
│  ┌──────────────────────────┐                                       │
│  │ paragraph_term_map{}     │ ← Build word-paragraph mapping        │
│  │ feature_db               │ ← Load AIGC/Human feature DB          │
│  └──────────────────────────┘                                       │
│                                                                      │
│        ↓ Step 5.1                                                    │
│  ┌──────────────────────────┐                                       │
│  │ fingerprint_issues[]     │ ← Detected AIGC fingerprints          │
│  │ density_per_para{}       │ ← Per-paragraph density               │
│  │ risk_score               │ ← Overall risk score                  │
│  └──────────────────────────┘                                       │
│                                                                      │
│        ↓ Step 5.2                                                    │
│  ┌──────────────────────────┐                                       │
│  │ human_coverage{}         │ ← Human feature coverage              │
│  │ injection_points[]       │ ← Where to add human features         │
│  │ feature_gaps[]           │ ← What features are missing           │
│  └──────────────────────────┘                                       │
│                                                                      │
│        ↓ Step 5.3                                                    │
│  ┌──────────────────────────┐                                       │
│  │ replacement_candidates{} │ ← Candidates per fingerprint          │
│  │ rule_suggestions[]       │ ← Track B suggestions                 │
│  └──────────────────────────┘                                       │
│                                                                      │
│        ↓ Step 5.4                                                    │
│  ┌──────────────────────────┐                                       │
│  │ rewritten_paragraphs[]   │ ← LLM rewritten text                  │
│  │ llm_suggestions[]        │ ← Track A suggestions                 │
│  │ changes[]                │ ← Detailed change log                 │
│  └──────────────────────────┘                                       │
│                                                                      │
│        ↓ Step 5.5                                                    │
│  ┌──────────────────────────┐                                       │
│  │ validation_results{}     │ ← Validation scores                   │
│  │ final_paragraphs[]       │ ← Validated final text                │
│  │ quality_report           │ ← Overall quality assessment          │
│  └──────────────────────────┘                                       │
│                                                                      │
│  Output                                                              │
│  ├── final_document_text                                            │
│  ├── analysis_report                                                │
│  └── change_log[]                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 六、与现有系统集成 | Integration with Existing System

### 6.1 与 LexicalOrchestrator 的关系

现有的 `lexical_orchestrator.py` 实现了基础的指纹检测和连接词分析。新设计将：

1. **保留现有检测逻辑** - Step 5.1 复用 `FINGERPRINT_TYPE_A/B/C` 词典
2. **增强检测能力** - 添加人类特征分析（Step 5.2）
3. **添加改写能力** - 整合 `llm_track.py` 和 `rule_track.py`（Step 5.4）
4. **添加验证机制** - 新增验证步骤（Step 5.5）

### 6.2 与双轨系统的关系

| 组件 Component | 集成方式 Integration |
|----------------|---------------------|
| `llm_track.py` | Step 5.4 使用 LLMTrack 生成建议 |
| `rule_track.py` | Step 5.3/5.4 使用 RuleTrack 生成候选 |
| 锁定词汇 | 从 `get_locked_terms_from_session()` 获取 |

### 6.3 代码结构建议

```
src/core/analyzer/layers/
├── lexical_orchestrator.py     # 重构以支持子步骤
├── lexical/                    # NEW: 子步骤模块
│   ├── __init__.py
│   ├── context_preparation.py  # Step 5.0
│   ├── fingerprint_detector.py # Step 5.1 (增强)
│   ├── human_feature_analyzer.py # Step 5.2 (NEW)
│   ├── candidate_generator.py  # Step 5.3 (NEW)
│   ├── paragraph_rewriter.py   # Step 5.4 (NEW)
│   └── result_validator.py     # Step 5.5 (NEW)

src/api/routes/analysis/
├── lexical.py                  # 现有路由增强
├── lexical/                    # NEW: 子步骤端点
│   ├── __init__.py
│   ├── context.py              # Step 5.0 API
│   ├── fingerprint.py          # Step 5.1 API
│   ├── human_features.py       # Step 5.2 API
│   ├── candidates.py           # Step 5.3 API
│   ├── rewrite.py              # Step 5.4 API
│   └── validate.py             # Step 5.5 API

src/data/
├── aigc_fingerprints.json      # AIGC指纹词库
├── human_features.json         # 人类特征词库 (NEW)
└── replacement_map.json        # 替换映射表
```

---

## 七、实现优先级 | Implementation Priority

| 优先级 Priority | 子步骤 Sub-Step | 原因 Reason |
|----------------|----------------|-------------|
| **P0** | Step 5.0 词汇环境准备 | 基础步骤，所有后续步骤依赖 |
| **P0** | Step 5.1 AIGC指纹检测 | 核心检测，已有基础实现 |
| **P1** | Step 5.4 LLM段落级改写 | 核心改写功能，用户感知最强 |
| **P1** | Step 5.5 改写结果验证 | 质量保障，必须与改写同步 |
| **P2** | Step 5.2 人类特征分析 | 增强功能，提升改写质量 |
| **P2** | Step 5.3 替换候选生成 | 支持双轨建议，可渐进实现 |

---

## 八、与其他Layer设计的对比 | Comparison with Other Layers

| 特点 Feature | Layer 2 (句子) | Layer 1 (词汇) |
|-------------|---------------|---------------|
| **分析单元** | 句子在段落中 | 词汇在段落中 |
| **上下文** | 段落上下文 | 句子+段落上下文 |
| **主要操作** | 合并/拆分/调整句子 | 替换/改写词汇 |
| **LLM使用** | 句式多样化 | 段落级综合改写 |
| **规则使用** | 句法重组规则 | 词汇替换规则 |
| **人类特征** | 句式多样性 | 词汇覆盖率 |
| **用户交互** | 确认句式变化 | 确认词汇替换 |

---

## 九、总结 | Summary

Layer 1 (词汇层) 子步骤系统设计的核心特点：

1. **先分析后改写** - Step 5.1-5.2 全面分析问题，Step 5.4 针对性改写
2. **段落为单位** - 按段落统计、分析、改写，保持上下文连贯
3. **锁定词保护** - 全流程保护用户锁定的专业术语
4. **双向优化** - 同时消除AIGC指纹和增加人类特征
5. **双轨建议** - 结合LLM智能改写和规则确定性替换
6. **学术严谨** - 验证环节确保学术写作规范
7. **质量验证** - 多维度验证确保改写质量

**详细设计请参考本文档各章节 For detailed design, see each section of this document**
