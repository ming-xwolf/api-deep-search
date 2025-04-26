#!/bin/bash

# 设置镜像名称和标签
IMAGE_NAME="api-deep-search"
TAG="latest"

# 显示构建信息
echo "开始构建 ${IMAGE_NAME}:${TAG} 镜像..."

# 构建Docker镜像
docker build -t ${IMAGE_NAME}:${TAG} .

# 检查构建结果
if [ $? -eq 0 ]; then
    echo "镜像构建成功: ${IMAGE_NAME}:${TAG}"
    echo "你可以使用以下命令运行该镜像:"
    echo "docker run -p 8000:8000 --env-file .env ${IMAGE_NAME}:${TAG}"
    echo "或者使用docker-compose启动完整环境:"
    echo "docker-compose up -d"
else
    echo "镜像构建失败，请检查错误信息。"
    exit 1
fi 