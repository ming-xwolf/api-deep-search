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
   # API Keys
   DEEPSEEK_API_KEY=your_deepseek_api_key
   OPENAI_API_KEY=your_openai_api_key  # 如果需要OpenAI嵌入
   SILICONFLOW_API_KEY=your_siliconflow_api_key  # 如果使用SiliconFlow嵌入
   
   # 模型API配置
   DEEPSEEK_BASE_URL=https://api.deepseek.com/v1  # Deepseek API的基础URL
   SILICONFLOW_BASE_URL=https://api.siliconflow.com/v1  # SiliconFlow API的基础URL
   OPENAI_BASE_URL=https://api.openai.com/v1  # OpenAI API的基础URL
   
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
   
   # 向量数据库配置
   QDRANT_URL=http://localhost:6333  # 如果使用远程Qdrant服务
   
   # 调试模式
   DEBUG=False  # 是否启用调试模式
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

上传API规范有三种方式，分别由两个不同的接口提供：

1. 通过URL上传（使用`/api/upload`接口）：

```http
POST /api/upload
Content-Type: application/json

{
  "url": "https://example.com/openapi.json",
  "file_type": "json"
}
```

2. 通过JSON或YAML内容上传（使用`/api/upload`接口）：

```http
POST /api/upload
Content-Type: application/json

{
  "content": "{ ... OpenAPI规范JSON内容 ... }",
  "file_type": "json"
}
```

3. 通过本地文件上传（使用`/api/upload_file`接口）：

```http
POST /api/upload_file
Content-Type: multipart/form-data

file=@/path/to/local/openapi.json
```

上传本地文件时，系统会自动检测文件格式（JSON或YAML）并解析API标题和版本信息。

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

#### 按OpenAPI版本搜索API

```http
POST /api/search_by_version
Content-Type: application/json

{
  "query": "如何获取用户列表?",
  "openapi_version": "3.0.0",
  "top_k": 3
}
```

此API允许你按OpenAPI规范版本筛选搜索结果，只返回指定版本的API端点。如果不指定版本，则搜索所有版本。

响应格式与`/api/search`接口相同。

#### 清理集合和文件

```http
POST /api/clean
```

此API将清空向量数据库中的所有API规范数据，并删除`upload`目录下相关的文件。

响应示例:

```json
{
  "message": "成功清空 api_specs 集合，并删除了 8/8 个磁盘文件"
}
```

响应消息中会显示成功清空的集合名称，以及成功删除的文件数量。

#### 获取文件列表

```http
GET /api/files
```

此API将返回`upload`目录下所有的API规范文件及其详细信息。

响应示例:

```json
{
  "files": [
    {
      "file_name": "用户管理API_v1.0.0_20240516123045_a1b2c3d4.json",
      "file_path": "upload/用户管理API_v1.0.0_20240516123045_a1b2c3d4.json",
      "file_size": 24680,
      "file_size_human": "24.10 KB",
      "modified_time": "2024-05-16 12:30:45",
      "file_type": "JSON"
    },
    {
      "file_name": "产品API_v2.0.0_20240515183012_e5f6g7h8.yaml",
      "file_path": "upload/产品API_v2.0.0_20240515183012_e5f6g7h8.yaml",
      "file_size": 18540,
      "file_size_human": "18.11 KB",
      "modified_time": "2024-05-15 18:30:12",
      "file_type": "YAML"
    }
  ],
  "total_count": 2,
  "total_size": 43220,
  "total_size_human": "42.21 KB"
}
```

响应内容包括:
- 文件列表（按修改时间降序排列，最新的在前）
- 每个文件的名称、路径、大小（字节数和人类可读格式）、修改时间和文件类型
- 总文件数量
- 总文件大小（字节数和人类可读格式）

#### 删除单个文件

```http
POST /api/delete
Content-Type: application/json

{
  "file_name": "用户管理API_v1.0.0_20240516123045_a1b2c3d4.json"
}
```

此API将删除指定的API规范文件，并从向量数据库中移除相关的嵌入数据。

响应示例:

```json
{
  "message": "成功删除文件 用户管理API_v1.0.0_20240516123045_a1b2c3d4.json 并移除了 8 个嵌入数据"
}
```

响应消息中会显示成功删除的文件名，以及从向量数据库中删除的数据点数量。

#### 获取OpenAPI版本列表

```http
GET /api/openapi_versions
```

此API将返回向量数据库中存储的所有OpenAPI规范版本。

响应示例:

```json
{
  "versions": [
    "2.0",
    "3.0.0",
    "3.1.0"
  ]
}
```

#### 按版本列出文件

```http
GET /api/files_by_version?openapi_version=3.0.0
```

