# 旧版模型在新5层架构中的集成状况分析
# Legacy Model Integration Status in New 5-Layer Architecture

> 分析日期 Analysis Date: 2026-01-08
> 版本 Version: v1.0

---

## 一、问题概述 | Issue Overview

用户询问:**旧版本有两个模型(PPL检测和无实际意义单词检测),现在是否已经接入到新的5层架构系统里面?**

**答案: ❌ 没有接入！**

这两个重要的检测模型目前**仅在旧版DEPRECATED API中使用**,**没有集成到新版5层架构的30个substeps**中。

---

## 二、两个模型的详细情况 | Model Details

### 2.1 模型1: PPL Calculator (困惑度计算器)

**文件位置:** `src/core/analyzer/ppl_calculator.py`

**功能:**
- 使用 ONNX Runtime 计算真实的 token-level 困惑度 (Perplexity)
- 基于 distilgpt2 语言模型
- 替代了旧版的 zlib 压缩比代理方法

**原理:**
```
困惑度(Perplexity)衡量语言模型对文本的"惊讶程度":
- 低PPL (< 20) = 文本可预测 = AI特征
- 高PPL (> 40) = 文本出人意料 = 人类特征
```

**实现亮点:**
- 真实的统计语言模型(非简单启发式规则)
- 支持 GPU 加速 (CUDAExecutionProvider)
- 懒加载机制(首次调用才加载模型)
- 自动回退到 zlib 方法(如果 ONNX 不可用)

**当前使用状况:**
```
src/core/analyzer/ppl_calculator.py (模型定义)
    ↓ 被引用
src/core/analyzer/scorer.py (RiskScorer类的_calculate_ppl方法)
    ↓ 被引用
❌ 新版5层架构substeps: 无引用
✅ 旧版DEPRECATED API: 有使用
```

---

### 2.2 模型2: Syntactic Void Detector (句法空洞检测器)

**文件位置:** `src/core/analyzer/syntactic_void.py`

**功能:**
- 检测"无实际意义的单词"或"华丽但空洞"的AI句式
- 识别7种典型的AI空洞模式

**检测的7种空洞模式:**

| 模式类型 | 示例 | 严重程度 |
|---------|------|---------|
| ABSTRACT_VERB_NOUN | "underscores the significance of" | High |
| TESTAMENT_PHRASE | "serves as a testament to" | High |
| PIVOTAL_ROLE | "plays a pivotal role in" | High |
| LANDSCAPE_PHRASE | "in the comprehensive landscape of" | High |
| EMPTY_FILLER | "it is important to note that" | Medium |
| CHARACTERIZED_BY | "is characterized by" | Medium |
| OFFERS_PATHWAY | "offers a novel pathway/approach" | Medium |

**检测方法:**
1. **快速路径**: 正则表达式匹配(10+种预定义模式)
2. **精确路径**: spaCy依存句法分析(检测抽象动词+抽象名词组合)

**抽象动词词库 (11个):**
```
underscore, highlight, exemplify, demonstrate, illustrate,
showcase, emphasize, signify, epitomize, encapsulate, embody
```

**抽象名词词库 (30+个):**
```
significance, importance, relevance, nuance, complexity,
landscape, tapestry, framework, paradigm, dynamic,
trajectory, evolution, transformation, dimension, facet, ...
```

**当前使用状况:**
```
src/core/analyzer/syntactic_void.py (模型定义)
    ↓ 被引用
src/core/analyzer/layers/sentence_orchestrator.py (SentenceOrchestrator类)
    ↓ 被引用
❌ 新版5层架构substeps: 无引用
✅ 旧版DEPRECATED API: 有使用
```

---

## 三、新旧架构对比 | Architecture Comparison

### 3.1 旧版架构 (DEPRECATED)

```
旧版 API 路由:
├── /api/v1/analyze (analyze.py)
├── /api/v1/structure (structure.py)
├── /api/v1/transition (transition.py)
└── /api/v1/paragraph (paragraph.py)

使用的核心模块:
├── scorer.py → 使用 PPL Calculator
└── sentence_orchestrator.py → 使用 Syntactic Void Detector
```

### 3.2 新版5层架构

