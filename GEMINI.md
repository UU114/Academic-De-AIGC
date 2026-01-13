# AcademicGuard (DEAI) Context for Gemini

This file provides essential context for the Gemini agent interacting with the AcademicGuard (DEAI) project.

## 1. Project Overview

**Project Name:** AcademicGuard (Internal Code: DEAI)
**Purpose:** An academic paper AIGC detection and human-AI collaborative humanization engine. It aims to help authors identify AI-generated content patterns and guide them in rewriting for academic professionalism, rather than just "hiding" from detectors.
**Core Philosophy:** "AI teaches you to rewrite, not rewrite for you."

### Key Features
*   **Three-Level Analysis:** Structure (Macro) -> Transition (Meso) -> Sentence (Micro).
*   **De-AIGC Tech:** CAASS v2.0 Scoring, ONNX PPL calculation, Burstiness detection, Semantic Echo.
*   **Dual-Track Suggestions:** Track A (LLM-based) and Track B (Rule-based).
*   **Dual Modes:** Intervention (Step-by-step control) and YOLO (Auto-processing).
*   **Style Control:** 0-10 Colloquialism levels.

## 2. Tech Stack & Architecture

### Backend
*   **Language:** Python 3.10+
*   **Framework:** FastAPI
*   **Server:** Uvicorn
*   **Database:** SQLite (Dev) / PostgreSQL (Prod), accessed via SQLAlchemy (Async) & aiosqlite/asyncpg.
*   **Migrations:** Alembic
*   **ML/NLP:** spaCy, Stanza, PyTorch, Transformers, ONNX Runtime, Sentence-Transformers.
*   **LLM Integration:** Volcengine (DeepSeek), Anthropic, OpenAI, Google Gemini.

### Frontend
*   **Framework:** React 18
*   **Language:** TypeScript 5.2+
*   **Build Tool:** Vite 5.0+
*   **Styling:** TailwindCSS 3.3+
*   **State Management:** Zustand
*   **HTTP Client:** Axios

### Infrastructure
*   **Containerization:** Docker & Docker Compose
*   **Cache:** Redis (configured in settings)

## 3. Directory Structure

*   `src/`: Backend source code.
    *   `main.py`: Application entry point.
    *   `config.py`: Configuration and environment variable management.
    *   `api/`: API routes (`analyze`, `suggest`, `documents`, etc.).
    *   `core/`: Core logic (`analyzer`, `suggester`, `validator`, `preprocessor`).
    *   `db/`: Database models and connection logic.
*   `frontend/`: React frontend application.
*   `data/`: Static data resources (fingerprints, term whitelists).
*   `models/`: Local ML models (ONNX, spaCy, Stanza).
*   `doc/`: Comprehensive project documentation.
*   `alembic/`: Database migration scripts.

## 4. Development Workflow & Commands

### Backend
*   **Environment:** Python 3.10+ virtual environment recommended.
*   **Install Dependencies:** `pip install -r requirements.txt`
*   **Run Server (Dev):** `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`
*   **Initialize Database:** `python -c "from src.db.database import init_db; import asyncio; asyncio.run(init_db())"`
*   **Download Models:** See `scripts/init_models.py` (or manual `spacy download`, etc.).

### Frontend
*   **Directory:** `cd frontend`
*   **Install Dependencies:** `npm install`
*   **Run Server (Dev):** `npm run dev` (Runs on port 5173 by default)
*   **Build:** `npm run build`

### Database Management
*   **Migrations:** `alembic upgrade head` (Check `alembic.ini` configuration).

### Docker
*   **Start All:** `docker-compose up -d`
*   **Logs:** `docker-compose logs -f`

## 5. Configuration (Env Vars)

Key environment variables (managed in `.env`, loaded via `src/config.py`):

*   `SYSTEM_MODE`: `debug` (default) or `operational`.
*   `DATABASE_URL`: Connection string.
*   `LLM_PROVIDER`: `volcengine` (default), `anthropic`, `openai`, `gemini`, `deepseek`.
*   `VOLCENGINE_API_KEY`, `ANTHROPIC_API_KEY`, etc.: API keys for LLMs.
*   `RISK_WEIGHT_*`: Weights for scoring (Structure is prioritized).

## 6. Coding Conventions

*   **Style:** Adhere to PEP 8 for Python and standard TypeScript/React conventions.
*   **Type Hinting:** Extensive use of Python type hints and Pydantic models.
*   **Comments:** Bilingual comments (English/Chinese) are prevalent in the codebase. Maintain this style if modifying existing files.
*   **Error Handling:** Use FastAPI's exception handling and standardized API responses.

## 7. Operational Modes

*   **Debug Mode:** No login/payment required.
*   **Operational Mode:** Requires user authentication and payment integration (Central Platform).
