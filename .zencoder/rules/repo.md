---
description: Repository Information Overview
alwaysApply: true
---

# ENABLEDRM Universal Automation Orchestration Platform

## Repository Summary
ENABLEDRM is a job-centric automation platform for orchestrating tasks across various target systems. It features a modern architecture with a FastAPI backend, React frontend, and uses PostgreSQL for data storage and Redis for caching.

## Repository Structure
- **backend/**: FastAPI application with API endpoints, database models, and business logic
- **frontend/**: React application with Material-UI components
- **database/**: SQL initialization scripts for PostgreSQL
- **nginx/**: Nginx configuration for reverse proxy and SSL termination
- **docs/**: Documentation files including API references and deployment guides
- **logs/**: Application logs directory

### Main Repository Components
- **Backend API**: FastAPI-based REST API with JWT authentication
- **Frontend UI**: React application with Material-UI components
- **Job System**: Celery-based task execution and scheduling
- **Database**: PostgreSQL for persistent storage
- **Cache**: Redis for session management and task queuing

## Projects

### Backend (FastAPI)
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

### Frontend (React)
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
**Framework**: React Testing Library
**Test Location**: frontend/src/tests
**Run Command**:
```bash
cd frontend
npm test
```

### Infrastructure
**Configuration File**: docker-compose.yml

#### Components
- PostgreSQL 15 (Database)
- Redis 7 (Cache)
- Nginx (Reverse Proxy)
- Celery (Task Queue)

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
**Services**: postgres, redis, backend, frontend, celery-worker, scheduler, nginx
**Network**: enabledrm-network (bridge)
**Volumes**: postgres_data (persistent database storage)