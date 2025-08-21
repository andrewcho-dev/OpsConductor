# OpsConductor Microservices

## Service Architecture

```
services/
├── infrastructure/          # Core infrastructure (databases, message broker, API gateway)
├── auth-service/           # Authentication & JWT token management
├── user-service/           # User management & profiles  
├── targets-service/        # Universal target systems management
├── jobs-service/           # Job creation, scheduling & management
├── execution-service/      # Job execution engine
├── frontend-service/       # React UI application
└── shared/                 # Shared libraries and utilities
```

## Build Order

1. **Infrastructure** - PostgreSQL, Redis, RabbitMQ, API Gateway
2. **Auth Service** - JWT authentication foundation
3. **User Service** - User management 
4. **Targets Service** - Target system management
5. **Jobs Service** - Job creation and scheduling
6. **Execution Service** - Job execution engine
7. **Frontend Service** - React user interface
8. **Integration Testing** - End-to-end system validation

## Service Communication

- **REST APIs** for synchronous communication
- **RabbitMQ** for asynchronous messaging and job processing
- **Docker networking** for service discovery
- **API Gateway** for external access and routing