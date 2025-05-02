from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Body
import os
import tempfile
import shutil
import subprocess
from typing import Optional
import httpx
import zipfile
import io

from app.services.file_storage import FileStorage
from app.services.api_detector_service import APIDetectorService

# 创建路由器
router = APIRouter(prefix="/api_detector", tags=["API检测"])

# 依赖注入
def get_file_storage():
    return FileStorage()

def get_api_detector_service():
    return APIDetectorService()

@router.post("/detect")
async def detect_apis(
    file: UploadFile = File(...),
    file_storage: FileStorage = Depends(get_file_storage)
):
    """检测代码库中的API
    
    上传代码库ZIP文件，系统会自动检测其中包含的API类型和定义
    支持REST API、WebSocket、gRPC、GraphQL和OpenAPI/Swagger规范
    """
    try:
        # 确保是ZIP文件
        if not file.filename.lower().endswith('.zip'):
            raise HTTPException(status_code=400, detail="仅支持ZIP格式的代码库文件")
        
        # 保存上传的ZIP文件
        temp_file_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        # 创建API检测服务
        api_detector = APIDetectorService()
        
        # 处理ZIP文件
        result = api_detector.process_zip_file(temp_file_path)
        
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        # 返回结果
        return {
            "message": f"检测完成，发现 {result['api_count']} 个API端点",
            "api_types": result["api_types"],
            "api_count": result["api_count"],
            "apis": result["apis"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API检测过程中出错: {str(e)}")

@router.get("/supported_types")
async def get_supported_api_types(
    api_detector_service: APIDetectorService = Depends(get_api_detector_service)
):
    """获取支持的API类型列表"""
    return api_detector_service.get_supported_types()

@router.post("/detect_from_github")
async def detect_apis_from_github(
    github_url: str = Body(..., embed=True),
    branch: Optional[str] = Body(None, embed=True),
    use_http_download: Optional[bool] = Body(False, embed=True),
    api_detector_service: APIDetectorService = Depends(get_api_detector_service)
):
    """从GitHub仓库URL检测API
    
    输入GitHub仓库URL，系统会自动克隆仓库并检测其中包含的API类型和定义
    支持REST API、WebSocket、gRPC、GraphQL和OpenAPI/Swagger规范
    
    Args:
        github_url: GitHub仓库URL，格式如 https://github.com/username/repo
        branch: 要检测的分支名称，默认为仓库的默认分支
        use_http_download: 是否使用HTTP下载ZIP而不是git克隆，默认为False
    """
    try:
        # 调用服务层方法处理GitHub仓库(同步调用，可能会阻塞)
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: api_detector_service.process_github_repo(
                github_url=github_url,
                branch=branch,
                use_http_download=use_http_download
            )
        )
        
        # 返回结果
        return {
            "message": f"检测完成，发现 {result['api_count']} 个API端点",
            "repository": result["repository"],
            "branch": result["branch"],
            "api_types": result["api_types"],
            "api_count": result["api_count"],
            "apis": result["apis"]
        }
              
    except ValueError as e:
        # URL格式错误等验证错误
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # 克隆或下载失败等运行时错误
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"发生错误: {str(e)}")
        print(f"错误堆栈: {error_trace}")
        raise HTTPException(status_code=500, detail=f"GitHub仓库API检测过程中出错: {str(e)}") 