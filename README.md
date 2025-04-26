# API Deep Search

这个项目使用向量数据库存储OpenAPI规范(OAS)文件，并使用deepseek大模型进行语义搜索。

## 功能

- 加载OpenAPI规范文件(JSON或YAML格式)
- 将API规范分解并存储到向量数据库中
- 将API规范原文件保存到磁盘，便于追踪和管理
- 使用deepseek大模型进行RAG(检索增强生成)检索
- 提供API端点进行查询和检索
- 支持一键清理向量数据库和磁盘文件
- 支持删除单个API规范文件及其对应的向量嵌入

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

3. 主要功能:
   - 上传API规范: `/api/upload` 接口
   - 搜索API接口: `/api/search` 接口
   - 列出文件: `/api/files` 接口
   - 清理所有数据: `/api/clean` 接口
   - 删除单个文件: `/api/delete` 接口

详细使用方法请参考 [USAGE.md](USAGE.md) 