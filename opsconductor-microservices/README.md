# OpsConductor Microservices Architecture

## 🏗️ Architecture Overview

This directory contains the complete microservices architecture for OpsConductor, transforming the platform from a monolithic structure to independent, scalable services.

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Auth Service  │  │  User Service   │  │ Universal Targets│  │ Job Management  │
│   ✅ EXISTING   │  │   ✅ EXISTING   │  │  🔄 EXTRACT     │  │  🔄 CREATE     │
│   Port: 3000    │  │   Port: 3002    │  │   Port: 3001    │  │   Port: 8001    │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Job Execution   │  │ Job Scheduling  │  │ Audit & Events  │  │   Frontend      │
│  🔄 CREATE     │  │  🔄 CREATE     │  │  🔄 CREATE     │  │   ✅ EXISTING   │
│   Port: 8002    │  │   Port: 8003    │  │   Port: 8004    │  │   Port: 3001    │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 📋 Service Status

### ✅ **Existing Services (Working)**
- **Auth Service** (Port 3000) - JWT authentication, token management
- **User Service** (Port 3002) - User management, profiles, permissions  
- **Frontend** (Port 3001) - React application with Material-UI

### 🔄 **Services in Development**
- **Universal Targets Service** (Port 3001) - Target management, connection methods
- **Job Management Service** (Port 8001) - Job definitions, lifecycle, validation
- **Job Execution Service** (Port 8002) - Job execution engine, SSH/WinRM connections
- **Job Scheduling Service** (Port 8003) - Cron scheduling, recurring jobs
- **Audit & Events Service** (Port 8004) - Event logging, audit trails, monitoring

## 🗄️ Database Architecture

| Service | Database | Port | Status |
|---------|----------|------|--------|
| Auth Service | `auth_db` | 5433 | ✅ Working |
| User Service | `user_db` | 5434 | ✅ Working |
| Universal Targets | `targets_db` | 5435 | 🔄 To Create |
| Job Management | `job_management` | 5432 | 🔄 To Create |
| Job Execution | `job_execution` | 5436 | 🔄 To Create |
| Job Scheduling | `job_scheduling` | 5437 | 🔄 To Create |
| Audit & Events | `audit_events` | 5438 | 🔄 To Create |

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend services)

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 2. Start Infrastructure Services
```bash
# Start databases, Redis, and RabbitMQ
docker-compose up -d auth-postgres user-postgres targets-postgres redis rabbitmq

# Wait for services to be healthy
docker-compose ps
```

### 3. Start Existing Services
```bash
# Start auth, user, and frontend services
docker-compose up -d auth-service user-service frontend
```

### 4. Start New Microservices (When Ready)
```bash
# Start job-related services
docker-compose up -d job-management-service job-execution-service job-scheduling-service audit-events-service

# Start API Gateway
docker-compose up -d api-gateway
```

### 5. Access Services
- **Frontend**: http://localhost:3001
- **Auth Service**: http://localhost:3000
- **User Service**: http://localhost:3002
- **API Gateway**: http://localhost:8080
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 🔧 Development Workflow

### Current Phase: Infrastructure & Shared Libraries ✅
- [x] Shared libraries with auth/user integration
- [x] Updated docker-compose with all services
- [x] Database infrastructure for all services
- [x] RabbitMQ setup with event routing

### Next Phase: Extract Universal Targets Service
```bash
# Extract targets functionality from legacy backend
cd /home/enabledrm/opsconductor-microservices
# TODO: Create universal-targets-service directory
# TODO: Extract from /home/enabledrm/backend/app/api/v3/targets.py
```

## 🔍 Service Integration

### Authentication Flow
1. Frontend → Auth Service (JWT tokens)
2. All services validate tokens via Auth Service
3. User context passed between services

### Service Communication
- **Synchronous**: HTTP REST APIs between services
- **Asynchronous**: RabbitMQ events for decoupled operations
- **Caching**: Redis for session management and performance

### Event-Driven Architecture
```
┌─────────────┐    Events    ┌─────────────┐    Events    ┌─────────────┐
│   Service   │ ──────────→  │  RabbitMQ   │ ──────────→  │   Service   │
│      A      │              │   Broker    │              │      B      │
└─────────────┘              └─────────────┘              └─────────────┘
```

## 📊 Monitoring & Health Checks

### Health Check Endpoints
- All services expose `/health` endpoint
- Docker health checks configured
- Service dependency management

### Logging Strategy
- Structured logging with correlation IDs
- Centralized log aggregation (future: ELK stack)
- Event tracking across service boundaries

## 🔒 Security

### Authentication & Authorization
- JWT tokens for all API calls
- Service-to-service authentication
- Role-based access control (RBAC)
- Permission validation at service level

### Network Security
- Internal Docker network isolation
- API Gateway as single entry point
- SSL/TLS termination at gateway

## 🎯 Development Roadmap

### Week 1: Infrastructure ✅
- [x] Shared libraries
- [x] Docker compose updates
- [x] Database setup
- [x] RabbitMQ configuration

### Week 2: Universal Targets Service
- [ ] Extract from legacy backend
- [ ] Independent database
- [ ] API migration
- [ ] Frontend integration

### Week 3: Job Management Service
- [ ] Job CRUD operations
- [ ] Service integrations
- [ ] Frontend updates

### Week 4-8: Remaining Services
- [ ] Job Execution Service
- [ ] Job Scheduling Service
- [ ] Audit & Events Service
- [ ] API Gateway
- [ ] Final migration

## 🛠️ Troubleshooting

### Common Issues
1. **Service Dependencies**: Check health status with `docker-compose ps`
2. **Database Connections**: Verify database URLs and credentials
3. **Network Issues**: Ensure all services are on `opsconductor-network`
4. **Authentication**: Verify JWT_SECRET_KEY is consistent across services

### Useful Commands
```bash
# View service logs
docker-compose logs -f [service-name]

# Check service health
docker-compose ps

# Restart specific service
docker-compose restart [service-name]

# View network configuration
docker network inspect opsconductor-microservices
```

## 📚 Documentation

- [Complete Workplan](./COMPLETE_WORKPLAN.md)
- [Architecture Details](./UPDATED_MICROSERVICES_ARCHITECTURE.md)
- [Shared Libraries](./shared-libs/README.md)
- [API Documentation](../docs/API_REFERENCE.md)

---

**Status**: Phase 1.2 Complete ✅ - Infrastructure & Docker Compose Updated
**Next**: Phase 2.1 - Extract Universal Targets Service