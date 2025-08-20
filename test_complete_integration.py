#!/usr/bin/env python3
"""
Complete Integration Test for Separated Auth Service
Tests the full flow: Auth Service -> Main Backend -> Frontend
"""
import requests
import json
import time

def test_auth_service_login():
    """Test login via auth service"""
    print("🔐 Testing Auth Service Login...")
    
    response = requests.post('http://localhost:8001/api/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        user = data.get('user')
        print(f"✅ Auth Service Login successful!")
        print(f"   User: {user.get('username')} ({user.get('role')})")
        print(f"   Token: {token[:50]}...")
        return token
    else:
        print(f"❌ Auth Service Login failed: {response.status_code} - {response.text}")
        return None

def test_main_backend_with_token(token):
    """Test main backend API with auth service token"""
    print("\n🔧 Testing Main Backend with Auth Token...")
    
    # Test targets endpoint
    response = requests.get('http://localhost:8000/api/v3/targets', 
                          headers={'Authorization': f'Bearer {token}'})
    
    if response.status_code == 200:
        targets = response.json()
        print(f"✅ Main Backend API successful!")
        print(f"   Retrieved {len(targets)} targets")
        return True
    else:
        print(f"❌ Main Backend API failed: {response.status_code} - {response.text}")
        return False

def test_auth_service_validation(token):
    """Test token validation via auth service"""
    print("\n🔍 Testing Auth Service Token Validation...")
    
    response = requests.post('http://localhost:8001/api/auth/validate', json={
        'token': token
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('valid'):
            user = data.get('user')
            print(f"✅ Token validation successful!")
            print(f"   Valid: {data.get('valid')}")
            print(f"   User: {user.get('username')} ({user.get('role')})")
            return True
        else:
            print(f"❌ Token validation failed: {data.get('error')}")
            return False
    else:
        print(f"❌ Token validation request failed: {response.status_code} - {response.text}")
        return False

def test_session_status(token):
    """Test session status via auth service"""
    print("\n⏰ Testing Session Status...")
    
    response = requests.get('http://localhost:8001/api/auth/session/status',
                          headers={'Authorization': f'Bearer {token}'})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Session status retrieved!")
        print(f"   Valid: {data.get('valid')}")
        print(f"   Time remaining: {data.get('time_remaining')} seconds")
        print(f"   Warning: {data.get('warning')}")
        return True
    else:
        print(f"❌ Session status failed: {response.status_code} - {response.text}")
        return False

def test_invalid_token():
    """Test main backend with invalid token"""
    print("\n🚫 Testing Main Backend with Invalid Token...")
    
    response = requests.get('http://localhost:8000/api/v3/targets', 
                          headers={'Authorization': 'Bearer invalid_token'})
    
    if response.status_code == 401:
        print(f"✅ Invalid token correctly rejected!")
        print(f"   Response: {response.json().get('detail')}")
        return True
    else:
        print(f"❌ Invalid token should have been rejected: {response.status_code}")
        return False

def test_logout(token):
    """Test logout via auth service"""
    print("\n🚪 Testing Logout...")
    
    response = requests.post('http://localhost:8001/api/auth/logout',
                           headers={'Authorization': f'Bearer {token}'})
    
    if response.status_code == 200:
        print(f"✅ Logout successful!")
        
        # Test that token is now invalid
        print("   Verifying token is now invalid...")
        response = requests.get('http://localhost:8000/api/v3/targets', 
                              headers={'Authorization': f'Bearer {token}'})
        
        if response.status_code == 401:
            print("   ✅ Token correctly invalidated after logout!")
            return True
        else:
            print(f"   ❌ Token should be invalid after logout: {response.status_code}")
            return False
    else:
        print(f"❌ Logout failed: {response.status_code} - {response.text}")
        return False

def main():
    """Run complete integration test"""
    print("🚀 Starting Complete Integration Test")
    print("=" * 60)
    
    # Test 1: Login via auth service
    token = test_auth_service_login()
    if not token:
        print("\n❌ Integration test failed at login step")
        return False
    
    # Test 2: Use token with main backend
    if not test_main_backend_with_token(token):
        print("\n❌ Integration test failed at main backend step")
        return False
    
    # Test 3: Validate token via auth service
    if not test_auth_service_validation(token):
        print("\n❌ Integration test failed at token validation step")
        return False
    
    # Test 4: Check session status
    if not test_session_status(token):
        print("\n❌ Integration test failed at session status step")
        return False
    
    # Test 5: Test invalid token rejection
    if not test_invalid_token():
        print("\n❌ Integration test failed at invalid token test")
        return False
    
    # Test 6: Logout and verify token invalidation
    if not test_logout(token):
        print("\n❌ Integration test failed at logout step")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL INTEGRATION TESTS PASSED!")
    print("✅ Auth Service is working correctly")
    print("✅ Main Backend integration is working correctly")
    print("✅ Token validation is working correctly")
    print("✅ Session management is working correctly")
    print("✅ Security (invalid token rejection) is working correctly")
    print("✅ Logout and token invalidation is working correctly")
    print("\n🏗️ The separated auth architecture is fully functional!")
    
    return True

if __name__ == "__main__":
    main()