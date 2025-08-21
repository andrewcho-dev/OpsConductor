# OpsConductor Microservices Architecture

A complete microservice-based job orchestration and execution platform built with FastAPI, PostgreSQL, Redis, and RabbitMQ.

## 🏗️ Architecture Overview

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Job Management  │  │ Job Execution   │  │ Job Scheduling  │  │ Audit & Events  │
│    Service      │  │    Service      │  │    Service      │  │    Service      │
│   Port: 8001    │  │   Port: 8002    │  │   Port: 8003    │  │   Port: 8004    │
│                 │  │                 │  │                 │  │                 │
│ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │
│ │   Jobs DB   │ │  │ │Executions DB│ │  │ │Schedules DB │ │  │ │  Events DB  │ │
│ │ Port: 5432  │ │  │ │ Port: 5433  │ │  │ │ Port: 5434  │ │  │ │ Port: 5435  │ │
│ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
         │                     │                     │                     │
         └─────────────────────┼─────────────────────┼─────────────────────┘
                               │                     │
                    ┌─────────────────┐    ┌─────────────────┐
                    │  API Gateway    │    │ Message Broker  │
                    │   Port: 8080    │    │   RabbitMQ      │
                    │   Port: 8443    │    │   Port: 5672    │
                    └─────────────────┘    └─────────────────┘
                               │
                    ┌─────────────────┐
                    │     Redis       │
                    │   Port: 6379    │
                    └─────────────────┘
```

## 🎯 Microservices

### 1. Job Management Service (Port 8001)
**Responsibility**: Job definition, lifecycle management, and validation

**Features**:
- ✅ Job CRUD operations
- ✅ Job validation and target verification
- ✅ Job metadata and configuration management
- ✅ Integration with external target service
- ✅ Event publishing for job lifecycle changes

**Database**: `job_management` (PostgreSQL)
- `jobs` - Job definitions
- `job_actions` - Action sequences
- `job_targets` - Target associations

**APIs**:
- `POST /api/v1/jobs` - Create job
- `GET /api/v1/jobs` - List jobs (with filtering/pagination)
- `GET /api/v1/jobs/{id}` - Get job details
- `PUT /api/v1/jobs/{id}` - Update job
- `DELETE /api/v1/jobs/{id}` - Delete job
- `POST /api/v1/jobs/{id}/execute` - Initiate execution
- `GET /api/v1/jobs/{id}/validate` - Validate job configuration

### 2. Job Execution Service (Port 8002)
**Responsibility**: Job execution engine and target communication

**Features**:
- ✅ Concurrent job execution on multiple targets
- ✅ SSH/WinRM connection management
- ✅ Retry logic with exponential backoff
- ✅ Safety checks for dangerous commands
- ✅ Real-time execution tracking
- ✅ Celery-based task processing

**Database**: `job_execution` (PostgreSQL)
- `job_executions` - Execution instances
- `job_execution_results` - Per-target results

**APIs**:
- `POST /api/v1/executions` - Create execution
- `GET /api/v1/executions/{id}` - Get execution details
- `GET /api/v1/executions/{id}/results` - Get execution results
- `POST /api/v1/executions/{id}/cancel` - Cancel execution
- `POST /api/v1/executions/{id}/retry` - Retry failed execution

**Workers**:
- Celery workers for async job execution
- Connection pooling and management
- Result aggregation and reporting

### 3. Job Scheduling Service (Port 8003)
**Responsibility**: Time-based job scheduling and triggering

**Features**:
- ✅ Multiple schedule types (once, recurring, cron)
- ✅ Cron expression parsing and validation
- ✅ Timezone support
- ✅ Schedule lifecycle management
- ✅ Automatic job triggering

**Database**: `job_scheduling` (PostgreSQL)
- `job_schedules` - Schedule definitions
- `schedule_executions` - Schedule execution history

**APIs**:
- `POST /api/v1/schedules` - Create schedule
- `GET /api/v1/schedules/job/{id}` - Get job schedules
- `GET /api/v1/schedules/{id}` - Get schedule details
- `PUT /api/v1/schedules/{id}` - Update schedule
- `DELETE /api/v1/schedules/{id}` - Delete schedule

### 4. Audit & Events Service (Port 8004)
**Responsibility**: Event logging, audit trails, and system monitoring

**Features**:
- ✅ Centralized event collection
- ✅ Audit trail management
- ✅ System metrics and monitoring
- ✅ Event-driven notifications
- ✅ Compliance reporting

**Database**: `audit_events` (PostgreSQL)
- `events` - System events
- `audit_logs` - Audit trails
- `metrics` - System metrics

**APIs**:
- `POST /api/v1/events` - Log event
- `GET /api/v1/events` - Query events
- `GET /api/v1/audit` - Get audit logs
- `GET /api/v1/metrics` - Get system metrics

## 🔧 Infrastructure Components

### Message Broker (RabbitMQ)
- **Purpose**: Inter-service event communication
- **Port**: 5672 (AMQP), 15672 (Management UI)
- **Features**:
  - Event publishing/subscribing
  - Reliable message delivery
  - Topic-based routing
  - Dead letter queues

### Cache & Task Queue (Redis)
- **Purpose**: Caching and Celery task queue
- **Port**: 6379
- **Features**:
  - Session caching
  - Task queue for Celery
  - Result backend
  - Pub/sub messaging

### API Gateway (Nginx)
- **Purpose**: Single entry point and load balancing
- **Ports**: 8080 (HTTP), 8443 (HTTPS)
- **Features**:
  - Request routing
  - Load balancing
  - SSL termination
  - Rate limiting
  - CORS handling

### Databases (PostgreSQL)
- **Job Management DB** (Port 5432): Job definitions and metadata
- **Job Execution DB** (Port 5433): Execution instances and results
- **Job Scheduling DB** (Port 5434): Schedule definitions and history
- **Audit Events DB** (Port 5435): Events and audit logs

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Git

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd opsconductor-microservices
   ```

