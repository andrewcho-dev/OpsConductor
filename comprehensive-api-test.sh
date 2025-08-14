#!/bin/bash

echo "=== COMPREHENSIVE AUTHENTICATED API TESTING ==="

BASE_URL="http://localhost"

# Step 1: Authenticate and get token
echo "🔐 Authenticating..."
AUTH_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' "$BASE_URL/api/auth/login")
TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token' 2>/dev/null)

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Authentication failed!"
    exit 1
fi

echo "✅ Authentication successful!"
echo "Token: ${TOKEN:0:50}..."

# Step 2: Test all endpoints with authentication
echo ""
echo "=== TESTING ALL AUTHENTICATED ENDPOINTS ==="

# Function to test authenticated endpoint
test_authenticated_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    echo -n "$method $endpoint: "
    
    if [ -n "$data" ]; then
        status_code=$(curl -s -o /tmp/api_response -w "%{http_code}" -X "$method" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    else
        status_code=$(curl -s -o /tmp/api_response -w "%{http_code}" -X "$method" \
            -H "Authorization: Bearer $TOKEN" \
            "$BASE_URL$endpoint")
    fi
    
    case "$status_code" in
        200) echo "✅ OK (200)" ;;
        201) echo "✅ Created (201)" ;;
        202) echo "✅ Accepted (202)" ;;
        204) echo "✅ No Content (204)" ;;
        400) echo "❌ Bad Request (400)" ;;
        401) echo "🔒 Unauthorized (401)" ;;
        403) echo "🚫 Forbidden (403)" ;;
        404) echo "❌ Not Found (404)" ;;
        405) echo "⚠️ Method Not Allowed (405)" ;;
        422) echo "📝 Validation Error (422)" ;;
        500) echo "💥 Server Error (500)" ;;
        *) echo "⚠️ Status: $status_code" ;;
    esac
    
    # Show response for successful calls
    if [ "$status_code" -eq 200 ] || [ "$status_code" -eq 201 ]; then
        response_size=$(wc -c < /tmp/api_response)
        if [ "$response_size" -gt 0 ] && [ "$response_size" -lt 1000 ]; then
            echo "    Response: $(cat /tmp/api_response | head -1)"
        elif [ "$response_size" -gt 0 ]; then
            echo "    Response size: ${response_size} bytes"
        fi
    fi
}

# Test all GET endpoints
echo "--- GET ENDPOINTS ---"
test_authenticated_endpoint "GET" "/api/users"
test_authenticated_endpoint "GET" "/api/users/me"  
test_authenticated_endpoint "GET" "/api/targets"
test_authenticated_endpoint "GET" "/api/jobs"
test_authenticated_endpoint "GET" "/api/jobs/history"
test_authenticated_endpoint "GET" "/api/jobs/status"
test_authenticated_endpoint "GET" "/api/system/settings"
test_authenticated_endpoint "GET" "/api/system/health" 
test_authenticated_endpoint "GET" "/api/celery/workers"
test_authenticated_endpoint "GET" "/api/audit"

# Test users endpoints
echo ""
echo "--- USERS MANAGEMENT ---"
test_authenticated_endpoint "GET" "/api/users"
test_authenticated_endpoint "POST" "/api/users" '{"username":"testuser","password":"testpass123","email":"test@example.com","full_name":"Test User"}'
test_authenticated_endpoint "GET" "/api/users/1" 
test_authenticated_endpoint "PUT" "/api/users/1" '{"full_name":"Updated Test User"}'
test_authenticated_endpoint "DELETE" "/api/users/999" # Test non-existent user

# Test targets endpoints  
echo ""
echo "--- TARGETS MANAGEMENT ---"
test_authenticated_endpoint "GET" "/api/targets"
test_authenticated_endpoint "POST" "/api/targets" '{"name":"TestTarget","host":"192.168.1.100","port":22,"username":"root","password":"password123"}'
test_authenticated_endpoint "GET" "/api/targets/discovery"
test_authenticated_endpoint "POST" "/api/targets/discovery" '{"network_range":"192.168.1.0/24","scan_type":"ping"}'

# Test jobs endpoints
echo ""  
echo "--- JOBS MANAGEMENT ---"
test_authenticated_endpoint "GET" "/api/jobs"
test_authenticated_endpoint "POST" "/api/jobs" '{"name":"TestJob","description":"Test job","action":"ping","targets":[1]}'
test_authenticated_endpoint "GET" "/api/jobs/1"
test_authenticated_endpoint "POST" "/api/jobs/1/execute"
test_authenticated_endpoint "GET" "/api/jobs/1/history"
test_authenticated_endpoint "GET" "/api/jobs/1/status"
test_authenticated_endpoint "DELETE" "/api/jobs/999" # Test non-existent job

# Test system endpoints
echo ""
echo "--- SYSTEM MANAGEMENT ---"
test_authenticated_endpoint "GET" "/api/system/health"
test_authenticated_endpoint "GET" "/api/system/settings"
test_authenticated_endpoint "PUT" "/api/system/settings" '{"setting_key":"test_value"}'
test_authenticated_endpoint "GET" "/api/system/logs"
test_authenticated_endpoint "GET" "/api/system/notifications"

# Test celery monitoring
echo ""
echo "--- CELERY MONITORING ---" 
test_authenticated_endpoint "GET" "/api/celery/workers"
test_authenticated_endpoint "GET" "/api/celery/tasks"
test_authenticated_endpoint "GET" "/api/celery/queues"
test_authenticated_endpoint "POST" "/api/celery/workers/restart"

# Test audit endpoints
echo ""
echo "--- AUDIT & LOGS ---"
test_authenticated_endpoint "GET" "/api/audit"
test_authenticated_endpoint "GET" "/api/audit/logs"
test_authenticated_endpoint "GET" "/api/logs"
test_authenticated_endpoint "GET" "/api/logs/application"
test_authenticated_endpoint "GET" "/api/logs/access"

echo ""
echo "=== API TESTING COMPLETE ==="
rm -f /tmp/api_response