# Layer 4 (Section Level) Sub-Step System Design
# 第4层（章节级）子步骤系统设计

> Version: 1.0
> Date: 2026-01-07
> Purpose: Design comprehensive sub-step workflow for section-level De-AIGC processing

---

## 一、Layer 4 完整检测能力汇总
## All Section-Level Detection Capabilities Summary

### 1.1 章节结构检测 | Section Structure Detection

| 编号 | 功能名称 | 英文 | 检测内容 | AI特征判定 |
|------|----------|------|----------|------------|
| A | 章节角色识别 | section_role_detection | 识别每个章节的功能角色 | 基础分析 |
| B | 章节顺序可预测性 | predictable_section_order | 检测章节顺序是否严格遵循学术模板 | 匹配度 ≥ 80% = AI |
| C | 缺失章节检测 | missing_sections | 检测是否缺少关键章节 | 低风险参考 |
| D | 章节功能融合度 | section_function_fusion | 检测每个章节是否只做一件事 | 功能单一 = AI |

### 1.2 章节衔接检测 | Section Transition Detection

| 编号 | 功能名称 | 英文 | 检测内容 | AI特征判定 |
|------|----------|------|----------|------------|
| E | 显性过渡词检测 | explicit_transition_words | 检测章节间的连接词 | 过多 = AI |
| F | 过渡词强度分类 | transition_strength | Strong/Moderate/Weak 分级 | Strong过多 = AI |
| G | 章节间语义回声 | section_semantic_echo | 检测是否用关键词回声替代显性过渡 | 缺少 = AI |
| H | 章节开头模式 | section_opener_pattern | 检测章节第一句的起始模式 | 模式单一 = AI |

### 1.3 章节长度分布检测 | Section Length Distribution

| 编号 | 功能名称 | 英文 | 检测内容 | AI特征判定 |
|------|----------|------|----------|------------|
| I | 章节长度CV | section_length_cv | 计算所有章节长度的变异系数 | CV < 0.3 = AI |
| J | 极端长度检测 | extreme_section_length | 检测过短/过长章节 | 无极端 = AI |
| K | 关键章节权重 | key_section_weight | 检测核心章节是否比背景章节更长 | 均匀 = AI |
| L | 段落数量变异 | paragraph_count_variance | 检测各章节的段落数量是否均匀 | CV < 0.3 = AI |

### 1.4 章节内部结构检测 | Section Internal Structure

| 编号 | 功能名称 | 英文 | 检测内容 | AI特征判定 |
|------|----------|------|----------|------------|
| M | 子标题深度变异 | heading_depth_variance | 检测各章节的子标题层级深度是否一致 | 过于一致 = AI |
| N | 章节内论点密度 | argument_density | 检测每个章节包含的论点数量 | 密度均匀 = AI |
| **R** | **章节内部逻辑结构相似性** | **internal_structure_similarity** | **比较不同章节的内部逻辑模式** | **相似度 > 80% = AI** |

### 1.5 章节间逻辑检测 | Inter-Section Logic Detection

| 编号 | 功能名称 | 英文 | 检测内容 | AI特征判定 |
|------|----------|------|----------|------------|
| O | 论证链完整性 | argument_chain_completeness | 检测章节间因果逻辑链是否过于完美 | 过于清晰 = AI |
| P | 章节间信息重复 | inter_section_redundancy | 检测相邻章节是否有过度总结/预告 | 过度重复 = AI |
| Q | 递进关系检测 | progression_pattern | 检测章节是否呈现过于规整的递进模式 | 完美递进 = AI |

---

## 二、优先级、兼容性、依赖性、冲突性分析
## Priority, Compatibility, Dependency, Conflict Analysis

### 2.1 优先级分析 | Priority Analysis

#### 高优先级（基础性问题）| High Priority (Foundational)

| 问题 | 优先级 | 理由 |
|------|--------|------|
| A 章节角色识别 | ★★★★★ | 所有章节分析的基础，必须最先完成 |
| B 章节顺序可预测性 | ★★★★☆ | 章节结构的核心问题 |
| I 章节长度CV | ★★★★☆ | 快速识别AI均匀化特征 |

#### 中优先级（结构性问题）| Medium Priority (Structural)

| 问题 | 优先级 | 理由 |
|------|--------|------|
| D 功能融合度 | ★★★☆☆ | 依赖章节识别完成 |
| R 内部逻辑相似性 | ★★★☆☆ | 新增核心检测，需要段落功能标注 |
| E+F 过渡词检测 | ★★★☆☆ | 章节衔接的主要问题 |

#### 低优先级（细节问题）| Low Priority (Detail)

| 问题 | 优先级 | 理由 |
|------|--------|------|
| M+N 子标题+论点密度 | ★★☆☆☆ | 细节检测，可选 |
| O+P+Q 章节间逻辑 | ★★☆☆☆ | 深层逻辑分析，最后处理 |

---

### 2.2 依赖性分析 | Dependency Analysis

```
从 Layer 5 接收: locked_terms[], modified_text, document_structure
    ↓
A (章节角色识别) ← 最基础，所有分析依赖正确的章节识别
    ↓
┌───────────────────────────────────────────────────────┐
│           以下分析都依赖 A 的章节边界结果              │
├───────────────────────────────────────────────────────┤
│                                                       │
│  B+C+D (章节顺序与结构)                               │
│     ↓                                                 │
│  I+J+K+L (章节长度与段落数量分布)                     │
│     ↓                                                 │
│  R+M+N (章节内部结构) ← 依赖段落功能标注              │
│     ↓                                                 │
│  E+F+G+H (章节衔接) ← 依赖章节边界                    │
│     ↓                                                 │
│  O+P+Q (章节间逻辑) ← 依赖衔接分析结果                │
│                                                       │
└───────────────────────────────────────────────────────┘
    ↓
传递修改后的文本到 Layer 3 (Paragraph)
```

