from typing import List, Dict, Any, Optional
import json
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from openai import OpenAI

from app.config.settings import settings
from app.models.schema import APIEndpoint, APISpec

class VectorStore:
    """向量数据库存储服务"""
    
    def __init__(self):
        # 初始化Qdrant客户端
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.qdrant_collection_name
        
        # 初始化嵌入服务
        self._init_embedding_service()
        
        # 确保集合存在
        self._ensure_collection_exists()
    
    def _init_embedding_service(self):
        """初始化嵌入服务"""
        self.embedding_provider = settings.embedding_provider
        
        if self.embedding_provider == "local":
            # 使用本地Sentence Transformers模型
            self.embedding_model = SentenceTransformer(settings.embedding_model)
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
    
    def _ensure_collection_exists(self):
        """确保向量集合存在"""
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.embedding_dimension,
                    distance=models.Distance.COSINE
                )
            )
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
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
    
    def _prepare_endpoint_text(self, endpoint: APIEndpoint) -> str:
        """准备用于嵌入的端点文本"""
        text_parts = [
            f"路径: {endpoint.path}",
            f"方法: {endpoint.method}"
        ]
        
        if endpoint.summary:
            text_parts.append(f"摘要: {endpoint.summary}")
            
        if endpoint.description:
            text_parts.append(f"描述: {endpoint.description}")
            
        if endpoint.tags:
            text_parts.append(f"标签: {', '.join(endpoint.tags)}")
            
        if endpoint.parameters:
            params_str = "\n".join([f"- {p.get('name', '')}: {p.get('description', '')}" 
                                   for p in endpoint.parameters if 'name' in p])
            if params_str:
                text_parts.append(f"参数:\n{params_str}")
                
        if endpoint.request_body:
            text_parts.append("请求体:")
            if isinstance(endpoint.request_body, dict):
                text_parts.append(json.dumps(endpoint.request_body, ensure_ascii=False))
            
        if endpoint.responses:
            text_parts.append("响应:")
            for status, response in endpoint.responses.items():
                text_parts.append(f"- {status}: {response.get('description', '')}")
                
        return "\n".join(text_parts)
    
    def store_api_spec(self, api_spec: APISpec):
        """存储API规范到向量数据库"""
        points = []
        
        for endpoint in api_spec.endpoints:
            # 准备文本并获取嵌入
            text = self._prepare_endpoint_text(endpoint)
            embedding = self._get_embedding(text)
            
            # 准备元数据
            payload = {
                "api_title": api_spec.title,
                "api_version": api_spec.version,
                "path": endpoint.path,
                "method": endpoint.method,
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags,
                "endpoint": endpoint.dict()
            }
            
            # 创建点
            point_id = str(uuid.uuid4())
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
            )
        
        # 批量插入点
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索最相关的API端点"""
        query_embedding = self._get_embedding(query)
        
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        
        results = []
        for result in search_results:
            endpoint_data = result.payload.get("endpoint", {})
            results.append({
                "score": result.score,
                "path": result.payload.get("path"),
                "method": result.payload.get("method"),
                "api_title": result.payload.get("api_title"),
                "api_version": result.payload.get("api_version"),
                "endpoint": APIEndpoint(**endpoint_data) if endpoint_data else None
            })
            
        return results 