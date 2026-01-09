"""
5-Layer Analysis API Routes
5层分析API路由

Step 1.0: Term Lock (词汇锁定) - /api/v1/analysis/term-lock
Layer 5: Document (文章层) - /api/v1/analysis/document
Layer 4: Section (章节层) - /api/v1/analysis/section
Layer 3: Paragraph (段落层) - /api/v1/analysis/paragraph
Layer 2: Sentence (句子层) - /api/v1/analysis/sentence
Layer 1: Lexical (词汇层) - /api/v1/analysis/lexical

Plus: Pipeline (全流水线) - /api/v1/analysis/pipeline
"""

from fastapi import APIRouter

# Create main router for analysis module
# 创建分析模块的主路由
router = APIRouter()

# Import sub-routers
# 导入子路由
from src.api.routes.analysis import document, section, paragraph, sentence, lexical, pipeline, term_lock
from src.api.routes.analysis import lexical_v2  # Layer 1 Enhanced

# Include all layer routes
# 包含所有层路由
# Step 1.0: Term Locking (must be first in workflow)
router.include_router(term_lock.router, prefix="/term-lock", tags=["Step 1.0: Term Lock"])
router.include_router(document.router, prefix="/document", tags=["Layer 5: Document"])
router.include_router(section.router, prefix="/section", tags=["Layer 4: Section"])
router.include_router(paragraph.router, prefix="/paragraph", tags=["Layer 3: Paragraph"])
router.include_router(sentence.router, prefix="/sentence", tags=["Layer 2: Sentence"])
router.include_router(lexical.router, prefix="/lexical", tags=["Layer 1: Lexical"])
router.include_router(lexical_v2.router, prefix="/lexical-v2", tags=["Layer 1: Lexical (Enhanced)"])
router.include_router(pipeline.router, prefix="/pipeline", tags=["Pipeline"])

__all__ = ["router"]
