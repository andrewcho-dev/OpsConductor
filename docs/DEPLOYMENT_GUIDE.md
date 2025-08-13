# EnableDRM Deployment Guide

## Overview

This guide covers deploying EnableDRM with the complete execution serialization system in production environments.

## Prerequisites

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ recommended
- **Storage**: 50GB+ for database and logs
- **Network**: Outbound access for target connections

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 13+ (if using external database)
- Redis 6+ (if using external cache)

## Production Deployment

### 1. Environment Configuration

Create production environment file:
```bash
# .env.production
# Database Configuration
DATABASE_URL=postgresql://enabledrm:secure_password@postgres:5432/enabledrm
POSTGRES_USER=enabledrm
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=enabledrm

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security Configuration
SECRET_KEY=your-super-secure-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Configuration
ENVIRONMENT=production
DEBUG=false
API_V1_STR=/api
PROJECT_NAME=EnableDRM

# Execution Configuration
MAX_CONCURRENT_TARGETS=50
CONNECTION_TIMEOUT=30
COMMAND_TIMEOUT=300

# Serialization Configuration
SERIAL_YEAR_DIGITS=4
SERIAL_SEQUENCE_DIGITS=5
EXECUTION_SEQUENCE_DIGITS=4
BRANCH_SEQUENCE_DIGITS=4
```

### 2. Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENVIRONMENT=${ENVIRONMENT}
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/ssl/certs
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
    restart: unless-stopped

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.core.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.core.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 3. Database Migration and Setup

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Starting EnableDRM Production Deployment"

# Create necessary directories
mkdir -p logs uploads backups ssl

# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Build custom images
docker-compose -f docker-compose.prod.yml build

# Start database services first
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 30

# Run database migrations
echo "📊 Running database migrations..."
docker-compose -f docker-compose.prod.yml exec postgres psql -U enabledrm -d enabledrm -f /backups/schema.sql

# Apply execution serialization migration
echo "🔢 Applying execution serialization migration..."
docker-compose -f docker-compose.prod.yml exec postgres psql -U enabledrm -d enabledrm < migrations/add_execution_serialization.sql

# Start all services
echo "🏃 Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 60

# Populate execution serials for existing data
echo "📝 Populating execution serials..."
docker-compose -f docker-compose.prod.yml exec backend python scripts/populate_execution_serials.py

# Create admin user
echo "👤 Creating admin user..."
docker-compose -f docker-compose.prod.yml exec backend python create_admin_user.py

echo "✅ Deployment completed successfully!"
echo "🌐 Frontend: http://localhost"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"
```

### 4. Production Dockerfile for Backend

```dockerfile
# backend/Dockerfile.prod
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R app:app /app

# Switch to app user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 5. Nginx Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/ssl/certs/cert.pem;
        ssl_certificate_key /etc/ssl/certs/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # Frontend static files
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Authentication endpoints (stricter rate limiting)
        location /api/auth/ {
            limit_req zone=login burst=5 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket support for real-time updates
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## Database Optimization

### 1. PostgreSQL Configuration

```sql
-- postgresql.conf optimizations
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200

-- Enable query logging for performance monitoring
log_statement = 'mod'
log_min_duration_statement = 1000
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

### 2. Execution Serialization Indexes

```sql
-- Optimized indexes for execution serialization
CREATE INDEX CONCURRENTLY idx_job_serial_year 
ON jobs USING btree (substring(job_serial, 2, 4));

CREATE INDEX CONCURRENTLY idx_execution_serial_job 
ON job_executions USING btree (substring(execution_serial, 1, 9));

CREATE INDEX CONCURRENTLY idx_branch_serial_execution 
ON job_execution_branches USING btree (substring(branch_serial, 1, 14));

CREATE INDEX CONCURRENTLY idx_target_serial_ref_performance 
ON job_execution_branches (target_serial_ref, created_at, status);

-- Partial indexes for active executions
CREATE INDEX CONCURRENTLY idx_active_executions 
ON job_executions (execution_serial) 
WHERE status IN ('running', 'scheduled');

CREATE INDEX CONCURRENTLY idx_active_branches 
ON job_execution_branches (branch_serial, status) 
WHERE status IN ('running', 'scheduled');
```

### 3. Database Partitioning

```sql
-- Partition job_executions by year for better performance
CREATE TABLE job_executions_2025 PARTITION OF job_executions
FOR VALUES FROM ('J2025') TO ('J2026');

CREATE TABLE job_executions_2026 PARTITION OF job_executions
FOR VALUES FROM ('J2026') TO ('J2027');

-- Partition job_execution_branches by year
CREATE TABLE job_execution_branches_2025 PARTITION OF job_execution_branches
FOR VALUES FROM ('J2025') TO ('J2026');

CREATE TABLE job_execution_branches_2026 PARTITION OF job_execution_branches
FOR VALUES FROM ('J2026') TO ('J2027');
```

## Monitoring and Logging

### 1. Application Monitoring

```python
# monitoring.py
import logging
import time
from functools import wraps
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
execution_counter = Counter('enabledrm_executions_total', 'Total executions', ['status'])
execution_duration = Histogram('enabledrm_execution_duration_seconds', 'Execution duration')
serial_generation_counter = Counter('enabledrm_serials_generated_total', 'Serials generated', ['type'])

def monitor_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_counter.labels(status='success').inc()
            return result
        except Exception as e:
            execution_counter.labels(status='error').inc()
            raise
        finally:
            duration = time.time() - start_time
            execution_duration.observe(duration)
    return wrapper

def monitor_serial_generation(serial_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            serial_generation_counter.labels(type=serial_type).inc()
            return result
        return wrapper
    return decorator
```

### 2. Structured Logging

```python
# logging_config.py
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add execution context if available
        if hasattr(record, 'execution_serial'):
            log_entry['execution_serial'] = record.execution_serial
        if hasattr(record, 'job_serial'):
            log_entry['job_serial'] = record.job_serial
        if hasattr(record, 'target_serial'):
            log_entry['target_serial'] = record.target_serial
            
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('/app/logs/enabledrm.log'),
        logging.StreamHandler()
    ]
)

