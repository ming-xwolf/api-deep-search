import uvicorn
from app.config.settings import settings

if __name__ == "__main__":
    """启动应用"""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 