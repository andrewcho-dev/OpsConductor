#!/usr/bin/env python3
"""
Auth Service Test Suite
Tests the Auth Service API endpoints with v1 standardization
"""

import requests
import json
import time
from typing import Dict, Optional

class AuthServiceTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        print("🔍 Testing health check...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_service_info(self) -> bool:
        """Test service info endpoint (v1 API)"""
        print("🔍 Testing service info (v1 API)...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/info", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Service info passed: {data}")
                return data.get("service") == "auth-service"
            else:
                print(f"❌ Service info failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Service info error: {e}")
            return False
    
    def test_list_users(self) -> bool:
        """Test list users endpoint"""
        print("🔍 Testing list users...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/auth/users", timeout=5)
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                print(f"✅ List users passed: Found {len(users)} users")
                return len(users) >= 3  # Should have admin, user, testuser
            else:
                print(f"❌ List users failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ List users error: {e}")
            return False
    
    def test_login(self, username: str, password: str) -> bool:
        """Test login endpoint"""
        print(f"🔍 Testing login for {username}...")
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": username, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                user = data.get("user", {})
                print(f"✅ Login successful: {user.get('username')} ({user.get('role')})")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_token_validation(self) -> bool:
        """Test token validation endpoint"""
        print("🔍 Testing token validation...")
        if not self.token:
            print("❌ No token available for validation")
            return False
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/validate",
                json={"token": self.token},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                valid = data.get("valid", False)
                user = data.get("user", {})
                print(f"✅ Token validation: valid={valid}, user={user.get('username')}")
                return valid
            else:
                print(f"❌ Token validation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Token validation error: {e}")
            return False
    
    def test_session_status(self) -> bool:
        """Test session status endpoint"""
        print("🔍 Testing session status...")
        if not self.token:
            print("❌ No token available for session status")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.session.get(
                f"{self.base_url}/api/v1/auth/session/status",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                active = data.get("active", False)
                user = data.get("user", {})
                print(f"✅ Session status: active={active}, user={user.get('username')}")
                return active
            else:
                print(f"❌ Session status failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Session status error: {e}")
            return False
    
    def test_list_sessions(self) -> bool:
        """Test list sessions endpoint"""
        print("🔍 Testing list sessions...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/auth/sessions", timeout=5)
            if response.status_code == 200:
                data = response.json()
                sessions = data.get("active_sessions", [])
                total = data.get("total", 0)
                print(f"✅ List sessions passed: {total} active sessions")
                return total >= 1  # Should have at least our session
            else:
                print(f"❌ List sessions failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ List sessions error: {e}")
            return False
    
    def test_logout(self) -> bool:
        """Test logout endpoint"""
        print("🔍 Testing logout...")
        if not self.token:
            print("❌ No token available for logout")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/logout",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Logout successful: {data.get('message')}")
                self.token = None
                return True
            else:
                print(f"❌ Logout failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Logout error: {e}")
            return False
    
    def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run comprehensive test suite"""
        print("🧪 Starting Auth Service Comprehensive Test Suite")
        print("=" * 60)
        
        results = {}
        
        # Test order matters for stateful operations
        test_cases = [
            ("Health Check", self.test_health_check),
            ("Service Info (v1 API)", self.test_service_info), 
            ("List Users", self.test_list_users),
            ("Login (admin)", lambda: self.test_login("admin", "admin123")),
            ("Token Validation", self.test_token_validation),
            ("Session Status", self.test_session_status),
            ("List Active Sessions", self.test_list_sessions),
            ("Logout", self.test_logout),
        ]
        
        for test_name, test_func in test_cases:
            print(f"\n🔄 Running: {test_name}")
            try:
                results[test_name] = test_func()
                status = "PASS" if results[test_name] else "FAIL"
                print(f"   Result: {status}")
            except Exception as e:
                print(f"   Result: ERROR - {e}")
                results[test_name] = False
            
            time.sleep(0.5)  # Small delay between tests
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! Auth service is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the auth service configuration.")
        
        return results

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Auth Service API")
    parser.add_argument("--url", default="http://localhost:8001", 
                        help="Auth service base URL (default: http://localhost:8001)")
    parser.add_argument("--wait", type=int, default=5,
                        help="Wait time before starting tests (default: 5 seconds)")
    
    args = parser.parse_args()
    
    print(f"🚀 Auth Service Tester")
    print(f"Target: {args.url}")
    print(f"Waiting {args.wait} seconds for service to be ready...")
    time.sleep(args.wait)
    
    tester = AuthServiceTester(args.url)
    results = tester.run_comprehensive_test()
    
    # Exit code based on results
    exit_code = 0 if all(results.values()) else 1
    exit(exit_code)

if __name__ == "__main__":
    main()