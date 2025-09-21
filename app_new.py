"""
緊急事件通報系統主程式
重構後的模組化版本
"""

from flask import Flask, request, abort, render_template, redirect, session, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent
import datetime
import logging
import os
import requests
import threading

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

# 驗證配置
try:
    config.validate_config()
except ValueError as e:
    print(f"配置驗證失敗: {e}")
    exit(1)

# 廣播寄送控制
line = 1
discord = 1

def Time() -> str:
    """獲取當前時間字串"""
    now = datetime.datetime.now().strftime("%Y年%m月%d日 %H時%M分%S秒")
    return now

# 註冊API路由
api_routes = APIRoutes(app)

# 請求前處理
@app.before_request
def before_request():
    """請求前處理"""
    user_info = logger_manager.get_user_info()
    logger_manager.log_user_action("頁面訪問", f"路徑: {request.path}")
    logger_manager.log_request(request.method, request.path, 200)

# 請求後處理
@app.after_request
def after_request(response):
    """請求後處理"""
    logger_manager.log_request(
        request.method, 
        request.path, 
        response.status_code
    )
    return response

# 主頁面路由
@app.route("/")
def index():
    """主頁面"""
    logger_manager.log_user_action("訪問主頁面")
    return render_template("Information/README.html")

# 案件通報路由
@app.route("/Inform/Read_02_Event")
def read_02_event():
    """案件分類選擇頁面"""
    logger_manager.log_user_action("訪問案件分類頁面")
    return render_template("Inform/02_event.html")

@app.route("/Inform/Read_03_Location")
def read_03_location():
    """案件地點選擇頁面"""
    logger_manager.log_user_action("訪問案件地點頁面")
    return render_template("Inform/03_location.html")

@app.route("/Inform/Read_04_Floor")
def read_04_floor():
    """樓層選擇頁面"""
    logger_manager.log_user_action("訪問樓層選擇頁面")
    return render_template("Inform/04_floor.html")

@app.route("/Inform/Read_05_Room")
def read_05_room():
    """房間選擇頁面"""
    logger_manager.log_user_action("訪問房間選擇頁面")
    return render_template("Inform/05_room.html")

@app.route("/Inform/Read_06_Content")
def read_06_content():
    """案件內容輸入頁面"""
    logger_manager.log_user_action("訪問案件內容頁面")
    return render_template("Inform/06_content.html")

@app.route("/Inform/Read_07_Check")
def read_07_check():
    """案件確認頁面"""
    logger_manager.log_user_action("訪問案件確認頁面")
    return render_template("Inform/07_check.html")

@app.route("/Inform/Read_08_Sending")
def read_08_sending():
    """案件發送頁面"""
    logger_manager.log_user_action("訪問案件發送頁面")
    return render_template("Inform/08_sending.html")

@app.route("/Inform/Read_10_Sended")
def read_10_sended():
    """案件發送完成頁面"""
    logger_manager.log_user_action("訪問案件發送完成頁面")
    return render_template("Inform/10_sended.html")

# 案件處理路由
@app.route("/Inform/Read_02_Event", methods=["POST"])
def process_02_event():
    """處理案件分類選擇"""
    event_type = request.form.get("event_type")
    if not event_type:
        return redirect("/Inform/Read_02_Event")
    
    session["event_type"] = event_type
    logger_manager.log_user_action("選擇案件分類", f"分類: {event_type}")
    return redirect("/Inform/Read_03_Location")

@app.route("/Inform/Read_03_Location", methods=["POST"])
def process_03_location():
    """處理案件地點選擇"""
    location = request.form.get("location")
    if not location:
        return redirect("/Inform/Read_03_Location")
    
    session["location"] = location
    logger_manager.log_user_action("選擇案件地點", f"地點: {location}")
    return redirect("/Inform/Read_04_Floor")

@app.route("/Inform/Read_04_Floor", methods=["POST"])
def process_04_floor():
    """處理樓層選擇"""
    floor = request.form.get("floor")
    if not floor:
        return redirect("/Inform/Read_04_Floor")
    
    session["floor"] = floor
    logger_manager.log_user_action("選擇樓層", f"樓層: {floor}")
    return redirect("/Inform/Read_05_Room")

@app.route("/Inform/Read_05_Room", methods=["POST"])
def process_05_room():
    """處理房間選擇"""
    room = request.form.get("room")
    if not room:
        return redirect("/Inform/Read_05_Room")
    
    session["room"] = room
    logger_manager.log_user_action("選擇房間", f"房間: {room}")
    return redirect("/Inform/Read_06_Content")

