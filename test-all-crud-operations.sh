#!/bin/bash

echo "=== COMPREHENSIVE CRUD OPERATIONS TESTING ==="
echo "Testing EVERY SINGLE FEATURE: CREATE, READ, UPDATE, DELETE"

BASE_URL="http://localhost"

# Authenticate and get token
echo "🔐 Authenticating..."
AUTH_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' "$BASE_URL/api/auth/login")
TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Authentication failed!"
    exit 1
fi
echo "✅ Token obtained: ${TOKEN:0:50}..."

echo ""
echo "=== 1. USERS CRUD TESTING ==="
echo ""

echo "1.1 📖 READ - Get all users"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/users/" | jq '.[:2]'

echo ""
echo "1.2 ➕ CREATE - Create new user"
USER_DATA='{"username":"testuser_'$(date +%s)'","password":"testpass123","email":"test@example.com","full_name":"Test User CRUD","role":"user"}'
echo "Creating user with data: $USER_DATA"
CREATE_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$USER_DATA" "$BASE_URL/api/users/")
echo "Create response:"
echo "$CREATE_RESPONSE" | jq .
NEW_USER_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id // empty')

if [ -n "$NEW_USER_ID" ]; then
    echo "✅ User created with ID: $NEW_USER_ID"
    
    echo ""
    echo "1.3 📖 READ - Get specific user"
    curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/users/$NEW_USER_ID" | jq .
    
    echo ""
    echo "1.4 ✏️ UPDATE - Update user"
    UPDATE_DATA='{"full_name":"Updated Test User","email":"updated@example.com"}'
    curl -s -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$UPDATE_DATA" "$BASE_URL/api/users/$NEW_USER_ID" | jq .
    
    echo ""
    echo "1.5 🗑️ DELETE - Delete user"
    DELETE_RESPONSE=$(curl -s -X DELETE -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/users/$NEW_USER_ID")
    echo "Delete response: $DELETE_RESPONSE"
else
    echo "❌ Failed to create user, skipping update/delete tests"
fi

echo ""
echo "=== 2. TARGETS CRUD TESTING ==="
echo ""

echo "2.1 📖 READ - Get all targets"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/targets/" | jq '.[:2]'

echo ""
echo "2.2 ➕ CREATE - Create new target"
TARGET_DATA='{"name":"TestTarget_'$(date +%s)'","host":"192.168.1.999","port":22,"username":"testuser","password":"testpass","target_type":"system","os_type":"linux","environment":"test"}'
echo "Creating target with data: $TARGET_DATA"
CREATE_TARGET_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$TARGET_DATA" "$BASE_URL/api/targets/")
echo "Create target response:"
echo "$CREATE_TARGET_RESPONSE" | jq .
NEW_TARGET_ID=$(echo "$CREATE_TARGET_RESPONSE" | jq -r '.id // empty')

if [ -n "$NEW_TARGET_ID" ]; then
    echo "✅ Target created with ID: $NEW_TARGET_ID"
    
    echo ""
    echo "2.3 📖 READ - Get specific target"
    curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/targets/$NEW_TARGET_ID" | jq .
    
    echo ""
    echo "2.4 ✏️ UPDATE - Update target"
    TARGET_UPDATE='{"name":"Updated Test Target","environment":"production"}'
    curl -s -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$TARGET_UPDATE" "$BASE_URL/api/targets/$NEW_TARGET_ID" | jq .
    
    echo ""
    echo "2.5 🗑️ DELETE - Delete target"
    curl -s -X DELETE -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/targets/$NEW_TARGET_ID"
    echo "Target deletion attempted"
else
    echo "❌ Failed to create target, skipping update/delete tests"
fi

echo ""
echo "=== 3. JOBS CRUD TESTING ==="
echo ""

echo "3.1 📖 READ - Get all jobs"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/jobs/" | jq .

echo ""
echo "3.2 ➕ CREATE - Create new job"
JOB_DATA='{"name":"TestJob_'$(date +%s)'","description":"CRUD test job","action":"ping","timeout_minutes":5,"parameters":{"count":3}}'
echo "Creating job with data: $JOB_DATA"
CREATE_JOB_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$JOB_DATA" "$BASE_URL/api/jobs/")
echo "Create job response:"
echo "$CREATE_JOB_RESPONSE" | jq .
NEW_JOB_ID=$(echo "$CREATE_JOB_RESPONSE" | jq -r '.id // empty')

if [ -n "$NEW_JOB_ID" ]; then
    echo "✅ Job created with ID: $NEW_JOB_ID"
    
    echo ""
    echo "3.3 📖 READ - Get specific job"
    curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/jobs/$NEW_JOB_ID" | jq .
    
    echo ""
    echo "3.4 ✏️ UPDATE - Update job"
    JOB_UPDATE='{"description":"Updated CRUD test job","timeout_minutes":10}'
    curl -s -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$JOB_UPDATE" "$BASE_URL/api/jobs/$NEW_JOB_ID" | jq .
    
    echo ""
    echo "3.5 ▶️ EXECUTE - Execute job"
    curl -s -X POST -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/jobs/$NEW_JOB_ID/execute" | jq .
    
    echo ""
    echo "3.6 📊 STATUS - Get job status"
    curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/jobs/$NEW_JOB_ID/status" | jq .
    
    echo ""
    echo "3.7 📜 HISTORY - Get job execution history"
    curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/jobs/$NEW_JOB_ID/history" | jq .
    
    echo ""
    echo "3.8 🗑️ DELETE - Delete job"
    curl -s -X DELETE -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/jobs/$NEW_JOB_ID"
    echo "Job deletion attempted"
else
    echo "❌ Failed to create job, skipping other tests"
fi

echo ""
echo "=== 4. SYSTEM SETTINGS TESTING ==="
echo ""

echo "4.1 📖 READ - Get all system settings"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/system/settings" | jq .

echo ""
echo "4.2 ✏️ UPDATE - Update system setting"
SETTING_UPDATE='{"setting_key":"test_setting","setting_value":"test_value","description":"CRUD test setting"}'
curl -s -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$SETTING_UPDATE" "$BASE_URL/api/system/settings/1" | jq .

echo ""
echo "=== 5. DISCOVERY TESTING ==="
echo ""

echo "5.1 🔍 DISCOVERY - Network discovery"
DISCOVERY_DATA='{"network_range":"192.168.1.0/24","scan_type":"ping","timeout":30}'
echo "Testing discovery with: $DISCOVERY_DATA"
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$DISCOVERY_DATA" "$BASE_URL/api/targets/discovery" | jq .

echo ""
echo "=== 6. CELERY MONITORING TESTING ==="
echo ""

echo "6.1 📊 WORKERS - Get worker status"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/celery/workers" | jq .

echo ""
echo "6.2 📊 QUEUES - Get queue status"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/celery/queues" | jq .

echo ""
echo "=== COMPREHENSIVE CRUD TESTING COMPLETE ==="
echo "✅ All major CRUD operations tested!"