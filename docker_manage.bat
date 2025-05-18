@echo off
REM Docker管理脚本 - 用于快速管理API Deep Search的Docker服务

REM 确保docker-compose.yml文件存在
if not exist "docker-compose.yml" (
    echo 错误: 在当前目录未找到docker-compose.yml文件
    exit /b 1
)

REM 显示帮助信息
:show_help
    echo API Deep Search - Docker管理脚本
    echo 用法: %0 [命令]
    echo.
    echo 命令:
    echo   start       启动服务
    echo   stop        停止服务
    echo   restart     重启服务
    echo   logs        查看日志 (使用 logs -f 持续查看)
    echo   status      查看服务状态
    echo   build       重新构建镜像
    echo   clean       清理无用镜像和卷
    echo   help        显示帮助信息
    echo.
    goto :eof

REM 如果没有参数，显示帮助信息
if "%~1"=="" (
    call :show_help
    exit /b 0
)

REM 处理命令
if "%~1"=="start" (
    echo 启动API Deep Search服务...
    docker-compose up -d
    echo 服务已启动，访问 http://localhost:18002
    exit /b 0
)

if "%~1"=="stop" (
    echo 停止API Deep Search服务...
    docker-compose down
    echo 服务已停止
    exit /b 0
)

if "%~1"=="restart" (
    echo 重启API Deep Search服务...
    docker-compose restart
    echo 服务已重启
    exit /b 0
)

if "%~1"=="logs" (
    echo 查看API Deep Search日志...
    if "%~2"=="-f" (
        docker-compose logs -f
    ) else (
        docker-compose logs
    )
    exit /b 0
)

if "%~1"=="status" (
    echo API Deep Search服务状态:
    docker-compose ps
    exit /b 0
)

if "%~1"=="build" (
    echo 重新构建API Deep Search镜像...
    docker-compose build --no-cache
    echo 构建完成
    exit /b 0
)

if "%~1"=="clean" (
    echo 清理无用的Docker资源...
    docker system prune -f
    echo 清理完成
    exit /b 0
)

if "%~1"=="help" (
    call :show_help
    exit /b 0
)

REM 未知命令
echo 错误: 未知命令 '%1'
call :show_help
exit /b 1 