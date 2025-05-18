# 基于官方的Python镜像
FROM python:3.10

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    HOST=0.0.0.0 \
    PORT=8000 \
    PIP_DEFAULT_TIMEOUT=100 \
    # 不安装Postgres二进制文件，使用纯Python实现
    PSYCOPG2_BINARY=0

# 禁用pip的版本检查，缩短构建时间
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# 复制依赖文件
COPY requirements.txt .

# 安装基本依赖
RUN pip install --upgrade pip && \
    # 使用清华大学镜像加速
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    # 安装基本依赖
    pip install wheel setuptools && \
    # 安装项目依赖
    pip install -r requirements.txt

# 复制应用代码
COPY . .

# 确保目录存在
RUN mkdir -p upload data/faiss_index

# 暴露应用端口
EXPOSE 8000

# 设置启动命令
CMD ["python", "app.py"] 