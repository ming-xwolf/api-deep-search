from typing import List, Dict, Any

from app.config.settings import settings
from app.models.schema import APIEndpoint
from app.services.factory.model_factory import ModelFactoryCreator
from app.services.factory.base import BaseLLMProvider

class LLMService:
    """大模型服务"""
    
    def __init__(self):
        """初始化LLM服务"""
        self.provider = self._create_provider()
        self.model = settings.llm_model
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens
        self.llm_provider_type = settings.llm_provider
        
    def _create_provider(self) -> BaseLLMProvider:
        """创建LLM提供者实例"""
        return ModelFactoryCreator.get_llm_provider()
    
    def generate_answer(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """生成查询答案"""
        # 使用LLM提供者生成回答
        return self.provider.generate_answer(query, search_results)
    
    def get_info(self) -> Dict[str, str]:
        """获取LLM信息"""
        return self.provider.get_provider_info()