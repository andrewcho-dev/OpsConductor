# OpsConductor Deployment Guide

This guide covers deploying OpsConductor in production environments.

## 🎯 Production Deployment

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ recommended  
- **Storage**: 50GB+ for database and logs
- **Network**: Outbound access for target connections
- **OS**: Linux (Ubuntu 20.04+ recommended)

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- SSL certificates (for HTTPS)

## 🚀 Quick Production Setup

### 1. Environment Configuration
```bash
# Copy production environment template
cp .env.production .env

# Edit with your production values
nano .env
```

### 2. Required Environment Variables
```bash
# Domain Configuration
DOMAIN_NAME=your-domain.com

# Database Security
POSTGRES_PASSWORD=your-secure-postgres-password-here

# Application Security  
SECRET_KEY=your-very-secure-secret-key-here-minimum-32-characters
JWT_SECRET_KEY=your-jwt-secret-key-here-minimum-32-characters

# Monitoring
GRAFANA_PASSWORD=your-secure-grafana-password-here
```

### 3. SSL Certificate Setup
```bash
# Place your SSL certificates in nginx/ssl/
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem

# Or generate self-signed certificates for testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

### 4. Deploy Services
```bash
# Start production environment
docker-compose -f docker-compose.prod.yml up -d

# Verify all services are running
docker-compose -f docker-compose.prod.yml ps
```

### 5. Initial Setup
```bash
# Create admin user
docker exec -it opsconductor-backend-prod python create_admin_user.py

# Verify application is accessible
curl -k https://your-domain.com/health
```

## 🔧 Configuration Options

### Database Configuration
```bash
# External PostgreSQL (optional)
DATABASE_URL=postgresql://user:password@external-db:5432/opsconductor

# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

### Performance Tuning
```bash
# Worker processes
WORKER_PROCESSES=4
WORKER_CONNECTIONS=1000

# Cache settings
CACHE_TTL_DEFAULT=300
CACHE_TTL_LONG=3600

# Job execution limits
MAX_CONCURRENT_TARGETS=50
CONNECTION_TIMEOUT=30
COMMAND_TIMEOUT=600
```

### Security Settings
```bash
# Allowed hosts
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
```

## 📊 Monitoring Setup

### Built-in Monitoring Stack
The production deployment includes:
- **Prometheus** - Metrics collection (port 9090)
- **Grafana** - Dashboards and alerting (port 3001)

### Access Monitoring
```bash
# Grafana dashboard
https://your-domain.com:3001
# Username: admin
# Password: ${GRAFANA_PASSWORD}

# Prometheus metrics
https://your-domain.com:9090
```

### Custom Alerts
Configure alerts in `monitoring/prometheus.yml`:
```yaml
rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

## 🔒 Security Hardening

### Network Security
```bash
# Firewall configuration (UFW example)
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable

# Optional: Restrict monitoring ports
ufw allow from trusted-ip to any port 9090  # Prometheus
ufw allow from trusted-ip to any port 3001  # Grafana
```

### SSL/TLS Configuration
Update `nginx/nginx.conf` for enhanced security:
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
add_header Strict-Transport-Security "max-age=63072000" always;
```

### Database Security
```bash
# Use strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Enable SSL for database connections
DATABASE_URL=postgresql://user:password@postgres:5432/opsconductor?sslmode=require
```

## 💾 Backup & Recovery

### Database Backup
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

docker exec opsconductor-postgres-prod pg_dump -U opsconductor opsconductor > \
  ${BACKUP_DIR}/opsconductor_${DATE}.sql

# Compress and rotate backups
gzip ${BACKUP_DIR}/opsconductor_${DATE}.sql
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete
```

### Configuration Backup
```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  .env nginx/ monitoring/ docker-compose.prod.yml
```

### Recovery Procedure
```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore database
gunzip -c backup.sql.gz | docker exec -i opsconductor-postgres-prod \
  psql -U opsconductor -d opsconductor

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart services with new images
docker-compose -f docker-compose.prod.yml up -d
```

### Database Migrations
```bash
# Run pending migrations
docker exec -it opsconductor-backend-prod alembic upgrade head
```

### Log Management
```bash
# Configure log rotation in /etc/logrotate.d/opsconductor
/home/opsconductor/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 root root
}
```

## 🚨 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service logs
docker-compose -f docker-compose.prod.yml logs backend

# Check system resources
docker stats
df -h
```

#### Database Connection Issues
```bash
# Test database connectivity
docker exec -it opsconductor-postgres-prod psql -U opsconductor -d opsconductor -c "SELECT 1;"

# Check database logs
docker logs opsconductor-postgres-prod
```

#### SSL Certificate Issues
```bash
# Verify certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Test SSL configuration
openssl s_client -connect your-domain.com:443
```

### Health Checks
```bash
# Application health
curl -k https://your-domain.com/health

# Service status
docker-compose -f docker-compose.prod.yml ps

# Resource usage
docker stats --no-stream
```

## 📞 Support

For production deployment support:
1. Check application logs: `docker-compose logs`
2. Review system metrics in Grafana
3. Consult the troubleshooting section
4. Create an issue on GitHub with logs and configuration details

---

**OpsConductor** - Enterprise-ready automation platform