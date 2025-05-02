import unittest
from unittest import mock
from io import BytesIO
import zipfile
import json
from fastapi.testclient import TestClient

from app.main import app
from app.services.api_detector_service import APIDetectorService


class TestAPIDetector(unittest.TestCase):
    """测试API检测功能"""
    
    def setUp(self):
        self.client = TestClient(app)
        self.service = APIDetectorService()
    
    @mock.patch('app.services.api_detector_service.APIDetectorService.process_github_repo')
    def test_detect_from_github_url(self, mock_process):
        """测试从GitHub URL检测API"""
        # 模拟检测结果
        mock_result = {
            "message": "检测完成，发现 5 个API端点",
            "repository": "https://github.com/testuser/testrepo",
            "branch": "main",
            "api_types": ["REST", "GraphQL"],
            "api_count": 5,
            "apis": [
                {
                    "type": "REST",
                    "path": "/api/users",
                    "file": "src/controllers/user_controller.js",
                    "line": 10
                }
            ]
        }
        mock_process.return_value = {
            "repository": "https://github.com/testuser/testrepo",
            "branch": "main",
            "api_types": ["REST", "GraphQL"],
            "api_count": 5,
            "apis": [
                {
                    "type": "REST",
                    "path": "/api/users",
                    "file": "src/controllers/user_controller.js",
                    "line": 10
                }
            ]
        }
        
        # 发送请求
        response = self.client.post(
            "/api/api_detector/detect_from_github",
            json={"github_url": "https://github.com/testuser/testrepo"}
        )
        
        # 检查结果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["repository"], "https://github.com/testuser/testrepo")
        self.assertEqual(data["api_count"], 5)
        mock_process.assert_called_once_with(
            github_url="https://github.com/testuser/testrepo",
            branch=None,
            use_http_download=False
        )
    
    @mock.patch('app.services.api_detector_service.APIDetectorService.process_github_repo')
    def test_detect_from_github_with_branch(self, mock_process):
        """测试从GitHub URL检测API并指定分支"""
        mock_process.return_value = {
            "repository": "https://github.com/testuser/testrepo",
            "branch": "develop",
            "api_types": [],
            "api_count": 0,
            "apis": []
        }
        
        response = self.client.post(
            "/api/api_detector/detect_from_github",
            json={
                "github_url": "https://github.com/testuser/testrepo",
                "branch": "develop",
                "use_http_download": True
            }
        )
        
        self.assertEqual(response.status_code, 200)
        mock_process.assert_called_once_with(
            github_url="https://github.com/testuser/testrepo",
            branch="develop",
            use_http_download=True
        )
    
    @mock.patch('app.services.api_detector_service.APIDetectorService.process_zip_file')
    def test_process_zip_file(self, mock_process):
        """测试处理ZIP文件"""
        # 模拟响应
        mock_process.return_value = {
            "api_types": ["REST"],
            "api_count": 3,
            "apis": [
                {"type": "REST", "path": "/api/test", "file": "test.py", "line": 10}
            ]
        }
        
        # 创建测试ZIP文件
        test_zip_content = BytesIO()
        with zipfile.ZipFile(test_zip_content, 'w') as test_zip:
            test_zip.writestr('test.py', 'print("Hello World")')
        test_zip_content.seek(0)
        
        # 发送请求
        response = self.client.post(
            "/api/api_detector/detect",
            files={"file": ("test.zip", test_zip_content, "application/zip")}
        )
        
        # 检查结果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["api_count"], 3)
        self.assertEqual(data["api_types"], ["REST"])
    
    def test_get_supported_types(self):
        """测试获取支持的API类型"""
        response = self.client.get("/api/api_detector/supported_types")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("supported_types", data)
        self.assertIn("supported_languages", data)
        
        # 检查返回的API类型列表
        api_types = [t["name"] for t in data["supported_types"]]
        self.assertIn("REST", api_types)
        self.assertIn("WebSocket", api_types)
        self.assertIn("gRPC", api_types)
        self.assertIn("GraphQL", api_types)
        self.assertIn("OpenAPI", api_types) 