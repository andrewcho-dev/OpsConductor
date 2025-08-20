# CENTRALIZED LOGGING IMPLEMENTATION REQUEST

## 🎯 **OBJECTIVE**
Implement centralized logging for OpsConductor microservices platform using Loki + Grafana stack, following proper microservices architecture principles.

## 📋 **CURRENT SITUATION**

### **Platform Architecture:**
- **OpsConductor**: Universal automation orchestration platform
- **Architecture**: Microservices-based with Docker Compose
- **Location**: `/home/enabledrm/` (use absolute paths)
- **Services**: Auth service, Backend, Frontend, PostgreSQL, Redis, Nginx
- **Monitoring**: Existing Prometheus + Grafana (ports 9090, 3001)

### **Current Logging Problems:**
- ✅ **Auth service** (opsconductor-auth-service) IS generating logs
- ❌ **Logs are ephemeral** - stored only in Docker containers, lost on restart
- ❌ **No centralized collection** - can't search across services
- ❌ **No persistence** - no historical log analysis
- ❌ **No correlation** - can't trace requests across auth → backend → frontend

### **Current Log Locations:**
```
Docker Containers (Ephemeral):
├── opsconductor-auth-service → Container logs (session mgmt, auth events)
├── opsconductor-backend → Container logs (API requests, job execution)
└── opsconductor-frontend → Container logs (UI events, errors)

Host Filesystem (Limited):
├── /home/enabledrm/logs/error.log → Backend errors only
└── /home/enabledrm/logs/monitor.log → System monitoring
```

### **Existing Infrastructure:**
```yaml
# Already running in docker-compose.yml:
prometheus:    # Port 9090 - metrics collection
grafana:       # Port 3001 - dashboards (has Prometheus datasource)
auth-service:  # Port 8001 - microservice with own database
backend:       # Port 8000 - main API service
frontend:      # Port 3000 - React UI
postgres:      # Main database
redis:         # Cache
nginx:         # Reverse proxy
```

## 🏗️ **REQUIRED IMPLEMENTATION**

### **Architecture Goal:**
Implement **true microservices separation** where observability services are separated from business services:

```
BUSINESS SERVICES:           OBSERVABILITY SERVICES:
├── auth-service            ├── prometheus (existing)
├── backend                 ├── grafana (existing) 
├── frontend                ├── loki (NEW)
├── postgres                └── promtail (NEW)
├── redis
└── nginx
```

### **Technical Requirements:**

1. **Add Loki Stack:**
   - **Loki container**: Log storage and indexing (port 3100)
   - **Promtail container**: Log collection from ALL containers
   - **Enhanced Grafana**: Add Loki as datasource to existing Grafana

2. **Log Collection Strategy:**
   - Promtail mounts `/var/lib/docker/containers` to collect ALL container logs
   - Automatic service discovery via Docker labels
   - Proper labeling for service identification

3. **Integration Requirements:**
   - **Zero downtime**: Add alongside existing services
   - **Preserve existing**: Keep current Prometheus/Grafana setup intact
   - **Microservices compliant**: Separate observability from business logic

## 📁 **FILE STRUCTURE CONTEXT**

The repository structure is:
```
/home/enabledrm/
├── docker-compose.yml           # Main services (modify this)
├── auth-service/               # Microservice with own DB
├── backend/                    # Main API service  
├── frontend/                   # React UI
├── monitoring/                 # Prometheus/Grafana configs
│   ├── prometheus.yml
│   └── grafana/
├── logs/                       # Current limited logging
└── [other directories...]
```

## 🔧 **IMPLEMENTATION TASKS**

### **Task 1: Add Loki Services to docker-compose.yml**
Add these services to the existing docker-compose.yml:
- Loki container with proper configuration
- Promtail container with Docker socket access
- Proper networking and dependencies

### **Task 2: Create Configuration Files**
Create in `/home/enabledrm/logging/`:
- `loki-config.yml` - Loki storage and retention settings
- `promtail-config.yml` - Log collection and labeling rules

### **Task 3: Enhance Existing Services**
Add logging labels to existing services for Promtail discovery:
- auth-service, backend, frontend, postgres, redis, nginx

### **Task 4: Grafana Integration**
- Add Loki datasource configuration
- Create log dashboard templates
- Set up log-based alerting

### **Task 5: Verification**
- Test log collection from all services
- Verify cross-service log correlation
- Confirm log persistence across container restarts

## 🎯 **EXPECTED OUTCOMES**

After implementation, we should be able to:

1. **Search across all services:**
   ```
   {service="auth-service"} |= "failed login"
   {service=~"auth-service|backend"} |= "user_id=123"
   ```

2. **Trace requests across microservices:**
   - Auth service login → Backend API calls → Frontend updates

3. **Historical analysis:**
   - Persistent logs with configurable retention
   - Performance trending and debugging

4. **Real-time monitoring:**
   - Live log streams in Grafana
   - Alerting on error patterns

## 🚨 **CRITICAL REQUIREMENTS**

- **Use absolute paths**: Always use `/home/enabledrm/` as root
- **Preserve existing**: Don't break current Prometheus/Grafana setup
- **Microservices architecture**: Keep observability separate from business logic
- **Zero downtime**: Implementation should not disrupt running services
- **Docker Compose**: Extend existing docker-compose.yml, don't replace

## 📊 **SUCCESS CRITERIA**

1. ✅ All container logs collected and searchable in Grafana
2. ✅ Auth service logs persistent across restarts  
3. ✅ Cross-service log correlation working
4. ✅ Existing Prometheus/Grafana functionality unchanged
5. ✅ Proper microservices separation maintained
6. ✅ Log retention and rotation configured

## 🔍 **CONTEXT FOR DEBUGGING**

Current auth service is generating logs like:
```
2025-08-20 20:44:52,732 - app.core.session_manager - INFO - Session 11_1755721797 activity updated
INFO: 172.18.0.2:41270 - "POST /api/auth/session/extend HTTP/1.1" 200 OK
```

These logs are currently only visible via `docker logs opsconductor-auth-service` and are lost on container restart.

---

**Please implement this centralized logging solution following microservices best practices.**