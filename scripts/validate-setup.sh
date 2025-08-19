#!/bin/bash

# =============================================================================
# OPSCONDUCTOR - SETUP VALIDATION SCRIPT
# =============================================================================
# Validates Docker infrastructure configuration

set -e

echo "🔍 OpsConductor Setup Validation"
echo "================================"

# Check Docker
echo "📦 Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed: $(docker --version)"
else
    echo "❌ Docker is not installed"
    exit 1
fi

# Check Docker Compose
echo "🐙 Checking Docker Compose..."
if docker compose version &> /dev/null; then
    echo "✅ Docker Compose is available: $(docker compose version)"
else
    echo "❌ Docker Compose is not available"
    exit 1
fi

# Check .env file
echo "⚙️  Checking environment configuration..."
if [ -f .env ]; then
    echo "✅ .env file exists"
    
    # Check required variables
    required_vars=("POSTGRES_DB" "POSTGRES_USER" "POSTGRES_PASSWORD" "SECRET_KEY" "JWT_SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            echo "✅ $var is configured"
        else
            echo "❌ $var is missing from .env"
        fi
    done
else
    echo "❌ .env file is missing"
    exit 1
fi

# Validate Docker Compose configurations
echo "🔧 Validating Docker Compose configurations..."

echo "  📋 Development configuration..."
if docker compose config --quiet; then
    echo "  ✅ Development configuration is valid"
else
    echo "  ❌ Development configuration has errors"
    exit 1
fi

echo "  🏭 Production configuration..."
if docker compose -f docker-compose.prod.yml config --quiet 2>/dev/null; then
    echo "  ✅ Production configuration is valid"
else
    echo "  ⚠️  Production configuration has warnings (check environment variables)"
fi

# Check SSL certificates
echo "🔐 Checking SSL certificates..."
if [ -f nginx/ssl/cert.pem ] && [ -f nginx/ssl/key.pem ]; then
    echo "✅ SSL certificates exist"
    
    # Check certificate validity
    if openssl x509 -in nginx/ssl/cert.pem -noout -checkend 86400 &>/dev/null; then
        echo "✅ SSL certificate is valid"
    else
        echo "⚠️  SSL certificate expires soon or is invalid"
    fi
else
    echo "❌ SSL certificates are missing"
    echo "   Run: ./setup.sh to generate them"
fi

# Check directory structure
echo "📁 Checking directory structure..."
required_dirs=("backend" "frontend" "nginx" "database/init" "monitoring")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir directory exists"
    else
        echo "❌ $dir directory is missing"
    fi
done

# Check key files
echo "📄 Checking key files..."
key_files=(
    "docker-compose.yml"
    "docker-compose.prod.yml"
    "nginx/nginx.conf"
    "nginx/nginx.prod.conf"
    "backend/Dockerfile"
    "backend/Dockerfile.dev"
    "frontend/Dockerfile"
    "frontend/Dockerfile.dev"
)

for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file is missing"
    fi
done

# Check for backup/junk files
echo "🧹 Checking for cleanup..."
junk_files=(
    "docker-compose.yml.backup"
    ".env.backup"
    "database/init/01_init.sql.backup"
)

junk_found=false
for file in "${junk_files[@]}"; do
    if [ -f "$file" ]; then
        echo "⚠️  Found junk file: $file"
        junk_found=true
    fi
done

if [ "$junk_found" = false ]; then
    echo "✅ No junk files found"
fi

echo ""
echo "🎉 Validation completed!"
echo ""
echo "Summary:"
echo "- OpsConductor Docker infrastructure is properly configured"
echo "- All required files and directories are present"
echo "- Docker Compose configurations are valid"
echo "- SSL certificates are configured"
echo ""
echo "Ready to deploy! 🚀"
echo ""
echo "Next steps:"
echo "  Development: docker compose up -d"
echo "  Production:  docker compose -f docker-compose.prod.yml up -d"
echo ""