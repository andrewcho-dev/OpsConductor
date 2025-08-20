#!/usr/bin/env python3
"""
Test the exact token that the frontend would get
"""
import requests
import json

def test_frontend_token():
    """Test the exact same flow as frontend"""
    print("🔍 Testing Frontend Token Flow")
    print("=" * 40)
    
    # Step 1: Login exactly like frontend does
    print("1. Login via auth service (frontend style)...")
    login_resp = requests.post('https://192.168.50.100/api/auth/login',
                             json={'username': 'admin', 'password': 'admin123'},
                             headers={'Content-Type': 'application/json'},
                             verify=False)
    
    if login_resp.status_code != 200:
        print(f"❌ Login failed: {login_resp.status_code}")
        return
    
    login_data = login_resp.json()
    token = login_data['access_token']
    
    print(f"✅ Login successful")
    print(f"   Token: {token}")
    print(f"   Session ID: {login_data.get('session_id')}")
    
    # Step 2: Test validation with this exact token
    print(f"\n2. Testing validation with this exact token...")
    validate_resp = requests.post('https://192.168.50.100/api/auth/validate',
                                json={'token': token},
                                headers={'Content-Type': 'application/json'},
                                verify=False)
    
    print(f"Validation status: {validate_resp.status_code}")
    if validate_resp.status_code == 200:
        validate_data = validate_resp.json()
        print(f"Validation result: {json.dumps(validate_data, indent=2)}")
        
        if not validate_data.get('valid'):
            print(f"❌ TOKEN IS INVALID!")
            print(f"   Error: {validate_data.get('error')}")
    else:
        print(f"❌ Validation request failed: {validate_resp.text}")
    
    # Step 3: Test /me with this exact token
    print(f"\n3. Testing /me with this exact token...")
    me_resp = requests.get('https://192.168.50.100/api/v3/auth/me',
                         headers={
                             'Authorization': f'Bearer {token}',
                             'Content-Type': 'application/json'
                         },
                         verify=False)
    
    print(f"/me status: {me_resp.status_code}")
    if me_resp.status_code == 200:
        print(f"✅ /me worked!")
    else:
        print(f"❌ /me failed: {me_resp.text}")

if __name__ == "__main__":
    test_frontend_token()