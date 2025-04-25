import json
import yaml
import httpx
from typing import Dict, List, Any, Union, Optional

from app.models.schema import APIEndpoint, APISpec

class OpenAPIParser:
    """OpenAPI规范解析器"""
    
    @staticmethod
    async def load_from_url(url: str) -> Dict[str, Any]:
        """从URL加载OpenAPI规范"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            
            content = response.text
            
            # 根据内容类型判断是JSON还是YAML
            if url.endswith('.json') or response.headers.get('content-type', '').startswith('application/json'):
                return json.loads(content)
            else:
                return yaml.safe_load(content)
    
    @staticmethod
    def load_from_string(content: str, file_type: str = "json") -> Dict[str, Any]:
        """从字符串加载OpenAPI规范"""
        if file_type.lower() == "json":
            return json.loads(content)
        else:
            return yaml.safe_load(content)
    
    @staticmethod
    def parse_openapi_spec(spec_data: Dict[str, Any]) -> APISpec:
        """解析OpenAPI规范"""
        # 获取基本信息
        info = spec_data.get('info', {})
        title = info.get('title', 'Unknown API')
        version = info.get('version', '1.0.0')
        description = info.get('description', '')
        
        # 获取服务器信息
        servers = spec_data.get('servers', [])
        
        # 解析所有端点
        endpoints = []
        
        paths = spec_data.get('paths', {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                # 跳过非HTTP方法的属性
                if method in ['parameters', 'summary', 'description', 'servers']:
                    continue
                    
                # 创建端点
                endpoint = APIEndpoint(
                    path=path,
                    method=method.upper(),
                    summary=operation.get('summary', ''),
                    description=operation.get('description', ''),
                    parameters=operation.get('parameters', []),
                    request_body=operation.get('requestBody', None),
                    responses=operation.get('responses', {}),
                    tags=operation.get('tags', []),
                    operationId=operation.get('operationId', '')
                )
                
                endpoints.append(endpoint)
        
        # 创建API规范
        api_spec = APISpec(
            title=title,
            version=version,
            description=description,
            servers=servers,
            endpoints=endpoints
        )
        
        return api_spec 