```
新版 API 路由:
/api/v1/analysis/substeps/
├── layer5/ (Step 1.0 - 1.5)  ← 文档层
├── layer4/ (Step 2.0 - 2.5)  ← 章节层
├── layer3/ (Step 3.0 - 3.5)  ← 段落层
├── layer2/ (Step 4.0 - 4.5)  ← 句子层
└── layer1/ (Step 5.0 - 5.5)  ← 词汇层

❌ 均未引用:
   - scorer.py
   - ppl_calculator.py
   - syntactic_void.py
   - sentence_orchestrator.py
```

---

## 四、影响分析 | Impact Analysis

### 4.1 功能缺失

| 功能 | 旧版 | 新版5层架构 | 影响 |
|------|------|------------|------|
| **真实PPL计算** | ✅ 有 | ❌ 无 | 无法准确评估文本的统计可预测性 |
| **句法空洞检测** | ✅ 有 | ❌ 无 | 无法识别AI特有的"华丽但空洞"句式 |
| **风险评分** | ✅ 有(scorer.py) | ⚠️ 部分实现 | 新版可能使用简化的评分逻辑 |

### 4.2 技术债务

**问题:**
- 投入资源开发的两个重要模型没有被利用
- 新版5层架构可能使用更简单的检测逻辑,准确性可能不如旧版
- 代码冗余:两套系统并存但功能不一致

### 4.3 用户体验影响

**首页宣传 vs 实际实现的差距:**

首页上我们宣传:
> "CAASS v2.0评分系统,综合困惑度、指纹词、突发性等多维度指标"

但实际情况:
- ❌ 新版5层架构**没有使用真实的PPL计算**
- ❌ 新版5层架构**没有使用句法空洞检测**
- ⚠️ 可能导致检测准确性下降

---

## 五、建议的解决方案 | Recommended Solutions

### 方案A: 快速集成 (推荐)

**目标:** 将两个模型集成到新版5层架构中

**实施步骤:**

#### Step 1: 集成 PPL Calculator 到 Layer 1 (词汇层)

```python
# 在 src/api/routes/substeps/layer1/step5_1.py (AIGC指纹检测)

from src.core.analyzer.ppl_calculator import calculate_onnx_ppl

async def analyze_fingerprints(document_id: str):
    # 现有的指纹词检测逻辑
    ...

    # 新增: 计算段落PPL
    for para in paragraphs:
        ppl_score, used_onnx = calculate_onnx_ppl(para.text)
        if used_onnx and ppl_score:
            para.ppl = ppl_score
            para.ppl_risk = "high" if ppl_score < 20 else "medium" if ppl_score < 40 else "low"

    return result
```

#### Step 2: 集成 Syntactic Void Detector 到 Layer 2 (句子层)

```python
# 在 src/api/routes/substeps/layer2/step4_1.py (句式结构分析)

from src.core.analyzer.syntactic_void import detect_syntactic_voids

async def analyze_sentence_patterns(document_id: str):
    # 现有的句式分析逻辑
    ...

    # 新增: 检测句法空洞
    for sent in sentences:
        void_result = detect_syntactic_voids(sent.text)
        if void_result.void_score > 30:
            sent.void_matches = void_result.matches
            sent.has_syntactic_void = True
            # 添加修改建议
            for match in void_result.matches:
                suggestions.append({
                    "type": "syntactic_void",
                    "pattern": match.pattern_type.value,
                    "matched_text": match.matched_text,
                    "suggestion": match.suggestion,
                    "suggestion_zh": match.suggestion_zh
                })

    return result
```

#### Step 3: 更新前端展示

```typescript
// frontend/src/pages/layers/LayerStep1_1.tsx

interface FingerprintResult {
  fingerprints: Array<...>;
  ppl: number;  // 新增
  ppl_risk: string;  // 新增
}

// 在UI中显示PPL信息
{result.ppl && (
  <div className="ppl-indicator">
    <span>Perplexity: {result.ppl.toFixed(2)}</span>
    <Badge color={getPPLColor(result.ppl_risk)}>
      {result.ppl_risk}
    </Badge>
  </div>
)}
```

```typescript
// frontend/src/pages/layers/LayerStep4_1.tsx

interface SentenceAnalysis {
  patterns: Array<...>;
  void_matches?: Array<VoidMatch>;  // 新增
  has_syntactic_void?: boolean;  // 新增
}

// 在UI中显示句法空洞检测结果
{sentence.has_syntactic_void && (
  <Alert type="warning">
    <strong>Syntactic Void Detected:</strong>
    {sentence.void_matches.map(match => (
      <div key={match.position}>
        <code>{match.matched_text}</code>
        <p>{match.suggestion_zh}</p>
      </div>
    ))}
  </Alert>
)}
```

