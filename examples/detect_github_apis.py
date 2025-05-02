#!/usr/bin/env python
"""
GitHub API检测示例

此示例演示如何使用API检测功能从GitHub仓库URL检测API定义。
"""

import sys
import json
import requests
import argparse

# 默认API服务URL
DEFAULT_API_URL = "http://localhost:8000"

def detect_apis_from_github(github_url, branch=None, use_http_download=True, api_url=DEFAULT_API_URL):
    """从GitHub仓库URL检测API
    
    Args:
        github_url: GitHub仓库URL
        branch: 要检测的分支名称，默认为仓库的默认分支
        use_http_download: 是否使用HTTP下载ZIP，默认为True
        api_url: API服务URL
        
    Returns:
        dict: 检测结果
    """
    endpoint = f"{api_url}/api/api_detector/detect_from_github"
    
    # 准备请求数据
    data = {
        "github_url": github_url
    }
    
    if branch:
        data["branch"] = branch
        
    data["use_http_download"] = use_http_download
    
    try:
        # 发送POST请求
        response = requests.post(endpoint, json=data)
        response.raise_for_status()
        
        # 返回解析后的JSON结果
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"错误: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                print(f"API错误: {error_data.get('detail', str(e))}")
            except:
                print(f"状态码: {e.response.status_code}, 响应: {e.response.text}")
        sys.exit(1)

def get_supported_types(api_url=DEFAULT_API_URL):
    """获取支持的API类型列表
    
    Args:
        api_url: API服务URL
        
    Returns:
        dict: 支持的API类型和编程语言列表
    """
    endpoint = f"{api_url}/api/api_detector/supported_types"
    
    try:
        # 发送GET请求
        response = requests.get(endpoint)
        response.raise_for_status()
        
        # 返回解析后的JSON结果
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"错误: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"状态码: {e.response.status_code}, 响应: {e.response.text}")
        sys.exit(1)

def print_result(result):
    """打印检测结果
    
    Args:
        result: 检测结果字典
    """
    print("\n===== API检测结果 =====")
    print(f"仓库: {result.get('repository')}")
    print(f"分支: {result.get('branch')}")
    print(f"发现API数量: {result.get('api_count')}")
    print(f"API类型: {', '.join(result.get('api_types', []))}")
    
    # 打印发现的API
    apis = result.get('apis', [])
    if apis:
        print("\n发现的API:")
        for i, api in enumerate(apis, 1):
            api_type = api.get('type', '未知')
            
            if api_type == 'REST':
                print(f"{i}. [REST] {api.get('path')} - 文件: {api.get('file')}:{api.get('line')}")
            
            elif api_type == 'WebSocket':
                print(f"{i}. [WebSocket] {api.get('path')} - 文件: {api.get('file')}:{api.get('line')}")
                
            elif api_type == 'gRPC':
                service = api.get('service', '未知服务')
                method = api.get('method', '')
                if method:
                    print(f"{i}. [gRPC] {service}.{method} - 文件: {api.get('file')}:{api.get('line')}")
                else:
                    print(f"{i}. [gRPC] {service} - 文件: {api.get('file')}:{api.get('line')}")
                    
            elif api_type == 'GraphQL':
                operation = api.get('operation', '')
                field = api.get('field', '')
                if operation and field:
                    print(f"{i}. [GraphQL] {operation} {field} - 文件: {api.get('file')}:{api.get('line')}")
                else:
                    print(f"{i}. [GraphQL] - 文件: {api.get('file')}:{api.get('line')}")
                    
            elif api_type == 'OpenAPI':
                title = api.get('title', '未知API')
                version = api.get('version', '')
                endpoints_count = len(api.get('endpoints', []))
                print(f"{i}. [OpenAPI] {title} {version} - {endpoints_count}个端点 - 文件: {api.get('file')}")
                
            else:
                print(f"{i}. [{api_type}] - 文件: {api.get('file')}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="从GitHub仓库URL检测API")
    parser.add_argument("github_url", help="GitHub仓库URL，格式如 https://github.com/username/repo")
    parser.add_argument("--branch", "-b", help="要检测的分支名称，默认为仓库的默认分支")
    parser.add_argument("--use-git", action="store_true", help="使用git克隆而不是HTTP下载")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help=f"API服务URL，默认为 {DEFAULT_API_URL}")
    parser.add_argument("--types", action="store_true", help="仅显示支持的API类型")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出结果")
    
    args = parser.parse_args()
    
    if args.types:
        # 获取支持的API类型列表
        supported_types = get_supported_types(args.api_url)
        
        if args.json:
            print(json.dumps(supported_types, indent=2))
        else:
            print("\n===== 支持的API类型 =====")
            for api_type in supported_types.get('supported_types', []):
                print(f"- {api_type['name']}: {api_type['description']}")
                
            print("\n===== 支持的编程语言 =====")
            for language in supported_types.get('supported_languages', []):
                print(f"- {language}")
        
        return
    
    # 从GitHub仓库URL检测API
    result = detect_apis_from_github(
        github_url=args.github_url,
        branch=args.branch,
        use_http_download=not args.use_git,
        api_url=args.api_url
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_result(result)

if __name__ == "__main__":
    main() 