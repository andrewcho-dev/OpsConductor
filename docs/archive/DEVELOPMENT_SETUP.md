# ENABLEDRM Development Setup

This guide provides multiple ways to run the ENABLEDRM development environment.

## 🚀 Quick Start (Recommended)

### Option 1: Simple Script-Based Setup
Use the provided scripts for the easiest development experience:

```bash
# Start the complete development environment
./dev-start.sh

# Check status of all services
./dev-status.sh

# Stop the development environment
./dev-stop.sh
```

### Option 2: Fully Containerized Setup
For a completely containerized development environment:

```bash
# Start all services including frontend in containers
docker compose -f docker-compose.dev.yml up -d

# Check status
docker compose -f docker-compose.dev.yml ps

# Stop all services
docker compose -f docker-compose.dev.yml down
```

### Option 3: Manual Setup (Current Method)
If you prefer manual control:

```bash
# Start backend services
docker compose up -d

# Start frontend separately
cd frontend && npm start
```

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js (v16 or higher)
- npm

## 🌐 Access URLs

After starting the development environment:

- **Frontend (Direct)**: http://localhost:3000
- **Frontend (HTTPS)**: https://localhost
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379

## 🔐 Default Login Credentials

- **Username**: `admin`
- **Password**: `admin123`

## 🛠️ Development Features

### Hot Reloading
- ✅ Frontend: Automatic browser refresh on code changes
- ✅ Backend: Automatic server restart on code changes
- ✅ No container rebuilds needed for code changes

### Volume Mounting
- Frontend source code is mounted for live editing
- Backend source code is mounted for live editing
- Database data persists between restarts

### HTTPS Support
- Self-signed SSL certificates included
- Nginx proxy provides HTTPS termination
- WebSocket support for hot reloading

## 📁 Project Structure

```
enabledrm/
├── backend/                 # FastAPI backend
├── frontend/               # React frontend
├── database/               # Database initialization scripts
├── nginx/                  # Nginx configuration
├── docker-compose.yml      # Current production-like setup
├── docker-compose.dev.yml  # Full containerized development
├── dev-start.sh           # Development startup script
├── dev-stop.sh            # Development stop script
└── dev-status.sh          # Development status checker
```

## 🔧 Troubleshooting

### Frontend Not Loading
```bash
# Check if React dev server is running
curl http://localhost:3000

# Check frontend logs
tail -f frontend-dev.log

# Restart frontend only
pkill -f "react-scripts start"
cd frontend && npm start
```

### Backend API Issues
```bash
# Check backend logs
docker compose logs -f backend

# Test backend directly
curl http://localhost:8000/health

# Restart backend
docker compose restart backend
```

### Database Connection Issues
```bash
# Check database status
docker compose exec postgres pg_isready -U enabledrm

# View database logs
docker compose logs -f postgres

# Reset database (WARNING: This will delete all data)
docker compose down -v
docker compose up -d
```

### SSL Certificate Issues
```bash
# Regenerate SSL certificates (if needed)
cd nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout enabledrm.key -out enabledrm.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

## 🚀 Production Deployment

For production deployment, use:

```bash
# Build and start production containers
docker compose -f docker-compose.prod.yml up -d
```

## 📝 Development Workflow

1. **Start Environment**: `./dev-start.sh`
2. **Make Changes**: Edit files in `frontend/src/` or `backend/app/`
3. **Test Changes**: Browser automatically refreshes, backend auto-reloads
4. **Check Status**: `./dev-status.sh`
5. **View Logs**: `tail -f frontend-dev.log` or `docker compose logs -f`
6. **Stop Environment**: `./dev-stop.sh`

## 🎯 Next Steps

- The admin user is automatically created on first startup
- Access the application at https://localhost
- Check the API documentation at http://localhost:8000/docs
- Monitor logs for any issues during development

## 🆘 Getting Help

If you encounter issues:

1. Run `./dev-status.sh` to check service status
2. Check logs: `docker compose logs -f`
3. Verify all prerequisites are installed
4. Ensure ports 3000, 8000, 5432, 6379, 80, and 443 are available