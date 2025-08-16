#!/usr/bin/env python3
"""
Simple test script to verify health API endpoints are working
"""

import requests
import json
import sys

def test_health_endpoint(url, description):
    """Test a health endpoint"""
    print(f"\n🔍 Testing {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS - Response received")
            print(f"Status: {data.get('status', 'unknown')}")
            if 'timestamp' in data:
                print(f"Timestamp: {data['timestamp']}")
            return True
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ FAILED - Connection refused (server not running?)")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ FAILED - Request timeout")
        return False
    except Exception as e:
        print(f"❌ FAILED - {str(e)}")
        return False

def main():
    """Test all health endpoints"""
    print("🏥 Health API Test Suite")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    endpoints = [
        (f"{base_url}/api/v2/health/", "Overall Health"),
        (f"{base_url}/api/v2/health/system", "System Health"),
        (f"{base_url}/api/v2/health/database", "Database Health"),
        (f"{base_url}/api/v2/health/application", "Application Health"),
        (f"{base_url}/health", "Basic Health Check"),
    ]
    
    results = []
    
    for url, description in endpoints:
        success = test_health_endpoint(url, description)
        results.append((description, success))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {description}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Health API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the backend server.")
        return 1

if __name__ == "__main__":
    sys.exit(main())