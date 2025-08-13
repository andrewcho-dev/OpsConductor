# ENABLEDRM Universal Automation Orchestration Platform

A job-centric automation platform for orchestrating tasks across any type of target system (servers, databases, cloud services, APIs, etc.) through a universal interface.

## 🏗️ Architecture Overview

This platform follows a **job-centric architecture** where:
- **Jobs are the fundamental organizing principle** of the entire system
- **Targets enable job execution** through various communication methods
- **Universal target architecture** supports any system type
- **Hierarchical execution tracking** with permanent serial identifiers
- **Comprehensive traceability** with detailed logging and audit trails

### 🔢 Execution Serialization System

The platform implements a hierarchical serialization system for complete execution traceability:

```
Job Serial:           J202500001
Execution Serial:     J202500001.0001
Target Result Serial: J202500001.0001.0001
Target Reference:     T202500001
```

**Benefits:**
- **Permanent Identifiers**: Every execution has a unique, human-readable serial
- **Hierarchical Relationships**: Clear parent-child execution structure
- **Cross-Reference Capability**: Link executions to specific targets
- **Performance Tracking**: Historical analysis by target and job
- **Audit Compliance**: Complete execution genealogy

## 🚀 Current Implementation Status

### ✅ Completed (Phase 1)
- **Infrastructure**: Docker containerization with React, FastAPI, PostgreSQL, Redis
- **User Management System**: Complete authentication and authorization
- **Role-based Access Control**: Administrator, Manager, User, Guest roles
- **Session Management**: JWT tokens with refresh capability
- **Security**: Password hashing, CORS, rate limiting, security headers

### ✅ Completed (Phase 2)
- **Job Management System**: Complete job creation, scheduling, and execution
- **Universal Target Management**: Multi-protocol target support (SSH, WinRM, API)
- **Execution Serialization**: Hierarchical tracking system (`J20250001.0001.0001`)
- **Real-time Monitoring**: Live execution status and progress tracking
- **Advanced Analytics**: Performance metrics and execution history
- **Sortable Data Tables**: Enhanced UI with column sorting and filtering

### 🔄 Coming Soon (Future Phases)
- Advanced Scheduling (cron, recurring jobs)
- Workflow Orchestration (job dependencies)
- Advanced Notification System
- API Integration Framework
- Performance Optimization

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **JWT** - Authentication tokens
- **bcrypt** - Password hashing

### Frontend
- **React** - User interface framework
- **Material-UI** - Component library
- **React Router** - Client-side routing
- **Axios** - HTTP client

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy and load balancer

## 📚 Documentation

### Core Documentation
- **[Execution Serialization System](docs/EXECUTION_SERIALIZATION.md)** - Complete guide to hierarchical execution tracking
- **[API Reference](docs/API_REFERENCE.md)** - Comprehensive API documentation with serialization examples
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Development patterns and best practices
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment with monitoring and security

### Quick Reference
- **Job Serial Format**: `J202500001` (10 characters)
- **Execution Serial Format**: `J202500001.0001` (15 characters)  
- **Target Result Serial Format**: `J202500001.0001.0001` (20 characters)
- **Target Serial Format**: `T202500001` (10 characters)

## 📋 Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 80, 3000, 8000, 5432, 6379 available

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Copy environment file
cp env.example .env

# Edit environment variables if needed
nano .env
```

### 2. Start the Platform

**For Development (Recommended):**
```bash
# Use the official development startup script
./dev-start.sh

# Check that all services are running
./dev-status.sh
```

**For Production:**
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Access the Platform

**Primary Access (HTTPS with Login):**
- **Main Application**: https://localhost ⭐ **USE THIS FOR LOGIN**

**Development Access:**
- **React Dev Server**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Default Login

- **Username**: `admin`
- **Password**: `admin123`
- **Role**: Administrator

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
POSTGRES_DB=enabledrm
POSTGRES_USER=enabledrm
POSTGRES_PASSWORD=enabledrm_secure_password_2024

# Security
SECRET_KEY=dev-secret-key-2024
JWT_SECRET_KEY=dev-jwt-secret-2024

# Frontend API URLs (leave empty for relative URLs)
REACT_APP_API_URL=
REACT_APP_WS_URL=
```

