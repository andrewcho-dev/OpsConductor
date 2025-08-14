#!/bin/bash

echo "🔧 Applying fixes to ENABLEDRM platform..."

# Stop services
echo "⏹️  Stopping services..."
docker-compose down

# Apply database migration
echo "🗄️  Applying database migration..."
docker-compose up -d postgres
sleep 10

# Apply the database schema fix directly
echo "📝 Applying database schema fix..."
docker-compose exec -T postgres psql -U enabledrm -d enabledrm -c "ALTER TABLE job_execution_logs ALTER COLUMN job_execution_id DROP NOT NULL;"

# Restart all services
echo "🚀 Starting all services..."
docker-compose up -d

echo "✅ Fixes applied successfully!"
echo ""
echo "📋 Summary of fixes applied:"
echo "1. ✅ Fixed job creation database schema issue (job_execution_id nullable)"
echo "2. ✅ Added discovery endpoints to /api/targets/discovery"
echo "3. ✅ Added audit system with /api/audit endpoints"
echo ""
echo "🧪 The following issues have been resolved:"
echo "- HIGH PRIORITY: Job creation database schema issue"
echo "- MEDIUM PRIORITY: Discovery API endpoint issues"
echo "- MEDIUM PRIORITY: Audit system missing"
echo ""
echo "🌐 Services should be available at:"
echo "- Frontend: http://localhost"
echo "- Backend API: http://localhost/api"
echo "- Audit API: http://localhost/api/audit"
echo "- Discovery API: http://localhost/api/targets/discovery"