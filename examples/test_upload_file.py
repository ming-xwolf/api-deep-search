import os
import sys
import requests
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

def test_upload_file(file_path):
    """测试文件上传API
    
    Args:
        file_path: 要上传的文件路径
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在!")
        return
    
    # 准备上传请求
    url = "http://localhost:8000/api/upload_file"
    
    # 获取文件名
    filename = os.path.basename(file_path)
    print(f"正在上传文件: {filename}")
    
    # 使用multipart/form-data上传文件
    files = {"file": (filename, open(file_path, "rb"), "application/json")}
    
    try:
        # 发送请求
        response = requests.post(url, files=files)
        response.raise_for_status()  # 检查响应状态码
        
        # 打印响应
        result = response.json()
        print("\n上传成功!")
        print(f"消息: {result.get('message')}")
        print(f"文件路径: {result.get('file_path')}")
        
    except requests.exceptions.RequestException as e:
        print(f"上传失败: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                print(f"错误详情: {error_detail}")
            except:
                print(f"响应状态码: {e.response.status_code}")
                print(f"响应内容: {e.response.text}")

if __name__ == "__main__":
    # 使用示例OpenAPI规范文件
    if len(sys.argv) > 1:
        # 如果提供了命令行参数，使用第一个参数作为文件路径
        file_path = sys.argv[1]
    else:
        # 默认使用examples目录下的示例文件
        example_file = os.path.join(os.path.dirname(__file__), "petstore.json")
        if not os.path.exists(example_file):
            print("示例文件不存在。请创建examples/petstore.json或指定一个API规范文件路径。")
            print("用法: python test_upload_file.py [文件路径]")
            sys.exit(1)
        file_path = example_file
    
    test_upload_file(file_path) 