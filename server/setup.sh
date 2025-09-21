#!/bin/bash

# 緊急事件通報系統 - 安裝腳本
# Emergency Management System - Installation Script

echo "=========================================="
echo "緊急事件通報系統 - 安裝"
echo "Emergency Management System - Setup"
echo "=========================================="

# 檢查是否以root身份執行
if [ "$EUID" -ne 0 ]; then
    echo "請以root身份執行此腳本 / Please run this script as root"
    exit 1
fi

# 設定變數
MAIN_SERVICE_NAME="ems-flask"
ADMIN_SERVICE_NAME="ems-admin"
MAIN_SERVICE_FILE="/etc/systemd/system/${MAIN_SERVICE_NAME}.service"
ADMIN_SERVICE_FILE="/etc/systemd/system/${ADMIN_SERVICE_NAME}.service"
APP_DIR="/var/www/ems/web"
VENV_DIR="/var/www/ems/venv"

# 檢查安裝選項
INSTALL_MAIN=true
INSTALL_ADMIN=true

# 如果有參數，解析安裝選項
if [ $# -gt 0 ]; then
    case "$1" in
        "main")
            INSTALL_ADMIN=false
            echo "只安裝主網站 / Installing main website only"
            ;;
        "admin")
            INSTALL_MAIN=false
            echo "只安裝管理網站 / Installing admin website only"
            ;;
        "all")
            echo "安裝全部服務 / Installing all services"
            ;;
        *)
            echo "用法 / Usage: $0 [main|admin|all]"
            echo "  main  - 只安裝主網站 / Install main website only"
            echo "  admin - 只安裝管理網站 / Install admin website only"
            echo "  all   - 安裝全部服務 / Install all services (default)"
            exit 1
            ;;
    esac
fi

echo "1. 檢查應用程式目錄..."
if [ ! -d "$APP_DIR" ]; then
    echo "錯誤：應用程式目錄不存在 / Error: App directory not found: $APP_DIR"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "錯誤：虛擬環境目錄不存在 / Error: Virtual environment not found: $VENV_DIR"
    exit 1
fi

echo "2. 檢查應用程式檔案..."
if [ "$INSTALL_MAIN" = true ]; then
    if [ ! -f "$APP_DIR/app.py" ]; then
        echo "錯誤：主應用程式檔案不存在 / Error: Main app file not found: $APP_DIR/app.py"
        exit 1
    fi
fi

if [ "$INSTALL_ADMIN" = true ]; then
    if [ ! -f "$APP_DIR/admin_app.py" ]; then
        echo "錯誤：管理應用程式檔案不存在 / Error: Admin app file not found: $APP_DIR/admin_app.py"
        exit 1
    fi
fi

echo "3. 複製systemd服務檔案..."

# 複製主網站服務檔案
if [ "$INSTALL_MAIN" = true ]; then
    cp "$APP_DIR/server/ems-flask.service" "$MAIN_SERVICE_FILE"
    if [ $? -eq 0 ]; then
        echo "✓ 主網站服務檔案複製成功 / Main website service file copied successfully"
    else
        echo "✗ 主網站服務檔案複製失敗 / Failed to copy main website service file"
        exit 1
    fi
fi

# 複製管理網站服務檔案
if [ "$INSTALL_ADMIN" = true ]; then
    cp "$APP_DIR/server/ems-admin.service" "$ADMIN_SERVICE_FILE"
    if [ $? -eq 0 ]; then
        echo "✓ 管理網站服務檔案複製成功 / Admin website service file copied successfully"
    else
        echo "✗ 管理網站服務檔案複製失敗 / Failed to copy admin website service file"
        exit 1
    fi
fi

echo "4. 設定檔案權限..."
if [ "$INSTALL_MAIN" = true ]; then
    chown www-data:www-data "$APP_DIR/app.py"
    chmod 755 "$APP_DIR/app.py"
    chmod 644 "$MAIN_SERVICE_FILE"
fi

if [ "$INSTALL_ADMIN" = true ]; then
    chown www-data:www-data "$APP_DIR/admin_app.py"
    chmod 755 "$APP_DIR/admin_app.py"
    chmod 644 "$ADMIN_SERVICE_FILE"
fi

echo "5. 重新載入systemd..."
systemctl daemon-reload

echo "6. 啟用服務..."
if [ "$INSTALL_MAIN" = true ]; then
    systemctl enable "$MAIN_SERVICE_NAME"
fi

if [ "$INSTALL_ADMIN" = true ]; then
    systemctl enable "$ADMIN_SERVICE_NAME"
fi

echo "7. 啟動服務..."
if [ "$INSTALL_MAIN" = true ]; then
    systemctl start "$MAIN_SERVICE_NAME"
fi

if [ "$INSTALL_ADMIN" = true ]; then
    systemctl start "$ADMIN_SERVICE_NAME"
fi

echo "8. 檢查服務狀態..."
sleep 3

MAIN_SERVICE_FAILED=false
ADMIN_SERVICE_FAILED=false

