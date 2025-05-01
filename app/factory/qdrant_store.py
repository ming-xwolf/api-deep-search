from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, PointIdsList
from langchain_qdrant import QdrantVectorStore

from app.config.settings import settings
from app.factory.embedding_factory import EmbeddingFactory
from app.factory.vector_store_base import VectorStore

class QdrantStore(VectorStore):
    """Qdrant 向量存储包装类"""
    
    def __init__(self):
        """初始化"""
        self.client = self._create_client()
        self.collection_name = settings.qdrant_collection_name
        self.embedding_function = EmbeddingFactory.create_embedding_function()
        
        # 确保集合存在
        self._ensure_collection()
        
        # 创建向量存储
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embedding_function
        )
    
    def _create_client(self):
        """创建QdrantClient实例"""
        return QdrantClient(url=settings.qdrant_url)
    
    def _ensure_collection(self):
        """确保Qdrant集合存在"""
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=settings.embedding_dimension,
                    distance=models.Distance.COSINE
                )
            )
    
    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
        """添加文本到向量存储"""
        self.vector_store.add_texts(texts=texts, metadatas=metadatas)
    
    def similarity_search(self, query: str, k: int = 5, filter: Optional[Any] = None) -> List[Any]:
        """相似度搜索"""
        return self.vector_store.similarity_search(query=query, k=k, filter=filter)
    
    def as_retriever(self) -> Any:
        """获取检索器"""
        return self.vector_store.as_retriever()
    
    def clean(self) -> bool:
        """清理向量存储"""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            self._ensure_collection()
            return True
        except Exception as e:
            print(f"清理集合时出错: {str(e)}")
            return False
    
    def delete_by_file_path(self, file_path: str) -> int:
        """根据文件路径删除文档"""
        try:
            # 获取所有点
            points = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="file_path",
                            match=MatchValue(value=file_path)
                        )
                    ]
                )
            )[0]
            
            if not points:
                return 0
                
            # 删除点
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(
                    points=[point.id for point in points]
                )
            )
            
            return len(points)
        except Exception as e:
            print(f"删除文档时出错: {str(e)}")
            return 0 