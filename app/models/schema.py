from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class APIEndpoint(BaseModel):
    """API端点数据模型"""
    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    operationId: Optional[str] = None

class APISpec(BaseModel):
    """API规范数据模型"""
    title: str
    version: str
    description: Optional[str] = None
    servers: List[Dict[str, str]] = Field(default_factory=list)
    endpoints: List[APIEndpoint] = Field(default_factory=list)

class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str
    top_k: int = 5
    
class APIEndpointWithSource(APIEndpoint):
    """带有源文件信息的API端点数据模型"""
    file_path: Optional[str] = None
    api_title: Optional[str] = None
    api_version: Optional[str] = None

class SearchResponse(BaseModel):
    """搜索响应模型"""
    results: List[APIEndpointWithSource]
    answer: str

class UploadAPISpecRequest(BaseModel):
    """上传API规范请求模型"""
    url: Optional[str] = None
    content: Optional[str] = None
    file_type: str = "json"  # "json" 或 "yaml" 