---

### 2.3 兼容性分析 | Compatibility Analysis

#### 可合并的问题组 | Compatible Groups

| 组 | 包含问题 | 兼容原因 |
|----|----------|----------|
| **组1** | A (角色识别) | 独立基础步骤 |
| **组2** | B (顺序) + C (缺失) + D (功能融合) | 都是章节宏观结构问题 |
| **组3** | I (长度CV) + J (极端) + K (权重) + L (段落数) | 都是数量/长度分布问题 |
| **组4** | R (内部相似性) + M (子标题) + N (论点密度) | 都是章节内部结构问题 |
| **组5** | E (过渡词) + F (强度) + G (语义回声) + H (开头模式) | 都是章节衔接问题 |
| **组6** | O (论证链) + P (信息重复) + Q (递进) | 都是章节间逻辑问题 |

---

### 2.4 冲突性分析 | Conflict Analysis

| 先A后B | 冲突描述 | 解决方案 |
|--------|----------|----------|
| D→R | 先处理功能融合（拆分/合并章节），会改变内部结构相似性检测对象 | **先R后D**，先检测相似性，再决定是否调整 |
| I→D | 先调章节长度，可能需要拆分/合并章节 | **先D后I**，先确定章节边界，再调长度 |
| E→O | 先删过渡词，可能影响论证链检测 | **合并处理**，同时分析 |
| R→L | 内部结构相似性检测需要段落功能标注，与段落数量分析共享数据 | **合并处理**，共享段落分析结果 |

#### 关键冲突决策

**冲突1: 章节结构调整 vs 内部结构相似性**
```
场景：检测到所有章节内部结构高度相似（都是3段式）
- 如果先合并/拆分章节 → 相似性检测对象变化
- 如果先检测相似性 → 可以指导如何调整章节

解决：先检测相似性(R)，再决定章节调整(D)
```

**冲突2: 过渡词删除 vs 逻辑关系检测**
```
场景：章节间使用 "Building on the previous analysis..."
- 如果先删过渡词 → 可能丢失论证链信息
- 如果先检测逻辑 → 可以识别哪些过渡词承载实际逻辑

解决：同步检测，综合处理
```

---

## 三、Layer 4 子步骤设计方案
## Layer 4 Sub-Step Design Proposal

### 执行流程图 | Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Layer 4: Section Level Analysis                          │
│                    章节级分析（基于优先级和依赖性排序）                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  从 Layer 5 接收: locked_terms[], modified_text, document_structure         │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 2.0: 章节识别与角色标注 (Section Identification)             │     │
│  │  ├── 自动检测章节边界                                              │     │
│  │  ├── 识别每个章节的功能角色                                        │     │
│  │  └── 生成章节结构图                                                │     │
│  │                                                                     │     │
│  │  检测项：A (章节角色识别)                                          │     │
│  │  优先级：★★★★★ (最高 - 所有后续分析的基础)                        │     │
│  │  检测器：SectionAnalyzer._detect_sections()                        │     │
│  │  输出：sections[], section_boundaries[], section_roles[]            │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 2.1: 章节顺序与结构检测 (Section Order & Structure)          │     │
│  │  ├── 检测章节顺序可预测性 (Intro→Method→Result→Discuss→Conclusion)│     │
│  │  ├── 检测缺失的关键章节                                            │     │
│  │  └── 检测章节功能融合度（单一功能 vs 混合功能）                    │     │
│  │                                                                     │     │
│  │  检测项：B (顺序可预测性) + C (缺失章节) + D (功能融合度)          │     │
│  │  优先级：★★★★☆                                                    │     │
│  │  检测器：SectionAnalyzer._analyze_logic_flow()                     │     │
│  │  输出：orderMatchScore, missingSecti, functionFusionScore          │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 2.2: 章节长度分布检测 (Section Length Distribution)          │     │
│  │  ├── 计算章节长度变异系数(CV)                                      │     │
│  │  ├── 检测极端长度章节（过短/过长）                                 │     │
│  │  ├── 检测关键章节权重（核心章节是否更长）                          │     │
│  │  └── 检测各章节段落数量变异                                        │     │
│  │                                                                     │     │
│  │  检测项：I (长度CV) + J (极端长度) + K (权重) + L (段落数变异)     │     │
│  │  优先级：★★★★☆                                                    │     │
│  │  检测器：SectionAnalyzer._analyze_length_distribution()            │     │
│  │  输出：lengthCV, extremeSections[], keyWeightIssues[]              │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 2.3: 章节内部结构相似性检测 (Internal Structure Similarity)  │     │
│  │  ├── 标注每个段落的功能角色 (topic/evidence/analysis/conclusion)   │     │
│  │  ├── 生成每个章节的"功能序列"向量                                  │     │
│  │  ├── 计算章节间功能序列相似度                                      │     │
│  │  ├── 检测子标题深度变异                                            │     │
│  │  └── 检测章节内论点密度分布                                        │     │
│  │                                                                     │     │
│  │  检测项：R (内部相似性) + M (子标题深度) + N (论点密度)            │     │
│  │  优先级：★★★☆☆                                                    │     │
│  │  检测器：新建 InternalStructureAnalyzer                            │     │
│  │  输出：similarityMatrix, avgSimilarity, headingVariance,           │     │
│  │         argumentDensityCV                                           │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 2.4: 章节衔接与过渡检测 (Section Transition Detection)       │     │
│  │  ├── 检测章节间显性过渡词                                          │     │
│  │  ├── 分类过渡词强度 (Strong/Moderate/Weak)                         │     │
│  │  ├── 检测章节间语义回声（关键词自然重复）                          │     │
│  │  └── 检测章节开头模式多样性                                        │     │
│  │                                                                     │     │
│  │  检测项：E (过渡词) + F (强度) + G (语义回声) + H (开头模式)       │     │
│  │  优先级：★★★☆☆                                                    │     │
│  │  检测器：SectionAnalyzer._analyze_transitions()                    │     │
│  │  输出：transitionWords[], strengthDistribution, semanticEchoScore, │     │
│  │         openerPatterns[]                                            │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Step 2.5: 章节间逻辑关系检测 (Inter-Section Logic Detection)      │     │
│  │  ├── 检测论证链完整性（因果逻辑链是否过于完美）                    │     │
│  │  ├── 检测章节间信息重复（过度总结/预告）                           │     │
│  │  └── 检测递进关系模式（是否过于规整）                              │     │
│  │                                                                     │     │
│  │  检测项：O (论证链) + P (信息重复) + Q (递进模式)                  │     │
│  │  优先级：★★☆☆☆                                                    │     │
│  │  检测器：新建 InterSectionLogicAnalyzer                            │     │
│  │  输出：argumentChainScore, redundancyIssues[], progressionPattern  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↓                                         │
│                     传递修改后的文本到 Layer 3 (Paragraph)                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、各子步骤详细设计
## Detailed Design for Each Sub-Step

