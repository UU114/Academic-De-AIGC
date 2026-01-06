# AcademicGuard

**英文论文 AIGC 检测与人源化协作引擎**
**Academic Paper AIGC Detection & Human-AI Collaborative Humanization Engine**

<p align="center">
  <img src="doc/assets/logo.png" alt="AcademicGuard Logo" width="200" />
</p>

<p align="center">
  <strong>🎯 AI 教你改，而非 AI 替你改 | AI guides you to revise, not revise for you</strong>
</p>

---

## 📋 目录 | Table of Contents

- [项目背景 | Background](#-项目背景--background)
- [解决的痛点 | Problems Solved](#-解决的痛点--problems-solved)
- [项目特点 | Features](#-项目特点--features)
- [工作逻辑 | How It Works](#-工作逻辑--how-it-works)
- [效果展示 | Demo](#-效果展示--demo)
- [技术架构 | Architecture](#-技术架构--architecture)
- [部署方法 | Deployment](#-部署方法--deployment)
- [模型下载 | Models](#-模型下载--models)
- [API 接口 | APIs](#-api-接口--apis)
- [预留接口 | Reserved Interfaces](#-中央平台预留接口--central-platform-reserved-interfaces)
- [配置说明 | Configuration](#-配置说明--configuration)
- [开发路线 | Roadmap](#-开发路线--roadmap)
- [许可证 | License](#-许可证--license)

---

## 🎯 项目背景 | Background

### 中文

随着 ChatGPT、Claude 等大语言模型 (LLM) 的普及，学术论文中 AI 生成内容 (AIGC) 的检测已成为学术界的重大挑战。Turnitin、GPTZero、Originality.AI 等检测工具相继问世，许多论文因"AI 特征过于明显"而遭到质疑或拒稿。

然而，现有的"降 AI 率"工具往往采用简单的同义词替换或随机打乱，导致：
- 学术表达被破坏，专业术语被错误替换
- 文章逻辑断裂，可读性大幅下降
- 治标不治本，无法从根本上消除 AI 痕迹

**AcademicGuard** 诞生于此需求——我们不做"AI 替你改"的黑盒工具，而是构建一套**人机协作的改写引导系统**，帮助作者理解 AI 写作的问题所在，并提供专业的改写建议，最终由作者本人完成高质量的修改。

### English

With the widespread adoption of large language models (LLMs) like ChatGPT and Claude, detecting AI-generated content (AIGC) in academic papers has become a significant challenge. Tools like Turnitin, GPTZero, and Originality.AI have emerged, and many papers face rejection due to "obvious AI characteristics."

However, existing "AI reduction" tools often rely on simple synonym replacement or random shuffling, resulting in:
- Academic expressions destroyed, technical terms incorrectly replaced
- Article logic broken, readability significantly reduced
- Treating symptoms not causes, unable to fundamentally eliminate AI traces

**AcademicGuard** was born from this need—we don't build black-box tools that "AI revises for you." Instead, we construct a **human-AI collaborative revision guidance system** that helps authors understand the problems in AI writing, provides professional revision suggestions, and ultimately enables authors to complete high-quality modifications themselves.

---

## 🔥 解决的痛点 | Problems Solved

| 痛点 Problem | 传统方案 Traditional Solution | AcademicGuard 方案 |
|--------------|------------------------------|-------------------|
| **AI 检测风险高** | 同义词随机替换 | 三阶分析 + 指纹消除 + PPL 优化 |
| **学术性被破坏** | 无法识别术语 | 智能术语锁定 + 引用格式保护 |
| **修改质量低** | 机器自动改写 | 人机协作 + 双轨建议 |
| **无法理解问题** | 黑盒处理 | 可视化风险评分 + 详细诊断报告 |
| **文章逻辑断裂** | 仅处理句子级 | 三阶流程：结构→衔接→句子 |
| **风格不一致** | 忽略风格分析 | 口语化程度检测 (0-10级) |
| **效率低下** | 逐句手动处理 | YOLO 模式 + 批量合并修改 |

---

## ✨ 项目特点 | Features

### 🏗️ 三阶分析架构 | Three-Level Analysis Architecture

区别于传统的句子级处理，AcademicGuard 采用**宏观→中观→微观**的渐进式优化：

Unlike traditional sentence-level processing, AcademicGuard uses **macro→meso→micro** progressive optimization:

```
┌─────────────────────────────────────────────────────────────────┐
│  Level 1: 骨架重组 (Skeleton Restructuring)                     │
│  ├── 全文结构诊断：检测线性流程、重复模式、均句长度             │
│  ├── 风格等级分析：0-10级口语化程度评估                         │
│  └── 章节建议：拆分/合并/补充内容的具体指导                     │
├─────────────────────────────────────────────────────────────────┤
│  Level 2: 关节润滑 (Joint Lubrication)                          │
│  ├── 逻辑断层检测：段落间语义连接缺失识别                       │
│  ├── 显性连接词捕获：高频 AI 连接词标记                         │
│  └── 语义回声生成：自然承接句替代机械连接词                     │
├─────────────────────────────────────────────────────────────────┤
│  Level 3: 皮肤精修 (Surface Polishing)                          │
│  ├── 指纹消除：40+ AI 高频词/短语识别与替换                     │
│  ├── 句式重组：打破公式化句型                                   │
│  └── 双轨建议：LLM 智能改写 + 规则替换                          │
└─────────────────────────────────────────────────────────────────┘
```

### 🛡️ 硬核 De-AIGC 技术 | Hardcore De-AIGC Technologies

| 技术 Technology | 说明 Description |
|-----------------|------------------|
| **CAASS v2.0 评分** | Context-Aware Adaptive Scoring System，上下文感知的动态风险评分 |
| **ONNX PPL 计算** | 使用 distilgpt2 模型计算真实 token 级困惑度，🤯/⚠️/🤖 直观展示 |
| **突发性分析** | Burstiness Detection，检测句子长度和结构的单一性 |
| **语义回声** | Semantic Echo，提取上段核心概念生成自然承接句 |
| **术语保护** | 自动锁定学术术语、统计数据 (p < 0.05)、引用格式 |
| **40+ 指纹词库** | 高频 AI 词/短语检测与智能替换建议 |
| **18点 LLM 改写技术** | 句式多样性、长句保护、逻辑框架重排、嵌套从句生成等 |
| **Step2-Step3 联动** | 句长规划与句子改写协同，逻辑类型驱动改写策略 |

### 💡 人机协作模式 | Human-AI Collaboration Modes

| 模式 Mode | 特点 Features | 适用场景 Use Case |
|-----------|--------------|------------------|
| **干预模式 Intervention** | 每步手动选择方案，完全控制 | 重要论文、高质量要求 |
| **YOLO 模式 Auto** | 全自动处理 L1→L2→L3，最后统一审核 | 时间紧迫、快速处理 |
| **批量修改 Merge Modify** | 勾选多问题，生成统一 Prompt 或直接修改 | 批量相似问题 |

### 🔀 双轨建议系统 | Dual-Track Suggestion System

| Track | 技术基础 | 优势 Advantages |
|-------|---------|-----------------|
| **Track A: LLM 智能建议** | Claude / GPT-4 / DeepSeek | 语义理解深、改写自然、处理复杂句式 |
| **Track B: 规则替换** | 指纹词库 + 语法规则 | 快速、可控、预测性强、成本低 |

---

## ⚙️ 工作逻辑 | How It Works

### 整体流程 | Overall Flow

```
                    ┌──────────────────┐
                    │   上传文档       │
                    │  Upload Document │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   预处理服务     │
                    │  Preprocessing   │
                    │  • 句子分割      │
                    │  • 术语锁定      │
                    │  • 格式保护      │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│  Level 1      │   │  Level 2      │   │  Level 3      │
│  结构分析     │──▶│  衔接分析     │──▶│  句子精修     │
│  Structure    │   │  Transition   │   │  Polishing    │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        │    ┌──────────────┴───────────────┐   │
        │    │       核心分析引擎           │   │
        │    │   Core Analysis Engine       │   │
        │    │  • CAASS v2.0 评分          │   │
        │    │  • PPL 困惑度计算           │   │
        │    │  • 指纹词检测               │   │
        │    │  • 突发性分析               │   │
        │    └──────────────────────────────┘   │
        │                                       │
        └───────────────────┬───────────────────┘
                            │
                   ┌────────▼─────────┐
                   │   建议生成引擎   │
                   │ Suggestion Engine│
                   │  • LLM Track     │
                   │  • Rule Track    │
                   └────────┬─────────┘
                            │
                   ┌────────▼─────────┐
                   │   用户选择/修改  │
                   │ User Selection   │
                   └────────┬─────────┘
                            │
                   ┌────────▼─────────┐
                   │   验证服务       │
                   │  Validation      │
                   │  • 语义保持检测  │
                   │  • 术语完整性    │
                   └────────┬─────────┘
                            │
                   ┌────────▼─────────┐
                   │   导出结果       │
                   │  Export Result   │
                   └──────────────────┘
```

### 详细阶段说明 | Detailed Stage Description

#### Level 1: 结构分析 (Structure Analysis)

```python
# Key Analysis Points:
# 1. Linear Flow Detection - Identify overly predictable paragraph sequences
# 2. Repetition Pattern - Find repeated sentence structures
# 3. Average Sentence Length - Detect uniform AI-like length distribution
# 4. Style Score (0-10) - Measure formality level vs target style
```

**输入 Input:** 完整文档
**输出 Output:** 结构问题列表 + 分章节修改建议

#### Level 2: 衔接分析 (Transition Analysis)

```python
# Key Analysis Points:
# 1. Logic Gap Detection - Missing semantic connections between paragraphs
# 2. Explicit Connector Capture - High-frequency AI connectors (Furthermore, Moreover...)
# 3. Semantic Echo Generation - Natural bridging sentences from core concepts
```

**输入 Input:** 相邻段落对
**输出 Output:** 衔接问题 + 语义回声替代句

#### Level 3: 句子精修 (Sentence Polishing)

```python
# Key Analysis Points:
# 1. Fingerprint Detection - 40+ AI signature words/phrases
# 2. PPL Calculation - Token-level perplexity scoring
# 3. Burstiness Analysis - Sentence length variation
# 4. Dual-Track Suggestions - LLM + Rule-based recommendations
# 5. Sentence Structure Diversity - Simple/Compound/Complex distribution
# 6. Long Sentence Protection - Preserve tight-logic sentences
# 7. Step2-Step3 Coordination - Logic-type driven rewriting
```

**输入 Input:** 单句/句子列表 + Step2句长规划 (可选)
**输出 Output:** 风险评分 + 双轨改写建议 + 句式分析

**18点 De-AIGC 改写技术 | 18-Point De-AIGC Rewriting Techniques:**

| 编号 | 技术 | 说明 |
|------|------|------|
| #1-#12 | 基础技术 | 术语保护、主语多样化、句长节奏、Hedging平衡等 |
| #13 | 句式多样性 | Simple 15-25%, Compound 20-30%, Complex 35-45% |
| #14 | 长句保护 | 紧密逻辑句子不拆分 (限定条件链/嵌套因果/对比综合) |
| #15 | 逻辑框架重排 | 打破 AI "原因→过程→结果" 线性模式 |
| #16 | 嵌套从句生成 | 关系从句、非限制性从句、分词短语 |
| #17 | 功能词丰富化 | 代词/助动词/介词密度 45-55% (人类特征) |
| #18 | Perplexity提升 | 领域词汇、意外过渡、同义词变化 |

---

## 📸 效果展示 | Demo

### 结构分析界面 | Structure Analysis Interface

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 结构分析报告 | Structure Analysis Report                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  风格评分 Style Score: 7/10 (学术论文级 Academic Paper Level)       │
│  ⚠️ 检测到风格不匹配：第3段口语化程度过高                           │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🔴 高风险区域 High Risk Zones                               │   │
│  │                                                             │   │
│  │ • Section 2: 线性流程过于明显 (Linear flow too obvious)     │   │
│  │   建议: 增加反例讨论或对比分析                              │   │
│  │                                                             │   │
│  │ • Section 4: 重复句式 "This demonstrates..." 出现 5 次     │   │
│  │   建议: 使用多样化的论证表达                                │   │
│  │                                                             │   │
│  │ ☑ 选择问题 → [生成 Prompt] [直接修改]                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 句子精修界面 | Sentence Polishing Interface

```
┌─────────────────────────────────────────────────────────────────────┐
│  ✍️ 句子精修 | Sentence Polishing                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  原句 Original:                                                     │
│  "It is important to note that this methodology demonstrates        │
│   significant improvements in overall performance metrics."         │
│                                                                     │
│  风险评分 Risk Score: 72/100 🔴                                     │
│  PPL: 15.3 🤖 (低困惑度 = 高 AI 特征)                               │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🔍 检测到的问题 Detected Issues:                            │   │
│  │                                                             │   │
│  │ • "It is important to note that" ← AI 指纹短语              │   │
│  │ • "demonstrates significant" ← 高频 AI 搭配                 │   │
│  │ • "overall performance" ← 模糊表达                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 💡 Track A: LLM 建议                                        │   │
│  │ "This methodology yielded a 23% accuracy boost compared     │   │
│  │  to baseline approaches in our experiments."                │   │
│  │                                       [采用 Accept]         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🔧 Track B: 规则替换                                        │   │
│  │ "The methodology shows notable gains in performance."       │   │
│  │ (替换: important to note → 删除, demonstrates → shows)      │   │
│  │                                       [采用 Accept]         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [上一句 Prev] [跳过 Skip] [下一句 Next]                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### PPL 可视化 | PPL Visualization

```
句子 1: The results clearly demonstrate...        PPL: 12.4 🤖
句子 2: Furthermore, it should be noted that...   PPL: 8.7  🤖
句子 3: We observed unexpected fluctuations...    PPL: 45.2 🤯
句子 4: This phenomenon suggests...               PPL: 18.9 ⚠️

🤖 = 低 PPL (高 AI 特征)  ⚠️ = 中等风险  🤯 = 高 PPL (人类特征)
```

---

## 🏛️ 技术架构 | Architecture

### 系统架构图 | System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend Layer (React 18)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ Structure   │ │ Transition  │ │ Polishing   │ │ Dashboard │ │
│  │ Analysis    │ │ Analysis    │ │ Editor      │ │ & History │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│                         │ Zustand State │                       │
└─────────────────────────┼───────────────┼───────────────────────┘
                          │  REST API     │
┌─────────────────────────▼───────────────▼───────────────────────┐
│                    API Gateway (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Routes: /analyze, /structure, /suggest, /session, etc. │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Core Business Layer                          │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │ Analyzer      │ │ Suggester     │ │ Validator     │         │
│  │ • Fingerprint │ │ • LLM Track   │ │ • Semantic    │         │
│  │ • Structure   │ │ • Rule Track  │ │ • Quality     │         │
│  │ • PPL (ONNX)  │ │ • 18-Point    │ │               │         │
│  │ • Scorer      │ │   De-AIGC     │ │               │         │
│  │ • Sentence    │ │               │ │               │         │
│  │   Structure   │ │               │ │               │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Infrastructure Layer                         │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │ LLM Services  │ │ NLP Models    │ │ Database      │         │
│  │ • Volcengine  │ │ • spaCy       │ │ • SQLite/PG   │         │
│  │ • Anthropic   │ │ • Stanza      │ │ • Alembic     │         │
│  │ • OpenAI      │ │ • ONNX PPL    │ │               │         │
│  │ • Gemini      │ │ • Sentence-   │ │               │         │
│  │ • DeepSeek    │ │   Transformers│ │               │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈详情 | Tech Stack Details

#### 后端 Backend

| 层级 Layer | 技术 Technology | 版本 Version |
|------------|-----------------|--------------|
| Framework | FastAPI | 0.104.0+ |
| Server | Uvicorn | 0.24.0+ |
| Validation | Pydantic | 2.5.0+ |
| ORM | SQLAlchemy | 2.0.23+ |
| Async DB | aiosqlite | 0.19.0+ |
| NLP Core | spaCy | 3.7.0+ |
| Academic NLP | Stanza | 1.6.0+ |
| Deep Learning | PyTorch | 2.1.0+ |
| Transformers | Hugging Face | 4.35.0+ |
| Embedding | Sentence-Transformers | 2.2.0+ |
| PPL Engine | ONNX Runtime | 1.16.0+ |

#### 前端 Frontend

| 技术 Technology | 版本 Version | 用途 Purpose |
|-----------------|--------------|--------------|
| React | 18+ | UI Framework |
| TypeScript | 5.2+ | Type Safety |
| Vite | 5.0+ | Build Tool |
| TailwindCSS | 3.3+ | Styling |
| Zustand | 4.4+ | State Management |
| React Router | 6.20+ | Routing |
| Axios | 1.6+ | HTTP Client |
| Recharts | 3.6.0+ | Data Visualization |

---

## 🚀 部署方法 | Deployment

### 环境要求 | Requirements

- **Python**: 3.8+ (推荐 3.10+)
- **Node.js**: 18+ (推荐 20 LTS)
- **RAM**: 8GB+ (PPL 模型加载需要)
- **Disk**: 5GB+ (模型文件)

### 方式一：开发环境 | Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourorg/academicguard.git
cd academicguard

# 2. Create Python virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Download NLP models (first time only)
python -m spacy download en_core_web_sm
python -c "import stanza; stanza.download('en')"

# 5. Install frontend dependencies
cd frontend
npm install
cd ..

# 6. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 7. Initialize database
python -c "from src.db.database import init_db; import asyncio; asyncio.run(init_db())"

# 8. Start services
# Terminal 1 - Backend:
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend:
cd frontend && npm run dev
```

### 方式二：Docker 部署 | Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**docker-compose.yml 示例:**

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/academicguard.db
      - VOLCENGINE_API_KEY=${VOLCENGINE_API_KEY}
    volumes:
      - ./data:/app/data
      - ./models:/app/models

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

### 方式三：生产部署 | Production Deployment

```bash
# 1. Use production database (PostgreSQL recommended)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/academicguard

# 2. Use Gunicorn with Uvicorn workers
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# 3. Build frontend for production
cd frontend
npm run build
# Serve with Nginx or similar

# 4. Enable HTTPS (required for production)
# Configure with Nginx/Caddy reverse proxy
```

### 访问地址 | Access URLs

| 服务 Service | 开发环境 Dev | 生产环境 Prod |
|--------------|-------------|---------------|
| 前端界面 Frontend | http://localhost:5173 | https://yourdomain.com |
| API 文档 Docs | http://localhost:8000/docs | https://api.yourdomain.com/docs |
| 后台管理 Admin | http://localhost:5173/admin | https://yourdomain.com/admin |

---

## 📦 模型下载 | Models

### 必需模型 | Required Models

| 模型 Model | 用途 Purpose | 下载方式 Download |
|------------|-------------|-------------------|
| **distilgpt2 (ONNX)** | PPL 困惑度计算 | 自动下载 / Auto download |
| **en_core_web_sm** | spaCy 基础 NLP | `python -m spacy download en_core_web_sm` |
| **Stanza English** | 依存句法分析 | `stanza.download('en')` |

### 可选模型 | Optional Models

| 模型 Model | 用途 Purpose | 下载方式 Download |
|------------|-------------|-------------------|
| **all-MiniLM-L6-v2** | 语义相似度 | 自动下载 (sentence-transformers) |
| **en_core_web_trf** | 高精度 NLP | `python -m spacy download en_core_web_trf` |

### 模型存储位置 | Model Storage

```
models/
├── onnx/
│   └── distilgpt2/           # PPL model (auto-download)
├── spacy/                    # spaCy models (via spacy download)
└── stanza_resources/         # Stanza models (via stanza.download)
```

### 首次运行模型初始化 | First Run Model Initialization

```python
# Run this script for first-time setup
python scripts/init_models.py
```

```python
# scripts/init_models.py content:
import spacy
import stanza
from sentence_transformers import SentenceTransformer

# Download spaCy model
spacy.cli.download("en_core_web_sm")

# Download Stanza model
stanza.download('en')

# Download sentence transformer (for semantic similarity)
SentenceTransformer('all-MiniLM-L6-v2')

print("All models downloaded successfully!")
```

---

## 📡 API 接口 | APIs

### 核心分析接口 | Core Analysis APIs

| 方法 | 端点 Endpoint | 功能 Function |
|------|---------------|---------------|
| POST | `/api/v1/analyze/` | 句子级 AIGC 分析 |
| POST | `/api/v1/structure/` | 全文结构分析 |
| POST | `/api/v1/paragraph/` | 段落逻辑分析 |
| POST | `/api/v1/transition/` | 段落衔接分析 |
| POST | `/api/v1/structure-guidance/` | 结构引导分析 |

### 建议生成接口 | Suggestion APIs

| 方法 | 端点 Endpoint | 功能 Function |
|------|---------------|---------------|
| POST | `/api/v1/suggest/` | 双轨建议 (LLM + 规则) |
| POST | `/api/v1/suggest/custom` | 自定义 Prompt 建议 |
| POST | `/api/v1/suggest/verify` | 建议验证 |

### 流程控制接口 | Flow Control APIs

| 方法 | 端点 Endpoint | 功能 Function |
|------|---------------|---------------|
| POST | `/api/v1/flow/start` | 启动三阶流程 |
| GET | `/api/v1/flow/{id}/progress` | 获取流程进度 |
| POST | `/api/v1/flow/{id}/complete-level` | 完成当前阶段 |

### 文档管理接口 | Document APIs

| 方法 | 端点 Endpoint | 功能 Function |
|------|---------------|---------------|
| POST | `/api/v1/documents/upload` | 上传文档 |
| GET | `/api/v1/documents/{id}` | 获取文档 |
| GET | `/api/v1/documents/` | 列出所有文档 |
| DELETE | `/api/v1/documents/{id}` | 删除文档 |

### 认证与支付接口 | Auth & Payment APIs

| 方法 | 端点 Endpoint | 功能 Function |
|------|---------------|---------------|
| POST | `/api/v1/auth/register` | 用户注册 (电话+密码+邮箱) |
| POST | `/api/v1/auth/login` | 用户登录 |
| POST | `/api/v1/payment/pay` | 发起支付 |
| POST | `/api/v1/payment/callback` | 支付回调 (Webhook) |

### 管理员接口 | Admin APIs

| 方法 | 端点 Endpoint | 功能 Function |
|------|---------------|---------------|
| POST | `/api/v1/admin/login` | 管理员登录 |
| GET | `/api/v1/admin/stats` | 统计数据 (营收/任务/用户) |
| GET | `/api/v1/admin/dashboard` | 仪表板数据 |

### API 示例 | API Examples

#### 句子分析 | Sentence Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "It is important to note that this methodology demonstrates significant improvements."
  }'
```

**Response:**
```json
{
  "risk_score": 72,
  "ppl": 15.3,
  "ppl_emoji": "🤖",
  "fingerprints": [
    {"phrase": "It is important to note that", "weight": 0.8},
    {"phrase": "demonstrates significant", "weight": 0.6}
  ],
  "suggestions": {
    "llm": "This methodology yielded notable improvements...",
    "rule": "The methodology shows significant gains..."
  }
}
```

---

## 🔌 中央平台预留接口 | Central Platform Reserved Interfaces

本节描述 AcademicGuard 与外部中央平台对接所需的接口规范。

### 认证接口 | Authentication Interfaces

#### 发送短信验证码 | Send SMS Code

```http
POST {PLATFORM_BASE_URL}/api/v1/auth/send-sms
Content-Type: application/json

{
    "phone": "13800138000",
    "app_id": "academicguard"
}
```

**Response:**
```json
{
    "success": true,
    "message": "sent",
    "expires_in": 300
}
```

#### 验证码登录 | Verify & Login

```http
POST {PLATFORM_BASE_URL}/api/v1/auth/verify-sms
Content-Type: application/json

{
    "phone": "13800138000",
    "code": "123456",
    "app_id": "academicguard"
}
```

**Response:**
```json
{
    "success": true,
    "user_id": "platform_uid_xxx",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "refresh_token_xxx",
    "expires_in": 86400
}
```

### 支付接口 | Payment Interfaces

#### 创建支付订单 | Create Payment Order

```http
POST {PLATFORM_BASE_URL}/api/v1/payments/create
Authorization: Bearer {PLATFORM_API_KEY}
Content-Type: application/json

{
    "app_id": "academicguard",
    "external_order_id": "task_uuid_xxx",
    "user_id": "platform_uid_xxx",
    "amount": 50.00,
    "currency": "CNY",
    "description": "AcademicGuard - 3200词文档处理",
    "notify_url": "https://yoursite.com/api/v1/payment/callback"
}
```

#### 支付回调 | Payment Callback (Webhook)

```http
POST https://yoursite.com/api/v1/payment/callback
X-Signature: hmac_sha256_signature
Content-Type: application/json

{
    "order_id": "platform_order_xxx",
    "external_order_id": "task_uuid_xxx",
    "status": "paid",
    "amount": 50.00,
    "timestamp": 1704096600,
    "signature": "hmac_sha256_signature_string"
}
```

### 接口状态码 | Status Codes

| 状态码 | 说明 Description |
|--------|------------------|
| `created` | 订单已创建，待支付 |
| `pending` | 支付处理中 |
| `paid` | 支付成功 |
| `failed` | 支付失败 |
| `cancelled` | 订单已取消 |
| `refunded` | 已退款 |

---

## ⚙️ 配置说明 | Configuration

### 环境变量 | Environment Variables

```env
# ============ 系统模式 | System Mode ============
SYSTEM_MODE=debug  # debug | operational

# ============ LLM API Keys ============
# Volcengine (DeepSeek v3) - Recommended
VOLCENGINE_API_KEY=your_key
VOLCENGINE_ENDPOINT_ID=your_endpoint_id

# Anthropic (Claude)
ANTHROPIC_API_KEY=your_key

# OpenAI
OPENAI_API_KEY=your_key

# Google Gemini
GEMINI_API_KEY=your_key

# DeepSeek Direct
DEEPSEEK_API_KEY=your_key

# ============ LLM 配置 | LLM Config ============
LLM_PROVIDER=volcengine  # volcengine | anthropic | openai | gemini | deepseek
LLM_MODEL=deepseek-v3-2-251201
LLM_MAX_TOKENS=1024
LLM_TEMPERATURE=0.7

# ============ 分析阈值 | Analysis Thresholds ============
PPL_THRESHOLD_HIGH=20.0      # PPL < 20: High AI risk
PPL_THRESHOLD_MEDIUM=40.0    # PPL < 40: Medium risk
SEMANTIC_SIMILARITY_THRESHOLD=0.80

# ============ 数据库 | Database ============
DATABASE_URL=sqlite+aiosqlite:///./data/academicguard.db
# For production:
# DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/academicguard

# ============ 中央平台 (运营模式) | Central Platform ============
PLATFORM_BASE_URL=https://api.yourplatform.com
PLATFORM_API_KEY=your_api_key
PLATFORM_APP_ID=academicguard

# ============ 定价 | Pricing ============
PRICE_PER_100_WORDS=2.0
MINIMUM_CHARGE=50.0

# ============ 安全 | Security ============
JWT_SECRET_KEY=your-super-secret-key
JWT_EXPIRE_MINUTES=1440
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password

# ============ 任务 | Task ============
TASK_EXPIRY_HOURS=24
```

### 双模式系统 | Dual-Mode System

| 模式 Mode | 登录 Login | 支付 Payment | 用途 Purpose |
|-----------|-----------|--------------|--------------|
| `debug` (默认) | 不需要 | 免费 | 开发测试 |
| `operational` | 需要 | 按字数收费 | 正式运营 |

### 计费规则 | Billing Rules (Operational Mode)

- **计费单位 Unit**: 100词/单元，向上取整
- **定价 Price**: ¥2.0 / 100词
- **最低消费 Minimum**: ¥50.0
- **字数统计 Word Count**: 自动排除参考文献部分

---

## 🗺️ 开发路线 | Roadmap

### ✅ 已完成 | Completed (MVP 98%)

- [x] 三阶分析流程 (Three-Level Flow)
- [x] CAASS v2.0 评分系统
- [x] ONNX PPL 困惑度计算
- [x] 40+ 指纹词库检测
- [x] 双轨建议系统 (LLM + Rule)
- [x] 干预/YOLO 双模式
- [x] 语义回声 (Semantic Echo)
- [x] 批量合并修改 (Merge Modify)
- [x] 用户认证 (电话+密码+邮箱)
- [x] 管理员后台仪表板
- [x] 多 LLM 支持 (Claude/GPT/DeepSeek/Gemini)
- [x] Step2-Step3 联动 (逻辑类型驱动句子改写)
- [x] 18点 LLM De-AIGC 改写技术
- [x] 句式多样性与长句保护
- [x] 句子结构分析器 (Simple/Compound/Complex检测)

### 🚧 进行中 | In Progress

- [ ] 文档导出功能 (Word/PDF)
- [ ] 批量文档处理
- [ ] 移动端适配

### 📋 计划中 | Planned

- [ ] 浏览器插件版本
- [ ] API 开放平台
- [ ] 多语言支持 (中文论文)
- [ ] 自定义指纹词库
- [ ] 团队协作功能

---

## 📄 许可证 | License

MIT License

---

## 🤝 贡献 | Contributing

欢迎提交 Issue 和 Pull Request。本项目致力于帮助学术写作者提升写作水平，请遵守学术诚信规范。

We welcome Issues and Pull Requests. This project is dedicated to helping academic writers improve their writing skills. Please adhere to academic integrity standards.

---

## ⚠️ 免责声明 | Disclaimer

**中文:**
本工具仅辅助优化文章语言风格，帮助作者理解和改进 AI 写作特征。最终内容的学术严谨性和原创性由作者本人负责。本工具不保证能 100% 通过所有 AIGC 检测器。请在遵守学术诚信规范的前提下使用本工具。

**English:**
This tool only assists in optimizing article language style and helps authors understand and improve AI writing characteristics. The academic rigor and originality of the final content are the responsibility of the author. This tool does not guarantee 100% passing of all AIGC detectors. Please use this tool in compliance with academic integrity standards.

---

<p align="center">
  Made with ❤️ for Academic Writing
</p>
