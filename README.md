
# 緊急事件通報系統

本專案是為了逢甲大學衛保救護隊設計的緊急事件通報系統，旨在快速傳遞事件資訊，提升應急處理效率。

## 協作指南

請參閱 [協作指南](COLLABORATION_GUIDELINES.md)，了解提交流程與規範。

## 功能簡介

1. **案件類別與分類選擇** - 使用者可選擇事件的緊急程度與分類，例如內科、外科、OHCA 等。
2. **地點與詳細資訊填寫** - 系統支援輸入事件地點、樓層及補充資訊。
3. **即時確認與通知** - 系統提供案件確認頁面，並即時廣播訊息給相關人員。
4. **伺服器錯誤與頁面未建置提醒** - 提供自訂的 404 和 500 錯誤頁面，提升使用體驗。
5. **隱私與版權聲明** - 系統包含隱私權保護政策與版權宣告，確保資料使用合規。

## 使用技術

- **後端框架**: Flask
- **前端技術**: HTML、CSS
- **資料庫**: MySQL，使用 PyMySQL 驅動進行連接與操作
- **伺服器環境**: Debian 10
- **其他**: LINE Bot API 用於訊息廣播功能

## 系統結構

```plaintext
app.py                     - 主程式檔案
templates/
    ├── Inform/            - 填報相關的頁面模板
    │   ├── 01_case.html   - 案件類別選擇
    │   ├── 02_event.html  - 案件分類選擇
    │   ├── 03_location.html - 地點輸入
    │   ├── 04_floor.html  - 樓層輸入
    │   ├── 05_room.html   - 教室或位置輸入
    │   ├── 06_content.html - 補充資訊輸入
    │   ├── 07_check.html  - 案件確認頁面
    │   ├── 08_sending.html - 廣播傳送頁面
    │   ├── 10_sended.html - 廣播完成頁面
    ├── Information/       - 其他資訊頁面模板
        ├── 404.html       - 404 頁面未建置
        ├── 500.html       - 500 伺服器錯誤
        ├── README.html    - 網站資訊頁
        ├── 著作權宣告.html - 版權宣告
        └── 隱私權保護政策.html - 隱私權政策
```

## 安裝與執行

### 前置需求

1. 安裝 Python 3.8 或更新版本
2. 安裝相關套件，請執行以下指令：
   ```bash
   pip install flask
   pip install pandas
   pip install pymysql
   pip install line-bot-sdk
   ```
3. 建立 MySQL 資料庫，並初始化以下結構（僅示例）：
   ```sql
   CREATE DATABASE emergency_system;
   USE emergency_system;

   CREATE TABLE cases (
       id INT AUTO_INCREMENT PRIMARY KEY,
       case_type VARCHAR(255) NOT NULL,
       event_type VARCHAR(255) NOT NULL,
       location VARCHAR(255),
       floor INT,
       room VARCHAR(255),
       additional_info TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

### 執行方式

1. 啟動伺服器：
   ```bash
   python app.py
   ```
2. 開啟瀏覽器，訪問 `http://127.0.0.1:5000` 進入系統主頁。

## 版權與授權

- **版權擁有者**: 王建葦
- **授權對象**: 逢甲大學衛保救護隊
- **版本**: Alpha 2.0.0

## 聯絡方式

- **管理員名稱**: 王建葦
- **管理員信箱**: [jw.albert.tw@gmail.com](mailto:jw.albert.tw@gmail.com)
- **伺服器資訊**: ems.fcuems.tw (Debian 10)

## 隱私權政策與版權

本系統遵守相關隱私權保護條款，所有使用者資料將嚴格保密，詳細條款請參閱 [隱私權保護政策](PRIVACY_POLICY.md) 與 [著作權宣告](COPYRIGHT_NOTICE.md)。