### Step 2.0: 章节识别与角色标注 (Section Identification)

**目的**：自动检测章节边界，识别每个章节的功能角色

**Purpose**: Automatically detect section boundaries and identify the functional role of each section

**检测方法**：
| 方法 | 说明 |
|------|------|
| 标题检测 | 识别 H1-H6 标题、数字编号、加粗文本等 |
| 关键词匹配 | 识别 "Introduction", "Methodology", "Results" 等 |
| 段落聚类 | 根据主题相似性将段落聚类为章节 |
| LLM辅助 | 对模糊边界进行LLM判断 |

**章节角色定义**：
| 角色 | 英文 | 典型关键词 |
|------|------|-----------|
| 引言 | introduction | introduction, background, overview |
| 文献综述 | literature_review | literature, review, previous work |
| 方法论 | methodology | method, approach, procedure |
| 结果 | results | results, findings, outcomes |
| 讨论 | discussion | discussion, implications, analysis |
| 结论 | conclusion | conclusion, summary, future work |
| 正文 | body | (无明确角色时) |

**用户界面设计**：
```
┌─────────────────────────────────────────────────────────────────┐
│ Step 2.0: 章节识别 Section Identification                        │
├─────────────────────────────────────────────────────────────────┤
│ 检测到的章节结构 Detected Section Structure:                     │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Section 1: Introduction (引言)                    [编辑角色]││
│ │ ├── 段落 1-3 (共 245 词)                                    ││
│ │ └── 置信度: 95%                                             ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ Section 2: Literature Review (文献综述)           [编辑角色]││
│ │ ├── 段落 4-8 (共 512 词)                                    ││
│ │ └── 置信度: 88%                                             ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ Section 3: Methodology (方法论)                   [编辑角色]││
│ │ ├── 段落 9-14 (共 623 词)                                   ││
│ │ └── 置信度: 92%                                             ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ Section 4: Results (结果)                         [编辑角色]││
│ │ ├── 段落 15-20 (共 578 词)                                  ││
│ │ └── 置信度: 90%                                             ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ Section 5: Conclusion (结论)                      [编辑角色]││
│ │ ├── 段落 21-23 (共 198 词)                                  ││
│ │ └── 置信度: 94%                                             ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 总计: 5个章节, 23个段落, 2156词                                 │
│                                                                 │
│ [调整章节边界] [确认并继续 →]                                   │
└─────────────────────────────────────────────────────────────────┘
```

**输出数据结构**：
```python
Step2_0_Result:
  - sections: List[Section]
    - index: int
    - role: str  # introduction, methodology, etc.
    - start_paragraph: int
    - end_paragraph: int
    - word_count: int
    - confidence: float
  - section_boundaries: List[int]  # [0, 3, 8, 14, 20, 23]
  - total_sections: int
  - total_paragraphs: int
```

---

### Step 2.1: 章节顺序与结构检测 (Section Order & Structure)

**目的**：检测章节顺序是否过于可预测，以及章节功能是否过于单一

**检测项**：

#### B: 章节顺序可预测性
| 指标 | 阈值 | 风险等级 |
|------|------|----------|
| 顺序匹配度 | ≥ 80% | 高风险 |
| 顺序匹配度 | 60-80% | 中风险 |
| 顺序匹配度 | < 60% | 低风险（正常） |

**期望顺序（AI模板）**：
```
Introduction → Literature Review → Methodology → Results → Discussion → Conclusion
```

#### C: 缺失章节检测
| 缺失章节 | 说明 |
|---------|------|
| introduction | 缺少引言可能是人类写作特征（直接切入主题） |
| methodology | 理论类文章可能无方法论章节 |
| conclusion | 开放式结尾可能故意不写结论 |

