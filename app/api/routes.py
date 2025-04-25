from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List

from app.models.schema import SearchRequest, SearchResponse, UploadAPISpecRequest, APIEndpoint
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.utils.openapi_parser import OpenAPIParser

router = APIRouter(prefix="/api", tags=["API"])

# 依赖注入
def get_vector_store():
    return VectorStore()

def get_llm_service():
    return LLMService()

@router.post("/search", response_model=SearchResponse)
async def search_api(
    request: SearchRequest,
    vector_store: VectorStore = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service)
):
    """搜索API"""
    # 使用向量存储搜索相关端点
    search_results = vector_store.search(request.query, request.top_k)
    
    # 如果没有结果，返回空
    if not search_results:
        return SearchResponse(results=[], answer="抱歉，我没有找到相关的API信息。")
    
    # 使用LLM生成回答
    answer = llm_service.generate_answer(request.query, search_results)
    
    # 提取端点结果
    endpoints = []
    for result in search_results:
        if result.get("endpoint"):
            endpoints.append(result["endpoint"])
    
    return SearchResponse(results=endpoints, answer=answer)

@router.post("/upload")
async def upload_api_spec(
    request: UploadAPISpecRequest,
    vector_store: VectorStore = Depends(get_vector_store)
):
    """上传API规范"""
    try:
        # 处理URL
        if request.url:
            spec_data = await OpenAPIParser.load_from_url(request.url)
        # 处理内容
        elif request.content:
            spec_data = OpenAPIParser.load_from_string(request.content, request.file_type)
        else:
            raise HTTPException(status_code=400, detail="必须提供URL或内容")
        
        # 解析OpenAPI规范
        api_spec = OpenAPIParser.parse_openapi_spec(spec_data)
        
        # 存储到向量数据库
        vector_store.store_api_spec(api_spec)
        
        return {"message": f"成功上传 {api_spec.title} v{api_spec.version}，包含 {len(api_spec.endpoints)} 个端点"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理API规范时出错: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"} 