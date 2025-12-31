# AcademicGuard 项目总结
# AcademicGuard Project Summary

---

## 一、项目概述 / Project Overview

**项目名称 / Project Name:** AcademicGuard
**英文全称 / Full Name:** Academic Paper AIGC Detection & Human-AI Collaborative Humanization Engine
**中文名称 / Chinese Name:** 英文论文 AIGC 检测与人源化协作引擎

**核心理念 / Core Philosophy:** **"AI教你改，而非AI替你改"** / **"AI teaches you to rewrite, not rewrite for you"**

AcademicGuard 是一套集"多维检测"与"人机协作改写"于一体的工具，帮助学术论文作者识别和修改可能被AIGC检测器（如Turnitin、GPTZero）标记的内容，同时保留学术专业性。

AcademicGuard is an integrated tool combining "multi-dimensional detection" with "human-AI collaborative rewriting", helping academic paper authors identify and modify content that may be flagged by AIGC detectors (like Turnitin, GPTZero) while preserving academic professionalism.

**开发状态 / Development Status:** Phase 1: MVP核心闭环 98% 完成 / Phase 1: MVP Core Loop 98% Complete

---

## 二、技术栈 / Technology Stack

### 2.1 后端 / Backend (Python)

| 组件 Component | 技术 Technology | 用途 Purpose |
|----------------|-----------------|--------------|
| 框架 Framework | FastAPI | 高性能异步API / High-performance async API |
| 服务器 Server | Uvicorn | ASGI服务器 / ASGI server |
| 数据验证 Validation | Pydantic 2.5+ | 请求响应验证 / Request/Response validation |
| ORM | SQLAlchemy 2.0+ | 数据库操作 / Database operations |
| NLP核心 | spaCy 3.7+ | 基础NLP处理 / Basic NLP processing |
| 学术NLP | Stanza 1.6+ | 依存句法分析 / Dependency parsing |
| 深度学习 | PyTorch 2.1+ | 神经网络框架 / Neural network framework |
| Transformers | Hugging Face 4.35+ | BERT/GPT模型 / BERT/GPT models |
| 语义相似度 | Sentence-Transformers | all-MiniLM-L6-v2模型 / Semantic similarity |
| LLM API | Anthropic SDK / OpenAI SDK | Claude/GPT API调用 / LLM API calls |

### 2.2 前端 / Frontend (TypeScript + React)

| 组件 Component | 技术 Technology | 用途 Purpose |
|----------------|-----------------|--------------|
| 框架 Framework | React 18+ | UI框架 / UI framework |
| 语言 Language | TypeScript 5.2+ | 类型安全 / Type safety |
| 构建工具 Build | Vite 5.0+ | 快速构建和HMR / Fast build and HMR |
| 样式 Styling | TailwindCSS 3.3+ | 原子化CSS / Atomic CSS |
| 状态管理 State | Zustand 4.4+ | 轻量级状态管理 / Lightweight state management |
| 路由 Routing | React Router 6.20+ | 页面路由 / Page routing |
| HTTP客户端 | Axios 1.6+ | API请求 / API requests |

### 2.3 数据库 / Database

- **开发环境:** SQLite (轻量、快速迭代)
- **生产环境:** PostgreSQL (推荐)

---

## 三、项目结构 / Project Structure

