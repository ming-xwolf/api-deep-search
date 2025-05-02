"""
示例脚本：加载OpenAPI规范
"""
import os
import json
import asyncio
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.openapi_parser import OpenAPIParser
from app.services.oas_rag_service import OASRAGService

async def load_example_spec():
    """
    加载示例API规范
    """
    print("加载示例API规范...")
    
    # 加载示例文件
    with open("app/data/example_openapi.json", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 解析OpenAPI规范
    spec_data = json.loads(content)
    api_spec = OpenAPIParser.parse_openapi_spec(spec_data)
    
    print(f"已加载API规范: {api_spec.title} v{api_spec.version}")
    print(f"端点数量: {len(api_spec.endpoints)}")
    
    # 存储到向量数据库
    rag_service = OASRAGService()
    rag_service.store_api_spec(api_spec)
    
    print("规范已存储到向量数据库")
    
    # 示例查询
    results = rag_service.search_by_version(query="如何获取用户列表", top_k=3)
    
    print("\n示例查询结果:")
    for i, result in enumerate(results, 1):
        print(f"\n【结果 {i}】")
        print(f"相关度: {result.get('score', 0):.4f}")
        print(f"路径: {result.get('path', 'N/A')}")
        print(f"方法: {result.get('method', 'N/A')}")
        print(f"API: {result.get('api_title', 'N/A')} v{result.get('api_version', 'N/A')}")
        
        endpoint = result.get('endpoint')
        if endpoint and endpoint.get('summary'):
            print(f"摘要: {endpoint.get('summary')}")

if __name__ == "__main__":
    # 运行异步函数
    asyncio.run(load_example_spec()) 