# API Deep Search 使用指南

## 环境设置

1. 确保安装Python 3.8+
2. 安装依赖的方式有两种:

### 方式一: 使用pip安装
```bash
pip install -r requirements.txt
```

### 方式二: 使用conda安装（推荐）
```bash
# 方法1: 使用自动化脚本
# Linux/macOS用户
./setup_conda.sh

# Windows用户
setup_conda.bat

# 方法2: 手动创建
conda env create -f environment.yml
conda activate api-deep-search
```

3. 安装Qdrant向量数据库，可通过Docker安装:
   ```bash
   docker run -p 6333:6333 -p 6334:6334 -v ./qdrant_data:/qdrant/storage qdrant/qdrant
   ```
4. 创建`.env`文件，参考`.env-example`填写必要配置:
   ```
   DEEPSEEK_API_KEY=your_deepseek_api_key
   DEEPSEEK_BASE_URL=https://api.deepseek.com/v1  # Deepseek API的基础URL
   OPENAI_API_KEY=your_openai_api_key  # 如果使用OpenAI嵌入
   SILICONFLOW_API_KEY=your_siliconflow_api_key  # 如果使用SiliconFlow嵌入
   SILICONFLOW_BASE_URL=https://api.siliconflow.com/v1  # SiliconFlow API的基础URL
   OPENAI_BASE_URL=https://api.openai.com/v1  # OpenAI API的基础URL
   
   # 嵌入配置
   EMBEDDING_PROVIDER=local  # 可选值: local, openai, siliconflow
   EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5  # 本地嵌入模型
   SILICONFLOW_EMBEDDING_MODEL=embe-medium  # SiliconFlow嵌入模型
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # OpenAI嵌入模型
   
   # LLM配置
   LLM_PROVIDER=deepseek  # 可选值: deepseek, openai, siliconflow
   DEEPSEEK_MODEL=deepseek-chat  # DeepSeek模型
   OPENAI_MODEL=gpt-3.5-turbo  # OpenAI模型
   SILICONFLOW_MODEL=sf-llama3-70b-chat  # SiliconFlow模型
   TEMPERATURE=0.3  # 模型温度
   MAX_TOKENS=1000  # 最大token数
   
   QDRANT_URL=http://localhost:16333  # 如果使用远程Qdrant服务
   DEBUG=False
   ```

## 基本用法

### 1. 运行API服务

```bash
python app.py
```

服务启动后，可以通过 http://localhost:8000/docs 访问API文档。

### 2. 加载示例API规范

```bash
python examples/load_spec.py
```

这将加载示例OpenAPI规范文件，并存储到向量数据库中。

### 3. 搜索API

```bash
python examples/search_api.py
```

通过命令行交互方式搜索API并获取回答。

### 4. API使用

项目提供以下HTTP API:

#### 上传API规范

```http
POST /api/upload
Content-Type: application/json

{
  "url": "https://example.com/openapi.json",
  "file_type": "json"
}
```

或者：

```http
POST /api/upload
Content-Type: application/json

{
  "content": "{ ... OpenAPI规范JSON内容 ... }",
  "file_type": "json"
}
```

响应示例:

```json
{
  "message": "成功上传 用户管理API v1.0.0，包含 8 个端点",
  "file_path": "upload/用户管理API_v1.0.0_20240516123045_a1b2c3d4.json"
}
```

系统会自动保存API规范文件到`upload`目录下，文件名包含API标题、版本、时间戳和唯一标识符。

#### 搜索API

```http
POST /api/search
Content-Type: application/json

{
  "query": "如何获取用户列表?",
  "top_k": 3
}
```

响应示例:

```json
{
  "results": [
    {
      "path": "/users",
      "method": "GET",
      "summary": "获取用户列表",
      "description": "返回系统中的用户列表，支持分页和筛选",
      "parameters": [...],
      "file_path": "upload/用户管理API_v1.0.0_20240516123045_a1b2c3d4.json",
      "api_title": "用户管理API",
      "api_version": "1.0.0"
    }
  ],
  "answer": "要获取用户列表，你可以使用GET方法访问/users端点..."
}
```

搜索结果中包含了API端点的详细信息，以及源文件的路径、API标题和版本信息，便于追踪和引用。

#### 清理集合和文件

```http
POST /api/clean-collection
```

此API将清空向量数据库中的所有API规范数据，并删除`upload`目录下相关的文件。

响应示例:

```json
{
  "message": "成功清空 api_specs 集合，并删除了 8/8 个磁盘文件"
}
```

响应消息中会显示成功清空的集合名称，以及成功删除的文件数量。

## 高级配置

在`app/config/settings.py`中可以配置:

1. 嵌入模型: 
   - 提供商: 支持本地模型(`local`)、OpenAI(`openai`)和SiliconFlow(`siliconflow`)
   - 本地模型: 默认使用`BAAI/bge-large-zh-v1.5`
   - OpenAI模型: 默认使用`text-embedding-3-small`(1536维)
   - SiliconFlow模型: 默认使用`embe-medium`(1024维)

2. 大模型配置: 
   - 提供商: 支持DeepSeek(`deepseek`)、OpenAI(`openai`)和SiliconFlow(`siliconflow`)
   - DeepSeek模型: 默认使用`deepseek-chat`
   - OpenAI模型: 默认使用`gpt-3.5-turbo`
   - SiliconFlow模型: 默认使用`sf-llama3-70b-chat`
   - 模型温度: 默认为0.3
   - 最大token数: 默认为1000

3. 向量数据库设置: 集合名称、维度等

4. 分块设置: 文本分块大小和重叠等

## 使用不同的嵌入模型

本项目支持三种不同的嵌入模型提供商:

### 1. 本地模型 (默认)

设置`EMBEDDING_PROVIDER=local`，使用SentenceTransformers库加载本地模型。适合无网络环境或追求低延迟的场景。

### 2. OpenAI嵌入

设置`EMBEDDING_PROVIDER=openai`，使用OpenAI的文本嵌入API。需要有效的OpenAI API密钥。

### 3. SiliconFlow嵌入

设置`EMBEDDING_PROVIDER=siliconflow`，使用SiliconFlow的文本嵌入API。需要有效的SiliconFlow API密钥。
SiliconFlow提供了高性能且价格合理的嵌入模型，支持OpenAI兼容的API格式。

## 使用不同的LLM模型

本项目支持三种不同的LLM提供商:

### 1. DeepSeek (默认)

设置`LLM_PROVIDER=deepseek`，使用DeepSeek的模型。默认使用`deepseek-chat`模型。

### 2. OpenAI

设置`LLM_PROVIDER=openai`，使用OpenAI的模型。默认使用`gpt-3.5-turbo`模型。

### 3. SiliconFlow

设置`LLM_PROVIDER=siliconflow`，使用SiliconFlow的模型。默认使用`sf-llama3-70b-chat`模型。

SiliconFlow提供了基于Llama 3等开源模型的高性能实现，同时支持OpenAI兼容的API格式，具有性价比优势。 