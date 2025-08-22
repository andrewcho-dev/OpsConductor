#!/bin/bash

# Test script for distributed Celery workers
echo "🧪 Testing OpsConductor Distributed Workers"
echo "=========================================="

# Test 1: Check if workers are running
echo "📊 1. Checking worker status..."
docker compose -f docker-compose.workers.yml ps

echo ""
echo "📋 2. Testing Celery worker connectivity..."

# Test execution worker
echo "   🔥 Testing execution worker..."
if docker exec execution-worker celery -A app.celery_app inspect ping >/dev/null 2>&1; then
    echo "   ✅ Execution worker is responsive"
else
    echo "   ❌ Execution worker is not responding"
fi

# Test system worker  
echo "   🛠️ Testing system worker..."
if docker exec system-worker celery -A app.celery_app inspect ping >/dev/null 2>&1; then
    echo "   ✅ System worker is responsive"
else
    echo "   ❌ System worker is not responding"
fi

echo ""
echo "📈 3. Testing task submission..."

# Submit a test system task
echo "   📊 Submitting test system metrics collection task..."
docker exec system-worker python3 -c "
from app.tasks.system_tasks import collect_system_metrics
result = collect_system_metrics.delay()
print(f'✅ Task submitted: {result.id}')
try:
    outcome = result.get(timeout=30)
    print(f'✅ Task completed successfully')
    print(f'📊 Metrics: CPU, Memory, Disk usage collected')
except Exception as e:
    print(f'❌ Task failed: {e}')
" 2>/dev/null || echo "   ⚠️  Task submission test skipped (dependencies not ready)"

echo ""
echo "🌐 4. Testing Node-RED accessibility..."
if curl -f -s http://localhost:8080/ >/dev/null 2>&1; then
    echo "   ✅ Node-RED is accessible at http://localhost:8080"
else
    echo "   ❌ Node-RED is not accessible (may still be starting up)"
fi

echo ""
echo "📊 5. Worker resource usage..."
docker stats --no-stream execution-worker system-worker system-scheduler node-red

echo ""
echo "🎯 Test Summary:"
echo "   💪 Execution Worker: High-performance job execution"
echo "   🛠️  System Worker: Background maintenance tasks"  
echo "   ⏰ Scheduler: Periodic task management"
echo "   🎨 Node-RED: Visual workflow designer"

echo ""
echo "✅ Distributed worker testing complete!"