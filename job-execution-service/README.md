# Job Execution Service

A dedicated microservice for job orchestration, execution, and scheduling in the OpsConductor platform.

## 🎯 **Service Overview**

The Job Execution Service handles all job-related operations including:
- Job creation, management, and lifecycle
- Job execution on remote targets via SSH/WinRM
- Job scheduling (one-time, recurring, cron-based)
- Execution result tracking and reporting
- Retry logic and error handling
- Concurrent execution management

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                Job Execution Service                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   FastAPI   │  │   Celery    │  │  Scheduler  │        │
│  │   REST API  │  │   Workers   │  │   (Beat)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Job Service │  │ Execution   │  │ Scheduling  │        │
│  │             │  │ Service     │  │ Service     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ PostgreSQL  │  │    Redis    │  │   Events    │        │
│  │  Database   │  │    Queue    │  │    Bus      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 **Technology Stack**

- **API Framework**: FastAPI (async/await)
- **Database**: PostgreSQL 15
- **Queue**: Redis 7 + Celery
- **Task Execution**: Async SSH/WinRM clients
- **Scheduling**: Celery Beat + Cron
- **Monitoring**: Structured logging + metrics
- **Communication**: HTTP REST + Redis pub/sub events

## 📊 **Database Schema**

### Core Entities
- **Jobs** - Job definitions and metadata
- **JobActions** - Actions to execute (commands, scripts, file transfers)
- **JobTargets** - Target associations
- **JobExecutions** - Execution instances
- **JobExecutionResults** - Per-target, per-action results
- **JobSchedules** - Scheduling configurations
- **ScheduleExecutions** - Schedule execution tracking

## 🚀 **Key Features**

### Job Types
- **Command** - Execute shell commands
- **Script** - Run scripts (bash, PowerShell, Python)
- **File Transfer** - Upload/download files
- **Composite** - Multi-step workflows

### Execution Engine
- **Async Execution** - Concurrent target processing
- **Connection Pooling** - Efficient SSH/WinRM connections
- **Retry Logic** - Exponential backoff with configurable limits
- **Timeout Handling** - Per-action and per-job timeouts
- **Result Streaming** - Real-time execution updates

### Scheduling
- **One-time** - Execute at specific datetime
- **Recurring** - Daily, weekly, monthly patterns
- **Cron** - Full cron expression support
- **Timezone Support** - Multi-timezone scheduling

### Safety & Reliability
- **Concurrency Limits** - Prevent target overload
- **Safety Checks** - Validate dangerous commands
- **Circuit Breakers** - Fail fast on target issues
- **Dead Letter Queue** - Handle failed executions

## 🔌 **Service Integration**

### External Service Calls
- **Target Service** - Get target details and credentials
- **User Service** - Validate users and permissions
- **Notification Service** - Send completion notifications
- **Audit Service** - Log execution events

### Event Publishing
- **Job Created** - New job registered
- **Job Started** - Execution began
- **Job Completed** - Execution finished
- **Job Failed** - Execution failed
- **Schedule Triggered** - Scheduled job executed

## 🐳 **Deployment**

### Docker Services
- **job-api** - FastAPI REST API server
- **job-worker** - Celery worker processes
- **job-scheduler** - Celery beat scheduler
- **job-db** - PostgreSQL database
- **job-redis** - Redis queue and cache

### Environment Configuration
- Database connection strings
- Redis connection settings
- External service URLs
- Execution limits and timeouts
- Retry and safety configurations

## 📈 **Monitoring & Observability**

### Metrics
- Job execution rates and durations
- Success/failure ratios
- Queue depths and processing times
- Target connection health
- Resource utilization

### Logging
- Structured JSON logging
- Execution tracing
- Error tracking
- Performance metrics

## 🔒 **Security**

### Authentication
- JWT token validation
- Service-to-service authentication
- Role-based access control

### Credential Management
- Encrypted credential storage
- Secure credential retrieval
- Connection security (SSH keys, certificates)

## 🚦 **API Endpoints**

### Job Management
- `POST /jobs` - Create job
- `GET /jobs` - List jobs
- `GET /jobs/{id}` - Get job details
- `PUT /jobs/{id}` - Update job
- `DELETE /jobs/{id}` - Delete job

### Job Execution
- `POST /jobs/{id}/execute` - Execute job
- `GET /jobs/{id}/executions` - List executions
- `GET /executions/{id}` - Get execution details
- `GET /executions/{id}/results` - Get execution results
- `POST /executions/{id}/cancel` - Cancel execution

### Job Scheduling
- `POST /jobs/{id}/schedules` - Create schedule
- `GET /jobs/{id}/schedules` - List schedules
- `PUT /schedules/{id}` - Update schedule
- `DELETE /schedules/{id}` - Delete schedule

### System
- `GET /health` - Health check
- `GET /metrics` - Service metrics
- `GET /status` - Service status