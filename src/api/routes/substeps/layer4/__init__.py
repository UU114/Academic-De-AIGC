"""
Layer 4 (Section Level) Substep Routes
Layer 4（章节级）子步骤路由

Step 2.0: Section Identification (章节识别)
Step 2.1: Section Order & Structure (章节顺序与结构)
Step 2.2: Section Length Distribution (章节长度分布)
Step 2.3: Internal Structure Similarity (内部结构相似性)
Step 2.4: Section Transition (章节衔接)
Step 2.5: Inter-Section Logic (章节间逻辑)
"""

from fastapi import APIRouter

router = APIRouter()

# Import all step routers
from src.api.routes.substeps.layer4 import step2_0, step2_1, step2_2, step2_3, step2_4, step2_5

# Include step routes
router.include_router(step2_0.router, prefix="/step2-0", tags=["Step 2.0: Section Identification"])
router.include_router(step2_1.router, prefix="/step2-1", tags=["Step 2.1: Section Order"])
router.include_router(step2_2.router, prefix="/step2-2", tags=["Step 2.2: Section Length"])
router.include_router(step2_3.router, prefix="/step2-3", tags=["Step 2.3: Internal Similarity"])
router.include_router(step2_4.router, prefix="/step2-4", tags=["Step 2.4: Section Transition"])
router.include_router(step2_5.router, prefix="/step2-5", tags=["Step 2.5: Inter-Section Logic"])

__all__ = ["router"]
