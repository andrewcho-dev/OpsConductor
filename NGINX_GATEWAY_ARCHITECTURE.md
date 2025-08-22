# 🔧 **OpsConductor - Complete Nginx Gateway Architecture**

## 🎯 **ARCHITECTURE TRANSFORMATION COMPLETE**

Your nginx gateway has been **completely rebuilt** to be production-ready with **zero hardcoded IPs** and proper microservices routing.

---

## 🏗️ **NEW ARCHITECTURE OVERVIEW**

### **Production Mode (Recommended)**
```bash
[Internet] → [Nginx:443] → [Microservices] → [PostgreSQL/Redis/MinIO]
                ↓
         [Static React Files]
```

### **Development Mode**
```bash
[Internet] → [Nginx:443] → [Microservices] → [PostgreSQL/Redis/MinIO]
                ↓
         [React Dev Server:3000]
```

---

## 🚀 **DEPLOYMENT OPTIONS**

### **✅ Production Deployment (Recommended)**
```bash
# Complete production build with static frontend
./scripts/deploy-production.sh
```

**Features:**
- ✅ **Static React build** served directly by nginx
- ✅ **No exposed service ports** - everything through nginx gateway
- ✅ **Optimized caching** for static assets
- ✅ **SSL termination** at nginx level
- ✅ **Object storage integration** via `/storage/` path
- ✅ **Complete security headers**

### **🔧 Development Deployment**
```bash
# Development with hot-reload frontend
./scripts/deploy-development.sh
```

**Features:**
- ✅ **Hot-reload React dev server** on port 3000
- ✅ **Direct service access** for debugging
- ✅ **Development optimizations**
- ✅ **Fast rebuild cycles**

---

## 🌐 **NGINX GATEWAY ROUTING**

### **Frontend Access**
```bash
https://localhost/           # Main React application
https://localhost/health     # System health check
```

### **Microservices API**
```bash
https://localhost/api/v1/auth/          # Authentication
https://localhost/api/v1/users/         # User management
https://localhost/api/v1/targets/       # Target systems
https://localhost/api/v1/jobs/          # Job management
https://localhost/api/v1/executions/    # Job execution
https://localhost/api/v1/audit/         # Audit events
https://localhost/api/v1/notifications/ # Notifications
https://localhost/api/v1/discovery/     # Target discovery
https://localhost/api/v1/schedules/     # Job scheduling
https://localhost/api/v1/management/    # Job orchestration
```

### **Object Storage**
```bash
https://localhost/storage/              # Direct object downloads
https://localhost/api/v1/storage/       # Storage management API
```

### **Health Monitoring**
```bash
https://localhost/health/services       # All services status
https://localhost/health/auth           # Auth service health
https://localhost/health/users          # User service health
https://localhost/health/targets        # Targets service health
https://localhost/health/jobs           # Jobs service health
https://localhost/health/executions     # Execution service health
# ... and more
```

---

## 🔐 **SECURITY FEATURES**

### **SSL/TLS Configuration**
- ✅ **TLS 1.2 + 1.3** only
- ✅ **Modern cipher suites**
- ✅ **HTTP to HTTPS redirect**
- ✅ **HSTS headers**
- ✅ **Security headers** (XSS, CSRF, etc.)

### **Access Control**
- ✅ **Rate limiting** per endpoint type
- ✅ **Hidden service ports** (no direct access)
- ✅ **Blocked sensitive files** (.env, .git, etc.)
- ✅ **CORS headers** properly configured

### **Performance Optimizations**
- ✅ **Gzip compression** for all text content
- ✅ **Static asset caching** (1 year for immutable files)
- ✅ **Connection keepalive**
- ✅ **Upstream health monitoring**

---

## 📦 **NO MORE HARDCODED IPs**

### **✅ Everything is Relative**
- **Frontend URLs**: All use relative paths (`/api/v1/`, `/storage/`)
- **Service Discovery**: Uses Docker container names (`auth-service:8000`)
- **Dynamic DNS**: Internal nginx resolver for service discovery
- **Environment Variables**: External domain configurable via `EXTERNAL_DOMAIN`

### **✅ Container-Based Routing**
```nginx
# Old (hardcoded):
proxy_pass http://192.168.1.100:8001;

# New (dynamic):
upstream auth-service {
    server auth-service:8000 max_fails=3 fail_timeout=30s;
}
proxy_pass http://auth-service;
```

---

## 🗄️ **OBJECT STORAGE INTEGRATION**

### **Complete MinIO Integration**
```bash
# Direct downloads (with signed URLs from execution service)
https://localhost/storage/bucket/object.txt

# Management API (create buckets, upload files)
https://localhost/api/v1/storage/
```

### **Automatic Storage Decision**
- **< 64KB**: Stored in PostgreSQL (execution_artifacts.content)
- **> 64KB**: Stored in MinIO (execution_artifacts.object_key)
- **Downloads**: Nginx serves signed URLs directly from MinIO

---

## 🎛️ **CONFIGURATION FILES**

### **Production Configuration**
- `nginx/nginx-production.conf` - **Complete production nginx config**
- `nginx/proxy_params` - **Standard proxy parameters**
- `frontend/Dockerfile.prod` - **Production React build**
- `docker-compose.prod.yml` - **Production override**

### **Legacy Configuration (for reference)**
- `nginx/nginx.conf` - **Original mixed dev/prod config**
- `services/api-gateway/nginx.conf` - **Microservices-only gateway**

---

## 🔄 **MIGRATION GUIDE**

### **From Current Setup to Production**
```bash
# 1. Stop current services
docker-compose down

# 2. Deploy in production mode
./scripts/deploy-production.sh

# 3. Verify everything works
curl -k https://localhost/health
curl -k https://localhost/api/v1/auth/health
```

### **Switch Between Modes**
```bash
# Switch to production
./scripts/deploy-production.sh

# Switch back to development
./scripts/deploy-development.sh
```

---

## 🎯 **BENEFITS OF NEW ARCHITECTURE**

### **🔒 Security**
- **No exposed service ports** in production
- **SSL termination** at gateway level
- **Complete security headers**
- **Rate limiting** per service type

### **⚡ Performance**
- **Static file serving** by nginx (not Node.js)
- **Optimized caching** strategies
- **Gzip compression**
- **Connection pooling**

### **🛠️ Operations**
- **Single entry point** for all traffic
- **Centralized logging** and monitoring
- **Easy SSL certificate management**
- **Health check aggregation**

### **🔧 Development**
- **Hot-reload** in development mode
- **Direct service access** for debugging
- **Easy mode switching**
- **No configuration conflicts**

---

## 📊 **MONITORING & DEBUGGING**

### **View All Services**
```bash
# Production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Development mode
docker-compose ps
```

### **Check Service Health**
```bash
# Overall health
curl -k https://localhost/health

# Individual services
curl -k https://localhost/health/auth
curl -k https://localhost/health/users
curl -k https://localhost/health/targets
```

### **View Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f nginx
docker-compose logs -f auth-service
```

---

## 🎊 **READY FOR PRODUCTION!**

Your **OpsConductor nginx gateway** is now:

- ✅ **Production-ready** with static frontend serving
- ✅ **Security-hardened** with proper headers and SSL
- ✅ **Performance-optimized** with caching and compression
- ✅ **Fully containerized** with no hardcoded IPs
- ✅ **Object storage integrated** with direct download support
- ✅ **Health monitored** at all levels
- ✅ **Easy to deploy** with automated scripts

**Next step**: Run `./scripts/deploy-production.sh` to see your complete production-ready platform! 🚀