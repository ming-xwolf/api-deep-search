"""本地模型提供商实现"""
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.services.factory.base import EmbeddingProvider, ModelFactory
from app.config.settings import settings

class LocalEmbeddingProvider(EmbeddingProvider):
    """本地嵌入模型提供者（基于HuggingFace模型）"""
    
    def __init__(self, model_name: str, embedding_dimension: int = 1024):
        """初始化本地嵌入提供者"""
        self.model_name = model_name
        self.embedding_dimension = embedding_dimension
        
        # 优先使用Langchain的HuggingFaceEmbeddings
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        except Exception:
            # 回退到直接使用SentenceTransformer
            self.model = SentenceTransformer(model_name)
    
    def get_embedding_value(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        try:
            # 尝试使用Langchain的嵌入模型
            if hasattr(self, 'embeddings'):
                return self.embeddings.embed_query(text)
            # 回退到SentenceTransformer
            return self.model.encode(text).tolist()
        except Exception as e:
            raise ValueError(f"嵌入文本时出错: {str(e)}")
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量的维度"""
        return self.embedding_dimension
    
    def get_provider_info(self) -> Dict[str, str]:
        """获取提供商信息"""
        return {
            "provider": "local",
            "model": self.model_name,
            "dimension": str(self.embedding_dimension)
        }

class LocalModelFactory(ModelFactory):
    """本地模型工厂"""
    
    @staticmethod
    def create_llm_provider(model_name: str, **kwargs) -> Any:
        """创建LLM提供者实例
        
        目前不支持本地LLM，返回None
        """
        return None
    
    @staticmethod
    def create_embedding_provider(model_name: str, **kwargs) -> EmbeddingProvider:
        """创建嵌入提供者实例"""
        embedding_dimension = kwargs.get("embedding_dimension", settings.embedding_dimension)
        
        return LocalEmbeddingProvider(
            model_name=model_name,
            embedding_dimension=embedding_dimension
        ) 