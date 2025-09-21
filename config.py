"""
配置管理模組
負責載入和管理應用程式配置
"""

import os
from dotenv import load_dotenv

class Config:
    """應用程式配置類別"""
    
    def __init__(self):
        # 載入環境變數
        load_dotenv("data/.env")
        
        # Flask 配置
        self.SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")
        self.SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")
        
        # LINE Bot 配置
        self.LINE_BOT_API_TOKEN = os.getenv("LINE_BOT_API_TOKEN")
        self.LINE_WEBHOOK_HANDLER = os.getenv("LINE_WEBHOOK_HANDLER")
        self.LINE_GROUP_ID = os.getenv("LINE_GROUP_ID")
        
        # Discord 配置
        self.DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
        
        # 確保必要目錄存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """確保必要的目錄存在"""
        directories = ["logs", "record", "data"]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def validate_config(self):
        """驗證配置是否完整"""
        required_configs = [
            ("LINE_BOT_API_TOKEN", self.LINE_BOT_API_TOKEN),
            ("LINE_WEBHOOK_HANDLER", self.LINE_WEBHOOK_HANDLER),
            ("LINE_GROUP_ID", self.LINE_GROUP_ID),
            ("DISCORD_WEBHOOK_URL", self.DISCORD_WEBHOOK_URL),
        ]
        
        missing_configs = []
        for name, value in required_configs:
            if not value:
                missing_configs.append(name)
        
        if missing_configs:
            raise ValueError(f"缺少必要的配置: {', '.join(missing_configs)}")
        
        return True

# 全域配置實例
config = Config()
