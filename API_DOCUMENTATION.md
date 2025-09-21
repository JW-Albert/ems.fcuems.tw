# 📡 API 詳細運作說明文件

## 📋 概述

本系統提供完整的RESTful API，支援案件紀錄的查詢、統計、管理等功能。所有API都採用JSON格式進行資料交換。

## 🔧 API 架構

### 基礎資訊
- **基礎URL**: `http://your-domain.com`
- **資料格式**: JSON
- **編碼**: UTF-8
- **認證**: 無需認證（內部系統）

### 回應格式
所有API都遵循統一的回應格式：

**成功回應：**
```json
{
    "success": true,
    "data": { ... },
    "timestamp": "2024-01-15T15:30:00"
}
```

**錯誤回應：**
```json
{
    "success": false,
    "error": "錯誤訊息"
}
```

## 📊 API 端點詳解

### 1. 案件紀錄管理 API

#### 1.1 獲取所有案件紀錄
**端點**: `GET /api/records`

**功能**: 獲取案件紀錄列表，支援過濾、分頁和統計

**查詢參數**:
| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `type` | string | 否 | `all` | 案件類型 (`all`, `OHCA`, `內科`, `外科`) |
| `from` | string | 否 | 今天 | 開始日期 (`YYYY-MM-DD`) |
| `to` | string | 否 | 今天 | 結束日期 (`YYYY-MM-DD`) |
| `limit` | integer | 否 | `100` | 每頁筆數 |
| `offset` | integer | 否 | `0` | 分頁偏移 |

**請求範例**:
```http
GET /api/records?type=OHCA&from=2024-01-15&to=2024-01-16&limit=50&offset=0
```

**回應範例**:
```json
{
    "success": true,
    "data": {
        "records": [
            {
                "filename": "case_20240115_143025.txt",
                "case_id": "20240115_143025",
                "timestamp": "2024-01-15T14:30:25",
                "time": "2024-01-15 14:30:25",
                "event_type": "OHCA",
                "location": "行政大樓",
                "room": "1樓",
                "content": "患者無意識，需要CPR",
                "message": "🚨 緊急事件通報 / Emergency Alert\n案件分類 / Case Type: OHCA\n...",
                "ip": "192.168.1.100",
                "country": "TW",
                "city": "Taipei",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "discord_success": true,
                "line_success": true,
                "discord_message_id": "1234567890",
                "server_time": "2024-01-15 14:30:25",
                "file_path": "record/case_20240115_143025.txt"
            }
        ],
        "pagination": {
            "total": 25,
            "limit": 50,
            "offset": 0,
            "has_more": false
        },
        "stats": {
            "total_cases": 25,
            "ohca_cases": 10,
            "internal_cases": 8,
            "surgical_cases": 7
        },
        "filters": {
            "case_type": "OHCA",
            "date_from": "2024-01-15",
            "date_to": "2024-01-16"
        }
    },
    "timestamp": "2024-01-15T15:30:00"
}
```

#### 1.2 獲取單一案件紀錄
**端點**: `GET /api/records/<case_id>`

**功能**: 根據案件ID獲取單一案件紀錄的完整資訊

**路徑參數**:
| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `case_id` | string | 是 | 案件ID格式: `YYYYMMDD_HHMMSS` |

**請求範例**:
```http
GET /api/records/20240115_143025
```

**回應範例**:
```json
{
    "success": true,
    "data": {
        "filename": "case_20240115_143025.txt",
        "case_id": "20240115_143025",
        "timestamp": "2024-01-15T14:30:25",
        "time": "2024-01-15 14:30:25",
        "event_type": "OHCA",
        "location": "行政大樓",
        "room": "1樓",
        "content": "患者無意識，需要CPR",
        "message": "🚨 緊急事件通報 / Emergency Alert\n案件分類 / Case Type: OHCA\n案件地點 / Location: 行政大樓\n案件位置 / Position: 1樓\n補充資訊 / Additional Info: 患者無意識，需要CPR\n通報時間 / Report Time: 2024-01-15 14:30:25",
        "ip": "192.168.1.100",
        "country": "TW",
        "city": "Taipei",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "discord_success": true,
        "line_success": true,
        "discord_message_id": "1234567890",
        "server_time": "2024-01-15 14:30:25",
        "file_path": "record/case_20240115_143025.txt"
    },
    "timestamp": "2024-01-15T15:30:00"
}
```

