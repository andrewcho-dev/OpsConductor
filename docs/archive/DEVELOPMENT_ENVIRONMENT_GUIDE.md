# ENABLEDRM Development Environment Guide

## 🚀 OFFICIAL STARTUP AND SHUTDOWN PROCEDURES

This document contains the **OFFICIAL** and **MANDATORY** procedures for starting and stopping the ENABLEDRM development environment. These procedures have been tested and verified to work correctly.

---

## ⚠️ CRITICAL RULES - ALWAYS FOLLOW THESE

### 1. **ALWAYS USE THE PROVIDED SCRIPTS**
- ✅ **DO**: Use `./dev-start.sh` to start the environment
- ✅ **DO**: Use `./dev-stop.sh` to stop the environment  
- ✅ **DO**: Use `./dev-status.sh` to check status
- ❌ **DON'T**: Start services manually with docker compose
- ❌ **DON'T**: Start React server manually with npm start
- ❌ **DON'T**: Kill processes manually unless absolutely necessary

### 2. **STARTUP SEQUENCE - MANDATORY ORDER**
```bash
# 1. Navigate to project root
cd /home/enabledrm

# 2. Start the complete environment
./dev-start.sh

# 3. Wait for completion message
# Look for: "✅ Development environment is ready! 🚀"

# 4. Verify all services are running
./dev-status.sh
```

### 3. **SHUTDOWN SEQUENCE - MANDATORY ORDER**
```bash
# 1. Navigate to project root
cd /home/enabledrm

# 2. Stop the complete environment
./dev-stop.sh

# 3. Wait for completion message
# Look for: "✅ ENABLEDRM Development Environment Stopped! 🛑"
```

---

## 🔧 TECHNICAL IMPLEMENTATION DETAILS

### React Server Management
The React development server uses a **screen-based approach** for reliable background execution:

- **Screen Session**: `react-dev` (detached)
- **Process Management**: Automatic PID tracking in `.react-dev-pid`
- **Logging**: Real-time logs in `frontend-dev.log`
- **Port**: 3000 (development server)

### Service Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    ENABLEDRM Services                       │
├─────────────────────────────────────────────────────────────┤
│ Frontend (React)     │ http://localhost:3000               │
│ Backend API          │ http://localhost:8000               │
│ Main App (HTTPS)     │ https://localhost                   │
│ Database (PostgreSQL)│ localhost:5432                      │
│ Redis Cache          │ localhost:6379                      │
│ Nginx Proxy          │ 80/443                              │
├─────────────────────────────────────────────────────────────┤
│ Docker Services: backend, postgres, redis, nginx,          │
│                 scheduler, celery-worker                    │
│ Screen Session:  react-dev (React development server)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 STANDARD OPERATING PROCEDURES

### Daily Development Workflow

#### Starting Work Session
```bash
cd /home/enabledrm
./dev-start.sh
# Wait for: "✅ Development environment is ready! 🚀"
./dev-status.sh  # Verify all services are green ✅
```

#### During Development
```bash
# Check service status anytime
./dev-status.sh

# View React logs in real-time
screen -r react-dev
# Press Ctrl+A, then D to detach

# View React logs from file
tail -f frontend-dev.log

# View backend logs
docker compose logs -f backend
```

#### Ending Work Session
```bash
cd /home/enabledrm
./dev-stop.sh
# Wait for: "✅ ENABLEDRM Development Environment Stopped! 🛑"
```

### Troubleshooting Procedures

#### If Services Don't Start Properly
```bash
# 1. Stop everything first
./dev-stop.sh

# 2. Wait 10 seconds
sleep 10

# 3. Start again
./dev-start.sh

# 4. Check status
./dev-status.sh
```

#### If React Server Issues Occur
```bash
# Check if screen session exists
screen -list

# Attach to React session to see errors
screen -r react-dev

# If needed, restart just the React server
screen -S react-dev -X quit
cd frontend
screen -dmS react-dev bash -c "npm start 2>&1 | tee ../frontend-dev.log"
cd ..
```

