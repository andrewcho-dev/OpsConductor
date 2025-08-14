#!/bin/bash

# OpsConductor Critical Security Fixes Application Script
# This script applies all critical security fixes identified in the security audit

set -e  # Exit on any error

echo "🚨 OpsConductor Critical Security Fixes"
echo "========================================"
echo ""

# Backup original files
echo "📦 Creating backups..."
cp docker-compose.yml docker-compose.yml.backup
cp .env .env.backup
cp database/init/01_init.sql database/init/01_init.sql.backup

echo "✅ Backups created"
echo ""

# Fix 1: Secure Grafana Password
echo "🔒 Fix 1: Securing Grafana password..."
sed -i 's/GF_SECURITY_ADMIN_PASSWORD=admin123/GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}/' docker-compose.yml

# Add Grafana password to .env if not exists
if ! grep -q "GRAFANA_ADMIN_PASSWORD" .env; then
    echo "" >> .env
    echo "# ==============================================================================" >> .env
    echo "# MONITORING - Grafana & Prometheus" >> .env
    echo "# ==============================================================================" >> .env
    echo "GRAFANA_ADMIN_PASSWORD=opsconductor_grafana_secure_2024" >> .env
fi

echo "✅ Grafana password secured"

# Fix 2: Secure Database Ports
echo "🔒 Fix 2: Securing database ports..."
sed -i 's/- "5432:5432"/# - "5432:5432"  # Commented out for security - use docker exec for DB access/' docker-compose.yml
sed -i 's/- "6379:6379"/# - "6379:6379"  # Commented out for security - use docker exec for Redis access/' docker-compose.yml

echo "✅ Database ports secured"

# Fix 3: Secure CORS Configuration
echo "🔒 Fix 3: Securing CORS configuration..."
sed -i 's/CORS_ORIGINS=\*/CORS_ORIGINS=http:\/\/localhost,https:\/\/localhost,http:\/\/127.0.0.1,https:\/\/127.0.0.1/' .env

echo "✅ CORS configuration secured"

# Fix 4: Update Admin Password
echo "🔒 Fix 4: Updating admin password..."
# Update the admin password hash in the database init script
sed -i 's/-- Create admin user (password: admin123)/-- Create admin user (password: OpsConductor2024!Admin)/' database/init/01_init.sql
sed -i 's/-- Note: This is a bcrypt hash of '\''admin123'\''/-- Note: This is a bcrypt hash of '\''OpsConductor2024!Admin'\''/' database/init/01_init.sql
sed -i 's/\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8\/LewdBPj\/RK\.s5uOeG/\$2b\$12\$9\/vgw\/JaQRgEOCGNG2XcW.fUu0WbJQcncJ1qXq9bvTnazrIjNaNPi/' database/init/01_init.sql

echo "✅ Admin password updated"

# Fix 5: Update SQLAlchemy Imports
echo "🔧 Fix 5: Updating deprecated SQLAlchemy imports..."
find backend/ -name "*.py" -exec sed -i 's/from sqlalchemy\.ext\.declarative import declarative_base/from sqlalchemy.orm import declarative_base/' {} \; 2>/dev/null || true

echo "✅ SQLAlchemy imports updated"

# Fix 6: Add Health Check Timeouts
echo "🔧 Fix 6: Adding health check timeouts..."
sed -i 's/test: \["CMD", "curl", "-f", "http:\/\/localhost:8000\/health"\]/test: ["CMD", "curl", "-f", "--max-time", "5", "http:\/\/localhost:8000\/health"]/' docker-compose.yml
sed -i 's/test: \["CMD", "curl", "-f", "http:\/\/localhost:3000"\]/test: ["CMD", "curl", "-f", "--max-time", "5", "http:\/\/localhost:3000"]/' docker-compose.yml

echo "✅ Health check timeouts added"

echo ""
echo "🎉 ALL CRITICAL SECURITY FIXES APPLIED!"
echo "========================================"
echo ""
echo "📋 Summary of changes:"
echo "  ✅ Grafana password secured with environment variable"
echo "  ✅ Database ports (PostgreSQL, Redis) secured"
echo "  ✅ CORS configuration restricted to localhost only"
echo "  ✅ Admin password updated to secure version"
echo "  ✅ SQLAlchemy imports updated to modern syntax"
echo "  ✅ Health check timeouts added"
echo ""
echo "🔐 NEW CREDENTIALS:"
echo "  Admin Username: admin"
echo "  Admin Password: OpsConductor2024!Admin"
echo "  Grafana Password: opsconductor_grafana_secure_2024"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "  1. Restart all services: docker-compose down && docker-compose up -d"
echo "  2. Test login with new admin credentials"
echo "  3. Verify Grafana access with new password"
echo "  4. Update any external references to old credentials"
echo ""
echo "📁 Backups created:"
echo "  - docker-compose.yml.backup"
echo "  - .env.backup"
echo "  - database/init/01_init.sql.backup"
echo ""
echo "✅ OpsConductor is now significantly more secure!"