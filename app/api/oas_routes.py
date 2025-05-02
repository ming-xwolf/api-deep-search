from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile, Form
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import tempfile

from app.models.schema import SearchRequest, SearchByVersionRequest, SearchResponse, UploadAPISpecRequest, APIEndpoint, APIEndpointWithSource
from app.services.file_storage import FileStorage
from app.utils.openapi_parser import OpenAPIParser
from app.services.oas_rag_service import OASRAGService

# 创建路由器
router = APIRouter(prefix="/oas", tags=["OpenAPI规范"])

# 依赖注入
def get_file_storage():
    return FileStorage()

def get_rag_service():
    return OASRAGService()

@router.post("/search", response_model=SearchResponse)
async def search_api(
    request: SearchRequest,
    rag_service: OASRAGService = Depends(get_rag_service)
):
    """搜索API"""
    result = rag_service.search(request.query)
    
    # 如果没有结果，返回空
    if not result["sources"]:
        return SearchResponse(results=[], answer="抱歉，我没有找到相关的API信息。")
    
    # 提取端点结果
    endpoints = []
    for source in result["sources"]:
        if source.get("endpoint"):
            # 创建带有源信息的端点对象
            endpoint = APIEndpointWithSource(
                **source["endpoint"],
                file_path=source.get("file_path"),
                api_title=source.get("api_title"),
                api_version=source.get("api_version"),
                openapi_version=source.get("openapi_version")
            )
            endpoints.append(endpoint)
    
    return SearchResponse(results=endpoints, answer=result["answer"])

@router.post("/upload")
async def upload_api_spec(
    request: UploadAPISpecRequest,
    rag_service: OASRAGService = Depends(get_rag_service),
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
        rag_service.store_api_spec(api_spec, file_path=file_path)
        
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
    rag_service: OASRAGService = Depends(get_rag_service),
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
        rag_service.store_api_spec(api_spec, file_path=file_path)
        
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

@router.post("/clean")
async def clean_collection(
    rag_service: OASRAGService = Depends(get_rag_service),
    file_storage: FileStorage = Depends(get_file_storage)
):
    """清空向量数据库集合和磁盘上的API规范文件"""
    try:
        # 清空向量数据库集合
        success = rag_service.clean_collection()
        if not success:
            raise HTTPException(status_code=500, detail="清空集合失败")
        
        # 清空上传目录
        total_files, deleted_files = file_storage.clean_upload_directory()
        
        return {
            "message": f"成功清空向量数据库集合，并删除了 {deleted_files}/{total_files} 个磁盘文件"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空集合时发生错误: {str(e)}")

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
async def delete(
    file_name: str = Body(..., embed=True),
    rag_service: OASRAGService = Depends(get_rag_service),
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
        deleted_embeddings = rag_service.delete_embeddings_by_file_path(file_path)
        
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

@router.post("/search_by_version", response_model=SearchResponse)
async def search_api_by_version(
    request: SearchByVersionRequest,
    rag_service: OASRAGService = Depends(get_rag_service)
) -> SearchResponse:
    """根据 OpenAPI 版本搜索 API
    
    Args:
        request: 搜索请求，包含查询和可选的 OpenAPI 版本
        rag_service: RAG 服务实例
        
    Returns:
        搜索结果响应
    """
    try:
        result = rag_service.search_api_by_version(
            query=request.query,
            openapi_version=request.openapi_version,
            top_k=request.top_k
        )
        
        # 提取端点结果
        endpoints = []
        for source in result["sources"]:
            if source.get("endpoint"):
                # 创建带有源信息的端点对象
                endpoint = APIEndpointWithSource(
                    **source["endpoint"],
                    file_path=source.get("file_path"),
                    api_title=source.get("api_title"),
                    api_version=source.get("api_version"),
                    openapi_version=source.get("openapi_version")
                )
                endpoints.append(endpoint)
        
        return SearchResponse(
            results=endpoints,
            answer=result["answer"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索 API 时出错: {str(e)}"
        )

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