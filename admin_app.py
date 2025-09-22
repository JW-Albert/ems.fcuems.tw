"""
緊急事件通報系統 - 管理網站
獨立的管理介面，提供日誌管理、案件紀錄管理、系統測試等功能
"""

from flask import Flask, request, render_template, jsonify, send_file
import datetime
import os
import logging

# 導入自定義模組
from config import config
from logger import logger_manager
from case_manager import case_manager
from message_broadcaster import message_broadcaster
from api_routes import APIRoutes

# 創建Flask應用程式
app = Flask(__name__, static_folder="static", static_url_path="/")
app.secret_key = config.SECRET_KEY
app.config["SESSION_TYPE"] = config.SESSION_TYPE

# 禁用Flask的請求日誌記錄
log = logging.getLogger('werkzeug')
log.disabled = True

# 驗證配置
try:
    config.validate_config()
except ValueError as e:
    print(f"配置驗證失敗: {e}")
    exit(1)

# 註冊API路由
api_routes = APIRoutes(app)

# 請求前處理
@app.before_request
def before_request():
    """請求前處理"""
    user_info = logger_manager.get_user_info()
    logger_manager.log_user_action("管理頁面訪問", f"路徑: {request.path}")

# 請求後處理
@app.after_request
def after_request(response):
    """請求後處理"""
    user_info = logger_manager.get_user_info()
    logger_manager.log_request(
        request.method, 
        request.path, 
        response.status_code
    )
    return response

# 管理首頁
@app.route("/")
def admin_home():
    """管理首頁"""
    logger_manager.log_user_action("訪問管理首頁")
    return render_template("admin/home.html")

# 系統測試路由
@app.route("/system/test")
def system_test():
    """系統測試頁面"""
    logger_manager.log_user_action("訪問系統測試頁面")
    return render_template("system/test.html")

@app.route("/system/test/line", methods=["POST"])
def test_line():
    """測試LINE Bot"""
    logger_manager.log_user_action("測試LINE Bot")
    result = message_broadcaster.test_line_message()
    
    if result["success"]:
        logger_manager.log_user_action("LINE Bot測試成功")
    else:
        logger_manager.log_user_action("LINE Bot測試失敗", result["error"])
    
    return jsonify(result)

@app.route("/system/test/discord", methods=["POST"])
def test_discord():
    """測試Discord Webhook"""
    logger_manager.log_user_action("測試Discord Webhook")
    result = message_broadcaster.test_discord_message()
    
    if result["success"]:
        logger_manager.log_user_action("Discord Webhook測試成功")
    else:
        logger_manager.log_user_action("Discord Webhook測試失敗", result["error"])
    
    return jsonify(result)

# 日誌管理路由
@app.route("/system/logs")
def system_logs():
    """日誌管理頁面"""
    logger_manager.log_user_action("訪問日誌管理頁面")
    return render_template("system/logs.html")

@app.route("/system/logs/files")
def get_log_files():
    """獲取日誌檔案列表"""
    logger_manager.log_user_action("獲取日誌檔案列表")
    log_files = logger_manager.get_log_files()
    return jsonify({"success": True, "files": log_files})

# 案件紀錄管理路由
@app.route("/system/records")
def system_records():
    """案件紀錄管理頁面"""
    logger_manager.log_user_action("訪問案件紀錄管理頁面")
    return render_template("system/records.html")

@app.route("/system/records/view/<filename>")
def view_record(filename):
    """查看案件紀錄"""
    logger_manager.log_user_action("查看案件紀錄", f"檔案: {filename}")
    content = case_manager.read_case_file(filename)
    if content:
        return jsonify({
            "success": True,
            "content": content
        })
    else:
        return jsonify({
            "success": False,
            "error": "案件紀錄不存在"
        }), 404

@app.route("/system/records/download/<filename>")
def download_record(filename):
    """下載案件紀錄"""
    logger_manager.log_user_action("下載案件紀錄", f"檔案: {filename}")
    file_path = os.path.join("record", filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "檔案不存在", 404

# 錯誤處理
@app.errorhandler(404)
def not_found(error):
    """404錯誤處理"""
    logger_manager.log_error(f"管理網站404錯誤: {request.path}")
    return render_template("Information/404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    """500錯誤處理"""
    logger_manager.log_error(f"管理網站500錯誤: {str(error)}")
    return render_template("Information/500.html"), 500

if __name__ == "__main__":
    # 啟動管理應用程式
    print("啟動緊急事件通報系統 - 管理網站")
    print("管理介面: https://admin.fcuems.tw/")
    app.run(host="0.0.0.0", port=5000, debug=True)
