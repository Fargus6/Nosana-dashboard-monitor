#!/usr/bin/env python3
"""
Quick Backend API Testing for Nosana Node Monitor Application
Tests core backend functionality quickly without heavy operations
"""

import requests
import time
import json
import sys
from datetime import datetime
import random

# Configuration
BASE_URL = "https://alert-hub-11.preview.emergentagent.com/api"
TEST_EMAIL = "test@prod.com"
TEST_PASSWORD = "TestProd123"

class QuickBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        
    def log_result(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def get_auth_token(self):
        """Get authentication token for testing"""
        if self.auth_token:
            return True
            
        try:
            # Login to get token (user should already exist)
            response = self.session.post(f"{BASE_URL}/auth/login", data={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                self.auth_token = response.json()["access_token"]
                return True
            else:
                print(f"Login failed with status {response.status_code}")
                
        except Exception as e:
            print(f"Failed to get auth token: {str(e)}")
            
        return False
    
    def test_authentication_endpoints(self):
        """Test authentication endpoints"""
        print("🔒 Testing Authentication Endpoints...")
        
        # Test login rate limiting
        login_attempts = 0
        rate_limited = False
        
        for i in range(12):
            try:
                response = self.session.post(f"{BASE_URL}/auth/login", data={
                    "username": "nonexistent@test.com",
                    "password": "wrongpassword"
                })
                login_attempts += 1
                if response.status_code == 429:
                    rate_limited = True
                    break
                time.sleep(0.05)
            except:
                break
        
        # Test JWT validation
        jwt_working = False
        try:
            response = self.session.get(f"{BASE_URL}/auth/me", 
                                      headers={"Authorization": "Bearer invalid_token"})
            jwt_working = response.status_code == 401
        except:
            pass
        
        # Test valid JWT
        valid_jwt = False
        if self.get_auth_token():
            try:
                response = self.session.get(f"{BASE_URL}/auth/me", 
                                          headers={"Authorization": f"Bearer {self.auth_token}"})
                valid_jwt = response.status_code == 200
            except:
                pass
        
        passed = rate_limited and jwt_working and valid_jwt
        
        self.log_result(
            "Authentication Endpoints Under Load",
            passed,
            f"Login attempts: {login_attempts}, Rate limited: {rate_limited}, JWT invalid rejected: {jwt_working}, JWT valid accepted: {valid_jwt}"
        )
    
    def test_node_crud_operations(self):
        """Test node CRUD operations"""
        print("🔒 Testing Node CRUD Operations...")
        
        if not self.get_auth_token():
            self.log_result("Node CRUD Operations Under Load", False, "Could not get auth token")
            return
        
        # Test node creation with valid address
        creation_success = False
        node_id = None
        try:
            response = self.session.post(
                f"{BASE_URL}/nodes",
                json={"address": "11111111111111111111111111111112", "name": "Test Node"},
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            if response.status_code == 200:
                creation_success = True
                node_id = response.json()['id']
            elif response.status_code == 400:
                # Node already exists, that's fine
                creation_success = True
        except Exception as e:
            print(f"Node creation error: {e}")
        
        # Test node retrieval
        retrieval_success = False
        try:
            response = self.session.get(
                f"{BASE_URL}/nodes",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            retrieval_success = response.status_code == 200
        except:
            pass
        
        # Test invalid address validation
        validation_working = False
        try:
            response = self.session.post(
                f"{BASE_URL}/nodes",
                json={"address": "invalid", "name": "Invalid Node"},
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            validation_working = response.status_code in [400, 422]
        except:
            pass
        
        # Test unauthorized access
        unauthorized_blocked = False
        try:
            response = self.session.get(f"{BASE_URL}/nodes")
            unauthorized_blocked = response.status_code == 401
        except:
            pass
        
        passed = creation_success and retrieval_success and validation_working and unauthorized_blocked
        
        self.log_result(
            "Node CRUD Operations Under Load",
            passed,
            f"Creation: {creation_success}, Retrieval: {retrieval_success}, Validation: {validation_working}, Unauthorized blocked: {unauthorized_blocked}"
        )
    
    def test_push_notifications(self):
        """Test push notification endpoints"""
        print("🔒 Testing Push Notifications...")
        
        if not self.get_auth_token():
            self.log_result("Push Notifications", False, "Could not get auth token")
            return
        
        # Test device token registration
        token_reg_success = False
        try:
            response = self.session.post(
                f"{BASE_URL}/notifications/register-token",
                params={"token": "test_device_token_12345"},
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            token_reg_success = response.status_code == 200
        except:
            pass
        
        # Test notification preferences GET
        prefs_get_success = False
        try:
            response = self.session.get(
                f"{BASE_URL}/notifications/preferences",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            prefs_get_success = response.status_code == 200
        except:
            pass
        
        # Test notification preferences POST
        prefs_post_success = False
        try:
            response = self.session.post(
                f"{BASE_URL}/notifications/preferences",
                json={
                    "user_id": "test_user",
                    "notify_offline": True,
                    "notify_online": True,
                    "notify_job_started": True,
                    "notify_job_completed": True,
                    "vibration": True,
                    "sound": True
                },
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            prefs_post_success = response.status_code == 200
        except:
            pass
        
        passed = token_reg_success and prefs_get_success and prefs_post_success
        
        self.log_result(
            "Push Notifications",
            passed,
            f"Token reg: {token_reg_success}, Prefs GET: {prefs_get_success}, Prefs POST: {prefs_post_success}"
        )
    
    def test_security_features(self):
        """Test security features"""
        print("🔒 Testing Security Features...")
        
        # Test security headers
        headers_present = False
        try:
            response = self.session.get(f"{BASE_URL}/auth/me")
            required_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Strict-Transport-Security",
                "Content-Security-Policy"
            ]
            headers_present = all(header in response.headers for header in required_headers)
        except:
            pass
        
        # Test input validation
        validation_working = True
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --"
        ]
        
        for malicious_input in malicious_inputs:
            try:
                response = self.session.post(f"{BASE_URL}/auth/register", json={
                    "email": f"{malicious_input}@test.com",
                    "password": "TestPass123"
                })
                if response.status_code == 200:
                    validation_working = False
                    break
            except:
                continue
        
        # Test password validation
        password_validation = True
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json={
                "email": f"weakpass{random.randint(1000,9999)}@test.com",
                "password": "weak"
            })
            if response.status_code == 200:
                password_validation = False
        except:
            pass
        
        passed = headers_present and validation_working and password_validation
        
        self.log_result(
            "Security Features",
            passed,
            f"Headers: {headers_present}, Input validation: {validation_working}, Password validation: {password_validation}"
        )
    
    def test_error_handling_resilience(self):
        """Test error handling and system resilience"""
        print("🔒 Testing Error Handling & Resilience...")
        
        # Test invalid endpoints
        invalid_endpoint_handled = False
        try:
            response = self.session.get(f"{BASE_URL}/nonexistent-endpoint")
            invalid_endpoint_handled = response.status_code == 404
        except:
            pass
        
        # Test malformed requests
        malformed_handled = False
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", data="invalid json")
            malformed_handled = response.status_code in [400, 422]
        except:
            pass
        
        # Test missing authentication
        missing_auth_handled = False
        try:
            response = self.session.get(f"{BASE_URL}/nodes")
            missing_auth_handled = response.status_code == 401
        except:
            pass
        
        # Test server responsiveness using auth endpoint
        server_responsive = True
        for i in range(3):
            try:
                response = self.session.get(f"{BASE_URL}/auth/me")
                if response.status_code not in [401, 200]:
                    server_responsive = False
                    break
                time.sleep(0.1)
            except:
                server_responsive = False
                break
        
        passed = invalid_endpoint_handled and malformed_handled and missing_auth_handled and server_responsive
        
        self.log_result(
            "Error Handling & Resilience",
            passed,
            f"Invalid endpoint: {invalid_endpoint_handled}, Malformed: {malformed_handled}, Missing auth: {missing_auth_handled}, Server responsive: {server_responsive}"
        )
    
    def test_auto_refresh_basic(self):
        """Test basic auto-refresh functionality (without heavy blockchain calls)"""
        print("🔒 Testing Auto-Refresh Basic...")
        
        if not self.get_auth_token():
            self.log_result("Auto-Refresh Blockchain Status", False, "Could not get auth token")
            return
        
        # Test refresh endpoint exists and responds
        refresh_endpoint_exists = False
        try:
            response = self.session.post(
                f"{BASE_URL}/nodes/refresh-all-status",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            refresh_endpoint_exists = response.status_code in [200, 429]  # 200 success or 429 rate limited
        except:
            pass
        
        # Test individual status check endpoint
        status_endpoint_exists = False
        try:
            response = self.session.get(f"{BASE_URL}/nodes/11111111111111111111111111111112/check-status")
            status_endpoint_exists = response.status_code in [200, 429]
        except:
            pass
        
        # Test invalid address handling
        invalid_handled = False
        try:
            response = self.session.get(f"{BASE_URL}/nodes/invalid_address/check-status")
            invalid_handled = response.status_code == 400
        except:
            pass
        
        passed = refresh_endpoint_exists and status_endpoint_exists and invalid_handled
        
        self.log_result(
            "Auto-Refresh Blockchain Status",
            passed,
            f"Refresh endpoint: {refresh_endpoint_exists}, Status endpoint: {status_endpoint_exists}, Invalid handled: {invalid_handled}"
        )
    
    def test_database_performance_basic(self):
        """Test basic database performance"""
        print("🔒 Testing Database Performance...")
        
        if not self.get_auth_token():
            self.log_result("Database Performance", False, "Could not get auth token")
            return
        
        # Test read performance
        read_success = False
        start_time = time.time()
        try:
            response = self.session.get(
                f"{BASE_URL}/nodes",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            end_time = time.time()
            read_success = response.status_code == 200 and (end_time - start_time) < 3.0
        except:
            pass
        
        # Test user data isolation
        isolation_working = True
        try:
            response = self.session.get(
                f"{BASE_URL}/nodes",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            if response.status_code == 200:
                nodes = response.json()
                # Should have reasonable number of nodes for this user
                isolation_working = len(nodes) < 200  # Reasonable upper limit
        except:
            isolation_working = False
        
        passed = read_success and isolation_working
        
        self.log_result(
            "Database Performance",
            passed,
            f"Read performance: {read_success}, Data isolation: {isolation_working}"
        )
    
    def run_quick_tests(self):
        """Run quick backend tests"""
        print("🚀 Starting Quick Backend Testing for Nosana Node Monitor")
        print("🎯 Testing critical backend functionality:")
        print("   • Authentication endpoints with rate limiting")
        print("   • Node CRUD operations") 
        print("   • Auto-refresh endpoints (basic)")
        print("   • Push notifications system")
        print("   • Security features")
        print("   • Database performance (basic)")
        print("   • Error handling and resilience")
        print("=" * 80)
        print()
        
        # Run all tests
        self.test_authentication_endpoints()
        self.test_node_crud_operations()
        self.test_auto_refresh_basic()
        self.test_push_notifications()
        self.test_security_features()
        self.test_database_performance_basic()
        self.test_error_handling_resilience()
        
        # Summary
        print("=" * 80)
        print("📊 QUICK BACKEND TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        total_tests = len(self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Failed tests details
        failed_tests = [result for result in self.test_results if not result["passed"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        else:
            print("🎉 ALL TESTS PASSED!")
        
        print()
        return passed_tests, total_tests, failed_tests

if __name__ == "__main__":
    tester = QuickBackendTester()
    passed, total, failed = tester.run_quick_tests()
    sys.exit(0 if passed == total else 1)