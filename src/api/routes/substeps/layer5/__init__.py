"""
Layer 5 (Document Level) Substep Routes
Layer 5（文档级）子步骤路由

Step 1.0: Term Locking (词汇锁定)
Step 1.1: Structure Framework Detection (结构框架检测)
Step 1.2: Paragraph Length Regularity (段落长度规律性)
Step 1.3: Progression & Closure Detection (推进模式与闭合检测)
Step 1.4: Connectors & Transitions (连接词与衔接)
Step 1.5: Content Substantiality (内容实质性)
"""

from fastapi import APIRouter

router = APIRouter()

# Import all step routers
# 导入所有步骤路由
from src.api.routes.substeps.layer5 import step1_0, step1_1, step1_2, step1_3, step1_4, step1_5

# Include step routes
# 包含步骤路由
router.include_router(step1_0.router, prefix="/step1-0", tags=["Step 1.0: Term Locking"])
router.include_router(step1_1.router, prefix="/step1-1", tags=["Step 1.1: Structure Framework"])
router.include_router(step1_2.router, prefix="/step1-2", tags=["Step 1.2: Section Uniformity"])
router.include_router(step1_3.router, prefix="/step1-3", tags=["Step 1.3: Logic Pattern"])
router.include_router(step1_4.router, prefix="/step1-4", tags=["Step 1.4: Paragraph Length"])
router.include_router(step1_5.router, prefix="/step1-5", tags=["Step 1.5: Transitions"])

__all__ = ["router"]
