#!/bin/bash

echo "=== COMPREHENSIVE API ENDPOINT TESTING ==="
echo "Testing all possible API endpoints..."

BASE_URL="http://localhost"
API_ENDPOINTS=(
    "/api"
    "/api/health"
    "/api/status"
    "/api/version"
    "/api/info"
    "/api/docs"
    "/api/redoc" 
    "/api/openapi.json"
    "/api/v1"
    "/api/auth"
    "/api/auth/login"
    "/api/auth/logout"
    "/api/auth/token"
    "/api/auth/refresh"
    "/api/auth/status"
    "/api/users"
    "/api/users/me"
    "/api/targets" 
    "/api/targets/discovery"
    "/api/jobs"
    "/api/jobs/execute"
    "/api/jobs/history"
    "/api/jobs/status"
    "/api/system"
    "/api/system/health"
    "/api/system/settings"
    "/api/notifications"
    "/api/audit"
    "/api/logs"
    "/api/celery"
    "/api/celery/workers"
    "/api/celery/tasks"
    "/api/analytics"
    "/api/monitoring"
)

echo "Testing GET requests..."
for endpoint in "${API_ENDPOINTS[@]}"; do
    echo -n "GET $endpoint: "
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    if [ "$status_code" -eq 200 ]; then
        echo "✅ OK (200)"
    elif [ "$status_code" -eq 401 ]; then
        echo "🔒 Requires Auth (401)"
    elif [ "$status_code" -eq 403 ]; then
        echo "🚫 Forbidden (403)"  
    elif [ "$status_code" -eq 404 ]; then
        echo "❌ Not Found (404)"
    else
        echo "⚠️  Status: $status_code"
    fi
done

echo ""
echo "Testing authentication endpoints with POST..."
AUTH_ENDPOINTS=(
    "/api/auth/login"
    "/api/login"  
    "/api/token"
    "/api/auth/token"
)

for endpoint in "${AUTH_ENDPOINTS[@]}"; do
    echo -n "POST $endpoint (test credentials): "
    status_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"admin123"}' \
        "$BASE_URL$endpoint")
    if [ "$status_code" -eq 200 ]; then
        echo "✅ OK (200) - Login endpoint found!"
    elif [ "$status_code" -eq 401 ]; then
        echo "🔒 Invalid credentials (401) - Endpoint exists"
    elif [ "$status_code" -eq 422 ]; then
        echo "📝 Validation error (422) - Endpoint exists" 
    elif [ "$status_code" -eq 404 ]; then
        echo "❌ Not Found (404)"
    else
        echo "⚠️  Status: $status_code"
    fi
done

echo ""
echo "=== API ENDPOINT TESTING COMPLETE ==="