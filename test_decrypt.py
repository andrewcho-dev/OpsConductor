#!/usr/bin/env python3
"""
Test script to check credential decryption
"""
import os
import sys
sys.path.append('/home/enabledrm/backend')

from app.utils.encryption_utils import decrypt_credentials

# Test the encrypted credentials from the database
encrypted_creds = "Z0FBQUFBQm9sc3VXaDVOX3A1QWt6R0RicXR0cjlNckMtQ2FkZDNELUtjRUs4dFVRMFI0bFZzTEk2YXdrdXNSYjB5ZFg0cGwzU3R2LUFfUTFOTDYwT2dzWVBtQktXNkh0MjA3dGExT0RSU0treDJyTFdTMjRndkZtVVFoQ0s1YklneVFYaExuTEVMN29OTS1KcWVYT3A1UVdkUk1qdVRnRkFDVTZXSGZpa0FhR25aUG4xeF9Jb19JPQ=="

try:
    # Set the SECRET_KEY from environment
    os.environ['SECRET_KEY'] = 'enabledrm-dev-secret-key-2024-super-secure'
    
    # Try to decrypt
    result = decrypt_credentials(encrypted_creds)
    print("SUCCESS: Credentials decrypted successfully!")
    print("Decrypted data:", result)
    
except Exception as e:
    print(f"ERROR: Failed to decrypt credentials: {str(e)}")
    print(f"Error type: {type(e).__name__}")