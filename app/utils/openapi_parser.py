import json
import yaml
import httpx
import os
from typing import Dict, List, Any, Union, Optional
import chardet

from app.models.schema import APIEndpoint, APISpec

class OpenAPIParser:
    """OpenAPI规范解析器"""
    
    @staticmethod
    async def load_from_url(url: str) -> Dict[str, Any]:
        """从URL加载OpenAPI规范"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            content = response.text
            
            # 根据内容类型判断是JSON还是YAML
            content_type = response.headers.get('content-type', '')
            if url.endswith('.json') or content_type.startswith('application/json'):
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    raise ValueError(f"解析JSON失败: {str(e)}")
            else:
                try:
                    return yaml.safe_load(content)
                except yaml.YAMLError as e:
                    raise ValueError(f"解析YAML失败: {str(e)}")
    
    @staticmethod
    async def get_raw_content_from_url(url: str) -> str:
        """从URL获取原始内容
        
        Args:
            url: API规范的URL
            
        Returns:
            原始文本内容
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
            except httpx.HTTPError as e:
                raise ValueError(f"获取URL内容失败: {str(e)}")
    
    @staticmethod
    def load_from_string(content: str, file_type: str = "json") -> Dict[str, Any]:
        """从字符串加载OpenAPI规范"""
        if file_type.lower() == "json":
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"解析JSON失败: {str(e)}")
        else:
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise ValueError(f"解析YAML失败: {str(e)}")
    
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
        
        # 检测OpenAPI规范版本
        openapi_version = None
        if 'openapi' in spec_data:
            # OpenAPI 3.x
            openapi_version = spec_data.get('openapi')
        elif 'swagger' in spec_data:
            # Swagger 2.x
            openapi_version = spec_data.get('swagger')
        
        # 根据不同版本解析所有端点
        endpoints = []
        
        paths = spec_data.get('paths', {})
        if not paths:
            raise ValueError("无效的OpenAPI规范: 缺少paths部分")
            
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
                
                # 根据规范版本处理差异（如果需要）
                if openapi_version and openapi_version.startswith('2.'):
                    # Swagger 2.x的特殊处理，例如处理请求体字段
                    if 'requestBody' not in operation and 'consumes' in operation:
                        # Swagger 2.x使用parameters+in:body代替requestBody
                        body_params = [p for p in operation.get('parameters', []) if p.get('in') == 'body']
                        if body_params:
                            endpoint.request_body = {
                                'content': {
                                    operation.get('consumes', ['application/json'])[0]: {
                                        'schema': body_params[0].get('schema', {})
                                    }
                                }
                            }
                
                endpoints.append(endpoint)
        
        # 创建API规范
        api_spec = APISpec(
            title=title,
            version=version,
            description=description,
            servers=servers,
            endpoints=endpoints,
            openapi_version=openapi_version
        )
        
        return api_spec
    
    @staticmethod
    def load_from_file(file_path: str) -> Dict[str, Any]:
        """从文件加载OpenAPI规范
        
        Args:
            file_path: API规范文件路径
            
        Returns:
            解析后的规范数据
        """
        # 读取文件内容并检测编码
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
        # 检测编码
        result = chardet.detect(file_content)
        encoding = result['encoding'] or 'utf-8'
        
        # 解码内容
        content = file_content.decode(encoding)
            
        # 根据文件扩展名判断格式
        if file_path.lower().endswith('.json'):
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"解析JSON文件失败: {str(e)}")
        else:
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise ValueError(f"解析YAML文件失败: {str(e)}")
            
    @staticmethod
    def determine_file_type(filename: str) -> str:
        """根据文件名确定文件类型
        
        Args:
            filename: 文件名
            
        Returns:
            文件类型: "json" 或 "yaml"
        """
        lower_filename = filename.lower()
        if lower_filename.endswith('.json'):
            return "json"
        elif lower_filename.endswith('.yaml') or lower_filename.endswith('.yml'):
            return "yaml"
        else:
            # 默认为JSON
            return "json" 