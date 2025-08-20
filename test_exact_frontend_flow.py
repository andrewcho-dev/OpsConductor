#!/usr/bin/env python3
"""
Test the exact frontend login flow to identify the 401 issue
"""
import requests
import json
import time

BASE_URL = "https://192.168.50.100"  # Same as frontend

def test_exact_frontend_flow():
    """Test the exact same flow the frontend uses"""
    print("🔐 Testing Exact Frontend Login Flow...")
    print(f"Using base URL: {BASE_URL}")
    
    # Step 1: Login via auth service (same as frontend)
    print("\n1️⃣ Step 1: Login via auth service...")
    try:
        login_response = requests.post(f'{BASE_URL}/api/auth/login', 
                                     json={'username': 'admin', 'password': 'admin123'},
                                     verify=False,
                                     timeout=10)
        
        print(f"Login status: {login_response.status_code}")
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        login_data = login_response.json()
        token = login_data.get('access_token')
        
        print(f"✅ Login successful!")
        print(f"   Token: {token[:50]}...")
        print(f"   User: {login_data.get('user', {}).get('username')}")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Immediately call /me endpoint (same timing as frontend)
    print("\n2️⃣ Step 2: Get user data from /me endpoint (immediate call)...")
    try:
        me_response = requests.get(f'{BASE_URL}/api/v3/auth/me',
                                 headers={
                                     'Authorization': f'Bearer {token}',
                                     'Content-Type': 'application/json'
                                 },
                                 verify=False,
                                 timeout=10)
        
        print(f"/me status: {me_response.status_code}")
        if me_response.status_code == 200:
            me_data = me_response.json()
            print(f"✅ /me endpoint successful!")
            print(f"   User: {me_data.get('username')} ({me_data.get('role')})")
            return True
        else:
            print(f"❌ /me endpoint failed: {me_response.text}")
            
            # Let's try with a small delay
            print("\n🔄 Retrying /me endpoint with 1 second delay...")
            time.sleep(1)
            
            retry_response = requests.get(f'{BASE_URL}/api/v3/auth/me',
                                        headers={
                                            'Authorization': f'Bearer {token}',
                                            'Content-Type': 'application/json'
                                        },
                                        verify=False,
                                        timeout=10)
            
            print(f"Retry status: {retry_response.status_code}")
            if retry_response.status_code == 200:
                print("✅ /me endpoint worked with delay!")
                return True
            else:
                print(f"❌ /me endpoint still failed: {retry_response.text}")
                return False
                
    except Exception as e:
        print(f"❌ /me endpoint error: {e}")
        return False

def test_token_validation_directly():
    """Test token validation directly with auth service"""
    print("\n🔍 Testing token validation directly...")
    
    # Get a fresh token
    login_response = requests.post(f'{BASE_URL}/api/auth/login', 
                                 json={'username': 'admin', 'password': 'admin123'},
                                 verify=False)
    
    if login_response.status_code != 200:
        print("❌ Could not get token for validation test")
        return
    
    token = login_response.json().get('access_token')
    print(f"Token for validation: {token[:50]}...")
    
    # Test validation endpoint directly
    validate_response = requests.post(f'{BASE_URL}/api/auth/validate',
                                    json={'token': token},
                                    verify=False)
    
    print(f"Validation status: {validate_response.status_code}")
    if validate_response.status_code == 200:
        validation_data = validate_response.json()
        print(f"Validation result: valid={validation_data.get('valid')}")
        if validation_data.get('error'):
            print(f"Validation error: {validation_data.get('error')}")
    else:
        print(f"Validation failed: {validate_response.text}")

def main():
    print("🚀 Testing Exact Frontend Login Flow")
    print("=" * 60)
    
    # Test the exact frontend flow
    success = test_exact_frontend_flow()
    
    # Test token validation directly
    test_token_validation_directly()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 FRONTEND LOGIN FLOW TEST PASSED!")
    else:
        print("❌ Frontend login flow test failed")
        print("💡 This explains the 401 error in the browser")

if __name__ == "__main__":
    main()