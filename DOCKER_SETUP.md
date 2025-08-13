# EnableDRM - Docker Environment Setup

## 🚀 Quick Start

```bash
# Start all services with HTTPS
docker-compose up -d

# Access the application
https://192.168.50.100
```

## 📁 File Structure

```
enabledrm/
├── .env                          # Main environment configuration
├── docker-compose.yml           # ONLY compose file (no confusion!)
├── backend/
│   ├── Dockerfile               # Production build
│   └── Dockerfile.dev           # Development build (used)
├── frontend/
│   ├── Dockerfile               # Production build  
│   ├── Dockerfile.dev           # Development build (used)
│   └── .env.local               # React dev server settings
└── nginx/
    ├── nginx.conf               # ONLY nginx config (HTTPS enabled)
    └── ssl/                     # SSL certificates
        ├── cert.pem
        └── key.pem
```

## 🔧 Configuration Files

### `.env` - Main Configuration
- Database settings (PostgreSQL)
- Redis cache settings
- JWT security keys
- Port configurations
- Job execution settings

### `docker-compose.yml` - Service Orchestration
- PostgreSQL database
- Redis cache
- FastAPI backend (development mode)
- React frontend (development mode)
- Celery worker & scheduler
- Nginx reverse proxy with SSL

### `nginx/nginx.conf` - Reverse Proxy
- HTTPS with SSL termination
- HTTP to HTTPS redirect
- API routing (/api → backend)
- WebSocket support (/ws → backend)
- Static file serving (/ → frontend)

## 🌐 Network Architecture

```
Internet → Nginx (HTTPS:443) → Services
                ↓
            ┌─────────────────┐
            │ /api → Backend  │ (FastAPI)
            │ /ws → Backend   │ (WebSocket)
            │ / → Frontend    │ (React)
            └─────────────────┘
```

## 🔒 Security Features

- **HTTPS Only**: HTTP redirects to HTTPS
- **SSL Termination**: Nginx handles SSL
- **Rate Limiting**: API and auth endpoints protected
- **Security Headers**: XSS, CSRF, clickjacking protection
- **CORS**: Configured for development

## 🛠️ Development vs Production

### Development (Current)
- Hot reload enabled
- Source maps disabled for performance
- All ports exposed for debugging
- Volume mounts for live code changes

### Production
- Optimized builds
- No hot reload
- Only nginx ports exposed
- Static file serving

## 📊 Service Ports

| Service    | Internal Port | External Port | Purpose |
|------------|---------------|---------------|---------|
| Nginx      | 80/443        | 80/443        | HTTPS proxy |
| Frontend   | 3000          | -             | React dev server |
| Backend    | 8000          | -             | FastAPI |
| PostgreSQL | 5432          | 5432*         | Database |
| Redis      | 6379          | 6379*         | Cache |

*Exposed for development/debugging only

## 🔄 Common Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Restart a service
docker-compose restart [service-name]

# Stop all services
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Clean everything
docker-compose down -v --remove-orphans
```

## ✅ Health Checks

All services have health checks:
- **Nginx**: `curl -f http://localhost/health`
- **Backend**: `curl -f http://localhost:8000/health`
- **Frontend**: `curl -f http://localhost:3000`
- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`

## 🚨 Troubleshooting

### SSL Certificate Issues
```bash
# Check certificates
ls -la nginx/ssl/
# Should see: cert.pem, key.pem
```

### Service Not Starting
```bash
# Check logs
docker-compose logs [service-name]

# Check health
docker-compose ps
```

### Port Conflicts
- Only ports 80, 443, 5432, 6379 should be exposed
- If conflicts occur, change ports in `.env`