#### 1.3 獲取案件統計資料
**端點**: `GET /api/stats`

**功能**: 獲取案件統計資料，包括類型分布、地點分布、時間分布等

**查詢參數**:
| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `from` | string | 否 | 今天 | 開始日期 (`YYYY-MM-DD`) |
| `to` | string | 否 | 今天 | 結束日期 (`YYYY-MM-DD`) |

**請求範例**:
```http
GET /api/stats?from=2024-01-15&to=2024-01-16
```

**回應範例**:
```json
{
    "success": true,
    "data": {
        "stats": {
            "total_cases": 25,
            "ohca_cases": 10,
            "internal_cases": 8,
            "surgical_cases": 7,
            "by_location": {
                "行政大樓": 8,
                "圖書館": 5,
                "工學大樓": 7,
                "商學大樓": 5
            },
            "by_hour": {
                "8": 2,
                "9": 3,
                "10": 4,
                "14": 5,
                "15": 6,
                "16": 5
            },
            "by_date": {
                "2024-01-15": 12,
                "2024-01-16": 13
            }
        },
        "filters": {
            "date_from": "2024-01-15",
            "date_to": "2024-01-16"
        }
    },
    "timestamp": "2024-01-15T15:30:00"
}
```

### 2. 網頁介面 API

#### 2.1 案件紀錄查詢（網頁版）
**端點**: `POST /system/records/api`

**功能**: 為網頁介面提供案件紀錄查詢功能

**請求格式**:
```json
{
    "case_type": "all|OHCA|內科|外科",
    "date_from": "2024-01-15",
    "date_to": "2024-01-16"
}
```

**回應格式**:
```json
{
    "success": true,
    "records": [ ... ],
    "stats": { ... }
}
```

#### 2.2 日誌查詢（網頁版）
**端點**: `POST /system/logs/api`

**功能**: 為網頁介面提供日誌查詢功能

**請求格式**:
```json
{
    "log_type": "all|info|error|warning",
    "date_from": "2024-01-15",
    "date_to": "2024-01-16",
    "ip_filter": "192.168.1.100"
}
```

**回應格式**:
```json
{
    "success": true,
    "logs": [
        {
            "timestamp": "2024-01-15 14:30:25",
            "level": "INFO",
            "message": "User Action: 頁面訪問 | IP: 192.168.1.100"
        }
    ],
    "stats": {
        "total_logs": 150,
        "info_logs": 120,
        "error_logs": 5,
        "warning_logs": 25
    }
}
```

### 3. 檔案管理 API

#### 3.1 匯出日誌檔案
**端點**: `POST /system/logs/export`

**功能**: 匯出指定日期範圍的日誌檔案

**請求格式**:
```json
{
    "date_from": "2024-01-15",
    "date_to": "2024-01-16"
}
```

**回應格式**:
```json
{
    "success": true,
    "message": "日誌已匯出到 logs_export_2024-01-15_2024-01-16.txt",
    "filename": "logs_export_2024-01-15_2024-01-16.txt"
}
```

#### 3.2 清除日誌檔案
**端點**: `POST /system/logs/clear`

**功能**: 清除指定日期範圍的日誌檔案

**請求格式**:
```json
{
    "date_from": "2024-01-15",
    "date_to": "2024-01-16"
}
```

**回應格式**:
```json
{
    "success": true,
    "message": "已清除 3 個日誌檔案",
    "cleared_files": [
        "flask_app_20240115.log",
        "flask_app_20240116.log"
    ]
}
```

#### 3.3 匯出案件紀錄
**端點**: `POST /system/records/export`

**功能**: 匯出指定日期範圍的案件紀錄

**請求格式**:
```json
{
    "date_from": "2024-01-15",
    "date_to": "2024-01-16"
}
```

**回應格式**:
```json
{
    "success": true,
    "message": "案件紀錄已匯出到 records_export_2024-01-15_2024-01-16.txt",
    "filename": "records_export_2024-01-15_2024-01-16.txt"
}
```

#### 3.4 清除案件紀錄
**端點**: `POST /system/records/clear`

**功能**: 清除指定日期範圍的案件紀錄

