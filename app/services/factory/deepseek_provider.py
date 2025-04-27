"""DeepSeek模型提供商实现"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI

from app.services.factory.base import BaseLLMProvider, EmbeddingProvider, ModelFactory
from app.config.settings import settings

class DeepseekLLMProvider(BaseLLMProvider):
    """DeepSeek大语言模型提供者"""
    
    def __init__(self, model_name: str, api_key: str, base_url: str, temperature: float = 0.3, max_tokens: int = 1000):
        """初始化DeepSeek模型提供者"""
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url
        
        # 使用OpenAI兼容接口创建ChatOpenAI实例
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            openai_api_base=base_url
        )
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用LLM获取回答"""
        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 调用LLM
        response = self.llm.invoke(messages)
        
        return response.content
    
    def get_provider_info(self) -> Dict[str, str]:
        """获取提供商信息"""
        return {
            "provider": "deepseek",
            "model": self.model_name,
            "temperature": str(self.temperature),
            "max_tokens": str(self.max_tokens),
            "base_url": self.base_url
        }

class DeepseekModelFactory(ModelFactory):
    """DeepSeek模型工厂"""
    
    @staticmethod
    def create_llm_provider(model_name: str, **kwargs) -> BaseLLMProvider:
        """创建LLM提供者实例"""
        api_key = kwargs.get("api_key", settings.deepseek_api_key)
        base_url = kwargs.get("base_url", settings.deepseek_base_url)
        temperature = kwargs.get("temperature", settings.temperature)
        max_tokens = kwargs.get("max_tokens", settings.max_tokens)
        
        return DeepseekLLMProvider(
            model_name=model_name, 
            api_key=api_key, 
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    @staticmethod
    def create_embedding_provider(model_name: str, **kwargs) -> EmbeddingProvider:
        """创建嵌入提供者实例
        
        DeepSeek不提供嵌入服务，返回None
        """
        return None 