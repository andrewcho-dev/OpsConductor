# OpsConductor Complete Architecture Inventory & Analysis

## 📊 **CURRENT STATE INVENTORY**

### **🟢 EXISTING & WORKING**

#### **Infrastructure Components**
- **✅ Docker Compose** - Complete multi-service orchestration
- **✅ Nginx** - Reverse proxy with SSL termination (80/443)
- **✅ PostgreSQL** - Multiple databases (main, auth, user)
- **✅ Redis** - Caching and session management
- **✅ Portainer** - Docker container management (port 9000)

#### **Working Services**
- **✅ Frontend (React)** - Container: `opsconductor-frontend:3000`
- **✅ Auth Service** - Container: `opsconductor-auth-service:8000` (Available in archive)
- **✅ User Service** - Container: `opsconductor-user-service:8000` (Available in archive)
- **✅ Backend (Legacy)** - Container: `opsconductor-backend:8000` (Monolithic, contains targets/jobs)
- **✅ Celery Worker** - Background task processing
- **✅ Scheduler** - Celery beat scheduler

#### **Databases**
- **✅ Main DB** - `opsconductor-postgres:5432` (legacy backend data)
- **✅ Auth DB** - `opsconductor-auth-postgres:5432` (authentication data)
- **✅ User DB** - `opsconductor-user-postgres:5432` (user management data)

---

### **🟡 PLANNED/PLACEHOLDER SERVICES (Empty Directories)**

