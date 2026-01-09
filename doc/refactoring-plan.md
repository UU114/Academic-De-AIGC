# Detection Logic Refactoring Plan | 检测逻辑重构计划

> Version: v1.0
> Status: Approved / 已批准
> Created: 2026-01-07

## Overview | 概述

Refactor the current scattered detection logic into a unified 5-layer architecture with flexible steps within each layer.

将当前分散的检测逻辑重构为统一的5层架构，每层内部有灵活的步骤划分。

## Current Problems | 当前问题

1. **Function Overlap | 功能重叠**: Connector detection in 3 files, fingerprint detection in 3 places
2. **Level Confusion | 层级混乱**: Step 1-1 and 1-2 both doing Level 1 work with unclear boundaries
3. **Unintegrated Modules | 未集成模块**: syntactic_void.py, structure_predictability.py, anchor_density.py exist but aren't used

## New 5-Layer Architecture | 新5层架构

```
Layer 5: Document (文章层)     → Step 1.x series
Layer 4: Section (章节层)      → Step 2.x series
Layer 3: Paragraph (段落层)    → Step 3.x series
Layer 2: Sentence (句子层)     → Step 4.x series
Layer 1: Lexical (词汇层)      → Step 5.x series
```

---

## Layer 5: Document Level | 文章层 (Step 1.x)

**Step 1.1 - Structure Analysis | 结构分析**
- Detect overall document structure patterns
- Identify section boundaries and roles
- **Integrate**: structure_predictability.py (5-dimension scoring)

**Step 1.2 - Global Risk Assessment | 全局风险评估**
- Calculate document-level AIGC risk score
- Generate overall detection summary
- Determine which lower layers need attention

**Files to modify | 需修改文件**:
- `src/core/analyzer/smart_structure.py`
- `src/api/routes/analysis.py` (endpoints)
- `frontend/src/components/steps/Step1_1.tsx` → Rename to `LayerDocument.tsx`

---

## Layer 4: Section Level | 章节层 (Step 2.x)

**Step 2.1 - Section Logic Flow | 章节逻辑流**
- Analyze logical relationships between sections
- Check section sequence rationality
- Detect structural anomalies

**Step 2.2 - Section Transitions | 章节衔接**
- Analyze transition quality between sections
- Detect abrupt topic changes
- Evaluate cross-section coherence

**Step 2.3 - Section Length Distribution | 章节长度分布**
- Analyze length balance across sections
- Detect abnormal length patterns
- Calculate length CV (coefficient of variation)

**Files to modify | 需修改文件**:
- NEW: `src/core/analyzer/section_analyzer.py`
- `src/api/routes/analysis.py` (new endpoints)
- `frontend/src/components/steps/Step1_2.tsx` → Rename to `LayerSection.tsx`

---

## Layer 3: Paragraph Level | 段落层 (Step 3.x)

**Step 3.1 - Paragraph Role Detection | 段落角色识别**
- Classify each paragraph's function (intro, body, conclusion, transition)
- Detect role distribution anomalies
- Uses: `paragraph_logic.py` SentenceRole classification

**Step 3.2 - Paragraph Internal Coherence | 段落内部连贯性**
- Analyze sentence relationships within paragraphs
- Detect logic breaks
- Check topic sentence patterns

**Step 3.3 - Anchor Density Analysis | 锚点密度分析**
- **Integrate**: anchor_density.py (13 anchor types)
- Calculate anchors per 100 words
- Flag high hallucination risk (<5 anchors/100 words)

**Step 3.4 - Sentence Length Distribution | 段内句子长度分布**
- Analyze sentence length variation within each paragraph
- Detect monotonous length patterns (all similar length = high AIGC risk)
- Calculate within-paragraph length CV (coefficient of variation)
- Flag paragraphs with low burstiness
- Provide sentence length rebalancing suggestions

**Step 3.N - Per-Paragraph Editing (Dynamic) | 逐段编辑（动态）**
- When user requests: generate one step per flagged paragraph
- Maximum granularity: one step per paragraph
- User can edit individual paragraphs

**Files to modify | 需修改文件**:
- `src/core/analyzer/paragraph_logic.py`
- `src/core/analyzer/anchor_density.py` (integrate)
- `src/core/analyzer/burstiness.py` (add paragraph-level sentence length analysis)
- `frontend/src/components/steps/Step2.tsx` → Rename to `LayerParagraph.tsx`

---

## Layer 2: Sentence Level | 句子层 (Step 4.x)

> **IMPORTANT | 重要设计原则**:
> All sentence-level analysis MUST be performed within paragraph context.
> Sentence rewriting with context-aware content requires paragraph-level information for accuracy.
>
> 所有句子层分析必须在段落上下文中进行。
> 与上下文相关的句子改写需要段落级别信息的支持才能更准确。

**Step 4.1 - Sentence Pattern Detection | 句式模式检测**
- Detect repetitive sentence structures
- Analyze sentence length distribution (within paragraph context)
- Calculate burstiness score
- **Context**: Receives paragraph boundaries and role info from Layer 3

