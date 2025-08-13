#!/usr/bin/env python3
"""
Test script to verify the job termination API endpoint
"""

import requests
import json
import sys

def test_terminate_api():
    # First, let's test if we can reach the API
    base_url = "http://localhost/api"
    
    print("🔍 Testing job termination API...")
    
    # Test 1: Check if the endpoint exists (should return 401 without auth)
    try:
        response = requests.post(f"{base_url}/jobs/safety/terminate/999", 
                               json={"reason": "test"})
        print(f"✅ API endpoint reachable. Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Authentication required (expected)")
        elif response.status_code == 404:
            print("❌ Endpoint not found - check routing")
        else:
            print(f"ℹ️  Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is the server running?")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_terminate_api()