# 🏗️ ENABLEDRM Docker Architecture

## Overview
This document describes the complete containerized architecture for the ENABLEDRM system, designed with proper separation of concerns and industry best practices.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        NGINX REVERSE PROXY                      │
│                     (Port 80/443 - SSL/TLS)                    │
│                    Routes: /, /api, /monitor                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────────┐
        │             │             │                 │
┌───────▼──────┐ ┌───▼────┐ ┌──────▼──────┐ ┌───────▼──────┐
│   FRONTEND   │ │BACKEND │ │   MONITOR   │ │   SCHEDULER  │
│   (React)    │ │(FastAPI│ │  (Python)   │ │ (Celery Beat)│
│   Port: 3000 │ │Port:8000│ │ Port: 9000  │ │              │
└──────────────┘ └───┬────┘ └─────────────┘ └──────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼────┐ ┌─────▼─────┐
│CELERY WORKER │ │ REDIS │ │POSTGRESQL │
│ (Background) │ │(Cache)│ │(Database) │
│              │ │:6379  │ │  :5432    │
└──────────────┘ └───────┘ └───────────┘
```

## Container Specifications

### 1. **nginx** - Reverse Proxy & SSL Termination
- **Purpose**: Route traffic, handle SSL, serve static files
- **Port**: 80 (HTTP), 443 (HTTPS)
- **Routes**:
  - `/` → Frontend (React)
  - `/api/*` → Backend (FastAPI)
  - `/monitor` → Monitor Dashboard
- **SSL**: Self-signed certificates for development
- **Dependencies**: frontend, backend, monitor

### 2. **frontend** - React Application
- **Purpose**: User interface and client-side logic
- **Port**: 3000 (internal)
- **Technology**: React 18 with Vite
- **Features**: Hot reload, development server
- **Environment**: Development mode with source maps
- **Dependencies**: None (standalone)

### 3. **backend** - FastAPI Application
- **Purpose**: REST API, authentication, business logic
- **Port**: 8000 (internal)
- **Technology**: FastAPI with Uvicorn
- **Features**: 
  - JWT Authentication
  - File upload handling
  - Database operations
  - API documentation (Swagger)
- **Dependencies**: postgres, redis

### 4. **monitor** - System Monitoring Dashboard
- **Purpose**: Monitor system health and container status
- **Port**: 9000 (internal)
- **Technology**: Python HTTP server
- **Features**:
  - Container health checks
  - Service status monitoring
  - Real-time dashboard
  - Docker socket access
- **Dependencies**: All other services (for monitoring)

### 5. **celery-worker** - Background Job Processor
- **Purpose**: Process asynchronous tasks
- **Technology**: Celery with Redis broker
- **Features**:
  - Email sending
  - File processing
  - Data imports/exports
  - Long-running tasks
- **Dependencies**: postgres, redis, backend

### 6. **celery-beat** - Task Scheduler
- **Purpose**: Schedule periodic tasks
- **Technology**: Celery Beat scheduler
- **Features**:
  - Cron-like scheduling
  - Periodic cleanup tasks
  - Health checks
  - Report generation
- **Dependencies**: postgres, redis

### 7. **postgres** - Primary Database
- **Purpose**: Persistent data storage
- **Port**: 5432 (internal)
- **Technology**: PostgreSQL 15
- **Features**:
  - User data
  - Application state
  - Transaction logs
  - Data persistence
- **Dependencies**: None

### 8. **redis** - Cache & Message Broker
- **Purpose**: Caching and task queue
- **Port**: 6379 (internal)
- **Technology**: Redis 7
- **Features**:
  - Session storage
  - API response caching
  - Celery message broker
  - Real-time data
- **Dependencies**: None

## Network Configuration

### Internal Network: `enabledrm-network`
- **Type**: Bridge network
- **Purpose**: Inter-container communication
- **DNS**: Automatic service discovery by container name

### Port Mapping
- **External Access**: Only through Nginx (80/443)
- **Internal Communication**: Container names as hostnames
- **Development**: Direct port access for debugging

## Volume Management

### Persistent Volumes
- `postgres_data`: Database files
- `redis_data`: Redis persistence
- `upload_data`: User uploaded files

### Development Volumes
- `./frontend:/app`: React source code (hot reload)
- `./backend:/app`: FastAPI source code (hot reload)
- `/var/run/docker.sock`: Docker socket for monitoring

## Environment Configuration

### Development (.env.dev)
```bash
# Database
POSTGRES_DB=enabledrm_dev
POSTGRES_USER=enabledrm
POSTGRES_PASSWORD=dev_password

# Redis
REDIS_URL=redis://redis:6379

# Backend
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=dev-jwt-secret
ENVIRONMENT=development

# Frontend
REACT_APP_API_URL=https://localhost/api
```

### Production (.env.prod)
```bash
# Database
POSTGRES_DB=enabledrm
POSTGRES_USER=enabledrm
POSTGRES_PASSWORD=${SECURE_PASSWORD}

# Redis
REDIS_URL=redis://redis:6379

# Backend
SECRET_KEY=${SECURE_SECRET_KEY}
JWT_SECRET_KEY=${SECURE_JWT_SECRET}
ENVIRONMENT=production

# Frontend
REACT_APP_API_URL=https://yourdomain.com/api
```

## Health Checks

Each container includes health checks:
- **nginx**: HTTP request to localhost
- **frontend**: HTTP request to React dev server
- **backend**: FastAPI health endpoint
- **monitor**: HTTP request to status endpoint
- **postgres**: pg_isready command
- **redis**: redis-cli ping
- **celery-worker**: Celery inspect ping
- **celery-beat**: Process check

## Scaling Strategy

### Development
- Single instance of each service
- Hot reload enabled
- Debug logging

### Production
- **nginx**: 1 instance (can add load balancer)
- **frontend**: 1 instance (static files served by nginx)
- **backend**: 2-4 instances (horizontal scaling)
- **celery-worker**: 2-8 instances (based on load)
- **celery-beat**: 1 instance (singleton)
- **postgres**: 1 instance (can add read replicas)
- **redis**: 1 instance (can add clustering)

## Security Considerations

### Network Security
- No direct external access to internal services
- All traffic routed through nginx
- Internal network isolation

### Data Security
- Environment variables for secrets
- Volume encryption in production
- SSL/TLS for all external communication

### Container Security
- Non-root users where possible
- Minimal base images
- Regular security updates

## Monitoring & Logging

### Container Logs
- Centralized logging via Docker
- Log rotation configured
- Structured JSON logging

### Health Monitoring
- Built-in health checks
- Custom monitoring dashboard
- Alert system for failures

### Performance Monitoring
- Resource usage tracking
- Response time monitoring
- Queue length monitoring

## Development Workflow

### Starting the System
```bash
# Start all services
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f

# Access services
# Frontend: https://localhost
# API Docs: https://localhost/api/docs
# Monitor: https://localhost/monitor
```

### Development Commands
```bash
# Rebuild specific service
docker compose -f docker-compose.dev.yml build backend

# Scale workers
docker compose -f docker-compose.dev.yml up -d --scale celery-worker=4

# Database operations
docker compose -f docker-compose.dev.yml exec postgres psql -U enabledrm -d enabledrm_dev

# Redis operations
docker compose -f docker-compose.dev.yml exec redis redis-cli
```

## Troubleshooting

### Common Issues
1. **Port conflicts**: Check if ports 80/443 are available
2. **Volume permissions**: Ensure proper file permissions
3. **Network issues**: Verify container connectivity
4. **Environment variables**: Check .env file configuration

### Debug Commands
```bash
# Check container status
docker compose -f docker-compose.dev.yml ps

# Inspect networks
docker network ls
docker network inspect enabledrm-network

# Container shell access
docker compose -f docker-compose.dev.yml exec backend bash
```

## Migration from Old Architecture

### Steps
1. Backup existing data
2. Stop old containers
3. Deploy new architecture
4. Migrate data
5. Update configuration
6. Test all services

### Rollback Plan
- Keep old docker-compose.yml as backup
- Database backup before migration
- Quick rollback procedure documented

---

**Last Updated**: $(date)
**Version**: 2.0.0
**Status**: Implementation in Progress