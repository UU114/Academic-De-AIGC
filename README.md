# AcademicGuard

**英文论文 AIGC 检测与人源化协作引擎**
**Academic Paper AIGC Detection & Human-AI Collaborative Humanization Engine**

> 🚀 **最新更新 (2026-01-04)**: 全新的三阶分析流程 (Three-Level Flow)、风格检测 (Style Analysis)、批量 AI 修改 (Merge Modify) 与语义回声 (Semantic Echo) 功能已上线！

---

## 📖 项目简介 | Introduction

AcademicGuard 是一套集"多维检测"与"人机协作改写"于一体的深度 De-AIGC 工具。不同于简单的同义词替换，我们采用**三阶分析架构 (Three-Level Analysis)**，从全文章节结构、段落逻辑关系到句子指纹特征，全方位降低被 Turnitin、GPTZero 等检测器误判的风险，同时显著提升文章的学术性与可读性。

**核心理念：AI 教你改，而非 AI 替你改**
**Core Philosophy: AI guides you to revise, not revise for you**

---

## 🌟 核心特性 | Key Features

### 🔄 全新三阶分析流程 (Three-Level Flow)

我们采用由宏观到微观的渐进式优化流程：

#### **Step 1-1: 结构分析 (Structure Analysis)**
- **全篇扫描**: 检测线性流程、重复模式、均句长度等 AI 典型特征。
- **风格检测**: 自动识别文章口语化等级 (0-10)，并与目标风格（如期刊论文级）对比，发出不匹配警告。
- **详细建议**: 提供分章节的具体修改建议（拆分、合并、补充内容等）。
- **批量修改**: 支持勾选多个问题，生成 AI 提示词或直接进行 AI 修改。

#### **Step 1-2: 关系分析 (Relationship Analysis)**
- **逻辑断层检测**: 识别段落间缺乏语义连接的断点。
- **显性连接词识别**: 捕捉 "Furthermore", "Moreover", "In conclusion" 等 AI 高频使用的连接词。
- **语义回声 (Semantic Echo)**: 自动提取上一段的核心概念，生成自然的承接句替代显性连接词。

#### **Step 2: 衔接优化 (Transition Optimization)**
- **深度衔接修复**: 专注于段落间的流畅过渡。
- **批量处理**: 整合 Step 1-2 的发现，支持批量生成优化的过渡句。
- **上下文保护**: 修改时自动保护前序步骤的优化成果。

#### **Step 3: 句子精修 (Sentence Polishing)**
- **指纹消除**: 识别并替换 40+ 高频 AI 指纹词和短语。
- **句式重组**: 打破公式化句型，增加句式多样性。
- **双轨建议**: 提供 LLM (智能改写) 和 Rule (规则替换) 两种建议。
- **干预/YOLO 模式**: 支持逐句精修（干预模式）或全自动处理（YOLO 模式）。

### 🛡️ 硬核 De-AIGC 技术

- **CAASS v2.0 评分系统**: 基于上下文感知的动态风险评分，结合 ONNX PPL (困惑度) 模型。
- **PPL 可视化**: 实时显示句子的困惑度，通过 Emoji (🤯/⚠️/🤖) 直观展示 AI 特征风险。
- **突发性 (Burstiness) 分析**: 检测句子长度和结构的单一性。
- **智能保护**: 自动锁定学术术语、统计数据 (p < 0.05) 和引用格式，防止被错误修改。

### 💡 智能协作功能

- **Merge Modify (合并修改)**: 在 Step 1 & 2 中，支持多选问题，一键生成针对性的 AI 修改提示词 (Prompt) 或直接应用修改。
- **Unified Task List (统一任务列表)**: 全新的历史记录页面，统一管理所有文档和会话，实时查看各阶段进度。
- **口语化程度控制**: 0-10 级可调，从"极度学术"到"日常口语"，全程贯穿分析与修改建议。

---

## 🛠️ 技术栈 | Tech Stack

| 层级 | 技术 |
|------|------|
| **后端** | FastAPI (Python 3.8+), SQLAlchemy (Async), SQLite |
| **前端** | React 18, TypeScript, Vite, Zustand, TailwindCSS |
| **AI/NLP** | ONNX (PPL Model), spaCy, Transformers |
| **LLM 集成** | Claude, OpenAI, Volcengine (豆包), DeepSeek, Gemini |
| **工具** | Git, PowerShell |

---

## 🚀 快速开始 | Quick Start

### 环境要求 | Requirements

- Python 3.8+
- Node.js 18+
- npm 或 yarn

### 安装 | Installation

```bash
# 1. 克隆项目
git clone <repository-url>
cd DEAI

# 2. 创建虚拟环境并安装后端依赖
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt

# 3. 安装前端依赖
cd frontend
npm install
cd ..
```

### 配置 | Configuration

1. 复制环境配置文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入至少一个 LLM 的 API Key：
   ```env
   # 推荐使用 Volcengine 或 DeepSeek 以获得高性价比
   VOLCENGINE_API_KEY=your_key
   VOLCENGINE_ENDPOINT_ID=your_endpoint_id
   
   # 或者
   OPENAI_API_KEY=your_key
   ANTHROPIC_API_KEY=your_key
   GEMINI_API_KEY=your_key
   ```

### 运行 | Run

**方式一：使用启动脚本（推荐）**

```bash
# Windows
scripts\dev.bat

# Linux/Mac
chmod +x scripts/dev.sh
./scripts/dev.sh
```

**方式二：手动启动**

```bash
# 终端 1 - 启动后端
venv\Scripts\activate  # Windows
uvicorn src.main:app --reload --port 8000

# 终端 2 - 启动前端
cd frontend
npm run dev
```

**访问地址：**
- 前端界面: http://localhost:5173
- API文档: http://localhost:8000/docs

---

## 📂 项目结构 | Project Structure

```
DEAI/
├── src/                    # FastAPI 后端源码
│   ├── api/                # API 路由与数据模型
│   │   ├── routes/         # 核心路由 (structure, suggest, session...)
│   │   └── schemas.py      # Pydantic 模型
│   ├── core/               # 核心业务逻辑
│   │   ├── analyzer/       # 分析器 (Structure, PPL, Fingerprint)
│   │   ├── suggester/      # 改写建议引擎
│   │   └── preprocessor/   # 预处理 (分句, 白名单)
│   ├── db/                 # 数据库模型 (SQLite)
│   └── prompts/            # LLM 提示词模板 (De-AIGC 核心知识库)
├── frontend/               # React 前端源码
│   ├── src/
│   │   ├── components/     # UI 组件 (RiskCard, StructurePanel...)
│   │   ├── pages/          # 页面 (Step1_1, Step1_2, Step2, Step3...)
│   │   ├── services/       # API 客户端
│   │   └── stores/         # Zustand 状态管理
│   └── ...
├── data/                   # 数据资源
│   ├── fingerprints/       # AI 指纹词库
│   └── terms/              # 术语白名单
└── doc/                    # 开发文档
```

---

## 📝 许可证 | License

MIT License

---

## 🤝 贡献 | Contributing

欢迎提交 Issue 和 Pull Request。本项目致力于帮助学术写作者提升写作水平，请遵守学术诚信规范。

> **免责声明**: 本工具仅辅助优化文章语言风格，不保证能 100% 通过所有 AIGC 检测器。最终内容的学术严谨性由作者本人负责。