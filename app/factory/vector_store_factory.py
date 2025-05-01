from typing import List, Dict, Any, Optional, Union, Tuple, Literal
from abc import ABC, abstractmethod
import os
import json
from pathlib import Path

# Qdrant相关导入
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, PointIdsList

# FAISS相关导入
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config.settings import settings
from app.factory.embedding_factory import EmbeddingFactory

class VectorStore(ABC):
    """通用向量存储接口"""
    
    @abstractmethod
    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
        """添加文本到向量存储
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表
        """
        pass
    
    @abstractmethod
    def similarity_search(self, query: str, k: int = 5, filter: Optional[Any] = None) -> List[Any]:
        """相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter: 过滤条件
            
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    def as_retriever(self) -> Any:
        """获取检索器
        
        Returns:
            检索器实例
        """
        pass
    
    @abstractmethod
    def clean(self) -> bool:
        """清理向量存储
        
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def delete_by_file_path(self, file_path: str) -> int:
        """根据文件路径删除文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 删除的文档数量
        """
        pass

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

class FAISSStore(VectorStore):
    """FAISS 向量存储实现"""
    
    def __init__(self):
        """初始化 FAISS 存储"""
        self.index_dir = settings.faiss_index_dir
        self.embedding_func = EmbeddingFactory.create_embedding()
        
        # 确保目录存在
        os.makedirs(self.index_dir, exist_ok=True)
        
        # 尝试加载现有索引或创建新索引
        self.vector_store = self._load_or_create_index()
        
        # 存储元数据的文件路径
        self.metadata_file = os.path.join(self.index_dir, "metadata.json")
        
        # 加载元数据
        self.metadata_map = self._load_metadata()
    
    def _load_or_create_index(self) -> FAISS:
        """加载或创建FAISS索引"""
        index_path = Path(self.index_dir)
        if (index_path / "index.faiss").exists() and (index_path / "index.pkl").exists():
            try:
                return FAISS.load_local(
                    folder_path=self.index_dir,
                    embeddings=self.embedding_func,
                    index_name="index",
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"加载FAISS索引失败: {str(e)}，将创建新索引")
                
        # 创建新索引
        return FAISS.from_texts(
            texts=["初始化索引"],  # 需要至少一个文档初始化
            embedding=self.embedding_func,
            metadatas=[{"init": True}]
        )
    
    def _save_index(self):
        """保存FAISS索引"""
        self.vector_store.save_local(self.index_dir, index_name="index")
    
    def _load_metadata(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载元数据"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载元数据失败: {str(e)}")
        
        return {}
    
    def _save_metadata(self):
        """保存元数据"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata_map, f, ensure_ascii=False, indent=2)
    
    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
        """添加文本到向量存储"""
        # 添加到FAISS索引
        self.vector_store.add_texts(texts=texts, metadatas=metadatas)
        
        # 更新元数据映射
        for metadata in metadatas:
            file_path = metadata.get("file_path")
            if file_path:
                if file_path not in self.metadata_map:
                    self.metadata_map[file_path] = []
                self.metadata_map[file_path].append(metadata)
        
        # 保存索引和元数据
        self._save_index()
        self._save_metadata()
    
    def similarity_search(self, query: str, k: int = 5, filter: Optional[Any] = None) -> List[Any]:
        """相似度搜索"""
        # FAISS没有原生的过滤功能，我们需要进行后处理
        if filter is None:
            return self.vector_store.similarity_search(query=query, k=k)
        
        # 对于OpenAPI版本过滤，获取更多结果然后手动过滤
        results = self.vector_store.similarity_search(query=query, k=k*3)  # 获取更多结果以便过滤
        
        # 手动过滤
        filtered_results = []
        for doc in results:
            if self._matches_filter(doc.metadata, filter):
                filtered_results.append(doc)
                if len(filtered_results) >= k:
                    break
        
        return filtered_results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter: Any) -> bool:
        """检查元数据是否匹配过滤条件"""
        # 处理Qdrant风格的过滤器
        if hasattr(filter, 'must') and filter.must:
            for condition in filter.must:
                if hasattr(condition, 'key') and hasattr(condition, 'match'):
                    key = condition.key
                    value = condition.match.value
                    if metadata.get(key) != value:
                        return False
            return True
        return False
    
    def as_retriever(self) -> Any:
        """获取检索器"""
        return self.vector_store.as_retriever()
    
    def clean(self) -> bool:
        """清理向量存储"""
        try:
            # 创建空索引
            self.vector_store = FAISS.from_texts(
                texts=["初始化索引"],
                embedding=self.embedding_func,
                metadatas=[{"init": True}]
            )
            
            # 保存空索引
            self._save_index()
            
            # 清空元数据
            self.metadata_map = {}
            self._save_metadata()
            
            return True
        except Exception as e:
            print(f"清理FAISS索引时出错: {str(e)}")
            return False
    
    def delete_by_file_path(self, file_path: str) -> int:
        """根据文件路径删除文档
        注意：FAISS不支持直接删除，需要重建索引
        """
        try:
            # 检查文件路径是否在元数据映射中
            if file_path not in self.metadata_map:
                return 0
            
            # 获取要删除的文档数量
            count = len(self.metadata_map[file_path])
            
            # 从元数据映射中删除
            del self.metadata_map[file_path]
            
            # 重建索引
            documents = []
            for file_docs in self.metadata_map.values():
                for metadata in file_docs:
                    # 从原始索引中检索文本内容
                    # 注意：这里有一个限制，因为FAISS不存储原始文本
                    # 我们使用元数据中的信息重建文档
                    documents.append(
                        Document(
                            page_content=metadata.get("text", ""),
                            metadata=metadata
                        )
                    )
            
            if documents:
                # 创建新索引
                self.vector_store = FAISS.from_documents(
                    documents=documents,
                    embedding=self.embedding_func
                )
                self._save_index()
            else:
                # 如果没有文档，创建空索引
                self.clean()
            
            # 保存更新后的元数据
            self._save_metadata()
            
            return count
        except Exception as e:
            print(f"从FAISS删除文档时出错: {str(e)}")
            return 0

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