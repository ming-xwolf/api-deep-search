"""模型工厂主类"""
from typing import Dict, Optional, Type, Any

from app.services.factory.base import ModelFactory, BaseLLMProvider, EmbeddingProvider
from app.services.factory.openai_provider import OpenAIModelFactory
from app.services.factory.local_provider import LocalModelFactory
from app.config.settings import settings

# 工厂注册表
FACTORY_REGISTRY: Dict[str, Type[ModelFactory]] = {
    "openai": OpenAIModelFactory,
    "local": LocalModelFactory,
}

# 尝试导入其他实现并注册
try:
    from app.services.factory.deepseek_provider import DeepseekModelFactory
    FACTORY_REGISTRY["deepseek"] = DeepseekModelFactory
except ImportError:
    pass

try:
    from app.services.factory.siliconflow_provider import SiliconFlowModelFactory
    FACTORY_REGISTRY["siliconflow"] = SiliconFlowModelFactory
except ImportError:
    pass

class ModelFactoryCreator:
    """模型工厂创建器"""
    
    @staticmethod
    def get_llm_provider(provider_type: Optional[str] = None, model_name: Optional[str] = None, **kwargs) -> BaseLLMProvider:
        """获取LLM提供者
        
        Args:
            provider_type: 提供商类型，如openai、deepseek等
            model_name: 模型名称
            **kwargs: 其他参数
            
        Returns:
            BaseLLMProvider: LLM提供者实例
        """
        # 确定提供商类型
        provider = provider_type or settings.llm_provider
        
        # 确定模型名称
        if model_name is None:
            if provider == "openai":
                model_name = settings.openai_model
            elif provider == "deepseek":
                model_name = settings.deepseek_model
            elif provider == "siliconflow":
                model_name = settings.siliconflow_model
            else:
                model_name = settings.openai_model
        
        # 获取工厂
        factory_class = FACTORY_REGISTRY.get(provider)
        if not factory_class:
            raise ValueError(f"不支持的LLM提供商: {provider}")
        
        # 创建LLM提供者
        llm_provider = factory_class.create_llm_provider(model_name, **kwargs)
        if not llm_provider:
            raise ValueError(f"无法创建LLM提供者: {provider}")
        
        return llm_provider
    
    @staticmethod
    def get_embedding_provider(provider_type: Optional[str] = None, model_name: Optional[str] = None, **kwargs) -> EmbeddingProvider:
        """获取嵌入提供者
        
        Args:
            provider_type: 提供商类型，如openai、local等
            model_name: 模型名称
            **kwargs: 其他参数
            
        Returns:
            EmbeddingProvider: 嵌入提供者实例
        """
        # 确定提供商类型
        provider = provider_type or settings.embedding_provider
        
        # 确定模型名称
        if model_name is None:
            if provider == "openai":
                model_name = settings.openai_embedding_model
            elif provider == "local":
                model_name = settings.local_embedding_model
            elif provider == "siliconflow":
                model_name = settings.siliconflow_embedding_model
            else:
                model_name = settings.local_embedding_model
        
        # 获取工厂
        factory_class = FACTORY_REGISTRY.get(provider)
        if not factory_class:
            raise ValueError(f"不支持的嵌入提供商: {provider}")
        
        # 创建嵌入提供者
        embedding_provider = factory_class.create_embedding_provider(model_name, **kwargs)
        if not embedding_provider:
            raise ValueError(f"无法创建嵌入提供者: {provider}")
        
        return embedding_provider 