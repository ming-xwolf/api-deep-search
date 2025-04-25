"""
示例脚本：搜索API
"""
import os
import sys
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService

async def search_api():
    """
    搜索API并使用大模型生成回答
    """
    # 初始化服务
    vector_store = VectorStore()
    llm_service = LLMService()
    
    # 获取用户查询
    query = input("请输入你的API查询问题: ")
    
    if not query:
        print("查询不能为空")
        return
    
    print("\n正在搜索相关API...")
    
    # 搜索向量数据库
    search_results = vector_store.search(query, top_k=3)
    
    if not search_results:
        print("未找到相关API信息")
        return
    
    # 显示搜索结果
    print("\n找到以下相关API:")
    for i, result in enumerate(search_results, 1):
        path = result.get('path', 'N/A')
        method = result.get('method', 'N/A')
        score = result.get('score', 0)
        title = result.get('api_title', 'Unknown API')
        
        endpoint = result.get('endpoint')
        summary = endpoint.summary if endpoint and endpoint.summary else 'N/A'
        
        print(f"\n{i}. {method} {path} (相关度: {score:.4f})")
        print(f"   API: {title}")
        print(f"   摘要: {summary}")
    
    print("\n正在生成回答...")
    
    # 使用大模型生成回答
    answer = llm_service.generate_answer(query, search_results)
    
    # 显示回答
    print("\n回答:")
    print("-" * 80)
    print(answer)
    print("-" * 80)

if __name__ == "__main__":
    # 运行异步函数
    asyncio.run(search_api()) 