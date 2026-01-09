"""
Substep API Routes
Substep API路由

Organized by layer:
按层组织：
- Layer 5 (Document): /api/v1/layer5/step1-x/...
- Layer 4 (Section): /api/v1/layer4/step2-x/...
- Layer 3 (Paragraph): /api/v1/layer3/step3-x/...
- Layer 2 (Sentence): /api/v1/layer2/step4-x/...
- Layer 1 (Lexical): /api/v1/layer1/step5-x/...
"""

from fastapi import APIRouter

# Create main router for substeps
# 创建substeps主路由
router = APIRouter()

# Import layer routers
# 导入层级路由
from src.api.routes.substeps import layer5, layer4, layer3, layer2, layer1

# Include all layer routes
# 包含所有层级路由
router.include_router(layer5.router, prefix="/layer5", tags=["Layer 5: Document"])
router.include_router(layer4.router, prefix="/layer4", tags=["Layer 4: Section"])
router.include_router(layer3.router, prefix="/layer3", tags=["Layer 3: Paragraph"])
router.include_router(layer2.router, prefix="/layer2", tags=["Layer 2: Sentence"])
router.include_router(layer1.router, prefix="/layer1", tags=["Layer 1: Lexical"])

__all__ = ["router"]
