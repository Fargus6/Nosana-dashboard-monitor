#!/usr/bin/env python3
"""
Quick test to verify rate limiting is working
"""

import requests
import time

BASE_URL = "https://ai-node-tracker.preview.emergentagent.com/api"

def test_registration_rate_limit():
    """Test registration rate limiting"""
    print("Testing registration rate limiting...")
    
    session = requests.Session()
    
    for i in range(3):
        try:
            response = session.post(f"{BASE_URL}/auth/register", json={
                "email": f"quicktest{i}@test.com",
                "password": "SecurePass123"
            })
            
            print(f"Attempt {i+1}: Status {response.status_code}")
            if response.status_code == 429:
                print(f"Rate limited: {response.json()}")
                return True
            elif response.status_code == 200:
                print("Registration successful")
            else:
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    return False

if __name__ == "__main__":
    test_registration_rate_limit()