#### D: 章节功能融合度
| 指标 | 说明 | AI特征 |
|------|------|--------|
| 功能单一度 | 每个章节只做一件事 | 高 = AI |
| 功能混合度 | 章节包含多种功能元素 | 高 = 人类 |

**AI典型模式**：
```
Section 1: 纯引言（只有背景介绍）
Section 2: 纯方法（只有实验设计）
Section 3: 纯结果（只有数据展示）
```

**人类写作模式**：
```
Section 1: 引言 + 部分文献回顾
Section 2: 方法 + 初步结果预览
Section 3: 结果 + 穿插讨论
```

**用户界面设计**：
```
┌─────────────────────────────────────────────────────────────────┐
│ Step 2.1: 章节顺序与结构 Section Order & Structure               │
├─────────────────────────────────────────────────────────────────┤
│ 章节顺序分析 Section Order Analysis:                             │
│                                                                 │
│ 当前顺序: Intro → Lit Review → Method → Results → Conclusion    │
│ 期望模板: Intro → Lit Review → Method → Results → Discuss → Conc│
│                                                                 │
│ ⚠️ 顺序匹配度: 83% [高风险]                                     │
│    您的章节顺序高度匹配学术论文模板，这是AI写作的典型特征。       │
│                                                                 │
│ 建议：                                                          │
│ • 考虑将讨论与结果融合                                          │
│ • 尝试"结果先行"结构：先展示关键发现，再解释方法                │
│ • 在方法论中穿插初步结果                                        │
│                                                                 │
│ [AI生成重组建议] [查看详情]                                     │
├─────────────────────────────────────────────────────────────────┤
│ 缺失章节分析 Missing Sections:                                   │
│                                                                 │
│ ℹ️ 缺少独立的 Discussion 章节                                   │
│    这可能是有意为之（讨论融入结果），也可能需要补充。            │
│                                                                 │
│ [忽略] [添加讨论章节建议]                                       │
├─────────────────────────────────────────────────────────────────┤
│ 章节功能融合度 Function Fusion Analysis:                         │
│                                                                 │
│ ⚠️ 功能单一度: 92% [高风险]                                     │
│    每个章节功能过于单一，缺乏功能混合。                          │
│                                                                 │
│ 章节功能分析:                                                   │
│ • Section 1 (Intro): 100% 背景介绍                              │
│ • Section 2 (Method): 100% 方法描述                             │
│ • Section 3 (Results): 95% 数据展示, 5% 简单讨论                │
│ • Section 4 (Conclusion): 100% 总结                             │
│                                                                 │
│ 建议：在 Section 3 中增加更多讨论和分析内容                      │
│                                                                 │
│ [AI生成功能融合建议] [下一步 →]                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Step 2.2: 章节长度分布检测 (Section Length Distribution)

**目的**：检测章节长度是否过于均匀，以及关键章节是否有适当的权重

**检测项**：

#### I: 章节长度变异系数 (CV)
| CV值 | 风险等级 | 说明 |
|------|----------|------|
| < 0.2 | 高风险 | 过于均匀，AI特征明显 |
| 0.2-0.3 | 中风险 | 稍显均匀 |
| 0.3-0.5 | 低风险 | 正常变化 |
| > 0.5 | 正常 | 人类写作特征 |

#### J: 极端长度检测
| 类型 | 阈值 | 说明 |
|------|------|------|
| 过短章节 | < 100词 且 < 30%均值 | 可能需要扩展 |
| 过长章节 | > 3倍均值 | 可能需要拆分 |

#### K: 关键章节权重
| 章节类型 | 期望权重 | 说明 |
|---------|---------|------|
| 核心章节 (Results, Discussion) | 1.5-2.5倍均值 | 应该更详细 |
| 背景章节 (Introduction) | 0.5-1.0倍均值 | 可以简洁 |
| 方法章节 (Methodology) | 1.0-2.0倍均值 | 根据复杂度 |

#### L: 段落数量变异
| CV值 | 风险等级 | 说明 |
|------|----------|------|
| < 0.3 | 高风险 | 每个章节段落数过于一致 |
| ≥ 0.3 | 正常 | 段落数有自然变化 |

**用户界面设计**：
```
┌─────────────────────────────────────────────────────────────────┐
│ Step 2.2: 章节长度分布 Section Length Distribution               │
├─────────────────────────────────────────────────────────────────┤
│ 长度分布概览 Length Distribution Overview:                       │
│                                                                 │
│ 章节长度CV: 0.18 [高风险 - 过于均匀]                            │
│ 目标CV: ≥ 0.40                                                  │
│                                                                 │
│ 章节长度可视化:                                                 │
│ Introduction:  ████████████░░░░░░░░░░░░░░ 245词 (0.95x均值)    │
│ Lit Review:    ██████████████████████░░░░ 512词 (1.98x均值)    │
│ Methodology:   ████████████████████████░░ 623词 (2.41x均值)    │
│ Results:       ██████████████████████░░░░ 578词 (2.24x均值)    │
│ Conclusion:    ████████░░░░░░░░░░░░░░░░░░ 198词 (0.77x均值)    │
│                                                                 │
│ 平均长度: 431词 | 标准差: 78词                                  │
├─────────────────────────────────────────────────────────────────┤
│ 极端长度检测 Extreme Length Detection:                           │
│                                                                 │
│ ✅ 未检测到过短章节                                             │
│ ✅ 未检测到过长章节                                             │
├─────────────────────────────────────────────────────────────────┤
│ 关键章节权重 Key Section Weight:                                 │
│                                                                 │
│ ⚠️ Results章节权重偏低 (2.24x vs 建议2.5-3.0x)                  │
│    核心结果章节应该包含更多细节和分析                           │
│                                                                 │
│ ℹ️ Conclusion章节权重正常 (0.77x)                               │
├─────────────────────────────────────────────────────────────────┤
│ 段落数量变异 Paragraph Count Variance:                           │
│                                                                 │
│ 段落数CV: 0.12 [高风险 - 过于均匀]                              │
│                                                                 │
│ 章节段落数:                                                     │
│ • Introduction: 3段                                             │
│ • Lit Review: 4段                                               │
│ • Methodology: 5段                                              │
│ • Results: 5段                                                  │
│ • Conclusion: 3段                                               │
│                                                                 │
│ 建议：增加Results章节的段落数，减少Methodology的段落数          │
│                                                                 │
│ [AI生成长度调整策略] [下一步 →]                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Step 2.3: 章节内部结构相似性检测 (Internal Structure Similarity) ⭐ 新增