#### Emergency Reset
```bash
# Nuclear option - only if everything is broken
./dev-stop.sh
docker system prune -f
pkill -f "react-scripts start"
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
screen -S react-dev -X quit 2>/dev/null || true
./dev-start.sh
```

---

## 🌐 ACCESS POINTS

### Primary Access (ALWAYS USE FOR LOGIN)
- **URL**: https://localhost
- **Purpose**: Main application with HTTPS proxy
- **Login**: admin / admin123

### Development Access
- **React Dev Server**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Service Monitoring
- **Status Check**: `./dev-status.sh`
- **All Logs**: `docker compose logs -f`
- **React Logs**: `tail -f frontend-dev.log` or `screen -r react-dev`

---

## 🚨 CRITICAL SUCCESS INDICATORS

### Startup Success Checklist
After running `./dev-start.sh`, verify these indicators:

```bash
./dev-status.sh
```

**ALL of these must show ✅:**
- ✅ React dev server is running on http://localhost:3000
- ✅ React process found (PID: XXXXX)
- ✅ Backend API is responding on http://localhost:8000
- ✅ Nginx proxy is working on https://localhost
- ✅ PostgreSQL database is ready
- ✅ Redis is responding
- ✅ Login endpoint is working (HTTP 200)

### Login Test
```bash
# This should return HTTP 200
curl -k -s -w "%{http_code}" -X POST "https://localhost/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}' \
    -o /dev/null
```

---

## 📝 MAINTENANCE NOTES

### Log File Management
- `frontend-dev.log`: React development server logs
- Docker logs: `docker compose logs [service_name]`
- Screen session: `screen -r react-dev`

### Process Management
- React PID stored in: `.react-dev-pid`
- Screen session name: `react-dev`
- Docker services managed by: `docker compose`

### Port Usage
- 3000: React development server
- 8000: Backend API
- 80/443: Nginx proxy
- 5432: PostgreSQL
- 6379: Redis

---

## 🔒 SECURITY NOTES

### Default Credentials
- **Username**: admin
- **Password**: admin123
- **Change these in production!**

### HTTPS Certificate
- Self-signed certificate for development
- Located in: `nginx/ssl/`
- Browser will show security warning (normal for dev)

---

## 📞 SUPPORT INFORMATION

### If Scripts Fail
1. Check you're in the correct directory: `/home/enabledrm`
2. Verify Docker is running: `docker info`
3. Check Node.js is installed: `node --version`
4. Check npm is installed: `npm --version`
5. Verify screen is available: `which screen`

### Common Issues and Solutions
1. **Port 3000 in use**: The scripts handle this automatically
2. **Docker not running**: Start Docker service first
3. **Permission denied**: Check file permissions on scripts
4. **Screen not found**: Install screen: `sudo apt-get install screen`

---

## 📋 SCRIPT MODIFICATION RULES

### ⚠️ WARNING: SCRIPT MODIFICATION RESTRICTIONS

**NEVER modify these scripts without understanding the full impact:**
- `dev-start.sh`: Contains critical React server startup logic
- `dev-stop.sh`: Contains proper cleanup procedures
- `dev-status.sh`: Service health checking logic

**If modifications are needed:**
1. Create a backup first
2. Test thoroughly in a separate environment
3. Document all changes
4. Update this guide accordingly

---

## 🎯 FINAL CHECKLIST

Before considering the environment "ready":

- [ ] `./dev-start.sh` completed successfully
- [ ] `./dev-status.sh` shows all ✅ green checkmarks
- [ ] https://localhost loads the login page
- [ ] Can login with admin/admin123
- [ ] React dev server accessible at http://localhost:3000
- [ ] Backend API docs accessible at http://localhost:8000/docs

**Only when ALL items are checked, the environment is ready for development.**

---

*This guide was created to ensure reliable and consistent development environment management. Always follow these procedures to avoid service startup issues.*

**Last Updated**: August 8, 2025
**Version**: 1.0 (Screen-based React server implementation)