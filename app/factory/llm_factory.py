from typing import Optional
from langchain_openai import ChatOpenAI
from app.config.settings import settings

class LLMFactory:
    """LLM 工厂类，用于根据配置生成对应的 LLM 实例"""
    
    @staticmethod
    def create_llm(temperature: Optional[float] = None) -> ChatOpenAI:
        """创建 LLM 实例
        
        Args:
            temperature: 温度参数，如果为 None 则使用配置中的默认值
            
        Returns:
            LLM 实例
        """
        if temperature is None:
            temperature = settings.temperature
            
        if settings.llm_provider == "openai":
            return ChatOpenAI(
                model_name=settings.openai_model,
                temperature=temperature,
                max_tokens=settings.max_tokens,
                openai_api_key=settings.openai_api_key,
                openai_api_base=settings.openai_base_url
            )
        elif settings.llm_provider == "deepseek":
            return ChatOpenAI(
                model_name=settings.deepseek_model,
                temperature=temperature,
                max_tokens=settings.max_tokens,
                openai_api_key=settings.deepseek_api_key,
                openai_api_base=settings.deepseek_base_url
            )
        elif settings.llm_provider == "siliconflow":
            return ChatOpenAI(
                model_name=settings.siliconflow_model,
                temperature=temperature,
                max_tokens=settings.max_tokens,
                openai_api_key=settings.siliconflow_api_key,
                openai_api_base=settings.siliconflow_base_url
            )
        else:
            raise ValueError(f"不支持的 LLM 提供商: {settings.llm_provider}")
    
    @staticmethod
    def get_info() -> dict:
        """获取当前 LLM 配置信息
        
        Returns:
            dict: 包含 LLM 配置信息的字典
        """
        info = {
            "provider": settings.llm_provider,
            "model": None,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "base_url": None
        }
        
        if settings.llm_provider == "openai":
            info["model"] = settings.openai_model
            info["base_url"] = settings.openai_base_url
        elif settings.llm_provider == "deepseek":
            info["model"] = settings.deepseek_model
            info["base_url"] = settings.deepseek_base_url
        elif settings.llm_provider == "siliconflow":
            info["model"] = settings.siliconflow_model
            info["base_url"] = settings.siliconflow_base_url
            
        return info 