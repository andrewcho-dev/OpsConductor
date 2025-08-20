#!/usr/bin/env python3
"""
Create Initial Admin User for OpsConductor
This script creates the first admin user in both auth and user services.
"""
import asyncio
import httpx
import hashlib
import uuid
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
AUTH_DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,  # auth-postgres port
    'database': 'auth_db',
    'user': 'auth_user',
    'password': 'auth_secure_password_2024'
}

USER_DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,  # user-postgres port
    'database': 'user_db',
    'user': 'user_user',
    'password': 'user_secure_password_2024'
}

# Admin user details
ADMIN_USER = {
    'user_id': 'admin-001',
    'username': 'admin',
    'email': 'admin@opsconductor.local',
    'password': 'admin123',  # Change this in production!
    'full_name': 'System Administrator',
    'role': 'admin',
    'permissions': ['*']  # All permissions
}

def hash_password(password: str) -> str:
    """Hash password using SHA-256 (simple for demo - use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_auth_credentials():
    """Create auth credentials in auth service database."""
    try:
        conn = psycopg2.connect(**AUTH_DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if admin user already exists
        cursor.execute("SELECT user_id FROM auth_credentials WHERE username = %s", (ADMIN_USER['username'],))
        if cursor.fetchone():
            print("✅ Admin user already exists in auth service")
            return True
        
        # Create auth credentials
        password_hash = hash_password(ADMIN_USER['password'])
        cursor.execute("""
            INSERT INTO auth_credentials (
                user_id, username, email, password_hash, 
                is_active, password_changed_at, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            ADMIN_USER['user_id'],
            ADMIN_USER['username'],
            ADMIN_USER['email'],
            password_hash,
            True,
            datetime.now(),
            datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Admin credentials created in auth service")
        return True
        
    except Exception as e:
        print(f"❌ Error creating auth credentials: {e}")
        return False

def create_user_profile():
    """Create user profile in user service database."""
    try:
        conn = psycopg2.connect(**USER_DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if admin user already exists
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (ADMIN_USER['username'],))
        if cursor.fetchone():
            print("✅ Admin user already exists in user service")
            return True
        
        # Create user profile
        cursor.execute("""
            INSERT INTO users (
                user_id, username, email, full_name, role, 
                permissions, is_active, created_at, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ADMIN_USER['user_id'],
            ADMIN_USER['username'],
            ADMIN_USER['email'],
            ADMIN_USER['full_name'],
            ADMIN_USER['role'],
            ADMIN_USER['permissions'],
            True,
            datetime.now(),
            'system'
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Admin user profile created in user service")
        return True
        
    except Exception as e:
        print(f"❌ Error creating user profile: {e}")
        return False

async def test_login():
    """Test login with the created admin user."""
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                "https://localhost/api/auth/login",
                json={
                    "username": ADMIN_USER['username'],
                    "password": ADMIN_USER['password']
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Login test successful!")
                print(f"   Token: {data.get('access_token', 'N/A')[:50]}...")
                return True
            else:
                print(f"❌ Login test failed: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing login: {e}")
        return False

def main():
    """Main function to create admin user."""
    print("🚀 Creating initial admin user for OpsConductor...")
    print(f"   Username: {ADMIN_USER['username']}")
    print(f"   Email: {ADMIN_USER['email']}")
    print(f"   Password: {ADMIN_USER['password']}")
    print()
    
    # Create auth credentials
    if not create_auth_credentials():
        print("❌ Failed to create auth credentials")
        return False
    
    # Create user profile
    if not create_user_profile():
        print("❌ Failed to create user profile")
        return False
    
    # Test login
    print("\n🧪 Testing login...")
    success = asyncio.run(test_login())
    
    if success:
        print("\n🎉 Admin user created successfully!")
        print("   You can now login at: https://localhost/login")
        print(f"   Username: {ADMIN_USER['username']}")
        print(f"   Password: {ADMIN_USER['password']}")
        print("\n⚠️  IMPORTANT: Change the default password after first login!")
    else:
        print("\n❌ Admin user creation completed but login test failed")
    
    return success

if __name__ == "__main__":
    main()