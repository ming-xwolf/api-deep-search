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

3. 安装向量数据库（选择以下之一）：

   a. Qdrant向量数据库（通过Docker安装）:
   ```bash
   docker run -p 6333:6333 -p 6334:6334 -v ./qdrant_data:/qdrant/storage qdrant/qdrant
   ```

   b. PostgreSQL与pgvector扩展：
   ```bash
   # 安装PostgreSQL和pgvector扩展
   docker run -d \
     --name postgres-pgvector \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_DB=vector_db \
     -p 5432:5432 \
     pgvector/pgvector:pg16
   ```

   在数据库中创建pgvector扩展：
   ```bash
   # 连接到PostgreSQL
   psql -h localhost -U postgres -d vector_db
   
   # 创建pgvector扩展
   CREATE EXTENSION IF NOT EXISTS vector;
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
   
   # 向量数据库配置
   VECTOR_STORE_PROVIDER=qdrant  # 可选值: qdrant, faiss, pgvector
   
   # Qdrant配置（使用Qdrant时）
   QDRANT_URL=http://localhost:6333
   
   # FAISS配置（使用FAISS时）
   FAISS_INDEX_DIR=data/faiss_index
   
   # PostgreSQL配置（使用pgvector时）
   PG_CONNECTION_STRING=postgresql://postgres:postgres@localhost:5432/vectordb
   PG_TABLE_NAME=api_specs
   
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

#### 系统信息

```http
GET /api/info
```

此API将返回系统的配置信息，包括LLM、嵌入模型和向量存储的配置。

响应示例:

```json
{
  "llm": {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "temperature": 0.3,
    "max_tokens": 1000
  },
  "embedding": {
    "provider": "local",
    "model": "BAAI/bge-large-zh-v1.5",
    "dimension": 1024
  },
  "vector_store": {
    "provider": "pgvector",
    "embedding_dimension": 1024,
    "connection_string": "postgresql://postgres***:***@***",
    "table_name": "api_specs"
  }
}
```

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
POST /api/search_api_by_version
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
  "message": "成功清空向量数据库集合，并删除了 8/8 个磁盘文件"
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
      "file_type": "JSON",
      "api_title": "用户管理API",
      "api_version": "1.0.0",
      "openapi_version": "3.0.0"
    },
    {
      "file_name": "产品API_v2.0.0_20240515183012_e5f6g7h8.yaml",
      "file_path": "upload/产品API_v2.0.0_20240515183012_e5f6g7h8.yaml",
      "file_size": 18540,
      "file_size_human": "18.11 KB",
      "modified_time": "2024-05-15 18:30:12",
      "file_type": "YAML",
      "api_title": "产品API",
      "api_version": "2.0.0",
      "openapi_version": "3.1.0"
    }
  ],
  "total_count": 2,
  "total_size": 43220,
  "total_size_human": "42.21 KB"
}
```

响应内容包括:
- 文件列表（按修改时间降序排列，最新的在前）
- 每个文件的名称、路径、大小（字节数和人类可读格式）、修改时间、文件类型和API信息
- 总文件数量
- 总文件大小（字节数和人类可读格式）

#### 仅删除向量数据

```http
POST /api/delete_vector_by_file_name
Content-Type: application/json

{
  "file_name": "用户管理API_v1.0.0_20240516123045_a1b2c3d4.json"
}
```

此API将仅从向量数据库中删除与指定文件相关的向量数据，但不会删除磁盘上的文件。这在需要重新索引文件或修复向量数据问题时特别有用。

响应示例:

```json
{
  "message": "成功删除文件 用户管理API_v1.0.0_20240516123045_a1b2c3d4.json 对应的向量嵌入",
  "deleted_embeddings_count": 8
}
```

响应消息会显示成功删除的向量数据数量。

#### 按版本列出文件

```http
GET /api/files_by_version?openapi_version=3.0.0
```

此API将返回指定OpenAPI版本的API规范文件。如果不指定版本，则返回所有文件。

响应格式与`/api/files`接口相同，但只包含指定版本的文件，并额外返回`filtered_version`字段。

#### 健康检查

```http
GET /api/health
```

此API用于检查服务是否正常运行。

响应示例:

```json
{
  "status": "healthy"
}
```

#### API检测功能

API检测功能允许分析代码库中的API定义和实现，支持多种API类型的识别，包括REST API、WebSocket、gRPC、GraphQL和OpenAPI/Swagger规范。

##### 1. 检测代码库中的API（上传ZIP文件）

```http
POST /api_detector/detect
Content-Type: multipart/form-data

file=@/path/to/your/code.zip
```

此接口接受一个ZIP格式的代码库文件，系统会自动分析并检测其中包含的API类型和定义。

响应示例：

```json
{
  "message": "检测完成，发现 15 个API端点",
  "api_types": ["REST", "GraphQL"],
  "api_count": 15,
  "apis": [
    {
      "type": "REST",
      "path": "/users",
      "method": "GET",
      "file": "src/controllers/user_controller.js",
      "line": 12
    },
    {
      "type": "GraphQL",
      "operation": "Query.getUser",
      "file": "src/graphql/schema.js",
      "line": 25
    }
    // ...更多API端点
  ]
}
```

##### 2. 获取支持的API类型列表

```http
GET /api_detector/supported_types
```

