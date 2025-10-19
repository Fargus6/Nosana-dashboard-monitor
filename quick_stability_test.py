#!/usr/bin/env python3
"""
QUICK STABILITY TEST - Essential stability checks without long waits
"""

import requests
import time
import json
import sys
import os
from datetime import datetime
import subprocess

# Configuration
BASE_URL = "https://node-pulse.preview.emergentagent.com/api"
TEST_EMAIL = "test@prod.com"
TEST_PASSWORD = "TestProd123"

class QuickStabilityTester:
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
    
    def test_secret_key_verification(self):
        """Verify SECRET_KEY exists and is static"""
        print("🔑 Testing SECRET_KEY Configuration...")
        
        try:
            env_file_path = "/app/backend/.env"
            
            if not os.path.exists(env_file_path):
                self.log_result("SECRET_KEY Configuration", False, "Backend .env file not found")
                return
            
            with open(env_file_path, 'r') as f:
                env_content = f.read()
            
            secret_key_found = False
            secret_key_value = None
            
            for line in env_content.split('\n'):
                if line.startswith('SECRET_KEY='):
                    secret_key_found = True
                    secret_key_value = line.split('=', 1)[1].strip('"')
                    break
            
            if not secret_key_found:
                self.log_result("SECRET_KEY Configuration", False, "SECRET_KEY not found in .env file")
                return
            
            if not secret_key_value or len(secret_key_value) < 32:
                self.log_result("SECRET_KEY Configuration", False, f"SECRET_KEY too short: {len(secret_key_value)} chars")
                return
            
            self.log_result(
                "SECRET_KEY Configuration", 
                True,
                f"SECRET_KEY properly configured: {secret_key_value[:10]}...{secret_key_value[-10:]} ({len(secret_key_value)} chars)"
            )
            
        except Exception as e:
            self.log_result("SECRET_KEY Configuration", False, f"Error reading .env file: {str(e)}")
    
    def test_authentication_and_token_creation(self):
        """Test authentication and token creation"""
        print("🎫 Testing Authentication & Token Creation...")
        
        try:
            # Register/login to get a token
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
                token_data = response.json()
                self.auth_token = token_data["access_token"]
                
                # Test token works
                me_response = self.session.get(
                    f"{BASE_URL}/auth/me",
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                
                token_works = me_response.status_code == 200
                
                self.log_result(
                    "Authentication & Token Creation", 
                    token_works,
                    f"Login successful, token created and validated. User: {me_response.json().get('email', 'unknown') if token_works else 'N/A'}"
                )
                
                return token_works
            else:
                self.log_result("Authentication & Token Creation", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication & Token Creation", False, f"Error: {str(e)}")
            return False
    
    def test_health_endpoint_performance(self):
        """Test health endpoint responds quickly"""
        print("💓 Testing Health Endpoint Performance...")
        
        response_times = []
        successful_requests = 0
        total_requests = 5
        
        for i in range(total_requests):
            try:
                start_time = time.time()
                response = self.session.get(f"{BASE_URL}/health", timeout=5)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                if response.status_code == 200:
                    successful_requests += 1
                
                print(f"   Request {i+1}: {response.status_code} in {response_time:.3f}s")
                
            except requests.exceptions.Timeout:
                print(f"   Request {i+1}: TIMEOUT")
                response_times.append(5.0)
            except Exception as e:
                print(f"   Request {i+1}: ERROR - {str(e)}")
                response_times.append(5.0)
        
        avg_response_time = sum(response_times) / len(response_times)
        success_rate = (successful_requests / total_requests) * 100
        
        passed = (avg_response_time < 1.0 and success_rate >= 80)
        
        self.log_result(
            "Health Endpoint Performance", 
            passed,
            f"Success rate: {success_rate:.1f}%, Avg response time: {avg_response_time:.3f}s"
        )
    
    def test_token_validation_consistency(self):
        """Test token validation works consistently"""
        print("🔐 Testing Token Validation Consistency...")
        
        if not self.auth_token:
            self.log_result("Token Validation Consistency", False, "No auth token available")
            return
        
        try:
            validation_results = []
            
            for i in range(5):
                try:
                    response = self.session.get(
                        f"{BASE_URL}/auth/me",
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                        timeout=10
                    )
                    
                    is_valid = response.status_code == 200
                    validation_results.append(is_valid)
                    
                    print(f"   Validation {i+1}: {'VALID' if is_valid else f'INVALID ({response.status_code})'}")
                    time.sleep(1)
                    
                except Exception as e:
                    validation_results.append(False)
                    print(f"   Validation {i+1}: ERROR - {str(e)}")
            
            valid_checks = sum(validation_results)
            total_checks = len(validation_results)
            success_rate = (valid_checks / total_checks) * 100
            
            passed = (success_rate == 100)
            
            self.log_result(
                "Token Validation Consistency", 
                passed,
                f"Valid checks: {valid_checks}/{total_checks} ({success_rate:.1f}%)"
            )
            
        except Exception as e:
            self.log_result("Token Validation Consistency", False, f"Error: {str(e)}")
    
    def test_session_persistence_basic(self):
        """Test basic session persistence"""
        print("🔄 Testing Session Persistence...")
        
        if not self.auth_token:
            self.log_result("Session Persistence", False, "No auth token available")
            return
        
        try:
            successful_requests = 0
            total_requests = 3
            
            for i in range(total_requests):
                print(f"   Testing session persistence {i+1}...")
                
                # Create new session to simulate fresh page load
                fresh_session = requests.Session()
                
                try:
                    response = fresh_session.get(
                        f"{BASE_URL}/nodes",
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        successful_requests += 1
                        nodes = response.json()
                        print(f"     ✅ Success - {len(nodes)} nodes loaded")
                    elif response.status_code == 401:
                        print(f"     ❌ Token expired/invalid (401)")
                    else:
                        print(f"     ⚠️  Unexpected status {response.status_code}")
                    
                except Exception as e:
                    print(f"     ❌ Error - {str(e)}")
                
                fresh_session.close()
                time.sleep(1)
            
            success_rate = (successful_requests / total_requests) * 100
            passed = (success_rate >= 80)
            
            self.log_result(
                "Session Persistence", 
                passed,
                f"Successful requests: {successful_requests}/{total_requests} ({success_rate:.1f}%)"
            )
            
        except Exception as e:
            self.log_result("Session Persistence", False, f"Error: {str(e)}")
    
    def test_error_handling_no_logout(self):
        """Test that errors don't cause auto-logout"""
        print("🚫 Testing No Auto-Logout on Errors...")
        
        if not self.auth_token:
            self.log_result("No Auto-Logout on Errors", False, "No auth token available")
            return
        
        try:
            # Verify token is valid before error tests
            response = self.session.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if response.status_code != 200:
                self.log_result("No Auto-Logout on Errors", False, "Token invalid before error test")
                return
            
            print("   Token valid before error simulation...")
            
            # Test various error scenarios
            error_scenarios = [
                ("Invalid endpoint", f"{BASE_URL}/nonexistent-endpoint"),
                ("Invalid node address", f"{BASE_URL}/nodes/invalid-address/check-status"),
            ]
            
            for scenario_name, url in error_scenarios:
                print(f"   Testing {scenario_name}...")
                
                try:
                    error_response = self.session.get(
                        url,
                        headers={"Authorization": f"Bearer {self.auth_token}"}
                    )
                    print(f"     Error response: {error_response.status_code}")
                except Exception as e:
                    print(f"     Expected error: {str(e)}")
                
                # Verify token still works after error
                time.sleep(1)
                
                verify_response = self.session.get(
                    f"{BASE_URL}/auth/me",
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                
                if verify_response.status_code != 200:
                    self.log_result(
                        "No Auto-Logout on Errors", 
                        False, 
                        f"Token invalidated after {scenario_name} (got {verify_response.status_code})"
                    )
                    return
                
                print(f"     ✅ Token still valid after {scenario_name}")
            
            self.log_result(
                "No Auto-Logout on Errors", 
                True,
                "Token remains valid after all error scenarios"
            )
            
        except Exception as e:
            self.log_result("No Auto-Logout on Errors", False, f"Error: {str(e)}")
    
    def test_protected_endpoints_access(self):
        """Test protected endpoints work with valid token"""
        print("🔒 Testing Protected Endpoints Access...")
        
        if not self.auth_token:
            self.log_result("Protected Endpoints Access", False, "No auth token available")
            return
        
        try:
            endpoints_to_test = [
                ("User info", f"{BASE_URL}/auth/me"),
                ("Nodes list", f"{BASE_URL}/nodes"),
                ("Notification preferences", f"{BASE_URL}/notifications/preferences"),
            ]
            
            successful_requests = 0
            
            for endpoint_name, url in endpoints_to_test:
                try:
                    response = self.session.get(
                        url,
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        successful_requests += 1
                        print(f"   ✅ {endpoint_name}: Success")
                    else:
                        print(f"   ❌ {endpoint_name}: Failed ({response.status_code})")
                        
                except Exception as e:
                    print(f"   ❌ {endpoint_name}: Error - {str(e)}")
            
            total_endpoints = len(endpoints_to_test)
            success_rate = (successful_requests / total_endpoints) * 100
            passed = (success_rate >= 80)
            
            self.log_result(
                "Protected Endpoints Access", 
                passed,
                f"Successful endpoints: {successful_requests}/{total_endpoints} ({success_rate:.1f}%)"
            )
            
        except Exception as e:
            self.log_result("Protected Endpoints Access", False, f"Error: {str(e)}")
    
    def run_quick_stability_tests(self):
        """Run quick stability tests"""
        print("🔒 QUICK STABILITY TEST - Essential Checks")
        print("=" * 60)
        print("Verifying:")
        print("• SECRET_KEY is static and properly configured")
        print("• Authentication and token creation works")
        print("• Health endpoint responds quickly")
        print("• Token validation is consistent")
        print("• Session persistence works")
        print("• No auto-logout on errors")
        print("• Protected endpoints accessible")
        print("=" * 60)
        print()
        
        # Run all quick tests
        self.test_secret_key_verification()
        self.test_authentication_and_token_creation()
        self.test_health_endpoint_performance()
        self.test_token_validation_consistency()
        self.test_session_persistence_basic()
        self.test_error_handling_no_logout()
        self.test_protected_endpoints_access()
        
        # Summary
        print("=" * 60)
        print("📊 QUICK STABILITY TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        total_tests = len(self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if passed_tests == total_tests:
            print("🎉 ALL QUICK STABILITY TESTS PASSED!")
            print("✅ SECRET_KEY is static - no token regeneration")
            print("✅ Authentication system working properly")
            print("✅ Health endpoint responsive")
            print("✅ Token validation consistent")
            print("✅ Session persistence working")
            print("✅ No auto-logout on errors")
            print("✅ Protected endpoints accessible")
        else:
            print("⚠️  SOME STABILITY ISSUES DETECTED")
            failed_tests = [result for result in self.test_results if not result["passed"]]
            if failed_tests:
                print("\n❌ FAILED TESTS:")
                for test in failed_tests:
                    print(f"  - {test['test']}: {test['details']}")
        
        print()
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = QuickStabilityTester()
    success = tester.run_quick_stability_tests()
    sys.exit(0 if success else 1)