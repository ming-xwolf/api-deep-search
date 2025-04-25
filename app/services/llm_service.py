from typing import List, Dict, Any
from openai import OpenAI
import json

from app.config.settings import settings
from app.models.schema import APIEndpoint

class LLMService:
    """大模型服务"""
    
    def __init__(self):
        """初始化LLM服务"""
        self._init_llm_client()
        self.model = settings.llm_model
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        if settings.llm_provider == "deepseek":
            self.client = OpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url
            )
        elif settings.llm_provider == "openai":
            self.client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
        elif settings.llm_provider == "siliconflow":
            self.client = OpenAI(
                api_key=settings.siliconflow_api_key,
                base_url=settings.siliconflow_base_url
            )
        else:
            # 默认使用deepseek
            self.client = OpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url
            )
    
    def generate_answer(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """生成查询答案"""
        # 构建提示词
        prompt = self._build_prompt(query, search_results)
        
        # 调用大模型API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个API专家助手，专门帮助用户理解和使用API。"},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content
    
    def _build_prompt(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """构建提示词"""
        prompt_parts = [
            f"用户查询: {query}\n\n",
            "以下是与查询最相关的API端点信息:\n\n"
        ]
        
        for i, result in enumerate(search_results, 1):
            endpoint = result.get("endpoint")
            if not endpoint:
                continue
                
            prompt_parts.append(f"【相关API {i}】\n")
            prompt_parts.append(f"得分: {result.get('score', 0):.2f}\n")
            prompt_parts.append(f"路径: {endpoint.path}\n")
            prompt_parts.append(f"方法: {endpoint.method}\n")
            
            if endpoint.summary:
                prompt_parts.append(f"摘要: {endpoint.summary}\n")
                
            if endpoint.description:
                prompt_parts.append(f"描述: {endpoint.description}\n")
                
            if endpoint.parameters:
                prompt_parts.append("参数:\n")
                for param in endpoint.parameters:
                    param_name = param.get("name", "")
                    param_desc = param.get("description", "")
                    param_required = "必需" if param.get("required", False) else "可选"
                    param_in = param.get("in", "")
                    prompt_parts.append(f"- {param_name} ({param_in}, {param_required}): {param_desc}\n")
            
            if endpoint.request_body:
                prompt_parts.append("请求体:\n")
                content = endpoint.request_body.get("content", {})
                for media_type, media_info in content.items():
                    prompt_parts.append(f"- 媒体类型: {media_type}\n")
                    schema = media_info.get("schema", {})
                    if schema:
                        prompt_parts.append(f"  结构: {json.dumps(schema, ensure_ascii=False)}\n")
            
            if endpoint.responses:
                prompt_parts.append("响应:\n")
                for status, response in endpoint.responses.items():
                    prompt_parts.append(f"- 状态码 {status}: {response.get('description', '')}\n")
            
            prompt_parts.append("\n")
        
        prompt_parts.append("\n根据以上API信息，请回答以下问题:\n")
        prompt_parts.append(f"{query}\n")
        prompt_parts.append("\n请提供详细的解释，如果可能，包括示例代码。回答应该清晰简洁，易于理解，并且直接针对用户的查询。")
        
        return "".join(prompt_parts)