- **🔄 services/targets-service/** - Universal target systems management
- **🔄 services/jobs-service/** - Job creation, scheduling & management
- **🔄 services/execution-service/** - Job execution engine
- **🔄 services/infrastructure/** - Core infrastructure utilities
- **🔄 services/shared/** - Shared libraries and utilities

---

### **📦 ARCHIVED SERVICES (Fully Implemented, Ready to Use)**

- **📦 archive/old-auth-service-20250821/** - Complete auth service
- **📦 archive/old-user-service-20250821/** - Complete user service
- **📦 archive/old-job-execution-service-20250821/** - Job execution engine
- **📦 archive/old-microservices-20250821/** - Complete microservice architecture

---

## 🏗️ **COMPLETE ARCHITECTURE DIAGRAM**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL ACCESS                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  Internet → Nginx (80/443) → SSL Termination → Load Balancer                       │
│             Container: opsconductor-nginx                                           │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           DOCKER NETWORK (Internal)                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │   FRONTEND      │    │  AUTH SERVICE   │    │  USER SERVICE   │                │
│  │    (React)      │    │   (FastAPI)     │    │   (FastAPI)     │                │
│  │ Port: 3000      │    │ Port: 8000      │    │ Port: 8000      │                │
│  │ Status: ✅       │    │ Status: ✅       │    │ Status: ✅       │                │
│  │                 │    │                 │    │                 │                │
│  │ opsconductor-   │    │ opsconductor-   │    │ opsconductor-   │                │
│  │ frontend        │    │ auth-service    │    │ user-service    │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│           │                       │                       │                        │
│           │              ┌─────────────────┐     ┌─────────────────┐              │
│           │              │   AUTH-DB       │     │   USER-DB       │              │
│           │              │ (PostgreSQL)    │     │ (PostgreSQL)    │              │
│           │              │ Port: 5432      │     │ Port: 5432      │              │
│           │              │ Volume: auth_   │     │ Volume: user_   │              │
│           │              │ postgres_data   │     │ postgres_data   │              │
│           │              └─────────────────┘     └─────────────────┘              │
│           │                                                                        │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │  BACKEND        │    │ TARGETS SERVICE │    │  JOBS SERVICE   │                │
│  │  (Legacy)       │    │   (Planned)     │    │   (Planned)     │                │
│  │ Port: 8000      │    │ Port: TBD       │    │ Port: TBD       │                │
│  │ Status: ✅       │    │ Status: 🔄       │    │ Status: 🔄       │                │
│  │ Contains:       │    │                 │    │                 │                │
│  │ - Targets API   │    │ Extract from    │    │ Extract from    │                │
│  │ - Jobs API      │    │ Backend ←       │    │ Backend ←       │                │
│  │ - Execution     │    │                 │    │                 │                │
│  │                 │    │                 │    │                 │                │
│  │ opsconductor-   │    │ opsconductor-   │    │ opsconductor-   │                │
│  │ backend         │    │ targets         │    │ jobs            │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│           │                       │                       │                        │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐              │
│  │   MAIN-DB       │     │  TARGETS-DB     │     │   JOBS-DB       │              │
│  │ (PostgreSQL)    │     │ (PostgreSQL)    │     │ (PostgreSQL)    │              │
│  │ Port: 5432      │     │ Port: TBD       │     │ Port: TBD       │              │
│  │ Volume:         │     │ Status: 🔄       │     │ Status: 🔄       │              │
│  │ postgres_data   │     │                 │     │                 │              │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘              │
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │ EXECUTION       │    │ CELERY WORKER   │    │   SCHEDULER     │                │
│  │   SERVICE       │    │  (Background)   │    │  (Celery Beat)  │                │
│  │  (Planned)      │    │ Port: N/A       │    │ Port: N/A       │                │
│  │ Port: TBD       │    │ Status: ✅       │    │ Status: ✅       │                │
│  │ Status: 🔄       │    │                 │    │                 │                │
│  │                 │    │ opsconductor-   │    │ opsconductor-   │                │
│  │ Extract from    │    │ celery-worker   │    │ scheduler       │                │
│  │ Backend ←       │    │                 │    │                 │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│           │                       │                       │                        │
│  ┌─────────────────┐                      ┌─────────────────┐                    │
│  │ EXECUTION-DB    │                      │     REDIS       │                    │
│  │ (PostgreSQL)    │                      │   (Cache)       │                    │
│  │ Port: TBD       │                      │ Port: 6379      │                    │
│  │ Status: 🔄       │                      │ Status: ✅       │                    │
│  │                 │                      │ Volume: N/A     │                    │
│  │                 │                      │ (In-memory)     │                    │
│  └─────────────────┘                      └─────────────────┘                    │
│                                                   │                               │
│  ┌─────────────────┐                                                             │
│  │   PORTAINER     │                                                             │
│  │ (Docker Mgmt)   │                                                             │
│  │ Port: 9000      │                                                             │
│  │ Status: ✅       │                                                             │
│  │ Volume:         │                                                             │
│  │ portainer_data  │                                                             │
│  └─────────────────┘                                                             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 **CONTAINER NAMING CONVENTIONS**

| Service | Container Name | Status | Port | Database |
|---------|----------------|--------|------|----------|
| **Frontend** | `opsconductor-frontend` | ✅ Working | 3000 | N/A |
| **Nginx** | `opsconductor-nginx` | ✅ Working | 80/443 | N/A |
| **Auth Service** | `opsconductor-auth-service` | ✅ Working | 8000 | `auth-postgres` |
| **User Service** | `opsconductor-user-service` | ✅ Working | 8000 | `user-postgres` |
| **Backend (Legacy)** | `opsconductor-backend` | ✅ Working | 8000 | `postgres` |
| **Targets Service** | `opsconductor-targets` | 🔄 Planned | TBD | TBD |
| **Jobs Service** | `opsconductor-jobs` | 🔄 Planned | TBD | TBD |
| **Execution Service** | `opsconductor-execution` | 🔄 Planned | TBD | TBD |
| **Celery Worker** | `opsconductor-celery-worker` | ✅ Working | N/A | N/A |
| **Scheduler** | `opsconductor-scheduler` | ✅ Working | N/A | N/A |
| **Redis** | `opsconductor-redis` | ✅ Working | 6379 | N/A |
| **Main DB** | `opsconductor-postgres` | ✅ Working | 5432 | N/A |
| **Auth DB** | `opsconductor-auth-postgres` | ✅ Working | 5432 | N/A |
| **User DB** | `opsconductor-user-postgres` | ✅ Working | 5432 | N/A |
| **Portainer** | `opsconductor-portainer` | ✅ Working | 9000 | N/A |

---

## 📦 **DOCKER VOLUMES**

| Volume Name | Purpose | Status |
|-------------|---------|--------|
| `postgres_data` | Main database storage | ✅ Active |
| `auth_postgres_data` | Auth database storage | ✅ Active |
| `user_postgres_data` | User database storage | ✅ Active |
| `portainer_data` | Portainer configuration | ✅ Active |

---

## 🌐 **NGINX ROUTING STRATEGY**

### **Current Routing (Working)**
```nginx
# External Users → Nginx → Services
/                    → frontend (React app)
/api/auth/          → auth-service 
/api/users/         → user-service
/api/config/        → auth-service (config endpoints)
/api/*              → backend (legacy - all other APIs)
/ws                 → backend (WebSocket)
/health             → nginx (health check)
```

### **Future Routing (Planned)**
```nginx
# When microservices are extracted
/api/targets/       → targets-service
/api/jobs/          → jobs-service  
/api/executions/    → execution-service
/api/schedules/     → scheduling-service (future)
/api/audit/         → audit-service (future)
```

---

## ⚡ **HTTP vs HTTPS INSIDE DOCKER**

### **🔥 RECOMMENDATION: HTTP INSIDE DOCKER NETWORK**

**✅ USE HTTP for Internal Service Communication:**

#### **Why HTTP is Perfect Inside Docker:**
1. **SSL Termination at Nginx** - Nginx handles all HTTPS/SSL certificates
2. **Internal Network Security** - Docker network is isolated and secure
3. **Performance** - No encryption/decryption overhead between services
4. **Simplicity** - No certificate management for internal services
5. **Industry Standard** - Netflix, Uber, Google use HTTP internally

#### **Security Model:**
```
Internet (HTTPS) → Nginx (SSL Termination) → Docker Network (HTTP)
```

#### **Configuration:**
```python
# Service-to-service calls (INTERNAL)
USER_SERVICE_URL = "http://user-service:8000"      # ✅ HTTP
AUTH_SERVICE_URL = "http://auth-service:8000"      # ✅ HTTP  
REDIS_URL = "redis://redis:6379"                   # ✅ No SSL

# External API calls (if needed)
EXTERNAL_API = "https://external-service.com"      # ✅ HTTPS
```

#### **HTTPS Only Needed For:**
- **External traffic** (Internet → Nginx)
- **External API calls** (Your services → Internet)
- **Database connections to external DBs** (if using cloud databases)

---

## 🚨 **CRITICAL ISSUES TO FIX**

### **1. HARDCODED LOCALHOST (CARDINAL RULE VIOLATION)**
```python
# CURRENT (BROKEN)
CORS_ORIGINS = ["http://localhost:3000", "https://localhost"]

# FIX TO
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
```

### **2. SERVICE EXTRACTION NEEDED**
- **Targets functionality** - Extract from `backend/app/api/v3/targets.py`
- **Jobs functionality** - Extract from `backend/app/api/v2/jobs.py`
- **Execution logic** - Extract from `backend/app/tasks/`

### **3. DATABASE CONSOLIDATION OPPORTUNITY**
- **Current**: 3 separate PostgreSQL instances
- **Option**: Single PostgreSQL with multiple databases
- **Trade-off**: Resource usage vs isolation

---

## 🎯 **RECOMMENDED NEXT STEPS**

### **Phase 1: Fix Cardinal Rule Violations (IMMEDIATE)**
1. Fix hardcoded localhost in all services
2. Ensure all URLs use container names
3. Test service communication

### **Phase 2: Extract Microservices (PRIORITY)**
1. **Targets Service** - Extract from backend
2. **Jobs Service** - Extract from backend  
3. **Execution Service** - Extract from backend

### **Phase 3: Optimize Architecture**
1. Consider database consolidation
2. Add monitoring/metrics
3. Add API gateway features
4. Add service mesh (if needed)

---

## ❓ **QUESTIONS FOR YOU**

1. **Database Strategy**: Keep 3 separate PostgreSQL instances or consolidate?

2. **Service Extraction**: Start with Targets Service extraction from backend?

3. **CORS Origins**: What should be the actual CORS origins for your environment?

4. **Missing Services**: Do we need notification service, audit service, scheduling service?

5. **Container Naming**: Are the current naming conventions good?

**This architecture is actually very solid - just needs the microservice extraction and Docker compliance fixes!**

---

## 🚀 **THE BEAUTY OF THIS ARCHITECTURE**

- **✅ No IP address management** - All container names
- **✅ SSL termination at edge** - HTTP internally  
- **✅ Service isolation** - Each service has own database
- **✅ Scalable** - Add more containers easily
- **✅ Portable** - Works anywhere Docker runs
- **✅ Secure** - Network isolation + SSL at edge
- **✅ Maintainable** - Clean service boundaries

**Ready to proceed with Phase 1: Fix cardinal rule violations?**