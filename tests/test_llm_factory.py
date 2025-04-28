from unittest import TestCase
from app.services.llm_factory import LLMFactory
from app.config.settings import settings

class TestLLMFactory(TestCase):
    def setUp(self):
        """保存原始设置"""
        self.original_settings = {
            "llm_provider": settings.llm_provider,
            "openai_api_key": settings.openai_api_key,
            "openai_base_url": settings.openai_base_url,
            "openai_model": settings.openai_model,
            "deepseek_api_key": settings.deepseek_api_key,
            "deepseek_base_url": settings.deepseek_base_url,
            "deepseek_model": settings.deepseek_model,
            "siliconflow_api_key": settings.siliconflow_api_key,
            "siliconflow_base_url": settings.siliconflow_base_url,
            "siliconflow_model": settings.siliconflow_model,
        }
    
    def tearDown(self):
        """恢复原始设置"""
        settings.llm_provider = self.original_settings["llm_provider"]
        settings.openai_api_key = self.original_settings["openai_api_key"]
        settings.openai_base_url = self.original_settings["openai_base_url"]
        settings.openai_model = self.original_settings["openai_model"]
        settings.deepseek_api_key = self.original_settings["deepseek_api_key"]
        settings.deepseek_base_url = self.original_settings["deepseek_base_url"]
        settings.deepseek_model = self.original_settings["deepseek_model"]
        settings.siliconflow_api_key = self.original_settings["siliconflow_api_key"]
        settings.siliconflow_base_url = self.original_settings["siliconflow_base_url"]
        settings.siliconflow_model = self.original_settings["siliconflow_model"]
    
    def test_create_openai_llm(self):
        """测试创建 OpenAI LLM"""
        settings.llm_provider = "openai"
        settings.openai_api_key = "test-key"
        settings.openai_base_url = "https://api.openai.com/v1"
        settings.openai_model = "gpt-3.5-turbo"
        
        llm = LLMFactory.create_llm()
        self.assertEqual(llm.model_name, "gpt-3.5-turbo")
        self.assertEqual(llm.openai_api_base, "https://api.openai.com/v1")
    
    def test_create_deepseek_llm(self):
        """测试创建 Deepseek LLM"""
        settings.llm_provider = "deepseek"
        settings.deepseek_api_key = "test-key"
        settings.deepseek_base_url = "https://api.deepseek.com/v1"
        settings.deepseek_model = "deepseek-chat"
        
        llm = LLMFactory.create_llm()
        self.assertEqual(llm.model_name, "deepseek-chat")
        self.assertEqual(llm.openai_api_base, "https://api.deepseek.com/v1")
    
    def test_create_siliconflow_llm(self):
        """测试创建 Siliconflow LLM"""
        settings.llm_provider = "siliconflow"
        settings.siliconflow_api_key = "test-key"
        settings.siliconflow_base_url = "https://api.siliconflow.com/v1"
        settings.siliconflow_model = "sf-llama3-70b-chat"
        
        llm = LLMFactory.create_llm()
        self.assertEqual(llm.model_name, "sf-llama3-70b-chat")
        self.assertEqual(llm.openai_api_base, "https://api.siliconflow.com/v1")
    
    def test_invalid_provider(self):
        """测试无效的 LLM 提供商"""
        settings.llm_provider = "invalid"
        with self.assertRaises(ValueError):
            LLMFactory.create_llm() 