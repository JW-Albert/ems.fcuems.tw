"""
訊息廣播模組
負責LINE和Discord訊息的發送
"""

import datetime
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import LineBotApiError
from dhooks import Webhook
from config import config
from logger import logger_manager

class MessageBroadcaster:
    """訊息廣播器"""
    
    def __init__(self):
        self.line_bot_api = LineBotApi(config.LINE_BOT_API_TOKEN)
        self.handler = WebhookHandler(config.LINE_WEBHOOK_HANDLER)
        self.group_id = config.LINE_GROUP_ID
        self.discord_webhook = Webhook(config.DISCORD_WEBHOOK_URL)
        
        # 廣播控制
        self.line_enabled = True
        self.discord_enabled = True
    
    def broadcast_message(self, message_content, case_data=None):
        """廣播訊息到LINE和Discord"""
        results = {
            'line_success': False,
            'discord_success': False,
            'line_error': None,
            'discord_error': None,
            'discord_message_id': None
        }
        
        # 發送LINE訊息
        if self.line_enabled:
            try:
                self.line_bot_api.push_message(
                    self.group_id,
                    TextSendMessage(text=message_content)
                )
                results['line_success'] = True
                logger_manager.log_user_action("LINE訊息發送成功", f"案件: {case_data.get('event_type', 'Unknown') if case_data else 'Test'}")
                
            except LineBotApiError as e:
                results['line_error'] = str(e)
                logger_manager.log_error(f"LINE訊息發送失敗: {e}")
                
            except Exception as e:
                results['line_error'] = str(e)
                logger_manager.log_error(f"LINE訊息發送異常: {e}")
        
        # 發送Discord訊息
        if self.discord_enabled:
            try:
                response = self.discord_webhook.send(message_content)
                results['discord_success'] = True
                results['discord_message_id'] = response.get('id')
                logger_manager.log_user_action("Discord訊息發送成功", f"案件: {case_data.get('event_type', 'Unknown') if case_data else 'Test'}")
                
            except Exception as e:
                results['discord_error'] = str(e)
                logger_manager.log_error(f"Discord訊息發送失敗: {e}")
        
        return results
    
    def test_line_message(self):
        """測試LINE訊息發送"""
        test_message = f"""🧪 系統測試訊息 / System Test Message
時間 / Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
狀態 / Status: LINE Bot 連線正常 / LINE Bot Connection OK
"""
        
        try:
            self.line_bot_api.push_message(
                self.group_id,
                TextSendMessage(text=test_message)
            )
            return {"success": True, "message": "LINE測試訊息發送成功"}
            
        except LineBotApiError as e:
            return {"success": False, "error": f"LINE API錯誤: {str(e)}"}
            
        except Exception as e:
            return {"success": False, "error": f"LINE發送異常: {str(e)}"}
    
    def test_discord_message(self):
        """測試Discord訊息發送"""
        test_message = f"""🧪 **系統測試訊息 / System Test Message**
時間 / Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
狀態 / Status: Discord Webhook 連線正常 / Discord Webhook Connection OK
"""
        
        try:
            response = self.discord_webhook.send(test_message)
            return {
                "success": True, 
                "message": "Discord測試訊息發送成功",
                "message_id": response.get('id')
            }
            
        except Exception as e:
            return {"success": False, "error": f"Discord發送失敗: {str(e)}"}
    
    def format_case_message(self, case_data):
        """格式化案件訊息"""
        event_type = case_data.get('event_type', 'Unknown')
        location = case_data.get('location', 'Unknown')
        room = case_data.get('room', 'Unknown')
        content = case_data.get('content', 'None')
        
        # 根據案件類型選擇表情符號
        emoji_map = {
            'OHCA': '🚨',
            '內科': '🏥',
            '外科': '⚕️'
        }
        emoji = emoji_map.get(event_type, '📢')
        
        message = f"""{emoji} 緊急事件通報 / Emergency Alert
案件分類 / Case Type: {event_type}
案件地點 / Location: {location}
案件位置 / Position: {room}
補充資訊 / Additional Info: {content}
通報時間 / Report Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return message
    
    def set_broadcast_control(self, line=None, discord=None):
        """設定廣播控制"""
        if line is not None:
            self.line_enabled = line
        if discord is not None:
            self.discord_enabled = discord
    
    def get_broadcast_status(self):
        """獲取廣播狀態"""
        return {
            'line_enabled': self.line_enabled,
            'discord_enabled': self.discord_enabled
        }

# 全域訊息廣播器實例
message_broadcaster = MessageBroadcaster()
