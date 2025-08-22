# 🏗️ OpsConductor - Complete Microservices Architecture Diagram

## 📊 **System Architecture Overview**

```mermaid
graph TB
    %% =============================================================================
    %% EXTERNAL ACCESS LAYER
    %% =============================================================================
    subgraph "🌐 External Access Layer"
        BROWSER[🖥️ Web Browser<br/>HTTPS Client]
        API_CLIENT[📱 API Client<br/>REST/HTTP]
    end

    %% =============================================================================
    %% FRONTEND & API GATEWAY LAYER  
    %% =============================================================================
    subgraph "🚀 Frontend & Gateway Layer"
        NGINX[🌐 Nginx API Gateway<br/>📍 Ports: 80, 443<br/>🔐 SSL Termination<br/>📦 nginx:alpine]
        FRONTEND[⚛️ React Frontend<br/>📍 Port: 3000<br/>📦 Node.js 18<br/>🎨 Material-UI<br/>📊 Redux Toolkit]
    end

    %% =============================================================================
    %% MICROSERVICES LAYER
    %% =============================================================================
    subgraph "🔧 Core Microservices Layer"
        AUTH_SERVICE[🔐 Auth Service<br/>📍 Port: 8000<br/>📦 FastAPI<br/>🔑 JWT Authentication<br/>📋 User Login/Logout]
        
        USER_SERVICE[👥 User Service<br/>📍 Port: 8000<br/>📦 FastAPI<br/>👤 User Management<br/>📋 CRUD Operations]
        
        TARGETS_SERVICE[🎯 Targets Service<br/>📍 Port: 8000<br/>📦 FastAPI<br/>🖥️ Target Management<br/>📡 Health Monitoring]
        
        JOBS_SERVICE[⚙️ Jobs Service<br/>📍 Port: 8000<br/>📦 FastAPI<br/>📝 Job Definitions<br/>🔄 Job Lifecycle]
        
        AUDIT_SERVICE[📋 Audit Events Service<br/>📍 Port: 8000<br/>📦 FastAPI<br/>📊 Compliance Logging<br/>🔍 Event Tracking]
        
        DISCOVERY_SERVICE[🔍 Target Discovery Service<br/>📍 Port: 8000<br/>📦 FastAPI<br/>🌐 Network Scanning<br/>📡 Auto Discovery]
        
        NOTIFICATION_SERVICE[📨 Notification Service<br/>📍 Port: 8000<br/>📦 FastAPI<br/>📧 Email Alerts<br/>🔔 Event Notifications]
    end

    %% =============================================================================
    %% EXECUTION & WORKERS LAYER
    %% =============================================================================
    subgraph "🚀 Distributed Execution Layer"
        EXECUTION_SERVICE[⚡ Execution Service<br/>📍 Port: 8000<br/>📦 FastAPI<br/>🎯 Job Orchestration]
        
        subgraph "👷 Distributed Workers"
            EXEC_WORKER[🔨 Execution Worker<br/>📦 Celery<br/>⚡ Job Execution<br/>🎯 Target Operations<br/>💻 Container Management]
            
            SYS_WORKER[🛠️ System Worker<br/>📦 Celery<br/>🧹 Maintenance Tasks<br/>🔍 Discovery Jobs<br/>📊 Health Checks]
            
            SYS_SCHEDULER[⏰ System Scheduler<br/>📦 Celery Beat<br/>📅 Periodic Tasks<br/>⏱️ Cron Jobs]
        end
        
        NODE_RED[🔴 Node-RED<br/>📍 Port: 1880<br/>📦 Node.js<br/>🔄 Visual Workflows<br/>🌊 Data Integration]
    end

    %% =============================================================================
    %% DATABASE LAYER
    %% =============================================================================
    subgraph "🗄️ Database Layer (Per-Service Isolation)"
        MAIN_POSTGRES[🗄️ Main PostgreSQL<br/>📍 Port: 5432<br/>📦 postgres:15-alpine<br/>📊 Shared Tables]
        
        AUTH_DB[🔐 Auth Database<br/>📍 Port: 5432<br/>📦 postgres:15-alpine<br/>👤 User Credentials<br/>🔑 Sessions]
        
        USER_DB[👥 User Database<br/>📍 Port: 5432<br/>📦 postgres:15-alpine<br/>👤 User Profiles<br/>📋 User Data]
        
        TARGETS_DB[🎯 Targets Database<br/>📍 Port: 5432<br/>📦 postgres:15-alpine<br/>🖥️ Target Configs<br/>📊 Health Status]
        
        JOBS_DB[⚙️ Jobs Database<br/>📍 Port: 5432<br/>📦 postgres:15-alpine<br/>📝 Job Definitions<br/>📊 Job History]
        
        EXEC_DB[🚀 Execution Database<br/>📍 Port: 5433 (External)<br/>📦 postgres:15-alpine<br/>🔄 Task Queue<br/>📊 Execution Logs]
        
        AUDIT_DB[📋 Audit Database<br/>📍 Port: 5432<br/>📦 postgres:15-alpine<br/>📊 Event Logs<br/>🔍 Compliance Data]
        
        NOTIFICATION_DB[📨 Notification Database<br/>📍 Port: 5432<br/>📦 postgres:15-alpine<br/>📧 Message Queue<br/>📨 Delivery Status]
    end

    %% =============================================================================
    %% CACHE & MESSAGING LAYER
    %% =============================================================================
    subgraph "📦 Cache & Messaging Layer"
        MAIN_REDIS[📦 Main Redis<br/>📍 Port: 6379<br/>📦 redis:7-alpine<br/>🔄 Session Cache<br/>⚡ API Cache]
        
        EXEC_REDIS[📦 Execution Redis<br/>📍 Port: 6379 (External)<br/>📦 redis:7-alpine<br/>🔄 Task Queue<br/>📊 Worker Communication]
    end

    %% =============================================================================
    %% STORAGE & MANAGEMENT LAYER
    %% =============================================================================
    subgraph "💾 Storage & Management Layer"
        MINIO[📦 MinIO Object Storage<br/>📍 S3 API: 9001<br/>📍 Console: 9090<br/>📦 minio/minio<br/>📁 Job Artifacts<br/>🗃️ File Storage]
        
        PORTAINER[🐳 Portainer<br/>📍 Port: 9000<br/>📦 portainer/portainer-ce<br/>🔧 Container Management<br/>📊 Docker Monitoring]
    end

    %% =============================================================================
    %% PERSISTENT VOLUMES
    %% =============================================================================
    subgraph "💽 Persistent Volumes"
        VOL_POSTGRES[📀 postgres_data]
        VOL_AUTH[📀 auth_postgres_data]
        VOL_USER[📀 user_postgres_data]
        VOL_TARGETS[📀 targets_postgres_data]
        VOL_JOBS[📀 jobs_postgres_data]
        VOL_EXEC[📀 execution_postgres_data]
        VOL_AUDIT[📀 audit_postgres_data]
        VOL_NOTIFICATION[📀 notification_postgres_data]
        VOL_MINIO[📀 minio_data]
        VOL_PORTAINER[📀 portainer_data]
        VOL_REDIS[📀 redis_data]
    end

    %% =============================================================================
    %% NETWORK LAYER
    %% =============================================================================
    subgraph "🌐 Network Layer"
        NETWORK[🔗 opsconductor-network<br/>📡 Docker Bridge Network<br/>🔒 Internal Communication]
    end

    %% =============================================================================
    %% CONNECTION FLOWS
    %% =============================================================================
    
    %% External to Gateway
    BROWSER -->|HTTPS:443<br/>HTTP:80| NGINX
    API_CLIENT -->|REST API| NGINX
    
    %% Gateway to Frontend
    NGINX -->|Proxy Pass<br/>Port: 3000| FRONTEND
    
    %% Gateway to Microservices
    NGINX -.->|/api/v1/auth/*<br/>Port: 8000| AUTH_SERVICE
    NGINX -.->|/api/v1/users/*<br/>Port: 8000| USER_SERVICE  
    NGINX -.->|/api/v1/targets/*<br/>Port: 8000| TARGETS_SERVICE
    NGINX -.->|/api/v1/jobs/*<br/>Port: 8000| JOBS_SERVICE
    NGINX -.->|/api/v1/audit/*<br/>Port: 8000| AUDIT_SERVICE
    NGINX -.->|/api/v1/discovery/*<br/>Port: 8000| DISCOVERY_SERVICE
    NGINX -.->|/api/v1/notifications/*<br/>Port: 8000| NOTIFICATION_SERVICE
    NGINX -.->|/api/v1/execution/*<br/>Port: 8000| EXECUTION_SERVICE

    %% Microservices to Databases
    AUTH_SERVICE === AUTH_DB
    USER_SERVICE === USER_DB
    TARGETS_SERVICE === TARGETS_DB
    JOBS_SERVICE === JOBS_DB
    EXECUTION_SERVICE === EXEC_DB
    AUDIT_SERVICE === AUDIT_DB
    NOTIFICATION_SERVICE === NOTIFICATION_DB
    
    %% Services to Cache
    AUTH_SERVICE -.-> MAIN_REDIS
    USER_SERVICE -.-> MAIN_REDIS
    TARGETS_SERVICE -.-> MAIN_REDIS
    
    %% Execution Layer Connections
    EXECUTION_SERVICE --> EXEC_WORKER
    EXECUTION_SERVICE --> SYS_WORKER
    EXECUTION_SERVICE --> SYS_SCHEDULER
    EXECUTION_SERVICE --> NODE_RED
    
    EXEC_WORKER -.-> EXEC_REDIS
    SYS_WORKER -.-> EXEC_REDIS
    SYS_SCHEDULER -.-> EXEC_REDIS
    
    %% Inter-Service Communication
    JOBS_SERVICE -.->|Job Triggers| EXECUTION_SERVICE
    TARGETS_SERVICE -.->|Target Data| EXECUTION_SERVICE
    EXECUTION_SERVICE -.->|Events| AUDIT_SERVICE
    EXECUTION_SERVICE -.->|Alerts| NOTIFICATION_SERVICE
    DISCOVERY_SERVICE -.->|Discovered Targets| TARGETS_SERVICE
    
    %% Storage Connections
    EXECUTION_SERVICE -.->|Artifacts| MINIO
    AUDIT_SERVICE -.->|Log Files| MINIO
    
    %% Database Volume Connections
    MAIN_POSTGRES --- VOL_POSTGRES
    AUTH_DB --- VOL_AUTH
    USER_DB --- VOL_USER
    TARGETS_DB --- VOL_TARGETS
    JOBS_DB --- VOL_JOBS
    EXEC_DB --- VOL_EXEC
    AUDIT_DB --- VOL_AUDIT
    NOTIFICATION_DB --- VOL_NOTIFICATION
    MINIO --- VOL_MINIO
    PORTAINER --- VOL_PORTAINER
    EXEC_REDIS --- VOL_REDIS

    %% Styling
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef gateway fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef microservice fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef database fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef cache fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef worker fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef volume fill:#f5f5f5,stroke:#424242,stroke-width:1px
    classDef network fill:#e0f2f1,stroke:#00695c,stroke-width:2px

    class BROWSER,API_CLIENT frontend
    class NGINX,FRONTEND gateway
    class AUTH_SERVICE,USER_SERVICE,TARGETS_SERVICE,JOBS_SERVICE,AUDIT_SERVICE,DISCOVERY_SERVICE,NOTIFICATION_SERVICE,EXECUTION_SERVICE microservice
    class MAIN_POSTGRES,AUTH_DB,USER_DB,TARGETS_DB,JOBS_DB,EXEC_DB,AUDIT_DB,NOTIFICATION_DB database
    class MAIN_REDIS,EXEC_REDIS cache
    class EXEC_WORKER,SYS_WORKER,SYS_SCHEDULER,NODE_RED worker
    class MINIO,PORTAINER storage
    class VOL_POSTGRES,VOL_AUTH,VOL_USER,VOL_TARGETS,VOL_JOBS,VOL_EXEC,VOL_AUDIT,VOL_NOTIFICATION,VOL_MINIO,VOL_PORTAINER,VOL_REDIS volume
    class NETWORK network
```

