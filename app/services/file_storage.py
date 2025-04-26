import os
import uuid
import json
import yaml
import glob
import shutil
from datetime import datetime
from typing import Optional, List, Tuple
import chardet

class FileStorage:
    """文件存储服务，用于保存上传的API规范文件"""
    
    def __init__(self, upload_dir: str = "upload"):
        """初始化文件存储服务
        
        Args:
            upload_dir: 上传文件保存的目录
        """
        self.upload_dir = upload_dir
        self._ensure_upload_dir_exists()
    
    def _ensure_upload_dir_exists(self):
        """确保上传目录存在"""
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def _generate_file_name(self, 
                          api_title: Optional[str] = None, 
                          api_version: Optional[str] = None,
                          file_type: str = "json") -> str:
        """生成文件名
        
        Args:
            api_title: API标题
            api_version: API版本
            file_type: 文件类型
            
        Returns:
            生成的文件名
        """
        # 生成时间戳和唯一ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # 准备文件名部分
        filename_parts = []
        
        if api_title:
            # 替换不合法的文件名字符
            safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in api_title)
            filename_parts.append(safe_title)
        
        if api_version:
            filename_parts.append(f"v{api_version}")
        
        filename_parts.append(timestamp)
        filename_parts.append(unique_id)
        
        # 组合文件名
        return "_".join(filename_parts) + f".{file_type}"
    
    def save_api_spec(self, 
                     content: str, 
                     file_type: str = "json", 
                     api_title: Optional[str] = None,
                     api_version: Optional[str] = None) -> str:
        """保存API规范文件到上传目录
        
        Args:
            content: API规范文件内容
            file_type: 文件类型，支持 "json" 或 "yaml"
            api_title: API标题，用于生成文件名
            api_version: API版本，用于生成文件名
            
        Returns:
            保存的文件路径
        """
        # 生成文件名和路径
        filename = self._generate_file_name(api_title, api_version, file_type)
        file_path = os.path.join(self.upload_dir, filename)
        
        # 美化JSON格式输出（如果是JSON）
        if file_type.lower() == "json":
            try:
                content_obj = json.loads(content)
                content = json.dumps(content_obj, indent=2, ensure_ascii=False)
            except:
                # 如果解析失败，保持原样
                pass
        
        # 保存文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return file_path
    
    def save_api_spec_from_url(self, 
                              url: str, 
                              content: str,
                              api_title: Optional[str] = None, 
                              api_version: Optional[str] = None) -> str:
        """从URL保存API规范文件
        
        Args:
            url: API规范的URL
            content: 已下载的内容
            api_title: API标题
            api_version: API版本
            
        Returns:
            保存的文件路径
        """
        # 确定文件类型
        file_type = "json" if url.lower().endswith(".json") else "yaml"
        
        # 保存文件
        return self.save_api_spec(
            content=content,
            file_type=file_type,
            api_title=api_title,
            api_version=api_version
        ) 
    
    def save_api_spec_from_file(self, 
                               uploaded_file_path: str,
                               file_type: str,
                               api_title: Optional[str] = None, 
                               api_version: Optional[str] = None) -> str:
        """从上传的文件保存API规范
        
        Args:
            uploaded_file_path: 上传的临时文件路径
            file_type: 文件类型，支持 "json" 或 "yaml"
            api_title: API标题
            api_version: API版本
            
        Returns:
            保存的文件路径
        """
        # 读取文件内容并检测编码
        with open(uploaded_file_path, 'rb') as f:
            file_content = f.read()
            
        # 检测编码
        result = chardet.detect(file_content)
        encoding = result['encoding'] or 'utf-8'
        
        # 解码内容
        content = file_content.decode(encoding)
            
        # 保存到目标位置
        return self.save_api_spec(
            content=content,
            file_type=file_type,
            api_title=api_title,
            api_version=api_version
        )
    
    def delete_file(self, file_path: str) -> bool:
        """删除指定的文件
        
        Args:
            file_path: 要删除的文件路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            return False
    
    def clean_upload_directory(self) -> Tuple[int, int]:
        """清空上传目录中的所有API规范文件
        
        Returns:
            Tuple[int, int]: (尝试删除的文件数, 成功删除的文件数)
        """
        # 确保目录存在
        self._ensure_upload_dir_exists()
        
        # 获取所有json和yaml文件
        json_files = glob.glob(os.path.join(self.upload_dir, "*.json"))
        yaml_files = glob.glob(os.path.join(self.upload_dir, "*.yaml"))
        yml_files = glob.glob(os.path.join(self.upload_dir, "*.yml"))
        
        all_files = json_files + yaml_files + yml_files
        deleted_count = 0
        
        # 删除所有文件
        for file_path in all_files:
            if self.delete_file(file_path):
                deleted_count += 1
        
        return len(all_files), deleted_count
        
    def list_files(self) -> List[str]:
        """列出上传目录中的所有API规范文件
        
        Returns:
            List[str]: 文件路径列表
        """
        # 确保目录存在
        self._ensure_upload_dir_exists()
        
        # 获取所有json和yaml文件
        json_files = glob.glob(os.path.join(self.upload_dir, "*.json"))
        yaml_files = glob.glob(os.path.join(self.upload_dir, "*.yaml"))
        yml_files = glob.glob(os.path.join(self.upload_dir, "*.yml"))
        
        return json_files + yaml_files + yml_files 