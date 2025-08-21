# OpsConductor Microservices Master Plan

## 🏗️ CURRENT STATE ANALYSIS

### Existing Monolithic Backend
**Location**: `/home/enabledrm/backend/`
- **Single FastAPI Application** - Handles everything
- **API Endpoints**: 14 API modules
  - `analytics.py` - Analytics and reporting
  - `audit.py` - Audit trails and compliance
  - `celery.py` - Task monitoring
  - `data_export.py` - Data export functionality  
  - `device_types.py` - Device type management
  - `discovery.py` - Network discovery
  - `docker.py` - Container management
  - `jobs_simple.py` - Job execution
  - `metrics.py` - System metrics
  - `notifications.py` - Notification system
  - `schedules.py` - Job scheduling
  - `system.py` - System health
  - `targets.py` - Universal targets
  - `websocket.py` - Real-time communications

### Database Structure
- **Single PostgreSQL**: All data in one database
- **Models**: 9 model files (analytics, celery, device_type, discovery, job, job_schedule, notification, system, universal_target)
- **Database Init Scripts**: 8 SQL files in `/database/init/`

### Current Infrastructure
- **PostgreSQL 15** - Single database
- **Redis 7** - Caching and sessions  
- **Nginx** - Reverse proxy and SSL
- **React Frontend** - Single page application
- **Celery** - Task queue and scheduling

---

## 🎯 TARGET MICROSERVICES ARCHITECTURE

### 1. Infrastructure Services (4 containers)
```
infrastructure/
├── postgres/          # PostgreSQL 15 - Port 5432
├── redis/             # Redis 7 - Port 6379  
├── rabbitmq/          # RabbitMQ 3 - Port 5672
└── api-gateway/       # Nginx - Port 80/443
```

### 2. Core Business Services (8 containers)

#### Auth Service
- **Port**: 8001
- **Database**: auth_db (PostgreSQL)
- **Responsibility**: JWT tokens, authentication, login/logout
- **Extracted From**: `backend/app/core/auth_dependencies.py`

#### User Management Service  
- **Port**: 8002
- **Database**: user_db (PostgreSQL)
- **Responsibility**: User CRUD, profiles, roles, permissions
- **Extracted From**: User-related functionality (needs to be identified)

#### Universal Targets Service
- **Port**: 8003  
- **Database**: targets_db (PostgreSQL)
- **Responsibility**: Target systems, connections, device types
- **Extracted From**: `targets.py`, `device_types.py`, `universal_target_models.py`

#### Job Management Service
- **Port**: 8004
- **Database**: jobs_db (PostgreSQL) 
- **Responsibility**: Job creation, scheduling, templates
- **Extracted From**: `jobs_simple.py`, `schedules.py`, `templates.py`, `job_models.py`

#### Job Execution Service
- **Port**: 8005
- **Database**: executions_db (PostgreSQL)
- **Responsibility**: Job execution engine, Celery tasks
- **Extracted From**: `celery.py`, Celery tasks, execution logic

#### Discovery Service
- **Port**: 8006
- **Database**: discovery_db (PostgreSQL)
- **Responsibility**: Network discovery, device scanning
- **Extracted From**: `discovery.py`, `discovery_models.py`

#### Analytics Service  
- **Port**: 8007
- **Database**: analytics_db (PostgreSQL)
- **Responsibility**: Reporting, metrics, data export
- **Extracted From**: `analytics.py`, `metrics.py`, `data_export.py`

#### System Management Service
- **Port**: 8008  
- **Database**: system_db (PostgreSQL)
- **Responsibility**: System health, Docker management, monitoring
- **Extracted From**: `system.py`, `docker.py`, health monitoring

### 3. Supporting Services (3 containers)

#### Audit Service
- **Port**: 8009
- **Database**: audit_db (PostgreSQL)
- **Responsibility**: Audit trails, compliance, logging
- **Extracted From**: `audit.py`, audit middleware

#### Notification Service
- **Port**: 8010
- **Database**: notifications_db (PostgreSQL) 
- **Responsibility**: Notifications, alerts, messaging
- **Extracted From**: `notifications.py`, `notification_models.py`

#### Frontend Service
- **Port**: 3000
- **Static Files**: React build
- **Responsibility**: User interface, served by Nginx
- **Source**: `/home/enabledrm/frontend/`

---

## 📊 CONTAINER BREAKDOWN

### Total Containers: 15

