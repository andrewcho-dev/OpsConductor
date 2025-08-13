# OpsConductor API Reference

## Overview

The OpsConductor API provides comprehensive access to job management, target administration, and execution monitoring with hierarchical serialization support.

## Base URL
```
http://localhost:8000/api
```

## Authentication

All API endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

## Execution Serialization

The API uses hierarchical serial identifiers for all execution-related operations:

- **Job Serial**: `J20250001` (9 characters)
- **Execution Serial**: `J20250001.0001` (14 characters)
- **Branch Serial**: `J20250001.0001.0001` (19 characters)
- **Target Serial**: `T20250001` (9 characters)

## Jobs API

### Create Job
```http
POST /api/jobs
Content-Type: application/json

{
  "name": "System Update",
  "description": "Update all production servers",
  "job_type": "command",
  "actions": [
    {
      "action_type": "command",
      "action_name": "update_system",
      "action_parameters": {
        "command": "sudo apt update && sudo apt upgrade -y"
      }
    }
  ],
  "target_ids": [1, 2, 3],
  "scheduled_at": "2025-01-08T10:00:00Z"
}
```

**Response:**
```json
{
  "id": 1,
  "job_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "job_serial": "J20250001",
  "name": "System Update",
  "description": "Update all production servers",
  "job_type": "command",
  "status": "scheduled",
  "created_at": "2025-01-08T09:00:00Z",
  "scheduled_at": "2025-01-08T10:00:00Z",
  "actions": [...]
}
```

### Execute Job
```http
POST /api/jobs/{job_id}/execute
Content-Type: application/json

{
  "target_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "id": 1,
  "execution_uuid": "550e8400-e29b-41d4-a716-446655440001",
  "execution_serial": "J20250001.0001",
  "execution_number": 1,
  "status": "running",
  "started_at": "2025-01-08T10:00:00Z",
  "branches": [
    {
      "id": 1,
      "branch_uuid": "550e8400-e29b-41d4-a716-446655440002",
      "branch_serial": "J20250001.0001.0001",
      "branch_id": "001",
      "target_id": 1,
      "target_serial_ref": "T20250001",
      "status": "running",
      "started_at": "2025-01-08T10:00:00Z"
    }
  ]
}
```

### Get Job Executions
```http
GET /api/jobs/{job_id}/executions
```

**Response:**
```json
[
  {
    "id": 1,
    "execution_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "execution_serial": "J20250001.0001",
    "execution_number": 1,
    "status": "completed",
    "started_at": "2025-01-08T10:00:00Z",
    "completed_at": "2025-01-08T10:05:00Z",
    "branches": [...]
  }
]
```

## Executions API

### Get Execution by Serial
```http
GET /api/executions/serial/{execution_serial}
```

**Example:**
```http
GET /api/executions/serial/J20250001.0001
```

**Response:**
```json
{
  "id": 1,
  "execution_uuid": "550e8400-e29b-41d4-a716-446655440001",
  "execution_serial": "J20250001.0001",
  "execution_number": 1,
  "status": "completed",
  "started_at": "2025-01-08T10:00:00Z",
  "completed_at": "2025-01-08T10:05:00Z",
  "job": {
    "id": 1,
    "job_serial": "J20250001",
    "name": "System Update"
  },
  "branches": [...]
}
```

### Get Branch by Serial
```http
GET /api/executions/branch/{branch_serial}
```

**Example:**
```http
GET /api/executions/branch/J20250001.0001.0001
```

**Response:**
```json
{
  "id": 1,
  "branch_uuid": "550e8400-e29b-41d4-a716-446655440002",
  "branch_serial": "J20250001.0001.0001",
  "branch_id": "001",
  "target_id": 1,
  "target_serial_ref": "T20250001",
  "status": "completed",
  "started_at": "2025-01-08T10:00:00Z",
  "completed_at": "2025-01-08T10:02:00Z",
  "result_output": "System updated successfully",
  "result_error": null,
  "exit_code": 0,
  "target": {
    "id": 1,
    "target_serial": "T20250001",
    "name": "prod-server-01",
    "ip_address": "192.168.1.100"
  }
}
```

### Search Executions
```http
GET /api/executions/search?q={query}&type={type}&limit={limit}
```

**Parameters:**
- `q`: Search query (serial, job name, target name)
- `type`: Filter by type (`execution`, `branch`, `all`)
- `limit`: Maximum results (default: 50)

**Example:**
```http
GET /api/executions/search?q=J20250001&type=execution&limit=10
```

## Targets API

### Get Target Performance
```http
GET /api/targets/{target_serial}/performance?days={days}
```

**Example:**
```http
GET /api/targets/T20250001/performance?days=30
```

**Response:**
```json
{
  "target_serial": "T20250001",
  "target_name": "prod-server-01",
  "period_days": 30,
  "total_executions": 45,
  "successful_executions": 42,
  "failed_executions": 3,
  "success_rate": 93.33,
  "average_duration": 120.5,
  "recent_executions": [
    {
      "branch_serial": "J20250001.0001.0001",
      "execution_serial": "J20250001.0001",
      "job_serial": "J20250001",
      "status": "completed",
      "duration": 115.2,
      "started_at": "2025-01-08T10:00:00Z"
    }
  ]
}
```

