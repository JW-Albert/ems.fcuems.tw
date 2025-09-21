"""
案件管理模組
負責案件紀錄的保存、讀取和管理
"""

import os
import datetime
from config import config

class CaseManager:
    """案件管理器"""
    
    def __init__(self):
        self.record_dir = "record"
        self._ensure_record_dir()
    
    def _ensure_record_dir(self):
        """確保案件紀錄目錄存在"""
        if not os.path.exists(self.record_dir):
            os.makedirs(self.record_dir)
    
    def save_case_record(self, case_data):
        """保存案件紀錄到檔案"""
        try:
            # 生成檔案名稱（時間戳記）
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"case_{timestamp}.txt"
            file_path = os.path.join(self.record_dir, filename)
            
            # 格式化案件資料
            content = self._format_case_content(case_data, timestamp)
            
            # 寫入檔案
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return filename
            
        except Exception as e:
            raise Exception(f"保存案件紀錄失敗: {str(e)}")
    
    def _format_case_content(self, case_data, timestamp):
        """格式化案件內容"""
        content = f"""案件紀錄 / Case Record
{'='*50}

案件資訊 / Case Information:
- 案件分類 / Case Type: {case_data.get('event_type', 'Unknown')}
- 案件地點 / Location: {case_data.get('location', 'Unknown')}
- 案件位置 / Position: {case_data.get('room', 'Unknown')}
- 補充資訊 / Additional Info: {case_data.get('content', 'None')}

通報者資訊 / Reporter Information:
- IP 地址 / IP Address: {case_data.get('ip', 'Unknown')}
- 國家 / Country: {case_data.get('country', 'Unknown')}
- 城市 / City: {case_data.get('city', 'Unknown')}
- 瀏覽器 / User Agent: {case_data.get('user_agent', 'Unknown')}

廣播結果 / Broadcast Results:
- Discord 發送 / Discord Send: {case_data.get('discord_success', False)}
- LINE 發送 / LINE Send: {case_data.get('line_success', False)}
- Discord 訊息 ID / Discord Message ID: {case_data.get('discord_message_id', 'None')}

完整訊息內容 / Complete Message:
{case_data.get('message', 'No message')}

系統資訊 / System Information:
- 伺服器時間 / Server Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 檔案路徑 / File Path: {os.path.join(self.record_dir, f'case_{timestamp}.txt')}
- 案件編號 / Case ID: {timestamp}

{'='*50}
"""
        return content
    
    def get_case_files(self, date_from=None, date_to=None):
        """獲取案件檔案列表"""
        case_files = []
        
        if not os.path.exists(self.record_dir):
            return case_files
        
        for filename in os.listdir(self.record_dir):
            if filename.startswith("case_") and filename.endswith(".txt"):
                try:
                    # 解析檔案名稱獲取時間
                    time_str = filename.replace("case_", "").replace(".txt", "")
                    case_time = datetime.datetime.strptime(time_str, "%Y%m%d_%H%M%S")
                    
                    # 檢查日期範圍
                    if date_from and date_to:
                        start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
                        end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
                        
                        if not (start_date.date() <= case_time.date() <= end_date.date()):
                            continue
                    
                    file_path = os.path.join(self.record_dir, filename)
                    stat = os.stat(file_path)
                    
                    case_files.append({
                        'filename': filename,
                        'case_id': time_str,
                        'time': case_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'timestamp': case_time.isoformat(),
                        'size': stat.st_size,
                        'modified': datetime.datetime.fromtimestamp(stat.st_mtime)
                    })
                    
                except ValueError:
                    continue
        
        return sorted(case_files, key=lambda x: x['case_id'], reverse=True)
    
    def read_case_file(self, filename):
        """讀取案件檔案內容"""
        file_path = os.path.join(self.record_dir, filename)
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def parse_case_record(self, content):
        """解析案件紀錄檔案內容（簡化版本）"""
        case_info = {}
        lines = content.split('\n')
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # 識別區段
            if '案件資訊 / Case Information:' in line:
                current_section = 'case_info'
                continue
            elif '通報者資訊 / Reporter Information:' in line:
                current_section = 'reporter_info'
                continue
            elif '廣播結果 / Broadcast Results:' in line:
                current_section = 'broadcast_results'
                continue
            elif line.startswith('='):
                continue
            
            # 解析各區段內容
            if current_section == 'case_info':
                # 移除可能的前綴符號
                clean_line = line.lstrip('- ')
                if '案件分類 / Case Type:' in clean_line:
                    case_info['event_type'] = clean_line.split(':', 1)[1].strip()
                elif '案件地點 / Location:' in clean_line:
                    case_info['location'] = clean_line.split(':', 1)[1].strip()
                elif '案件位置 / Position:' in clean_line:
                    case_info['room'] = clean_line.split(':', 1)[1].strip()
                elif '補充資訊 / Additional Info:' in clean_line:
                    case_info['content'] = clean_line.split(':', 1)[1].strip()
            
            elif current_section == 'reporter_info':
                # 移除可能的前綴符號
                clean_line = line.lstrip('- ')
                if 'IP 地址 / IP Address:' in clean_line:
                    case_info['ip'] = clean_line.split(':', 1)[1].strip()
                elif '國家 / Country:' in clean_line:
                    case_info['country'] = clean_line.split(':', 1)[1].strip()
                elif '城市 / City:' in clean_line:
                    case_info['city'] = clean_line.split(':', 1)[1].strip()
            
            elif current_section == 'broadcast_results':
                # 移除可能的前綴符號
                clean_line = line.lstrip('- ')
                if 'Discord 發送 / Discord Send:' in clean_line:
                    case_info['discord_success'] = clean_line.split(':', 1)[1].strip().lower() == 'true'
                elif 'LINE 發送 / LINE Send:' in clean_line:
                    case_info['line_success'] = clean_line.split(':', 1)[1].strip().lower() == 'true'
        
        return case_info
    
    def parse_case_record_full(self, content):
        """解析案件紀錄檔案內容（完整版本）"""
        case_info = {}
        lines = content.split('\n')
        
        # 初始化所有欄位
        case_info.update({
            'event_type': None,
            'location': None,
            'room': None,
            'content': None,
            'message': None,
            'ip': None,
            'country': None,
            'city': None,
            'user_agent': None,
            'discord_success': False,
            'line_success': False,
            'discord_message_id': None,
            'server_time': None,
            'file_path': None
        })
        
        current_section = None
        message_lines = []
        
        for line in lines:
            line = line.strip()
            
            # 識別區段
            if '案件資訊 / Case Information:' in line:
                current_section = 'case_info'
                continue
            elif '通報者資訊 / Reporter Information:' in line:
                current_section = 'reporter_info'
                continue
            elif '廣播結果 / Broadcast Results:' in line:
                current_section = 'broadcast_results'
                continue
            elif '完整訊息內容 / Complete Message:' in line:
                current_section = 'message'
                continue
            elif '系統資訊 / System Information:' in line:
                current_section = 'system_info'
                continue
            elif line.startswith('='):
                continue
            
            # 解析各區段內容
            if current_section == 'case_info':
                if '案件分類 / Case Type:' in line:
                    case_info['event_type'] = line.split(':', 1)[1].strip()
                elif '案件地點 / Location:' in line:
                    case_info['location'] = line.split(':', 1)[1].strip()
                elif '案件位置 / Position:' in line:
                    case_info['room'] = line.split(':', 1)[1].strip()
                elif '補充資訊 / Additional Info:' in line:
                    case_info['content'] = line.split(':', 1)[1].strip()
            
            elif current_section == 'reporter_info':
                if 'IP 地址 / IP Address:' in line:
                    case_info['ip'] = line.split(':', 1)[1].strip()
                elif '國家 / Country:' in line:
                    case_info['country'] = line.split(':', 1)[1].strip()
                elif '城市 / City:' in line:
                    case_info['city'] = line.split(':', 1)[1].strip()
                elif '瀏覽器 / User Agent:' in line:
                    case_info['user_agent'] = line.split(':', 1)[1].strip()
            
            elif current_section == 'broadcast_results':
                if 'Discord 發送 / Discord Send:' in line:
                    case_info['discord_success'] = line.split(':', 1)[1].strip().lower() == 'true'
                elif 'LINE 發送 / LINE Send:' in line:
                    case_info['line_success'] = line.split(':', 1)[1].strip().lower() == 'true'
                elif 'Discord 訊息 ID / Discord Message ID:' in line:
                    case_info['discord_message_id'] = line.split(':', 1)[1].strip()
            
            elif current_section == 'message':
                if not line.startswith('-'):
                    message_lines.append(line)
            
            elif current_section == 'system_info':
                if '伺服器時間 / Server Time:' in line:
                    case_info['server_time'] = line.split(':', 1)[1].strip()
                elif '檔案路徑 / File Path:' in line:
                    case_info['file_path'] = line.split(':', 1)[1].strip()
        
        # 組合完整訊息
        case_info['message'] = '\n'.join(message_lines)
        
        return case_info
    
    def clear_case_files(self, date_from=None, date_to=None):
        """清除案件檔案"""
        cleared_files = []
        
        if not os.path.exists(self.record_dir):
            return cleared_files
        
        for filename in os.listdir(self.record_dir):
            if filename.startswith("case_") and filename.endswith(".txt"):
                try:
                    # 解析檔案名稱獲取時間
                    time_str = filename.replace("case_", "").replace(".txt", "")
                    case_time = datetime.datetime.strptime(time_str, "%Y%m%d_%H%M%S")
                    
                    # 檢查日期範圍
                    if date_from and date_to:
                        start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
                        end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
                        
                        if not (start_date.date() <= case_time.date() <= end_date.date()):
                            continue
                    
                    file_path = os.path.join(self.record_dir, filename)
                    os.remove(file_path)
                    cleared_files.append(filename)
                    
                except ValueError:
                    continue
        
        return cleared_files
    
    def get_case_stats(self, date_from=None, date_to=None):
        """獲取案件統計資料"""
        stats = {
            'total_cases': 0,
            'ohca_cases': 0,
            'internal_cases': 0,
            'surgical_cases': 0,
            'by_location': {},
            'by_hour': {},
            'by_date': {}
        }
        
        case_files = self.get_case_files(date_from, date_to)
        
        for case_file in case_files:
            try:
                content = self.read_case_file(case_file['filename'])
                if content:
                    case_info = self.parse_case_record(content)
                    
                    # 統計
                    stats['total_cases'] += 1
                    if case_info.get('event_type') == 'OHCA':
                        stats['ohca_cases'] += 1
                    elif case_info.get('event_type') == '內科':
                        stats['internal_cases'] += 1
                    elif case_info.get('event_type') == '外科':
                        stats['surgical_cases'] += 1
                    
                    # 地點統計
                    location = case_info.get('location', 'Unknown')
                    stats['by_location'][location] = stats['by_location'].get(location, 0) + 1
                    
                    # 小時統計
                    case_time = datetime.datetime.strptime(case_file['case_id'], "%Y%m%d_%H%M%S")
                    hour = case_time.hour
                    stats['by_hour'][hour] = stats['by_hour'].get(hour, 0) + 1
                    
                    # 日期統計
                    date_key = case_time.strftime("%Y-%m-%d")
                    stats['by_date'][date_key] = stats['by_date'].get(date_key, 0) + 1
                    
            except Exception as e:
                continue
        
        return stats

# 全域案件管理器實例
case_manager = CaseManager()
