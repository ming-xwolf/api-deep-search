from typing import List, Dict, Any, Optional
import json
import uuid

from app.models.schema import APIEndpoint, APISpec
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import QdrantVectorService

class VectorStore:
    """向量数据库存储服务"""
    
    def __init__(self):
        # 初始化向量服务和嵌入服务
        self.vector_service = QdrantVectorService()
        self.embedding_service = EmbeddingService()
        
        # 确保集合存在
        self.vector_service.ensure_collection_exists(
            vector_size=self.embedding_service.get_embedding_dimension()
        )
    
    @property
    def collection_name(self) -> str:
        """获取集合名称"""
        return self.vector_service.collection_name
    
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
    
    def store_api_spec(self, api_spec: APISpec, file_path: Optional[str] = None):
        """存储API规范到向量数据库
        
        Args:
            api_spec: API规范对象
            file_path: API规范文件在磁盘上的路径
        """
        points = []
        
        for endpoint in api_spec.endpoints:
            # 准备文本并获取嵌入
            text = self._prepare_endpoint_text(endpoint)
            embedding = self.embedding_service.get_embedding(text)
            
            # 准备元数据
            payload = {
                "api_title": api_spec.title,
                "api_version": api_spec.version,
                "openapi_version": api_spec.openapi_version,
                "path": endpoint.path,
                "method": endpoint.method,
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags,
                "endpoint": endpoint.dict()
            }
            
            # 添加文件路径（如果有）
            if file_path:
                payload["file_path"] = file_path
            
            # 创建点
            point_id = str(uuid.uuid4())
            points.append(
                self.vector_service.create_point(embedding, payload, point_id)
            )
        
        # 批量插入点
        self.vector_service.upsert_points(points)

    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索最相关的API端点"""
        query_embedding = self.embedding_service.get_embedding(query)
        
        search_results = self.vector_service.search(
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
                "openapi_version": result.payload.get("openapi_version"),
                "file_path": result.payload.get("file_path"),
                "endpoint": APIEndpoint(**endpoint_data) if endpoint_data else None
            })
            
        return results
    
    def clean_collection(self) -> bool:
        """清理向量数据库集合
        
        如果集合存在，则删除并重新创建集合，清空所有数据
        
        Returns:
            bool: 操作是否成功
        """
        try:
            # 删除集合
            success = self.vector_service.delete_collection()
            if not success:
                return False
            
            # 重新创建集合
            self.vector_service.ensure_collection_exists(
                vector_size=self.embedding_service.get_embedding_dimension()
            )
            return True
        except Exception as e:
            print(f"清理集合时出错: {str(e)}")
            return False
    
    def get_all_file_paths(self) -> List[str]:
        """获取向量数据库中存储的所有文件路径
        
        Returns:
            List[str]: 所有文件路径的列表
        """
        try:
            # 获取所有点的数量
            collection_info = self.vector_service.get_collection_info()
            points_count = collection_info.points_count
            
            if points_count == 0:
                return []
            
            # 获取所有点
            scroll_result = self.vector_service.scroll(
                limit=points_count,
                with_payload=True,
                with_vectors=False
            )
            
            # 提取所有文件路径
            file_paths = set()
            for point in scroll_result[0]:
                if "file_path" in point.payload:
                    file_paths.add(point.payload["file_path"])
            
            return list(file_paths)
        except Exception as e:
            print(f"获取文件路径时出错: {str(e)}")
            return []
            
    def delete_embeddings_by_file_path(self, file_path: str) -> int:
        """根据文件路径删除向量数据库中的嵌入数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 删除的嵌入数据数量
        """
        try:
            # 获取所有点的数量
            collection_info = self.vector_service.get_collection_info()
            points_count = collection_info.points_count
            
            if points_count == 0:
                return 0
            
            # 获取所有匹配该文件路径的点
            file_filter = self.vector_service.create_file_filter(file_path)
            
            scroll_result = self.vector_service.scroll(
                limit=points_count,
                scroll_filter=file_filter,
                with_payload=False,
                with_vectors=False
            )
            
            # 提取所有点的ID
            point_ids = [point.id for point in scroll_result[0]]
            
            # 如果没有匹配的点，直接返回
            if not point_ids:
                return 0
            
            # 删除所有匹配的点
            self.vector_service.delete_points(point_ids)
            
            return len(point_ids)
        except Exception as e:
            print(f"删除嵌入数据时出错: {str(e)}")
            return 0


    def get_openapi_versions(self) -> List[str]:
        """获取所有存储的OpenAPI规范版本
        
        Returns:
            List[str]: 版本列表
        """
        # 查询所有记录，但只返回openapi_version字段
        query_response = self.vector_service.scroll(
            limit=10000,
            with_payload=["openapi_version"],
            with_vectors=False
        )
        
        # 提取版本并去重
        versions = set()
        for record in query_response[0]:
            version = record.payload.get("openapi_version")
            if version:
                versions.add(version)
        
        # 返回排序后的版本列表
        return sorted(list(versions))
    
    def search_by_version(self, query: str, openapi_version: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """按OpenAPI版本搜索API端点
        
        Args:
            query: 搜索查询
            openapi_version: 要筛选的OpenAPI版本，如果为None则不筛选
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        query_embedding = self.embedding_service.get_embedding(query)
        
        # 准备筛选条件
        search_filter = None
        if openapi_version:
            search_filter = self.vector_service.create_oas_version_filter(openapi_version)
        
        # 执行搜索
        search_results = self.vector_service.search(
            query_vector=query_embedding,
            limit=top_k,
            query_filter=search_filter
        )
        
        # 处理结果
        results = []
        for result in search_results:
            endpoint_data = result.payload.get("endpoint", {})
            results.append({
                "score": result.score,
                "path": result.payload.get("path"),
                "method": result.payload.get("method"),
                "api_title": result.payload.get("api_title"),
                "api_version": result.payload.get("api_version"),
                "openapi_version": result.payload.get("openapi_version"),
                "file_path": result.payload.get("file_path"),
                "endpoint": APIEndpoint(**endpoint_data) if endpoint_data else None
            })
            
        return results 
