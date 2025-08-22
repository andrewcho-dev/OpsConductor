#!/bin/bash

# OpsConductor Distributed Workers Startup Script
# This script starts the distributed Celery worker architecture

set -e

echo "🚀 Starting OpsConductor Distributed Workers Architecture"
echo "============================================================"

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ docker compose is not available. Please install Docker with Compose plugin."
    exit 1
fi

# Set environment variables if not already set
export POSTGRES_DB=${POSTGRES_DB:-execution_service}
export POSTGRES_USER=${POSTGRES_USER:-postgres}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}

echo "📋 Configuration:"
echo "   Database: $POSTGRES_DB"
echo "   User: $POSTGRES_USER"
echo ""

echo "🏗️  Building Docker images..."
docker compose -f docker-compose.workers.yml build

echo ""
echo "🚀 Starting distributed workers..."

# Start infrastructure first (database, redis)
echo "   📊 Starting database and Redis..."
docker compose -f docker-compose.workers.yml up -d redis execution-db

# Wait for database to be ready
echo "   ⏳ Waiting for database to be ready..."
until docker compose -f docker-compose.workers.yml exec -T execution-db pg_isready -U postgres; do
  echo "      Database is unavailable - sleeping"
  sleep 2
done
echo "   ✅ Database is ready"

# Wait for Redis to be ready
echo "   ⏳ Waiting for Redis to be ready..."
until docker compose -f docker-compose.workers.yml exec -T redis redis-cli ping; do
  echo "      Redis is unavailable - sleeping"
  sleep 2
done
echo "   ✅ Redis is ready"

# Start workers
echo "   💪 Starting execution worker..."
docker compose -f docker-compose.workers.yml up -d execution-worker

echo "   🛠️  Starting system worker..."
docker compose -f docker-compose.workers.yml up -d system-worker

# Start scheduler after workers are up
echo "   ⏰ Starting scheduler..."
sleep 5  # Give workers time to start
docker compose -f docker-compose.workers.yml up -d system-scheduler

# Start Node-RED
echo "   🎨 Starting Node-RED..."
docker compose -f docker-compose.workers.yml up -d node-red nginx-proxy

echo ""
echo "✅ Distributed workers started successfully!"
echo ""
echo "🔗 Access Points:"
echo "   📊 Node-RED Interface: http://localhost:8080"
echo "   🐳 Docker containers:"
docker compose -f docker-compose.workers.yml ps

echo ""
echo "📊 Worker Status:"
echo "   💪 Execution Worker: Handles job execution tasks"
echo "   🛠️  System Worker: Handles cleanup, discovery, health tasks"
echo "   ⏰ Scheduler: Manages periodic tasks"
echo "   🎨 Node-RED: Visual workflow designer"

echo ""
echo "🔧 Useful Commands:"
echo "   📋 View logs: docker compose -f docker-compose.workers.yml logs -f [service_name]"
echo "   📊 Check status: docker compose -f docker-compose.workers.yml ps"
echo "   🛑 Stop workers: docker compose -f docker-compose.workers.yml down"
echo "   🔄 Restart worker: docker compose -f docker-compose.workers.yml restart [service_name]"

echo ""
echo "🎯 Next Steps:"
echo "   1. Open Node-RED at http://localhost:8080"
echo "   2. Install OpsConductor custom nodes"
echo "   3. Create your first automation workflow!"
echo ""