```
DEAI/
├── .env.example                  # Environment config template
├── README.md                     # Project documentation
├── requirements.txt              # Python dependencies
├── academicguard.db             # SQLite database
│
├── doc/                          # Documentation
│   ├── plan.md                   # Development plan
│   ├── structure.md              # Technical architecture
│   ├── process.md                # Development progress
│   └── algorithm-summary.md      # Algorithm logic summary
│
├── src/                          # Backend source code
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # Configuration management
│   │
│   ├── api/                      # API layer
│   │   ├── routes/
│   │   │   ├── documents.py      # Document upload/management
│   │   │   ├── analyze.py        # Text analysis
│   │   │   ├── suggest.py        # Rewrite suggestions (Track A/B/C)
│   │   │   ├── session.py        # Session management
│   │   │   └── export.py         # Result export
│   │   └── schemas.py            # Pydantic data models
│   │
│   ├── core/                     # Core business logic
│   │   ├── preprocessor/
│   │   │   ├── segmenter.py      # Sentence segmentation
│   │   │   └── term_locker.py    # Term locking (whitelist + NER)
│   │   │
│   │   ├── analyzer/
│   │   │   ├── fingerprint.py    # AI fingerprint word detection
│   │   │   ├── scorer.py         # Composite scorer (4 dimensions)
│   │   │   └── perplexity.py     # PPL calculation
│   │   │
│   │   ├── suggester/
│   │   │   ├── llm_track.py      # Track A: LLM intelligent rewriting
│   │   │   ├── rule_track.py     # Track B: Rule-based replacement
│   │   │   └── selector.py       # Suggestion selector
│   │   │
│   │   └── validator/
│   │       ├── semantic.py       # Semantic similarity (Sentence-BERT)
│   │       └── quality_gate.py   # Quality gate (multi-layer validation)
│   │
│   ├── db/
│   │   ├── database.py           # Database connection
│   │   └── models.py             # SQLAlchemy ORM models
│   │
│   └── utils/                    # Utility functions
│
├── data/                         # Data resources
│   ├── fingerprints/
│   │   ├── words.json            # Fingerprint word library (50+ words)
│   │   └── phrases.json          # Fingerprint phrase library (40+ phrases)
│   ├── synonyms/
│   │   └── level_preferences.json
│   └── terms/
│       └── whitelist.json        # Academic term whitelist
│
├── frontend/                     # Frontend source code
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       │
│       ├── components/
│       │   ├── common/           # Common components
│       │   ├── editor/           # Editor components
│       │   └── settings/         # Settings components
│       │
│       ├── pages/
│       │   ├── Home.tsx          # Home page
│       │   ├── Upload.tsx        # File upload
│       │   ├── Intervention.tsx  # Intervention mode
│       │   ├── Yolo.tsx          # YOLO mode
│       │   ├── Review.tsx        # Result review
│       │   └── History.tsx       # History
│       │
│       ├── stores/               # Zustand state stores
│       ├── services/             # API services
│       └── types/                # TypeScript types
│
├── scripts/                      # Dev scripts
├── tests/                        # Test directory
└── exports/                      # Export output directory
```

---

## 四、核心功能模块 / Core Functional Modules

### 4.1 预处理服务 / Preprocessing Service

**智能分句 (SentenceSegmenter):**
- 处理学术文本特殊情况（缩写、引用、小数点等）
- 自动识别：标题、章节、表格说明、图片说明、参考文献
- 过滤非正文内容（短于15字符）
- Handles special academic text cases (abbreviations, citations, decimals)
- Auto-identifies: titles, sections, table captions, figure captions, references

**术语锁定 (TermLocker):**
- 白名单术语识别（按学科分类）
- 统计模式识别（p < 0.05, R² = 0.89）
- 引用格式保护（[1], (Smith, 2020)）
- Whitelist term recognition (by discipline)
- Statistical pattern recognition
- Citation format protection

### 4.2 分析引擎 / Analysis Engine

**四维度评分系统 / Four-Dimensional Scoring System:**

| 维度 Dimension | 权重 Weight | 说明 Description |
|----------------|-------------|------------------|
| PPL (困惑度) | 0.35 | zlib压缩比（AI文本压缩率高）/ Compression ratio |
| 指纹词 Fingerprint | 0.30 | 一级词40分，二级词15分 / Level 1: +40, Level 2: +15 |
| 突发性 Burstiness | 0.20 | 句子长度标准差/平均值 / Sentence length variance |
| 结构 Structure | 0.15 | 连接词、空洞短语、模板 / Connectors, filler phrases |

**指纹词系统 / Fingerprint Word System:**
- **一级词 Level 1 (Dead Giveaways):** delve, tapestry, multifaceted, plethora, elucidate (+40分/word)
- **二级词 Level 2 (AI Habitual):** crucial, pivotal, paramount, moreover, furthermore (+15分/word)
- **指纹短语 Phrases:** "it is important to note that", "plays a crucial role" 等40+个

**风险等级 / Risk Levels:**

| 等级 Level | 分数 Score | 含义 Meaning |
|------------|------------|--------------|
| High 高风险 | ≥50 | 很可能是AI生成 / Likely AI-generated |
| Medium 中风险 | 25-49 | 有AI特征需注意 / Has AI features |
| Low 低风险 | 10-24 | 轻微AI特征 / Minor AI features |
| Safe 安全 | <10 | 人类写作风格 / Human writing style |

