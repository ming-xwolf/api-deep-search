"""
API检测服务，用于检测代码库中存在的API类型和定义
支持多种编程语言和API类型：REST、WebSocket、gRPC等
"""

import os
import re
import json
import yaml
from typing import Dict, List, Any, Optional, Set, Tuple
import glob
import zipfile
import tempfile
import shutil
import subprocess
import httpx
from pathlib import Path

class APIDetector:
    """API检测器基类"""
    
    def __init__(self):
        self.name = "基础检测器"
        self.description = "检测基础API模式"
        self.supported_extensions = []
    
    def detect(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检测文件中的API
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            List[Dict[str, Any]]: 检测到的API列表
        """
        return []
    
    def can_process(self, file_path: str) -> bool:
        """检查是否可以处理该文件"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_extensions

class RestAPIDetector(APIDetector):
    """REST API检测器"""
    
    def __init__(self):
        super().__init__()
        self.name = "REST API检测器"
        self.description = "检测REST API端点"
        # 支持多种编程语言
        self.supported_extensions = ['.py', '.js', '.ts', '.java', '.go', '.php', '.rb', '.cs']
        
        # 各种框架的API路由模式
        self.patterns = {
            # Python (FastAPI, Flask, Django)
            '.py': [
                # FastAPI
                r'@\w+\.(?:get|post|put|delete|patch|head|options)\s*\(\s*[\'"]([^\'"]+)[\'"]',
                # Flask
                r'@\w+\.route\s*\(\s*[\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?',
                # Django
                r'path\s*\(\s*[\'"]([^\'"]+)[\'"](?:,\s*\w+\.as_view\(\))?'
            ],
            # JavaScript/TypeScript (Express, NestJS)
            '.js': [
                r'(?:app|router)\.(?:get|post|put|delete|patch|use)\s*\(\s*[\'"]([^\'"]+)[\'"]',
                r'@(?:Get|Post|Put|Delete|Patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'
            ],
            '.ts': [
                r'(?:app|router)\.(?:get|post|put|delete|patch|use)\s*\(\s*[\'"]([^\'"]+)[\'"]',
                r'@(?:Get|Post|Put|Delete|Patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'
            ],
            # Java (Spring)
            '.java': [
                r'@(?:RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*(?:value\s*=\s*)?[\'"]([^\'"]+)[\'"]'
            ],
            # Go
            '.go': [
                r'(?:r|router|mux)\.(?:Handle|HandleFunc)\s*\(\s*[\'"]([^\'"]+)[\'"]',
                r'(?:r|router|mux)\.(?:GET|POST|PUT|DELETE|PATCH)\s*\(\s*[\'"]([^\'"]+)[\'"]'
            ],
            # PHP
            '.php': [
                r'\$(?:app|router)->(?:get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'
            ],
            # Ruby (Rails)
            '.rb': [
                r'(?:get|post|put|delete|patch)\s+[\'"]([^\'"]+)[\'"]'
            ],
            # C# (.NET)
            '.cs': [
                r'\[(?:HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch|Route)\s*\(\s*(?:template:\s*)?[\'"]([^\'"]+)[\'"]'
            ]
        }
    
    def detect(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检测REST API端点"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.patterns:
            return []
        
        api_endpoints = []
        patterns = self.patterns.get(ext, [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                route = match.group(1)
                api_endpoints.append({
                    "type": "REST",
                    "path": route,
                    "file": file_path,
                    "line": content[:match.start()].count('\n') + 1
                })
        
        return api_endpoints

class WebSocketDetector(APIDetector):
    """WebSocket API检测器"""
    
    def __init__(self):
        super().__init__()
        self.name = "WebSocket检测器"
        self.description = "检测WebSocket端点"
        self.supported_extensions = ['.py', '.js', '.ts', '.java', '.go', '.php', '.rb', '.cs']
        
        self.patterns = {
            # Python
            '.py': [
                r'@\w+\.websocket\s*\(\s*[\'"]([^\'"]+)[\'"]',
                r'WebSocketApp\s*\(\s*[\'"]([^\'"]+)[\'"]'
            ],
            # JavaScript/TypeScript
            '.js': [
                r'new WebSocket\s*\(\s*[\'"](?:wss?://)?([^\'"]+)[\'"]',
                r'@WebSocketGateway\s*\(\s*(?:path\s*:\s*)?[\'"]([^\'"]+)[\'"]'
            ],
            '.ts': [
                r'new WebSocket\s*\(\s*[\'"](?:wss?://)?([^\'"]+)[\'"]',
                r'@WebSocketGateway\s*\(\s*(?:path\s*:\s*)?[\'"]([^\'"]+)[\'"]'
            ],
            # Java
            '.java': [
                r'@ServerEndpoint\s*\(\s*[\'"]([^\'"]+)[\'"]'
            ],
            # Go
            '.go': [
                r'websocket\.Upgrade\s*\(',
                r'upgrader\.Upgrade\s*\('
            ],
            # 其他语言...
        }
    
    def detect(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检测WebSocket端点"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.patterns:
            return []
        
        api_endpoints = []
        patterns = self.patterns.get(ext, [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                try:
                    route = match.group(1) if len(match.groups()) > 0 else "未指定路径"
                    api_endpoints.append({
                        "type": "WebSocket",
                        "path": route,
                        "file": file_path,
                        "line": content[:match.start()].count('\n') + 1
                    })
                except IndexError:
                    # 如果没有捕获组，则表示检测到了WebSocket但未指定路径
                    api_endpoints.append({
                        "type": "WebSocket",
                        "path": "未指定路径",
                        "file": file_path,
                        "line": content[:match.start()].count('\n') + 1
                    })
        
        return api_endpoints

class GrpcDetector(APIDetector):
    """gRPC API检测器"""
    
    def __init__(self):
        super().__init__()
        self.name = "gRPC检测器"
        self.description = "检测gRPC服务和方法"
        self.supported_extensions = ['.proto', '.py', '.js', '.ts', '.java', '.go', '.php', '.rb', '.cs']
    
    def detect(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检测gRPC服务和方法"""
        ext = os.path.splitext(file_path)[1].lower()
        
        api_endpoints = []
        
        # 特别处理.proto文件 - 直接解析定义
        if ext == '.proto':
            # 服务定义
            service_matches = re.finditer(r'service\s+(\w+)\s*{([^}]+)}', content)
            for service_match in service_matches:
                service_name = service_match.group(1)
                service_content = service_match.group(2)
                
                # 方法定义
                method_matches = re.finditer(r'rpc\s+(\w+)\s*\(([^)]+)\)\s*returns\s*\(([^)]+)\)', service_content)
                for method_match in method_matches:
                    method_name = method_match.group(1)
                    request_type = method_match.group(2).strip()
                    response_type = method_match.group(3).strip()
                    
                    api_endpoints.append({
                        "type": "gRPC",
                        "service": service_name,
                        "method": method_name,
                        "request": request_type,
                        "response": response_type,
                        "file": file_path,
                        "line": content[:method_match.start() + service_match.start()].count('\n') + 1
                    })
        
        # 检测各种语言中的gRPC实现
        else:
            # 检测gRPC服务实现
            if ext == '.py':
                # Python gRPC服务器实现
                server_matches = re.finditer(r'add_(\w+)_servicer_to_server\(', content)
                for match in server_matches:
                    service_name = match.group(1)
                    api_endpoints.append({
                        "type": "gRPC",
                        "service": service_name,
                        "file": file_path,
                        "line": content[:match.start()].count('\n') + 1
                    })
            
            elif ext in ['.js', '.ts']:
                # Node.js gRPC服务器实现
                server_matches = re.finditer(r'server\.addService\((\w+)\.service', content)
                for match in server_matches:
                    service_name = match.group(1)
                    api_endpoints.append({
                        "type": "gRPC",
                        "service": service_name,
                        "file": file_path,
                        "line": content[:match.start()].count('\n') + 1
                    })
            
            elif ext == '.go':
                # Go gRPC服务器实现
                server_matches = re.finditer(r'Register(\w+)Server\(', content)
                for match in server_matches:
                    service_name = match.group(1)
                    api_endpoints.append({
                        "type": "gRPC",
                        "service": service_name,
                        "file": file_path,
                        "line": content[:match.start()].count('\n') + 1
                    })
            
            elif ext == '.java':
                # Java gRPC服务器实现
                server_matches = re.finditer(r'\.addService\(\s*new\s+(\w+)\(', content)
                for match in server_matches:
                    service_name = match.group(1)
                    api_endpoints.append({
                        "type": "gRPC",
                        "service": service_name,
                        "file": file_path,
                        "line": content[:match.start()].count('\n') + 1
                    })
        
        return api_endpoints

class GraphQLDetector(APIDetector):
    """GraphQL API检测器"""
    
    def __init__(self):
        super().__init__()
        self.name = "GraphQL检测器"
        self.description = "检测GraphQL架构和解析器"
        self.supported_extensions = ['.graphql', '.gql', '.py', '.js', '.ts', '.java']
    
    def detect(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检测GraphQL服务"""
        ext = os.path.splitext(file_path)[1].lower()
        api_endpoints = []
        
        # .graphql/.gql文件 - 直接解析定义
        if ext in ['.graphql', '.gql']:
            # 查询类型定义
            type_matches = re.finditer(r'type\s+(\w+)\s*{([^}]+)}', content)
            for type_match in type_matches:
                type_name = type_match.group(1)
                if type_name in ['Query', 'Mutation', 'Subscription']:
                    type_content = type_match.group(2)
                    
                    # 字段定义
                    field_matches = re.finditer(r'(\w+)(?:\([^)]*\))?\s*:\s*([^\n]+)', type_content)
                    for field_match in field_matches:
                        field_name = field_match.group(1)
                        field_type = field_match.group(2).strip()
                        
                        api_endpoints.append({
                            "type": "GraphQL",
                            "operation": type_name.lower(),
                            "field": field_name,
                            "return_type": field_type,
                            "file": file_path,
                            "line": content[:field_match.start() + type_match.start()].count('\n') + 1
                        })
        
        # 检测各种语言中的GraphQL实现
        else:
            # 通用GraphQL库调用
            if ext in ['.py', '.js', '.ts', '.java']:
                graphql_patterns = [
                    r'new GraphQLSchema\(', 
                    r'makeExecutableSchema\(',
                    r'typeDefs\s*=',
                    r'gql\s*`',
                    r'graphene\.Schema\('
                ]
                
                for pattern in graphql_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        api_endpoints.append({
                            "type": "GraphQL",
                            "note": "检测到GraphQL架构定义",
                            "file": file_path,
                            "line": content[:match.start()].count('\n') + 1
                        })
        
        return api_endpoints

class SwaggerDetector(APIDetector):
    """Swagger/OpenAPI检测器"""
    
    def __init__(self):
        super().__init__()
        self.name = "Swagger/OpenAPI检测器"
        self.description = "检测Swagger和OpenAPI定义文件"
        self.supported_extensions = ['.json', '.yaml', '.yml']
    
    def can_process(self, file_path: str) -> bool:
        """检查是否可以处理该文件"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.supported_extensions:
            return False
            
        # 检查文件名是否符合OpenAPI命名惯例
        basename = os.path.basename(file_path).lower()
        if any(name in basename for name in ['swagger', 'openapi', 'api']):
            return True
            
        # 尝试读取文件前几行检查是否包含openapi或swagger标识
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # 只读取前1KB内容
                return 'swagger' in content.lower() or 'openapi' in content.lower()
        except:
            return False
    
    def detect(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检测Swagger和OpenAPI定义文件"""
        ext = os.path.splitext(file_path)[1].lower()
        api_endpoints = []
        
        try:
            # 根据文件类型解析内容
            if ext == '.json':
                spec = json.loads(content)
            else:  # .yaml或.yml
                spec = yaml.safe_load(content)
            
            # 确定是否是OpenAPI规范
            spec_version = None
            if 'swagger' in spec:
                spec_version = f"Swagger {spec['swagger']}"
            elif 'openapi' in spec:
                spec_version = f"OpenAPI {spec['openapi']}"
            else:
                return []  # 不是OpenAPI规范
            
            api_info = {
                "type": "OpenAPI",
                "version": spec_version,
                "title": spec.get('info', {}).get('title', 'Unknown API'),
                "description": spec.get('info', {}).get('description', ''),
                "file": file_path
            }
            
            # 提取API端点
            paths = spec.get('paths', {})
            endpoints = []
            
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                        endpoints.append({
                            "path": path,
                            "method": method.upper(),
                            "summary": details.get('summary', ''),
                            "description": details.get('description', '')
                        })
            
            api_info["endpoints"] = endpoints
            api_endpoints.append(api_info)
            
        except Exception as e:
            # 解析错误，可能不是有效的OpenAPI文件
            pass
        
        return api_endpoints

class APIDetectorService:
    """API检测服务"""
    
    def __init__(self):
        self.detectors = [
            RestAPIDetector(),
            WebSocketDetector(),
            GrpcDetector(),
            GraphQLDetector(),
            SwaggerDetector()
        ]
    
    def process_zip_file(self, zip_file_path: str) -> Dict[str, Any]:
        """处理上传的ZIP文件
        
        Args:
            zip_file_path: ZIP文件路径
            
        Returns:
            Dict[str, Any]: 检测结果
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 解压ZIP文件
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 扫描解压后的目录
            return self.scan_directory(temp_dir)
        
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
    
    def scan_directory(self, directory_path: str) -> Dict[str, Any]:
        """扫描目录中的所有文件
        
        Args:
            directory_path: 目录路径
            
        Returns:
            Dict[str, Any]: 检测结果
        """
        result = {
            "api_count": 0,
            "api_types": set(),
            "apis": []
        }
        
        # 收集所有文件
        all_files = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        
        # 处理每个文件
        for file_path in all_files:
            relative_path = os.path.relpath(file_path, directory_path)
            
            # 跳过二进制文件和一些不相关的文件类型
            if self._should_skip_file(file_path):
                continue
            
            # 查找适合的检测器
            for detector in self.detectors:
                if detector.can_process(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # 检测API
                        apis = detector.detect(relative_path, content)
                        if apis:
                            # 更新相对路径
                            for api in apis:
                                api["file"] = relative_path
                                result["apis"].append(api)
                                result["api_count"] += 1
                                if "type" in api:
                                    result["api_types"].add(api["type"])
                    except Exception as e:
                        # 忽略读取或处理错误
                        continue
        
        # 将集合转换为列表以便JSON序列化
        result["api_types"] = list(result["api_types"])
        
        return result
    
    def get_supported_types(self) -> Dict[str, Any]:
        """获取支持的API类型列表
        
        Returns:
            Dict[str, Any]: 支持的API类型和语言列表
        """
        return {
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
    
    def _should_skip_file(self, file_path: str) -> bool:
        """判断是否应该跳过该文件"""
        # 跳过二进制文件和一些与API无关的文件类型
        ignore_extensions = [
            '.exe', '.dll', '.so', '.dylib', '.jar', '.war', '.ear',
            '.class', '.pyc', '.jpg', '.jpeg', '.png', '.gif', '.svg',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.tar',
            '.gz', '.rar', '.7z', '.mp3', '.mp4', '.avi', '.mov',
            '.sqlite', '.db'
        ]
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ignore_extensions:
            return True
        
        # 跳过隐藏文件和目录
        parts = Path(file_path).parts
        for part in parts:
            if part.startswith('.'):
                return True
        
        # 跳过常见的不相关目录
        ignore_dirs = ['node_modules', 'venv', '.git', '.svn', '.hg', '__pycache__', 'dist', 'build']
        for ignore_dir in ignore_dirs:
            if f'/{ignore_dir}/' in file_path or file_path.endswith(f'/{ignore_dir}'):
                return True
        
        return False
    
    def process_github_repo(self, github_url: str, branch: Optional[str] = None, use_http_download: bool = False) -> Dict[str, Any]:
        """从GitHub仓库URL检测API
        
        Args:
            github_url: GitHub仓库URL，格式如 https://github.com/username/repo
            branch: 要检测的分支名称，默认为仓库的默认分支
            use_http_download: 是否使用HTTP下载ZIP而不是git克隆，默认为False
            
        Returns:
            Dict[str, Any]: 检测结果
            
        Raises:
            ValueError: 当GitHub URL格式不正确或仓库不存在时
            RuntimeError: 当克隆或下载失败时
        """
        # 创建临时目录用于克隆仓库
        temp_dir = None
        scan_dir = None
        
        try:
            # 验证GitHub URL格式
            if not github_url.startswith("https://github.com/"):
                raise ValueError("请提供有效的GitHub仓库URL，格式为 https://github.com/username/repo")
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            print(f"创建临时目录: {temp_dir}")
            
            # 解析GitHub用户名和仓库名
            _, _, _, username, repo = github_url.rstrip('/').split('/')
            
            if use_http_download:
                scan_dir = self._download_github_repo(username, repo, branch, temp_dir)
            else:
                scan_dir = self._clone_github_repo(github_url, branch, temp_dir)
            
            print(f"开始扫描目录: {scan_dir}")
            # 扫描仓库目录
            result = self.scan_directory(scan_dir)
            print(f"扫描完成，发现 {result['api_count']} 个API端点")
            
            # 添加仓库信息
            result["repository"] = github_url
            result["branch"] = branch or "默认分支"
            
            return result
            
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                print(f"清理临时目录: {temp_dir}")
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    print(f"清理临时目录时出错: {str(e)}")
    
    def _clone_github_repo(self, github_url: str, branch: Optional[str], temp_dir: str) -> str:
        """使用git命令克隆GitHub仓库
        
        Args:
            github_url: GitHub仓库URL
            branch: 分支名称
            temp_dir: 临时目录路径
            
        Returns:
            str: 扫描目录路径
            
        Raises:
            RuntimeError: 当克隆失败时
        """
        # 构建git clone命令
        clone_cmd = ["git", "clone"]
        
        # 如果指定了分支，添加分支参数
        if branch:
            clone_cmd.extend(["-b", branch])
        
        # 添加深度参数，减少下载量
        clone_cmd.extend(["--depth", "1"])
        
        # 添加仓库URL和目标目录
        clone_cmd.extend([github_url, temp_dir])
        
        print(f"执行命令: {' '.join(clone_cmd)}")
        
        # 执行克隆命令
        process = subprocess.Popen(
            clone_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        
        stdout_str = stdout.decode('utf-8', errors='ignore') if stdout else ""
        stderr_str = stderr.decode('utf-8', errors='ignore') if stderr else ""
        
        print(f"命令返回码: {process.returncode}")
        if stdout_str:
            print(f"标准输出: {stdout_str}")
        if stderr_str:
            print(f"标准错误: {stderr_str}")
        
        if process.returncode != 0:
            raise RuntimeError(f"仓库克隆失败: {stderr_str}")
        
        # 检查目录是否为空
        if not os.listdir(temp_dir):
            raise RuntimeError("仓库克隆成功但目录为空")
            
        # 在git克隆模式下，直接使用temp_dir作为扫描目录
        return temp_dir
    
    def _download_github_repo(self, username: str, repo: str, branch: Optional[str], temp_dir: str) -> str:
        """通过HTTP下载GitHub仓库ZIP文件
        
        Args:
            username: GitHub用户名
            repo: 仓库名称
            branch: 分支名称
            temp_dir: 临时目录路径
            
        Returns:
            str: 扫描目录路径
            
        Raises:
            RuntimeError: 当下载或解压失败时
        """
        # 使用HTTP下载ZIP文件
        print(f"使用HTTP下载仓库: {username}/{repo}")
        
        # 构建下载URL（使用默认分支或指定分支）
        zip_branch = branch or 'main'
        download_url = f"https://github.com/{username}/{repo}/archive/refs/heads/{zip_branch}.zip"
        
        print(f"下载URL: {download_url}")
        
        try:
            # 下载ZIP文件（使用同步客户端，启用重定向跟随）
            with httpx.Client(timeout=60, follow_redirects=True) as client:
                response = client.get(download_url)
                response.raise_for_status()  # 如果请求失败则抛出异常
                
            # 将内容保存到临时ZIP文件
            zip_content = response.content
            zip_file_path = os.path.join(temp_dir, "repo.zip")
            with open(zip_file_path, 'wb') as f:
                f.write(zip_content)
                
            print(f"下载完成，ZIP大小: {len(zip_content)} 字节")
            
            # 解压ZIP文件到临时目录
            print(f"开始解压ZIP文件: {zip_file_path}")
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            # 删除ZIP文件
            os.unlink(zip_file_path)
            
            # 查找解压后的主目录
            extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
            if not extracted_dirs:
                raise RuntimeError("ZIP文件解压成功但未找到目录")
            
            # 使用第一个目录作为工作目录
            scan_dir = os.path.join(temp_dir, extracted_dirs[0])
            print(f"解压完成，扫描目录: {scan_dir}")
            return scan_dir
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # 尝试使用master分支
                if zip_branch != 'master':
                    print(f"分支 {zip_branch} 不存在，尝试使用master分支")
                    return self._download_github_repo(username, repo, 'master', temp_dir)
                else:
                    raise RuntimeError(f"仓库或分支不存在: {username}/{repo}/{zip_branch}")
            else:
                raise RuntimeError(f"下载仓库失败: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"处理仓库ZIP文件时出错: {str(e)}") 