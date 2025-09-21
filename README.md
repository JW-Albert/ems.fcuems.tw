
# 緊急事件通報系統 / Emergency Management System

本專案是為了逢甲大學衛保救護隊設計的緊急事件通報系統，旨在快速傳遞事件資訊，提升應急處理效率。

This project is an emergency management system designed for the Feng Chia University Health and Safety Rescue Team, aimed at rapidly disseminating incident information and improving emergency response efficiency.

## 協作指南 / Collaboration Guidelines

請參閱 [協作指南](COLLABORATION_GUIDELINES.md)，了解提交流程與規範。

Please refer to [Collaboration Guidelines](COLLABORATION_GUIDELINES.md) for submission processes and standards.

## 功能簡介 / Features

1. **案件類別與分類選擇 / Case Category and Classification Selection** - 使用者可選擇事件的緊急程度與分類，例如內科、外科、OHCA 等。Users can select the urgency level and classification of incidents, such as internal medicine, surgery, OHCA, etc.

2. **地點與詳細資訊填寫 / Location and Detailed Information Entry** - 系統支援輸入事件地點、樓層及補充資訊。The system supports input of incident location, floor, and additional information.

3. **即時確認與通知 / Real-time Confirmation and Notification** - 系統提供案件確認頁面，並即時廣播訊息給相關人員。The system provides case confirmation pages and broadcasts messages to relevant personnel in real-time.

4. **多平台訊息廣播 / Multi-platform Message Broadcasting** - 支援 LINE Bot 和 Discord Webhook 進行訊息廣播。Supports LINE Bot and Discord Webhook for message broadcasting.

5. **系統測試功能 / System Testing Function** - 提供 LINE Bot 和 Discord Webhook 的快速測試功能，確保通訊正常運作。Provides quick testing functionality for LINE Bot and Discord Webhook to ensure proper communication.

6. **詳細日誌記錄 / Detailed Logging System** - 完整記錄使用者動作、請求回應、地理位置資訊，支援 Cloudflare Tunnel。Comprehensive logging of user actions, request responses, and geographic information with Cloudflare Tunnel support.

7. **案件紀錄管理 / Case Record Management** - 每個案件自動儲存為獨立檔案，包含完整案件資訊和通報者資料。Each case is automatically saved as an individual file with complete case information and reporter data.

8. **伺服器錯誤與頁面未建置提醒 / Server Error and Page Not Found Handling** - 提供自訂的 404 和 500 錯誤頁面，提升使用體驗。Provides custom 404 and 500 error pages to improve user experience.

9. **隱私與版權聲明 / Privacy and Copyright Statements** - 系統包含隱私權保護政策與版權宣告，確保資料使用合規。The system includes privacy protection policies and copyright statements to ensure compliant data usage.

## 使用技術 / Technologies Used

- **後端框架 / Backend Framework**: Flask
- **前端技術 / Frontend Technologies**: HTML、CSS
- **配置管理 / Configuration Management**: .env 檔案 / .env files
- **伺服器環境 / Server Environment**: Debian 10
- **其他 / Others**: LINE Bot API 用於訊息廣播功能 / LINE Bot API for message broadcasting functionality

## 系統結構 / System Structure

```plaintext
app.py                     - 主程式檔案 / Main application file
data/
    ├── .env              - 環境變數配置檔案 / Environment variables configuration file
templates/
    ├── Inform/            - 填報相關的頁面模板 / Incident reporting page templates
    │   ├── 02_event.html  - 案件分類選擇 / Case classification selection
    │   ├── 03_location.html - 地點輸入 / Location input
    │   ├── 05_room.html   - 教室或位置輸入 / Room or position input
    │   ├── 06_content.html - 補充資訊輸入 / Additional information input
    │   ├── 07_check.html  - 案件確認頁面 / Case confirmation page
    │   ├── 08_sending.html - 廣播傳送頁面 / Broadcasting transmission page
    │   └── 10_sended.html - 廣播完成頁面 / Broadcasting completion page
    ├── Information/       - 其他資訊頁面模板 / Other information page templates
    │   ├── 404.html       - 404 頁面未建置 / 404 page not found
    │   ├── 500.html       - 500 伺服器錯誤 / 500 server error
    │   ├── README.html    - 網站資訊頁 / Website information page
    │   ├── 著作權宣告.html - 版權宣告 / Copyright statement
    │   └── 隱私權保護政策.html - 隱私權政策 / Privacy policy
    └── system/            - 系統管理頁面模板 / System management page templates
        ├── test.html     - 系統測試頁面 / System test page
        ├── logs.html     - 日誌管理頁面 / Log management page
        └── records.html  - 案件紀錄管理頁面 / Case records management page
server/
    ├── boot.sh           - 伺服器啟動腳本 / Server boot script
    ├── setup.sh          - 系統安裝腳本 / System installation script
    └── ems-flask.service - systemd 服務檔案 / systemd service file
```

## 安裝與執行 / Installation and Execution

### 前置需求 / Prerequisites

1. 安裝 Python 3.8 或更新版本 / Install Python 3.8 or newer
2. 安裝相關套件，請執行以下指令 / Install required packages with the following commands:
   ```bash
   pip install -r requirements.txt
   ```
3. 配置環境變數 / Configure environment variables:
   - 複製 `data/.env.example` 到 `data/.env` / Copy `data/.env.example` to `data/.env`
   - 填入您的 LINE Bot API 金鑰、Discord Webhook URL 等 / Fill in your LINE Bot API keys, Discord Webhook URL, etc.

### 執行方式 / Execution Methods