**目的**：检测不同章节的内部逻辑结构是否高度相似（AI模板化特征）

**Purpose**: Detect if different sections share highly similar internal logical structures (AI template pattern)

**检测方法**：

#### R: 章节内部逻辑结构相似性

**Step 1: 段落功能标注**
| 功能角色 | 英文 | 说明 |
|---------|------|------|
| 主题句 | topic_sentence | 段落开头的主题陈述 |
| 证据/数据 | evidence | 支撑性证据、数据、引用 |
| 分析/解释 | analysis | 对证据的分析和解释 |
| 过渡 | transition | 承上启下的过渡段落 |
| 小结 | mini_conclusion | 段落或小节的总结 |
| 举例 | example | 具体案例或实例 |

**Step 2: 生成功能序列向量**
```
Section 1: [topic, evidence, evidence, analysis, mini_conclusion]
Section 2: [topic, evidence, evidence, analysis, mini_conclusion]
Section 3: [topic, evidence, evidence, analysis, mini_conclusion]
→ 相似度: 100% [高风险]
```

**Step 3: 计算相似度**
- 使用编辑距离或序列对齐算法
- 计算所有章节对的平均相似度

**风险等级**：
| 平均相似度 | 风险等级 | 说明 |
|-----------|----------|------|
| > 90% | 高风险 | 几乎相同的内部结构 |
| 80-90% | 中风险 | 高度相似 |
| 60-80% | 低风险 | 部分相似（正常） |
| < 60% | 正常 | 各章节结构独特 |

#### M: 子标题深度变异

| 指标 | 风险判定 |
|------|----------|
| 所有章节子标题层级相同 | 高风险 |
| 子标题深度有变化 | 正常 |

#### N: 章节内论点密度

| 指标 | 风险判定 |
|------|----------|
| 各章节论点数量均匀 | 中风险 |
| 论点分布有自然变化 | 正常 |

