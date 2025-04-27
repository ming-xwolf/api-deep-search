"""OpenAI模型提供商实现"""
from typing import List, Dict, Any, Optional
import json

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.services.factory.base import BaseLLMProvider, EmbeddingProvider, ModelFactory
from app.config.settings import settings

class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI大语言模型提供者"""
    
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 1000):
        """初始化OpenAI模型提供者"""
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 创建ChatOpenAI实例
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            openai_api_base=base_url or settings.openai_base_url
        )
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用LLM获取回答"""
        # 创建提示模板
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{prompt}")
        ])
        
        # 创建消息并调用LLM
        chain = prompt_template | self.llm
        response = chain.invoke({"prompt": user_prompt})
        
        return response.content
    
    def get_provider_info(self) -> Dict[str, str]:
        """获取提供商信息"""
        return {
            "provider": "openai",
            "model": self.model_name,
            "temperature": str(self.temperature),
            "max_tokens": str(self.max_tokens)
        }

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI嵌入模型提供者"""
    
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        """初始化OpenAI嵌入提供者"""
        self.model_name = model_name
        
        # 创建OpenAIEmbeddings实例
        self.embeddings = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=base_url or settings.openai_base_url
        )
        
        # OpenAI text-embedding-3-small维度为1536
        self.embedding_dimension = 1536 if model_name.startswith("text-embedding-3") else 1536
    
    def get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        return self.embeddings.embed_query(text)
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量的维度"""
        return self.embedding_dimension
    
    def get_provider_info(self) -> Dict[str, str]:
        """获取提供商信息"""
        return {
            "provider": "openai",
            "model": self.model_name,
            "dimension": str(self.embedding_dimension)
        }

class OpenAIModelFactory(ModelFactory):
    """OpenAI模型工厂"""
    
    @staticmethod
    def create_llm_provider(model_name: str, **kwargs) -> BaseLLMProvider:
        """创建LLM提供者实例"""
        api_key = kwargs.get("api_key", settings.openai_api_key)
        base_url = kwargs.get("base_url", settings.openai_base_url)
        temperature = kwargs.get("temperature", settings.temperature)
        max_tokens = kwargs.get("max_tokens", settings.max_tokens)
        
        return OpenAILLMProvider(
            model_name=model_name, 
            api_key=api_key, 
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    @staticmethod
    def create_embedding_provider(model_name: str, **kwargs) -> EmbeddingProvider:
        """创建嵌入提供者实例"""
        api_key = kwargs.get("api_key", settings.openai_api_key)
        base_url = kwargs.get("base_url", settings.openai_base_url)
        
        return OpenAIEmbeddingProvider(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url
        ) 