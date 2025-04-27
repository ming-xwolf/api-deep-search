"""SiliconFlow模型提供商实现"""
from typing import List, Dict, Any, Optional
import json
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.services.factory.base import BaseLLMProvider, EmbeddingProvider, ModelFactory
from app.config.settings import settings

class SiliconFlowLLMProvider(BaseLLMProvider):
    """SiliconFlow大语言模型提供者"""
    
    def __init__(self, model_name: str, api_key: str, base_url: str, temperature: float = 0.3, max_tokens: int = 1000):
        """初始化SiliconFlow模型提供者"""
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
            "provider": "siliconflow",
            "model": self.model_name,
            "temperature": str(self.temperature),
            "max_tokens": str(self.max_tokens),
            "base_url": self.base_url
        }

class SiliconFlowEmbeddingProvider(EmbeddingProvider):
    """SiliconFlow嵌入模型提供者"""
    
    def __init__(self, model_name: str, api_key: str, base_url: str):
        """初始化SiliconFlow嵌入提供者"""
        self.model_name = model_name
        self.base_url = base_url
        
        # 使用OpenAI兼容接口创建OpenAIEmbeddings实例
        self.embeddings = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=base_url
        )
        
        # SiliconFlow的embe-medium维度为1024
        self.embedding_dimension = 1024
    
    def get_embedding_value(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        return self.embeddings.embed_query(text)
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量的维度"""
        return self.embedding_dimension
    
    def get_provider_info(self) -> Dict[str, str]:
        """获取提供商信息"""
        return {
            "provider": "siliconflow",
            "model": self.model_name,
            "dimension": str(self.embedding_dimension),
            "base_url": self.base_url
        }

class SiliconFlowModelFactory(ModelFactory):
    """SiliconFlow模型工厂"""
    
    @staticmethod
    def create_llm_provider(model_name: str, **kwargs) -> BaseLLMProvider:
        """创建LLM提供者实例"""
        api_key = kwargs.get("api_key", settings.siliconflow_api_key)
        base_url = kwargs.get("base_url", settings.siliconflow_base_url)
        temperature = kwargs.get("temperature", settings.temperature)
        max_tokens = kwargs.get("max_tokens", settings.max_tokens)
        
        return SiliconFlowLLMProvider(
            model_name=model_name, 
            api_key=api_key, 
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    @staticmethod
    def create_embedding_provider(model_name: str, **kwargs) -> EmbeddingProvider:
        """创建嵌入提供者实例"""
        api_key = kwargs.get("api_key", settings.siliconflow_api_key)
        base_url = kwargs.get("base_url", settings.siliconflow_base_url)
        
        return SiliconFlowEmbeddingProvider(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url
        ) 