"""
示例脚本：搜索API
"""
import os
import sys
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.oas_rag_service import OASRAGService

async def search_api():
    """
    搜索API并使用大模型生成回答
    """
    # 初始化服务
    rag_service = OASRAGService()
    
    # 获取用户查询
    query = input("请输入你的API查询问题: ")
    
    if not query:
        print("查询不能为空")
        return
    
    print("\n正在搜索相关API...")
    
    # 搜索并生成回答
    result = rag_service.search(query)
    
    if not result.get("sources"):
        print("未找到相关API信息")
        return
    
    # 显示搜索结果
    search_results = result.get("sources", [])
    print("\n找到以下相关API:")
    for i, src in enumerate(search_results, 1):
        path = src.get('path', 'N/A')
        method = src.get('method', 'N/A')
        score = src.get('score', 0)
        title = src.get('api_title', 'Unknown API')
        
        endpoint = src.get('endpoint', {})
        summary = endpoint.get('summary') if endpoint else 'N/A'
        
        print(f"\n{i}. {method} {path} (相关度: {score:.4f})")
        print(f"   API: {title}")
        print(f"   摘要: {summary}")
    
    # 显示回答
    answer = result.get("answer", "无法生成回答")
    print("\n回答:")
    print("-" * 80)
    print(answer)
    print("-" * 80)

if __name__ == "__main__":
    # 运行异步函数
    asyncio.run(search_api()) 