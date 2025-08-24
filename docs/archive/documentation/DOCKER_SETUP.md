# OpsConductor Docker Infrastructure

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose V2

### Development Setup
```bash
# 1. Run setup script
./setup.sh

# 2. Edit environment variables
nano .env

# 3. Start all services
docker compose up -d

# 4. Access OpsConductor
https://localhost
```

### Production Setup
```bash
# 1. Copy production environment template
cp .env.production .env

# 2. Edit production values (IMPORTANT!)
nano .env

# 3. Deploy production stack
docker compose -f docker-compose.prod.yml up -d

# 4. Access OpsConductor
https://your-domain.com
```

## 📋 Services Overview

| Service | Container Name | Purpose | Port |
|---------|----------------|---------|------|
| **nginx** | opsconductor-nginx | Reverse proxy, SSL termination | 80, 443 |
| **frontend** | opsconductor-frontend | React application | 3000 |
| **backend** | opsconductor-backend | FastAPI application | 8000 |

| **redis** | opsconductor-redis | Cache and message broker | 6379 |
| **celery-worker** | opsconductor-celery-worker | Background task processing | - |
| **scheduler** | opsconductor-scheduler | Scheduled task management | - |
| **prometheus** | opsconductor-prometheus | Metrics collection | 9090 |
| **grafana** | opsconductor-grafana | Monitoring dashboards | 3001 |

## 🔒 Security Features

### HTTPS Only
- All HTTP traffic redirected to HTTPS
- Self-signed certificates for development
- Production-ready SSL configuration

### Network Security
- Internal Docker network isolation
- No exposed database ports in production
- Rate limiting on API endpoints

### Container Security
- Non-root user execution
- Minimal base images (Alpine Linux)
- Security headers configured

## 🌐 URL Configuration

### Relative URLs Only
All frontend URLs are relative to support any domain:
- API: `/api`
- WebSocket: `/ws`
- Frontend: `/`

### CORS Configuration
Development: `https://localhost,https://127.0.0.1`
Production: Configure in `.env` file

## 📁 Volume Mounts

### Development
- `./backend:/app` - Hot reload for backend
- `./frontend:/app` - Hot reload for frontend
- `./backend/uploads:/app/uploads` - File uploads

### Production
- `./logs:/app/logs` - Application logs
- `./backend/uploads:/app/uploads` - File uploads
- Named volumes for data persistence

## 🔧 Environment Variables

### Required Variables
```bash
# Database
POSTGRES_DB=opsconductor_dev
POSTGRES_USER=opsconductor
POSTGRES_PASSWORD=secure_password

# Security
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret

# Network
CORS_ORIGINS=https://your-domain.com
```

### Optional Variables
```bash
# Performance
MAX_CONCURRENT_TARGETS=20
CONNECTION_TIMEOUT=30
COMMAND_TIMEOUT=300

# Monitoring
GRAFANA_ADMIN_PASSWORD=secure_password
```

## 🚀 Deployment Commands

### Development
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Rebuild and restart
docker compose up -d --build
```

### Production
```bash
# Deploy production stack
docker compose -f docker-compose.prod.yml up -d

# View production logs
docker compose -f docker-compose.prod.yml logs -f

# Update production deployment
docker compose -f docker-compose.prod.yml up -d --build
```

## 🔍 Health Checks

All services include health checks:
- **Backend**: `GET /health`
- **Frontend**: `GET /`
- **Database**: `pg_isready`
- **Redis**: `redis-cli ping`
- **Nginx**: `GET /health`

## 📊 Monitoring

### Prometheus Metrics
- Application metrics: `https://localhost/api/v1/monitoring/metrics`
- System health: `https://localhost/api/v1/monitoring/health`

### Grafana Dashboards
- Access: `https://localhost:3001`
- Default credentials: `admin` / `${GRAFANA_ADMIN_PASSWORD}`

## 🐛 Troubleshooting

### Common Issues

#### SSL Certificate Errors
```bash
# Regenerate certificates
rm nginx/ssl/*
./setup.sh
```

#### Permission Errors
```bash
# Fix permissions
sudo chown -R $USER:$USER .
chmod +x setup.sh
```

#### Container Won't Start
```bash
# Check logs
docker compose logs [service-name]

# Validate configuration
docker compose config
```

#### Database Connection Issues
```bash
# Check database status
docker compose exec postgres pg_isready -U opsconductor

# Reset database
docker compose down -v
docker compose up -d
```

### Log Locations
- Application logs: `./logs/`
- Nginx logs: `./logs/nginx/`
- Container logs: `docker compose logs [service]`

## 🔄 Updates and Maintenance

### Updating Services
```bash
# Pull latest images
docker compose pull

# Restart with new images
docker compose up -d
```

### Database Backups
```bash
# Create backup
docker compose exec postgres pg_dump -U opsconductor opsconductor_dev > backup.sql

# Restore backup
docker compose exec -T postgres psql -U opsconductor opsconductor_dev < backup.sql
```

### Cleaning Up
```bash
# Remove unused containers and images
docker system prune -a

# Remove all OpsConductor data (DESTRUCTIVE!)
docker compose down -v
docker volume prune
```

## 📞 Support

For issues with the Docker infrastructure:
1. Check this documentation
2. Review container logs
3. Validate configuration with `docker compose config`
4. Check system resources and Docker status