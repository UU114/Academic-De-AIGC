"""
Layer 3 (Paragraph Level) Substep Routes
Layer 3（段落级）子步骤路由

Step 3.0: Paragraph Identification (段落识别)
Step 3.1: Paragraph Role Detection (段落角色识别)
Step 3.2: Internal Coherence Analysis (内部连贯性)
Step 3.3: Anchor Density Analysis (锚点密度)
Step 3.4: Sentence Length Distribution (句长分布)
Step 3.5: Paragraph Transition Analysis (段落过渡)
"""

from fastapi import APIRouter

router = APIRouter()

# Import all step routers
from src.api.routes.substeps.layer3 import step3_0, step3_1, step3_2, step3_3, step3_4, step3_5

# Include step routes
router.include_router(step3_0.router, prefix="/step3-0", tags=["Step 3.0: Paragraph Identification"])
router.include_router(step3_1.router, prefix="/step3-1", tags=["Step 3.1: Paragraph Role"])
router.include_router(step3_2.router, prefix="/step3-2", tags=["Step 3.2: Internal Coherence"])
router.include_router(step3_3.router, prefix="/step3-3", tags=["Step 3.3: Anchor Density"])
router.include_router(step3_4.router, prefix="/step3-4", tags=["Step 3.4: Sentence Length"])
router.include_router(step3_5.router, prefix="/step3-5", tags=["Step 3.5: Paragraph Transition"])

__all__ = ["router"]
