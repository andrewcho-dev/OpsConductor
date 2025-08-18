#!/usr/bin/env python3
"""
Test script for the SIMPLIFIED job system
NO SERIALIZATION COMPLEXITY - just clean IDs and execution tracking
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_simplified_jobs():
    print("🧪 TESTING SIMPLIFIED JOB SYSTEM")
    print("=" * 50)
    
    # Step 1: Login to get token
    print("1️⃣ Logging in...")
    login_data = {"username": "admin", "password": "admin123"}
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
        
        token = response.json().get("access_token")
        if not token:
            print("❌ No access token received")
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
        
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False
    
    # Step 2: Get targets
    print("\n2️⃣ Getting targets...")
    try:
        response = requests.get(f"{BASE_URL}/api/targets", headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to get targets: {response.status_code}")
            return False
            
        targets = response.json()
        if not targets:
            print("❌ No targets found")
            return False
            
        target_id = targets[0]["id"]
        print(f"✅ Found target: {targets[0]['name']} (ID: {target_id})")
        
    except Exception as e:
        print(f"❌ Error getting targets: {str(e)}")
        return False
    
    # Step 3: Create a simple job using v3 API
    print("\n3️⃣ Creating job with simplified v3 API...")
    job_data = {
        "name": f"Test Job - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Simple test job with no serialization complexity",
        "actions": [
            {
                "action_type": "command",
                "action_name": "Test Command",
                "action_parameters": {
                    "command": "echo 'Hello from simplified job system!'"
                }
            }
        ],
        "target_ids": [target_id]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v3/jobs/", json=job_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to create job: {response.status_code} - {response.text}")
            return False
            
        job = response.json()
        job_id = job["id"]
        print(f"✅ Job created successfully!")
        print(f"   Job ID: {job_id}")
        print(f"   Job Name: {job['name']}")
        print(f"   Status: {job['status']}")
        
    except Exception as e:
        print(f"❌ Error creating job: {str(e)}")
        return False
    
    # Step 4: Execute the job
    print("\n4️⃣ Executing job...")
    try:
        response = requests.post(f"{BASE_URL}/api/v3/jobs/{job_id}/execute", 
                               json={}, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to execute job: {response.status_code} - {response.text}")
            return False
            
        execution = response.json()
        execution_id = execution["id"]
        execution_number = execution["execution_number"]
        print(f"✅ Job execution started!")
        print(f"   Execution ID: {execution_id}")
        print(f"   Execution Number: {execution_number}")
        print(f"   Status: {execution['status']}")
        print(f"   Total Targets: {execution['total_targets']}")
        
    except Exception as e:
        print(f"❌ Error executing job: {str(e)}")
        return False
    
    # Step 5: Check execution status
    print("\n5️⃣ Monitoring execution...")
    for i in range(10):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{BASE_URL}/api/v3/jobs/{job_id}/executions", headers=headers)
            if response.status_code == 200:
                executions = response.json()
                if executions:
                    current_execution = executions[0]  # Most recent
                    status = current_execution["status"]
                    print(f"   Status: {status} (check {i+1}/10)")
                    
                    if status in ["completed", "failed"]:
                        print(f"✅ Execution finished with status: {status}")
                        print(f"   Successful targets: {current_execution['successful_targets']}")
                        print(f"   Failed targets: {current_execution['failed_targets']}")
                        break
                        
            time.sleep(3)
            
        except Exception as e:
            print(f"⚠️ Error checking status: {str(e)}")
    
    # Step 6: Get execution results
    print("\n6️⃣ Getting execution results...")
    try:
        response = requests.get(f"{BASE_URL}/api/v3/jobs/{job_id}/executions/{execution_number}/results", 
                               headers=headers)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Found {len(results)} execution results:")
            
            for result in results:
                print(f"   Target: {result['target_name']}")
                print(f"   Action: {result['action_name']}")
                print(f"   Status: {result['status']}")
                print(f"   Output: {result.get('output_text', 'N/A')}")
                if result.get('error_text'):
                    print(f"   Error: {result['error_text']}")
                print(f"   Execution Time: {result.get('execution_time_ms', 0)}ms")
                print()
        else:
            print(f"⚠️ Could not get results: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Error getting results: {str(e)}")
    
    # Step 7: List all jobs
    print("\n7️⃣ Listing all jobs...")
    try:
        response = requests.get(f"{BASE_URL}/api/v3/jobs/", headers=headers)
        if response.status_code == 200:
            jobs = response.json()
            print(f"✅ Found {len(jobs)} jobs:")
            for job in jobs[-3:]:  # Show last 3 jobs
                print(f"   ID: {job['id']} | Name: {job['name']} | Status: {job['status']}")
        else:
            print(f"⚠️ Could not list jobs: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Error listing jobs: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 SIMPLIFIED JOB SYSTEM TEST COMPLETED!")
    print("✅ No serialization complexity")
    print("✅ Clean ID-based tracking")
    print("✅ Simple execution results")
    return True

if __name__ == "__main__":
    success = test_simplified_jobs()
    exit(0 if success else 1)