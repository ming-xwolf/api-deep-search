from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config.settings import settings
from app.factory.embedding_factory import EmbeddingFactory

class VectorStoreFactory:
    """向量存储工厂类"""
    
    @staticmethod
    def create_vector_store() -> Qdrant:
        """创建向量存储实例
        
        Returns:
            Qdrant: 向量存储实例
        """
        # 创建 Qdrant 客户端
        client = QdrantClient(url=settings.qdrant_url)
        collection_name = settings.qdrant_collection_name
        
        # 确保集合存在
        VectorStoreFactory._ensure_collection_exists(client, collection_name)
        
        # 创建向量存储实例
        return Qdrant(
            client=client,
            collection_name=collection_name,
            embeddings=EmbeddingFactory.create_embedding()
        )
    
    @staticmethod
    def _ensure_collection_exists(client: QdrantClient, collection_name: str):
        """确保 Qdrant 集合存在
        
        Args:
            client: Qdrant 客户端
            collection_name: 集合名称
        """
        collections = client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if collection_name not in collection_names:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=settings.embedding_dimension,
                    distance=models.Distance.COSINE
                )
            )
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        """获取向量存储配置信息
        
        Returns:
            Dict[str, Any]: 配置信息
        """
        return {
            "provider": "qdrant",
            "url": settings.qdrant_url,
            "collection_name": settings.qdrant_collection_name,
            "embedding_dimension": settings.embedding_dimension
        } 