### 4.3 建议引擎 / Suggestion Engine

**轨道A: LLM智能改写 / Track A: LLM Intelligent Rewriting**
- 使用Claude/GPT-4 API
- 5级口语化风格提示词（0-10级用户可选）
- 支持词汇偏好映射
- Fallback机制（LLM失败用规则代替）

**轨道B: 规则替换 / Track B: Rule-based Replacement**
- 50+指纹词的多等级替换表
- 40+高频短语替换
- 句法调整（主被动转换、长句拆分）
- BERT MLM上下文感知替换

**轨道C: 用户自定义 / Track C: User Custom**
- 用户自行修改
- 提供3点写作建议
- 通过质量门控验证

### 4.4 验证服务 / Validation Service

**多层验证机制 / Multi-layer Validation:**
1. **语义层 Semantic:** Sentence-BERT相似度 ≥80%
2. **术语层 Terminology:** 锁定术语100%保留检查
3. **风险层 Risk:** 改写后风险评分降低

**失败处理 / Failure Handling:**
- 语义相似度<80% → 使用规则建议替代
- 仍然失败 → 标记为"需人工处理"
- 最多重试3次 → 超过则跳过

---

## 五、双模式架构 / Dual-Mode Architecture

### 5.1 干预模式 / Intervention Mode

**特点:** 逐句控制、精细修改、适合重要论文
**Features:** Sentence-by-sentence control, fine-grained editing, suitable for important papers

**工作流 / Workflow:**
1. 上传文档 → 自动分句和分析 / Upload → Auto segment & analyze
2. 逐句展示（左侧列表、右侧详情）/ Sentence-by-sentence display
3. 双轨建议选择或自定义修改 / Dual-track suggestions or custom edit
4. 实时验证 / Real-time validation
5. 标记为已处理/跳过/需审核 / Mark as processed/skip/review
6. 手动导航到下一句 / Manual navigation to next

### 5.2 YOLO模式 / YOLO Mode (Auto-processing)

**特点:** 自动处理、快速、适合长文档
**Features:** Auto processing, fast, suitable for long documents

**工作流 / Workflow:** (待完成 / To be completed)
1. 全文分析 / Full-text analysis
2. 自动应用最优建议 / Auto-apply best suggestions
3. 生成对比报告 / Generate comparison report
4. 用户最后审核 / User final review

---

## 六、API接口设计 / API Design

### 6.1 核心端点 / Core Endpoints

**文档处理 / Document Processing:**
```
POST   /api/v1/documents/upload         # Upload document
GET    /api/v1/documents/{id}           # Get document info
DELETE /api/v1/documents/{id}           # Delete document
```

**分析 / Analysis:**
```
POST   /api/v1/analyze                  # Analyze AIGC risk
```

**改写建议 / Suggestions:**
```
POST   /api/v1/suggest                  # Get dual-track suggestions
POST   /api/v1/suggest/apply            # Apply suggestion and validate
POST   /api/v1/suggest/custom           # Validate custom modification
POST   /api/v1/suggest/hints            # Get 3 writing hints
POST   /api/v1/suggest/analyze          # Deep syntax analysis (LLM)
```

**会话管理 / Session Management:**
```
POST   /api/v1/session/start            # Start session
GET    /api/v1/session/{id}/current     # Get current sentence
GET    /api/v1/session/{id}/sentences   # Get all sentences
POST   /api/v1/session/{id}/next        # Go to next sentence
POST   /api/v1/session/{id}/skip        # Skip current sentence
POST   /api/v1/session/{id}/flag        # Flag for manual review
```

**导出 / Export:**
```
POST   /api/v1/export/document          # Export final document
POST   /api/v1/export/report            # Export analysis report
```

---

## 七、数据流 / Data Flow