@app.route("/Inform/Read_06_Content", methods=["POST"])
def process_06_content():
    """處理案件內容輸入"""
    content = request.form.get("content", "")
    session["content"] = content
    logger_manager.log_user_action("輸入案件內容", f"內容長度: {len(content)}")
    return redirect("/Inform/Read_07_Check")

@app.route("/Inform/Read_07_Check", methods=["POST"])
def process_07_check():
    """處理案件確認"""
    logger_manager.log_user_action("確認案件資訊")
    return redirect("/Inform/Read_08_Sending")

@app.route("/Inform/Read_08_Sending", methods=["POST"])
def process_08_sending():
    """處理案件發送"""
    logger_manager.log_user_action("開始發送案件")
    return redirect("/Inform/Read_09_Sending")

@app.route("/Inform/Read_09_Sending")
def read_09_sending():
    """案件發送處理頁面"""
    try:
        # 獲取案件資料
        case_data = {
            'event_type': session.get('event_type', 'Unknown'),
            'location': session.get('location', 'Unknown'),
            'floor': session.get('floor', 'Unknown'),
            'room': session.get('room', 'Unknown'),
            'content': session.get('content', 'None')
        }
        
        # 格式化訊息
        message_content = message_broadcaster.format_case_message(case_data)
        
        # 廣播訊息
        broadcast_results = message_broadcaster.broadcast_message(message_content, case_data)
        
        # 準備案件紀錄資料
        user_info = logger_manager.get_user_info()
        case_record_data = {
            **case_data,
            'message': message_content,
            'ip': user_info['ip'],
            'country': user_info['country'],
            'city': user_info['city'],
            'user_agent': user_info['user_agent'],
            'discord_success': broadcast_results['discord_success'],
            'line_success': broadcast_results['line_success'],
            'discord_message_id': broadcast_results.get('discord_message_id')
        }
        
        # 保存案件紀錄
        try:
            filename = case_manager.save_case_record(case_record_data)
            logger_manager.log_user_action("案件紀錄已保存", f"檔案: {filename}")
        except Exception as e:
            logger_manager.log_error(f"保存案件紀錄失敗: {e}")
        
        # 記錄發送結果
        logger_manager.log_user_action("案件發送完成", f"LINE: {broadcast_results['line_success']}, Discord: {broadcast_results['discord_success']}")
        
        # 清除session
        session.clear()
        
        return render_template("Inform/10_sended.html", 
                             line_success=broadcast_results['line_success'],
                             discord_success=broadcast_results['discord_success'],
                             line_error=broadcast_results.get('line_error'),
                             discord_error=broadcast_results.get('discord_error'))
        
    except Exception as e:
        logger_manager.log_error(f"案件發送處理失敗: {e}")
        return render_template("Inform/10_sended.html", 
                             line_success=False,
                             discord_success=False,
                             line_error=str(e),
                             discord_error=str(e))

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
        return content
    else:
        return "案件紀錄不存在", 404

@app.route("/system/records/download/<filename>")
def download_record(filename):
    """下載案件紀錄"""
    logger_manager.log_user_action("下載案件紀錄", f"檔案: {filename}")
    file_path = os.path.join("record", filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "檔案不存在", 404

# LINE Bot Webhook
@app.route("/callback", methods=["POST"])
def callback():
    """LINE Bot回調處理"""
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理LINE訊息"""
    logger_manager.log_user_action("收到LINE訊息", f"訊息: {event.message.text}")
    
    # 回覆訊息
    reply_text = f"收到訊息: {event.message.text}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

@handler.add(JoinEvent)
def handle_join(event):
    """處理LINE群組加入事件"""
    logger_manager.log_user_action("LINE Bot加入群組")
    
    reply_text = "緊急事件通報系統已啟動！"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# 錯誤處理
@app.errorhandler(404)
def not_found(error):
    """404錯誤處理"""
    logger_manager.log_error(f"404錯誤: {request.path}")
    return render_template("Information/404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    """500錯誤處理"""
    logger_manager.log_error(f"500錯誤: {str(error)}")
    return render_template("Information/500.html"), 500

if __name__ == "__main__":
    # 設定日誌
    logger_manager.setup_logging()
    
    # 啟動應用程式
    app.run(host="0.0.0.0", port=5000, debug=True)
