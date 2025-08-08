"""
配置文件 - 用于存储API配置和其他设置
"""

import os
from typing import Optional


def load_env_file(env_path: str = ".env") -> None:
    """
    加载.env文件中的环境变量
    
    Args:
        env_path: .env文件路径
    """
    if not os.path.exists(env_path):
        return
        
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


class Config:
    """配置管理类"""
    
    @staticmethod
    def get_openai_config() -> dict:
        """
        获取OpenAI配置
        
        Returns:
            包含API配置的字典
        """
        # 先尝试加载.env文件
        load_env_file()
        
        return {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'api_base': os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1'),
            'model': os.getenv('OPENAI_MODEL_NAME', os.getenv('OPENAI_MODEL', 'gpt-4o'))
        }
    
    @staticmethod
    def get_gemini_config() -> dict:
        """
        获取Gemini配置
        
        Returns:
            包含API配置的字典
        """
        # 先尝试加载.env文件
        load_env_file()
        
        return {
            'api_key': os.getenv('GEMINI_API_KEY'),
            'api_base': os.getenv('GEMINI_API_BASE', 'https://generativelanguage.googleapis.com/v1beta'),
            'model': os.getenv('GEMINI_MODEL_NAME', os.getenv('GEMINI_MODEL', 'gemini-2.5-pro'))
        }
    
    @staticmethod
    def validate_openai_config() -> bool:
        """验证OpenAI配置是否完整"""
        config = Config.get_openai_config()
        return bool(config['api_key'])
    
    @staticmethod
    def validate_config() -> bool:
        """验证配置是否完整"""
        config = Config.get_gemini_config()
        return bool(config['api_key'])
    
    @staticmethod
    def get_file_paths() -> dict:
        """获取文件路径配置"""
        return {
            'pdf_file': '《数据安全管理员题库》（客观题）-20250713（提交版）.pdf',
            'output_excel': '题库处理结果.xlsx',
            'template_excel': '2-《数据安全管理员题库》（客观题）-20250805.xlsx'
        }