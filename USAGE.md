# API Deep Search 使用指南

## 环境设置

1. 确保安装Python 3.8+
2. 安装依赖
   ```bash
   pip install -r requirements.txt
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
   
   # 嵌入配置
   EMBEDDING_PROVIDER=local  # 可选值: local, openai, siliconflow
   EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5  # 本地嵌入模型
   SILICONFLOW_EMBEDDING_MODEL=embe-medium  # SiliconFlow嵌入模型
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # OpenAI嵌入模型
   
   QDRANT_URL=http://localhost:6333  # 如果使用远程Qdrant服务
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
      "parameters": [...]
    }
  ],
  "answer": "要获取用户列表，你可以使用GET方法访问/users端点..."
}
```

## 高级配置

在`app/config/settings.py`中可以配置:

1. 嵌入模型: 
   - 提供商: 支持本地模型(`local`)、OpenAI(`openai`)和SiliconFlow(`siliconflow`)
   - 本地模型: 默认使用`BAAI/bge-large-zh-v1.5`
   - OpenAI模型: 默认使用`text-embedding-3-small`(1536维)
   - SiliconFlow模型: 默认使用`embe-medium`(1024维)

2. 大模型配置: 
   - 模型: 默认使用`deepseek-ai/deepseek-coder-33b-instruct`
   - API基础URL: 默认为`https://api.deepseek.com/v1`

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