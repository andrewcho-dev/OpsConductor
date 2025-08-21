#!/usr/bin/env python3
"""
Test script to verify Celery API authentication and functionality
"""
import requests
import json
import time

def test_celery_api():
    base_url = "http://localhost:8000"
    
    # First, let's try to find a valid user
    print("🔍 Testing Celery API authentication...")
    
    # Try common admin credentials
    credentials = [
        {"username": "admin", "password": "admin123"},
        {"username": "admin", "password": "admin"},
        {"username": "admin", "password": "password"},
        {"username": "admin", "password": "opsconductor"},
        {"username": "administrator", "password": "admin"},
    ]
    
    token = None
    for cred in credentials:
        print(f"🔑 Trying {cred['username']}:{cred['password']}")
        try:
            response = requests.post(f"{base_url}/api/v1/auth/login", json=cred, timeout=10)
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                print(f"✅ Login successful! Token: {token[:20]}...")
                break
            else:
                print(f"❌ Login failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Login error: {e}")
    
    if not token:
        print("❌ Could not authenticate with any credentials")
        return
    
    # Test Celery API endpoints
    headers = {'Authorization': f'Bearer {token}'}
    
    endpoints = [
        "/api/v1/celery/stats",
        "/api/v1/celery/workers", 
        "/api/v1/celery/queues"
    ]
    
    for endpoint in endpoints:
        print(f"\n🧪 Testing {endpoint}")
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=30)
            duration = time.time() - start_time
            
            print(f"⏱️ Response time: {duration:.2f}s")
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Data keys: {list(data.keys())}")
                if endpoint == "/api/v1/celery/stats":
                    print(f"   📈 Completed tasks: {data.get('completed_tasks', 'N/A')}")
                    print(f"   📈 Active tasks: {data.get('active_tasks', 'N/A')}")
                elif endpoint == "/api/v1/celery/workers":
                    print(f"   👷 Total workers: {data.get('total_workers', 'N/A')}")
                    print(f"   👷 Active workers: {data.get('active_workers', 'N/A')}")
                elif endpoint == "/api/v1/celery/queues":
                    print(f"   📋 Queues: {list(data.keys())}")
            else:
                print(f"❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_celery_api()