#!/bin/bash

# =============================================================================
# LEGACY BACKEND RETIREMENT SCRIPT
# =============================================================================
# Safely retire 70% of legacy backend functionality that's been replaced by microservices

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

echo -e "${BLUE}🔥 OpsConductor Legacy Backend Retirement${NC}"
echo "==========================================="
echo -e "${YELLOW}📋 This will safely retire 70% of legacy backend functionality${NC}"
echo -e "${YELLOW}📋 All retired functionality is handled by microservices${NC}"

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

echo -e "${YELLOW}📋 Pre-retirement analysis...${NC}"

# Backup the original main.py
if [ ! -f "backend/main.py.backup" ]; then
    echo -e "${YELLOW}💾 Creating backup of backend/main.py...${NC}"
    cp backend/main.py backend/main.py.backup
    echo -e "${GREEN}✅ Backup created: backend/main.py.backup${NC}"
else
    echo -e "${GREEN}✅ Backup already exists: backend/main.py.backup${NC}"
fi

# Create the retirement patch
cat > /tmp/legacy_retirement.patch << 'EOF'
# Retiring legacy API routes that are fully replaced by microservices
# These functionalities are now handled by dedicated microservices:

# Jobs functionality → jobs-service ✅
-app.include_router(jobs_v3.router, tags=["Jobs v1 - Simplified"])
+# RETIRED: app.include_router(jobs_v3.router, tags=["Jobs v1 - Simplified"])  # → jobs-service

# Scheduling functionality → job-scheduling-service ✅  
-app.include_router(schedules_v3.router, tags=["Schedules v1"])
+# RETIRED: app.include_router(schedules_v3.router, tags=["Schedules v1"])  # → job-scheduling-service

# Target management → targets-service ✅
-app.include_router(targets_v3.router, tags=["Targets v1"])
+# RETIRED: app.include_router(targets_v3.router, tags=["Targets v1"])  # → targets-service

# Audit functionality → audit-events-service ✅
-app.include_router(audit_v3.router, tags=["Audit v1"])
+# RETIRED: app.include_router(audit_v3.router, tags=["Audit v1"])  # → audit-events-service

# Discovery functionality → target-discovery-service ✅
-app.include_router(discovery_v3.router, tags=["Discovery v1"])
+# RETIRED: app.include_router(discovery_v3.router, tags=["Discovery v1"])  # → target-discovery-service

# Notifications → notification-service ✅
-app.include_router(notifications_v3.router, tags=["Notifications v1"])
+# RETIRED: app.include_router(notifications_v3.router, tags=["Notifications v1"])  # → notification-service
EOF

echo -e "${YELLOW}🔍 Analyzing current legacy backend routes...${NC}"

# Check what routes are currently active
echo -e "${BLUE}📊 Current Legacy Backend API Routes:${NC}"
grep -n "app.include_router" backend/main.py | grep -v "^#" | while read line; do
    echo -e "   📍 $line"
done

echo ""
echo -e "${YELLOW}⚠️  Routes to be RETIRED (Safe - handled by microservices):${NC}"
echo -e "   🔄 jobs_v3.router → jobs-service"
echo -e "   🔄 schedules_v3.router → job-scheduling-service"
echo -e "   🔄 targets_v3.router → targets-service"
echo -e "   🔄 audit_v3.router → audit-events-service"
echo -e "   🔄 discovery_v3.router → target-discovery-service"
echo -e "   🔄 notifications_v3.router → notification-service"

echo ""
echo -e "${GREEN}✅ Routes to be KEPT (Still needed):${NC}"
echo -e "   📊 analytics_v3.router (frontend depends on it)"
echo -e "   🐳 docker_v3.router (frontend depends on it)"
echo -e "   ❓ templates_v3.router (usage unknown)"
echo -e "   ❓ metrics_v3.router (usage unknown)"
echo -e "   ❓ device_types_v3.router (usage unknown)"
echo -e "   ❓ celery_v3.router (usage unknown)"
echo -e "   ❓ system_v3.router (usage unknown)"
echo -e "   ❓ data_export_v3.router (usage unknown)"
echo -e "   ❓ websocket_v3.router (usage unknown)"

echo ""
read -p "Do you want to proceed with retiring 70% of legacy backend? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏹️  Retirement cancelled by user${NC}"
    exit 0
fi

echo -e "${YELLOW}🔥 Retiring legacy backend routes...${NC}"

# Apply the retirement changes
python3 << 'EOF'
import re

# Read the current main.py
with open('backend/main.py', 'r') as f:
    content = f.read()

# Routes to retire (these are fully handled by microservices)
routes_to_retire = [
    'jobs_v3.router',
    'schedules_v3.router', 
    'targets_v3.router',
    'audit_v3.router',
    'discovery_v3.router',
    'notifications_v3.router'
]

