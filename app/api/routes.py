from fastapi import APIRouter
from typing import Dict, Any

from app.factory.llm_factory import LLMFactory
from app.factory.embedding_factory import EmbeddingFactory
from app.factory.vector_store_factory import VectorStoreFactory
from app.api.oas_routes import router as oas_router
from app.api.api_detector_routes import router as api_detector_router

# 创建主路由器
router = APIRouter(prefix="/api", tags=["API"])

# 添加子路由器
router.include_router(oas_router)
router.include_router(api_detector_router)

@router.get("/info")
def get_info() -> Dict[str, Any]:
    """获取系统配置信息"""
    return {
        "llm": LLMFactory.get_info(),
        "embedding": EmbeddingFactory.get_info(),
        "vector_store": VectorStoreFactory.get_info()
    }

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


