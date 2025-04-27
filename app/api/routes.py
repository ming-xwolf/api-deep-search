from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile, Form
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import tempfile

from app.models.schema import SearchRequest, SearchResponse, UploadAPISpecRequest, APIEndpoint, APIEndpointWithSource
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.services.file_storage import FileStorage
from app.utils.openapi_parser import OpenAPIParser
from app.services.embedding_service import EmbeddingService
from app.config import settings
from app.services.vector_service import QdrantVectorService

router = APIRouter(prefix="/api", tags=["API"])

# 依赖注入
def get_vector_store():
    return VectorStore()

def get_llm_service():
    return LLMService()

def get_file_storage():
    return FileStorage()

def get_embedding_service():
    return EmbeddingService()

def get_vector_service():
    return QdrantVectorService()

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
            # 创建带有源信息的端点对象
            endpoint = APIEndpointWithSource(
                **result["endpoint"].dict(),
                file_path=result.get("file_path"),
                api_title=result.get("api_title"),
                api_version=result.get("api_version"),
                openapi_version=result.get("openapi_version")
            )
            endpoints.append(endpoint)
    
    return SearchResponse(results=endpoints, answer=answer)

@router.post("/upload")
async def upload_api_spec(
    request: UploadAPISpecRequest,
    vector_store: VectorStore = Depends(get_vector_store),
    file_storage: FileStorage = Depends(get_file_storage)
):
    """通过URL或内容上传API规范
    
    支持两种上传方式：
    1. 通过URL上传
    2. 通过JSON或YAML内容上传
    """
    try:
        # 准备变量
        raw_content = None
        file_type = None
        api_title = "Unknown API"
        api_version = "1.0.0"
        
        # 根据上传方式处理输入
        if request.url:
            # 方式1: URL上传
            raw_content = await OpenAPIParser.get_raw_content_from_url(request.url)
            file_type = "json" if request.url.lower().endswith(".json") else "yaml"
            
        elif request.content:
            # 方式2: 内容上传
            raw_content = request.content
            file_type = request.file_type
            
        else:
            raise HTTPException(status_code=400, detail="必须提供URL或内容")
        
        # 解析API信息（用于文件命名）
        try:
            if request.url:
                spec_data = await OpenAPIParser.load_from_url(request.url)
            else:
                spec_data = OpenAPIParser.load_from_string(raw_content, file_type)
                
            info = spec_data.get('info', {})
            api_title = info.get('title', api_title)
            api_version = info.get('version', api_version)
        except Exception:
            # 如果解析失败，使用默认值
            pass
        
        # 保存文件到目标位置
        file_path = ""
        if request.url:
            # 从URL保存
            file_path = file_storage.save_api_spec_from_url(
                url=request.url,
                content=raw_content,
                api_title=api_title,
                api_version=api_version
            )
        else:
            # 从内容保存
            file_path = file_storage.save_api_spec(
                content=raw_content,
                file_type=file_type,
                api_title=api_title,
                api_version=api_version
            )
        
        # 解析API规范
        spec_data = OpenAPIParser.load_from_file(file_path)
        api_spec = OpenAPIParser.parse_openapi_spec(spec_data)
        
        # 存储到向量数据库
        vector_store.store_api_spec(api_spec, file_path=file_path)
        
        return {
            "message": f"成功上传 {api_spec.title} v{api_spec.version}，包含 {len(api_spec.endpoints)} 个端点",
            "file_path": file_path,
            "api_title": api_spec.title,
            "api_version": api_spec.version,
            "openapi_version": api_spec.openapi_version,
            "endpoints_count": len(api_spec.endpoints)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理API规范时出错: {str(e)}")

@router.post("/upload_file")
async def upload_file_api_spec(
    file: UploadFile = File(...),
    vector_store: VectorStore = Depends(get_vector_store),
    file_storage: FileStorage = Depends(get_file_storage)
):
    """通过本地文件上传API规范"""
    try:
        # 准备变量
        temp_file_path = None
        api_title = "Unknown API"
        api_version = "1.0.0"
        
        # 获取原始文件名和类型
        original_filename = file.filename
        file_type = OpenAPIParser.determine_file_type(original_filename)
        
        # 使用临时文件处理上传内容
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        try:
            # 解析API信息
            spec_data = OpenAPIParser.load_from_file(temp_file_path)
            info = spec_data.get('info', {})
            api_title = info.get('title', api_title)
            api_version = info.get('version', api_version)
        except Exception:
            # 如果解析失败，使用文件名作为标题
            api_title = os.path.splitext(original_filename)[0]
        
        # 保存文件到目标位置
        file_path = file_storage.save_api_spec_from_file(
            uploaded_file_path=temp_file_path,
            file_type=file_type,
            api_title=api_title,
            api_version=api_version
        )
            
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            
        # 解析API规范
        spec_data = OpenAPIParser.load_from_file(file_path)
        api_spec = OpenAPIParser.parse_openapi_spec(spec_data)
        
        # 存储到向量数据库
        vector_store.store_api_spec(api_spec, file_path=file_path)
        
        return {
            "message": f"成功上传 {api_spec.title} v{api_spec.version}，包含 {len(api_spec.endpoints)} 个端点",
            "file_path": file_path,
            "api_title": api_spec.title,
            "api_version": api_spec.version,
            "openapi_version": api_spec.openapi_version,
            "endpoints_count": len(api_spec.endpoints)
        }
    
    except Exception as e:
        # 清理任何可能残留的临时文件
        if 'temp_file_path' in locals() and temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
        raise HTTPException(status_code=500, detail=f"处理API规范时出错: {str(e)}")

@router.post("/clean")
async def clean_collection(
    vector_store: VectorStore = Depends(get_vector_store),
    file_storage: FileStorage = Depends(get_file_storage)
):
    """清空向量数据库集合和磁盘上的API规范文件"""
    try:
        # 获取所有文件路径
        file_paths = vector_store.get_all_file_paths()
        file_count = len(file_paths)
        
        # 清空向量数据库集合
        success = vector_store.clean_collection()
        if not success:
            raise HTTPException(status_code=500, detail="清空集合失败")
        
        # 删除所有文件
        deleted_count = 0
        for file_path in file_paths:
            if file_storage.delete_file(file_path):
                deleted_count += 1
        
        # 如果没有获取到具体文件路径，尝试清空整个上传目录
        if file_count == 0:
            total_files, deleted_files = file_storage.clean_upload_directory()
            return {
                "message": f"成功清空 {vector_store.collection_name} 集合，并删除了 {deleted_files}/{total_files} 个磁盘文件"
            }
        
        return {
            "message": f"成功清空 {vector_store.collection_name} 集合，并删除了 {deleted_count}/{file_count} 个磁盘文件"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空集合时发生错误: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

@router.get("/files")
async def list_files(
    file_storage: FileStorage = Depends(get_file_storage)
):
    """列出上传目录中的所有API规范文件"""
    try:
        # 获取所有文件
        files = file_storage.list_files()
        
        # 准备文件信息
        file_infos = []
        for file_path in files:
            file_name = os.path.basename(file_path)
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            modified_time = datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            # 尝试确定文件类型
            file_type = "unknown"
            if file_name.lower().endswith('.json'):
                file_type = "JSON"
            elif file_name.lower().endswith('.yaml') or file_name.lower().endswith('.yml'):
                file_type = "YAML"
            
            # 尝试读取文件内容获取API信息
            api_title = None
            api_version = None
            openapi_version = None
            try:
                spec_data = OpenAPIParser.load_from_file(file_path)
                info = spec_data.get('info', {})
                api_title = info.get('title')
                api_version = info.get('version')
                
                # 提取OpenAPI规范版本
                if 'openapi' in spec_data:
                    openapi_version = spec_data.get('openapi')
                elif 'swagger' in spec_data:
                    openapi_version = spec_data.get('swagger')
            except:
                # 如果解析失败，使用文件名作为标题
                pass
            
            file_infos.append({
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size,
                "file_size_human": f"{file_size / 1024:.2f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.2f} MB",
                "modified_time": modified_time,
                "file_type": file_type,
                "api_title": api_title,
                "api_version": api_version,
                "openapi_version": openapi_version
            })
        
        # 按修改时间排序（最新的在前面）
        file_infos.sort(key=lambda x: x["modified_time"], reverse=True)
        
        return {
            "files": file_infos,
            "total_count": len(file_infos),
            "total_size": sum(info["file_size"] for info in file_infos),
            "total_size_human": f"{sum(info['file_size'] for info in file_infos) / 1024:.2f} KB" if sum(info["file_size"] for info in file_infos) < 1024 * 1024 else f"{sum(info['file_size'] for info in file_infos) / (1024 * 1024):.2f} MB"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表时出错: {str(e)}")

@router.post("/delete")
async def delete_file(
    file_name: str = Body(..., embed=True),
    vector_store: VectorStore = Depends(get_vector_store),
    file_storage: FileStorage = Depends(get_file_storage)
):
    """根据文件名删除磁盘上的文件并从向量数据库中删除对应的embedding
    
    Args:
        file_name: 要删除的文件名
    """
    try:
        # 获取文件路径
        file_path = os.path.join(file_storage.upload_dir, file_name)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件 {file_name} 不存在")
        
        # 从向量数据库中删除嵌入数据
        deleted_embeddings = vector_store.delete_embeddings_by_file_path(file_path)
        
        # 从磁盘中删除文件
        file_deleted = file_storage.delete_file(file_path)
        
        if not file_deleted:
            raise HTTPException(status_code=500, detail=f"删除文件 {file_name} 失败")
        
        return {
            "message": f"成功删除文件 {file_name} 及其对应的向量嵌入",
            "deleted_embeddings_count": deleted_embeddings
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件时出错: {str(e)}")

@router.get("/openapi_versions")
async def get_openapi_versions(
    vector_store: VectorStore = Depends(get_vector_store)
):
    """获取系统中所有的OpenAPI规范版本"""
    try:
        # 获取所有API的OpenAPI版本
        versions = vector_store.get_openapi_versions()
        
        return {
            "versions": versions,
            "count": len(versions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取OpenAPI版本列表时出错: {str(e)}")

@router.post("/search_by_version")
async def search_api_by_version(
    query: str,
    openapi_version: Optional[str] = None,
    top_k: int = 5,
    vector_store: VectorStore = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service)
):
    """根据OpenAPI版本筛选搜索API"""
    try:
        # 使用向量存储搜索相关端点并按版本筛选
        search_results = vector_store.search_by_version(query, openapi_version, top_k)
        
        # 如果没有结果，返回空
        if not search_results:
            return SearchResponse(results=[], answer="抱歉，我没有找到相关的API信息。")
        
        # 使用LLM生成回答
        answer = llm_service.generate_answer(query, search_results)
        
        # 提取端点结果
        endpoints = []
        for result in search_results:
            if result.get("endpoint"):
                # 创建带有源信息的端点对象
                endpoint = APIEndpointWithSource(
                    **result["endpoint"].dict(),
                    file_path=result.get("file_path"),
                    api_title=result.get("api_title"),
                    api_version=result.get("api_version"),
                    openapi_version=result.get("openapi_version")
                )
                endpoints.append(endpoint)
        
        return SearchResponse(results=endpoints, answer=answer)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"按版本搜索API时出错: {str(e)}")

@router.get("/files_by_version")
async def list_files_by_version(
    openapi_version: Optional[str] = None,
    file_storage: FileStorage = Depends(get_file_storage)
):
    """按OpenAPI版本列出文件"""
    try:
        # 获取所有文件
        files = file_storage.list_files()
        
        # 准备文件信息
        file_infos = []
        for file_path in files:
            file_name = os.path.basename(file_path)
            
            # 尝试读取文件内容获取API信息
            api_title = None
            api_version = None
            spec_openapi_version = None
            try:
                spec_data = OpenAPIParser.load_from_file(file_path)
                info = spec_data.get('info', {})
                api_title = info.get('title')
                api_version = info.get('version')
                
                # 提取OpenAPI规范版本
                if 'openapi' in spec_data:
                    spec_openapi_version = spec_data.get('openapi')
                elif 'swagger' in spec_data:
                    spec_openapi_version = spec_data.get('swagger')
            except:
                # 如果解析失败，跳过该文件
                continue
            
            # 如果指定了版本筛选条件，但不匹配当前文件，则跳过
            if openapi_version and spec_openapi_version != openapi_version:
                continue
                
            # 文件符合条件，添加到结果中
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            modified_time = datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            # 确定文件类型
            file_type = "unknown"
            if file_name.lower().endswith('.json'):
                file_type = "JSON"
            elif file_name.lower().endswith('.yaml') or file_name.lower().endswith('.yml'):
                file_type = "YAML"
            
            file_infos.append({
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size,
                "file_size_human": f"{file_size / 1024:.2f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.2f} MB",
                "modified_time": modified_time,
                "file_type": file_type,
                "api_title": api_title,
                "api_version": api_version,
                "openapi_version": spec_openapi_version
            })
        
        # 按修改时间排序（最新的在前面）
        file_infos.sort(key=lambda x: x["modified_time"], reverse=True)
        
        return {
            "files": file_infos,
            "total_count": len(file_infos),
            "filtered_version": openapi_version,
            "total_size": sum(info["file_size"] for info in file_infos),
            "total_size_human": f"{sum(info['file_size'] for info in file_infos) / 1024:.2f} KB" if sum(info["file_size"] for info in file_infos) < 1024 * 1024 else f"{sum(info['file_size'] for info in file_infos) / (1024 * 1024):.2f} MB"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表时出错: {str(e)}")

@router.get("/embedding_info")
async def get_embedding_info(
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """获取嵌入服务信息"""
    try:
        return {
            "provider": embedding_service.embedding_provider,
            "dimension": embedding_service.get_embedding_dimension(),
            "model": getattr(embedding_service, "embedding_model_name", None)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取嵌入服务信息时出错: {str(e)}")

@router.get("/vector_service_info")
async def get_vector_service_info(
    vector_service: QdrantVectorService = Depends(get_vector_service)
):
    """获取向量数据库服务信息"""
    try:
        # 获取集合信息
        try:
            collection_info = vector_service.get_collection_info()
            points_count = collection_info.points_count
            collection_exists = True
        except Exception:
            points_count = 0
            collection_exists = False
        
        return {
            "service_type": "qdrant",
            "collection_name": vector_service.collection_name,
            "collection_exists": collection_exists,
            "points_count": points_count,
            "url": vector_service.url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取向量服务信息时出错: {str(e)}")

@router.get("/llm_info")
async def get_llm_info(
    llm_service: LLMService = Depends(get_llm_service)
):
    """获取当前使用的LLM信息"""
    return {
        "provider": llm_service.llm_provider,
        "model": llm_service.model,
        "temperature": llm_service.temperature,
        "max_tokens": llm_service.max_tokens,
        "base_url": llm_service.client.base_url
    } 