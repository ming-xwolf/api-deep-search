@echo off
setlocal enabledelayedexpansion

REM 确保当前目录是项目根目录
if not exist environment.yml (
    echo 错误: 未找到environment.yml文件，请确保你在项目根目录中。
    exit /b 1
)

REM 检查conda是否安装
where conda >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到conda命令。请先安装Anaconda或Miniconda。
    exit /b 1
)

REM 创建环境
echo 正在创建api-deep-search conda环境...
call conda env create -f environment.yml

REM 检查是否创建成功
if %ERRORLEVEL% neq 0 (
    echo 错误: 创建环境失败，请检查environment.yml文件或conda安装。
    exit /b 1
)

echo 环境创建成功！可以使用以下命令激活环境:
echo conda activate api-deep-search

REM 提示用户激活环境
set /p choice=现在要继续配置吗? (y/n): 
if /i "!choice!"=="y" (
    echo 请手动激活环境，在命令提示符中运行:
    echo conda activate api-deep-search
    
    REM 提示用户创建.env文件
    if not exist .env (
        echo 未找到.env文件。
        set /p create_env=是否要从.env-example创建.env文件? (y/n): 
        if /i "!create_env!"=="y" (
            if exist .env-example (
                copy .env-example .env
                echo .env文件已创建。请编辑该文件并填入你的API密钥和配置信息。
            ) else (
                echo 未找到.env-example文件。请手动创建.env文件。
            )
        )
    )
    
    echo 设置完成！激活环境后，可以使用以下命令启动应用:
    echo python app.py
)

endlocal 