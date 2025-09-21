"""
API路由模組
負責所有API端點的處理
"""

import datetime
import os
from flask import request, jsonify, send_file
from case_manager import case_manager
from logger import logger_manager

class APIRoutes:
    """API路由處理器"""
    
    def __init__(self, app):
        self.app = app
        self._register_routes()
    
    def _register_routes(self):
        """註冊API路由"""
        
        @self.app.route("/api/records", methods=["GET"])
        def api_get_all_records():
            """API: 獲取所有案件紀錄 (JSON格式)"""
            try:
                # 獲取查詢參數
                case_type = request.args.get('type', 'all')
                date_from = request.args.get('from', '')
                date_to = request.args.get('to', '')
                limit = int(request.args.get('limit', 100))  # 預設最多100筆
                offset = int(request.args.get('offset', 0))  # 分頁偏移
                
                records = []
                stats = {
                    'total_cases': 0,
                    'ohca_cases': 0,
                    'internal_cases': 0,
                    'surgical_cases': 0
                }
                
                # 如果沒有指定日期範圍，預設為今天
                if not date_from:
                    date_from = datetime.datetime.now().strftime("%Y-%m-%d")
                if not date_to:
                    date_to = date_from
                
                # 獲取案件檔案
                case_files = case_manager.get_case_files(date_from, date_to)
                
                for case_file in case_files:
                    try:
                        # 讀取案件檔案
                        content = case_manager.read_case_file(case_file['filename'])
                        if content:
                            # 解析完整案件資訊
                            case_info = case_manager.parse_case_record_full(content)
                            case_info.update(case_file)
                            
                            # 統計
                            stats['total_cases'] += 1
                            if case_info.get('event_type') == 'OHCA':
                                stats['ohca_cases'] += 1
                            elif case_info.get('event_type') == '內科':
                                stats['internal_cases'] += 1
                            elif case_info.get('event_type') == '外科':
                                stats['surgical_cases'] += 1
                            
                            # 類型過濾
                            if case_type == 'all' or case_info.get('event_type') == case_type:
                                records.append(case_info)
                                
                    except Exception as e:
                        logger_manager.log_error(f"Failed to parse case record {case_file['filename']}: {e}")
                        continue
                
                # 按時間排序（最新的在前）
                records.sort(key=lambda x: x['case_id'], reverse=True)
                
                # 分頁處理
                total_records = len(records)
                records = records[offset:offset + limit]
                
                return jsonify({
                    "success": True,
                    "data": {
                        "records": records,
                        "pagination": {
                            "total": total_records,
                            "limit": limit,
                            "offset": offset,
                            "has_more": offset + limit < total_records
                        },
                        "stats": stats,
                        "filters": {
                            "case_type": case_type,
                            "date_from": date_from,
                            "date_to": date_to
                        }
                    },
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
            except Exception as e:
                logger_manager.log_error(f"API get all records failed: {e}")
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route("/api/records/<case_id>", methods=["GET"])
        def api_get_single_record(case_id):
            """API: 獲取單一案件紀錄 (JSON格式)"""
            try:
                # 搜尋案件檔案
                filename = f"case_{case_id}.txt"
                content = case_manager.read_case_file(filename)
                
                if not content:
                    return jsonify({"success": False, "error": "案件紀錄不存在"})
                
                # 解析完整案件資訊
                case_info = case_manager.parse_case_record_full(content)
                case_info['filename'] = filename
                case_info['case_id'] = case_id
                
                # 解析時間
                try:
                    case_time = datetime.datetime.strptime(case_id, "%Y%m%d_%H%M%S")
                    case_info['timestamp'] = case_time.isoformat()
                    case_info['time'] = case_time.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    case_info['timestamp'] = None
                    case_info['time'] = None
                
                return jsonify({
                    "success": True,
                    "data": case_info,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
            except Exception as e:
                logger_manager.log_error(f"API get single record failed: {e}")
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route("/api/stats", methods=["GET"])
        def api_get_stats():
            """API: 獲取案件統計資料 (JSON格式)"""
            try:
                date_from = request.args.get('from', '')
                date_to = request.args.get('to', '')
                
                # 如果沒有指定日期範圍，預設為今天
                if not date_from:
                    date_from = datetime.datetime.now().strftime("%Y-%m-%d")
                if not date_to:
                    date_to = date_from
                
                # 獲取統計資料
                stats = case_manager.get_case_stats(date_from, date_to)
                
                return jsonify({
                    "success": True,
                    "data": {
                        "stats": stats,
                        "filters": {
                            "date_from": date_from,
                            "date_to": date_to
                        }
                    },
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
            except Exception as e:
                logger_manager.log_error(f"API get stats failed: {e}")
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route("/system/records/api", methods=["POST"])
        def get_records_api():
            """獲取案件紀錄資料API（網頁介面使用）"""
            try:
                data = request.get_json()
                case_type = data.get('case_type', 'all')
                date_from = data.get('date_from', '')
                date_to = data.get('date_to', '')
                
                records = []
                stats = {
                    'total_cases': 0,
                    'ohca_cases': 0,
                    'internal_cases': 0,
                    'surgical_cases': 0
                }
                
                # 如果沒有指定日期範圍，顯示所有記錄
                # 保持空字串以顯示所有記錄
                
                # 獲取案件檔案
                case_files = case_manager.get_case_files(date_from, date_to)
                
                for case_file in case_files:
                    try:
                        # 讀取案件檔案
                        content = case_manager.read_case_file(case_file['filename'])
                        if content:
                            # 解析案件資訊
                            case_info = case_manager.parse_case_record(content)
                            case_info.update(case_file)
                            
                            # 統計
                            stats['total_cases'] += 1
                            if case_info.get('event_type') == 'OHCA':
                                stats['ohca_cases'] += 1
                            elif case_info.get('event_type') == '內科':
                                stats['internal_cases'] += 1
                            elif case_info.get('event_type') == '外科':
                                stats['surgical_cases'] += 1
                            
                            # 類型過濾
                            if case_type == 'all' or case_info.get('event_type') == case_type:
                                records.append(case_info)
                                
                    except Exception as e:
                        logger_manager.log_error(f"Failed to parse case record {case_file['filename']}: {e}")
                        continue
                
                # 按時間排序（最新的在前）
                records.sort(key=lambda x: x['case_id'], reverse=True)
                
                return jsonify({
                    "success": True,
                    "records": records,
                    "stats": stats
                })
                
            except Exception as e:
                logger_manager.log_error(f"Get records API failed: {e}")
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route("/system/logs/api", methods=["POST"])
        def get_logs_api():
            """獲取日誌資料API"""
            try:
                data = request.get_json()
                log_type = data.get('log_type', 'all')
                date_from = data.get('date_from', '')
                date_to = data.get('date_to', '')
                ip_filter = data.get('ip_filter', '')
                
                logs = []
                stats = {
                    'total_requests': 0,
                    'user_actions': 0,
                    'incidents': 0,
                    'tests': 0
                }
                
                # 如果沒有指定日期範圍，預設為今天
                if not date_from:
                    date_from = datetime.datetime.now().strftime("%Y-%m-%d")
                if not date_to:
                    date_to = date_from
                
                # 轉換日期格式並生成日期列表
                try:
                    start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
                    end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
                    
                    # 生成日期範圍
                    current_date = start_date
                    while current_date <= end_date:
                        date_str = current_date.strftime("%Y%m%d")
                        log_filename = logger_manager.get_log_filename(date_str)
                        
                        # 讀取日誌檔案
                        if os.path.exists(log_filename):
                            log_lines = logger_manager.read_log_file(os.path.basename(log_filename))
                            logger_manager.log_user_action("日誌API調試", f"讀取到 {len(log_lines)} 行日誌")
                            
                            for i, line in enumerate(log_lines):
                                line = line.strip()
                                if not line:
                                    continue
                                
                                # 只調試前5行
                                if i < 5:
                                    logger_manager.log_user_action("日誌行調試", f"第{i+1}行: {repr(line[:100])}")
                                
                                # 解析日誌行
                                try:
                                    # 嘗試多種解析方式
                                    if ' [' in line and '] ' in line:
                                        parts = line.split(' [', 2)
                                        if len(parts) >= 2:
                                            timestamp = parts[0]
                                            # 從 parts[1] 中分離 level 和 message
                                            level_message = parts[1]
                                            if '] ' in level_message:
                                                level, message = level_message.split('] ', 1)
                                                level = level.strip()
                                                message = message.strip()
                                                
                                                # 調試解析結果
                                                if i < 5:
                                                    logger_manager.log_user_action("解析成功", f"第{i+1}行: {timestamp} | {level} | {message[:30]}...")
                                            else:
                                                if i < 5:
                                                    logger_manager.log_user_action("解析失敗", f"第{i+1}行找不到 '] '")
                                                continue
                                        else:
                                            if i < 5:
                                                logger_manager.log_user_action("解析失敗", f"第{i+1}行parts長度不足: {len(parts)}")
                                            continue
                                    elif '] ' in line:
                                        # 備用解析方式
                                        bracket_pos = line.find('] ')
                                        if bracket_pos > 0:
                                            timestamp_level = line[:bracket_pos]
                                            message = line[bracket_pos + 2:]
                                            if ' [' in timestamp_level:
                                                timestamp, level = timestamp_level.split(' [', 1)
                                                level = level.rstrip(']')
                                            else:
                                                continue
                                        else:
                                            continue
                                    else:
                                        if i < 5:
                                            logger_manager.log_user_action("解析失敗", f"第{i+1}行格式不符合: 找不到 ' [' 或 '] '")
                                        continue
                                    
                                    # 類型過濾
                                    if log_type != 'all' and level.lower() != log_type.lower():
                                        if i < 5:
                                            logger_manager.log_user_action("類型過濾", f"第{i+1}行被過濾: {level} != {log_type}")
                                        continue
                                    
                                    # IP過濾
                                    if ip_filter and ip_filter not in message:
                                        if i < 5:
                                            logger_manager.log_user_action("IP過濾", f"第{i+1}行被過濾: IP不匹配")
                                        continue
                                    
                                    logs.append({
                                        'timestamp': timestamp,
                                        'type': level,
                                        'content': message
                                    })
                                    
                                    # 統計
                                    stats['total_requests'] += 1
                                    if 'USER_ACTION' in message or 'User Action' in message:
                                        stats['user_actions'] += 1
                                    elif 'INCIDENT' in message or '案件' in message:
                                        stats['incidents'] += 1
                                    elif 'TEST' in message or '測試' in message:
                                        stats['tests'] += 1
                                    
                                    # 記錄成功添加的日誌
                                    if i < 5:
                                        logger_manager.log_user_action("日誌添加成功", f"第{i+1}行已添加: {level}")
                                    
                                except Exception as e:
                                    continue
                        
                        current_date += datetime.timedelta(days=1)
                
                except ValueError as e:
                    return jsonify({"success": False, "error": f"日期格式錯誤: {str(e)}"})
                
                # 按時間排序（最新的在前）
                logs.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # 記錄最終結果
                logger_manager.log_user_action("日誌API結果", f"返回 {len(logs)} 條日誌，統計: {stats}")
                
                return jsonify({
                    "success": True,
                    "logs": logs,
                    "stats": stats
                })
                
            except Exception as e:
                logger_manager.log_error(f"Get logs API failed: {e}")
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route("/system/logs/export", methods=["POST"])
        def export_logs():
            """匯出日誌檔案"""
            try:
                data = request.get_json()
                date_from = data.get('date_from', '')
                date_to = data.get('date_to', '')
                
                # 如果沒有指定日期範圍，預設為今天
                if not date_from:
                    date_from = datetime.datetime.now().strftime("%Y-%m-%d")
                if not date_to:
                    date_to = date_from
                
                # 生成匯出檔案名稱
                export_filename = f"logs_export_{date_from}_{date_to}.txt"
                export_path = os.path.join("logs", export_filename)
                
                # 收集日誌內容
                all_logs = []
                try:
                    start_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
                    end_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
                    
                    current_date = start_date
                    while current_date <= end_date:
                        date_str = current_date.strftime("%Y%m%d")
                        log_filename = logger_manager.get_log_filename(date_str)
                        
                        if os.path.exists(log_filename):
                            log_lines = logger_manager.read_log_file(f"flask_app_{date_str}.log")
                            all_logs.extend(log_lines)
                        
                        current_date += datetime.timedelta(days=1)
                
                except ValueError as e:
                    return jsonify({"success": False, "error": f"日期格式錯誤: {str(e)}"})
                
                # 寫入匯出檔案
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(f"日誌匯出 / Log Export\n")
                    f.write(f"日期範圍 / Date Range: {date_from} ~ {date_to}\n")
                    f.write(f"匯出時間 / Export Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*50 + "\n\n")
                    f.writelines(all_logs)
                
                # 返回檔案下載
                from flask import send_file
                return send_file(
                    export_path,
                    as_attachment=True,
                    download_name=export_filename,
                    mimetype='text/plain'
                )
                
            except Exception as e:
                logger_manager.log_error(f"Export logs failed: {e}")
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route("/system/logs/clear", methods=["POST"])
        def clear_logs():
            """清除日誌檔案"""
            try:
                data = request.get_json()
                date_from = data.get('date_from', '')
                date_to = data.get('date_to', '')
                
                cleared_files = logger_manager.clear_log_files(date_from, date_to)
                message = f"已清除 {len(cleared_files)} 個日誌檔案" if cleared_files else "沒有找到要清除的日誌檔案"
                
                return jsonify({
                    "success": True,
                    "message": message,
                    "cleared_files": cleared_files
                })
                
            except Exception as e:
                logger_manager.log_error(f"Clear logs failed: {e}")
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route("/system/records/export", methods=["POST"])
        def export_records():
            """匯出案件紀錄檔案"""
            try:
                data = request.get_json()
                date_from = data.get('date_from', '')
                date_to = data.get('date_to', '')
                
                # 如果沒有指定日期範圍，顯示所有記錄
                # 保持空字串以顯示所有記錄
                
                # 生成匯出檔案名稱
                if date_from and date_to:
                    export_filename = f"records_export_{date_from}_{date_to}.txt"
                else:
                    export_filename = f"records_export_all.txt"
                export_path = os.path.join("record", export_filename)
                
                # 收集案件紀錄
                case_files = case_manager.get_case_files(date_from, date_to)
                
                # 寫入匯出檔案
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(f"案件紀錄匯出 / Case Records Export\n")
                    f.write(f"日期範圍 / Date Range: {date_from} ~ {date_to}\n")
                    f.write(f"匯出時間 / Export Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"案件總數 / Total Cases: {len(case_files)}\n")
                    f.write("="*50 + "\n\n")
                    
                    for case_file in case_files:
                        content = case_manager.read_case_file(case_file['filename'])
                        if content:
                            f.write(f"案件檔案 / Case File: {case_file['filename']}\n")
                            f.write("-" * 30 + "\n")
                            f.write(content)
                            f.write("\n" + "="*50 + "\n\n")
                
                return jsonify({
                    "success": True,
                    "message": f"案件紀錄已匯出到 {export_filename}",
                    "filename": export_filename
                })
                
            except Exception as e:
                logger_manager.log_error(f"Export records failed: {e}")
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route("/system/records/clear", methods=["POST"])
        def clear_records():
            """清除案件紀錄檔案"""
            try:
                data = request.get_json()
                date_from = data.get('date_from', '')
                date_to = data.get('date_to', '')
                
                cleared_files = case_manager.clear_case_files(date_from, date_to)
                message = f"已清除 {len(cleared_files)} 個案件紀錄檔案" if cleared_files else "沒有找到要清除的案件紀錄檔案"
                
                return jsonify({
                    "success": True,
                    "message": message,
                    "cleared_files": cleared_files
                })
                
            except Exception as e:
                logger_manager.log_error(f"Clear records failed: {e}")
                return jsonify({"success": False, "error": str(e)})
