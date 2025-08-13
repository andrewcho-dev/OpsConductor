# OpsConductor - Enterprise Automation Orchestration Platform

OpsConductor is a comprehensive job-centric automation platform designed for orchestrating tasks across various target systems. Built with modern architecture principles, it provides enterprise-grade features for system administration, network discovery, and automated task execution.

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 20GB+ storage

### Development Setup
```bash
# Clone the repository
git clone https://github.com/andrewcho-dev/OpsConductor.git
cd OpsConductor

# Start all services
docker-compose up -d

# Access the application
https://localhost
```

Default credentials:
- **Username**: `admin`
- **Password**: `admin123`

## 🏗️ Architecture

### Core Components
- **FastAPI Backend** - REST API with JWT authentication
- **React Frontend** - Modern Material-UI interface
- **PostgreSQL** - Primary database
- **Redis** - Caching and task queuing
- **Celery** - Background task processing
- **Nginx** - Reverse proxy with SSL termination

### Key Features
- **Advanced Workflow Engine** - Create sophisticated automation workflows with conditional logic
- **Actions Workspace** - Visual workflow designer with 8+ action types (commands, scripts, APIs, files, etc.)
- **Conditional Logic & Dependencies** - Build complex workflows with branching logic and action dependencies
- **Target Management** - Manage servers, network devices, and cloud resources
- **Network Discovery** - Automated device discovery and scanning
- **Real-time Monitoring** - Live job execution tracking with hierarchical serialization
- **Variable System** - Powerful templating with system and custom variables
- **User Management** - Role-based access control
- **Audit Logging** - Comprehensive activity tracking
- **System Health** - Service monitoring and restart capabilities

## 📁 Project Structure

```
OpsConductor/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── domains/        # Domain-driven design modules
│   │   ├── models/         # Database models
│   │   ├── routers/        # Route handlers
│   │   ├── services/       # Business logic
│   │   └── shared/         # Shared infrastructure
│   ├── Dockerfile          # Production container
│   └── requirements.txt    # Python dependencies
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   └── store/          # State management
│   ├── Dockerfile          # Production container
│   └── package.json        # Node.js dependencies
├── database/               # Database initialization
├── nginx/                  # Reverse proxy configuration
├── monitoring/             # Prometheus/Grafana configs
├── docker-compose.yml      # Development environment
├── docker-compose.prod.yml # Production environment
└── .env                    # Environment configuration
```

## 🔧 Configuration

### Environment Variables
Key configuration options in `.env`:

```bash
# Database
POSTGRES_DB=opsconductor_dev
POSTGRES_USER=opsconductor
POSTGRES_PASSWORD=opsconductor_secure_password_2024

# Security
SECRET_KEY=opsconductor-dev-secret-key-2024-super-secure
JWT_SECRET_KEY=opsconductor-dev-jwt-secret-2024-super-secure

# Performance
MAX_CONCURRENT_TARGETS=20
CONNECTION_TIMEOUT=30
COMMAND_TIMEOUT=300
```

### Production Deployment
For production deployment, use `docker-compose.prod.yml`:

```bash
# Copy and configure production environment
cp .env.production .env
# Edit .env with your production values

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🎯 Core Features

### Advanced Workflow Engine
- **Actions Workspace** - Visual workflow designer with drag-and-drop interface
- **8+ Action Types** - Commands, scripts, APIs, databases, files, email, conditions, parallel execution
- **Conditional Logic** - Execute actions based on runtime conditions and previous results
- **Action Dependencies** - Define execution order and prerequisites
- **Variable System** - System and custom variables with templating support
- **Retry & Error Handling** - Sophisticated error recovery and rollback mechanisms
- **Workflow Validation** - Real-time validation with circular dependency detection

### Job Management
- Create sophisticated multi-step workflows across multiple targets
- Target-first workflow design for better compatibility
- Hierarchical execution tracking with serial identifiers
- Real-time execution monitoring with detailed logging
- Comprehensive execution history and audit trails

### Target Management
- Universal target support (SSH, WinRM, API endpoints)
- Automated network discovery
- Target grouping and tagging
- Connection testing and validation
- Credential management

### Discovery Dashboard
- Network scanning and device discovery
- Service detection and port scanning
- Device fingerprinting
- Integration with target management

### System Monitoring
- Real-time system health monitoring
- Service restart and reload capabilities
- Performance metrics and analytics
- Alert and notification system

### User Management
- Role-based access control (Admin, Operator, Viewer)
- JWT-based authentication
- User activity auditing
- Session management

## 📚 Documentation

### User Guides
- **[Actions Workspace Guide](docs/ACTIONS_WORKSPACE_GUIDE.md)** - Complete guide to creating workflows
- **[Actions Quick Reference](docs/ACTIONS_QUICK_REFERENCE.md)** - Quick reference card for workflow creation
- **[API Reference](docs/API_REFERENCE.md)** - Comprehensive API documentation
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment instructions
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Development setup and contribution guide
- **[Changelog](docs/CHANGELOG.md)** - Version history and release notes

### Quick Start Workflows

#### Simple Command Execution
```json
{
  "name": "System Health Check",
  "actions": [
    {
      "type": "command",
      "name": "Check Disk Space",
      "parameters": {
        "command": "df -h"
      }
    }
  ],
  "target_ids": [1, 2, 3]
}
```

#### Multi-Step Deployment
```json
{
  "name": "Application Deployment",
  "actions": [
    {
      "id": "health-check",
      "type": "command",
      "name": "Pre-deployment Check",
      "parameters": {
        "command": "curl -f http://localhost/health"
      }
    },
    {
      "id": "deploy",
      "type": "script",
      "name": "Deploy Application",
      "parameters": {
        "scriptType": "bash",
        "scriptContent": "#!/bin/bash\necho 'Deploying...'\n# Deployment logic here"
      },
      "dependencies": [
        {
          "actionId": "health-check",
          "status": "success"
        }
      ]
    },
    {
      "id": "notify",
      "type": "email",
      "name": "Send Notification",
      "parameters": {
        "to": "ops-team@company.com",
        "subject": "Deployment Complete",
        "body": "Deployment of ${JOB_NAME} completed on ${TARGET_HOST}"
      },
      "dependencies": [
        {
          "actionId": "deploy",
          "status": "success"
        }
      ]
    }
  ]
}
```

## 🔌 API Reference

### Authentication
All API endpoints require JWT authentication:
```bash
curl -H "Authorization: Bearer <jwt_token>" \
     https://localhost/api/jobs
```

### Key Endpoints
- `POST /api/auth/login` - User authentication
- `GET /api/jobs` - List jobs with workflow details
- `POST /api/jobs` - Create workflow-based jobs
- `GET /api/targets` - List targets
- `POST /api/targets` - Create target
- `GET /api/discovery/scan` - Network discovery
- `GET /api/system/health` - System health

For complete API documentation, see [API Reference](docs/API_REFERENCE.md).

## 🛠️ Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Database Migrations
```bash
# Access the backend container
docker exec -it opsconductor-backend bash

# Run migrations
alembic upgrade head
```

## 📊 Monitoring

### Built-in Monitoring
- Prometheus metrics collection
- Grafana dashboards
- System health endpoints
- Real-time job execution tracking

### Access Monitoring
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication
- Role-based access control
- Secure credential storage
- Session management

### Network Security
- SSL/TLS termination at nginx
- Internal service communication
- Configurable CORS policies
- Rate limiting

## 🚀 Production Considerations

### Performance Tuning
- Adjust `MAX_CONCURRENT_TARGETS` based on system capacity
- Configure database connection pooling
- Optimize Redis cache settings
- Scale Celery workers as needed

### Backup & Recovery
- Regular PostgreSQL backups
- Configuration file versioning
- Log rotation and archiving
- Disaster recovery procedures

### Monitoring & Alerting
- Configure Prometheus alerting rules
- Set up Grafana notifications
- Monitor system resource usage
- Track job execution metrics

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses
This software incorporates several third-party libraries and components. See the [NOTICE](NOTICE) file for detailed attribution and license information for all third-party components.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API reference

---

**OpsConductor** - Orchestrating automation at enterprise scale.

*Copyright © 2025 Enabled Enterprises LLC. All rights reserved.*