```
用户输入文本 / User Input
    ↓
[预处理服务 / Preprocessing]
  ├─ 文本分句 / Sentence Segmentation
  ├─ 内容类型识别 / Content Type Identification
  └─ 术语锁定 / Term Locking
    ↓
[分析引擎 / Analysis Engine]
  ├─ PPL计算 / PPL Calculation
  ├─ 指纹词检测 / Fingerprint Detection
  ├─ 突发性计算 / Burstiness Calculation
  ├─ 结构分析 / Structure Analysis
  └─ 综合评分 → 风险等级 / Composite Score → Risk Level
    ↓
[双轨建议生成 / Dual-Track Suggestions]
  ├─ 轨道A: LLM改写 / Track A: LLM Rewriting
  └─ 轨道B: 规则替换 / Track B: Rule Replacement
    ↓
[用户选择/自定义 / User Selection/Custom]
  ├─ 干预模式：逐句选择 / Intervention: Sentence-by-sentence
  └─ 轨道C：用户自行修改 / Track C: User custom edit
    ↓
[验证服务 / Validation Service]
  ├─ 语义相似度检查 / Semantic Similarity Check
  ├─ 术语完整性检查 / Term Integrity Check
  └─ 风险复检 / Risk Recheck
    ↓
[结果输出 / Output]
  ├─ 保存修改到数据库 / Save to database
  ├─ 返回新风险分数 / Return new risk score
  └─ 显示修改前后对比 / Show before/after comparison
```

---

## 八、数据库设计 / Database Design

| 表名 Table | 主要字段 Key Fields | 说明 Description |
|------------|---------------------|------------------|
| **documents** | id, filename, original_text, processed_text, status | 上传的文档 / Uploaded documents |
| **sessions** | id, document_id, mode, colloquialism_level, target_lang, status | 处理会话 / Processing sessions |
| **sentences** | id, document_id, index, original_text, analysis_json, risk_score, content_type | 分句结果 / Segmented sentences |
| **modifications** | id, sentence_id, session_id, source, modified_text, new_risk_score | 修改记录 / Modification records |
| **fingerprint_words** | word, category, risk_weight, replacements_json | 指纹词库 / Fingerprint library |
| **term_whitelist** | term, domain, user_defined | 术语白名单 / Term whitelist |

---

## 九、项目创新点 / Project Innovations

1. **分级指纹词系统 / Tiered Fingerprint System** - 区分AI的"确凿证据"和"常见习惯" / Distinguishes "dead giveaways" from "common habits"

2. **人类特征减分机制 / Human Feature Deduction** - 识别真实人类写作标记降低误判 / Reduces false positives by recognizing human writing markers

3. **双轨建议系统 / Dual-Track Suggestion System** - 让用户在AI智能改写和规则替换间选择 / User chooses between LLM and rules

4. **口语化程度参数 / Colloquialism Level** - 0-10级精细控制写作风格 / Fine-grained control of writing style

5. **术语自动锁定 / Auto Term Locking** - 保护学科关键词和统计数据 / Protects discipline keywords and statistics

6. **干预模式 / Intervention Mode** - 用户完全控制修改过程 / Full user control over modifications

---

## 十、与竞品对比 / Comparison with Competitors

| 特性 Feature | Turnitin | GPTZero | AcademicGuard |
|--------------|----------|---------|---------------|
| 检测类型 Detection | 抄袭+AIGC | AIGC | AIGC |
| 提供建议 Suggestions | 否 No | 否 No | **是 Yes** |
| 人机协作 Human-AI Collab | 否 No | 否 No | **是 Yes** |
| 保护术语 Term Protection | 否 No | 否 No | **是 Yes** |
| 口语化等级 Colloquialism | 无 None | 无 None | **0-10级** |
| 本地部署 Self-hosted | 否 No | 否 No | **是 Yes** |

---

## 十一、启动与运行 / Getting Started

### 后端 / Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端 / Frontend
```bash
cd frontend
npm install
npm run dev
```

### 访问 / Access
- 前端 Frontend: http://localhost:5173
- 后端API Backend: http://localhost:8000
- API文档 Docs: http://localhost:8000/docs

---

## 十二、开发进度 / Development Progress

**已完成 / Completed (Phase 1 - 98%):**
- ✅ 后端框架搭建 / Backend framework
- ✅ 核心模块实现 / Core modules implementation
- ✅ 前端UI完成 / Frontend UI
- ✅ API接口实现 / API endpoints
- ✅ 数据库模型 / Database models
- ✅ 干预模式功能 / Intervention mode
- ✅ 建议缓存机制 / Suggestion caching

**待完成 / To Be Completed:**
- [ ] YOLO模式后端逻辑 / YOLO mode backend
- [ ] 端到端集成测试 / E2E integration tests
- [ ] LLM API完整测试 / LLM API full testing
- [ ] 性能优化 / Performance optimization
- [ ] 生产部署配置 / Production deployment

---

*文档生成时间 / Generated: 2025-12-31*
