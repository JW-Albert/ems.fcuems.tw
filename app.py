from flask import Flask, request, abort, render_template, redirect, session
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent
import datetime
import email.message
import smtplib
import pymysql
import pandas as pd
from dhooks import Webhook

app = Flask(__name__, static_folder="static", static_url_path="/")
app.secret_key = 'secret_key'
app.config['SESSION_TYPE'] = 'filesystem'



# 廣播寄送控制
line = 1
discord = 1
mail = 0
t_mail = 0 #資料庫尚未建置



################################ 前置函數 ################################
def sql_search(table) -> pd.DataFrame:
    db = pymysql.connect(host='localhost', port=3306, user='fcuemsadmin', passwd='FCUems@2541', charset='utf8', db='fcuems')
    sql = "SELECT * FROM `"+ table +"`"
    data = pd.read_sql(sql, db)
    db.close()
    return data

def Time() -> str:
    now = datetime.datetime.now().strftime("%Y年%m月%d日 %H時%M分%S秒")
    return now

def mail_msg(who: str) -> email.message.EmailMessage:
    msg = email.message.EmailMessage()
    msg["From"] = "自己填你的"
    msg["To"] = who
    msg["Subject"] = f"逢甲大學 緊急事件通報系統 案件類型 「{case_table[session['case']]}」 緊急事件通知"
    msg.set_content(session.get('message', ''))
    return msg

def send_mail(sql :str) -> None:
    mail_data = sql_search(sql)
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login("自己填你的", "自己去設定")
    for email in mail_data["EMAIL"]:
        msg = mail_msg(email)
        server.send_message(msg)
    server.close()

def open_csv(file :str) -> pd.DataFrame:
    data = pd.read_csv(file + ".csv")
    return data



################################ LINE ################################
# 設定 LINE Bot 的認證資訊
line_bot_info = open_csv("data/line_bot")
line_bot_api = LineBotApi(line_bot_info["LineBotApi"][0])
handler = WebhookHandler(line_bot_info["WebhookHandler"][0])

group_id = open_csv("data/line_group")
group_id = group_id["group_id"][0]

# Line Bot 返回資訊
@app.route("/bot/callback", methods=['POST'])
def bot_callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 加入群組顯示群組 ID
@handler.add(JoinEvent)
def handle_join(event):
    group_id = event.source.group_id
    print(f"Bot has joined the group with groupId: {group_id}")
    line_bot_api.push_message(group_id, TextSendMessage(text="大家好！我是逢甲大學衛保救護隊的報警機器人!\n本群組ID: {group_id}"))

# 訊號測試
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_token = event.reply_token
    if user_message == "訊號測試":
        line_bot_api.reply_message(reply_token, TextSendMessage(text="訊號良好"))

# 單獨用戶寄發(好友)
def send_person_message(message):
    line_bot_api.broadcast(TextSendMessage(text=message))

# 群組用戶寄發
def send_group_message(group_id, message):
    line_bot_api.push_message(group_id, TextSendMessage(text=message))

# 寄送報警訊息
def broadcast_message(group_id, message):
    # 寄送予好友
    send_person_message(message)
    # 寄送予群組
    send_group_message(group_id, message)



################################ Discord  ################################
#Discord Webhook
discord_info = open_csv("data/discord_hook")
hook = Webhook(discord_info["Webhook"][0])
def discord_send(message):
    hook.send(message)



################################ 主程式 ################################
case_table = {1: "危急", 2: "一般"}
event_table = {1: "OHCA(暈倒)", 2: "內科", 3: "外科"}
locat_table = {1: "行政大樓", 2: "行政二館", 3: "紀念館", 4: "圖書館", 5: "科航", 6: "商學", 7: "忠勤", 8: "建築", 9: "語文", 10: "工學",
               11: "人言", 12: "資電", 13: "人社", 14: "電通", 15: "育樂", 16: "土木", 17: "理學", 18: "學思", 19: "體育館", 20: "文創中心",
               21: "共善"}

@app.route("/")
@app.route("/Inform/01_Case")
def Inform_01_Case():
    session['case'] = 0
    session['event'] = 0
    session['locat'] = "0"
    session['room'] = "NULL"
    session['content'] = ""
    session['message'] = "NULL"
    return render_template("/Inform/01_case.html")

@app.route("/Inform/Read_01_Case", methods=["POST"])
def Inform_Read_01_Case():
    session['case'] = int(request.form.get("case"))
    return redirect("/Inform/02_Event")

@app.route("/Inform/02_Event")
def Inform_02_Event():
    return render_template("/Inform/02_event.html")

@app.route("/Inform/Read_02_Event", methods=["POST"])
def Inform_Read_02_Event():
    session['event'] = int(request.form.get("event"))
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

    if(selected_button != 0):
        session['locat'] = str(selected_button)
    else:
        session['locat'] = "99"
        locat_table.update({99: custom_location})
    
    session['locat_table'] = locat_table

    return redirect("/Inform/05_Room")

@app.route("/Inform/05_Room")
def Inform_05_Room():
    return render_template("/Inform/05_room.html")

@app.route("/Inform/Read_05_Room", methods=["POST"])
def Inform_Read_05_Room():
    session['room'] = request.form.get("room")
    return redirect("/Inform/06_Content")

@app.route("/Inform/06_Content")
def Inform_06_Content():
    return render_template("/Inform/06_content.html")

@app.route("/Inform/Read_06_Content", methods=["POST"])
def Inform_Read_06_Content():
    session['content'] = request.form.get("content", "")
    return redirect("/Inform/07_Check")

@app.route("/Inform/07_Check")
def Inform_07_Check():
    return render_template("/Inform/07_check.html",
                           case=case_table[session['case']],
                           event=event_table[session['event']],
                           locat=session['locat_table'][session['locat']],
                           room=session['room'],
                           content=session['content'])

@app.route("/Inform/08_Send")
def Inform_08_Send():
    return render_template("/Inform/08_sending.html")

@app.route("/Inform/09_Sending")
def Inform_09_Sending():
    # 處理內容中的換行符
    content_with_tabs = session['content'].replace('\n', '\n\t')
    
    # 使用多行字串組合訊息
    session['message'] = (
        "緊急事件通報\n"
        f"案件類型：{case_table[session['case']]}\n"
        f"案件分類：{event_table[session['event']]}\n"
        f"案件地點：{session['locat_table'][session['locat']]}\n"
        f"案件位置：{session['room']}\n"
        f"案件補充：\n\t{content_with_tabs}\n"
        f"通報時間：{Time()}"
    )

    if(discord == 1):
        discord_send(session['message']+"\n@everyone")
    if(mail == 1):
        send_mail("EMT")
    if(t_mail == 1):
        send_mail("T_EMT")
    if(line == 1):
        broadcast_message(group_id, session['message'])
    
    return redirect("/Inform/10_Sended")

@app.route("/Inform/10_Sended")
def Inform_10_Sended():
    return render_template("/Inform/10_sended.html")


################################ 靜態區 ################################
#伺服器狀態與資訊頁
@app.route("/Information/README")
def Information_README():
    return render_template("/Information/README.html")

#隱私權保護政策頁面
@app.route("/Information/Privacy")
def Information_Privacy():
    return render_template("/Information/隱私權保護政策.html")

#Error 404頁面
@app.errorhandler(404)
def page_not_found(e):
    return render_template("/Information/404.html")

#Error 500頁面
@app.errorhandler(500)
def server_error(e):
    return render_template("/Information/500.html")

if __name__ == '__main__':
    app.run()
