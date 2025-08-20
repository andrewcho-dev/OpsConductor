#!/usr/bin/env python3
"""
Debug the exact token validation issue
"""
import requests
import json
import time

def debug_token_validation():
    """Debug why tokens are failing validation"""
    print("🔍 Debugging Token Validation Issue")
    print("=" * 50)
    
    # Step 1: Get a fresh token
    print("1. Getting fresh token...")
    login_resp = requests.post('https://localhost/api/auth/login',
                             json={'username': 'admin', 'password': 'admin123'},
                             verify=False)
    
    if login_resp.status_code != 200:
        print(f"❌ Login failed: {login_resp.status_code}")
        return
    
    login_data = login_resp.json()
    token = login_data['access_token']
    session_id = login_data.get('session_id')
    
    print(f"✅ Login successful")
    print(f"   Token: {token[:50]}...")
    print(f"   Session ID: {session_id}")
    
    # Step 2: Test validation immediately
    print("\n2. Testing validation immediately...")
    validate_resp = requests.post('https://localhost/api/auth/validate',
                                json={'token': token},
                                verify=False)
    
    print(f"Validation status: {validate_resp.status_code}")
    if validate_resp.status_code == 200:
        validate_data = validate_resp.json()
        print(f"Validation result: {json.dumps(validate_data, indent=2)}")
    else:
        print(f"Validation failed: {validate_resp.text}")
    
    # Step 3: Test /me endpoint immediately
    print("\n3. Testing /me endpoint immediately...")
    me_resp = requests.get('https://localhost/api/v3/auth/me',
                         headers={'Authorization': f'Bearer {token}'},
                         verify=False)
    
    print(f"/me status: {me_resp.status_code}")
    if me_resp.status_code == 200:
        print(f"✅ /me worked: {me_resp.json()}")
    else:
        print(f"❌ /me failed: {me_resp.text}")
    
    # Step 4: Wait a moment and test again
    print("\n4. Waiting 2 seconds and testing again...")
    time.sleep(2)
    
    validate_resp2 = requests.post('https://localhost/api/auth/validate',
                                 json={'token': token},
                                 verify=False)
    
    print(f"Validation status (after wait): {validate_resp2.status_code}")
    if validate_resp2.status_code == 200:
        validate_data2 = validate_resp2.json()
        print(f"Validation result: valid={validate_data2.get('valid')}")
        if not validate_data2.get('valid'):
            print(f"❌ Token became invalid! Error: {validate_data2.get('error')}")
    
    me_resp2 = requests.get('https://localhost/api/v3/auth/me',
                          headers={'Authorization': f'Bearer {token}'},
                          verify=False)
    
    print(f"/me status (after wait): {me_resp2.status_code}")
    
    # Step 5: Check if multiple requests cause issues
    print("\n5. Testing multiple concurrent requests...")
    import threading
    
    results = []
    
    def test_me_endpoint():
        resp = requests.get('https://localhost/api/v3/auth/me',
                          headers={'Authorization': f'Bearer {token}'},
                          verify=False)
        results.append(resp.status_code)
    
    # Make 3 concurrent requests
    threads = []
    for i in range(3):
        t = threading.Thread(target=test_me_endpoint)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print(f"Concurrent request results: {results}")
    success_count = len([r for r in results if r == 200])
    print(f"Success rate: {success_count}/3")

if __name__ == "__main__":
    debug_token_validation()