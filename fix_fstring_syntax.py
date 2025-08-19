#!/usr/bin/env python3
"""
Fix f-string syntax errors in v3 API files
"""

import os
import re

def fix_fstring_in_file(filepath):
    """Fix f-string syntax errors in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix router prefix patterns
    content = re.sub(
        r'router = APIRouter\(prefix=f"\{os\.getenv\(\\\'API_BASE_URL\\\', \\\'\/api\/v3\\\'\)\}\/([^"]+)", tags=\[([^\]]+)\]\)',
        r'api_base_url = os.getenv("API_BASE_URL", "/api/v3")\nrouter = APIRouter(prefix=f"{api_base_url}/\1", tags=[\2])',
        content
    )
    
    # Fix download URL patterns
    content = re.sub(
        r'"download_url": f"\{os\.getenv\(\'API_BASE_URL\', \'\/api\/v3\'\)\}\/([^"]+)"',
        r'"download_url": f"{os.getenv(\'API_BASE_URL\', \'/api/v3\')}/\1"',
        content
    )
    
    # Fix double f patterns (ff")
    content = re.sub(
        r'"([^"]*?)": ff"\{os\.getenv\(\\\'API_BASE_URL\\\', \\\'\/api\/v3\\\'\)\}\/([^"]+)"',
        r'"\1": f"{os.getenv(\'API_BASE_URL\', \'/api/v3\')}/\2"',
        content
    )
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False

def main():
    """Fix all v3 API files"""
    v3_dir = "/home/enabledrm/backend/app/api/v3"
    
    for filename in os.listdir(v3_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(v3_dir, filename)
            fix_fstring_in_file(filepath)

if __name__ == "__main__":
    main()