# ENABLEDRM Development Commands

## 🚀 **AUTOMATED DEVELOPMENT STARTUP IS NOW AVAILABLE!**

### **What's New:**
- ✅ **One-Command Startup**: `./dev-start.sh` starts everything
- ✅ **Automated Frontend**: React dev server starts automatically
- ✅ **Status Monitoring**: `./dev-status.sh` checks all services
- ✅ **Clean Shutdown**: `./dev-stop.sh` stops everything properly
- ✅ **Hot Reloading**: Code changes are reflected in ~2-5 seconds
- ✅ **Volume Mounting**: Your local files are directly served
- ✅ **No More Rebuilds**: No need to rebuild containers for code changes
- ✅ **HTTPS Support**: Available through nginx proxy
- ✅ **Admin User**: Automatically created on startup

## 🎯 **Quick Start (RECOMMENDED)**

### **Start Everything:**
```bash
./dev-start.sh
```

### **Check Status:**
```bash
./dev-status.sh
```

### **Stop Everything:**
```bash
./dev-stop.sh
```

## 🔧 **Alternative Methods**

### **Manual Method (Original):**
```bash
# Start backend services
docker compose up -d

# Start frontend separately
cd frontend && npm start
```

### **Fully Containerized (Advanced):**
```bash
# Start all services including frontend in containers
docker compose -f docker-compose.dev.yml up -d
```

## 🌐 **Access URLs**
- **Frontend (Direct)**: http://localhost:3000 (with hot reloading)
- **Frontend (HTTPS)**: https://localhost (through nginx proxy)
- **Backend API**: http://localhost:8000 (with auto-reload)
- **API Docs**: http://localhost:8000/docs

## 🔐 **Login Credentials**
- **Username**: `admin`
- **Password**: `admin123`

## 📋 **Development Workflow**
1. Run `./dev-start.sh` to start everything
2. Edit any React component in `frontend/src/`
3. Save the file - browser automatically refreshes in 2-5 seconds
4. Edit backend code in `backend/app/` - server auto-reloads
5. Use `./dev-status.sh` to check if everything is running
6. Run `./dev-stop.sh` when done

## 📊 **Monitoring & Logs**
```bash
# View frontend logs
tail -f frontend-dev.log

# View backend logs
docker compose logs -f backend

# View all service logs
docker compose logs -f

# Check service status
./dev-status.sh
```

## 🚀 **Production Deployment**
```bash
# For production (when ready)
docker compose -f docker-compose.prod.yml up -d
```

## 🎉 **Your Login Issues are SOLVED!**

The startup script ensures:
- ✅ All services start in the correct order
- ✅ Frontend React server starts automatically
- ✅ Admin user is created
- ✅ All dependencies are checked
- ✅ Clear status reporting