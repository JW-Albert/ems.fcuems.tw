from flask import Flask, request, abort, render_template, redirect, session, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent
import datetime
import logging
from dhooks import Webhook
import os
import requests
import threading
from dotenv import load_dotenv

# 載入環境變數
load_dotenv("data/.env")

app = Flask(__name__, static_folder="static", static_url_path="/")
app.secret_key = os.getenv("SECRET_KEY", "secret_key")
app.config["SESSION_TYPE"] = "filesystem"

# 廣播寄送控制
line = 1
discord = 1


def Time() -> str:
    now = datetime.datetime.now().strftime("%Y年%m月%d日 %H時%M分%S秒")
    return now


# LINE Bot 設定
line_bot_api_token = os.getenv("LINE_BOT_API_TOKEN")
line_webhook_handler = os.getenv("LINE_WEBHOOK_HANDLER")
line_bot_api = LineBotApi(line_bot_api_token)
handler = WebhookHandler(line_webhook_handler)

group_id = os.getenv("LINE_GROUP_ID")

# 確保 logs 和 record 目錄存在
if not os.path.exists("logs"):
    os.makedirs("logs")

if not os.path.exists("record"):
    os.makedirs("record")

# 日誌檔案管理
def get_log_filename(date=None):
    """獲取指定日期的日誌檔案名稱"""
    if date is None:
        date = datetime.datetime.now().strftime("%Y%m%d")
    return f"logs/flask_app_{date}.log"

def setup_logging():
    """設定日誌系統"""
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    log_filename = get_log_filename(current_date)
    
    # 清除現有的處理器
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # 設定新的日誌配置
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 同時輸出到控制台（開發時使用）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logging.getLogger().addHandler(console_handler)

# 初始化日誌系統
setup_logging()


def get_real_ip():
    """獲取真實IP地址，支援Cloudflare Tunnel"""
    # Cloudflare Tunnel 優先
    if request.headers.get("CF-Connecting-IP"):
        return request.headers["CF-Connecting-IP"]
    # Cloudflare 代理
    elif request.headers.get("CF-IPCountry"):
        return request.headers.get("CF-Connecting-IP", request.remote_addr)
    # 其他代理
    elif request.headers.get("X-Forwarded-For"):
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    elif request.headers.get("X-Real-IP"):
        return request.headers["X-Real-IP"]
    else:
        return request.remote_addr


def get_user_info():
    """獲取使用者資訊"""
    ip = get_real_ip()
    user_agent = request.headers.get("User-Agent", "Unknown")
    country = request.headers.get("CF-IPCountry", "Unknown")
    city = request.headers.get("CF-IPCity", "Unknown")
    referer = request.headers.get("Referer", "Direct")
    
    return {
        "ip": ip,
        "user_agent": user_agent,
        "country": country,
        "city": city,
        "referer": referer
    }


def log_user_action(action, details=None):
    """記錄使用者動作"""
    user_info = get_user_info()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_message = (
        f"[{timestamp}] USER_ACTION: {action} | "
        f"IP={user_info['ip']} | "
        f"Country={user_info['country']} | "
        f"City={user_info['city']} | "
        f"Path={request.path} | "
        f"Method={request.method}"
    )
    
    if details:
        log_message += f" | Details={details}"
    
    logging.info(log_message)


def save_case_record(case_data):
    """儲存案件紀錄到檔案"""
    try:
        # 生成檔案名稱（精確到秒）
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"record/case_{timestamp}.txt"
        
        # 準備案件資料
        record_content = []
        record_content.append("=" * 50)
        record_content.append("緊急事件通報紀錄 / Emergency Incident Report")
        record_content.append("=" * 50)
        record_content.append(f"案件編號 / Case ID: {timestamp}")
        record_content.append(f"通報時間 / Report Time: {Time()}")
        record_content.append("")
        
        # 案件基本資訊
        record_content.append("案件資訊 / Case Information:")
        record_content.append("-" * 30)
        record_content.append(f"案件分類 / Case Type: {case_data.get('event_type', 'Unknown')}")
        record_content.append(f"案件地點 / Location: {case_data.get('location', 'Unknown')}")
        record_content.append(f"案件位置 / Position: {case_data.get('room', 'Unknown')}")
        record_content.append(f"補充資訊 / Additional Info: {case_data.get('content', 'None')}")
        record_content.append("")
        
        # 通報者資訊
        user_info = get_user_info()
        record_content.append("通報者資訊 / Reporter Information:")
        record_content.append("-" * 30)
        record_content.append(f"IP 地址 / IP Address: {user_info['ip']}")
        record_content.append(f"國家 / Country: {user_info['country']}")
        record_content.append(f"城市 / City: {user_info['city']}")
        record_content.append(f"瀏覽器 / User Agent: {user_info['user_agent']}")
        record_content.append("")
        
        # 廣播結果
        record_content.append("廣播結果 / Broadcast Results:")
        record_content.append("-" * 30)
        record_content.append(f"Discord 發送 / Discord Send: {case_data.get('discord_success', False)}")
        record_content.append(f"LINE 發送 / LINE Send: {case_data.get('line_success', False)}")
        if case_data.get('discord_message_id'):
            record_content.append(f"Discord 訊息 ID / Discord Message ID: {case_data.get('discord_message_id')}")
        record_content.append("")
        
        # 完整訊息內容
        record_content.append("完整訊息內容 / Complete Message:")
        record_content.append("-" * 30)
        record_content.append(case_data.get('message', 'No message'))
        record_content.append("")
        
        # 系統資訊
        record_content.append("系統資訊 / System Information:")
        record_content.append("-" * 30)
        record_content.append(f"伺服器時間 / Server Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        record_content.append(f"檔案路徑 / File Path: {filename}")
        record_content.append("=" * 50)
        
        # 寫入檔案
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(record_content))
        
        # 記錄到日誌
        log_user_action("SAVE_CASE_RECORD", f"File={filename}")
        logging.info(f"Case record saved to {filename}")
        
        return filename
        
    except Exception as e:
        logging.error(f"Failed to save case record: {e}")
        return None