### HTTPS Support

For HTTPS support in development:

1. **Change default passwords** in `.env`
2. **Generate secure secrets** for JWT and encryption
3. **Configure SSL/TLS** certificates
4. **Set up proper firewall rules**
5. **Configure backup strategies**

## 📚 API Documentation

### Authentication Endpoints

- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### User Management Endpoints (Admin Only)

- `GET /api/users/` - List all users
- `POST /api/users/` - Create new user
- `GET /api/users/{id}` - Get user by ID
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user (soft delete)

## 🔐 Security Features

### Authentication & Authorization
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Session management with automatic cleanup
- Password hashing with bcrypt

### Network Security
- CORS configuration
- Rate limiting on API endpoints
- Security headers (XSS protection, CSRF, etc.)
- Input validation and sanitization

### Data Security
- Encrypted credential storage
- Audit logging for all operations
- Immutable user session tracking

## 🏗️ Architecture Principles

### 1. Job-Centric Design
- Jobs are the central focus of the system
- All functionality supports job execution
- Immutable job history and audit trails

### 2. Universal Target Architecture
- Any system can be a target through communication methods
- Dynamic connection parameters (no hardcoded values)
- Support for SSH, HTTP, API, Database, etc.

### 3. No Hardcoded Network Configuration
- All network details come from database
- Environment variables for configuration
- Relative URLs in frontend code

### 4. Comprehensive Traceability
- Everything is logged with taxonomy-based categorization
- Performance metrics collection
- Immutable audit trails for compliance

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 80, 3000, 8000, 5432, 6379 are available
2. **Database connection**: Check PostgreSQL container is running
3. **Frontend not loading**: Verify React container is healthy
4. **Authentication issues**: Check JWT secrets in environment

### Logs and Debugging

```bash
# View all container logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Health Checks

```bash
# Check service health
curl http://localhost/health
curl http://localhost:8000/api/health

# Check database connection
docker-compose exec postgres psql -U enabledrm -d enabledrm -c "SELECT 1;"
```

## 📈 Monitoring

### Built-in Monitoring
- Container health checks
- API endpoint monitoring
- Database connection status
- User session tracking

### Logs
- Application logs in containers
- Nginx access/error logs
- Database query logs (when enabled)

## 🔄 Development

### 🚨 IMPORTANT: Development Environment Setup

**ALWAYS use the official development scripts for reliable service management:**

```bash
# Start development environment
./dev-start.sh

# Check service status  
./dev-status.sh

# Stop development environment
./dev-stop.sh
```

📖 **Read the complete guide**: [DEVELOPMENT_ENVIRONMENT_GUIDE.md](./DEVELOPMENT_ENVIRONMENT_GUIDE.md)

This guide contains **mandatory procedures** for:
- ✅ Proper startup/shutdown sequences
- ✅ React server management (screen-based)
- ✅ Service monitoring and troubleshooting
- ✅ Access points and login procedures

### Adding New Features

1. **Backend**: Add models, services, and routers in `backend/app/`
2. **Frontend**: Add components in `frontend/src/components/`
3. **Database**: Update models and run migrations
4. **Testing**: Add tests for new functionality

### Code Structure

```
├── backend/
│   ├── app/
│   │   ├── core/          # Configuration and security
│   │   ├── database/      # Database setup
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── contexts/      # React contexts
│   │   └── services/      # API services
│   └── package.json
├── database/
│   └── init/              # Database initialization
├── nginx/
│   └── nginx.conf         # Reverse proxy config
└── docker-compose.yml
```

## 📄 License

This project is proprietary software. All rights reserved.

## 🤝 Support

For support and questions:
- Check the troubleshooting section
- Review the architecture documentation
- Contact the development team

---

**ENABLEDRM Platform** - Universal Automation Orchestration 