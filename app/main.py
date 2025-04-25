from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.config.settings import settings
from app.api.routes import router as api_router

# 确保上传目录存在
os.makedirs("upload", exist_ok=True)

# 创建应用
app = FastAPI(
    title="API深度搜索",
    description="使用向量数据库和大模型技术进行API规范搜索",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加路由
app.include_router(api_router)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用API深度搜索服务",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    } 