#!/usr/bin/env python3
import base64
import json
import sys

def decode_jwt_payload(token):
    """Decode JWT payload without verification."""
    try:
        # Split the token
        parts = token.split('.')
        if len(parts) != 3:
            print("Invalid JWT format")
            return None
        
        # Decode the payload (second part)
        payload = parts[1]
        
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        # Decode base64
        decoded = base64.urlsafe_b64decode(payload)
        
        # Parse JSON
        payload_data = json.loads(decoded)
        
        return payload_data
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 debug_token.py <jwt_token>")
        sys.exit(1)
    
    token = sys.argv[1]
    payload = decode_jwt_payload(token)
    
    if payload:
        print("JWT Payload:")
        print(json.dumps(payload, indent=2))
    else:
        print("Failed to decode token")