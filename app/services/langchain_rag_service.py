from typing import List, Dict, Any, Optional
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import json

from app.config.settings import settings
from app.models.schema import APIEndpoint, APISpec
from app.factory.llm_factory import LLMFactory
from app.factory.vector_store_factory import VectorStoreFactory, VectorStore
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

class LangchainRAGService:
    """使用 Langchain 实现的 RAG 服务"""
    
    def __init__(self):
        """初始化服务"""
        self.llm = LLMFactory.create_llm()
        self.vector_store = VectorStoreFactory.create_vector_store()
        self.qa_chain = self._create_qa_chain()
    
    def _create_qa_chain(self) -> RetrievalQA:
        """创建 QA 链"""
        prompt_template = """你是一个API专家助手，专门帮助用户理解和使用API。

用户查询: {question}

以下是与查询最相关的API端点信息:

{context}

根据以上API信息，请回答以下问题:
{question}

请提供详细的解释，如果可能，包括示例代码。回答应该清晰简洁，易于理解，并且直接针对用户的查询。请用中文回答，并确保回答准确、专业。如果无法从上下文中找到答案，请说明原因。"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
    
    def search_by_version(self, query: str, openapi_version: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """根据 OpenAPI 版本搜索文档
        
        Args:
            query: 搜索查询
            openapi_version: OpenAPI 版本
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        filter_condition = None
        if openapi_version:
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="openapi_version",
                        match=MatchValue(value=openapi_version)
                    )
                ]
            )
        
        search_results = self.vector_store.similarity_search(
            query=query,
            k=top_k,
            filter=filter_condition
        )
        
        return self._process_search_results(search_results)
    
    def _process_search_results(self, search_results: List[Any]) -> List[Dict[str, Any]]:
        """处理搜索结果
        
        Args:
            search_results: 搜索结果列表
            
        Returns:
            List[Dict[str, Any]]: 处理后的结果列表
        """
        sources = []
        for doc in search_results:
            metadata = doc.metadata
            if "endpoint" in metadata:
                sources.append({
                    "score": metadata.get("score", 0),
                    "path": metadata.get("path"),
                    "method": metadata.get("method"),
                    "api_title": metadata.get("api_title"),
                    "api_version": metadata.get("api_version"),
                    "openapi_version": metadata.get("openapi_version"),
                    "file_path": metadata.get("file_path"),
                    "endpoint": metadata.get("endpoint")
                })
        return sources
    
    def store_api_spec(self, api_spec: APISpec, file_path: Optional[str] = None):
        """存储 API 规范
        
        Args:
            api_spec: API 规范对象
            file_path: 文件路径
        """
        documents = []
        metadatas = []
        
        for endpoint in api_spec.endpoints:
            # 准备文档文本
            text = self._prepare_endpoint_text(endpoint)
            
            # 准备元数据
            metadata = {
                "api_title": api_spec.title,
                "api_version": api_spec.version,
                "openapi_version": api_spec.openapi_version,
                "path": endpoint.path,
                "method": endpoint.method,
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags,
                "endpoint": endpoint.dict(),
                "text": text  # 存储原始文本，用于FAISS重建
            }
            
            if file_path:
                metadata["file_path"] = file_path
            
            documents.append(text)
            metadatas.append(metadata)
        
        # 批量添加文档
        self.vector_store.add_texts(
            texts=documents,
            metadatas=metadatas
        )
    
    def _prepare_endpoint_text(self, endpoint: APIEndpoint) -> str:
        """准备端点文本
        
        Args:
            endpoint: API 端点对象
            
        Returns:
            str: 格式化后的文本
        """
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
            text_parts.append("参数:")
            for param in endpoint.parameters:
                param_name = param.get("name", "")
                param_desc = param.get("description", "")
                param_required = "必需" if param.get("required", False) else "可选"
                param_in = param.get("in", "")
                text_parts.append(f"- {param_name} ({param_in}, {param_required}): {param_desc}")
                
        if endpoint.request_body:
            text_parts.append("请求体:")
            content = endpoint.request_body.get("content", {})
            for media_type, media_info in content.items():
                text_parts.append(f"- 媒体类型: {media_type}")
                schema = media_info.get("schema", {})
                if schema:
                    text_parts.append(f"  结构: {json.dumps(schema, ensure_ascii=False)}")
            
        if endpoint.responses:
            text_parts.append("响应:")
            for status, response in endpoint.responses.items():
                text_parts.append(f"- 状态码 {status}: {response.get('description', '')}")
                
        return "\n".join(text_parts)
    
    def _build_prompt(self, query: str, context: List[Dict[str, Any]]) -> str:
        """构建提示词"""
        prompt_parts = [
            f"用户查询: {query}\n\n",
            "以下是与查询最相关的API端点信息:\n\n"
        ]
        
        for i, result in enumerate(context, 1):
            endpoint = result.get("endpoint")
            if not endpoint:
                continue
                
            prompt_parts.append(f"【相关API {i}】\n")
            prompt_parts.append(f"路径: {endpoint.get('path', '')}\n")
            prompt_parts.append(f"方法: {endpoint.get('method', '')}\n")
            
            if endpoint.get('summary'):
                prompt_parts.append(f"摘要: {endpoint['summary']}\n")
                
            if endpoint.get('description'):
                prompt_parts.append(f"描述: {endpoint['description']}\n")
                
            if endpoint.get('parameters'):
                prompt_parts.append("参数:\n")
                for param in endpoint['parameters']:
                    param_name = param.get("name", "")
                    param_desc = param.get("description", "")
                    param_required = "必需" if param.get("required", False) else "可选"
                    param_in = param.get("in", "")
                    prompt_parts.append(f"- {param_name} ({param_in}, {param_required}): {param_desc}\n")
            
            if endpoint.get('request_body'):
                prompt_parts.append("请求体:\n")
                content = endpoint['request_body'].get("content", {})
                for media_type, media_info in content.items():
                    prompt_parts.append(f"- 媒体类型: {media_type}\n")
                    schema = media_info.get("schema", {})
                    if schema:
                        prompt_parts.append(f"  结构: {json.dumps(schema, ensure_ascii=False)}\n")
            
            if endpoint.get('responses'):
                prompt_parts.append("响应:\n")
                for status, response in endpoint['responses'].items():
                    prompt_parts.append(f"- 状态码 {status}: {response.get('description', '')}\n")
            
            prompt_parts.append("\n")
        
        prompt_parts.append("\n根据以上API信息，请回答以下问题:\n")
        prompt_parts.append(f"{query}\n")
        prompt_parts.append("\n请提供详细的解释，如果可能，包括示例代码。回答应该清晰简洁，易于理解，并且直接针对用户的查询。")
        
        return "".join(prompt_parts)
    
    def search(self, query: str) -> Dict[str, Any]:
        """搜索API并生成回答
        
        Args:
            query: 搜索查询
            
        Returns:
            包含搜索结果和生成的回答的字典
        """
        # 使用 invoke 方法替代 __call__
        result = self.qa_chain.invoke({"query": query})
        
        # 处理搜索结果
        sources = self._process_search_results(result.get("source_documents", []))
        
        # 生成回答
        return self._generate_response(query, sources)
    
    def search_api_by_version(self, query: str, openapi_version: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """根据OpenAPI版本筛选搜索API
        
        Args:
            query: 搜索查询
            openapi_version: OpenAPI版本，可选
            top_k: 返回结果数量，默认为5
            
        Returns:
            包含搜索结果和生成的回答的字典
        """
        # 使用自己的搜索方法
        sources = self.search_by_version(
            query=query,
            openapi_version=openapi_version,
            top_k=top_k
        )
        
        # 如果没有结果，返回特定消息
        if not sources and openapi_version:
            return {
                "answer": f"抱歉，我没有找到符合 OpenAPI {openapi_version} 版本的API信息。",
                "sources": []
            }
        
        # 生成回答
        return self._generate_response(query, sources)
    
    def _generate_response(self, query: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成回答
        
        Args:
            query: 搜索查询
            sources: 源文档列表
            
        Returns:
            包含回答和源文档的字典
        """
        if not sources:
            return {
                "answer": "抱歉，我没有找到相关的API信息。",
                "sources": []
            }
        
        # 构建系统提示
        system_prompt = "你是一个API专家助手，专门帮助用户理解和使用API。"
        
        # 构建用户提示
        user_prompt = self._build_prompt(query, sources)
        
        # 调用LLM生成回答
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            "answer": response.content,
            "sources": sources
        }
    
    def clean_collection(self) -> bool:
        """清理向量存储中的所有文档
        
        Returns:
            bool: 是否成功
        """
        return self.vector_store.clean()
            
    def delete_embeddings_by_file_path(self, file_path: str) -> int:
        """根据文件路径删除向量存储中的文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 删除的文档数量
        """
        return self.vector_store.delete_by_file_path(file_path) 