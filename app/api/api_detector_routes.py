from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
import os
import tempfile

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