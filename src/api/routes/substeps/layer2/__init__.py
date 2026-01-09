"""
Layer 2 (Sentence Level) Substep Routes
Layer 2（句子级）子步骤路由

Step 4.0: Sentence Identification (句子识别)
Step 4.1: Sentence Pattern Analysis (句式分析)
Step 4.2: Sentence Length Analysis (句长分析)
Step 4.3: Sentence Merger Suggestions (合并建议)
Step 4.4: Connector Optimization (连接词优化)
Step 4.5: Pattern Diversification (句式多样化)
"""

from fastapi import APIRouter

router = APIRouter()

# Import all step routers
from src.api.routes.substeps.layer2 import step4_0, step4_1, step4_2, step4_3, step4_4, step4_5

# Include step routes
router.include_router(step4_0.router, prefix="/step4-0", tags=["Step 4.0: Sentence Identification"])
router.include_router(step4_1.router, prefix="/step4-1", tags=["Step 4.1: Sentence Pattern"])
router.include_router(step4_2.router, prefix="/step4-2", tags=["Step 4.2: Sentence Length"])
router.include_router(step4_3.router, prefix="/step4-3", tags=["Step 4.3: Sentence Merger"])
router.include_router(step4_4.router, prefix="/step4-4", tags=["Step 4.4: Connector Optimization"])
router.include_router(step4_5.router, prefix="/step4-5", tags=["Step 4.5: Pattern Diversification"])

__all__ = ["router"]
