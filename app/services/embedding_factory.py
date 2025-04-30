from typing import Union
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config.settings import settings

class EmbeddingFactory:
    """嵌入模型工厂类，用于根据配置生成对应的嵌入模型实例"""
    
    @staticmethod
    def create_embedding() -> Union[OpenAIEmbeddings, HuggingFaceEmbeddings]:
        """创建嵌入模型实例
        
        Returns:
            Union[OpenAIEmbeddings, HuggingFaceEmbeddings]: 嵌入模型实例
        """
        if settings.embedding_provider == "openai":
            return OpenAIEmbeddings(
                model=settings.openai_embedding_model,
                openai_api_key=settings.openai_api_key,
                openai_api_base=settings.openai_base_url
            )
        elif settings.embedding_provider == "local":
            return HuggingFaceEmbeddings(
                model_name=settings.local_embedding_model,
                model_kwargs={"device": "cpu"}
            )
        elif settings.embedding_provider == "siliconflow":
            return OpenAIEmbeddings(
                model=settings.siliconflow_embedding_model,
                openai_api_key=settings.siliconflow_api_key,
                openai_api_base=settings.siliconflow_base_url
            )
        else:
            raise ValueError(f"不支持的嵌入模型提供商: {settings.embedding_provider}")
    
    @staticmethod
    def get_info() -> dict:
        """获取当前嵌入模型配置信息
        
        Returns:
            dict: 包含嵌入模型配置信息的字典
        """
        info = {
            "provider": settings.embedding_provider,
            "model": None,
            "base_url": None,
            "device": "cpu"
        }
        
        if settings.embedding_provider == "openai":
            info["model"] = settings.openai_embedding_model
            info["base_url"] = settings.openai_base_url
        elif settings.embedding_provider == "local":
            info["model"] = settings.local_embedding_model
        elif settings.embedding_provider == "siliconflow":
            info["model"] = settings.siliconflow_embedding_model
            info["base_url"] = settings.siliconflow_base_url
            
        return info 