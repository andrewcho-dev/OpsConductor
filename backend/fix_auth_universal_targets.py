#!/usr/bin/env python3
"""
Script to add authentication to all endpoints in universal_targets.py that are missing it.
"""

import re

def fix_authentication():
    file_path = "/home/enabledrm/backend/app/routers/universal_targets.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find router endpoints without current_user parameter
    # Look for @router.method followed by async def that doesn't have current_user
    pattern = r'(@router\.\w+\([^)]*\)\s*\nasync def \w+\(\s*[^)]*?)(\s*\):)'
    
    def add_auth_if_missing(match):
        full_match = match.group(0)
        params_part = match.group(1)
        closing_part = match.group(2)
        
        # Check if current_user is already present
        if 'current_user' in params_part:
            return full_match  # Already has authentication
        
        # Check if this is the login endpoint (should not have auth)
        if 'login' in params_part.lower():
            return full_match
        
        # Add current_user parameter
        if params_part.strip().endswith('('):
            # No parameters yet
            new_params = params_part + '\n    current_user: Dict[str, Any] = Depends(get_current_user),'
        else:
            # Has other parameters
            new_params = params_part + ',\n    current_user: Dict[str, Any] = Depends(get_current_user)'
        
        return new_params + closing_part
    
    # Apply the fix
    new_content = re.sub(pattern, add_auth_if_missing, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write back if changed
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print("Added authentication to missing endpoints in universal_targets.py")
        return True
    else:
        print("No changes needed - all endpoints already have authentication")
        return False

if __name__ == "__main__":
    fix_authentication()