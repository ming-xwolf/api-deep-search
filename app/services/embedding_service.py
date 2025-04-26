from typing import List
from sentence_transformers import SentenceTransformer
from openai import OpenAI

from app.config.settings import settings

class EmbeddingService:
    """嵌入服务，负责生成文本的向量表示"""
    
    def __init__(self):
        """初始化嵌入服务"""
        self.embedding_provider = settings.embedding_provider
        self.embedding_dimension = None
        
        if self.embedding_provider == "local":
            # 使用本地Sentence Transformers模型
            self.embedding_model = SentenceTransformer(settings.local_embedding_model)
            self.embedding_model_name = settings.local_embedding_model
            self.embedding_dimension = settings.embedding_dimension
        elif self.embedding_provider == "openai":
            # 使用OpenAI API
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
            self.embedding_model_name = settings.openai_embedding_model
            self.embedding_dimension = 1536  # OpenAI的text-embedding-3-small维度
        elif self.embedding_provider == "siliconflow":
            # 使用SiliconFlow API
            self.siliconflow_client = OpenAI(
                api_key=settings.siliconflow_api_key,
                base_url=settings.siliconflow_base_url
            )
            self.embedding_model_name = settings.siliconflow_embedding_model
            self.embedding_dimension = 1024  # SiliconFlow的embe-medium维度
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量的维度"""
        return self.embedding_dimension
    
    def get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            文本的嵌入向量
        """
        if self.embedding_provider == "local":
            # 使用本地模型
            return self.embedding_model.encode(text).tolist()
        elif self.embedding_provider == "openai":
            # 使用OpenAI API
            response = self.openai_client.embeddings.create(
                model=self.embedding_model_name,
                input=text
            )
            return response.data[0].embedding
        elif self.embedding_provider == "siliconflow":
            # 使用SiliconFlow API
            response = self.siliconflow_client.embeddings.create(
                model=self.embedding_model_name,
                input=text
            )
            return response.data[0].embedding
        else:
            raise ValueError(f"不支持的嵌入提供商: {self.embedding_provider}") 