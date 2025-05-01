from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

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