**实施工作量估计:**
- 后端集成: 2-3小时
- 前端UI更新: 1-2小时
- 测试验证: 1小时
- **总计: 4-6小时**

---

### 方案B: 重构统一 (彻底但耗时)

**目标:** 将旧版的 scorer.py 和 sentence_orchestrator.py 完全重构到新架构

**优点:**
- 代码更统一,维护成本低
- 消除技术债务

**缺点:**
- 工作量大(估计2-3天)
- 可能引入新bug
- 需要全面回归测试

**不推荐原因:** 当前新版5层架构已经稳定运行,大规模重构风险高

---

### 方案C: 渐进式迁移 (平衡方案)

**阶段1 (立即):** 采用方案A快速集成PPL和句法空洞检测
**阶段2 (1个月后):** 评估效果,决定是否需要深度重构
**阶段3 (3个月后):** 如果旧版API已无用户,可以安全删除

---

## 六、实施优先级建议 | Priority Recommendations

### 高优先级 ⭐⭐⭐

**理由:** 首页已经宣传了PPL检测和句法空洞检测,但新版系统实际没有,存在功能缺失

**建议行动:**
1. **本周内**完成方案A的实施
2. 在 Layer 1 (step5_1) 集成 PPL Calculator
3. 在 Layer 2 (step4_1) 集成 Syntactic Void Detector
4. 更新前端UI展示检测结果

### 中优先级 ⭐⭐

**理由:** 代码冗余,但不影响核心功能

**建议行动:**
1. 标记 scorer.py 和 sentence_orchestrator.py 为 DEPRECATED
2. 添加注释说明这些模块仅用于旧版API
3. 在文档中记录迁移计划

### 低优先级 ⭐

**理由:** 可以等待更合适的时机

**建议行动:**
1. 监控旧版API的使用率
2. 当使用率降至5%以下时,考虑完全删除
3. 在删除前确保所有功能已迁移到新版

---

## 七、测试计划 | Testing Plan

### 7.1 单元测试

```python
# test_ppl_integration.py

async def test_layer1_ppl_calculation():
    """测试Layer 1集成PPL计算"""
    result = await analyze_fingerprints(test_document_id)

    assert "ppl" in result
    assert result["ppl"] > 0
    assert result["ppl_risk"] in ["high", "medium", "low"]

async def test_layer2_void_detection():
    """测试Layer 2集成句法空洞检测"""
    result = await analyze_sentence_patterns(test_document_id)

    if result["has_syntactic_void"]:
        assert len(result["void_matches"]) > 0
        for match in result["void_matches"]:
            assert match["suggestion"] is not None
```

### 7.2 集成测试

使用真实AI生成文本测试:
1. 上传包含典型AI句式的文档
2. 运行完整5层流程
3. 验证 PPL < 20 的段落被正确标记为高风险
4. 验证包含 "underscores the significance of" 的句子被检测为句法空洞

### 7.3 性能测试

- PPL计算性能: 单段落(100词) < 500ms
- 句法空洞检测性能: 单句 < 100ms
- 确保不影响整体处理速度

---

## 八、结论与行动项 | Conclusion & Action Items

### 核心结论

**❌ 两个重要模型(PPL Calculator和Syntactic Void Detector)没有集成到新版5层架构中**

这导致:
- 首页宣传的功能实际不可用(PPL检测、句法空洞检测)
- 新版系统的检测准确性可能不如旧版
- 代码冗余和技术债务

### 立即行动项 (本周)

- [ ] **Day 1-2**: 实施方案A - 集成 PPL Calculator 到 Layer 1
- [ ] **Day 2-3**: 实施方案A - 集成 Syntactic Void Detector 到 Layer 2
- [ ] **Day 3**: 更新前端UI展示新功能
- [ ] **Day 4**: 编写单元测试和集成测试
- [ ] **Day 5**: 验证功能,更新文档

### 中期行动项 (1个月内)

- [ ] 收集用户反馈,评估集成效果
- [ ] 优化PPL和句法空洞的展示方式
- [ ] 考虑是否需要深度重构旧模块

### 长期行动项 (3个月内)

- [ ] 评估旧版API使用率
- [ ] 如果使用率低,计划删除旧版代码
- [ ] 完全消除代码冗余

---

> 文档创建: 2026-01-08
> 状态: 等待实施决策
> 推荐方案: **方案A - 快速集成 (4-6小时工作量)**
