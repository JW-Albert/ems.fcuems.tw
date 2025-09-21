#!/bin/bash

# 緊急事件通報系統 - 完整安裝腳本
# Emergency Management System - Complete Installation Script
# 
# 此腳本會自動完成以下工作：
# This script will automatically complete the following tasks:
# 1. 建立必要的目錄結構 / Create necessary directory structure
# 2. 安裝系統依賴套件 / Install system dependencies
# 3. 建立Python虛擬環境 / Create Python virtual environment
# 4. 安裝Python依賴套件 / Install Python dependencies
# 5. 設定目錄權限 / Set directory permissions
# 6. 安裝systemd服務 / Install systemd services
# 7. 啟動服務 / Start services
#
# 使用方式 / Usage:
# sudo ./setup_all.sh
#
# 注意 / Note: 請先將應用程式檔案複製到 /var/www/ems/web/
# Please copy application files to /var/www/ems/web/ first

echo "=========================================="
echo "緊急事件通報系統 - 完整安裝"
echo "Emergency Management System - Complete Setup"
echo "=========================================="

# 檢查是否以root身份執行
if [ "$EUID" -ne 0 ]; then
    echo "請以root身份執行此腳本 / Please run this script as root"
    exit 1
fi

# 檢查腳本是否在正確的目錄執行
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -f "$SCRIPT_DIR/ems-main.service" ] || [ ! -f "$SCRIPT_DIR/ems-admin.service" ]; then
    echo "錯誤：找不到systemd服務檔案 / Error: systemd service files not found"
    echo "請確保在server目錄中執行此腳本 / Please run this script from the server directory"
    echo "當前目錄 / Current directory: $SCRIPT_DIR"
    exit 1
fi

# 設定變數
MAIN_SERVICE_NAME="ems-main"
ADMIN_SERVICE_NAME="ems-admin"
MAIN_SERVICE_FILE="/etc/systemd/system/${MAIN_SERVICE_NAME}.service"
ADMIN_SERVICE_FILE="/etc/systemd/system/${ADMIN_SERVICE_NAME}.service"
APP_DIR="/var/www/ems/web"
VENV_DIR="/var/www/ems/venv"
EMS_DIR="/var/www/ems"

echo "1. 檢查並建立應用程式目錄..."
if [ ! -d "$EMS_DIR" ]; then
    echo "建立EMS目錄 / Creating EMS directory: $EMS_DIR"
    mkdir -p "$EMS_DIR"
fi

if [ ! -d "$APP_DIR" ]; then
    echo "建立應用程式目錄 / Creating app directory: $APP_DIR"
    mkdir -p "$APP_DIR"
fi

echo "2. 安裝系統依賴套件..."
echo "更新系統套件 / Updating system packages..."
apt update -y && apt upgrade -y

echo "安裝Python相關套件 / Installing Python packages..."
apt install -y python3 python3-pip python3-venv python3-dev

echo "3. 建立虛擬環境..."
if [ ! -d "$VENV_DIR" ]; then
    echo "建立虛擬環境 / Creating virtual environment: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
else
    echo "虛擬環境已存在 / Virtual environment already exists: $VENV_DIR"
fi

echo "4. 啟動虛擬環境並安裝Python套件..."
echo "啟動虛擬環境 / Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "升級pip、setuptools、wheel / Upgrading pip, setuptools, wheel..."
pip3 install --upgrade pip setuptools wheel

echo "安裝Python依賴套件 / Installing Python dependencies..."
if [ -f "$APP_DIR/requirements.txt" ]; then
    pip3 install -r "$APP_DIR/requirements.txt"
    echo "✓ Python依賴套件安裝完成 / Python dependencies installed successfully"
else
    echo "⚠️ 找不到requirements.txt檔案 / requirements.txt not found"
    echo "請確保應用程式檔案已正確複製到 $APP_DIR / Please ensure app files are copied to $APP_DIR"
fi

echo "5. 檢查應用程式檔案..."
if [ ! -f "$APP_DIR/app.py" ]; then
    echo "錯誤：主應用程式檔案不存在 / Error: Main app file not found: $APP_DIR/app.py"
    echo "請先將應用程式檔案複製到 $APP_DIR / Please copy app files to $APP_DIR first"
    exit 1
fi

if [ ! -f "$APP_DIR/admin_app.py" ]; then
    echo "錯誤：管理應用程式檔案不存在 / Error: Admin app file not found: $APP_DIR/admin_app.py"
    echo "請先將應用程式檔案複製到 $APP_DIR / Please copy app files to $APP_DIR first"
    exit 1
fi

echo "6. 建立必要目錄並設定權限..."
# 建立logs和record目錄
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/record"
mkdir -p "$APP_DIR/data"

# 設定目錄權限
chown -R www-data:www-data "$EMS_DIR"
chmod -R 755 "$EMS_DIR"
chmod -R 755 "$APP_DIR/logs"
chmod -R 755 "$APP_DIR/record"
chmod -R 755 "$APP_DIR/data"

echo "✓ 目錄權限設定完成 / Directory permissions set successfully"

echo "7. 複製systemd服務檔案..."

# 複製主網站服務檔案
cp "$APP_DIR/server/ems-main.service" "$MAIN_SERVICE_FILE"
if [ $? -eq 0 ]; then
    echo "✓ 主網站服務檔案複製成功 / Main website service file copied successfully"
else
    echo "✗ 主網站服務檔案複製失敗 / Failed to copy main website service file"
    exit 1
