# AcademicGuard

**英文论文 AIGC 检测与人源化协作引擎**
**Academic Paper AIGC Detection & Human-AI Collaborative Humanization Engine**

---

## 项目简介 | Introduction

AcademicGuard 是一套集"多维检测"与"人机协作改写"于一体的工具，帮助学术论文作者识别和修改可能被AIGC检测器（如Turnitin、GPTZero）标记的内容，同时保留学术专业性。

AcademicGuard is a tool that combines "multi-dimensional detection" with "human-AI collaborative rewriting" to help academic paper authors identify and modify content that may be flagged by AIGC detectors (such as Turnitin, GPTZero) while preserving academic professionalism.

**核心理念：AI教你改，而非AI替你改**
**Core Philosophy: AI guides you to revise, not revise for you**

---

## 功能特性 | Features

### 双模式设计 | Dual Mode Design

- **YOLO模式**: 自动处理，最后审核，适合时间紧迫场景
- **干预模式**: 逐句控制，精细修改，适合重要论文

### 双轨建议系统 | Dual-track Suggestion System

- **轨道A (LLM)**: 基于Claude/GPT-4的智能改写建议
- **轨道B (规则)**: 基于同义词替换与句法重组的确定性建议
- **轨道C (自定义)**: 用户自行修改，通过语义验证后应用

### 多维度检测 | Multi-dimensional Detection

- 困惑度(PPL)分析
- AI指纹词检测 (40+ 高频词，20+ 偏好短语)
- 突发性(Burstiness)分析
- 结构模式分析
- Turnitin/GPTZero双视角

### 智能保护 | Intelligent Protection

- 学术术语自动锁定
- 统计数据保护 (p < 0.05, R² = 0.89)
- 引用格式保护

### 口语化程度控制 | Colloquialism Level Control

- 0-10级可调
- 从"期刊论文级"到"口语讨论级"
- 影响词汇选择和句式风格
- 推荐设置：期刊(1)、论文(4)、作业(5)、会议(6)

### 多语言支持 | Multi-language Support

- 中文解释和说明
- 支持日语、韩语、西班牙语 (计划中)

---

## 技术栈 | Tech Stack

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI (Python 3.8+) |
| 前端 | React 18 + TypeScript + Vite |
| 样式 | TailwindCSS |
| 状态管理 | Zustand |
| NLP | spaCy, Stanza, Transformers |
| LLM | Claude API, OpenAI API |
| 数据库 | SQLite (MVP) / PostgreSQL |

---

## 快速开始 | Quick Start

### 环境要求 | Requirements

- Python 3.8+
- Node.js 18+
- npm 或 yarn

### 安装 | Installation

```bash
# 克隆项目
git clone <repository-url>
cd DEAI

# 创建虚拟环境并安装后端依赖
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 配置 | Configuration

复制环境配置文件并填写API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# LLM API Keys (至少需要一个)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Application
DEBUG=true
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
# 终端1 - 启动后端
venv\Scripts\activate  # Windows
uvicorn src.main:app --reload --port 8000

# 终端2 - 启动前端
cd frontend
npm run dev
```

**访问地址：**
- 前端界面: http://localhost:5173
- API文档: http://localhost:8000/docs

---

## 项目结构 | Project Structure

```
DEAI/
├── doc/                    # 文档
│   ├── plan.md            # 开发计划
│   ├── structure.md       # 技术架构
│   └── process.md         # 开发进度
├── src/                    # 后端源码
│   ├── api/               # API路由
│   │   ├── routes/        # 路由模块
│   │   └── schemas.py     # 数据模式
│   ├── core/              # 核心业务逻辑
│   │   ├── preprocessor/  # 预处理 (分句、术语锁定)
│   │   ├── analyzer/      # 分析 (指纹词、风险评分)
│   │   ├── suggester/     # 建议 (LLM轨道、规则轨道)
│   │   └── validator/     # 验证 (语义相似度、质量门控)
│   ├── db/                # 数据库模型
│   └── services/          # 服务层
├── data/                   # 数据资源
│   ├── fingerprints/      # 指纹词库 (40+词, 20+短语)
│   └── terms/             # 术语白名单 (按学科分类)
├── frontend/              # 前端源码
│   ├── src/
│   │   ├── components/    # UI组件
│   │   │   ├── common/    # 通用组件
│   │   │   ├── editor/    # 编辑器组件
│   │   │   └── settings/  # 设置组件
│   │   ├── pages/         # 页面组件
│   │   ├── stores/        # 状态管理
│   │   ├── services/      # API服务
│   │   └── types/         # TypeScript类型
│   └── ...
├── scripts/               # 启动脚本
│   ├── dev.bat           # Windows开发启动
│   └── dev.sh            # Unix开发启动
└── tests/                 # 测试
```

---

## 页面功能 | Page Features

| 页面 | 功能说明 |
|------|---------|
| 首页 | 产品介绍、特性展示、快速入口 |
| 上传页 | 文件上传/文本粘贴、处理模式选择、口语化程度设置 |
| 干预模式 | 逐句分析、双轨建议展示、自定义修改、实时验证 |
| YOLO模式 | 自动处理进度、实时日志、暂停/继续控制 |
| 结果审核 | 风险对比统计、修改记录、文档/报告导出 |

---

## API 端点 | API Endpoints

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/v1/documents/upload` | POST | 上传文档 |
| `/api/v1/analyze` | POST | 分析文本AIGC风险 |
| `/api/v1/suggest` | POST | 获取改写建议 |
| `/api/v1/session/start` | POST | 开始处理会话 |
| `/api/v1/session/{id}/current` | GET | 获取当前句子 |
| `/api/v1/session/{id}/next` | POST | 处理下一句 |
| `/api/v1/session/{id}/skip` | POST | 跳过当前句子 |
| `/api/v1/export/document` | POST | 导出处理结果 |
| `/api/v1/export/report` | POST | 导出分析报告 |

完整API文档请访问: `http://localhost:8000/docs`

---

## 开发状态 | Development Status

- [x] Phase 1: MVP核心闭环 (98%)
  - [x] 后端核心模块
  - [x] 前端UI组件
  - [x] API路由框架
  - [ ] 端到端集成测试
- [ ] Phase 2: 双轨完善
- [ ] Phase 3: 多语言与体验优化
- [ ] Phase 4: 测试与部署

---

## 许可证 | License

MIT License

---

## 贡献 | Contributing

欢迎提交Issue和Pull Request。

---

> 本项目仅供学术研究和学习使用，请遵守学术诚信规范。
> This project is for academic research and learning purposes only. Please follow academic integrity guidelines.
