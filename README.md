# API Deep Search

这个项目使用向量数据库存储OpenAPI规范(OAS)文件，并使用deepseek大模型进行语义搜索。

## 功能

- 加载OpenAPI规范文件(JSON或YAML格式)
- 将API规范分解并存储到向量数据库中
- 使用deepseek大模型进行RAG(检索增强生成)检索
- 提供API端点进行查询和检索

## 安装

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

## 环境变量

在项目根目录创建`.env`文件：

```
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_API_KEY=your_openai_api_key  # 如果需要OpenAI嵌入
QDRANT_URL=your_qdrant_url  # 如果使用远程Qdrant服务
```

## 使用方法

1. 启动服务:

```bash
python app.py
```

2. 访问API文档: http://localhost:8000/docs 