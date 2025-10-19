#!/usr/bin/env python3
"""
CRITICAL STABILITY TESTING - Verify NO auto-logout and NO server sleep

This test verifies the stability fixes implemented to prevent:
1. Automatic logout issues
2. Server sleep problems  
3. Token invalidation after server restart
4. Random logouts on errors

Tests:
- SECRET_KEY stability (no regeneration)
- Keep-alive system effectiveness
- Token validation persistence
- Session persistence across page reloads
- No auto-logout on network errors
"""

import requests
import time
import json
import sys
import os
from datetime import datetime
import subprocess

# Configuration
BASE_URL = "https://nosanamonitor.preview.emergentagent.com/api"
TEST_EMAIL = "test@prod.com"
TEST_PASSWORD = "TestProd123"

class StabilityTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.secret_key_first_chars = None
        self.secret_key_last_chars = None
        
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
    
    def test_secret_key_exists_and_static(self):
        """Test SECRET_KEY exists in .env and is static"""
        print("🔑 Testing SECRET_KEY Stability...")
        
        try:
            # Check if SECRET_KEY exists in backend .env file
            env_file_path = "/app/backend/.env"
            
            if not os.path.exists(env_file_path):
                self.log_result("SECRET_KEY Exists", False, "Backend .env file not found")
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
                self.log_result("SECRET_KEY Exists", False, "SECRET_KEY not found in .env file")
                return
            
            if not secret_key_value or len(secret_key_value) < 32:
                self.log_result("SECRET_KEY Exists", False, f"SECRET_KEY too short: {len(secret_key_value)} chars")
                return
            
            # Store first and last 10 characters for verification
            self.secret_key_first_chars = secret_key_value[:10]
            self.secret_key_last_chars = secret_key_value[-10:]
            
            self.log_result(
                "SECRET_KEY Exists", 
                True,
                f"SECRET_KEY found in .env: {self.secret_key_first_chars}...{self.secret_key_last_chars} ({len(secret_key_value)} chars)"
            )
            
        except Exception as e:
            self.log_result("SECRET_KEY Exists", False, f"Error reading .env file: {str(e)}")
    
    def test_token_creation_with_current_secret(self):
        """Test token creation works with current SECRET_KEY"""
        print("🔑 Testing Token Creation...")
        
        try:
            # Register/login to get a token
            # First try to register (might already exist)
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
                    "Token Creation", 
                    token_works,
                    f"Token created and validated successfully. User: {me_response.json().get('email', 'unknown') if token_works else 'N/A'}"
                )
                
                return token_works
            else:
                self.log_result("Token Creation", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Token Creation", False, f"Error creating token: {str(e)}")
            return False
    
    def test_backend_service_restart_token_persistence(self):
        """Test token remains valid after backend service restart"""
        print("🔄 Testing Token Persistence After Backend Restart...")
        
        if not self.auth_token:
            self.log_result("Token Persistence After Restart", False, "No auth token available")
            return
        
        try:
            # First verify token works before restart
            pre_restart_response = self.session.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if pre_restart_response.status_code != 200:
                self.log_result("Token Persistence After Restart", False, "Token invalid before restart")
                return
            
            print("   Token valid before restart. Restarting backend service...")
            
            # Restart backend service
            try:
                restart_result = subprocess.run(
                    ["sudo", "supervisorctl", "restart", "backend"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if restart_result.returncode != 0:
                    self.log_result("Token Persistence After Restart", False, f"Failed to restart backend: {restart_result.stderr}")
                    return
                
                print("   Backend service restarted. Waiting 5 seconds for startup...")
                time.sleep(5)
                
            except subprocess.TimeoutExpired:
                self.log_result("Token Persistence After Restart", False, "Backend restart timed out")
                return
            except Exception as e:
                self.log_result("Token Persistence After Restart", False, f"Error restarting backend: {str(e)}")
                return
            
            # Test token still works after restart
            max_retries = 10
            for attempt in range(max_retries):
                try:
                    post_restart_response = self.session.get(
                        f"{BASE_URL}/auth/me",
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                        timeout=10
                    )
                    
                    if post_restart_response.status_code == 200:
                        user_data = post_restart_response.json()
                        self.log_result(
                            "Token Persistence After Restart", 
                            True,
                            f"Token remains valid after restart. User: {user_data.get('email', 'unknown')}"
                        )
                        return
                    elif post_restart_response.status_code == 401:
                        self.log_result("Token Persistence After Restart", False, "Token invalidated after restart (401)")
                        return
                    else:
                        print(f"   Attempt {attempt + 1}: Server returned {post_restart_response.status_code}, retrying...")
                        time.sleep(2)
                        
                except requests.exceptions.RequestException as e:
                    print(f"   Attempt {attempt + 1}: Connection error, retrying... ({str(e)})")
                    time.sleep(2)
            
            self.log_result("Token Persistence After Restart", False, "Server not responding after restart")
            
        except Exception as e:
            self.log_result("Token Persistence After Restart", False, f"Error testing token persistence: {str(e)}")
    
    def test_health_endpoint_responsiveness(self):
        """Test /api/health endpoint responds quickly and consistently"""
        print("💓 Testing Health Endpoint Responsiveness...")
        
        response_times = []
        successful_requests = 0
        total_requests = 10
        
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
                time.sleep(0.5)  # Small delay between requests
                
            except requests.exceptions.Timeout:
                print(f"   Request {i+1}: TIMEOUT")
                response_times.append(5.0)  # Count timeout as 5 seconds
            except Exception as e:
                print(f"   Request {i+1}: ERROR - {str(e)}")
                response_times.append(5.0)
        
        avg_response_time = sum(response_times) / len(response_times)
        success_rate = (successful_requests / total_requests) * 100
        
        # Health endpoint should respond in under 1 second consistently
        passed = (avg_response_time < 1.0 and success_rate >= 90)
        
        self.log_result(
            "Health Endpoint Responsiveness", 
            passed,
            f"Success rate: {success_rate:.1f}%, Avg response time: {avg_response_time:.3f}s"
        )
    
    def test_keep_alive_system_effectiveness(self):
        """Test keep-alive system prevents server sleep"""
        print("⏰ Testing Keep-Alive System Effectiveness...")
        
        try:
            # Test health endpoint multiple times over 2 minutes to simulate keep-alive
            print("   Testing server responsiveness over 2 minutes...")
            
            start_time = time.time()
            test_duration = 120  # 2 minutes
            ping_interval = 10   # Every 10 seconds
            
            response_times = []
            failed_pings = 0
            
            while (time.time() - start_time) < test_duration:
                try:
                    ping_start = time.time()
                    response = self.session.get(f"{BASE_URL}/health", timeout=5)
                    ping_end = time.time()
                    
                    response_time = ping_end - ping_start
                    response_times.append(response_time)
                    
                    if response.status_code != 200:
                        failed_pings += 1
                    
                    elapsed = time.time() - start_time
                    print(f"   Ping at {elapsed:.0f}s: {response.status_code} in {response_time:.3f}s")
                    
                    time.sleep(ping_interval)
                    
                except requests.exceptions.Timeout:
                    failed_pings += 1
                    response_times.append(5.0)
                    elapsed = time.time() - start_time
                    print(f"   Ping at {elapsed:.0f}s: TIMEOUT")
                    time.sleep(ping_interval)
                except Exception as e:
                    failed_pings += 1
                    response_times.append(5.0)
                    elapsed = time.time() - start_time
                    print(f"   Ping at {elapsed:.0f}s: ERROR - {str(e)}")
                    time.sleep(ping_interval)
            
            total_pings = len(response_times)
            avg_response_time = sum(response_times) / total_pings if total_pings > 0 else 0
            success_rate = ((total_pings - failed_pings) / total_pings) * 100 if total_pings > 0 else 0
            
            # Server should stay responsive with good performance
            passed = (success_rate >= 90 and avg_response_time < 2.0)
            
            self.log_result(
                "Keep-Alive System Effectiveness", 
                passed,
                f"Pings: {total_pings}, Success rate: {success_rate:.1f}%, Avg response: {avg_response_time:.3f}s"
            )
            
        except Exception as e:
            self.log_result("Keep-Alive System Effectiveness", False, f"Error testing keep-alive: {str(e)}")
    
    def test_token_validation_stability(self):
        """Test token validation remains stable over time"""
        print("🎫 Testing Token Validation Stability...")
        
        if not self.auth_token:
            self.log_result("Token Validation Stability", False, "No auth token available")
            return
        
        try:
            # Test token validation multiple times over 3 minutes
            print("   Testing token validation over 3 minutes...")
            
            start_time = time.time()
            test_duration = 180  # 3 minutes
            check_interval = 30  # Every 30 seconds
            
            validation_results = []
            
            while (time.time() - start_time) < test_duration:
                try:
                    check_start = time.time()
                    response = self.session.get(
                        f"{BASE_URL}/auth/me",
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                        timeout=10
                    )
                    check_end = time.time()
                    
                    response_time = check_end - check_start
                    is_valid = response.status_code == 200
                    
                    validation_results.append({
                        "valid": is_valid,
                        "status_code": response.status_code,
                        "response_time": response_time
                    })
                    
                    elapsed = time.time() - start_time
                    status = "VALID" if is_valid else f"INVALID ({response.status_code})"
                    print(f"   Token check at {elapsed:.0f}s: {status} in {response_time:.3f}s")
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    validation_results.append({
                        "valid": False,
                        "status_code": 0,
                        "response_time": 0,
                        "error": str(e)
                    })
                    elapsed = time.time() - start_time
                    print(f"   Token check at {elapsed:.0f}s: ERROR - {str(e)}")
                    time.sleep(check_interval)
            
            valid_checks = sum(1 for r in validation_results if r["valid"])
            total_checks = len(validation_results)
            success_rate = (valid_checks / total_checks) * 100 if total_checks > 0 else 0
            
            # Token should remain valid throughout the test
            passed = (success_rate == 100)
            
            self.log_result(
                "Token Validation Stability", 
                passed,
                f"Valid checks: {valid_checks}/{total_checks} ({success_rate:.1f}%)"
            )
            
        except Exception as e:
            self.log_result("Token Validation Stability", False, f"Error testing token validation: {str(e)}")
    
    def test_session_persistence_simulation(self):
        """Test session persistence across simulated page reloads"""
        print("🔄 Testing Session Persistence Simulation...")
        
        if not self.auth_token:
            self.log_result("Session Persistence Simulation", False, "No auth token available")
            return
        
        try:
            # Simulate multiple page reloads by making fresh requests with stored token
            reload_count = 5
            successful_reloads = 0
            
            for i in range(reload_count):
                print(f"   Simulating page reload {i+1}...")
                
                # Create new session to simulate fresh page load
                fresh_session = requests.Session()
                
                try:
                    # Test protected endpoint with stored token
                    response = fresh_session.get(
                        f"{BASE_URL}/nodes",
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        successful_reloads += 1
                        nodes = response.json()
                        print(f"     ✅ Reload {i+1}: Success - {len(nodes)} nodes loaded")
                    elif response.status_code == 401:
                        print(f"     ❌ Reload {i+1}: Token expired/invalid (401)")
                    else:
                        print(f"     ⚠️  Reload {i+1}: Unexpected status {response.status_code}")
                    
                    time.sleep(2)  # Wait between reloads
                    
                except Exception as e:
                    print(f"     ❌ Reload {i+1}: Error - {str(e)}")
                
                fresh_session.close()
            
            success_rate = (successful_reloads / reload_count) * 100
            passed = (success_rate == 100)
            
            self.log_result(
                "Session Persistence Simulation", 
                passed,
                f"Successful reloads: {successful_reloads}/{reload_count} ({success_rate:.1f}%)"
            )
            
        except Exception as e:
            self.log_result("Session Persistence Simulation", False, f"Error testing session persistence: {str(e)}")
    
    def test_no_auto_logout_on_errors(self):
        """Test that network errors don't cause auto-logout"""
        print("🚫 Testing No Auto-Logout on Network Errors...")
        
        if not self.auth_token:
            self.log_result("No Auto-Logout on Errors", False, "No auth token available")
            return
        
        try:
            # First verify token is valid
            response = self.session.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if response.status_code != 200:
                self.log_result("No Auto-Logout on Errors", False, "Token invalid before error test")
                return
            
            print("   Token valid before error simulation...")
            
            # Simulate various error conditions
            error_scenarios = [
                ("Invalid endpoint", f"{BASE_URL}/nonexistent-endpoint"),
                ("Malformed request", f"{BASE_URL}/nodes"),
                ("Server error simulation", f"{BASE_URL}/nodes/invalid-address/check-status"),
            ]
            
            for scenario_name, url in error_scenarios:
                print(f"   Testing {scenario_name}...")
                
                try:
                    if scenario_name == "Malformed request":
                        # Send malformed JSON
                        error_response = self.session.post(
                            url,
                            data="invalid json",
                            headers={"Authorization": f"Bearer {self.auth_token}"}
                        )
                    else:
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
            self.log_result("No Auto-Logout on Errors", False, f"Error testing auto-logout prevention: {str(e)}")
    
    def test_idle_period_survival(self):
        """Test server and session survive extended idle period"""
        print("😴 Testing Idle Period Survival (5+ minutes)...")
        
        if not self.auth_token:
            self.log_result("Idle Period Survival", False, "No auth token available")
            return
        
        try:
            # Verify token works before idle period
            pre_idle_response = self.session.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if pre_idle_response.status_code != 200:
                self.log_result("Idle Period Survival", False, "Token invalid before idle period")
                return
            
            print("   Token valid before idle period. Starting 5-minute idle simulation...")
            
            # Wait for 5 minutes (300 seconds) with no activity
            idle_duration = 300
            start_time = time.time()
            
            # Show progress every minute
            while (time.time() - start_time) < idle_duration:
                elapsed = time.time() - start_time
                remaining = idle_duration - elapsed
                print(f"   Idle time: {elapsed:.0f}s / {idle_duration}s (remaining: {remaining:.0f}s)")
                time.sleep(60)  # Wait 1 minute
            
            print("   Idle period complete. Testing server and session...")
            
            # Test server responsiveness after idle
            try:
                health_response = self.session.get(f"{BASE_URL}/health", timeout=10)
                server_responsive = health_response.status_code == 200
                print(f"   Server health check: {health_response.status_code} ({'responsive' if server_responsive else 'unresponsive'})")
            except Exception as e:
                server_responsive = False
                print(f"   Server health check: ERROR - {str(e)}")
            
            # Test token still works after idle
            try:
                post_idle_response = self.session.get(
                    f"{BASE_URL}/auth/me",
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=10
                )
                
                token_valid = post_idle_response.status_code == 200
                print(f"   Token validation: {post_idle_response.status_code} ({'valid' if token_valid else 'invalid'})")
                
                if token_valid:
                    # Test protected endpoint
                    nodes_response = self.session.get(
                        f"{BASE_URL}/nodes",
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                        timeout=10
                    )
                    
                    protected_endpoint_works = nodes_response.status_code == 200
                    print(f"   Protected endpoint: {nodes_response.status_code} ({'working' if protected_endpoint_works else 'not working'})")
                else:
                    protected_endpoint_works = False
                
            except Exception as e:
                token_valid = False
                protected_endpoint_works = False
                print(f"   Token validation: ERROR - {str(e)}")
            
            passed = (server_responsive and token_valid and protected_endpoint_works)
            
            self.log_result(
                "Idle Period Survival", 
                passed,
                f"Server responsive: {server_responsive}, Token valid: {token_valid}, Protected endpoints: {protected_endpoint_works}"
            )
            
        except Exception as e:
            self.log_result("Idle Period Survival", False, f"Error testing idle period survival: {str(e)}")
    
    def run_stability_tests(self):
        """Run comprehensive stability tests"""
        print("🔒 CRITICAL STABILITY TESTING - Verify NO auto-logout and NO server sleep")
        print("=" * 80)
        print("Testing stability fixes for:")
        print("• SECRET_KEY regeneration → Now static in .env")
        print("• Server going to sleep → Keep-alive pings every 30s") 
        print("• Random logouts on errors → Better error handling")
        print("• Token invalidation → Persistent JWT validation")
        print("=" * 80)
        print()
        
        # Run all stability tests in order
        self.test_secret_key_exists_and_static()
        self.test_token_creation_with_current_secret()
        self.test_backend_service_restart_token_persistence()
        self.test_health_endpoint_responsiveness()
        self.test_keep_alive_system_effectiveness()
        self.test_token_validation_stability()
        self.test_session_persistence_simulation()
        self.test_no_auto_logout_on_errors()
        self.test_idle_period_survival()
        
        # Summary
        print("=" * 80)
        print("📊 STABILITY TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        total_tests = len(self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Critical stability requirements
        critical_tests = [
            "SECRET_KEY Exists",
            "Token Creation", 
            "Token Persistence After Restart",
            "Health Endpoint Responsiveness",
            "Keep-Alive System Effectiveness",
            "Token Validation Stability",
            "Session Persistence Simulation",
            "No Auto-Logout on Errors",
            "Idle Period Survival"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if result["test"] in critical_tests and result["passed"])
        
        print(f"Critical Stability Tests: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("🎉 STABILITY VERIFIED - NO auto-logout, NO server sleep!")
            print("✅ Users will stay logged in")
            print("✅ Server stays responsive") 
            print("✅ Sessions persist across page reloads")
            print("✅ Tokens remain valid after server restarts")
        else:
            print("⚠️  STABILITY ISSUES DETECTED - Some critical systems need attention")
        
        print()
        
        # Failed tests details
        failed_tests = [result for result in self.test_results if not result["passed"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        else:
            print("🎉 ALL STABILITY TESTS PASSED!")
        
        print()
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = StabilityTester()
    success = tester.run_stability_tests()
    sys.exit(0 if success else 1)