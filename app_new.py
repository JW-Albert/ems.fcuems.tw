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

# 禁用Flask的請求日誌記錄
import logging
log = logging.getLogger('werkzeug')
log.disabled = True

# LINE Bot 設定
from linebot import LineBotApi, WebhookHandler
line_bot_api = LineBotApi(config.LINE_BOT_API_TOKEN)
handler = WebhookHandler(config.LINE_WEBHOOK_HANDLER)

# 驗證配置
try:
    config.validate_config()
except ValueError as e:
    print(f"配置驗證失敗: {e}")
    exit(1)

# 廣播寄送控制
line = 1
discord = 1

# 案件分類和地點對照表
event_table = {1: "OHCA", 2: "內科", 3: "外科"}
locat_table = {
    1: "行政大樓",
    2: "行政二館",
    3: "丘逢甲紀念館",
    4: "圖書館",
    5: "科學與航太館",
    6: "商學大樓",
    7: "忠勤樓",
    8: "建築館",
    9: "語文大樓",
    10: "工學大樓",
    11: "人言大樓",
    12: "資訊電機館",
    13: "人文社會館",
    14: "電子通訊館",
    15: "育樂館",
    16: "土木水利館",
    17: "理學大樓",
    18: "學思樓",
    19: "體育館",
    20: "文創中心",
    21: "共善樓",
}

def Time() -> str:
    """獲取當前時間字串"""
    now = datetime.datetime.now().strftime("%Y年%m月%d日 %H時%M分%S秒")
    return now