#### Infrastructure (4)
1. **postgres-main** - Primary PostgreSQL instance
2. **redis** - Caching and sessions
3. **rabbitmq** - Message broker for async communication  
4. **api-gateway** - Nginx reverse proxy

#### Microservices (8)  
5. **auth-service** - Authentication
6. **user-service** - User management
7. **targets-service** - Universal targets  
8. **jobs-service** - Job management
9. **execution-service** - Job execution
10. **discovery-service** - Network discovery
11. **analytics-service** - Analytics and reporting
12. **system-service** - System management

#### Supporting (3)
13. **audit-service** - Audit and compliance
14. **notification-service** - Notifications  
15. **frontend** - React UI

---

## 🗄️ DATABASE BREAKDOWN

### Single to Multi-Database Migration

#### Current: 1 Database
- `opsconductor` - All tables

#### Target: 9 Databases  
1. **auth_db** - User credentials, sessions, tokens
2. **user_db** - User profiles, roles, permissions
3. **targets_db** - Targets, devices, connections  
4. **jobs_db** - Job definitions, schedules, templates
5. **executions_db** - Job executions, results, logs
6. **discovery_db** - Discovery scans, found devices
7. **analytics_db** - Metrics, reports, analytics data
8. **system_db** - System health, Docker stats
9. **audit_db** - Audit trails, compliance logs
10. **notifications_db** - Notifications, alerts

---

## 🔌 PORT ALLOCATION

### Infrastructure
- **5432** - PostgreSQL
- **6379** - Redis  
- **5672** - RabbitMQ
- **80/443** - Nginx API Gateway

### Microservices  
- **8001** - Auth Service
- **8002** - User Management Service
- **8003** - Universal Targets Service
- **8004** - Job Management Service
- **8005** - Job Execution Service
- **8006** - Discovery Service
- **8007** - Analytics Service  
- **8008** - System Management Service
- **8009** - Audit Service
- **8010** - Notification Service
- **3000** - Frontend Service

---

## 🚀 BUILD STRATEGY

### Phase 1: Infrastructure Setup
1. Set up PostgreSQL with multiple databases
2. Configure Redis  
3. Set up RabbitMQ
4. Configure API Gateway with routing

### Phase 2: Core Services (Sequential)
1. **Auth Service** - Foundation for all others
2. **User Management** - Depends on Auth  
3. **Universal Targets** - Independent
4. **Job Management** - Independent
5. **Job Execution** - Depends on Jobs + Targets

### Phase 3: Supporting Services
1. **Discovery Service** - Depends on Targets
2. **Analytics Service** - Depends on multiple sources
3. **System Management** - Independent
4. **Audit Service** - Cross-cutting concern
5. **Notification Service** - Cross-cutting concern

### Phase 4: Frontend Integration
1. **Frontend Service** - Integrate with all APIs
2. **End-to-End Testing** - Full system validation

---

## 📋 EXTRACTION PLAN

### Files to Extract from `/backend/app/`:

#### Auth Service
- `core/auth_dependencies.py`
- JWT-related utilities
- Authentication middleware

#### Universal Targets Service  
- `api/v3/targets.py`
- `api/v3/device_types.py`
- `models/universal_target_models.py`
- `models/device_type_models.py`
- Target-related services

#### Job Management Service
- `api/v3/jobs_simple.py`  
- `api/v3/schedules.py`
- `api/v3/templates.py`
- `models/job_models.py`
- `models/job_schedule_models.py`
- Job-related services

#### Job Execution Service
- `api/v3/celery.py`
- `tasks/` directory (all Celery tasks)
- `celery.py` (Celery app config)
- Execution-related services

#### And so on for each service...

---

## ⚠️ MIGRATION CONSIDERATIONS

### Data Migration
- **Database Schema Split** - Tables need to be moved to appropriate databases
- **Foreign Key Relationships** - Need to become API calls
- **Data Consistency** - Ensure referential integrity across services

### Code Dependencies  
- **Shared Models** - Move to shared library
- **Cross-Service Communication** - Replace direct imports with HTTP/RabbitMQ calls
- **Authentication** - Each service validates tokens with Auth Service

### Testing Strategy
- **Service-Level Tests** - Each service independently testable  
- **Integration Tests** - Cross-service communication
- **End-to-End Tests** - Full workflow validation

---

**Next Steps**: Do you want me to proceed with this plan? Should I adjust anything before we start the extraction process?