# 🚀 部署指南

## 📋 問題修復摘要

### 原始錯誤
```
NameError: name 'handler' is not defined
```

### 修復內容
1. **在 `app.py` 中添加了 LINE Bot 變數定義**
2. **在 `api_routes.py` 中添加了 `os` 模組導入**
3. **確保所有模組正確導入**

## 🔧 修復的檔案

### 1. `app.py` 修復
**添加的程式碼：**
```python
# LINE Bot 設定
from linebot import LineBotApi, WebhookHandler
line_bot_api = LineBotApi(config.LINE_BOT_API_TOKEN)
handler = WebhookHandler(config.LINE_WEBHOOK_HANDLER)
```

### 2. `api_routes.py` 修復
**添加的程式碼：**
```python
import os
```

## 📦 部署步驟

### 1. 備份現有檔案
```bash
# 在伺服器上備份現有檔案
sudo cp /var/www/ems/web/app.py /var/www/ems/web/app_backup_$(date +%Y%m%d_%H%M%S).py
```

### 2. 上傳修復後的檔案
```bash
# 上傳所有修復後的檔案到伺服器
scp app.py root@your-server:/var/www/ems/web/
scp config.py root@your-server:/var/www/ems/web/
scp logger.py root@your-server:/var/www/ems/web/
scp case_manager.py root@your-server:/var/www/ems/web/
scp message_broadcaster.py root@your-server:/var/www/ems/web/
scp api_routes.py root@your-server:/var/www/ems/web/
```

### 3. 設定檔案權限
```bash
# 在伺服器上設定正確的權限
sudo chown -R www-data:www-data /var/www/ems/web/
sudo chmod -R 755 /var/www/ems/web/
```

### 4. 重啟服務
```bash
# 重啟 Flask 應用程式
sudo systemctl restart ems-flask.service

# 檢查服務狀態
sudo systemctl status ems-flask.service

# 查看日誌
sudo journalctl -u ems-flask.service -f
```

## 🔍 驗證部署

### 1. 檢查服務狀態
```bash
sudo systemctl status ems-flask.service
```
**預期結果：** `Active: active (running)`

### 2. 檢查日誌
```bash
sudo journalctl -u ems-flask.service -n 20 --no-pager
```
**預期結果：** 沒有 `NameError: name 'handler' is not defined` 錯誤

### 3. 測試應用程式
```bash
# 測試主頁面
curl http://localhost:5000/

# 測試API
curl http://localhost:5000/api/records
```

## 📊 部署前後對比

### 部署前（錯誤）
```
Sep 21 22:59:56 net1-fcuems-3 flask[840]: NameError: name 'handler' is not defined
Sep 21 22:59:56 net1-fcuems-3 systemd[1]: ems-flask.service: Main process exited, code=exited, status=1/FAILURE
```

### 部署後（預期）
```
Sep 21 22:59:56 net1-fcuems-3 flask[840]: * Running on all addresses (0.0.0.0)
Sep 21 22:59:56 net1-fcuems-3 flask[840]: * Running on http://127.0.0.1:5000
Sep 21 22:59:56 net1-fcuems-3 flask[840]: * Running on http://[::1]:5000
```

## 🛠️ 故障排除

### 如果仍然出現錯誤

1. **檢查 Python 路徑**
```bash
which python3
python3 --version
```

2. **檢查依賴套件**
```bash
pip3 list | grep -E "(flask|line-bot|dhooks|dotenv)"
```

3. **檢查配置檔案**
```bash
ls -la /var/www/ems/web/data/.env
cat /var/www/ems/web/data/.env
```

4. **檢查模組導入**
```bash
cd /var/www/ems/web
python3 -c "import app; print('Import successful')"
```

### 常見問題

1. **模組找不到**
   - 確保所有 `.py` 檔案都在正確的目錄中
   - 檢查 Python 路徑設定

2. **權限問題**
   - 確保 `www-data` 使用者有讀取權限
   - 檢查檔案所有權

3. **配置問題**
   - 確保 `.env` 檔案存在且包含必要的配置
   - 檢查配置值是否正確

## 📞 支援

如果部署過程中遇到問題，請檢查：

1. **服務日誌**：`sudo journalctl -u ems-flask.service -f`
2. **系統日誌**：`sudo journalctl -f`
3. **應用程式日誌**：`/var/www/ems/web/logs/`

---

**注意**：部署前請確保在測試環境中驗證所有功能正常運作。
