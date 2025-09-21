# 緊急事件通報系統 - 安裝指南
# Emergency Management System - Installation Guide

## 快速開始 / Quick Start

### 方法一：統一安裝腳本 / Method 1: Unified Installation Script

**這是最推薦的安裝方式 / This is the most recommended installation method**

```bash
# 1. 將應用程式檔案複製到目標目錄 / Copy application files to target directory
sudo cp -r . /var/www/ems/web/

# 2. 進入server目錄 / Enter server directory
cd /var/www/ems/web/server

# 3. 執行統一安裝腳本 / Run unified installation script
sudo ./setup_all.sh
```

**安裝完成後 / After installation:**

- 主網站 / Main Website: `http://localhost:8000`
- 管理網站 / Admin Website: `http://localhost:5000`

### 方法二：手動安裝 / Method 2: Manual Installation

如果您需要更多控制或遇到問題，可以手動執行以下步驟：

If you need more control or encounter issues, you can manually execute the following steps:

#### 步驟 1: 建立目錄結構 / Step 1: Create Directory Structure

```bash
sudo mkdir -p /var/www/ems/web
sudo mkdir -p /var/www/ems/venv
sudo mkdir -p /var/www/ems/web/logs
sudo mkdir -p /var/www/ems/web/record
sudo mkdir -p /var/www/ems/web/data
```

#### 步驟 2: 安裝系統依賴 / Step 2: Install System Dependencies

```bash
sudo apt update -y && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev
```

#### 步驟 3: 建立虛擬環境 / Step 3: Create Virtual Environment

```bash
cd /var/www/ems
python3 -m venv venv
source venv/bin/activate
pip3 install --upgrade pip setuptools wheel
```

#### 步驟 4: 安裝Python套件 / Step 4: Install Python Packages

```bash
cd web
pip3 install -r requirements.txt
```

#### 步驟 5: 設定權限 / Step 5: Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/ems
sudo chmod -R 755 /var/www/ems
sudo chmod -R 755 /var/www/ems/web/logs
sudo chmod -R 755 /var/www/ems/web/record
sudo chmod -R 755 /var/www/ems/web/data
```

#### 步驟 6: 安裝systemd服務 / Step 6: Install systemd Services

```bash
# 複製服務檔案 / Copy service files
sudo cp /var/www/ems/web/server/ems-main.service /etc/systemd/system/
sudo cp /var/www/ems/web/server/ems-admin.service /etc/systemd/system/

# 重新載入systemd / Reload systemd
sudo systemctl daemon-reload

# 啟用服務 / Enable services
sudo systemctl enable ems-main
sudo systemctl enable ems-admin

# 啟動服務 / Start services
sudo systemctl start ems-main
sudo systemctl start ems-admin
```

## 服務管理 / Service Management

### 檢查服務狀態 / Check Service Status

```bash
# 檢查主網站服務 / Check main website service
sudo systemctl status ems-main

# 檢查管理網站服務 / Check admin website service
sudo systemctl status ems-admin

# 檢查所有EMS服務 / Check all EMS services
sudo systemctl status ems-main ems-admin
```

### 服務控制 / Service Control

```bash
# 啟動服務 / Start services
sudo systemctl start ems-main
sudo systemctl start ems-admin

# 停止服務 / Stop services
sudo systemctl stop ems-main
sudo systemctl stop ems-admin

# 重啟服務 / Restart services
sudo systemctl restart ems-main
sudo systemctl restart ems-admin

# 重新載入服務 / Reload services
sudo systemctl reload ems-main
sudo systemctl reload ems-admin
```

### 查看日誌 / View Logs

```bash
# 查看主網站日誌 / View main website logs
sudo journalctl -u ems-main -f

# 查看管理網站日誌 / View admin website logs
sudo journalctl -u ems-admin -f

# 查看最近的日誌 / View recent logs
sudo journalctl -u ems-main -n 50
sudo journalctl -u ems-admin -n 50
```

## 故障排除 / Troubleshooting

### 常見問題 / Common Issues

#### 1. 權限錯誤 / Permission Errors

```bash
# 重新設定權限 / Reset permissions
sudo chown -R www-data:www-data /var/www/ems
sudo chmod -R 755 /var/www/ems
```

#### 2. 服務啟動失敗 / Service Start Failure

```bash
# 檢查服務狀態 / Check service status
sudo systemctl status ems-main
sudo systemctl status ems-admin

# 查看詳細錯誤 / View detailed errors
sudo journalctl -u ems-main -n 20
sudo journalctl -u ems-admin -n 20
```

#### 3. 虛擬環境問題 / Virtual Environment Issues

```bash
# 重新建立虛擬環境 / Recreate virtual environment
sudo rm -rf /var/www/ems/venv
cd /var/www/ems
python3 -m venv venv
source venv/bin/activate
pip3 install --upgrade pip setuptools wheel
cd web
pip3 install -r requirements.txt
```

#### 4. 端口衝突 / Port Conflicts

```bash
# 檢查端口使用情況 / Check port usage
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :5000

# 停止衝突的服務 / Stop conflicting services
sudo systemctl stop conflicting-service-name
```

### 測試安裝 / Test Installation

```bash
# 測試主網站 / Test main website
curl -I http://localhost:8000

# 測試管理網站 / Test admin website
curl -I http://localhost:5000

# 測試API / Test API
curl http://localhost:8000/api/stats
```

## 配置 / Configuration

### 環境變數 / Environment Variables

1. 複製範例檔案 / Copy example file:
   ```bash
   cp /var/www/ems/web/data/.env.example /var/www/ems/web/data/.env
   ```

2. 編輯配置檔案 / Edit configuration file:
   ```bash
   sudo nano /var/www/ems/web/data/.env
   ```

3. 填入您的配置 / Fill in your configuration:
   ```env
   LINE_BOT_API_TOKEN=your_line_bot_api_token
   LINE_WEBHOOK_HANDLER=your_webhook_handler
   LINE_GROUP_ID=your_group_id
   DISCORD_WEBHOOK_URL=your_discord_webhook_url
   SECRET_KEY=your_secret_key
   SESSION_TYPE=filesystem
   ```

### 防火牆設定 / Firewall Configuration

```bash
# 開放必要端口 / Open necessary ports
sudo ufw allow 8000
sudo ufw allow 5000
sudo ufw reload
```

## 更新 / Updates

### 更新應用程式 / Update Application

```bash
# 停止服務 / Stop services
sudo systemctl stop ems-main ems-admin

# 備份現有檔案 / Backup existing files
sudo cp -r /var/www/ems/web /var/www/ems/web.backup.$(date +%Y%m%d)

# 複製新檔案 / Copy new files
sudo cp -r . /var/www/ems/web/

# 重新設定權限 / Reset permissions
sudo chown -R www-data:www-data /var/www/ems/web
sudo chmod -R 755 /var/www/ems/web

# 更新Python套件 / Update Python packages
cd /var/www/ems/web
source ../venv/bin/activate
pip3 install -r requirements.txt

# 重新啟動服務 / Restart services
sudo systemctl start ems-main ems-admin
```

## 支援 / Support

如果您遇到問題，請：

If you encounter issues, please:

1. 檢查日誌檔案 / Check log files
2. 確認服務狀態 / Verify service status
3. 檢查權限設定 / Check permission settings
4. 聯絡管理員 / Contact administrator

**聯絡方式 / Contact Information:**
- 管理員 / Administrator: 王建葦
- 信箱 / Email: [admin@mail.jw-albert.tw](mailto:admin@mail.jw-albert.tw)
