from typing import List, Dict, Any, Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config.settings import settings

class QdrantVectorService:
    """Qdrant向量数据库服务，处理底层向量操作"""
    
    def __init__(self):
        """初始化Qdrant客户端"""
        self.url = settings.qdrant_url
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.qdrant_collection_name
    
    def ensure_collection_exists(self, vector_size: int):
        """确保向量集合存在
        
        Args:
            vector_size: 向量维度
        """
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
    
    def upsert_points(self, points: List[models.PointStruct]):
        """批量插入或更新点
        
        Args:
            points: 要插入的点列表
        """
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
    
    def search(self, 
               query_vector: List[float], 
               limit: int = 5, 
               query_filter: Optional[models.Filter] = None) -> List[Dict[str, Any]]:
        """搜索向量
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量限制
            query_filter: 过滤条件
            
        Returns:
            搜索结果
        """
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter
        )
    
    def delete_collection(self) -> bool:
        """删除集合
        
        Returns:
            bool: 操作是否成功
        """
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            return True
        except Exception as e:
            print(f"删除集合时出错: {str(e)}")
            return False
    
    def get_collection_info(self):
        """获取集合信息"""
        return self.client.get_collection(self.collection_name)
    
    def scroll(self, 
               limit: int, 
               scroll_filter: Optional[models.Filter] = None,
               with_payload: bool = True,
               with_vectors: bool = False,
               payload_fields: Optional[List[str]] = None):
        """滚动查询集合中的点
        
        Args:
            limit: 返回结果数量限制
            scroll_filter: 过滤条件
            with_payload: 是否返回payload
            with_vectors: 是否返回向量
            payload_fields: 要返回的payload字段
            
        Returns:
            查询结果
        """
        payload_param = True
        if payload_fields:
            payload_param = payload_fields
            
        return self.client.scroll(
            collection_name=self.collection_name,
            limit=limit,
            filter=scroll_filter,
            with_payload=payload_param,
            with_vectors=with_vectors
        )
    
    def delete_points(self, point_ids: List[str]) -> bool:
        """删除指定ID的点
        
        Args:
            point_ids: 要删除的点ID列表
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if not point_ids:
                return True
                
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=point_ids
                )
            )
            return True
        except Exception as e:
            print(f"删除点时出错: {str(e)}")
            return False 