"""基础模型工厂和接口定义"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json

class LLMProvider(ABC):
    """大语言模型提供者抽象基类"""
    
    @abstractmethod
    def generate_answer(self, query: str, context: List[Dict[str, Any]]) -> str:
        """生成回答"""
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, str]:
        """获取提供商信息"""
        pass

class BaseLLMProvider(LLMProvider):
    """LLM提供者基础实现类"""
    
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
    
    def generate_answer(self, query: str, context: List[Dict[str, Any]]) -> str:
        """生成回答的通用实现"""
        # 构建提示词
        prompt = self._build_prompt(query, context)
        
        # 获取系统提示
        system_prompt = "你是一个API专家助手，专门帮助用户理解和使用API。"
        
        # 调用模型生成回答（由子类实现模型调用）
        return self._call_llm(system_prompt, prompt)
    
    @abstractmethod
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用LLM获取回答（需要子类实现）"""
        pass

class EmbeddingProvider(ABC):
    """嵌入模型提供者抽象基类"""
    
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量的维度"""
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, str]:
        """获取提供商信息"""
        pass

class ModelFactory(ABC):
    """模型工厂抽象基类"""
    
    @staticmethod
    @abstractmethod
    def create_llm_provider(model_name: str, **kwargs) -> LLMProvider:
        """创建LLM提供者实例"""
        pass
    
    @staticmethod
    @abstractmethod
    def create_embedding_provider(model_name: str, **kwargs) -> EmbeddingProvider:
        """创建嵌入提供者实例"""
        pass 