### Get Target Execution History
```http
GET /api/targets/{target_serial}/executions?limit={limit}&offset={offset}
```

**Example:**
```http
GET /api/targets/T20250001/executions?limit=20&offset=0
```

**Response:**
```json
{
  "target_serial": "T20250001",
  "total": 45,
  "limit": 20,
  "offset": 0,
  "executions": [
    {
      "branch_serial": "J20250001.0001.0001",
      "execution_serial": "J20250001.0001",
      "job_serial": "J20250001",
      "job_name": "System Update",
      "status": "completed",
      "started_at": "2025-01-08T10:00:00Z",
      "completed_at": "2025-01-08T10:02:00Z",
      "exit_code": 0
    }
  ]
}
```

## Analytics API

### Get Execution Analytics
```http
GET /api/analytics/executions?period={period}&group_by={group_by}
```

**Parameters:**
- `period`: Time period (`24h`, `7d`, `30d`, `90d`)
- `group_by`: Grouping (`hour`, `day`, `week`, `month`)

**Response:**
```json
{
  "period": "7d",
  "group_by": "day",
  "total_executions": 156,
  "successful_executions": 142,
  "failed_executions": 14,
  "success_rate": 91.03,
  "data": [
    {
      "date": "2025-01-08",
      "executions": 23,
      "successful": 21,
      "failed": 2,
      "success_rate": 91.30
    }
  ]
}
```

### Get Job Performance Metrics
```http
GET /api/analytics/jobs/{job_serial}/metrics?period={period}
```

**Example:**
```http
GET /api/analytics/jobs/J20250001/metrics?period=30d
```

**Response:**
```json
{
  "job_serial": "J20250001",
  "job_name": "System Update",
  "period": "30d",
  "total_executions": 12,
  "successful_executions": 11,
  "failed_executions": 1,
  "success_rate": 91.67,
  "average_duration": 125.4,
  "target_performance": [
    {
      "target_serial": "T20250001",
      "target_name": "prod-server-01",
      "executions": 12,
      "success_rate": 100.0,
      "average_duration": 115.2
    }
  ]
}
```

## Bulk Operations

### Bulk Execution Lookup
```http
POST /api/executions/bulk
Content-Type: application/json

{
  "serials": [
    "J20250001.0001.0001",
    "J20250001.0001.0002",
    "J20250001.0002.0001"
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "serial": "J20250001.0001.0001",
      "found": true,
      "data": {
        "branch_serial": "J20250001.0001.0001",
        "status": "completed",
        "target_serial_ref": "T20250001"
      }
    }
  ],
  "not_found": []
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": "validation_error",
  "message": "Invalid execution serial format",
  "details": {
    "field": "execution_serial",
    "expected_format": "J20250001.0001",
    "received": "invalid_serial"
  }
}
```

### Common Error Codes
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `422` - Validation Error (invalid data format)
- `500` - Internal Server Error

## Rate Limiting

API requests are rate-limited per user:
- **Standard Users**: 100 requests/minute
- **Administrators**: 500 requests/minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641648000
```

## Pagination

List endpoints support pagination:
```http
GET /api/jobs?page=1&per_page=20&sort=created_at&order=desc
```

**Response includes pagination metadata:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 156,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## WebSocket Events

Real-time execution updates via WebSocket:

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/executions');
```

### Event Types
```json
{
  "type": "execution_started",
  "data": {
    "execution_serial": "J20250001.0001",
    "job_serial": "J20250001",
    "status": "running",
    "started_at": "2025-01-08T10:00:00Z"
  }
}

{
  "type": "branch_completed",
  "data": {
    "branch_serial": "J20250001.0001.0001",
    "execution_serial": "J20250001.0001",
    "target_serial_ref": "T20250001",
    "status": "completed",
    "exit_code": 0,
    "completed_at": "2025-01-08T10:02:00Z"
  }
}
```

## SDK Examples

### Python SDK
```python
from enabledrm_sdk import EnableDRMClient

client = EnableDRMClient(
    base_url="http://localhost:8000",
    token="your_jwt_token"
)

# Get execution by serial
execution = client.executions.get_by_serial("J20250001.0001")
print(f"Status: {execution.status}")

# Get target performance
performance = client.targets.get_performance("T20250001", days=30)
print(f"Success rate: {performance.success_rate}%")
```

### JavaScript SDK
```javascript
import { EnableDRMClient } from '@enabledrm/sdk';

const client = new EnableDRMClient({
  baseURL: 'http://localhost:8000',
  token: 'your_jwt_token'
});

// Get execution by serial
const execution = await client.executions.getBySerial('J20250001.0001');
console.log(`Status: ${execution.status}`);

// Get target performance
const performance = await client.targets.getPerformance('T20250001', { days: 30 });
console.log(`Success rate: ${performance.successRate}%`);
```

This API reference provides comprehensive access to the EnableDRM platform's execution serialization system and all related functionality.