**Step 4.2 - Syntactic Void Detection | 句法空洞检测**
- **Integrate**: syntactic_void.py (spaCy en_core_web_md)
- Detect 7 void pattern types
- Flag hollow/empty constructions
- **Context**: Consider sentence position in paragraph for severity weighting

**Step 4.3 - Sentence Role Classification | 句子角色分类**
- 10 sentence roles: CLAIM, EVIDENCE, ANALYSIS, CRITIQUE, CONCESSION, SYNTHESIS, TRANSITION, CONTEXT, IMPLICATION, ELABORATION
- Extract from paragraph_logic.py to independent module
- **Context**: Role classification depends on surrounding sentences in paragraph

**Step 4.4 - Sentence Polish (Intervention/Yolo) | 句子润色** (CONTEXT-CRITICAL)
- Interactive sentence-by-sentence editing
- Two modes: Intervention (user confirms each) and Yolo (batch auto)
- **Context**: Rewriting prompts MUST include:
  - Full paragraph text for context
  - Sentence role in paragraph
  - Previous/next sentence for coherence
  - Paragraph's role in section

**Files to modify | 需修改文件**:
- `src/core/analyzer/burstiness.py`
- `src/core/analyzer/syntactic_void.py` (integrate)
- NEW: `src/core/analyzer/sentence_role.py` (extract from paragraph_logic.py)
- NEW: `src/core/analyzer/sentence_context.py` (paragraph context provider)
- `frontend/src/components/steps/Step3.tsx` → Rename to `LayerSentence.tsx`

---

## Layer 1: Lexical Level | 词汇层 (Step 5.x)

**Step 5.1 - Fingerprint Detection | 指纹词检测**
- Consolidate all fingerprint detection:
  - Type A: Dead Giveaways (+40 risk)
  - Type B: Academic Clichés (+5-25 risk)
  - Type C: Connectors (+10-30 risk)
- Move fingerprints from scorer.py to fingerprint.py

**Step 5.2 - Connector Analysis | 连接词分析**
- Analyze connector usage patterns
- Detect overuse of specific connectors
- Consolidate connector detection (currently in 3 files)

**Step 5.3 - Word-Level Risk | 词级风险**
- PPL (Perplexity) per-word analysis
- Individual word replacement suggestions

**Files to modify | 需修改文件**:
- `src/core/analyzer/fingerprint.py` (consolidate)
- `src/core/analyzer/connector.py`
- `src/core/analyzer/scorer.py` (remove fingerprint logic, keep scoring)
- NEW: `frontend/src/components/steps/LayerLexical.tsx`

---

## Backend API Structure | 后端API结构

```
/api/v1/analysis/
├── document/           # Layer 5
│   ├── structure      # Step 1.1
│   └── risk           # Step 1.2
├── section/           # Layer 4
│   ├── logic          # Step 2.1
│   ├── transition     # Step 2.2
│   └── length         # Step 2.3
├── paragraph/         # Layer 3
│   ├── role           # Step 3.1
│   ├── coherence      # Step 3.2
│   ├── anchor         # Step 3.3
│   └── sentence-length # Step 3.4
├── sentence/          # Layer 2 (requires paragraph context)
│   ├── pattern        # Step 4.1
│   ├── void           # Step 4.2
│   ├── role           # Step 4.3
│   └── polish         # Step 4.4 (context-critical)
└── lexical/           # Layer 1
    ├── fingerprint    # Step 5.1
    ├── connector      # Step 5.2
    └── word-risk      # Step 5.3
```

---

## Frontend Navigation | 前端导航

```
Document Analysis | 文档分析
├── [1] Document Layer | 文章层
│   └── 1.1 Structure → 1.2 Risk Assessment
├── [2] Section Layer | 章节层
│   └── 2.1 Logic → 2.2 Transitions → 2.3 Length
├── [3] Paragraph Layer | 段落层
│   └── 3.1 Roles → 3.2 Coherence → 3.3 Anchors → 3.4 Sentence Length → [3.N Per-paragraph]
├── [4] Sentence Layer | 句子层 (with paragraph context | 段落上下文)
│   └── 4.1 Patterns → 4.2 Void → 4.3 Roles → 4.4 Polish
└── [5] Lexical Layer | 词汇层
    └── 5.1 Fingerprints → 5.2 Connectors → 5.3 Word Risk
```

---

## Implementation Phases | 实施阶段

### Phase 1: Backend Restructure | 后端重构 ✅ COMPLETED
1. ✅ Create new directory structure: `src/core/analyzer/layers/`
2. ✅ Create layer orchestrators for each layer
3. ✅ Consolidate overlapping functions
4. ✅ Integrate unintegrated modules

**Completed 2026-01-07**: Created 8 new files, ~2300 lines of code

### Phase 2: API Refactoring | API重构 ✅ COMPLETED
1. ✅ Create new route structure under `/api/v1/analysis/`
2. ✅ Implement unified response format
3. ✅ Add layer-aware context passing

