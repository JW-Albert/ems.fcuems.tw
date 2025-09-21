# 🔧 模組化重構說明

## 📋 重構概述

原本的 `app.py` 檔案過於冗長（1575行），已成功重構為模組化架構，提高程式碼的可維護性和可讀性。

## 🏗️ 新架構結構

### 1. **配置管理模組** (`config.py`)
- **功能**：統一管理所有配置參數
- **特點**：
  - 自動載入 `.env` 檔案
  - 配置驗證功能
  - 自動創建必要目錄
  - 集中管理所有環境變數

### 2. **日誌管理模組** (`logger.py`)
- **功能**：完整的日誌系統管理
- **特點**：
  - 支援Cloudflare Tunnel
  - 每日日誌檔案輪替
  - 詳細的使用者動作記錄
  - 日誌檔案管理功能

### 3. **案件管理模組** (`case_manager.py`)
- **功能**：案件紀錄的完整管理
- **特點**：
  - 案件檔案保存和讀取
  - 案件資料解析（簡化版和完整版）
  - 案件統計功能
  - 案件檔案清理功能

### 4. **訊息廣播模組** (`message_broadcaster.py`)
- **功能**：LINE和Discord訊息發送
- **特點**：
  - 統一的訊息廣播介面
  - 測試功能
  - 訊息格式化
  - 廣播控制功能

### 5. **API路由模組** (`api_routes.py`)
- **功能**：所有API端點的處理
- **特點**：
  - RESTful API設計
  - JSON格式回應
  - 分頁支援
  - 統計功能

### 6. **主程式** (`app.py`)
- **功能**：Flask應用程式主體
- **特點**：
  - 簡化的路由定義
  - 模組化導入
  - 清晰的程式結構

## 📊 重構前後對比

| 項目 | 重構前 | 重構後 |
|------|--------|--------|
| 主程式行數 | 1575行 | ~200行 |
| 模組數量 | 1個 | 6個 |
| 可維護性 | 低 | 高 |
| 可讀性 | 低 | 高 |
| 功能分離 | 無 | 完整 |

## 🚀 使用方式

### 1. **安裝依賴**
```bash
pip install -r requirements.txt
```

### 2. **配置環境變數**
確保 `data/.env` 檔案包含必要的配置：
```env
LINE_BOT_API_TOKEN=your_token_here
LINE_WEBHOOK_HANDLER=your_handler_here
LINE_GROUP_ID=your_group_id_here
DISCORD_WEBHOOK_URL=your_webhook_url_here
SECRET_KEY=your_secret_key_here
```

### 3. **啟動應用程式**
```bash
python app.py
```

## 🔧 模組功能說明

### 配置管理 (`config.py`)
```python
from config import config

# 獲取配置
secret_key = config.SECRET_KEY
line_token = config.LINE_BOT_API_TOKEN

# 驗證配置
config.validate_config()
```

### 日誌管理 (`logger.py`)
```python
from logger import logger_manager

# 記錄使用者動作
logger_manager.log_user_action("頁面訪問", "主頁面")

# 記錄錯誤
logger_manager.log_error("錯誤訊息", "上下文")

# 獲取使用者資訊
user_info = logger_manager.get_user_info()
```

### 案件管理 (`case_manager.py`)
```python
from case_manager import case_manager

# 保存案件紀錄
filename = case_manager.save_case_record(case_data)

# 讀取案件檔案
content = case_manager.read_case_file(filename)

# 解析案件資料
case_info = case_manager.parse_case_record(content)

# 獲取統計資料
stats = case_manager.get_case_stats("2024-01-15", "2024-01-16")
```

### 訊息廣播 (`message_broadcaster.py`)
```python
from message_broadcaster import message_broadcaster

# 廣播訊息
results = message_broadcaster.broadcast_message(message_content, case_data)

# 測試LINE
result = message_broadcaster.test_line_message()

# 測試Discord
result = message_broadcaster.test_discord_message()

# 格式化案件訊息
message = message_broadcaster.format_case_message(case_data)
```

## 📁 檔案結構

```
ems.fcuems.tw/
├── app.py                 # 主程式（重構後）
├── app_backup.py          # 原始程式備份
├── config.py              # 配置管理模組
├── logger.py              # 日誌管理模組
├── case_manager.py        # 案件管理模組
├── message_broadcaster.py # 訊息廣播模組
├── api_routes.py          # API路由模組
├── test_modules.py        # 模組測試腳本
├── requirements.txt       # 依賴清單
├── data/
│   └── .env              # 環境變數配置
├── logs/                 # 日誌檔案目錄
├── record/               # 案件紀錄目錄
└── templates/            # 模板檔案
```

## ✅ 重構優勢

1. **可維護性提升**：每個模組職責單一，易於維護
2. **可讀性提升**：程式碼結構清晰，易於理解
3. **可擴展性提升**：新功能可以獨立模組開發
4. **可測試性提升**：每個模組可以獨立測試
5. **程式碼重用**：模組可以在其他專案中重用

## 🔄 遷移指南

如果您需要從原始版本遷移到模組化版本：

1. **備份原始檔案**：`app_backup.py` 已自動創建
2. **檢查配置**：確保 `data/.env` 檔案正確配置
3. **測試功能**：使用 `test_modules.py` 驗證模組載入
4. **逐步遷移**：可以逐步將功能遷移到新架構

## 🐛 故障排除

### 常見問題

1. **模組載入失敗**
   - 檢查Python路徑
   - 確認所有依賴已安裝

2. **配置錯誤**
   - 檢查 `data/.env` 檔案
   - 確認所有必要配置已設定

3. **權限問題**
   - 檢查目錄創建權限
   - 確認檔案讀寫權限

## 📞 支援

如有問題，請檢查：
1. 錯誤日誌（`logs/` 目錄）
2. 模組測試結果
3. 配置檔案設定

---

**注意**：重構後的程式碼保持了所有原有功能，但結構更加清晰和可維護。建議在生產環境使用前進行充分測試。
