#!/usr/bin/env python3

import requests
import json

# Test the auth service
def test_login():
    url = "http://localhost:8001/api/auth/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"Login successful!")
        print(f"Token: {token_data['access_token'][:50]}...")
        
        # Test token validation
        validate_url = "http://localhost:8001/api/auth/validate"
        validate_data = {"token": token_data["access_token"]}
        
        validate_response = requests.post(validate_url, json=validate_data)
        print(f"Validation Status: {validate_response.status_code}")
        print(f"Validation Response: {validate_response.text}")
        
    else:
        print("Login failed")

if __name__ == "__main__":
    test_login()