def discord_send(message):
    """發送 Discord 訊息並返回訊息 ID"""
    try:
        # 使用 requests 直接呼叫 Discord Webhook API 來獲取訊息 ID
        # 添加 wait=true 參數來獲取訊息 ID
        payload = {"content": message}
        response = requests.post(f"{config.DISCORD_WEBHOOK_URL}?wait=true", json=payload)
        
        if response.status_code == 200:  # 使用 wait=true 時，成功回應是 200
            # 從回應中獲取訊息 ID
            message_data = response.json()
            message_id = message_data.get('id')
            logging.info(f"Discord message sent successfully, ID: {message_id}")
            return message_id
        else:
            logging.error(f"Failed to send Discord message: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logging.error(f"Error sending Discord message: {e}")
        return None

def broadcast_message(group_id, message):
    """廣播訊息到LINE群組"""
    line_bot_api.push_message(group_id, TextSendMessage(text=message))

# 註冊API路由
api_routes = APIRoutes(app)

# 請求前處理
@app.before_request
def before_request():
    """請求前處理"""
    user_info = logger_manager.get_user_info()
    logger_manager.log_user_action("頁面訪問", f"路徑: {request.path}")
    # 不在這裡記錄請求，避免重複記錄

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

# 主頁面路由
@app.route("/")
@app.route("/Inform/Read_02_Event")
def show_02_event():
    """案件分類選擇頁面（主頁面）"""
    # 重置session變數
    session["event"] = 0
    session["locat"] = "0"
    session["room"] = "NULL"
    session["content"] = ""
    session["message"] = "NULL"
    
    # 初始化地點表（複製預設表）
    session["locat_table"] = locat_table
    
    logger_manager.log_user_action("訪問主頁面（案件分類）")
    return render_template("Inform/02_event.html")

@app.route("/Inform/Read_03_Location")
def show_03_location():
    """案件地點選擇頁面"""
    logger_manager.log_user_action("訪問案件地點頁面")
    return render_template("Inform/03_location.html")

@app.route("/Inform/Read_04_Floor")
def read_04_floor():
    """樓層選擇頁面"""
    logger_manager.log_user_action("訪問樓層選擇頁面")
    return render_template("Inform/04_floor.html")

@app.route("/Inform/Read_05_Room")
def show_05_room():
    """房間選擇頁面"""
    logger_manager.log_user_action("訪問房間選擇頁面")
    return render_template("Inform/05_room.html")

@app.route("/Inform/Read_06_Content")
def show_06_content():
    """案件內容輸入頁面"""
    logger_manager.log_user_action("訪問案件內容頁面")
    return render_template("Inform/06_content.html")

@app.route("/Inform/Read_07_Check")
def show_07_check():
    """案件確認頁面"""
    logger_manager.log_user_action("訪問案件確認頁面")
    
    # 準備案件資料
    event_type = session.get('event', 0)
    location_id = session.get('locat', '0')
    room = session.get('room', 'NULL')
    content = session.get('content', '')
    
    # 獲取案件分類名稱
    event_name = event_table.get(event_type, 'Unknown')
    
    # 獲取地點名稱
    try:
        location_id_int = int(location_id)
        location_name = session["locat_table"].get(session["locat"], 'Unknown')
    except (ValueError, TypeError):
        # 如果轉換失敗，可能是自訂地點（ID為99）或其他特殊情況
        location_name = session["locat_table"].get(location_id, 'Unknown')
    
    return render_template("Inform/07_check.html", 
                          event=event_name,
                          locat=location_name,
                          room=room,
                          content=content)

@app.route("/Inform/Read_08_Sending")
def show_08_sending():
    """案件發送頁面"""
    logger_manager.log_user_action("訪問案件發送頁面")
    return render_template("Inform/08_sending.html")

@app.route("/Inform/Read_10_Sended")
def show_10_sended():
    """案件發送完成頁面"""
    logger_manager.log_user_action("訪問案件發送完成頁面")
    return render_template("Inform/10_sended.html")

# 案件處理路由
@app.route("/Inform/Read_02_Event", methods=["POST"])
def process_02_event():
    """處理案件分類選擇"""
    event_type = int(request.form.get("event"))
    session["event"] = event_type
    
    # 記錄事件類型選擇
    event_name = event_table.get(event_type, "Unknown")
    logger_manager.log_user_action("選擇案件分類", f"分類: {event_name}({event_type})")
    
    return redirect("/Inform/Read_03_Location")

@app.route("/Inform/Read_03_Location", methods=["POST"])
def process_03_location():
    """處理案件地點選擇"""
    # 接收按鈕選擇值
    selected_button = request.form.get("selectedButtonInput")
    selected_button = int(selected_button)

    # 接收手動輸入值
    custom_location = request.form.get("customLocation")
    
    if selected_button != 0:
        # 預設地點
        session["locat"] = str(selected_button)
        location_name = session["locat_table"].get(session["locat"], "Unknown")
        logger_manager.log_user_action("選擇案件地點", f"地點: {location_name}({selected_button})")
    else:
        # 自訂地點：新增到地點表
        session["locat"] = "99"
        session["locat_table"].update({99: custom_location})
        logger_manager.log_user_action("自訂案件地點", f"自訂地點: {custom_location}")

    return redirect("/Inform/Read_05_Room")


@app.route("/Inform/Read_05_Room", methods=["POST"])
def process_05_room():
    """處理房號選擇"""
    room = request.form.get("room")
    if len(room) == 1:
        room = room + " 樓"
    session["room"] = room
    
    # 記錄房間/位置輸入
    logger_manager.log_user_action("輸入房號位置", f"房號: {room}")
    
    return redirect("/Inform/Read_06_Content")

@app.route("/Inform/Read_06_Content", methods=["POST"])
def process_06_content():
    """處理案件內容輸入"""
    content = request.form.get("content", "")
    session["content"] = content
    
    # 記錄補充資訊輸入
    content_length = len(content)
    logger_manager.log_user_action("輸入案件內容", f"內容長度: {content_length}")
    
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
def show_09_sending():
    """案件發送處理頁面"""
    # 處理內容中的換行符
    content_with_tabs = session["content"].replace("\n", "\n\t")

    # 使用多行字串組合訊息
    session["message"] = (
        "緊急事件通報\n"
        f"案件分類： {event_table[session['event']]}\n"
        f"案件地點： {session['locat_table'][session['locat']]}\n"
        f"案件位置： {session['room']}\n"
        f"案件補充：\n\t{content_with_tabs}\n"
        f"通報時間： {Time()}"
    )

    # 記錄事件通報
    logger_manager.log_user_action("提交案件通報", 
        f"Event={event_table[session['event']]} | "
        f"Location={session['locat_table'][session['locat']]} | "
        f"Room={session['room']} | "
        f"ContentLength={len(session['content'])}"
    )

    # 發送訊息並記錄結果
    discord_success = False
    line_success = False
    discord_message_id = None
    
    if discord == 1:
        message_id = discord_send(session["message"] + "\n@everyone\n# [事件回覆](https://forms.gle/dww4orwk2RHSbVV2A)")
        if message_id:
            discord_success = True
            discord_message_id = message_id
            logger_manager.log_user_action("Discord發送成功", f"MessageID={message_id}")
        else:
            logger_manager.log_user_action("Discord發送失敗", "Failed to send Discord message")
    
    if line == 1:
        try:
            broadcast_message(config.LINE_GROUP_ID, session["message"])
            line_success = True
            logger_manager.log_user_action("LINE發送成功", f"GroupID={config.LINE_GROUP_ID}")
        except Exception as e:
            logger_manager.log_user_action("LINE發送失敗", f"Error={str(e)}")

    # 記錄整體發送結果
    logger_manager.log_user_action("案件廣播完成", 
        f"Discord={discord_success} | LINE={line_success}")

    # 準備案件資料並儲存紀錄
    case_data = {
        'event_type': event_table[session['event']],
        'location': session['locat_table'][session['locat']],
        'room': session['room'],
        'content': session['content'],
        'message': session["message"],
        'discord_success': discord_success,
        'line_success': line_success,
        'discord_message_id': discord_message_id
    }
    
    # 儲存案件紀錄
    try:
        filename = case_manager.save_case_record(case_data)
        logger_manager.log_user_action("案件紀錄已保存", f"RecordFile={filename}")
    except Exception as e:
        logger_manager.log_user_action("案件紀錄保存失敗", f"Failed to save case record: {e}")

    return redirect("/Inform/Read_10_Sended")

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
    # 啟動應用程式
    app.run(host="0.0.0.0", port=5000, debug=True)
