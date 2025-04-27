from typing import List, Dict

from app.config.settings import settings
from app.services.factory.model_factory import ModelFactoryCreator
from app.services.factory.base import EmbeddingProvider

class EmbeddingService:
    """嵌入服务，负责生成文本的向量表示"""
    
    def __init__(self):
        """初始化嵌入服务"""
        self.embedding_provider_type = settings.embedding_provider
        self.provider = self._create_provider()
    
    def _create_provider(self) -> EmbeddingProvider:
        """创建嵌入提供者实例"""
        return ModelFactoryCreator.get_embedding_provider()
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量的维度"""
        return self.provider.get_embedding_dimension()
    
    def get_embedding_value(self, text: str) -> List[float]:
        """获取文本嵌入向量
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            文本的嵌入向量
        """
        return self.provider.get_embedding_value(text)
    
    def get_info(self) -> Dict[str, str]:
        """获取嵌入服务信息"""
        return self.provider.get_provider_info() 