此API将返回指定OpenAPI版本的API规范文件。如果不指定版本，则返回所有文件。

响应格式与`/api/files`接口相同，但只包含指定版本的文件。

#### 获取服务信息

系统提供了几个API端点来查询当前服务的配置和状态信息：

1. 获取嵌入服务信息：

```http
GET /api/embedding_info
```

响应示例:

```json
{
  "provider": "openai",
  "model": "text-embedding-3-small",
  "dimension": "1536"
}
```

2. 获取向量服务信息：

```http
GET /api/vector_service_info
```

响应示例:

```json
{
  "service_type": "qdrant",
  "collection_name": "api_specs",
  "collection_exists": true,
  "points_count": 143,
  "url": "http://localhost:6333"
}
```

3. 获取LLM服务信息：

```http
GET /api/llm_info
```

响应示例:

```json
{
  "provider": "deepseek",
  "model": "deepseek-chat",
  "temperature": "0.3",
  "max_tokens": "1000"
}
```

### 5. 示例代码

项目提供了几个示例Python脚本，位于`examples`目录：

1. `load_spec.py`: 演示如何加载API规范到向量数据库
2. `search_api.py`: 演示如何搜索API并获取回答
3. `clean_collection.py`: 演示如何清理向量数据库和文件

例如，要搜索API：

```python
import requests

# 定义搜索查询
search_query = {
    "query": "如何获取用户列表?",
    "top_k": 3
}

# 发送请求
response = requests.post("http://localhost:8000/api/search", json=search_query)
results = response.json()

# 打印结果
print(f"回答: {results['answer']}")
print("\n相关API端点:")
for endpoint in results['results']:
    print(f"- {endpoint['method']} {endpoint['path']}: {endpoint['summary']}")
```

## Docker部署

### 使用Docker Compose（推荐）

项目提供了`docker-compose.yml`文件，可以一键部署API服务和Qdrant向量数据库：

```bash
docker-compose up -d
```

这将启动两个容器：
- `app`: API服务，暴露8000端口
- `qdrant`: Qdrant向量数据库，暴露6333和6334端口

所有数据将持久化存储在Docker卷中，可以通过以下命令查看：

```bash
docker volume ls
```

### 单独使用Docker

如果需要单独运行API服务，可以使用以下命令：

```bash
# 构建镜像
docker build -t api-deep-search .

# 运行容器
docker run -p 8000:8000 --env-file .env -v ./upload:/app/upload api-deep-search
```

## 高级配置

### 嵌入模型配置

系统支持三种嵌入模型提供商：

1. 本地模型（默认）：使用HuggingFace模型，如`BAAI/bge-large-zh-v1.5`
2. OpenAI：使用OpenAI的嵌入模型，如`text-embedding-3-small`
3. SiliconFlow：使用SiliconFlow的嵌入模型，如`embe-medium`

通过`.env`文件中的`EMBEDDING_PROVIDER`配置项选择提供商。

### LLM模型配置

系统支持三种LLM提供商：

1. DeepSeek（默认）：如`deepseek-chat`
2. OpenAI：如`gpt-3.5-turbo`或`gpt-4-turbo`
3. SiliconFlow：如`sf-llama3-70b-chat`

通过`.env`文件中的`LLM_PROVIDER`配置项选择提供商。

### 向量数据库配置

系统默认使用Qdrant作为向量数据库。可以通过`.env`文件中的`QDRANT_URL`配置连接地址，默认为`http://localhost:6333`。

### 调试模式

通过`.env`文件中的`DEBUG`配置项可以开启或关闭调试模式。开启调试模式后，系统会输出更多的日志信息，有助于排查问题。

## 故障排除

### 常见问题

1. **连接Qdrant失败**

   ```
   Failed to connect to Qdrant at http://localhost:6333
   ```

   解决方案：确保Qdrant容器正在运行，并且URL配置正确。使用以下命令检查：

   ```bash
   docker ps | grep qdrant
   ```

2. **嵌入模型加载失败**

   ```
   Failed to load embedding model
   ```

   解决方案：确保已安装正确的依赖，如果使用本地模型，确保模型可以下载：

   ```bash
   pip install sentence-transformers
   ```

3. **API密钥无效**

   ```
   Invalid API key for provider
   ```

   解决方案：检查`.env`文件中的API密钥配置是否正确，并确保选择的提供商对应的API密钥已设置。

### 日志

系统日志位于项目根目录下的`app.log`文件中，可以通过以下命令查看：

```bash
tail -f app.log
```

Docker环境中的日志可以通过以下命令查看：

```bash
docker-compose logs -f
```

或者

```bash
docker logs api-deep-search
``` 