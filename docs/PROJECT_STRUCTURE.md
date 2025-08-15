# OpsConductor Project Structure

## Overview
This document outlines the complete project structure and organization of the OpsConductor platform.

## Root Directory Structure

```
OpsConductor/
├── backend/                    # FastAPI backend application
├── frontend/                   # React frontend application
├── database/                   # Database initialization scripts
├── nginx/                      # Nginx configuration and SSL
├── monitoring/                 # Prometheus and Grafana configuration
├── tests/                      # Automated test suite
├── docs/                       # Documentation
├── logs/                       # Application logs
├── docker-compose.yml          # Development environment
├── docker-compose.prod.yml     # Production environment
├── .env                        # Environment configuration
├── .env.production            # Production environment template
└── README.md                  # Main project documentation
```

## Backend Structure (`backend/`)

```
backend/
├── app/                        # Main application package
│   ├── api/                   # API route definitions
│   ├── core/                  # Core functionality and utilities
│   ├── database/              # Database connection and configuration
│   ├── domains/               # Domain-specific business logic
│   ├── models/                # SQLAlchemy database models
│   ├── routers/               # FastAPI route handlers
│   ├── schemas/               # Pydantic data models
│   ├── services/              # Business logic services
│   ├── shared/                # Shared utilities and infrastructure
│   ├── tasks/                 # Celery background tasks
│   └── utils/                 # Utility functions
├── alembic/                   # Database migration management
├── logs/                      # Backend application logs
├── migrations/                # SQL migration scripts
├── scripts/                   # Utility and maintenance scripts
├── uploads/                   # File upload storage
├── Dockerfile                 # Production container image
├── Dockerfile.dev             # Development container image
├── main.py                    # FastAPI application entry point
└── requirements.txt           # Python dependencies
```

## Frontend Structure (`frontend/`)

```
frontend/
├── public/                    # Static public assets
├── src/                       # React application source
│   ├── components/           # Reusable React components
│   │   ├── common/          # Shared UI components
│   │   ├── jobs/            # Job management components
│   │   ├── targets/         # Target management components
│   │   ├── users/           # User management components
│   │   └── system/          # System management components
│   ├── contexts/            # React context providers
│   ├── features/            # Feature-specific components
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API service functions
│   ├── store/               # Redux store configuration
│   ├── styles/              # CSS and styling
│   ├── utils/               # Utility functions
│   ├── App.js               # Main application component
│   └── index.js             # Application entry point
├── build/                     # Production build output
├── Dockerfile                 # Production container image
├── Dockerfile.dev             # Development container image
├── nginx.conf                 # Nginx configuration for serving
├── package.json               # Node.js dependencies
└── package-lock.json          # Dependency lock file
```

## Database Structure (`database/`)

```
database/
└── init/                      # Database initialization scripts
    ├── 01_init.sql           # Core tables and initial data
    ├── 02_job_tables.sql     # Job management tables
    ├── 03_add_job_targets_table.sql  # Job-target relationships
    ├── 04_analytics_tables.sql       # Analytics and reporting
    ├── 05_discovery_tables.sql       # Network discovery
    ├── 06_job_schedule_tables.sql    # Job scheduling
    ├── 07_notification_tables.sql    # Notification system
    └── 08_celery_tables.sql          # Celery task management
```

## Documentation Structure (`docs/`)

```
docs/
├── ACTIONS_QUICK_REFERENCE.md    # Quick reference for workflow actions
├── ACTIONS_WORKSPACE_GUIDE.md    # Complete workflow creation guide
├── API_REFERENCE.md              # REST API documentation
├── CHANGELOG.md                  # Version history and changes
├── DEPLOYMENT_GUIDE.md           # Production deployment instructions
├── DEVELOPER_GUIDE.md            # Development setup and guidelines
├── PROJECT_STRUCTURE.md          # This file
├── SECURITY_GUIDE.md             # Security configuration and practices
└── TESTING_GUIDE.md              # Testing procedures and automation
```

## Test Structure (`tests/`)

```
tests/
├── api/                          # API integration tests
│   └── api-comprehensive.spec.ts
├── e2e/                          # End-to-end tests
│   ├── pages/                   # Page object models
│   │   ├── base.page.ts
│   │   ├── dashboard.page.ts
│   │   ├── jobs.page.ts
│   │   ├── login.page.ts
│   │   ├── targets.page.ts
│   │   └── users.page.ts
│   ├── comprehensive.spec.ts    # Full workflow tests
│   ├── smoke-test.spec.ts       # Basic functionality tests
│   └── test-data.ts             # Shared test data
├── playwright.config.ts         # Test configuration
├── package.json                 # Test dependencies
└── README.md                    # Testing documentation
```

## Configuration Files

### Environment Configuration
- **`.env`** - Development environment variables
- **`.env.production`** - Production environment template
- **`env.example`** - Environment variable examples

### Container Configuration
- **`docker-compose.yml`** - Development multi-container setup
- **`docker-compose.prod.yml`** - Production multi-container setup

### Service Configuration
- **`nginx/nginx.conf`** - Nginx reverse proxy configuration
- **`monitoring/prometheus.yml`** - Prometheus metrics configuration
- **`monitoring/grafana/`** - Grafana dashboards and datasources

## Key Design Principles

### Separation of Concerns
- **Backend**: Pure API and business logic
- **Frontend**: User interface and experience
- **Database**: Data persistence and integrity
- **Infrastructure**: Service orchestration and deployment

### Scalability
- **Microservice Architecture**: Independent, scalable components
- **Container-based**: Easy deployment and scaling
- **Queue-based Processing**: Asynchronous task execution
- **Caching Layer**: Redis for performance optimization

### Security
- **Environment-based Configuration**: Secure credential management
- **Role-based Access Control**: Granular permission system
- **Network Isolation**: Container-based security boundaries
- **SSL/TLS Termination**: Encrypted communication

### Maintainability
- **Clear Directory Structure**: Logical organization
- **Comprehensive Documentation**: Detailed guides and references
- **Automated Testing**: Quality assurance and regression prevention
- **Version Control**: Git-based change management

## Development Workflow

### Local Development
1. **Environment Setup**: Configure `.env` file
2. **Service Startup**: `docker-compose up -d`
3. **Development**: Edit code with hot-reload
4. **Testing**: Run automated test suite
5. **Debugging**: Use container logs and debugging tools

### Production Deployment
1. **Environment Configuration**: Set production variables
2. **Image Building**: Build optimized container images
3. **Service Deployment**: Deploy with production compose
4. **Health Verification**: Confirm all services are operational
5. **Monitoring Setup**: Configure alerts and dashboards

This structure provides a solid foundation for enterprise-scale automation orchestration while maintaining clarity and maintainability.