**請求格式**:
```json
{
    "date_from": "2024-01-15",
    "date_to": "2024-01-16"
}
```

**回應格式**:
```json
{
    "success": true,
    "message": "已清除 5 個案件紀錄檔案",
    "cleared_files": [
        "case_20240115_143025.txt",
        "case_20240115_150230.txt",
        "case_20240116_091545.txt"
    ]
}
```

### 4. 檔案存取 API

#### 4.1 查看案件紀錄
**端點**: `GET /system/records/view/<filename>`

**功能**: 直接查看案件紀錄檔案內容

**路徑參數**:
| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `filename` | string | 是 | 案件檔案名稱 |

**請求範例**:
```http
GET /system/records/view/case_20240115_143025.txt
```

**回應**: 純文字格式的案件紀錄內容

#### 4.2 下載案件紀錄
**端點**: `GET /system/records/download/<filename>`

**功能**: 下載案件紀錄檔案

**路徑參數**:
| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `filename` | string | 是 | 案件檔案名稱 |

**請求範例**:
```http
GET /system/records/download/case_20240115_143025.txt
```

**回應**: 檔案下載

## 🔧 API 使用範例

### 1. 使用 curl 測試

#### 獲取所有案件
```bash
curl "http://127.0.0.1:5000/api/records"
```

#### 獲取OHCA案件
```bash
curl "http://127.0.0.1:5000/api/records?type=OHCA"
```

#### 獲取指定日期範圍的案件
```bash
curl "http://127.0.0.1:5000/api/records?from=2024-01-15&to=2024-01-16"
```

#### 分頁查詢
```bash
curl "http://127.0.0.1:5000/api/records?limit=10&offset=20"
```

#### 獲取單一案件
```bash
curl "http://127.0.0.1:5000/api/records/20240115_143025"
```

#### 獲取統計資料
```bash
curl "http://127.0.0.1:5000/api/stats?from=2024-01-15&to=2024-01-16"
```

### 2. 使用 JavaScript 測試

#### 獲取所有案件
```javascript
fetch('/api/records')
    .then(response => response.json())
    .then(data => {
        console.log('案件總數:', data.data.stats.total_cases);
        console.log('案件列表:', data.data.records);
    })
    .catch(error => console.error('錯誤:', error));
```

#### 獲取OHCA案件
```javascript
fetch('/api/records?type=OHCA')
    .then(response => response.json())
    .then(data => {
        console.log('OHCA案件:', data.data.records);
    })
    .catch(error => console.error('錯誤:', error));
```

#### 獲取統計資料
```javascript
fetch('/api/stats?from=2024-01-15&to=2024-01-16')
    .then(response => response.json())
    .then(data => {
        console.log('統計資料:', data.data.stats);
    })
    .catch(error => console.error('錯誤:', error));
```

### 3. 使用 Python 測試

#### 獲取所有案件
```python
import requests

response = requests.get('http://127.0.0.1:5000/api/records')
data = response.json()

if data['success']:
    print(f"案件總數: {data['data']['stats']['total_cases']}")
    for record in data['data']['records']:
        print(f"案件: {record['case_id']} - {record['event_type']}")
else:
    print(f"錯誤: {data['error']}")
```

#### 獲取OHCA案件
```python
import requests

response = requests.get('http://127.0.0.1:5000/api/records?type=OHCA')
data = response.json()

if data['success']:
    print(f"OHCA案件數: {data['data']['stats']['ohca_cases']}")
    for record in data['data']['records']:
        print(f"OHCA案件: {record['case_id']} - {record['location']}")
else:
    print(f"錯誤: {data['error']}")
```

#### 獲取統計資料
```python
import requests

response = requests.get('http://127.0.0.1:5000/api/stats?from=2024-01-15&to=2024-01-16')
data = response.json()

if data['success']:
    stats = data['data']['stats']
    print(f"總案件數: {stats['total_cases']}")
    print(f"OHCA案件: {stats['ohca_cases']}")
    print(f"內科案件: {stats['internal_cases']}")
    print(f"外科案件: {stats['surgical_cases']}")
    
    print("\n地點分布:")
    for location, count in stats['by_location'].items():
        print(f"  {location}: {count}")
    
    print("\n時間分布:")
    for hour, count in stats['by_hour'].items():
        print(f"  {hour}時: {count}")
else:
    print(f"錯誤: {data['error']}")
```