## 📊 **Port Summary Table**

| Component | Internal Port | External Port | Protocol | Purpose |
|-----------|---------------|---------------|----------|---------|
| **🌐 Nginx Gateway** | 80, 443 | 80, 443 | HTTP/HTTPS | SSL Termination, Routing |
| **⚛️ React Frontend** | 3000 | 3000 | HTTP | Single Page Application |
| **🔐 Auth Service** | 8000 | - | HTTP | JWT Authentication |
| **👥 User Service** | 8000 | - | HTTP | User Management |
| **🎯 Targets Service** | 8000 | - | HTTP | Target Management |
| **⚙️ Jobs Service** | 8000 | - | HTTP | Job Definitions |
| **⚡ Execution Service** | 8000 | - | HTTP | Job Orchestration |
| **📋 Audit Service** | 8000 | - | HTTP | Event Logging |
| **🔍 Discovery Service** | 8000 | - | HTTP | Network Discovery |
| **📨 Notification Service** | 8000 | - | HTTP | Alert Management |
| **🗄️ PostgreSQL DBs** | 5432 | - | TCP | Database Access |
| **🚀 Execution DB** | 5432 | 5433 | TCP | Worker Database |
| **📦 Redis Cache** | 6379 | - | TCP | Caching/Sessions |
| **📦 Execution Redis** | 6379 | 6379 | TCP | Task Queue |
| **📦 MinIO S3 API** | 9000 | 9001 | HTTP | Object Storage API |
| **📦 MinIO Console** | 9090 | 9090 | HTTP | Web Management |
| **🐳 Portainer** | 9000 | 9000 | HTTP | Container Management |
| **🔴 Node-RED** | 1880 | 1880 | HTTP | Visual Workflows |

