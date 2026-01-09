"""
Layer 1 (Lexical Level) Substep Routes
Layer 1（词汇级）子步骤路由

Step 5.0: Lexical Context Preparation (词汇环境准备)
Step 5.1: AIGC Fingerprint Detection (AIGC指纹检测)
Step 5.2: Human Feature Analysis (人类特征分析)
Step 5.3: Replacement Generation (替换候选生成)
Step 5.4: Paragraph Rewriting (段落改写)
Step 5.5: Rewrite Validation (改写验证)
"""

from fastapi import APIRouter

router = APIRouter()

# Import all step routers
from src.api.routes.substeps.layer1 import step5_0, step5_1, step5_2, step5_3, step5_4, step5_5

# Include step routes
router.include_router(step5_0.router, prefix="/step5-0", tags=["Step 5.0: Lexical Context"])
router.include_router(step5_1.router, prefix="/step5-1", tags=["Step 5.1: Fingerprint Detection"])
router.include_router(step5_2.router, prefix="/step5-2", tags=["Step 5.2: Human Features"])
router.include_router(step5_3.router, prefix="/step5-3", tags=["Step 5.3: Replacement Generation"])
router.include_router(step5_4.router, prefix="/step5-4", tags=["Step 5.4: Paragraph Rewriting"])
router.include_router(step5_5.router, prefix="/step5-5", tags=["Step 5.5: Validation"])

__all__ = ["router"]