此接口返回系统支持检测的所有API类型列表。

响应示例：

```json
[
  {
    "name": "REST",
    "description": "RESTful API端点，包括GET、POST、PUT、DELETE等HTTP方法"
  },
  {
    "name": "WebSocket",
    "description": "WebSocket连接和消息处理"
  },
  {
    "name": "gRPC",
    "description": "基于Protocol Buffers的gRPC服务定义"
  },
  {
    "name": "GraphQL",
    "description": "GraphQL查询和变更操作"
  },
  {
    "name": "OpenAPI",
    "description": "OpenAPI/Swagger规范文件"
  }
]
```

##### 3. 从GitHub仓库URL检测API

```http
POST /api_detector/detect_from_github
Content-Type: application/json

{
  "github_url": "https://github.com/username/repo",
  "branch": "main",
  "use_http_download": false
}
```

此接口接受一个GitHub仓库URL，系统会自动克隆仓库并检测其中包含的API类型和定义。参数说明：

- `github_url`：GitHub仓库URL，格式如 https://github.com/username/repo
- `branch`：要检测的分支名称，默认为仓库的默认分支（可选）
- `use_http_download`：是否使用HTTP下载ZIP而不是git克隆，默认为false（可选）

响应示例：

```json
{
  "message": "检测完成，发现 20 个API端点",
  "repository": "username/repo",
  "branch": "main",
  "api_types": ["REST", "gRPC", "OpenAPI"],
  "api_count": 20,
  "apis": [
    {
      "type": "REST",
      "path": "/api/products",
      "method": "GET",
      "file": "src/controllers/product_controller.js",
      "line": 8
    },
    {
      "type": "gRPC",
      "service": "ProductService",
      "method": "GetProduct",
      "file": "src/proto/product.proto",
      "line": 15
    },
    {
      "type": "OpenAPI",
      "path": "/api/users/{id}",
      "method": "GET",
      "file": "docs/openapi.yaml",
      "line": 42
    }
    // ...更多API端点
  ]
}
```

通过这些API检测接口，您可以快速分析任何代码库中的API实现，无需手动查找和整理API文档。

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

## API检测功能

系统支持从各种来源检测API定义，包括代码库文件和GitHub仓库。

### 检测支持的API类型

系统可以检测以下类型的API：

- **REST API**：检测各种框架中的REST端点定义，如FastAPI、Flask、Express等
- **WebSocket API**：检测WebSocket连接和服务端点
- **gRPC API**：检测gRPC服务和方法定义
- **GraphQL API**：检测GraphQL查询和变更
- **OpenAPI/Swagger**：检测OpenAPI规范文件

### 从ZIP文件检测API

您可以上传包含代码库的ZIP文件，系统会自动扫描并检测其中的API定义：

```http
POST /api/api_detector/detect
Content-Type: multipart/form-data

file=@/path/to/local/codebase.zip
```

响应示例:

```json
{
  "message": "检测完成，发现 15 个API端点",
  "api_types": ["REST", "WebSocket", "gRPC"],
  "api_count": 15,
  "apis": [
    {
      "type": "REST",
      "path": "/api/users",
      "file": "src/controllers/user_controller.js",
      "line": 24
    },
    {
      "type": "WebSocket",
      "path": "/ws/notifications",
      "file": "src/websocket/notification_service.js",
      "line": 18
    }
    // 更多API...
  ]
}
```

### 从GitHub仓库URL检测API

您可以直接从GitHub仓库URL检测API，无需手动下载和上传代码：

```http
POST /api/api_detector/detect_from_github
Content-Type: application/json

{
  "github_url": "https://github.com/username/repo",
  "branch": "main",
  "use_http_download": true
}
```

参数说明:
- `github_url`: GitHub仓库URL，必须以 "https://github.com/" 开头
- `branch`: 要检测的分支名称，可选，默认为仓库的默认分支
- `use_http_download`: 是否使用HTTP下载ZIP而不是git克隆，可选，默认为false

响应示例:

```json
{
  "message": "检测完成，发现 8 个API端点",
  "repository": "https://github.com/username/repo",
  "branch": "main",
  "api_types": ["REST", "GraphQL"],
  "api_count": 8,
  "apis": [
    {
      "type": "REST",
      "path": "/api/products",
      "file": "controllers/product_controller.js",
      "line": 15
    },
    {
      "type": "GraphQL",
      "operation": "query",
      "field": "getUser",
      "return_type": "User!",
      "file": "schema/user.graphql",
      "line": 10
    }
    // 更多API...
  ]
}
```

### 获取支持的API类型

获取系统支持检测的API类型和编程语言列表：

```http
GET /api/api_detector/supported_types
```

响应示例:

```json
{
  "supported_types": [
    {"name": "REST", "description": "RESTful API (HTTP GET/POST/PUT/DELETE等)"},
    {"name": "WebSocket", "description": "WebSocket API"},
    {"name": "gRPC", "description": "gRPC服务和方法"},
    {"name": "GraphQL", "description": "GraphQL查询和变更"},
    {"name": "OpenAPI", "description": "OpenAPI/Swagger规范"}
  ],
  "supported_languages": [
    "Python", "JavaScript", "TypeScript", "Java", 
    "Go", "PHP", "Ruby", "C#", "Protocol Buffers"
  ]
}
``` 