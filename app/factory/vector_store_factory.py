from typing import Dict, Any, Optional
from app.config.settings import settings
from app.factory.vector_store_base import VectorStore
from app.factory.qdrant_store import QdrantStore
from app.factory.faiss_store import FAISSStore

class VectorStoreFactory:
    """向量存储工厂类"""
    
    @staticmethod
    def create_vector_store(provider: Optional[str] = None) -> VectorStore:
        """创建向量存储实例
        
        Args:
            provider: 向量存储提供商，如果为 None，则使用配置中的默认值
            
        Returns:
            VectorStore: 向量存储实例
        """
        # 默认使用配置中的提供商
        provider = provider or settings.vector_store_provider
        
        if provider.lower() == "qdrant":
            return QdrantStore()
        elif provider.lower() == "faiss":
            return FAISSStore()
        else:
            raise ValueError(f"不支持的向量存储提供商: {provider}")
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        """获取向量存储配置信息
        
        Returns:
            Dict[str, Any]: 配置信息
        """
        provider = settings.vector_store_provider
        
        info = {
            "provider": provider,
            "embedding_dimension": settings.embedding_dimension
        }
        
        if provider == "qdrant":
            info.update({
                "url": settings.qdrant_url,
                "collection_name": settings.qdrant_collection_name
            })
        elif provider == "faiss":
            info.update({
                "index_dir": settings.faiss_index_dir
            })
        
        return info 