"""
日誌管理模組
負責系統日誌的設定、記錄和管理
"""

import logging
import datetime
import os
from flask import request
from config import config

class LoggerManager:
    """日誌管理器"""
    
    def __init__(self):
        self.setup_logging()
    
    def get_log_filename(self, date=None):
        """獲取指定日期的日誌檔案名稱"""
        if date is None:
            date = datetime.datetime.now().strftime("%Y%m%d")
        return f"logs/flask_app_{date}.log"
    
    def setup_logging(self):
        """設定日誌系統"""
        # 確保日誌目錄存在
        if not os.path.exists("logs"):
            os.makedirs("logs")
        
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        log_filename = self.get_log_filename(current_date)
        
        # 清除現有的處理器
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # 設定根日誌器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # 設定檔案日誌
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # 設定控制台日誌
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # 設定 Flask 日誌器
        flask_logger = logging.getLogger('werkzeug')
        flask_logger.setLevel(logging.INFO)
        flask_logger.addHandler(file_handler)
        flask_logger.addHandler(console_handler)
    
    def get_real_ip(self):
        """獲取真實IP地址（支援Cloudflare Tunnel）"""
        # Cloudflare Tunnel 優先
        if request.headers.get('CF-Connecting-IP'):
            return request.headers.get('CF-Connecting-IP')
        
        # Cloudflare 其他標頭
        if request.headers.get('CF-IPCountry'):
            # 如果有 Cloudflare 標頭，嘗試其他方式獲取 IP
            if request.headers.get('X-Forwarded-For'):
                return request.headers.get('X-Forwarded-For').split(',')[0].strip()
            if request.headers.get('X-Real-IP'):
                return request.headers.get('X-Real-IP')
        
        # 其他代理
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        
        if request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        
        # 直接連接
        return request.remote_addr
    
    def get_user_info(self):
        """獲取使用者資訊"""
        ip = self.get_real_ip()
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # Cloudflare 地理資訊
        country = request.headers.get('CF-IPCountry', 'Unknown')
        city = request.headers.get('CF-IPCity', 'Unknown')
        
        # Cloudflare 其他資訊
        cf_ray = request.headers.get('CF-Ray', 'Unknown')
        cf_visitor = request.headers.get('CF-Visitor', 'Unknown')
        
        # 來源頁面
        referer = request.headers.get('Referer', 'Direct')
        
        return {
            'ip': ip,
            'user_agent': user_agent,
            'country': country,
            'city': city,
            'referer': referer,
            'cf_ray': cf_ray,
            'cf_visitor': cf_visitor
        }
    
    def log_user_action(self, action, details=None):
        """記錄使用者動作"""
        user_info = self.get_user_info()
        
        log_message = f"User Action: {action}"
        if details:
            log_message += f" | Details: {details}"
        
        log_message += f" | IP: {user_info['ip']} | Country: {user_info['country']} | City: {user_info['city']}"
        
        logging.info(log_message)
    
    def log_request(self, method, path, status_code, response_time=None):
        """記錄請求資訊"""
        user_info = self.get_user_info()
        
        log_message = f"Request: {method} {path} | Status: {status_code}"
        if response_time:
            log_message += f" | Response Time: {response_time}ms"
        
        log_message += f" | IP: {user_info['ip']} | Country: {user_info['country']} | City: {user_info['city']}"
        
        # 添加 Cloudflare 資訊
        if user_info['cf_ray'] != 'Unknown':
            log_message += f" | CF-Ray: {user_info['cf_ray']}"
        if user_info['cf_visitor'] != 'Unknown':
            log_message += f" | CF-Visitor: {user_info['cf_visitor']}"
        
        logging.info(log_message)
    
    def log_error(self, error, context=None):
        """記錄錯誤資訊"""
        user_info = self.get_user_info()
        
        log_message = f"Error: {str(error)}"
        if context:
            log_message += f" | Context: {context}"
        
        log_message += f" | IP: {user_info['ip']} | Country: {user_info['country']} | City: {user_info['city']}"
        
        logging.error(log_message)
    
    def get_log_files(self):
        """獲取所有日誌檔案"""
        log_files = []
        if os.path.exists("logs"):
            for filename in os.listdir("logs"):
                if filename.startswith("flask_app_") and filename.endswith(".log"):
                    file_path = os.path.join("logs", filename)
                    stat = os.stat(file_path)
                    log_files.append({
                        'filename': filename,
                        'date': filename.replace("flask_app_", "").replace(".log", ""),
                        'size': stat.st_size,
                        'modified': datetime.datetime.fromtimestamp(stat.st_mtime)
                    })
        
        return sorted(log_files, key=lambda x: x['date'], reverse=True)
    
    def read_log_file(self, filename, lines=None):
        """讀取日誌檔案內容"""
        file_path = os.path.join("logs", filename)
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            if lines:
                return f.readlines()[-lines:]
            else:
                return f.readlines()
    
    def clear_log_files(self, date_from=None, date_to=None):
        """清除日誌檔案"""
        cleared_files = []
        
        if os.path.exists("logs"):
            for filename in os.listdir("logs"):
                if filename.startswith("flask_app_") and filename.endswith(".log"):
                    file_date_str = filename.replace("flask_app_", "").replace(".log", "")
                    
                    # 檢查日期範圍
                    if date_from and date_to:
                        try:
                            file_date = datetime.datetime.strptime(file_date_str, "%Y%m%d")
                            start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
                            end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
                            
                            if not (start_date <= file_date <= end_date):
                                continue
                        except ValueError:
                            continue
                    
                    file_path = os.path.join("logs", filename)
                    os.remove(file_path)
                    cleared_files.append(filename)
        
        return cleared_files

# 全域日誌管理器實例
logger_manager = LoggerManager()
