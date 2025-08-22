#!/bin/bash

# =============================================================================
# OPSCONDUCTOR - PRODUCTION DEPLOYMENT SCRIPT
# =============================================================================
# Deploys OpsConductor in production mode with optimized nginx and static frontend

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

echo -e "${BLUE}🚀 OpsConductor Production Deployment${NC}"
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

echo -e "${YELLOW}🔨 Building frontend for production...${NC}"
# Build the frontend first
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build frontend-builder

echo -e "${YELLOW}📦 Building all services...${NC}"
# Build all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

echo -e "${YELLOW}🏗️  Creating frontend build...${NC}"
# Run frontend builder to create static files
docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm frontend-builder

echo -e "${YELLOW}🚀 Starting production services...${NC}"
# Start all services in production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

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
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
        exit 1
    fi
    
    echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts - waiting for services...${NC}"
    sleep 2
    ((attempt++))
done

echo -e "${YELLOW}🔍 Checking individual microservices...${NC}"
services=("auth" "users" "targets" "jobs" "executions" "audit" "notifications")

for service in "${services[@]}"; do
    if curl -f -s -k "https://localhost/health/$service" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service-service is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  $service-service health check failed${NC}"
    fi
done

echo ""
echo -e "${GREEN}🎉 PRODUCTION DEPLOYMENT COMPLETE!${NC}"
echo "=================================================="
echo -e "${BLUE}📍 Access Points:${NC}"
echo -e "   🌐 Main Application: ${GREEN}https://localhost${NC}"
echo -e "   🔐 API Gateway:      ${GREEN}https://localhost/api/v1/${NC}"
echo -e "   🗄️  Object Storage:   ${GREEN}https://localhost/storage/${NC}"
echo -e "   ❤️  Health Check:     ${GREEN}https://localhost/health${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${BLUE}💡 Useful Commands:${NC}"
echo -e "   View logs:     ${YELLOW}docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f${NC}"
echo -e "   Stop services: ${YELLOW}docker-compose -f docker-compose.yml -f docker-compose.prod.yml down${NC}"
echo -e "   Restart:       ${YELLOW}$0${NC}"

echo ""
echo -e "${GREEN}🚀 OpsConductor is running in production mode!${NC}"