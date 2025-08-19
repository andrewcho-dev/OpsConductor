#!/usr/bin/env python3
"""
Script to systematically update all authentication dependencies to use centralized auth.
"""
import os
import re
import glob

def update_router_auth(file_path):
    """Update a single router file to use centralized authentication."""
    print(f"Updating {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Skip if already updated
    if 'from app.core.auth_dependencies import get_current_user' in content:
        print(f"  ✅ Already updated: {file_path}")
        return
    
    # Skip OLD files
    if '.OLD' in file_path:
        print(f"  ⏭️  Skipping OLD file: {file_path}")
        return
    
    original_content = content
    
    # 1. Remove old security imports
    content = re.sub(r'from app\.core\.security import.*verify_token.*\n', '', content)
    content = re.sub(r'from fastapi\.security import HTTPBearer.*\n', '', content)
    
    # 2. Add centralized auth import
    if 'from app.core.auth_dependencies import get_current_user' not in content:
        # Find a good place to add the import
        if 'from app.database.database import get_db' in content:
            content = content.replace(
                'from app.database.database import get_db',
                'from app.database.database import get_db\nfrom app.core.auth_dependencies import get_current_user'
            )
        elif 'from typing import' in content:
            content = re.sub(
                r'(from typing import.*\n)',
                r'\1from app.core.auth_dependencies import get_current_user\n',
                content
            )
    
    # 3. Remove security = HTTPBearer() lines
    content = re.sub(r'security = HTTPBearer\(\)\n', '', content)
    
    # 4. Remove local get_current_user function definitions
    # This is a complex regex to match the entire function
    get_current_user_pattern = r'def get_current_user\([^)]*\):[^}]*?return [^\n]*\n\n'
    content = re.sub(get_current_user_pattern, '', content, flags=re.DOTALL)
    
    # 5. Update type hints from User to Dict[str, Any]
    content = re.sub(r'current_user: User = Depends\(get_current_user\)', 
                     'current_user: Dict[str, Any] = Depends(get_current_user)', content)
    
    # 6. Update current_user.attribute to current_user["attribute"]
    content = re.sub(r'current_user\.(\w+)', r'current_user["\1"]', content)
    
    # 7. Add typing import if needed
    if 'Dict[str, Any]' in content and 'from typing import' in content:
        if 'Dict' not in content.split('from typing import')[1].split('\n')[0]:
            content = re.sub(
                r'from typing import ([^\n]*)',
                r'from typing import \1, Dict, Any',
                content
            )
    elif 'Dict[str, Any]' in content and 'from typing import' not in content:
        # Add typing import
        content = 'from typing import Dict, Any\n' + content
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✅ Updated: {file_path}")
    else:
        print(f"  ⏭️  No changes needed: {file_path}")

def main():
    """Update all router files."""
    # Find all Python files in routers and api directories
    patterns = [
        '/home/enabledrm/backend/app/routers/*.py',
        '/home/enabledrm/backend/app/api/*.py',
        '/home/enabledrm/backend/app/api/v1/*.py',
        '/home/enabledrm/backend/app/api/v2/*.py',
        '/home/enabledrm/backend/app/api/v3/*.py'
    ]
    
    files_to_update = []
    for pattern in patterns:
        files_to_update.extend(glob.glob(pattern))
    
    # Remove duplicates and sort
    files_to_update = sorted(set(files_to_update))
    
    print(f"Found {len(files_to_update)} files to check...")
    
    for file_path in files_to_update:
        try:
            update_router_auth(file_path)
        except Exception as e:
            print(f"  ❌ Error updating {file_path}: {e}")
    
    print("\n🎯 Authentication update complete!")

if __name__ == "__main__":
    main()