@app.before_request
def log_request_info():
    """記錄請求資訊"""
    user_info = get_user_info()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 基本請求記錄
    logging.info(
        f"[{timestamp}] REQUEST: {request.method} {request.path} | "
        f"IP={user_info['ip']} | "
        f"Country={user_info['country']} | "
        f"City={user_info['city']} | "
        f"User-Agent={user_info['user_agent'][:100]} | "
        f"Referer={user_info['referer']}"
    )
    
    # 記錄特殊動作
    if request.path.startswith("/Inform/"):
        log_user_action("ACCESS_INCIDENT_FORM", f"Page={request.path}")
    elif request.path.startswith("/system/"):
        log_user_action("ACCESS_SYSTEM_PAGE", f"Page={request.path}")
    elif request.path.startswith("/Information/"):
        log_user_action("ACCESS_INFO_PAGE", f"Page={request.path}")


@app.after_request
def log_response_info(response):
    """記錄回應資訊"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logging.info(
        f"[{timestamp}] RESPONSE: {response.status_code} {request.path} | "
        f"IP={get_real_ip()}"
    )
    
    return response


@app.route("/bot/callback", methods=["POST"])
def bot_callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(JoinEvent)
def handle_join(event):
    group_id = event.source.group_id
    print(f"Bot has joined the group with groupId: {group_id}")
    line_bot_api.push_message(
        group_id,
        TextSendMessage(
            text="大家好！我是逢甲大學衛保救護隊的報警機器人!\n" f"本群組ID: {group_id}"
        ),
    )


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_token = event.reply_token
    if user_message == "訊號測試":
        line_bot_api.reply_message(reply_token, TextSendMessage(text="訊號良好"))


def send_person_message(message):
    line_bot_api.broadcast(TextSendMessage(text=message))


def send_group_message(group_id, message):
    line_bot_api.push_message(group_id, TextSendMessage(text=message))


def broadcast_message(group_id, message):
    # 寄送予好友
    # send_person_message(message)
    # 寄送予群組
    send_group_message(group_id, message)


# Discord Webhook
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
hook = Webhook(webhook_url)


def discord_send(message):
    """發送 Discord 訊息並返回訊息 ID"""
    try:
        # 使用 requests 直接呼叫 Discord Webhook API 來獲取訊息 ID
        # 添加 wait=true 參數來獲取訊息 ID
        payload = {"content": message}
        response = requests.post(f"{webhook_url}?wait=true", json=payload)
        
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


def discord_edit_message(message_id, new_content):
    """使用 Discord Webhook 編輯訊息"""
    try:
        # 使用 Discord Webhook API 編輯訊息
        # 格式：https://discord.com/api/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}
        edit_url = f"{webhook_url}/messages/{message_id}"
        payload = {"content": new_content}
        response = requests.patch(edit_url, json=payload)
        
        if response.status_code == 200:
            logging.info(f"Successfully edited Discord message {message_id}")
            return True
        else:
            logging.error(f"Failed to edit Discord message {message_id}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Error editing Discord message {message_id}: {e}")
        return False


def schedule_discord_edit(message_id, original_message, delay_hours=1):
    """安排定時編輯 Discord 訊息"""
    def edit_after_delay():
        # 只移除事件回覆連結，保留 @everyone
        new_content = original_message.replace("\n# [事件回覆](https://forms.gle/dww4orwk2RHSbVV2A)", "")
        success = discord_edit_message(message_id, new_content)
        if success:
            logging.info(f"Successfully removed reply link from message {message_id}")
        else:
            logging.error(f"Failed to remove reply link from message {message_id}")
    
    # 設定定時任務，1小時後執行
    timer = threading.Timer(delay_hours * 3600, edit_after_delay)
    timer.start()
    logging.info(f"Scheduled Discord message edit for message {message_id} in {delay_hours} hour(s)")


# 主程式設定
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


@app.route("/")
@app.route("/Inform/02_Event")
def Inform_02_Event():
    # 因為主頁改為02_event，所以在此重置變數
    session["event"] = 0
    session["locat"] = "0"
    session["room"] = "NULL"
    session["content"] = ""
    session["message"] = "NULL"
    return render_template("/Inform/02_event.html")


@app.route("/Inform/Read_02_Event", methods=["POST"])
def Inform_Read_02_Event():
    event_type = int(request.form.get("event"))
    session["event"] = event_type
    
    # 記錄事件類型選擇
    event_name = event_table.get(event_type, "Unknown")
    log_user_action("SELECT_EVENT_TYPE", f"Event={event_name}({event_type})")
    
    return redirect("/Inform/03_Location")


@app.route("/Inform/03_Location")
def Inform_03_Location():
    return render_template("/Inform/03_location.html")


@app.route("/Inform/Read_03_Location", methods=["POST"])
def Inform_Read_03_Location():
    # 接收按鈕選擇值
    selected_button = request.form.get("selectedButtonInput")
    selected_button = int(selected_button)

    # 接收手動輸入值
    custom_location = request.form.get("customLocation")

    if selected_button != 0:
        session["locat"] = str(selected_button)
        location_name = locat_table.get(selected_button, "Unknown")
        log_user_action("SELECT_LOCATION", f"Location={location_name}({selected_button})")
    else:
        session["locat"] = "99"
        locat_table.update({99: custom_location})
        log_user_action("CUSTOM_LOCATION", f"CustomLocation={custom_location}")

    session["locat_table"] = locat_table

    return redirect("/Inform/05_Room")

@app.route("/Inform/05_Room")
def Inform_05_Room():
    return render_template("/Inform/05_room.html")


@app.route("/Inform/Read_05_Room", methods=["POST"])
def Inform_Read_05_Room():
    room = request.form.get("room")
    if (len(room) == 1):
        room = room + " 樓"
    session["room"] = room
    
    # 記錄房間/位置輸入
    log_user_action("INPUT_ROOM", f"Room={room}")
    
    return redirect("/Inform/06_Content")


@app.route("/Inform/06_Content")
def Inform_06_Content():
    return render_template("/Inform/06_content.html")


@app.route("/Inform/Read_06_Content", methods=["POST"])
def Inform_Read_06_Content():
    content = request.form.get("content", "")
    session["content"] = content
    
    # 記錄補充資訊輸入
    content_length = len(content)
    log_user_action("INPUT_CONTENT", f"ContentLength={content_length}")
    
    return redirect("/Inform/07_Check")


@app.route("/Inform/07_Check")
def Inform_07_Check():
    return render_template(
        "/Inform/07_check.html",
        event=event_table[session["event"]],
        locat=session["locat_table"][session["locat"]],
        room=session["room"],
        content=session["content"],
    )


@app.route("/Inform/08_Send")
def Inform_08_Send():
    return render_template("/Inform/08_sending.html")


@app.route("/Inform/09_Sending")
def Inform_09_Sending():
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
    log_user_action("SUBMIT_INCIDENT", 
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
            schedule_discord_edit(message_id, session["message"] + "\n@everyone\n# [事件回覆](https://forms.gle/dww4orwk2RHSbVV2A)")
            discord_success = True
            discord_message_id = message_id
            log_user_action("DISCORD_SEND_SUCCESS", f"MessageID={message_id}")
        else:
            log_user_action("DISCORD_SEND_FAILED", "Failed to send Discord message")
    
    if line == 1:
        try:
            broadcast_message(group_id, session["message"])
            line_success = True
            log_user_action("LINE_SEND_SUCCESS", f"GroupID={group_id}")
        except Exception as e:
            log_user_action("LINE_SEND_FAILED", f"Error={str(e)}")

    # 記錄整體發送結果
    log_user_action("INCIDENT_BROADCAST_COMPLETE", 
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
    record_file = save_case_record(case_data)
    if record_file:
        log_user_action("CASE_RECORD_SAVED", f"RecordFile={record_file}")
    else:
        log_user_action("CASE_RECORD_FAILED", "Failed to save case record")

    return redirect("/Inform/10_Sended")


@app.route("/Inform/10_Sended")
def Inform_10_Sended():
    return render_template("/Inform/10_sended.html")


@app.route("/system/test")
def system_test():
    return render_template("/system/test.html")


@app.route("/system/test/line", methods=["POST"])
def test_line_bot():
    """測試 LINE Bot 功能"""
    try:
        # 記錄測試開始
        log_user_action("TEST_LINE_BOT_START")
        
        # 創建測試訊息
        test_message = (
            "🔧 系統測試訊息 / System Test Message\n"
            f"測試時間： {Time()}\n"
            "LINE Bot 功能正常運作！\n"
            "LINE Bot is working properly!"
        )
        
        # 發送測試訊息到群組
        send_group_message(group_id, test_message)
        
        # 記錄測試成功
        log_user_action("TEST_LINE_BOT_SUCCESS", f"GroupID={group_id}")
        logging.info("LINE Bot test message sent successfully")
        return jsonify({"success": True, "message": "LINE Bot 測試成功"})
        
    except Exception as e:
        # 記錄測試失敗
        log_user_action("TEST_LINE_BOT_FAILED", f"Error={str(e)}")
        logging.error(f"LINE Bot test failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/system/test/discord", methods=["POST"])
def test_discord():
    """測試 Discord Webhook 功能"""
    try:
        # 記錄測試開始
        log_user_action("TEST_DISCORD_START")
        
        # 創建測試訊息
        test_message = (
            "🔧 **系統測試訊息 / System Test Message**\n"
            f"**測試時間：** {Time()}\n"
            "Discord Webhook 功能正常運作！\n"
            "Discord Webhook is working properly!"
        )
        
        # 發送測試訊息
        message_id = discord_send(test_message)
        
        if message_id:
            # 記錄測試成功
            log_user_action("TEST_DISCORD_SUCCESS", f"MessageID={message_id}")
            logging.info(f"Discord test message sent successfully, ID: {message_id}")
            return jsonify({"success": True, "message": "Discord 測試成功", "message_id": message_id})
        else:
            # 記錄測試失敗
            log_user_action("TEST_DISCORD_FAILED", "Failed to send Discord message")
            logging.error("Discord test message failed to send")
            return jsonify({"success": False, "error": "Discord 訊息發送失敗"})
        
    except Exception as e:
        # 記錄測試失敗
        log_user_action("TEST_DISCORD_FAILED", f"Error={str(e)}")
        logging.error(f"Discord test failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/system/logs")
def system_logs():
    """系統日誌管理頁面"""
    return render_template("/system/logs.html")


@app.route("/system/records")
def system_records():
    """案件紀錄管理頁面"""
    return render_template("/system/records.html")


@app.route("/system/logs/files", methods=["GET"])
def get_log_files():
    """獲取可用的日誌檔案列表"""
    try:
        log_files = []
        
        if os.path.exists("logs"):
            for filename in os.listdir("logs"):
                if filename.startswith("flask_app_") and filename.endswith(".log"):
                    # 提取日期
                    date_str = filename.replace("flask_app_", "").replace(".log", "")
                    try:
                        # 轉換為可讀格式
                        date_obj = datetime.datetime.strptime(date_str, "%Y%m%d")
                        readable_date = date_obj.strftime("%Y-%m-%d")
                        
                        # 獲取檔案大小
                        file_path = os.path.join("logs", filename)
                        file_size = os.path.getsize(file_path)
                        
                        log_files.append({
                            "filename": filename,
                            "date": readable_date,
                            "size": file_size,
                            "size_mb": round(file_size / 1024 / 1024, 2)
                        })
                    except ValueError:
                        # 日期格式不正確，跳過
                        continue
        
        # 按日期排序（最新的在前）
        log_files.sort(key=lambda x: x["date"], reverse=True)
        
        return jsonify({
            "success": True,
            "files": log_files
        })
        
    except Exception as e:
        logging.error(f"Get log files failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/system/records/api", methods=["POST"])
def get_records_api():
    """獲取案件紀錄資料API"""
    try:
        data = request.get_json()
        case_type = data.get('case_type', 'all')
        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')
        
        records = []
        stats = {
            'total_cases': 0,
            'ohca_cases': 0,
            'internal_cases': 0,
            'surgical_cases': 0
        }
        
        # 如果沒有指定日期範圍，預設為今天
        if not date_from:
            date_from = datetime.datetime.now().strftime("%Y-%m-%d")
        if not date_to:
            date_to = date_from
        
        # 轉換日期格式並生成日期列表
        try:
            start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
            
            # 生成日期範圍
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                
                # 搜尋該日期的案件檔案
                if os.path.exists("record"):
                    for filename in os.listdir("record"):
                        if filename.startswith(f"case_{date_str}") and filename.endswith(".txt"):
                            try:
                                # 解析檔案名稱獲取時間
                                time_str = filename.replace("case_", "").replace(".txt", "")
                                case_time = datetime.datetime.strptime(time_str, "%Y%m%d_%H%M%S")
                                
                                # 讀取案件檔案
                                file_path = os.path.join("record", filename)
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                # 解析案件資訊
                                case_info = parse_case_record(content)
                                case_info['filename'] = filename
                                case_info['case_id'] = time_str
                                case_info['time'] = case_time.strftime("%Y-%m-%d %H:%M:%S")
                                
                                # 統計
                                stats['total_cases'] += 1
                                if case_info.get('event_type') == 'OHCA':
                                    stats['ohca_cases'] += 1
                                elif case_info.get('event_type') == '內科':
                                    stats['internal_cases'] += 1
                                elif case_info.get('event_type') == '外科':
                                    stats['surgical_cases'] += 1
                                
                                # 類型過濾
                                if case_type == 'all' or case_info.get('event_type') == case_type:
                                    records.append(case_info)
                                    
                            except Exception as e:
                                logging.error(f"Failed to parse case record {filename}: {e}")
                                continue
                
                current_date += datetime.timedelta(days=1)
        
        except ValueError as e:
            return jsonify({"success": False, "error": f"日期格式錯誤: {str(e)}"})
        
        # 按時間排序（最新的在前）
        records.sort(key=lambda x: x['case_id'], reverse=True)
        
        return jsonify({
            'success': True,
            'records': records,
            'stats': stats
        })
        
    except Exception as e:
        logging.error(f"Get records API failed: {e}")
        return jsonify({"success": False, "error": str(e)})


def parse_case_record(content):
    """解析案件紀錄檔案內容"""
    case_info = {}
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if '案件分類 / Case Type:' in line:
            case_info['event_type'] = line.split(':', 1)[1].strip()
        elif '案件地點 / Location:' in line:
            case_info['location'] = line.split(':', 1)[1].strip()
        elif '案件位置 / Position:' in line:
            case_info['room'] = line.split(':', 1)[1].strip()
        elif 'IP 地址 / IP Address:' in line:
            case_info['ip'] = line.split(':', 1)[1].strip()
        elif '國家 / Country:' in line:
            case_info['country'] = line.split(':', 1)[1].strip()
        elif '城市 / City:' in line:
            case_info['city'] = line.split(':', 1)[1].strip()
    
    return case_info


@app.route("/system/records/view/<filename>")
def view_record(filename):
    """查看案件紀錄詳情"""
    try:
        file_path = os.path.join("record", filename)
        
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "案件紀錄檔案不存在"})
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content
        })
        
    except Exception as e:
        logging.error(f"View record failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/system/records/download/<filename>")
def download_record(filename):
    """下載案件紀錄檔案"""
    try:
        file_path = os.path.join("record", filename)
        
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "案件紀錄檔案不存在"})
        
        from flask import send_file
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logging.error(f"Download record failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/system/records/export", methods=["POST"])
def export_records():
    """匯出案件紀錄檔案"""
    try:
        data = request.get_json()
        case_type = data.get('case_type', 'all')
        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')
        
        # 如果沒有指定日期範圍，預設為今天
        if not date_from:
            date_from = datetime.datetime.now().strftime("%Y-%m-%d")
        if not date_to:
            date_to = date_from
        
        records_content = []
        
        # 轉換日期格式並生成日期列表
        try:
            start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
            
            # 生成日期範圍
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                
                # 搜尋該日期的案件檔案
                if os.path.exists("record"):
                    for filename in os.listdir("record"):
                        if filename.startswith(f"case_{date_str}") and filename.endswith(".txt"):
                            try:
                                file_path = os.path.join("record", filename)
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                # 解析案件資訊進行過濾
                                case_info = parse_case_record(content)
                                if case_type == 'all' or case_info.get('event_type') == case_type:
                                    records_content.append(f"\n=== {filename} ===")
                                    records_content.append(content)
                                    
                            except Exception as e:
                                logging.error(f"Failed to read case record {filename}: {e}")
                                continue
                
                current_date += datetime.timedelta(days=1)
        
        except ValueError as e:
            return jsonify({"success": False, "error": f"日期格式錯誤: {str(e)}"})
        
        if not records_content:
            records_content.append("No case records found for the specified criteria.")
        
        # 創建回應
        from flask import Response
        filename = f"case_records_{date_from}_to_{date_to}.txt"
        response = Response(
            '\n'.join(records_content),
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Export records failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/system/records/clear", methods=["POST"])
def clear_records():
    """清除案件紀錄檔案"""
    try:
        data = request.get_json()
        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')
        
        # 如果沒有指定日期範圍，預設為今天
        if not date_from:
            date_from = datetime.datetime.now().strftime("%Y-%m-%d")
        if not date_to:
            date_to = date_from
        
        cleared_files = []
        
        # 轉換日期格式並生成日期列表
        try:
            start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
            
            # 生成日期範圍
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                
                # 搜尋該日期的案件檔案
                if os.path.exists("record"):
                    for filename in os.listdir("record"):
                        if filename.startswith(f"case_{date_str}") and filename.endswith(".txt"):
                            file_path = os.path.join("record", filename)
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                cleared_files.append(filename)
                
                current_date += datetime.timedelta(days=1)
        
        except ValueError as e:
            return jsonify({"success": False, "error": f"日期格式錯誤: {str(e)}"})
        
        # 記錄清除操作
        log_user_action("CLEAR_CASE_RECORDS", f"Cleared records from {date_from} to {date_to}")
        
        message = f"已清除 {len(cleared_files)} 個案件紀錄檔案" if cleared_files else "沒有找到要清除的案件紀錄檔案"
        return jsonify({"success": True, "message": message, "cleared_files": cleared_files})
        
    except Exception as e:
        logging.error(f"Clear records failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/records", methods=["GET"])
def api_get_all_records():
    """API: 獲取所有案件紀錄 (JSON格式)"""
    try:
        # 獲取查詢參數
        case_type = request.args.get('type', 'all')
        date_from = request.args.get('from', '')
        date_to = request.args.get('to', '')
        limit = int(request.args.get('limit', 100))  # 預設最多100筆
        offset = int(request.args.get('offset', 0))  # 分頁偏移
        
        records = []
        stats = {
            'total_cases': 0,
            'ohca_cases': 0,
            'internal_cases': 0,
            'surgical_cases': 0
        }
        
        # 如果沒有指定日期範圍，預設為今天
        if not date_from:
            date_from = datetime.datetime.now().strftime("%Y-%m-%d")
        if not date_to:
            date_to = date_from
        
        # 轉換日期格式並生成日期列表
        try:
            start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
            
            # 生成日期範圍
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                
                # 搜尋該日期的案件檔案
                if os.path.exists("record"):
                    for filename in os.listdir("record"):
                        if filename.startswith(f"case_{date_str}") and filename.endswith(".txt"):
                            try:
                                # 解析檔案名稱獲取時間
                                time_str = filename.replace("case_", "").replace(".txt", "")
                                case_time = datetime.datetime.strptime(time_str, "%Y%m%d_%H%M%S")
                                
                                # 讀取案件檔案
                                file_path = os.path.join("record", filename)
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                # 解析完整案件資訊
                                case_info = parse_case_record_full(content)
                                case_info['filename'] = filename
                                case_info['case_id'] = time_str
                                case_info['timestamp'] = case_time.isoformat()
                                case_info['time'] = case_time.strftime("%Y-%m-%d %H:%M:%S")
                                
                                # 統計
                                stats['total_cases'] += 1
                                if case_info.get('event_type') == 'OHCA':
                                    stats['ohca_cases'] += 1
                                elif case_info.get('event_type') == '內科':
                                    stats['internal_cases'] += 1
                                elif case_info.get('event_type') == '外科':
                                    stats['surgical_cases'] += 1
                                
                                # 類型過濾
                                if case_type == 'all' or case_info.get('event_type') == case_type:
                                    records.append(case_info)
                                    
                            except Exception as e:
                                logging.error(f"Failed to parse case record {filename}: {e}")
                                continue
                
                current_date += datetime.timedelta(days=1)
        
        except ValueError as e:
            return jsonify({"success": False, "error": f"日期格式錯誤: {str(e)}"})
        
        # 按時間排序（最新的在前）
        records.sort(key=lambda x: x['case_id'], reverse=True)
        
        # 分頁處理
        total_records = len(records)
        records = records[offset:offset + limit]
        
        return jsonify({
            "success": True,
            "data": {
                "records": records,
                "pagination": {
                    "total": total_records,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_records
                },
                "stats": stats,
                "filters": {
                    "case_type": case_type,
                    "date_from": date_from,
                    "date_to": date_to
                }
            },
            "timestamp": datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"API get all records failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/records/<case_id>", methods=["GET"])
def api_get_single_record(case_id):
    """API: 獲取單一案件紀錄 (JSON格式)"""
    try:
        # 搜尋案件檔案
        filename = f"case_{case_id}.txt"
        file_path = os.path.join("record", filename)
        
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "案件紀錄不存在"})
        
        # 讀取案件檔案
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析完整案件資訊
        case_info = parse_case_record_full(content)
        case_info['filename'] = filename
        case_info['case_id'] = case_id
        
        # 解析時間
        try:
            case_time = datetime.datetime.strptime(case_id, "%Y%m%d_%H%M%S")
            case_info['timestamp'] = case_time.isoformat()
            case_info['time'] = case_time.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            case_info['timestamp'] = None
            case_info['time'] = None
        
        return jsonify({
            "success": True,
            "data": case_info,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"API get single record failed: {e}")
        return jsonify({"success": False, "error": str(e)})


def parse_case_record_full(content):
    """解析案件紀錄檔案內容（完整版本）"""
    case_info = {}
    lines = content.split('\n')
    
    # 初始化所有欄位
    case_info.update({
        'event_type': None,
        'location': None,
        'room': None,
        'content': None,
        'message': None,
        'ip': None,
        'country': None,
        'city': None,
        'user_agent': None,
        'discord_success': False,
        'line_success': False,
        'discord_message_id': None,
        'server_time': None,
        'file_path': None
    })
    
    current_section = None
    message_lines = []
    
    for line in lines:
        line = line.strip()
        
        # 識別區段
        if '案件資訊 / Case Information:' in line:
            current_section = 'case_info'
            continue
        elif '通報者資訊 / Reporter Information:' in line:
            current_section = 'reporter_info'
            continue
        elif '廣播結果 / Broadcast Results:' in line:
            current_section = 'broadcast_results'
            continue
        elif '完整訊息內容 / Complete Message:' in line:
            current_section = 'message'
            continue
        elif '系統資訊 / System Information:' in line:
            current_section = 'system_info'
            continue
        elif line.startswith('-') or line.startswith('='):
            continue
        
        # 解析各區段內容
        if current_section == 'case_info':
            if '案件分類 / Case Type:' in line:
                case_info['event_type'] = line.split(':', 1)[1].strip()
            elif '案件地點 / Location:' in line:
                case_info['location'] = line.split(':', 1)[1].strip()
            elif '案件位置 / Position:' in line:
                case_info['room'] = line.split(':', 1)[1].strip()
            elif '補充資訊 / Additional Info:' in line:
                case_info['content'] = line.split(':', 1)[1].strip()
        
        elif current_section == 'reporter_info':
            if 'IP 地址 / IP Address:' in line:
                case_info['ip'] = line.split(':', 1)[1].strip()
            elif '國家 / Country:' in line:
                case_info['country'] = line.split(':', 1)[1].strip()
            elif '城市 / City:' in line:
                case_info['city'] = line.split(':', 1)[1].strip()
            elif '瀏覽器 / User Agent:' in line:
                case_info['user_agent'] = line.split(':', 1)[1].strip()
        
        elif current_section == 'broadcast_results':
            if 'Discord 發送 / Discord Send:' in line:
                case_info['discord_success'] = line.split(':', 1)[1].strip().lower() == 'true'
            elif 'LINE 發送 / LINE Send:' in line:
                case_info['line_success'] = line.split(':', 1)[1].strip().lower() == 'true'
            elif 'Discord 訊息 ID / Discord Message ID:' in line:
                case_info['discord_message_id'] = line.split(':', 1)[1].strip()
        
        elif current_section == 'message':
            if not line.startswith('-'):
                message_lines.append(line)
        
        elif current_section == 'system_info':
            if '伺服器時間 / Server Time:' in line:
                case_info['server_time'] = line.split(':', 1)[1].strip()
            elif '檔案路徑 / File Path:' in line:
                case_info['file_path'] = line.split(':', 1)[1].strip()
    
    # 組合完整訊息
    case_info['message'] = '\n'.join(message_lines)
    
    return case_info


@app.route("/api/stats", methods=["GET"])
def api_get_stats():
    """API: 獲取案件統計資料 (JSON格式)"""
    try:
        date_from = request.args.get('from', '')
        date_to = request.args.get('to', '')
        
        # 如果沒有指定日期範圍，預設為今天
        if not date_from:
            date_from = datetime.datetime.now().strftime("%Y-%m-%d")
        if not date_to:
            date_to = date_from
        
        stats = {
            'total_cases': 0,
            'ohca_cases': 0,
            'internal_cases': 0,
            'surgical_cases': 0,
            'by_location': {},
            'by_hour': {},
            'by_date': {}
        }
        
        # 轉換日期格式並生成日期列表
        try:
            start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
            
            # 生成日期範圍
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                
                # 搜尋該日期的案件檔案
                if os.path.exists("record"):
                    for filename in os.listdir("record"):
                        if filename.startswith(f"case_{date_str}") and filename.endswith(".txt"):
                            try:
                                # 解析檔案名稱獲取時間
                                time_str = filename.replace("case_", "").replace(".txt", "")
                                case_time = datetime.datetime.strptime(time_str, "%Y%m%d_%H%M%S")
                                
                                # 讀取案件檔案
                                file_path = os.path.join("record", filename)
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                # 解析案件資訊
                                case_info = parse_case_record(content)
                                
                                # 統計
                                stats['total_cases'] += 1
                                if case_info.get('event_type') == 'OHCA':
                                    stats['ohca_cases'] += 1
                                elif case_info.get('event_type') == '內科':
                                    stats['internal_cases'] += 1
                                elif case_info.get('event_type') == '外科':
                                    stats['surgical_cases'] += 1
                                
                                # 地點統計
                                location = case_info.get('location', 'Unknown')
                                stats['by_location'][location] = stats['by_location'].get(location, 0) + 1
                                
                                # 小時統計
                                hour = case_time.hour
                                stats['by_hour'][hour] = stats['by_hour'].get(hour, 0) + 1
                                
                                # 日期統計
                                date_key = case_time.strftime("%Y-%m-%d")
                                stats['by_date'][date_key] = stats['by_date'].get(date_key, 0) + 1
                                    
                            except Exception as e:
                                logging.error(f"Failed to parse case record {filename}: {e}")
                                continue
                
                current_date += datetime.timedelta(days=1)
        
        except ValueError as e:
            return jsonify({"success": False, "error": f"日期格式錯誤: {str(e)}"})
        
        return jsonify({
            "success": True,
            "data": {
                "stats": stats,
                "filters": {
                    "date_from": date_from,
                    "date_to": date_to
                }
            },
            "timestamp": datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"API get stats failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/system/logs/api", methods=["POST"])
def get_logs_api():
    """獲取日誌資料API"""
    try:
        data = request.get_json()
        log_type = data.get('log_type', 'all')
        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')
        ip_filter = data.get('ip_filter', '')
        
        logs = []
        stats = {
            'total_requests': 0,
            'user_actions': 0,
            'incidents': 0,
            'tests': 0
        }
        
        # 如果沒有指定日期範圍，預設為今天
        if not date_from:
            date_from = datetime.datetime.now().strftime("%Y-%m-%d")
        if not date_to:
            date_to = date_from
        
        # 轉換日期格式並生成日期列表
        try:
            start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
            
            # 生成日期範圍
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                log_filename = get_log_filename(date_str)
                
                # 讀取該日期的日誌檔案
                try:
                    with open(log_filename, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # IP 過濾（在解析前先過濾）
                            if ip_filter and ip_filter not in line:
                                continue
                            
                            # 解析日誌格式
                            if 'REQUEST:' in line:
                                stats['total_requests'] += 1
                                if log_type in ['all', 'request']:
                                    logs.append({
                                        'timestamp': line.split(']')[0][1:],
                                        'type': 'REQUEST',
                                        'content': line,
                                        'date': current_date.strftime("%Y-%m-%d")
                                    })
                            elif 'RESPONSE:' in line:
                                if log_type in ['all', 'response']:
                                    logs.append({
                                        'timestamp': line.split(']')[0][1:],
                                        'type': 'RESPONSE',
                                        'content': line,
                                        'date': current_date.strftime("%Y-%m-%d")
                                    })
                            elif 'USER_ACTION:' in line:
                                stats['user_actions'] += 1
                                if 'SUBMIT_INCIDENT' in line:
                                    stats['incidents'] += 1
                                elif 'TEST_' in line:
                                    stats['tests'] += 1
                                
                                if log_type in ['all', 'user-action']:
                                    logs.append({
                                        'timestamp': line.split(']')[0][1:],
                                        'type': 'USER_ACTION',
                                        'content': line,
                                        'date': current_date.strftime("%Y-%m-%d")
                                    })
                            elif 'ERROR' in line or 'WARNING' in line:
                                if log_type in ['all', 'error']:
                                    logs.append({
                                        'timestamp': line.split(']')[0][1:],
                                        'type': 'ERROR',
                                        'content': line,
                                        'date': current_date.strftime("%Y-%m-%d")
                                    })
                
                except FileNotFoundError:
                    # 該日期的日誌檔案不存在，跳過
                    pass
                
                current_date += datetime.timedelta(days=1)
        
        except ValueError as e:
            return jsonify({"success": False, "error": f"日期格式錯誤: {str(e)}"})
        
        # 按時間排序（最新的在前）
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 限制返回數量
        logs = logs[:1000]
        
        return jsonify({
            'success': True,
            'logs': logs,
            'stats': stats
        })
        
    except Exception as e:
        logging.error(f"Get logs API failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/system/logs/export", methods=["POST"])
def export_logs():
    """匯出日誌檔案"""
    try:
        data = request.get_json()
        log_type = data.get('log_type', 'all')
        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')
        ip_filter = data.get('ip_filter', '')
        
        # 如果沒有指定日期範圍，預設為今天
        if not date_from:
            date_from = datetime.datetime.now().strftime("%Y-%m-%d")
        if not date_to:
            date_to = date_from
        
        logs_content = []
        
        # 轉換日期格式並生成日期列表
        try:
            start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
            
            # 生成日期範圍
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                log_filename = get_log_filename(date_str)
                
                # 讀取該日期的日誌檔案
                try:
                    with open(log_filename, 'r', encoding='utf-8') as f:
                        # 添加日期分隔標記
                        logs_content.append(f"\n=== {current_date.strftime('%Y-%m-%d')} ===")
                        
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # 根據類型過濾
                            if log_type == 'request' and 'REQUEST:' not in line:
                                continue
                            elif log_type == 'response' and 'RESPONSE:' not in line:
                                continue
                            elif log_type == 'user-action' and 'USER_ACTION:' not in line:
                                continue
                            elif log_type == 'error' and 'ERROR' not in line and 'WARNING' not in line:
                                continue
                            
                            # IP 過濾
                            if ip_filter and ip_filter not in line:
                                continue
                            
                            logs_content.append(line)
                
                except FileNotFoundError:
                    logs_content.append(f"No logs found for {current_date.strftime('%Y-%m-%d')}")
                
                current_date += datetime.timedelta(days=1)
        
        except ValueError as e:
            return jsonify({"success": False, "error": f"日期格式錯誤: {str(e)}"})
        
        if not logs_content:
            logs_content.append("No logs found for the specified criteria.")
        
        # 創建回應
        from flask import Response
        filename = f"logs_{date_from}_to_{date_to}.txt"
        response = Response(
            '\n'.join(logs_content),
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Export logs failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/system/logs/clear", methods=["POST"])
def clear_logs():
    """清除日誌檔案"""
    try:
        data = request.get_json()
        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')
        
        # 如果沒有指定日期範圍，預設為今天
        if not date_from:
            date_from = datetime.datetime.now().strftime("%Y-%m-%d")
        if not date_to:
            date_to = date_from
        
        cleared_files = []
        
        # 轉換日期格式並生成日期列表
        try:
            start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
            
            # 生成日期範圍
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                log_filename = get_log_filename(date_str)
                
                # 清除該日期的日誌檔案
                if os.path.exists(log_filename):
                    os.remove(log_filename)
                    cleared_files.append(current_date.strftime("%Y-%m-%d"))
                
                current_date += datetime.timedelta(days=1)
        
        except ValueError as e:
            return jsonify({"success": False, "error": f"日期格式錯誤: {str(e)}"})
        
        # 記錄清除操作
        log_user_action("CLEAR_LOGS", f"Cleared logs from {date_from} to {date_to}")
        
        message = f"已清除 {len(cleared_files)} 個日誌檔案" if cleared_files else "沒有找到要清除的日誌檔案"
        return jsonify({"success": True, "message": message, "cleared_files": cleared_files})
        
    except Exception as e:
        logging.error(f"Clear logs failed: {e}")
        return jsonify({"success": False, "error": str(e)})


# 靜態頁面路由
@app.route("/Information/README")
def Information_README():
    return render_template("/Information/README.html")


@app.route("/Information/Privacy")
def Information_Privacy():
    return render_template("/Information/隱私權保護政策.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("/Information/404.html")


@app.errorhandler(500)
def server_error(e):
    return render_template("/Information/500.html")


if __name__ == "__main__":
    app.run()
