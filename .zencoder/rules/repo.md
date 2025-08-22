---
description: Repository Information Overview
alwaysApply: true
---

# OpsConductor Universal Automation Orchestration Platform

## Repository Summary
OpsConductor is a comprehensive job-centric automation platform for orchestrating tasks across various target systems. It features a modern microservices architecture with individual FastAPI services, API gateway routing, React frontend, and uses PostgreSQL for data storage and Redis for caching. The legacy monolithic backend code is preserved for reference only.

## Repository Structure
- **services/**: **[ACTIVE]** Microservices-based architecture with individual services
- **frontend/**: **[ACTIVE]** React application with Material-UI components
- **archive/legacy-backend-20250822/**: **[RETIRED]** Original monolithic FastAPI application (fully replaced by microservices)
- **database/**: SQL initialization scripts for PostgreSQL
- **nginx/**: Nginx configuration for reverse proxy and SSL termination
- **docs/**: Documentation files including API references and deployment guides
- **tests/**: Comprehensive E2E and API tests using Playwright
- **monitoring/**: Prometheus and Grafana configurations
- **logs/**: Application logs directory

### Active Architecture (Microservices + Frontend)
- **Frontend UI**: React application with Material-UI components
- **API Gateway**: Nginx-based routing and load balancing
- **Auth Service**: JWT authentication and authorization
- **User Service**: User management and profiles
- **Jobs Service**: Job definition and lifecycle management
- **Targets Service**: Target system management and discovery
- **Execution Service**: Job execution with Celery workers
- **Notification Service**: Event notifications and alerts
- **Audit Events Service**: System audit logging and compliance
- **Database**: PostgreSQL for persistent storage
- **Cache**: Redis for session management and task queuing

## Projects

### **[ACTIVE]** Microservices Architecture
**Location**: services/
**Components**: Individual FastAPI services with dedicated databases and responsibilities

### **[LEGACY - REFERENCE ONLY]** Backend (FastAPI)
**Configuration File**: backend/requirements.txt

#### Language & Runtime
**Language**: Python
**Version**: 3.11
**Framework**: FastAPI 0.104.1
**Package Manager**: pip

#### Dependencies
**Main Dependencies**:
- fastapi==0.104.1
- sqlalchemy==2.0.23
- celery==5.3.4
- python-jose==3.3.0
- paramiko==3.4.0
- psycopg2-binary==2.9.9
- redis==5.0.1

**Development Dependencies**:
- uvicorn[standard]==0.24.0
- alembic==1.12.1
- python-dotenv==1.0.0

#### Build & Installation
```bash
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload
```

#### Docker
**Dockerfile**: backend/Dockerfile
**Image**: Python 3.11-slim
**Configuration**: Multi-container setup with Celery workers and scheduler

#### Testing
**Framework**: Built-in Python unittest
**Test Location**: backend/app/tests
**Run Command**:
```bash
cd backend
python -m unittest discover
```

### **[ACTIVE]** Frontend (React)
**Configuration File**: frontend/package.json

#### Language & Runtime
**Language**: JavaScript/React
**Version**: Node.js 18
**Framework**: React 18.2.0
**Package Manager**: npm

#### Dependencies
**Main Dependencies**:
- react==18.2.0
- react-router-dom==6.20.1
- @mui/material==5.14.20
- @mui/x-data-grid==6.18.2
- @reduxjs/toolkit==2.8.2
- axios==1.6.2
- chart.js==4.5.0

**Development Dependencies**:
- react-scripts==5.0.1
- @types/react==18.2.45
- @types/react-dom==18.2.18

#### Build & Installation
```bash
cd frontend
npm install
npm start
```

#### Docker
**Dockerfile**: frontend/Dockerfile
**Image**: Multi-stage build with Node.js 18-alpine for build and nginx:alpine for serving
**Configuration**: Static file serving with custom nginx configuration

#### Testing
**Framework**: React Testing Library (Unit), Playwright (E2E)
**Test Location**: frontend/src/tests (Unit), tests/e2e (E2E)
**Run Command**:
```bash
cd frontend
npm test

# E2E Tests (from root)
npm run test:comprehensive
```

### Testing Framework
**Configuration File**: tests/package.json

#### Language & Runtime
**Language**: TypeScript
**Framework**: Playwright 1.40.0
**Package Manager**: npm

#### Test Types
- **API Tests**: Comprehensive testing of REST API endpoints
- **E2E Tests**: Full user workflow testing with browser automation
- **Smoke Tests**: Basic functionality verification
- **Frontend E2E Tests**: Complete frontend testing covering authentication, navigation, CRUD operations, real-time features, and system health monitoring

#### E2E Test Coverage
- **Authentication & Security**: Login flow with SSL certificate handling
- **Universal Targets**: Target management, creation, filtering, health monitoring
- **Job Management**: Job creation wizard, scheduling, execution tracking
- **System Health**: Real-time monitoring dashboard, container management, resource tracking
- **User Management**: User CRUD operations, role management, status tracking
- **Navigation**: Cross-page navigation, responsive design, layout consistency
- **Real-time Features**: Live timestamps, system status, loading states
- **Error Handling**: Empty states, network conditions, graceful degradation

#### Run Commands
```bash
cd tests
npm install
npm test           # All tests
npm run test:smoke # Smoke tests only
npm run test:api   # API tests only
npm run test:e2e   # E2E tests only
```

### Infrastructure
**Configuration File**: docker-compose.yml

#### Components
- PostgreSQL 15 (Database)
- Redis 7 (Cache)
- Nginx (Reverse Proxy)
- Celery (Task Queue)
- Prometheus (Metrics Collection)
- Grafana (Monitoring Dashboards)

#### Usage & Operations
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild and restart services
docker-compose up -d --build
```

#### Docker
**Main File**: docker-compose.yml
**Services**: postgres, redis, backend, frontend, celery-worker, scheduler, nginx, prometheus, grafana
**Network**: opsconductor-network (bridge)
**Volumes**: postgres_data, prometheus_data, grafana_data (persistent storage)