fi

# 複製管理網站服務檔案
cp "$APP_DIR/server/ems-admin.service" "$ADMIN_SERVICE_FILE"
if [ $? -eq 0 ]; then
    echo "✓ 管理網站服務檔案複製成功 / Admin website service file copied successfully"
else
    echo "✗ 管理網站服務檔案複製失敗 / Failed to copy admin website service file"
    exit 1
fi

echo "8. 設定檔案權限..."
chown www-data:www-data "$APP_DIR/app.py"
chown www-data:www-data "$APP_DIR/admin_app.py"
chmod 755 "$APP_DIR/app.py"
chmod 755 "$APP_DIR/admin_app.py"
chmod 644 "$MAIN_SERVICE_FILE"
chmod 644 "$ADMIN_SERVICE_FILE"

echo "9. 重新載入systemd..."
systemctl daemon-reload

echo "10. 啟用服務..."
systemctl enable "$MAIN_SERVICE_NAME"
systemctl enable "$ADMIN_SERVICE_NAME"

echo "11. 啟動服務..."
systemctl start "$MAIN_SERVICE_NAME"
systemctl start "$ADMIN_SERVICE_NAME"

echo "12. 檢查服務狀態..."
sleep 3

# 檢查主網站服務
if systemctl is-active --quiet "$MAIN_SERVICE_NAME"; then
    echo "✓ 主網站服務啟動成功 / Main website service started successfully"
else
    echo "✗ 主網站服務啟動失敗 / Failed to start main website service"
    echo "查看錯誤日誌 / Check error logs: journalctl -u $MAIN_SERVICE_NAME -f"
    MAIN_SERVICE_FAILED=true
fi

# 檢查管理網站服務
if systemctl is-active --quiet "$ADMIN_SERVICE_NAME"; then
    echo "✓ 管理網站服務啟動成功 / Admin website service started successfully"
else
    echo "✗ 管理網站服務啟動失敗 / Failed to start admin website service"
    echo "查看錯誤日誌 / Check error logs: journalctl -u $ADMIN_SERVICE_NAME -f"
    ADMIN_SERVICE_FAILED=true
fi

echo ""
echo "=========================================="
echo "安裝完成 / Installation Complete"
echo "=========================================="

# 顯示服務狀態
echo "服務狀態 / Service Status:"
echo "  主網站 / Main Website:"
if [ "$MAIN_SERVICE_FAILED" = true ]; then
    echo "    ❌ 服務異常 / Service Error"
else
    echo "    ✅ 服務正常 / Service OK"
fi
echo "    地址 / URL: http://localhost:8000"
echo "    服務名 / Service: $MAIN_SERVICE_NAME"

echo ""
echo "  管理網站 / Admin Website:"
if [ "$ADMIN_SERVICE_FAILED" = true ]; then
    echo "    ❌ 服務異常 / Service Error"
else
    echo "    ✅ 服務正常 / Service OK"
fi
echo "    地址 / URL: http://localhost:5000"
echo "    服務名 / Service: $ADMIN_SERVICE_NAME"

echo ""
echo "服務管理指令 / Service Management Commands:"
echo "  主網站 / Main Website:"
echo "    啟動 / Start:   systemctl start $MAIN_SERVICE_NAME"
echo "    停止 / Stop:    systemctl stop $MAIN_SERVICE_NAME"
echo "    重啟 / Restart: systemctl restart $MAIN_SERVICE_NAME"
echo "    狀態 / Status:  systemctl status $MAIN_SERVICE_NAME"
echo "    日誌 / Logs:    journalctl -u $MAIN_SERVICE_NAME -f"

echo ""
echo "  管理網站 / Admin Website:"
echo "    啟動 / Start:   systemctl start $ADMIN_SERVICE_NAME"
echo "    停止 / Stop:    systemctl stop $ADMIN_SERVICE_NAME"
echo "    重啟 / Restart: systemctl restart $ADMIN_SERVICE_NAME"
echo "    狀態 / Status:  systemctl status $ADMIN_SERVICE_NAME"
echo "    日誌 / Logs:    journalctl -u $ADMIN_SERVICE_NAME -f"

echo ""
echo "  全部服務 / All Services:"
echo "    啟動全部 / Start All:   systemctl start $MAIN_SERVICE_NAME $ADMIN_SERVICE_NAME"
echo "    停止全部 / Stop All:    systemctl stop $MAIN_SERVICE_NAME $ADMIN_SERVICE_NAME"
echo "    重啟全部 / Restart All: systemctl restart $MAIN_SERVICE_NAME $ADMIN_SERVICE_NAME"

echo ""
echo "快速測試 / Quick Test:"
echo "  主網站 / Main Site: curl -I http://localhost:8000"
echo "  管理網站 / Admin Site: curl -I http://localhost:5000"

# 如果有服務失敗，顯示錯誤信息
if [ "$MAIN_SERVICE_FAILED" = true ] || [ "$ADMIN_SERVICE_FAILED" = true ]; then
    echo ""
    echo "⚠️  部分服務啟動失敗，請檢查日誌 / Some services failed to start, please check logs"
    echo "   主網站日誌 / Main site logs: journalctl -u $MAIN_SERVICE_NAME -n 20"
    echo "   管理網站日誌 / Admin site logs: journalctl -u $ADMIN_SERVICE_NAME -n 20"
    exit 1
fi

echo ""
echo "🎉 所有服務安裝完成！/ All services installed successfully!"
echo "=========================================="
