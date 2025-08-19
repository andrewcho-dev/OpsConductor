# API Consolidation Audit Report

## Current State Analysis

### Frontend API Usage (All endpoints currently used by frontend)

#### Jobs API
- ✅ `/api/v3/jobs/` - Already in v3
- ✅ `/api/v3/jobs/{id}` - Already in v3  
- ✅ `/api/v3/jobs/{id}/execute` - Already in v3
- ✅ `/api/v3/jobs/{id}/executions` - Already in v3
- ❌ `/api/jobs/safety/cleanup-stale` - Missing from v3
- ❌ `/api/jobs/safety/health` - Missing from v3
- ❌ `/api/jobs/schedules` - Missing from v3

#### Users API
- ❌ `/api/users/` - Currently in routers, needs to be in v3
- ❌ `/api/users/{id}` - Currently in routers, needs to be in v3
- ❌ `/api/users/{id}/change-password` - Currently in routers, needs to be in v3
- ❌ `/api/users/{id}/activate` - Currently in routers, needs to be in v3
- ❌ `/api/users/{id}/deactivate` - Currently in routers, needs to be in v3

#### Targets API
- ❌ `/api/targets/` - Currently in routers, needs to be in v3
- ❌ `/api/targets/{id}` - Currently in routers, needs to be in v3
- ❌ `/api/targets/{id}/test` - Currently in routers, needs to be in v3
- ❌ `/api/targets/health-check-batch` - Missing from v3
- ❌ `/api/v1/targets/bulk/test` - Currently in v1, needs to be in v3
- ❌ `/api/v1/targets/bulk/update` - Currently in v1, needs to be in v3
- ❌ `/api/v1/targets/statistics/overview` - Currently in v1, needs to be in v3
- ❌ `/api/v1/targets/health/check` - Currently in v1, needs to be in v3
- ❌ `/api/v1/targets/health/perform` - Currently in v1, needs to be in v3
- ❌ `/api/v1/targets/types` - Currently in v1, needs to be in v3

#### Auth API
- ❌ `/api/auth/refresh` - Currently in auth_session, needs to be in v3

#### System APIs
- ❌ `/api/system/info` - Currently in system_info, needs to be in v3
- ❌ `/api/v2/health/` - Currently in v2, needs to be in v3
- ❌ `/api/v2/health/application` - Currently in v2, needs to be in v3
- ❌ `/api/v2/health/database` - Currently in v2, needs to be in v3
- ❌ `/api/v2/health/system` - Currently in v2, needs to be in v3
- ❌ `/api/v2/health/volumes/prune` - Currently in v2, needs to be in v3

#### Monitoring APIs
- ❌ `/api/monitoring/netdata-info` - Missing from v3
- ❌ `/api/monitoring/system-metrics` - Missing from v3

#### Celery APIs
- ❌ `/api/celery/stats` - Currently in v1, needs to be in v3
- ❌ `/api/celery/queues` - Currently in v1, needs to be in v3
- ❌ `/api/celery/workers` - Currently in v1, needs to be in v3
- ❌ `/api/celery/active-tasks` - Missing from v3
- ❌ `/api/celery/metrics/history` - Missing from v3

#### Analytics/Metrics APIs
- ❌ `/api/v2/metrics/dashboard` - Currently in v2, needs to be in v3
- ❌ `/api/v2/metrics/jobs/performance` - Currently in v2, needs to be in v3
- ❌ `/api/v2/metrics/system/health` - Currently in v2, needs to be in v3
- ❌ `/api/v2/metrics/trends/executions` - Currently in v2, needs to be in v3
- ❌ `/api/v2/metrics/reports/summary` - Currently in v2, needs to be in v3

#### Audit APIs
- ❌ `/api/v1/audit/event-types` - Currently in v1, needs to be in v3
- ❌ `/api/v1/audit/lookups/targets` - Currently in v1, needs to be in v3

### Backend API Structure Analysis

#### Currently in v3:
- `/api/v3/jobs/` - Complete jobs API
- `/api/schedules/` - Job schedules (but wrong prefix!)

#### Currently in v2:
- Multiple enhanced APIs that need to be moved to v3

#### Currently in v1:
- Celery monitoring
- Some target operations
- Audit lookups

#### Currently in routers (no version):
- Users API
- Targets API  
- Auth API

## Consolidation Plan

### Phase 1: Move/Copy APIs to v3 Structure
1. **Create v3 structure for all missing APIs**
2. **Copy functionality from existing versions**
3. **Ensure 100% feature parity**

### Phase 2: Update Backend Routing
1. **Update main.py to include all v3 routers**
2. **Ensure consistent `/api/v3/` prefixes**
3. **Test all endpoints**

### Phase 3: Update Frontend
1. **Remove all hardcoded version paths**
2. **Use clean paths like `/jobs/`, `/users/`, etc.**
3. **Update environment to use `/api/v3` base**

### Phase 4: Testing & Validation
1. **Test all frontend functionality**
2. **Verify no broken endpoints**
3. **Clean up old version dependencies**

## Target v3 API Structure

```
/api/v3/
├── auth/
│   ├── login
│   ├── logout
│   └── refresh
├── users/
│   ├── /
│   ├── {id}
│   ├── {id}/change-password
│   ├── {id}/activate
│   └── {id}/deactivate
├── targets/
│   ├── /
│   ├── {id}
│   ├── {id}/test
│   ├── bulk/test
│   ├── bulk/update
│   ├── statistics/overview
│   ├── health/check
│   ├── health/perform
│   ├── health-check-batch
│   └── types
├── jobs/
│   ├── / (already exists)
│   ├── {id} (already exists)
│   ├── {id}/execute (already exists)
│   ├── {id}/executions (already exists)
│   ├── safety/cleanup-stale
│   ├── safety/health
│   └── schedules
├── system/
│   ├── info
│   └── health/
│       ├── /
│       ├── application
│       ├── database
│       ├── system
│       └── volumes/prune
├── monitoring/
│   ├── netdata-info
│   └── system-metrics
├── celery/
│   ├── stats
│   ├── queues
│   ├── workers
│   ├── active-tasks
│   └── metrics/history
├── metrics/
│   ├── dashboard
│   ├── jobs/performance
│   ├── system/health
│   ├── trends/executions
│   └── reports/summary
└── audit/
    ├── event-types
    └── lookups/targets
```

## Implementation Priority

### High Priority (Core functionality)
1. Users API → v3
2. Targets API → v3  
3. Auth API → v3
4. System/Health APIs → v3

### Medium Priority (Monitoring)
1. Celery APIs → v3
2. Metrics APIs → v3
3. System monitoring → v3

### Low Priority (Additional features)
1. Audit APIs → v3
2. Job safety APIs → v3
3. Advanced monitoring → v3