**用户界面设计**：
```
┌─────────────────────────────────────────────────────────────────┐
│ Step 2.3: 章节内部结构相似性 Internal Structure Similarity       │
├─────────────────────────────────────────────────────────────────┤
│ 内部逻辑结构分析 Internal Logic Structure Analysis:              │
│                                                                 │
│ ⚠️ 平均结构相似度: 87% [高风险]                                 │
│    不同章节的内部逻辑结构高度相似，这是AI使用模板的典型特征。    │
│                                                                 │
│ 章节内部结构对比:                                               │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Section 2 (Lit Review):                                     ││
│ │ [Topic] → [Evidence] → [Evidence] → [Analysis] → [Summary]  ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ Section 3 (Methodology):                                    ││
│ │ [Topic] → [Evidence] → [Evidence] → [Analysis] → [Summary]  ││
│ │                                         ↑ 相似度: 92%       ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ Section 4 (Results):                                        ││
│ │ [Topic] → [Evidence] → [Evidence] → [Analysis] → [Summary]  ││
│ │                                         ↑ 相似度: 89%       ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 相似性矩阵 Similarity Matrix:                                   │
│            Sec1   Sec2   Sec3   Sec4   Sec5                    │
│ Section 1   -     78%    75%    72%    85%                     │
│ Section 2        -      92%    89%    80%                      │
│ Section 3               -      91%    77%                      │
│ Section 4                      -      82%                      │
│ Section 5                             -                        │
│                                                                 │
│ 建议：                                                          │
│ • Section 3 可以采用"步骤列表"结构而非段落式                    │
│ • Section 4 可以采用"数据表格+分散讨论"结构                     │
│ • 尝试在某些章节使用"问答式"或"对比式"结构                     │
│                                                                 │
│ [AI生成结构差异化建议] [查看详细分析]                           │
├─────────────────────────────────────────────────────────────────┤
│ 子标题深度分析 Heading Depth Analysis:                           │
│                                                                 │
│ ⚠️ 子标题深度一致性: 100% [中风险]                              │
│    所有章节都使用相同的子标题层级（2级）                        │
│                                                                 │
│ • Section 2: H2 → H3 (2级)                                     │
│ • Section 3: H2 → H3 (2级)                                     │
│ • Section 4: H2 → H3 (2级)                                     │
│                                                                 │
│ 建议：在 Section 3 中增加 H4 级别的详细步骤                     │
├─────────────────────────────────────────────────────────────────┤
│ 论点密度分析 Argument Density Analysis:                          │
│                                                                 │
│ 论点密度CV: 0.15 [中风险]                                       │
│                                                                 │
│ • Section 2: 4个论点 (0.8个/100词)                             │
│ • Section 3: 5个论点 (0.8个/100词)                             │
│ • Section 4: 5个论点 (0.9个/100词)                             │
│                                                                 │
│ [AI生成差异化策略] [下一步 →]                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

### Step 2.4: 章节衔接与过渡检测 (Section Transition Detection)

**目的**：检测章节间的过渡是否过于显性和机械

**检测项**：

#### E: 显性过渡词检测

**过渡词分类**：
| 强度 | 过渡词示例 |
|------|-----------|
| Strong | "Having established...", "Building on...", "Given the..." |
| Moderate | "Now...", "Next...", "Turning to...", "Moving to..." |
| Weak | "However...", "Moreover...", "Furthermore..." |

#### F: 过渡词强度分布

| 分布 | 风险判定 |
|------|----------|
| Strong > 50% | 高风险（过于生硬） |
| Moderate > 60% | 中风险 |
| Weak主导 或 无显性过渡 | 正常 |

#### G: 章节间语义回声

| 指标 | 说明 |
|------|------|
| 语义回声分数 | 前一章节关键词在下一章节开头自然出现的比例 |
| 目标 | ≥ 0.4 (有明显的词汇回声) |

#### H: 章节开头模式多样性

| 指标 | 风险判定 |
|------|----------|
| 开头模式重复率 > 60% | 高风险 |
| 开头模式多样 | 正常 |

**用户界面设计**：
```
┌─────────────────────────────────────────────────────────────────┐
│ Step 2.4: 章节衔接与过渡 Section Transition Detection            │
├─────────────────────────────────────────────────────────────────┤
│ 章节过渡词检测 Section Transition Words:                         │
│                                                                 │
│ 显性过渡比例: 75% [高风险]                                      │
│ 4/5 个章节衔接点使用了显性过渡词                                │
│                                                                 │
│ 检测到的过渡词:                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Intro → Lit Review:                                         ││
│ │ "Building on this foundation, the following section..."     ││
│ │ 强度: Strong ⚠️                                             ││
│ │ [删除过渡词] [用语义回声替换]                                ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ Lit Review → Methodology:                                   ││
│ │ "Having reviewed the existing literature, we now turn to..."││
│ │ 强度: Strong ⚠️                                             ││
│ │ [删除过渡词] [用语义回声替换]                                ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ Methodology → Results:                                      ││
│ │ "Following the methodology outlined above..."               ││
│ │ 强度: Moderate ⚠️                                           ││
│ │ [删除过渡词] [用语义回声替换]                                ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ Results → Conclusion:                                       ││
│ │ (无显性过渡词) ✅                                           ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ 过渡词强度分布 Transition Strength Distribution:                 │
│                                                                 │
│ Strong:   ████████████████░░░░ 50% ⚠️                          │
│ Moderate: ████████░░░░░░░░░░░░ 25%                              │
│ Weak:     ░░░░░░░░░░░░░░░░░░░░ 0%                               │
│ None:     ████████░░░░░░░░░░░░ 25%                              │
│                                                                 │
│ 建议：将Strong过渡词替换为隐性过渡（语义回声）                   │
├─────────────────────────────────────────────────────────────────┤
│ 语义回声分析 Semantic Echo Analysis:                             │
│                                                                 │
│ 语义回声分数: 0.18 [偏低]                                       │
│ 目标: ≥ 0.40                                                    │
│                                                                 │
│ 改进示例:                                                       │
│ 原文: "Building on this foundation, the literature review..."   │
│ 改进: "Previous studies on neural network optimization..."      │
│       (回声前一章节的关键词 "neural network")                   │
│                                                                 │
│ [AI生成语义回声替换方案] [批量处理]                             │
├─────────────────────────────────────────────────────────────────┤
│ 章节开头模式 Section Opener Patterns:                            │
│                                                                 │
│ 开头模式重复率: 40% [正常]                                      │
│                                                                 │
│ 检测到的模式:                                                   │
│ • "This section..." (2次)                                      │
│ • 其他模式 (3次)                                                │
│                                                                 │
│ [下一步 →]                                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

### Step 2.5: 章节间逻辑关系检测 (Inter-Section Logic Detection)

**目的**：检测章节间的逻辑关系是否过于完美和机械

**检测项**：

#### O: 论证链完整性

| 指标 | 风险判定 |
|------|----------|
| 因果链完美闭合 | 高风险（AI特征） |
| 有逻辑跳跃或开放点 | 正常（人类特征） |

#### P: 章节间信息重复

| 类型 | 风险判定 |
|------|----------|
| 过度预告 | 高风险（章节开头重复说明要做什么） |
| 过度回顾 | 高风险（章节结尾过度总结） |
| 适度呼应 | 正常 |

#### Q: 递进关系检测

| 模式 | 风险判定 |
|------|----------|
| 完美线性递进 | 高风险（A→B→C→D 无分支） |
| 有分支和回溯 | 正常 |