## 📊 資料結構說明

### 案件紀錄資料結構
```json
{
    "filename": "case_20240115_143025.txt",
    "case_id": "20240115_143025",
    "timestamp": "2024-01-15T14:30:25",
    "time": "2024-01-15 14:30:25",
    "event_type": "OHCA|內科|外科",
    "location": "案件地點",
    "room": "案件位置",
    "content": "補充資訊",
    "message": "完整訊息內容",
    "ip": "通報者IP",
    "country": "國家代碼",
    "city": "城市名稱",
    "user_agent": "瀏覽器資訊",
    "discord_success": true|false,
    "line_success": true|false,
    "discord_message_id": "Discord訊息ID",
    "server_time": "伺服器時間",
    "file_path": "檔案路徑"
}
```

### 統計資料結構
```json
{
    "total_cases": 25,
    "ohca_cases": 10,
    "internal_cases": 8,
    "surgical_cases": 7,
    "by_location": {
        "行政大樓": 8,
        "圖書館": 5,
        "工學大樓": 7,
        "商學大樓": 5
    },
    "by_hour": {
        "8": 2,
        "9": 3,
        "10": 4,
        "14": 5,
        "15": 6,
        "16": 5
    },
    "by_date": {
        "2024-01-15": 12,
        "2024-01-16": 13
    }
}
```

### 分頁資料結構
```json
{
    "total": 25,
    "limit": 50,
    "offset": 0,
    "has_more": false
}
```

## ⚠️ 錯誤處理

### 常見錯誤碼和訊息

| 錯誤類型 | 錯誤訊息 | 說明 |
|----------|----------|------|
| 日期格式錯誤 | `日期格式錯誤: time data 'invalid-date' does not match format '%Y-%m-%d'` | 日期參數格式不正確 |
| 案件不存在 | `案件紀錄不存在` | 指定的案件ID不存在 |
| 檔案不存在 | `檔案不存在` | 指定的檔案不存在 |
| 配置錯誤 | `缺少必要的配置: LINE_BOT_API_TOKEN, DISCORD_WEBHOOK_URL` | 系統配置不完整 |

### 錯誤處理範例

#### JavaScript 錯誤處理
```javascript
fetch('/api/records')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('成功:', data.data);
        } else {
            console.error('API錯誤:', data.error);
        }
    })
    .catch(error => {
        console.error('網路錯誤:', error);
    });
```

#### Python 錯誤處理
```python
import requests

try:
    response = requests.get('http://127.0.0.1:5000/api/records')
    data = response.json()
    
    if data['success']:
        print('成功:', data['data'])
    else:
        print('API錯誤:', data['error'])
        
except requests.exceptions.RequestException as e:
    print('網路錯誤:', e)
except Exception as e:
    print('其他錯誤:', e)
```

## 🔒 安全性考量

### 1. 輸入驗證
- 所有日期參數都經過格式驗證
- 案件ID格式嚴格驗證
- 檔案名稱路徑檢查防止目錄遍歷攻擊

### 2. 錯誤處理
- 不暴露內部系統資訊
- 統一的錯誤回應格式
- 詳細的錯誤日誌記錄

### 3. 資料保護
- 敏感資訊（如IP地址）僅在內部使用
- 日誌檔案定期清理
- 案件紀錄檔案權限控制

## 📈 效能優化

### 1. 分頁支援
- 預設限制每頁100筆記錄
- 支援offset和limit參數
- 避免一次載入過多資料

### 2. 快取機制
- 統計資料可考慮快取
- 檔案列表快取
- 減少重複計算

### 3. 資料庫優化
- 按時間排序優化
- 索引建立建議
- 查詢條件優化

## 🚀 擴展建議

### 1. 認證機制
- JWT Token認證
- API Key認證
- 角色權限控制

### 2. 速率限制
- 請求頻率限制
- IP白名單
- 防止濫用

### 3. 監控和告警
- API使用統計
- 錯誤率監控
- 效能指標追蹤

### 4. 版本控制
- API版本管理
- 向後相容性
- 漸進式升級

---

**注意**: 本API文件基於當前系統架構，如有更新請參考最新版本。建議在生產環境使用前進行充分測試。
