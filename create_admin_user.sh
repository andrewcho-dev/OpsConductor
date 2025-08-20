#!/bin/bash
# Create Initial Admin User for OpsConductor

echo "🚀 Creating initial admin user for OpsConductor..."

# Admin user details
USER_ID="admin-001"
USERNAME="admin"
EMAIL="admin@opsconductor.local"
PASSWORD="admin123"
FULL_NAME="System Administrator"
ROLE="admin"

# Hash password (simple SHA-256 for demo)
PASSWORD_HASH=$(echo -n "$PASSWORD" | sha256sum | cut -d' ' -f1)

echo "   Username: $USERNAME"
echo "   Email: $EMAIL"
echo "   Password: $PASSWORD"
echo ""

# Create auth credentials in auth service database
echo "📝 Creating auth credentials..."
docker compose exec auth-postgres psql -U auth_user -d auth_db -c "
INSERT INTO auth_credentials (
    user_id, username, email, password_hash, 
    is_active, password_changed_at, created_at
) VALUES (
    '$USER_ID', '$USERNAME', '$EMAIL', '$PASSWORD_HASH', 
    true, NOW(), NOW()
) ON CONFLICT (username) DO NOTHING;
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Auth credentials created"
else
    echo "⚠️  Auth credentials may already exist"
fi

# Create user profile in user service database
echo "📝 Creating user profile..."
docker compose exec user-postgres psql -U user_user -d user_db -c "
INSERT INTO users (
    user_id, username, email, full_name, role, 
    permissions, is_active, created_at, created_by
) VALUES (
    '$USER_ID', '$USERNAME', '$EMAIL', '$FULL_NAME', '$ROLE', 
    '{\"*\"}', true, NOW(), 'system'
) ON CONFLICT (username) DO NOTHING;
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ User profile created"
else
    echo "⚠️  User profile may already exist"
fi

# Test login
echo ""
echo "🧪 Testing login..."
RESPONSE=$(curl -k -s -w "%{http_code}" -o /tmp/login_response.json \
    -X POST "https://localhost/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

if [ "$RESPONSE" = "200" ]; then
    echo "✅ Login test successful!"
    TOKEN=$(cat /tmp/login_response.json | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "   Token: ${TOKEN:0:50}..."
    rm -f /tmp/login_response.json
    
    echo ""
    echo "🎉 Admin user created successfully!"
    echo "   You can now login at: https://localhost/login"
    echo "   Username: $USERNAME"
    echo "   Password: $PASSWORD"
    echo ""
    echo "⚠️  IMPORTANT: Change the default password after first login!"
else
    echo "❌ Login test failed (HTTP $RESPONSE)"
    if [ -f /tmp/login_response.json ]; then
        echo "   Response: $(cat /tmp/login_response.json)"
        rm -f /tmp/login_response.json
    fi
fi