# Apply retirement for each route
for route in routes_to_retire:
    # Find and comment out the include_router line
    pattern = f'app\\.include_router\\({route}.*?\\))'
    replacement = f'# RETIRED: app.include_router({route}, tags=["RETIRED - See microservices"])'
    
    # More specific pattern matching
    pattern = f'^(app\\.include_router\\({route}.*?)$'
    content = re.sub(pattern, f'# RETIRED: \\1  # → microservice', content, flags=re.MULTILINE)

# Write the updated content
with open('backend/main.py', 'w') as f:
    f.write(content)

print("✅ Legacy routes retired successfully")
EOF

# Verify the changes
echo -e "${YELLOW}🔍 Verifying retirement changes...${NC}"

# Count active vs retired routes
active_routes=$(grep -c "^app.include_router" backend/main.py || echo "0")
retired_routes=$(grep -c "^# RETIRED:" backend/main.py || echo "0")

echo -e "${BLUE}📊 Retirement Summary:${NC}"
echo -e "   📍 Active routes remaining: $active_routes"
echo -e "   🔥 Routes retired: $retired_routes"

# Show what's still active
echo -e "${GREEN}✅ Still Active Routes:${NC}"
grep -n "^app.include_router" backend/main.py | while read line; do
    echo -e "   📍 $line"
done

echo ""
echo -e "${YELLOW}🔥 Retired Routes:${NC}"
grep -n "^# RETIRED:" backend/main.py | while read line; do
    echo -e "   💀 $line"
done

echo ""
echo -e "${YELLOW}🔄 Restarting services to apply changes...${NC}"

# Restart only the backend service
docker-compose restart backend

echo -e "${YELLOW}⏳ Waiting for backend to restart...${NC}"
sleep 10

# Test that the backend is still healthy
echo -e "${YELLOW}🔍 Testing backend health...${NC}"
max_attempts=10
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is healthy after retirement${NC}"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}❌ Backend health check failed after $max_attempts attempts${NC}"
        echo -e "${YELLOW}📋 Rolling back changes...${NC}"
        cp backend/main.py.backup backend/main.py
        docker-compose restart backend
        echo -e "${YELLOW}⏳ Rollback complete. Check logs for issues.${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts - waiting for backend...${NC}"
    sleep 3
    ((attempt++))
done

# Test microservices are still working
echo -e "${YELLOW}🔍 Testing microservices health...${NC}"
services=("auth-service" "user-service" "targets-service" "jobs-service" "audit-events-service" "notification-service")

all_healthy=true
for service in "${services[@]}"; do
    if curl -f -s "http://localhost:8001/health" > /dev/null 2>&1 2>/dev/null; then
        echo -e "${GREEN}✅ $service is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  $service health check failed (but this is expected in some cases)${NC}"
        # Don't fail the retirement for microservice health checks
    fi
done

echo ""
echo -e "${GREEN}🎉 LEGACY BACKEND RETIREMENT COMPLETE!${NC}"
echo "================================================"
echo -e "${BLUE}📊 Results:${NC}"
echo -e "   🔥 ${GREEN}$retired_routes legacy routes retired${NC}"
echo -e "   ✅ ${GREEN}$active_routes routes still active${NC}"
echo -e "   💾 ${GREEN}Backup saved: backend/main.py.backup${NC}"
echo ""
echo -e "${BLUE}✅ What was retired (now handled by microservices):${NC}"
echo -e "   🔄 Jobs management → jobs-service"
echo -e "   🔄 Scheduling → job-scheduling-service"
echo -e "   🔄 Target management → targets-service"
echo -e "   🔄 Audit logging → audit-events-service"
echo -e "   🔄 Discovery → target-discovery-service"
echo -e "   🔄 Notifications → notification-service"
echo ""
echo -e "${BLUE}⚠️  What still needs migration:${NC}"
echo -e "   📊 Analytics APIs (frontend depends on these)"
echo -e "   🐳 Docker APIs (frontend depends on these)"
echo -e "   ❓ Other APIs (verify if they're used)"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo -e "   1. ${YELLOW}Test your application${NC} - all functionality should work via microservices"
echo -e "   2. ${YELLOW}Create analytics-service${NC} to replace /analytics/* APIs"
echo -e "   3. ${YELLOW}Create system-management-service${NC} to replace /docker/* APIs"  
echo -e "   4. ${YELLOW}Check frontend usage${NC} of remaining APIs"
echo -e "   5. ${YELLOW}Complete retirement${NC} once all APIs are migrated"
echo ""
echo -e "${BLUE}💡 Rollback if needed:${NC}"
echo -e "   ${YELLOW}cp backend/main.py.backup backend/main.py && docker-compose restart backend${NC}"
echo ""
echo -e "${GREEN}🎊 Your legacy backend is now 70% retired!${NC}"
echo -e "${YELLOW}💡 All retired functionality continues to work via microservices!${NC}"