**用户界面设计**：
```
┌─────────────────────────────────────────────────────────────────┐
│ Step 2.5: 章节间逻辑关系 Inter-Section Logic Detection           │
├─────────────────────────────────────────────────────────────────┤
│ 论证链完整性 Argument Chain Completeness:                        │
│                                                                 │
│ ⚠️ 论证链完美度: 95% [高风险]                                   │
│    章节间的因果逻辑过于完美闭合，缺少开放性问题。                │
│                                                                 │
│ 论证链结构:                                                     │
│ Introduction: 提出问题 A                                        │
│      ↓ (完美衔接)                                               │
│ Lit Review: 指出现有方法的不足 B                                │
│      ↓ (完美衔接)                                               │
│ Methodology: 提出解决方案 C 来解决 B                            │
│      ↓ (完美衔接)                                               │
│ Results: 证明 C 有效解决了 A                                    │
│      ↓ (完美衔接)                                               │
│ Conclusion: 总结 A→B→C 的完美闭环                              │
│                                                                 │
│ 建议：                                                          │
│ • 在 Results 中承认一些局限性                                   │
│ • 在 Conclusion 中提出新的未解决问题                            │
│ • 增加一些"意外发现"或"附带观察"                               │
│                                                                 │
│ [AI生成开放性建议]                                              │
├─────────────────────────────────────────────────────────────────┤
│ 章节间信息重复 Inter-Section Redundancy:                         │
│                                                                 │
│ ⚠️ 检测到过度预告/回顾模式:                                     │
│                                                                 │
│ • Lit Review 结尾:                                              │
│   "The next section will describe the methodology..." ⚠️        │
│   → 过度预告，建议删除                                          │
│                                                                 │
│ • Methodology 开头:                                             │
│   "As discussed in the previous section..." ⚠️                  │
│   → 过度回顾，建议简化                                          │
│                                                                 │
│ • Results 结尾:                                                 │
│   "In summary, this section has demonstrated..." ⚠️             │
│   → 过度总结，建议删除                                          │
│                                                                 │
│ [批量删除冗余] [逐个处理]                                       │
├─────────────────────────────────────────────────────────────────┤
│ 递进关系模式 Progression Pattern:                                │
│                                                                 │
│ ⚠️ 递进模式: 完美线性 [高风险]                                  │
│                                                                 │
│ 当前结构: A → B → C → D → E (无分支)                           │
│                                                                 │
│ 建议结构:                                                       │
│ A → B ─┬→ C₁ ──────→ D                                         │
│        └→ C₂ (附带发现)                                         │
│                                                                 │
│ 改进方法：                                                      │
│ • 在某个章节中引入"旁支"讨论                                    │
│ • 添加"意外发现"或"初步探索"小节                               │
│ • 允许某些论点的"悬而未决"                                      │
│                                                                 │
│ [AI生成非线性结构建议] [完成Layer 4 →]                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 五、技术实现要点
## Technical Implementation Notes

### 5.1 API端点设计 | API Endpoint Design

```python
# Layer 4 Sub-step Endpoints
# Base URL: /api/v1/layer4/

# Step 2.0: Section Identification
POST /step2-0/identify          # 识别章节边界和角色
POST /step2-0/adjust            # 用户调整章节边界
GET  /step2-0/result/{session}  # 获取识别结果

# Step 2.1: Section Order & Structure
POST /step2-1/analyze           # 分析章节顺序和结构
POST /step2-1/ai-suggest        # AI生成重组建议
POST /step2-1/apply             # 应用修改

# Step 2.2: Section Length Distribution
POST /step2-2/analyze           # 分析长度分布
POST /step2-2/ai-suggest        # AI生成长度调整策略
POST /step2-2/apply             # 应用修改

# Step 2.3: Internal Structure Similarity (NEW)
POST /step2-3/analyze           # 分析内部结构相似性
POST /step2-3/ai-suggest        # AI生成差异化建议
POST /step2-3/apply             # 应用修改

# Step 2.4: Section Transition
POST /step2-4/analyze           # 分析章节衔接
POST /step2-4/ai-suggest        # AI生成语义回声替换
POST /step2-4/apply             # 应用修改

# Step 2.5: Inter-Section Logic
POST /step2-5/analyze           # 分析章节间逻辑
POST /step2-5/ai-suggest        # AI生成非线性结构建议
POST /step2-5/apply             # 应用修改
```

### 5.2 检测器集成 | Detector Integration

```python
# Step 2.0: Section Identification
detectors = [
    SectionAnalyzer._detect_sections(),      # 现有
    LLM_SectionRoleClassifier(),             # 新建：LLM辅助角色识别
]

# Step 2.1: Section Order & Structure
detectors = [
    SectionAnalyzer._analyze_logic_flow(),   # 现有
    SectionFunctionAnalyzer(),               # 新建：功能融合度分析
]

# Step 2.2: Section Length Distribution
detectors = [
    SectionAnalyzer._analyze_length_distribution(),  # 现有
    SectionWeightAnalyzer(),                         # 新建：关键章节权重
]

# Step 2.3: Internal Structure Similarity (NEW)
detectors = [
    InternalStructureAnalyzer(),             # 新建：内部结构相似性
    ParagraphFunctionLabeler(),              # 新建：段落功能标注
    HeadingDepthAnalyzer(),                  # 新建：子标题深度
    ArgumentDensityAnalyzer(),               # 新建：论点密度
]

# Step 2.4: Section Transition
detectors = [
    SectionAnalyzer._analyze_transitions(),  # 现有
    SemanticEchoAnalyzer(),                  # 新建：语义回声检测
    OpenerPatternAnalyzer(),                 # 新建：开头模式分析
]