**Completed 2026-01-07**: Created 8 new API files, 30 endpoints
- `src/api/routes/analysis/__init__.py` - Module router
- `src/api/routes/analysis/schemas.py` - Unified request/response schemas
- `src/api/routes/analysis/document.py` - Layer 5 routes
- `src/api/routes/analysis/section.py` - Layer 4 routes
- `src/api/routes/analysis/paragraph.py` - Layer 3 routes
- `src/api/routes/analysis/sentence.py` - Layer 2 routes (with paragraph context)
- `src/api/routes/analysis/lexical.py` - Layer 1 routes
- `src/api/routes/analysis/pipeline.py` - Full pipeline orchestration

### Phase 3: Frontend Refactoring | 前端重构 ✅ COMPLETED
1. ✅ Create 5-layer analysis API service
2. ✅ Create Layer components (LayerDocument, LayerSection, LayerParagraph, LayerSentence, LayerLexical)
3. ✅ Implement flexible step navigation within layers
4. ✅ Update App.tsx routes for new layer components

**Completed 2026-01-07**: Created 7 new frontend files
- `frontend/src/services/analysisApi.ts` - 5-layer API service (~600 lines)
- `frontend/src/pages/layers/LayerDocument.tsx` - Layer 5 component
- `frontend/src/pages/layers/LayerSection.tsx` - Layer 4 component
- `frontend/src/pages/layers/LayerParagraph.tsx` - Layer 3 component
- `frontend/src/pages/layers/LayerSentence.tsx` - Layer 2 component (with paragraph context)
- `frontend/src/pages/layers/LayerLexical.tsx` - Layer 1 component
- `frontend/src/pages/layers/index.ts` - Module exports

### Phase 4: Integration Testing | 集成测试 ✅ COMPLETED
1. ✅ Test each layer independently - All 30 API endpoints tested
2. ✅ Test cross-layer context flow - Pipeline full/partial working
3. ✅ Frontend components - All 5 Layer components tested and working

**Completed 2026-01-07**:
- Backend: All 30 API endpoints tested and working
- Bug fixes: LayerContext full_text optional, pattern_issues dict-to-list conversion
- Schema fixes: Added `text` field to Section/Paragraph/Sentence requests with model_validator
- Frontend fixes: Updated Layer components to use `doc.originalText`, added `_get_paragraphs` helpers
- Route replacement: Upload.tsx and History.tsx now navigate to new Layer routes
- Frontend: All 5 Layer components fully tested with Playwright
  - LayerDocument: Risk 76 (High)
  - LayerSection: Risk 44 (Medium), 4 sections, 2 issues
  - LayerParagraph: Risk 37 (Medium), 5 issues
  - LayerSentence: Risk 10 (Low), 12 sentences
  - LayerLexical: Risk 18 (Low), fingerprint detection working

---

## Critical Files | 关键文件

**Backend to Modify**:
- `src/core/analyzer/scorer.py` - Remove fingerprint logic
- `src/core/analyzer/fingerprint.py` - Consolidate all fingerprints
- `src/core/analyzer/paragraph_logic.py` - Extract sentence roles
- `src/core/analyzer/syntactic_void.py` - Integrate into pipeline
- `src/core/analyzer/anchor_density.py` - Integrate into pipeline
- `src/core/analyzer/structure_predictability.py` - Integrate into pipeline
- `src/api/routes/analysis.py` - New endpoint structure

**Frontend to Modify**:
- `frontend/src/components/steps/Step1_1.tsx` → `LayerDocument.tsx`
- `frontend/src/components/steps/Step1_2.tsx` → `LayerSection.tsx`
- `frontend/src/components/steps/Step2.tsx` → `LayerParagraph.tsx`
- `frontend/src/components/steps/Step3.tsx` → `LayerSentence.tsx`
- NEW: `frontend/src/components/steps/LayerLexical.tsx`

**New Files to Create**:
- `src/core/analyzer/layers/document_orchestrator.py`
- `src/core/analyzer/layers/section_analyzer.py`
- `src/core/analyzer/layers/paragraph_orchestrator.py`
- `src/core/analyzer/layers/sentence_orchestrator.py`
- `src/core/analyzer/layers/lexical_orchestrator.py`
- `src/core/analyzer/sentence_role.py`
- `src/core/analyzer/sentence_context.py` - Paragraph context provider for sentence-level analysis

---

## Design Principles | 设计原则

1. **Coarse to Fine | 从粗到细**: Process document → section → paragraph → sentence → word
2. **Context Passing | 上下文传递**: Each layer receives context from upper layers
3. **Flexible Steps | 灵活步骤**: Steps within layers are dynamically determined by detected issues
4. **Maximum Granularity | 最大颗粒度**: One step per paragraph at most (for editing mode)
5. **Consolidated Logic | 整合逻辑**: No duplicate detection across files
6. **Sentence-in-Paragraph | 句子段落化**: Sentence analysis must be performed within paragraph context for context-aware accuracy | 句子分析必须在段落上下文中进行，以确保上下文相关内容的准确性
7. **Paragraph-Level Sentence Metrics | 段落级句子指标**: Sentence length distribution analysis belongs to paragraph layer, not sentence layer | 句子长度分布分析属于段落层而非句子层

---

> Related Documents | 相关文档:
> - `doc/detection-logic.md` - 检测逻辑详细分析
> - `doc/plan.md` - 项目总体计划