# 檢查主網站服務
if [ "$INSTALL_MAIN" = true ]; then
    if systemctl is-active --quiet "$MAIN_SERVICE_NAME"; then
        echo "✓ 主網站服務啟動成功 / Main website service started successfully"
    else
        echo "✗ 主網站服務啟動失敗 / Failed to start main website service"
        echo "查看錯誤日誌 / Check error logs: journalctl -u $MAIN_SERVICE_NAME -f"
        MAIN_SERVICE_FAILED=true
    fi
fi

# 檢查管理網站服務
if [ "$INSTALL_ADMIN" = true ]; then
    if systemctl is-active --quiet "$ADMIN_SERVICE_NAME"; then
        echo "✓ 管理網站服務啟動成功 / Admin website service started successfully"
    else
        echo "✗ 管理網站服務啟動失敗 / Failed to start admin website service"
        echo "查看錯誤日誌 / Check error logs: journalctl -u $ADMIN_SERVICE_NAME -f"
        ADMIN_SERVICE_FAILED=true
    fi
fi

echo ""
echo "=========================================="
echo "安裝完成 / Installation Complete"
echo "=========================================="

# 顯示服務狀態
echo "服務狀態 / Service Status:"

if [ "$INSTALL_MAIN" = true ]; then
    echo "  主網站 / Main Website:"
    if [ "$MAIN_SERVICE_FAILED" = true ]; then
        echo "    ❌ 服務異常 / Service Error"
    else
        echo "    ✅ 服務正常 / Service OK"
    fi
    echo "    地址 / URL: http://localhost:5000"
    echo "    服務名 / Service: $MAIN_SERVICE_NAME"
fi

if [ "$INSTALL_ADMIN" = true ]; then
    echo "  管理網站 / Admin Website:"
    if [ "$ADMIN_SERVICE_FAILED" = true ]; then
        echo "    ❌ 服務異常 / Service Error"
    else
        echo "    ✅ 服務正常 / Service OK"
    fi
    echo "    地址 / URL: http://localhost:5001"
    echo "    服務名 / Service: $ADMIN_SERVICE_NAME"
fi

echo ""
echo "服務管理指令 / Service Management Commands:"

if [ "$INSTALL_MAIN" = true ]; then
    echo "  主網站 / Main Website:"
    echo "    啟動 / Start:   systemctl start $MAIN_SERVICE_NAME"
    echo "    停止 / Stop:    systemctl stop $MAIN_SERVICE_NAME"
    echo "    重啟 / Restart: systemctl restart $MAIN_SERVICE_NAME"
    echo "    狀態 / Status:  systemctl status $MAIN_SERVICE_NAME"
    echo "    日誌 / Logs:    journalctl -u $MAIN_SERVICE_NAME -f"
fi

if [ "$INSTALL_ADMIN" = true ]; then
    echo "  管理網站 / Admin Website:"
    echo "    啟動 / Start:   systemctl start $ADMIN_SERVICE_NAME"
    echo "    停止 / Stop:    systemctl stop $ADMIN_SERVICE_NAME"
    echo "    重啟 / Restart: systemctl restart $ADMIN_SERVICE_NAME"
    echo "    狀態 / Status:  systemctl status $ADMIN_SERVICE_NAME"
    echo "    日誌 / Logs:    journalctl -u $ADMIN_SERVICE_NAME -f"
fi

if [ "$INSTALL_MAIN" = true ] && [ "$INSTALL_ADMIN" = true ]; then
    echo "  全部服務 / All Services:"
    echo "    啟動全部 / Start All:   systemctl start $MAIN_SERVICE_NAME $ADMIN_SERVICE_NAME"
    echo "    停止全部 / Stop All:    systemctl stop $MAIN_SERVICE_NAME $ADMIN_SERVICE_NAME"
    echo "    重啟全部 / Restart All: systemctl restart $MAIN_SERVICE_NAME $ADMIN_SERVICE_NAME"
fi

echo ""
echo "快速測試 / Quick Test:"
if [ "$INSTALL_MAIN" = true ]; then
    echo "  主網站 / Main Site: curl -I http://localhost:5000"
fi
if [ "$INSTALL_ADMIN" = true ]; then
    echo "  管理網站 / Admin Site: curl -I http://localhost:5001"
fi

# 如果有服務失敗，顯示錯誤信息
if [ "$MAIN_SERVICE_FAILED" = true ] || [ "$ADMIN_SERVICE_FAILED" = true ]; then
    echo ""
    echo "⚠️  部分服務啟動失敗，請檢查日誌 / Some services failed to start, please check logs"
    if [ "$MAIN_SERVICE_FAILED" = true ]; then
        echo "   主網站日誌 / Main site logs: journalctl -u $MAIN_SERVICE_NAME -n 20"
    fi
    if [ "$ADMIN_SERVICE_FAILED" = true ]; then
        echo "   管理網站日誌 / Admin site logs: journalctl -u $ADMIN_SERVICE_NAME -n 20"
    fi
    exit 1
fi

echo ""
echo "🎉 安裝完成！/ Installation completed!"
echo "=========================================="