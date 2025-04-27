# API Deep Search

这个项目使用向量数据库存储OpenAPI规范(OAS)文件，并使用大模型进行语义搜索和回答生成。

## 功能

- 加载OpenAPI规范文件(JSON或YAML格式)
- 将API规范分解并存储到向量数据库中
- 将API规范原文件保存到磁盘，便于追踪和管理
- 支持多种大模型提供商进行RAG(检索增强生成)检索：
  - DeepSeek大模型
  - OpenAI兼容接口
  - SiliconFlow兼容接口
- 多种嵌入模型支持：
  - 本地HuggingFace模型嵌入
  - OpenAI嵌入
  - SiliconFlow嵌入
- 提供API端点进行查询和检索
- 支持一键清理向量数据库和磁盘文件
- 支持删除单个API规范文件及其对应的向量嵌入
- 支持从本地磁盘上传API规范文件
- 支持按OpenAPI版本搜索和过滤API端点

## 系统架构

API深度搜索系统由以下核心组件构成：

### 1. 向量存储服务 (VectorStore)

管理API规范的存储、搜索和维护，依赖Qdrant向量数据库和嵌入服务。

### 2. 向量数据库服务 (QdrantVectorService)

封装对Qdrant向量数据库的底层操作，处理向量的存储和检索。

### 3. LLM服务 (LLMService)

生成基于API上下文的自然语言回答，支持OpenAI、DeepSeek和SiliconFlow。

### 4. 嵌入服务 (EmbeddingService)

生成文本的向量表示，支持OpenAI、本地(HuggingFace)和SiliconFlow。

## 安装

### 使用pip安装

```bash
# 克隆代码库
git clone <repository-url>
cd api-deep-search

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 使用conda安装（推荐）

```bash
# 克隆代码库
git clone <repository-url>
cd api-deep-search

# 创建conda环境
conda env create -f environment.yml

# 激活环境
conda activate api-deep-search
```

## 环境变量

在项目根目录创建`.env`文件：

```
# API Keys
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_API_KEY=your_openai_api_key  # 如果需要OpenAI嵌入
SILICONFLOW_API_KEY=your_siliconflow_api_key  # 如果使用SiliconFlow嵌入

# 模型API配置
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
SILICONFLOW_BASE_URL=https://api.siliconflow.com/v1
OPENAI_BASE_URL=https://api.openai.com/v1

# 向量数据库配置
QDRANT_URL=http://localhost:6333  # 如果使用远程Qdrant服务

# 嵌入配置
EMBEDDING_PROVIDER=local  # 可选值: local, openai, siliconflow
LOCAL_EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5  # 本地嵌入模型
SILICONFLOW_EMBEDDING_MODEL=embe-medium  # SiliconFlow嵌入模型
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # OpenAI嵌入模型

# LLM配置
LLM_PROVIDER=deepseek  # 可选值: deepseek, openai, siliconflow
DEEPSEEK_MODEL=deepseek-chat  # DeepSeek模型
OPENAI_MODEL=gpt-3.5-turbo  # OpenAI模型
SILICONFLOW_MODEL=sf-llama3-70b-chat  # SiliconFlow模型
TEMPERATURE=0.3  # 模型温度
MAX_TOKENS=1000  # 最大token数
```

## 使用方法

1. 启动服务:

```bash
python app.py
```

2. 访问API文档: http://localhost:8000/docs 

3. 主要功能:
   - 上传API规范(URL或内容): `/api/upload` 接口
   - 上传API规范(本地文件): `/api/upload_file` 接口
   - 搜索API接口: `/api/search` 接口
   - 按版本搜索API: `/api/search_by_version` 接口 
   - 列出文件: `/api/files` 接口
   - 清理所有数据: `/api/clean` 接口
   - 删除单个文件: `/api/delete` 接口
   - 查看嵌入服务信息: `/api/embedding_info` 接口
   - 查看向量服务信息: `/api/vector_service_info` 接口
   - 查看LLM服务信息: `/api/llm_info` 接口

详细使用方法请参考 [USAGE.md](USAGE.md) 

## Docker部署

### 使用Docker镜像构建和运行

1. 构建Docker镜像:

```bash
# Linux/Mac
./build.sh

# Windows
build.bat
```

2. 运行Docker容器:

```bash
docker run -p 8000:8000 --env-file .env api-deep-search:latest
```

### 使用Docker Compose部署

1. 启动所有服务:

```bash
docker-compose up -d
```

2. 查看日志:

```bash
docker-compose logs -f
```

3. 停止服务:

```bash
docker-compose down
```

Docker环境会自动配置应用和Qdrant向量数据库，并保留上传的文件和向量数据。 