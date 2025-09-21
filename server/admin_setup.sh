#!/bin/bash

# 緊急事件通報系統 - 管理網站安裝腳本
# Emergency Management System - Admin Website Setup Script

echo "=========================================="
echo "緊急事件通報系統 - 管理網站安裝"
echo "Emergency Management System - Admin Setup"
echo "=========================================="

# 檢查是否以root身份執行
if [ "$EUID" -ne 0 ]; then
    echo "請以root身份執行此腳本 / Please run this script as root"
    exit 1
fi

# 設定變數
SERVICE_NAME="ems-admin"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
APP_DIR="/var/www/ems/web"
VENV_DIR="/var/www/ems/venv"

echo "1. 檢查應用程式目錄..."
if [ ! -d "$APP_DIR" ]; then
    echo "錯誤：應用程式目錄不存在 / Error: App directory not found: $APP_DIR"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "錯誤：虛擬環境目錄不存在 / Error: Virtual environment not found: $VENV_DIR"
    exit 1
fi

echo "2. 檢查管理應用程式檔案..."
if [ ! -f "$APP_DIR/admin_app.py" ]; then
    echo "錯誤：管理應用程式檔案不存在 / Error: Admin app file not found: $APP_DIR/admin_app.py"
    exit 1
fi

echo "3. 複製systemd服務檔案..."
cp "$APP_DIR/server/ems-admin.service" "$SERVICE_FILE"
if [ $? -eq 0 ]; then
    echo "✓ 服務檔案複製成功 / Service file copied successfully"
else
    echo "✗ 服務檔案複製失敗 / Failed to copy service file"
    exit 1
fi

echo "4. 設定檔案權限..."
chown www-data:www-data "$APP_DIR/admin_app.py"
chmod 755 "$APP_DIR/admin_app.py"
chmod 644 "$SERVICE_FILE"

echo "5. 重新載入systemd..."
systemctl daemon-reload

echo "6. 啟用服務..."
systemctl enable "$SERVICE_NAME"

echo "7. 啟動服務..."
systemctl start "$SERVICE_NAME"

echo "8. 檢查服務狀態..."
sleep 3
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✓ 管理網站服務啟動成功 / Admin service started successfully"
    echo "管理網站地址 / Admin URL: http://localhost:5000"
else
    echo "✗ 管理網站服務啟動失敗 / Failed to start admin service"
    echo "查看錯誤日誌 / Check error logs: journalctl -u $SERVICE_NAME -f"
    exit 1
fi

echo ""
echo "=========================================="
echo "安裝完成 / Installation Complete"
echo "=========================================="
echo "主網站 / Main Site: http://localhost:8000"
echo "管理網站 / Admin Site: http://localhost:5000"
echo ""
echo "服務管理指令 / Service Management Commands:"
echo "  啟動 / Start:   systemctl start $SERVICE_NAME"
echo "  停止 / Stop:    systemctl stop $SERVICE_NAME"
echo "  重啟 / Restart: systemctl restart $SERVICE_NAME"
echo "  狀態 / Status:  systemctl status $SERVICE_NAME"
echo "  日誌 / Logs:    journalctl -u $SERVICE_NAME -f"
echo "=========================================="