# Set structured formatter
for handler in logging.root.handlers:
    handler.setFormatter(StructuredFormatter())
```

### 3. Health Checks

```python
# health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.serial_service import SerialService

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check including serialization system"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database connectivity
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Serial service functionality
    try:
        # Test serial validation
        test_job_serial = "J20250001"
        test_execution_serial = "J20250001.0001"
        test_branch_serial = "J20250001.0001.0001"
        
        assert SerialService.validate_job_serial(test_job_serial)
        assert SerialService.validate_execution_serial(test_execution_serial)
        assert SerialService.validate_branch_serial(test_branch_serial)
        
        health_status["checks"]["serialization"] = "healthy"
    except Exception as e:
        health_status["checks"]["serialization"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis connectivity (if configured)
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status
```

## Backup and Recovery

### 1. Database Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="enabledrm"

# Create backup directory
mkdir -p $BACKUP_DIR

# Full database backup
echo "Creating full database backup..."
docker exec enabledrm-postgres pg_dump -U enabledrm -d $DB_NAME > $BACKUP_DIR/full_backup_$TIMESTAMP.sql

# Execution data backup (for serialization recovery)
echo "Creating execution serialization backup..."
docker exec enabledrm-postgres pg_dump -U enabledrm -d $DB_NAME \
  --table=jobs \
  --table=job_executions \
  --table=job_execution_branches \
  --table=universal_targets \
  > $BACKUP_DIR/execution_serials_$TIMESTAMP.sql

# Compress backups
gzip $BACKUP_DIR/full_backup_$TIMESTAMP.sql
gzip $BACKUP_DIR/execution_serials_$TIMESTAMP.sql

# Clean old backups (keep last 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

### 2. Recovery Procedures

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
DB_NAME="enabledrm"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Restoring database from $BACKUP_FILE..."

# Stop application services
docker-compose -f docker-compose.prod.yml stop backend celery celery-beat

# Restore database
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | docker exec -i enabledrm-postgres psql -U enabledrm -d $DB_NAME
else
    docker exec -i enabledrm-postgres psql -U enabledrm -d $DB_NAME < $BACKUP_FILE
fi

# Verify serialization integrity
echo "Verifying execution serialization integrity..."
docker exec enabledrm-postgres psql -U enabledrm -d $DB_NAME -c "
SELECT 
    COUNT(*) as total_executions,
    COUNT(execution_serial) as serialized_executions,
    COUNT(*) - COUNT(execution_serial) as missing_serials
FROM job_executions;
"

# Restart services
docker-compose -f docker-compose.prod.yml start backend celery celery-beat

echo "Database restore completed"
```

## Security Hardening

### 1. SSL/TLS Configuration

```bash
# Generate SSL certificates (for production, use proper CA-signed certificates)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"
```

### 2. Firewall Configuration

```bash
# UFW firewall rules
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 3. Docker Security

```yaml
# docker-compose.security.yml
version: '3.8'

services:
  backend:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

## Performance Tuning

### 1. Connection Pooling

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 2. Redis Configuration

```redis
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 3. Application Optimization

```python
# Async execution for better performance
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def execute_job_async(job_id: int, target_ids: List[int]):
    """Execute job asynchronously across multiple targets"""
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        tasks = []
        for target_id in target_ids:
            task = asyncio.get_event_loop().run_in_executor(
                executor, execute_on_target, job_id, target_id
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

This deployment guide provides comprehensive coverage for deploying EnableDRM with the execution serialization system in production environments, including security, monitoring, backup, and performance considerations.