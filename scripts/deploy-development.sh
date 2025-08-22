#!/bin/bash

# =============================================================================
# OPSCONDUCTOR - DEVELOPMENT DEPLOYMENT SCRIPT
# =============================================================================
# Deploys OpsConductor in development mode with hot-reload frontend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 OpsConductor Development Deployment${NC}"
echo "=================================================="

# Check if docker and docker-compose are available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

echo -e "${YELLOW}📋 Pre-deployment checks...${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found. Please create it first.${NC}"
    exit 1
fi

# Check if SSL certificates exist
if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
    echo -e "${YELLOW}⚠️  SSL certificates not found. Creating self-signed certificates...${NC}"
    mkdir -p nginx/ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    echo -e "${GREEN}✅ SSL certificates created${NC}"
fi

echo -e "${YELLOW}🛑 Stopping existing services...${NC}"
docker-compose down --remove-orphans

echo -e "${YELLOW}📦 Building services for development...${NC}"
# Build services
docker-compose build

echo -e "${YELLOW}🚀 Starting development services...${NC}"
# Start all services in development mode (default docker-compose.yml)
docker-compose up -d

echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 15

# Wait for health checks
echo -e "${YELLOW}🔍 Checking service health...${NC}"
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f -s -k https://localhost/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Main gateway is healthy${NC}"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}❌ Gateway health check failed after $max_attempts attempts${NC}"
        echo -e "${YELLOW}📋 Service status:${NC}"
        docker-compose ps
        exit 1
    fi
    
    echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts - waiting for services...${NC}"
    sleep 2
    ((attempt++))
done

echo -e "${YELLOW}🔍 Checking frontend hot-reload...${NC}"
if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend development server is running${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend development server may still be starting...${NC}"
fi

echo ""
echo -e "${GREEN}🎉 DEVELOPMENT DEPLOYMENT COMPLETE!${NC}"
echo "=================================================="
echo -e "${BLUE}📍 Access Points:${NC}"
echo -e "   🌐 Main Application: ${GREEN}https://localhost${NC}"
echo -e "   🔥 Frontend Dev:     ${GREEN}http://localhost:3000${NC} (Hot Reload)"
echo -e "   🔐 API Gateway:      ${GREEN}https://localhost/api/v1/${NC}"
echo -e "   🗄️  Object Storage:   ${GREEN}http://localhost:9001${NC} (Direct MinIO)"
echo -e "   📊 MinIO Console:    ${GREEN}http://localhost:9090${NC}"
echo -e "   ❤️  Health Check:     ${GREEN}https://localhost/health${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${BLUE}💡 Useful Commands:${NC}"
echo -e "   View logs:           ${YELLOW}docker-compose logs -f${NC}"
echo -e "   View specific logs:  ${YELLOW}docker-compose logs -f [service-name]${NC}"
echo -e "   Stop services:       ${YELLOW}docker-compose down${NC}"
echo -e "   Restart:             ${YELLOW}$0${NC}"
echo -e "   Switch to production:${YELLOW}./scripts/deploy-production.sh${NC}"

echo ""
echo -e "${GREEN}🚀 OpsConductor is running in development mode!${NC}"
echo -e "${YELLOW}💡 Frontend changes will auto-reload at http://localhost:3000${NC}"