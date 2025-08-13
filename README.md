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
- **Job Orchestration** - Execute commands across multiple targets
- **Target Management** - Manage servers, network devices, and cloud resources
- **Network Discovery** - Automated device discovery and scanning
- **Real-time Monitoring** - Live job execution tracking
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

### Job Management
- Create and execute jobs across multiple targets
- Support for commands, scripts, and file transfers
- Hierarchical execution tracking with serial identifiers
- Real-time execution monitoring
- Comprehensive execution history

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

## 🔌 API Reference

### Authentication
All API endpoints require JWT authentication:
```bash
curl -H "Authorization: Bearer <jwt_token>" \
     https://localhost/api/jobs
```

### Key Endpoints
- `POST /api/auth/login` - User authentication
- `GET /api/jobs` - List jobs
- `POST /api/jobs` - Create job
- `GET /api/targets` - List targets
- `POST /api/targets` - Create target
- `GET /api/discovery/scan` - Network discovery
- `GET /api/system/health` - System health

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