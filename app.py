from flask import Flask, request, abort, render_template, redirect, session
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent
import datetime
import email.message
import smtplib
import pymysql
import pandas as pd
import logging
from dhooks import Webhook
import os
import requests
import threading
import time

app = Flask(__name__, static_folder="static", static_url_path="/")
app.secret_key = "secret_key"
app.config["SESSION_TYPE"] = "filesystem"

# 廣播寄送控制
line = 1
discord = 1
mail = 0


def Time() -> str:
    now = datetime.datetime.now().strftime("%Y年%m月%d日 %H時%M分%S秒")
    return now


def open_csv(file: str) -> pd.DataFrame:
    data = pd.read_csv(file + ".csv")
    return data


# LINE Bot 設定
line_bot_info = open_csv("data/line_bot")
line_bot_api = LineBotApi(line_bot_info["LineBotApi"][0])
handler = WebhookHandler(line_bot_info["WebhookHandler"][0])

group_id = open_csv("data/line_group")
group_id = group_id["group_id"][0]

# 確保 logs 目錄存在
if not os.path.exists("logs"):
    os.makedirs("logs")

# 使用當前日期作為日誌文件名
current_date = datetime.datetime.now().strftime("%Y%m%d")
log_filename = f"logs/flask_app_{current_date}.log"

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def get_real_ip():
    if request.headers.get("CF-Connecting-IP"):
        return request.headers["CF-Connecting-IP"]
    elif request.headers.get("X-Forwarded-For"):
        return request.headers["X-Forwarded-For"].split(",")[0]
    else:
        return request.remote_addr


@app.before_request
def log_request_info():
    ip = get_real_ip()
    method = request.method
    path = request.path
    user_agent = request.headers.get("User-Agent", "Unknown")
    logging.info(f"Access: IP={ip} Method={method} Path={path} User-Agent={user_agent}")


@app.after_request
def log_response_info(response):
    logging.info(f"Response: Status={response.status_code} Path={request.path}")
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
discord_info = open_csv("data/discord_hook")
webhook_url = discord_info["Webhook"][0]
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
    session["event"] = int(request.form.get("event"))
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
    else:
        session["locat"] = "99"
        locat_table.update({99: custom_location})

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
    return redirect("/Inform/06_Content")


@app.route("/Inform/06_Content")
def Inform_06_Content():
    return render_template("/Inform/06_content.html")


@app.route("/Inform/Read_06_Content", methods=["POST"])
def Inform_Read_06_Content():
    session["content"] = request.form.get("content", "")
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

    if discord == 1:
        message_id = discord_send(session["message"] + "\n@everyone\n# [事件回覆](https://forms.gle/dww4orwk2RHSbVV2A)")
        if message_id:
            schedule_discord_edit(message_id, session["message"] + "\n@everyone\n# [事件回覆](https://forms.gle/dww4orwk2RHSbVV2A)")
    if line == 1:
        broadcast_message(group_id, session["message"])

    return redirect("/Inform/10_Sended")


@app.route("/Inform/10_Sended")
def Inform_10_Sended():
    return render_template("/Inform/10_sended.html")


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