## 🔄 **Service Communication Patterns**

### **🌐 Frontend → Gateway → Microservices**
- Browser/API clients connect via HTTPS (443) to Nginx
- Nginx routes `/api/v1/*` paths to appropriate microservices
- All microservices run on internal port 8000

### **⚡ Job Execution Flow**
1. **Frontend** → Job creation via **Jobs Service**
2. **Jobs Service** → Triggers **Execution Service**  
3. **Execution Service** → Dispatches to **Workers** via Redis queue
4. **Workers** → Execute on targets, log to **Audit Service**
5. **Workers** → Store artifacts in **MinIO**, send alerts via **Notification Service**

### **🔍 Discovery Flow**
1. **Discovery Service** → Scans networks periodically
2. **Discovery Service** → Registers found targets in **Targets Service**
3. **Targets Service** → Updates health status continuously

### **📊 Data Persistence**
- Each microservice has dedicated PostgreSQL database
- Execution workers share dedicated database and Redis
- All databases persist data via Docker volumes
- MinIO provides S3-compatible object storage for files

## 🛡️ **Security & Isolation**

- **🔐 Authentication**: Centralized via Auth Service with JWT tokens
- **🌐 Network Isolation**: All internal communication via Docker bridge network
- **🗄️ Database Isolation**: Per-service databases prevent data leakage
- **📦 Container Security**: Services run as non-root users where possible
- **🔐 SSL Termination**: HTTPS enforced at gateway level

## 📈 **Scalability Features**

- **📊 Horizontal Scaling**: Individual microservice scaling
- **👷 Distributed Workers**: Multiple execution workers for parallel processing  
- **📦 Caching Strategy**: Redis caching for frequently accessed data
- **🗄️ Database Optimization**: Dedicated databases prevent bottlenecks
- **📁 Object Storage**: MinIO for scalable file storage

---

**💡 This architecture provides a modern, scalable, and maintainable platform for universal automation orchestration with clear separation of concerns and robust operational capabilities.**