import os
from typing import Optional, Literal
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings(BaseModel):
    """应用程序配置设置"""
    # API Keys
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    siliconflow_api_key: Optional[str] = os.getenv("SILICONFLOW_API_KEY", "")
    
    # 模型API配置
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    siliconflow_base_url: str = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.com/v1")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # 向量数据库配置
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:16333")
    qdrant_collection_name: str = "api_specs"
    
    # 嵌入配置
    embedding_provider: Literal["local", "openai", "siliconflow"] = os.getenv("EMBEDDING_PROVIDER", "local")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")  # 本地模型默认使用BGE中文大模型
    siliconflow_embedding_model: str = os.getenv("SILICONFLOW_EMBEDDING_MODEL", "embe-medium")  # siliconflow默认嵌入模型
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")  # OpenAI默认嵌入模型
    embedding_dimension: int = 1024  # 确保这与所选模型维度一致
    
    # 应用程序配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # LLM模型配置
    llm_provider: Literal["deepseek", "openai", "siliconflow"] = os.getenv("LLM_PROVIDER", "deepseek")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    siliconflow_model: str = os.getenv("SILICONFLOW_MODEL", "sf-llama3-70b-chat")
    temperature: float = float(os.getenv("TEMPERATURE", "0.3"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "1000"))
    chunk_size: int = 1000
    chunk_overlap: int = 200

    @property
    def llm_model(self) -> str:
        """根据提供商获取模型名称"""
        if self.llm_provider == "deepseek":
            return self.deepseek_model
        elif self.llm_provider == "openai":
            return self.openai_model
        elif self.llm_provider == "siliconflow":
            return self.siliconflow_model
        return self.deepseek_model

# 创建配置实例
settings = Settings() 