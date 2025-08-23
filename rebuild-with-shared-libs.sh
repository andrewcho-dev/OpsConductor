#!/bin/bash

# Helper script to rebuild services with shared library cache busting
# Usage: ./rebuild-with-shared-libs.sh [service-name]
# If no service name provided, rebuilds all services that use shared libraries

set -e

# Show help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "🔧 Shared Library Cache Bust Rebuild Script"
    echo ""
    echo "Usage:"
    echo "  ./rebuild-with-shared-libs.sh                 # Rebuild all services with shared libs"
    echo "  ./rebuild-with-shared-libs.sh [service-name]  # Rebuild specific service"
    echo "  ./rebuild-with-shared-libs.sh --help          # Show this help"
    echo ""
    echo "Services with shared libraries:"
    echo "  - auth-service"
    echo "  - user-service"
    echo "  - targets-service"
    echo "  - jobs-service"
    echo "  - execution-service"
    echo "  - audit-events-service"
    echo "  - notification-service"
    echo "  - job-management-service"
    echo "  - job-scheduling-service"
    echo "  - target-discovery-service"
    echo ""
    echo "💡 This script ensures shared library changes are picked up by busting Docker's layer cache."
    exit 0
fi

CACHE_BUST=$(date +%s)
SERVICES_WITH_SHARED_LIBS=(
    "auth-service"
    "user-service"
    "targets-service"
    "jobs-service"
    "execution-service"
    "audit-events-service"
    "notification-service"
    "job-management-service"
    "job-scheduling-service"
    "target-discovery-service"
)

echo "🔧 Rebuilding with shared library cache bust: $CACHE_BUST"

if [ $# -eq 0 ]; then
    echo "📦 Rebuilding all services with shared libraries..."
    for service in "${SERVICES_WITH_SHARED_LIBS[@]}"; do
        echo "  🔨 Building $service..."
        docker compose build --build-arg SHARED_LIBS_CACHE_BUST=$CACHE_BUST "$service"
    done
    echo "✅ All services rebuilt successfully!"
    echo ""
    echo "💡 To restart all services: docker compose up -d"
else
    SERVICE_NAME="$1"
    echo "📦 Rebuilding $SERVICE_NAME with shared library cache bust..."
    docker compose build --build-arg SHARED_LIBS_CACHE_BUST=$CACHE_BUST "$SERVICE_NAME"
    echo "✅ $SERVICE_NAME rebuilt successfully!"
    echo ""
    echo "💡 To restart this service: docker compose up -d $SERVICE_NAME"
fi

echo ""
echo "🎯 Cache bust value used: $CACHE_BUST"
echo "📝 This ensures shared library changes are picked up in the rebuild."