2. **Start infrastructure services**:
   ```bash
   docker-compose up -d rabbitmq redis job-management-db job-execution-db job-scheduling-db audit-events-db
   ```

3. **Wait for services to be healthy**:
   ```bash
   docker-compose ps
   ```

4. **Start microservices**:
   ```bash
   docker-compose up -d job-management-service job-execution-service job-scheduling-service audit-events-service
   ```

5. **Start API Gateway**:
   ```bash
   docker-compose up -d api-gateway
   ```

6. **Verify deployment**:
   ```bash
   curl http://localhost:8080/health
   ```

### Development Setup

1. **Install shared libraries**:
   ```bash
   cd shared-libs
   pip install -e .
   ```

2. **Start each service individually**:
   ```bash
   # Job Management Service
   cd job-management-service
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload

   # Job Execution Service
   cd job-execution-service
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8002 --reload

   # Start Celery workers
   celery -A app.core.celery_app worker --loglevel=info
   ```

## 📊 Service Communication

### Event-Driven Architecture
Services communicate through RabbitMQ events:

```python
# Job Management → Job Execution
EventType.JOB_EXECUTED → Triggers execution

# Job Execution → Job Management  
EventType.EXECUTION_COMPLETED → Updates job status

# Job Scheduling → Job Management
EventType.SCHEDULE_TRIGGERED → Initiates job execution

# All Services → Audit Events
EventType.* → Centralized logging
```

### HTTP API Communication
Services also communicate via HTTP APIs:

```python
# Job Management calls Job Execution
POST /api/v1/executions
{
  "job_id": 123,
  "target_ids": [1, 2, 3]
}

# Job Execution calls Job Management
GET /api/v1/jobs/123
```

## 🔒 Security

### Authentication
- JWT-based authentication across all services
- Service-to-service authentication
- Role-based access control

### Safety Features
- Command safety validation
- Dangerous operation detection
- Execution sandboxing
- Audit logging

## 📈 Monitoring & Observability

### Health Checks
Each service exposes health endpoints:
- `/health` - Service health status
- `/metrics` - Service metrics
- `/version` - Service version info

### Logging
- Structured JSON logging
- Centralized log aggregation
- Request tracing with correlation IDs
- Performance metrics

### Metrics
- Service-level metrics
- Business metrics (job success rates, execution times)
- Infrastructure metrics (database, message queue)

## 🔧 Configuration

### Environment Variables
Each service uses environment-specific configuration:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Message Broker
RABBITMQ_URL=amqp://user:pass@host:port/

# External Services
JOB_EXECUTION_SERVICE_URL=http://job-execution-service:8002
TARGET_SERVICE_URL=http://target-service:3001

# Security
JWT_SECRET_KEY=your-secret-key
```

### Service Discovery
Services discover each other through:
- Environment variables for service URLs
- Docker Compose service names
- Health check endpoints

## 🧪 Testing

### Unit Tests
```bash
cd job-management-service
pytest tests/unit/

cd job-execution-service  
pytest tests/unit/
```

### Integration Tests
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/
```

### End-to-End Tests
```bash
# Full system tests
pytest tests/e2e/
```

## 📦 Deployment

### Production Deployment
```bash
# Build all services
docker-compose build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment
Kubernetes manifests available in `/k8s` directory:
```bash
kubectl apply -f k8s/
```

## 🔄 Migration from Monolith

If migrating from the original monolithic service:

1. **Data Migration**: Scripts to migrate data between databases
2. **API Compatibility**: Maintain backward compatibility during transition
3. **Gradual Rollout**: Deploy services incrementally
4. **Monitoring**: Enhanced monitoring during migration

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

---

## 🎯 Key Benefits of This Architecture

### ✅ **True Microservices**
- **Single Responsibility**: Each service has one clear purpose
- **Independent Databases**: No shared data stores
- **Independent Deployment**: Services can be deployed separately
- **Technology Independence**: Each service can use different tech stacks

### ✅ **Scalability**
- **Horizontal Scaling**: Scale services independently based on load
- **Resource Optimization**: Allocate resources where needed most
- **Performance Isolation**: Issues in one service don't affect others

### ✅ **Reliability**
- **Fault Isolation**: Service failures are contained
- **Circuit Breakers**: Prevent cascade failures
- **Retry Logic**: Automatic recovery from transient failures
- **Health Monitoring**: Proactive issue detection

### ✅ **Development Velocity**
- **Team Autonomy**: Different teams can own different services
- **Independent Development**: Parallel development without conflicts
- **Technology Choice**: Use best tool for each job
- **Faster Deployments**: Deploy only what changed

### ✅ **Operational Excellence**
- **Observability**: Comprehensive monitoring and logging
- **Event-Driven**: Loose coupling through events
- **API-First**: Well-defined service contracts
- **Infrastructure as Code**: Reproducible deployments

This is a **production-ready microservice architecture** that provides all the benefits of distributed systems while maintaining the functionality of the original job execution service!