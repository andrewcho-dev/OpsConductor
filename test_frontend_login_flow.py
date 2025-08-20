#!/usr/bin/env python3
"""
Test the complete frontend login flow with separated auth service
"""
import requests
import json

BASE_URL = "https://localhost"

def test_complete_login_flow():
    """Test the complete login flow that the frontend uses"""
    print("🔐 Testing Complete Frontend Login Flow...")
    
    # Step 1: Login via auth service
    print("\n1️⃣ Step 1: Login via auth service...")
    login_response = requests.post(f'{BASE_URL}/api/auth/login', 
                                 json={'username': 'admin', 'password': 'admin123'},
                                 verify=False)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        return False
    
    login_data = login_response.json()
    token = login_data.get('access_token')
    user_from_login = login_data.get('user')
    
    print(f"✅ Login successful!")
    print(f"   Token: {token[:50]}...")
    print(f"   User from login: {user_from_login.get('username')} ({user_from_login.get('role')})")
    
    # Step 2: Get user data from main backend /me endpoint
    print("\n2️⃣ Step 2: Get user data from main backend /me endpoint...")
    me_response = requests.get(f'{BASE_URL}/api/v3/auth/me',
                             headers={'Authorization': f'Bearer {token}'},
                             verify=False)
    
    if me_response.status_code != 200:
        print(f"❌ /me endpoint failed: {me_response.status_code} - {me_response.text}")
        return False
    
    me_data = me_response.json()
    print(f"✅ /me endpoint successful!")
    print(f"   User from /me: {me_data.get('username')} ({me_data.get('role')})")
    print(f"   Email: {me_data.get('email')}")
    print(f"   Active: {me_data.get('is_active')}")
    
    # Step 3: Test main backend API access
    print("\n3️⃣ Step 3: Test main backend API access...")
    targets_response = requests.get(f'{BASE_URL}/api/v3/targets',
                                  headers={'Authorization': f'Bearer {token}'},
                                  verify=False)
    
    if targets_response.status_code != 200:
        print(f"❌ Main API failed: {targets_response.status_code} - {targets_response.text}")
        return False
    
    targets = targets_response.json()
    print(f"✅ Main API access successful!")
    print(f"   Retrieved {len(targets)} targets")
    
    # Step 4: Test logout via auth service
    print("\n4️⃣ Step 4: Test logout via auth service...")
    logout_response = requests.post(f'{BASE_URL}/api/auth/logout',
                                  headers={'Authorization': f'Bearer {token}'},
                                  verify=False)
    
    if logout_response.status_code != 200:
        print(f"❌ Logout failed: {logout_response.status_code} - {logout_response.text}")
        return False
    
    print(f"✅ Logout successful!")
    
    # Step 5: Verify token is now invalid
    print("\n5️⃣ Step 5: Verify token is now invalid...")
    test_response = requests.get(f'{BASE_URL}/api/v3/targets',
                               headers={'Authorization': f'Bearer {token}'},
                               verify=False)
    
    if test_response.status_code == 401:
        print(f"✅ Token correctly invalidated after logout!")
        return True
    else:
        print(f"❌ Token should be invalid: {test_response.status_code}")
        return False

def main():
    print("🚀 Testing Complete Frontend Login Flow")
    print("=" * 60)
    
    if test_complete_login_flow():
        print("\n" + "=" * 60)
        print("🎉 COMPLETE FRONTEND LOGIN FLOW TEST PASSED!")
        print("✅ Auth service login works")
        print("✅ Main backend /me endpoint works")
        print("✅ Main backend API access works")
        print("✅ Auth service logout works")
        print("✅ Token invalidation works")
        print("\n🌐 Frontend should now work correctly!")
    else:
        print("\n❌ Frontend login flow test failed")

if __name__ == "__main__":
    main()