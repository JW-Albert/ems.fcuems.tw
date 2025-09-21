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
line = 0
discord = 0

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

# 公開API路由（供外部訪問）
@app.route("/api/stats", methods=["GET"])
def get_stats():
    """獲取系統統計資料"""
    try:
        # 獲取案件統計
        case_files = case_manager.get_case_files()
        case_stats = case_manager.get_case_stats()
        
        # 獲取日誌統計
        log_files = logger_manager.get_log_files()
        
        return jsonify({
            "success": True,
            "data": {
                "cases": {
                    "total": len(case_files),
                    "today": case_stats.get('total_cases', 0),
                    "ohca": case_stats.get('ohca_cases', 0),
                    "internal": case_stats.get('internal_cases', 0),
                    "surgical": case_stats.get('surgical_cases', 0)
                },
                "logs": {
                    "total_files": len(log_files),
                    "latest_file": log_files[0]['filename'] if log_files else None
                },
                "system": {
                    "status": "running",
                    "uptime": "active"
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/cases", methods=["GET"])
def get_cases():
    """獲取案件列表（公開API）"""
    try:
        # 獲取查詢參數
        case_type = request.args.get('type', 'all')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        # 獲取案件檔案
        case_files = case_manager.get_case_files()
        
        # 過濾案件
        filtered_cases = []
        for case_file in case_files[offset:offset+limit]:
            content = case_manager.read_case_file(case_file['filename'])
            if content:
                case_info = case_manager.parse_case_record(content)
                if case_type == 'all' or case_info.get('event_type') == case_type:
                    case_info.update(case_file)
                    filtered_cases.append(case_info)
        
        return jsonify({
            "success": True,
            "data": {
                "cases": filtered_cases,
                "total": len(case_files),
                "limit": limit,
                "offset": offset
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/cases/<case_id>", methods=["GET"])
def get_case_detail(case_id):
    """獲取特定案件詳情"""
    try:
        content = case_manager.read_case_file(case_id)
        if content:
            case_info = case_manager.parse_case_record_full(content)
            return jsonify({
                "success": True,
                "data": case_info
            })
        else:
            return jsonify({"success": False, "error": "案件不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/logs", methods=["GET"])
def get_logs():
    """獲取日誌資料（公開API）"""
    try:
        # 獲取查詢參數
        log_type = request.args.get('type', 'all')
        limit = int(request.args.get('limit', 50))
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # 如果沒有指定日期範圍，預設為今天
        if not date_from:
            date_from = datetime.datetime.now().strftime("%Y-%m-%d")
        if not date_to:
            date_to = date_from
        
        logs = []
        stats = {
            'total_requests': 0,
            'user_actions': 0,
            'incidents': 0,
            'tests': 0
        }
        
        # 轉換日期格式並生成日期列表
        try:
            start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
            
            # 生成日期範圍
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                log_filename = logger_manager.get_log_filename(date_str)
                
                # 讀取日誌檔案
                if os.path.exists(log_filename):
                    log_lines = logger_manager.read_log_file(os.path.basename(log_filename))
                    
                    for line in log_lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 解析日誌行
                        try:
                            if ' [' in line and '] ' in line:
                                parts = line.split(' [', 2)
                                if len(parts) >= 2:
                                    timestamp = parts[0]
                                    level_message = parts[1]
                                    if '] ' in level_message:
                                        level, message = level_message.split('] ', 1)
                                        level = level.strip()
                                        message = message.strip()
                                        
                                        # 類型過濾
                                        if log_type != 'all' and level.lower() != log_type.lower():
                                            continue
                                        
                                        logs.append({
                                            'timestamp': timestamp,
                                            'type': level,
                                            'content': message
                                        })
                                        
                                        # 統計
                                        stats['total_requests'] += 1
                                        if 'USER_ACTION' in message or 'User Action' in message:
                                            stats['user_actions'] += 1
                                        elif 'INCIDENT' in message or '案件' in message:
                                            stats['incidents'] += 1
                                        elif 'TEST' in message or '測試' in message:
                                            stats['tests'] += 1
                        except Exception:
                            continue
                
                current_date += datetime.timedelta(days=1)
        
        except ValueError as e:
            return jsonify({"success": False, "error": f"日期格式錯誤: {str(e)}"}), 400
        
        # 按時間排序並限制數量
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        logs = logs[:limit]
        
        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "stats": stats,
                "total": len(logs)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 注意：敏感操作（如清除、匯出）仍保留在管理網站中

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
    
    # 準備案件資料
    case_data = {
        'event_type': event_table.get(session.get('event', 0), 'Unknown'),
        'location': session.get('locat_table', {}).get(session.get('locat', 0), 'Unknown'),
        'room': session.get('room', 'Unknown'),
        'content': session.get('content', 'Unknown'),
        'message': session.get('message', 'Unknown')
    }
    
    return render_template("Inform/10_sended.html", case_data=case_data)

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
        session["locat_table"].update({"99": custom_location})
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
        f"案件地點： {session['locat_table'].get(session['locat'], 'Unknown')}\n"
        f"案件位置： {session['room']}\n"
        f"案件補充：\n\t{content_with_tabs}\n"
        f"通報時間： {Time()}"
    )

    # 記錄事件通報
    logger_manager.log_user_action("提交案件通報", 
        f"Event={event_table[session['event']]} | "
        f"Location={session['locat_table'].get(session['locat'], 'Unknown')} | "
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

    # 獲取通報者資訊
    user_info = logger_manager.get_user_info()
    
    # 準備案件資料並儲存紀錄
    case_data = {
        'event_type': event_table[session['event']],
        'location': session['locat_table'].get(session['locat'], 'Unknown'),
        'room': session['room'],
        'content': session['content'],
        'message': session["message"],
        'discord_success': discord_success,
        'line_success': line_success,
        'discord_message_id': discord_message_id,
        'ip': user_info.get('ip', 'Unknown'),
        'country': user_info.get('country', 'Unknown'),
        'city': user_info.get('city', 'Unknown'),
        'user_agent': user_info.get('user_agent', 'Unknown')
    }
    
    # 儲存案件紀錄
    try:
        filename = case_manager.save_case_record(case_data)
        logger_manager.log_user_action("案件紀錄已保存", f"RecordFile={filename}")
    except Exception as e:
        logger_manager.log_user_action("案件紀錄保存失敗", f"Failed to save case record: {e}")

    return redirect("/Inform/Read_10_Sended")

# 注意：系統管理功能已移至獨立的管理網站 (admin_app.py)
# 管理網站運行在端口 5001，提供日誌管理、案件紀錄管理和系統測試功能

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
