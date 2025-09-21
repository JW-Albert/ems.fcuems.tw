"""
測試模組化重構
"""

def test_config():
    """測試配置模組"""
    try:
        from config import config
        print("✅ 配置模組載入成功")
        print(f"   - SECRET_KEY: {config.SECRET_KEY[:10]}...")
        print(f"   - LINE_BOT_API_TOKEN: {'已設定' if config.LINE_BOT_API_TOKEN else '未設定'}")
        print(f"   - DISCORD_WEBHOOK_URL: {'已設定' if config.DISCORD_WEBHOOK_URL else '未設定'}")
        return True
    except Exception as e:
        print(f"❌ 配置模組載入失敗: {e}")
        return False

def test_logger():
    """測試日誌模組"""
    try:
        from logger import logger_manager
        print("✅ 日誌模組載入成功")
        print(f"   - 日誌檔案: {logger_manager.get_log_filename()}")
        return True
    except Exception as e:
        print(f"❌ 日誌模組載入失敗: {e}")
        return False

def test_case_manager():
    """測試案件管理模組"""
    try:
        from case_manager import case_manager
        print("✅ 案件管理模組載入成功")
        print(f"   - 案件目錄: {case_manager.record_dir}")
        return True
    except Exception as e:
        print(f"❌ 案件管理模組載入失敗: {e}")
        return False

def test_message_broadcaster():
    """測試訊息廣播模組"""
    try:
        from message_broadcaster import message_broadcaster
        print("✅ 訊息廣播模組載入成功")
        print(f"   - LINE狀態: {'啟用' if message_broadcaster.line_enabled else '停用'}")
        print(f"   - Discord狀態: {'啟用' if message_broadcaster.discord_enabled else '停用'}")
        return True
    except Exception as e:
        print(f"❌ 訊息廣播模組載入失敗: {e}")
        return False

def test_api_routes():
    """測試API路由模組"""
    try:
        from api_routes import APIRoutes
        print("✅ API路由模組載入成功")
        return True
    except Exception as e:
        print(f"❌ API路由模組載入失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🧪 開始測試模組化重構...")
    print("=" * 50)
    
    tests = [
        test_config,
        test_logger,
        test_case_manager,
        test_message_broadcaster,
        test_api_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 測試結果: {passed}/{total} 模組載入成功")
    
    if passed == total:
        print("🎉 所有模組載入成功！模組化重構完成！")
    else:
        print("⚠️  部分模組載入失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main()