1. 開發環境執行 / Development environment execution:
   ```bash
   python app.py
   ```
2. 生產環境部署 / Production environment deployment:
   ```bash
   # 使用提供的安裝腳本 / Use the provided installation script
   ./server/setup.sh
   ```
3. 開啟瀏覽器，訪問 `http://127.0.0.1:5000` 進入系統主頁 / Open browser and visit `http://127.0.0.1:5000` to access the system homepage.

### 系統測試 / System Testing

系統提供快速測試功能，確保 LINE Bot 和 Discord Webhook 正常運作：

The system provides quick testing functionality to ensure LINE Bot and Discord Webhook are working properly:

1. 訪問測試頁面 / Access test page: `http://127.0.0.1:5000/system/test`
2. 點擊「測試 LINE Bot」按鈕測試 LINE 群組訊息 / Click "Test LINE Bot" button to test LINE group message
3. 點擊「測試 Discord」按鈕測試 Discord 頻道訊息 / Click "Test Discord" button to test Discord channel message
4. 查看測試結果和狀態訊息 / Check test results and status messages

### 日誌管理 / Log Management

系統提供完整的日誌管理功能，記錄所有使用者動作和系統事件：

The system provides comprehensive log management functionality, recording all user actions and system events:

1. 訪問日誌頁面 / Access log page: `http://127.0.0.1:5000/system/logs`
2. 查看即時統計資料 / View real-time statistics
3. 過濾和搜尋日誌 / Filter and search logs
4. 匯出日誌檔案 / Export log files
5. 清除舊日誌 / Clear old logs

**記錄內容包括 / Logged content includes:**
- 使用者 IP 地址和地理位置 / User IP address and geographic location
- 所有頁面訪問和動作 / All page visits and actions
- 事件通報詳細資訊 / Incident reporting details
- 系統測試結果 / System test results
- 錯誤和警告訊息 / Error and warning messages

**日誌檔案管理 / Log File Management:**
- 每天自動創建新的日誌檔案 / Automatic daily log file creation
- 檔案命名格式：`flask_app_YYYYMMDD.log` / File naming format: `flask_app_YYYYMMDD.log`
- 支援多天日誌查詢和匯出 / Support multi-day log query and export
- 自動日誌輪轉，避免單一檔案過大 / Automatic log rotation to prevent oversized files

### 案件紀錄管理 / Case Record Management

系統提供完整的案件紀錄管理功能，每個案件都會自動儲存為獨立檔案：

The system provides comprehensive case record management functionality, with each case automatically saved as an individual file:

1. 訪問案件紀錄頁面 / Access case records page: `http://127.0.0.1:5000/system/records`
2. 查看案件統計資料 / View case statistics
3. 按案件類型、日期範圍過濾 / Filter by case type and date range
4. 查看案件詳情和下載個別檔案 / View case details and download individual files
5. 匯出和清除案件紀錄 / Export and clear case records

**案件紀錄內容包括 / Case record content includes:**
- 案件基本資訊（類型、地點、位置、補充資訊）/ Basic case information (type, location, position, additional info)
- 通報者資訊（IP、地理位置、瀏覽器）/ Reporter information (IP, geographic location, browser)
- 廣播結果（Discord、LINE 發送狀態）/ Broadcast results (Discord, LINE send status)
- 完整訊息內容和系統資訊 / Complete message content and system information

**案件檔案管理 / Case File Management:**
- 檔案命名格式：`case_YYYYMMDD_HHMMSS.txt` / File naming format: `case_YYYYMMDD_HHMMSS.txt`
- 每個案件一個檔案，便於管理和查詢 / One file per case for easy management and query
- 支援多天案件查詢和匯出 / Support multi-day case query and export
- 自動儲存到 `record/` 資料夾 / Automatically saved to `record/` folder

## 環境變數配置 / Environment Variables Configuration

系統使用 `.env` 檔案進行配置管理，包含以下變數：

The system uses `.env` files for configuration management, including the following variables:

```env
# LINE Bot 設定 / LINE Bot Configuration
LINE_BOT_API_TOKEN=your_line_bot_api_token
LINE_WEBHOOK_HANDLER=your_webhook_handler
LINE_GROUP_ID=your_group_id

# Discord Webhook 設定 / Discord Webhook Configuration
DISCORD_WEBHOOK_URL=your_discord_webhook_url

# 資料庫設定 / Database Configuration
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=emergency_system
```

## 版權與授權 / Copyright and License

- **版權擁有者 / Copyright Owner**: 王建葦
- **授權對象 / Licensee**: 逢甲大學衛保救護隊 / Feng Chia University Health and Safety Rescue Team
- **版本 / Version**: Alpha 2.0.0

## 聯絡方式 / Contact Information

- **管理員名稱 / Administrator Name**: 王建葦
- **管理員信箱 / Administrator Email**: [admin@mail.jw-albert.tw](mailto:admin@mail.jw-albert.tw)
- **伺服器資訊 / Server Information**: ems.fcuems.tw (Debian 10)

## 隱私權政策與版權 / Privacy Policy and Copyright

本系統遵守相關隱私權保護條款，所有使用者資料將嚴格保密，詳細條款請參閱 [隱私權保護政策](templates/Information/PRIVACY_POLICY.md) 與 [著作權宣告](templates/Information/COPYRIGHT_NOTICE.md)。

This system complies with relevant privacy protection terms. All user data will be strictly confidential. For detailed terms, please refer to [Privacy Policy](templates/Information/PRIVACY_POLICY.md) and [Copyright Notice](templates/Information/COPYRIGHT_NOTICE.md).
