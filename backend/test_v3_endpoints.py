#!/usr/bin/env python3
"""
Test all v3 API endpoints to ensure they work properly
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_v3_endpoints():
    print("🧪 TESTING ALL v3 API ENDPOINTS")
    print("=" * 50)
    
    # Login
    print("1️⃣ Login...")
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return False
    
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Test all v3 endpoints
    endpoints_to_test = [
        ("GET", "/api/v3/jobs/", "List jobs"),
        ("GET", "/api/targets", "List targets"),
    ]
    
    for method, endpoint, description in endpoints_to_test:
        print(f"\n2️⃣ Testing {method} {endpoint} - {description}")
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json={})
            
            if response.status_code in [200, 201]:
                data = response.json()
                if isinstance(data, list):
                    print(f"✅ {description}: Found {len(data)} items")
                elif isinstance(data, dict):
                    print(f"✅ {description}: Response received")
                else:
                    print(f"✅ {description}: Success")
            else:
                print(f"⚠️ {description}: Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description}: Error - {str(e)}")
    
    # Test job creation and execution flow
    print(f"\n3️⃣ Testing job creation and execution flow...")
    
    # Get a target first
    response = requests.get(f"{BASE_URL}/api/targets", headers=headers)
    if response.status_code == 200:
        targets = response.json()
        if targets:
            target_id = targets[0]["id"]
            print(f"✅ Using target: {targets[0]['name']} (ID: {target_id})")
            
            # Create job
            job_data = {
                "name": f"v3 API Test Job - {datetime.now().strftime('%H%M%S')}",
                "description": "Testing v3 API endpoints",
                "actions": [
                    {
                        "action_type": "command",
                        "action_name": "Test Command",
                        "action_parameters": {
                            "command": "echo 'v3 API test successful'"
                        }
                    }
                ],
                "target_ids": [target_id]
            }
            
            response = requests.post(f"{BASE_URL}/api/v3/jobs/", json=job_data, headers=headers)
            if response.status_code == 200:
                job = response.json()
                job_id = job["id"]
                print(f"✅ Job created: ID {job_id}")
                
                # Execute job
                response = requests.post(f"{BASE_URL}/api/v3/jobs/{job_id}/execute", 
                                       json={}, headers=headers)
                if response.status_code == 200:
                    execution = response.json()
                    print(f"✅ Job executed: Execution ID {execution['id']}")
                    
                    # Get executions
                    response = requests.get(f"{BASE_URL}/api/v3/jobs/{job_id}/executions", 
                                          headers=headers)
                    if response.status_code == 200:
                        executions = response.json()
                        print(f"✅ Found {len(executions)} executions")
                        
                        if executions:
                            execution_number = executions[0]["execution_number"]
                            # Get results
                            response = requests.get(
                                f"{BASE_URL}/api/v3/jobs/{job_id}/executions/{execution_number}/results", 
                                headers=headers
                            )
                            if response.status_code == 200:
                                results = response.json()
                                print(f"✅ Found {len(results)} execution results")
                            else:
                                print(f"⚠️ Results endpoint: Status {response.status_code}")
                    else:
                        print(f"⚠️ Executions endpoint: Status {response.status_code}")
                else:
                    print(f"⚠️ Execute endpoint: Status {response.status_code}")
            else:
                print(f"⚠️ Create job: Status {response.status_code}")
        else:
            print("⚠️ No targets found for testing")
    else:
        print(f"⚠️ Could not get targets: Status {response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 v3 API ENDPOINT TESTING COMPLETED!")
    return True

if __name__ == "__main__":
    test_v3_endpoints()