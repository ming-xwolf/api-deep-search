#!/bin/bash

# 检查是否存在requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "错误: 未找到requirements.txt文件，请确保你在项目根目录中。"
    exit 1
fi

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo "错误: 未找到conda命令。请先安装Anaconda或Miniconda。"
    exit 1
fi

# 创建环境
echo "正在创建api-deep-search conda环境..."
conda create -n api-deep-search python=3.10 -y

# 检查是否创建成功
if [ $? -ne 0 ]; then
    echo "错误: 创建环境失败，请检查conda安装。"
    exit 1
fi

# 安装pip依赖
echo "正在安装依赖..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate api-deep-search
pip install -r requirements.txt

# 检查是否安装成功
if [ $? -ne 0 ]; then
    echo "错误: 安装依赖失败，请检查requirements.txt文件或网络连接。"
    exit 1
fi

echo "环境创建成功！可以使用以下命令激活环境:"
echo "conda activate api-deep-search"

# 提示用户创建.env文件
if [ ! -f ".env" ]; then
    echo "未找到.env文件。"
    read -p "是否要从.env-example创建.env文件? (y/n): " create_env
    if [ "$create_env" = "y" ] || [ "$create_env" = "Y" ]; then
        if [ -f ".env-example" ]; then
            cp .env-example .env
            echo ".env文件已创建。请编辑该文件并填入你的API密钥和配置信息。"
        else
            echo "未找到.env-example文件。请手动创建.env文件。"
        fi
    fi
fi

echo "设置完成！激活环境后，可以使用以下命令启动应用:"
echo "python app.py" 