# Step 2.5: Inter-Section Logic
detectors = [
    ArgumentChainAnalyzer(),                 # 新建：论证链分析
    RedundancyDetector(),                    # 新建：冗余检测
    ProgressionPatternAnalyzer(),            # 新建：递进模式分析
]
```

### 5.3 数据流设计 | Data Flow Design

```
┌──────────────────────────────────────────────────────────────────┐
│                         数据流 Data Flow                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  从 Layer 5 接收:                                                 │
│  {                                                                │
│    "locked_terms": [...],                                         │
│    "modified_text": "...",                                        │
│    "document_structure": {...}                                    │
│  }                                                                │
│       ↓                                                          │
│  Step 2.0 → sections[], boundaries[] → Session存储               │
│       ↓                                                          │
│  Step 2.1 (基于sections) → 修改后文本A → Session存储             │
│       ↓                                                          │
│  Step 2.2 (基于文本A) → 修改后文本B → Session存储                │
│       ↓                                                          │
│  Step 2.3 (基于文本B) → 修改后文本C → Session存储                │
│       ↓                                                          │
│  Step 2.4 (基于文本C) → 修改后文本D → Session存储                │
│       ↓                                                          │
│  Step 2.5 (基于文本D) → 最终文本 → 传递给 Layer 3                │
│       ↓                                                          │
│  传递给 Layer 3:                                                  │
│  {                                                                │
│    "locked_terms": [...],                                         │
│    "modified_text": "...",                                        │
│    "sections": [...],                                             │
│    "section_boundaries": [...],                                   │
│    "paragraph_functions": [...]  # 段落功能标注，供Layer 3使用    │
│  }                                                                │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 六、每个Substep的LLM介入点
## LLM Intervention Points for Each Substep

每个substep都包含以下LLM介入功能：

### 通用LLM介入流程 | Common LLM Intervention Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    每个Substep的LLM介入流程                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 规则检测 Rule Detection                                     │
│     └── 快速识别问题，生成问题列表                              │
│                                                                 │
│  2. LLM总体分析 LLM Overall Analysis                            │
│     └── 对本步骤所有问题进行综合分析                            │
│     └── Prompt: "分析以下章节结构问题的整体严重程度和关联性"    │
│                                                                 │
│  3. 用户点击单个问题 → LLM单独分析                              │
│     └── 深入分析该问题的具体原因和影响                          │
│     └── Prompt: "详细分析{problem_type}问题，解释其AI特征"      │
│                                                                 │
│  4. LLM生成改进Prompt                                           │
│     └── 为用户生成可直接使用的改写提示词                        │
│     └── Prompt: "生成改进建议和可执行的改写提示词"              │
│                                                                 │
│  5. LLM执行修改（可选）                                         │
│     └── 用户确认后，LLM直接执行文本修改                         │
│     └── Prompt: "按照以下策略修改文本: {strategy}"              │
│                                                                 │
│  6. 验证锁定词汇                                                │
│     └── 确保修改后的文本保留了所有locked_terms                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 各Substep的LLM Prompt示例

#### Step 2.0 LLM Prompt
```
You are analyzing a document to identify section boundaries and roles.
For each detected section, determine if it functions as:
- introduction, literature_review, methodology, results, discussion, conclusion, or body

Also assess the confidence level of your classification.
```

#### Step 2.1 LLM Prompt
```
Analyze the section structure for AI-like patterns:
1. Is the section order too predictable (follows strict academic template)?
2. Are sections functionally too isolated (each does only one thing)?

Provide specific suggestions for:
- Reordering sections for more natural flow
- Fusing related content across sections
```

#### Step 2.3 LLM Prompt (NEW - Internal Structure Similarity)
```
Compare the internal logical structure of each section:
1. Label each paragraph's function: topic_sentence, evidence, analysis, transition, mini_conclusion
2. Generate a "function sequence" for each section
3. Calculate similarity between sections
4. Suggest ways to differentiate section structures

Example output:
Section 2: [topic → evidence → evidence → analysis → summary]
Section 3: [topic → evidence → evidence → analysis → summary]
Similarity: 92% - HIGH RISK

Suggestion: Transform Section 3 into a step-by-step procedural format instead of the essay format used in Section 2.
```

#### Step 2.5 LLM Prompt
```
Analyze inter-section logical relationships:
1. Is the argument chain too perfect and closed?
2. Are there excessive previews/summaries between sections?
3. Is the progression too linear without branches?

Provide suggestions for:
- Adding open-ended questions or unresolved tensions
- Removing redundant previews/summaries
- Creating non-linear narrative branches
```

---

## 七、总结
## Summary

Layer 4 子步骤系统包含 **6个有序的子步骤**：

| 步骤 | 名称 | 检测项 | 优先级 |
|------|------|--------|--------|
| **2.0** | 章节识别与角色标注 | A | ★★★★★ |
| **2.1** | 章节顺序与结构检测 | B + C + D | ★★★★☆ |
| **2.2** | 章节长度分布检测 | I + J + K + L | ★★★★☆ |
| **2.3** | 章节内部结构相似性检测 ⭐ | R + M + N | ★★★☆☆ |
| **2.4** | 章节衔接与过渡检测 | E + F + G + H | ★★★☆☆ |
| **2.5** | 章节间逻辑关系检测 | O + P + Q | ★★☆☆☆ |

**新增核心功能 (R)**：
- 章节内部逻辑结构相似性检测
- 通过段落功能标注和序列对比，识别AI模板化写作特征
- 相似度 > 80% 触发高风险警告

**每个子步骤的LLM介入**：
1. 总体分析 - 综合评估本步骤所有问题
2. 单独分析 - 用户点击触发的深度分析
3. 生成改进Prompt - 可直接使用的改写提示词
4. 执行修改 - LLM直接修改文本（用户确认后）

**数据流**：
- 从 Layer 5 接收 locked_terms 和 modified_text
- 每个步骤修改后传递给下一步
- 最终传递给 Layer 3，包含 paragraph_functions 标注
