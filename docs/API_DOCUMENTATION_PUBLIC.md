# 緊急事件通報系統 - 公開API文檔
# Emergency Management System - Public API Documentation

## 概述 / Overview

本系統提供公開的API接口，供外部系統訪問和整合。所有API都通過主網站 (端口 8000) 提供，無需通過管理網站。

This system provides public API interfaces for external system access and integration. All APIs are provided through the main website (port 8000) without requiring access to the admin website.

## 基礎URL / Base URL

```
http://your-domain.com:8000/api
```

## API端點 / API Endpoints

### 1. 系統統計 / System Statistics

**端點 / Endpoint**: `GET /api/stats`

**描述 / Description**: 獲取系統整體統計資料 / Get overall system statistics

**回應範例 / Response Example**:
```json
{
  "success": true,
  "data": {
    "cases": {
      "total": 25,
      "today": 3,
      "ohca": 1,
      "internal": 1,
      "surgical": 1
    },
    "logs": {
      "total_files": 5,
      "latest_file": "flask_app_20250922.log"
    },
    "system": {
      "status": "running",
      "uptime": "active"
    }
  }
}
```

### 2. 案件列表 / Case List

**端點 / Endpoint**: `GET /api/cases`

**參數 / Parameters**:
- `type` (可選): 案件類型 (`all`, `OHCA`, `內科`, `外科`)
- `limit` (可選): 每頁數量 (預設: 10)
- `offset` (可選): 偏移量 (預設: 0)

**回應範例 / Response Example**:
```json
{
  "success": true,
  "data": {
    "cases": [
      {
        "case_id": "case_20250922_001.txt",
        "event_type": "OHCA",
        "location": "行政大樓",
        "room": "1樓",
        "timestamp": "2025-09-22 10:30:00",
        "status": "completed"
      }
    ],
    "total": 25,
    "limit": 10,
    "offset": 0
  }
}
```

### 3. 案件詳情 / Case Detail

**端點 / Endpoint**: `GET /api/cases/{case_id}`

**參數 / Parameters**:
- `case_id`: 案件檔案名稱

**回應範例 / Response Example**:
```json
{
  "success": true,
  "data": {
    "case_id": "case_20250922_001.txt",
    "event_type": "OHCA",
    "location": "行政大樓",
    "room": "1樓",
    "content": "患者無意識，需要緊急處理",
    "timestamp": "2025-09-22 10:30:00",
    "reporter_info": {
      "ip": "192.168.1.100",
      "country": "TW",
      "city": "台中市"
    },
    "broadcast_result": {
      "discord_success": true,
      "line_success": true,
      "discord_message_id": "123456789"
    }
  }
}
```

### 4. 日誌資料 / Log Data

**端點 / Endpoint**: `GET /api/logs`

**參數 / Parameters**:
- `type` (可選): 日誌類型 (`all`, `INFO`, `ERROR`, `WARNING`)
- `limit` (可選): 每頁數量 (預設: 50)
- `date_from` (可選): 開始日期 (格式: YYYY-MM-DD)
- `date_to` (可選): 結束日期 (格式: YYYY-MM-DD)

**回應範例 / Response Example**:
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "timestamp": "2025-09-22 10:30:00",
        "type": "INFO",
        "content": "User Action: 提交案件通報 | Details: Event=OHCA | Location=行政大樓"
      }
    ],
    "stats": {
      "total_requests": 150,
      "user_actions": 25,
      "incidents": 3,
      "tests": 2
    },
    "total": 50
  }
}
```

## 錯誤處理 / Error Handling

所有API都遵循統一的錯誤回應格式：

All APIs follow a unified error response format:

```json
{
  "success": false,
  "error": "錯誤訊息 / Error message"
}
```

**HTTP狀態碼 / HTTP Status Codes**:
- `200`: 成功 / Success
- `400`: 請求參數錯誤 / Bad Request
- `404`: 資源不存在 / Not Found
- `500`: 伺服器內部錯誤 / Internal Server Error

## 使用範例 / Usage Examples

### 1. 獲取今日案件統計
```bash
curl "http://your-domain.com:8000/api/stats"
```

### 2. 獲取最近10個案件
```bash
curl "http://your-domain.com:8000/api/cases?limit=10"
```

### 3. 獲取特定案件詳情
```bash
curl "http://your-domain.com:8000/api/cases/case_20250922_001.txt"
```

### 4. 獲取今日日誌
```bash
curl "http://your-domain.com:8000/api/logs?date_from=2025-09-22&date_to=2025-09-22"
```

## 安全考量 / Security Considerations

1. **只讀訪問**: 所有公開API都是只讀的，不允許修改數據
2. **無認證**: 目前API不需要認證，適合內部系統使用
3. **敏感操作**: 清除、匯出等敏感操作仍保留在管理網站中
4. **速率限制**: 建議實施速率限制以防止濫用

## 整合建議 / Integration Recommendations

1. **監控系統**: 使用 `/api/stats` 監控系統狀態
2. **案件追蹤**: 使用 `/api/cases` 追蹤案件處理進度
3. **日誌分析**: 使用 `/api/logs` 進行日誌分析和報告
4. **儀表板**: 結合多個API創建實時儀表板

## 更新日誌 / Changelog

- **2025-09-22**: 初始版本發布 / Initial version released
- **2025-09-22**: 添加案件和日誌API / Added case and log APIs
