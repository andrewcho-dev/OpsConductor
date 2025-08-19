#!/usr/bin/env python3
"""
Script to fix remaining authentication functions that the first script missed.
"""
import os
import re

def fix_file(filepath):
    """Fix a single file by removing local get_current_user functions."""
    print(f"Fixing {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Skip if it's auth_session.py (has legitimate get_current_user functions)
    if 'auth_session.py' in filepath:
        print(f"  ⏭️  Skipping auth_session.py (has legitimate functions)")
        return
    
    # Add centralized import if not present
    if 'from app.core.auth_dependencies import get_current_user' not in content:
        # Find a good place to add it
        if 'from app.database.database import get_db' in content:
            content = content.replace(
                'from app.database.database import get_db',
                'from app.database.database import get_db\nfrom app.core.auth_dependencies import get_current_user'
            )
        elif 'from typing import' in content:
            # Add after typing imports
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from typing import'):
                    lines.insert(i + 1, 'from app.core.auth_dependencies import get_current_user')
                    break
            content = '\n'.join(lines)
    
    # Remove local get_current_user function definitions
    # This regex matches the function definition and its entire body
    patterns = [
        # Pattern 1: Simple function
        r'def get_current_user\([^)]*\):[^}]*?return [^\n]*\n\n',
        # Pattern 2: Function with try/except
        r'def get_current_user\([^)]*\):\s*"""[^"]*"""\s*try:.*?except Exception.*?\n\n',
        # Pattern 3: Multi-line function with detailed error handling
        r'def get_current_user\([^)]*\):\s*"""[^"]*"""\s*try:.*?timestamp.*?\n        \)\n\n',
    ]
    
    for pattern in patterns:
        content = re.sub(pattern, '# Local get_current_user removed - using centralized auth_dependencies\n\n', 
                        content, flags=re.DOTALL)
    
    # Remove security = HTTPBearer() lines
    content = re.sub(r'security = HTTPBearer\(\)\n', '', content)
    
    # Remove HTTPBearer imports if not needed elsewhere
    if 'HTTPBearer' in content and 'Depends(security)' not in content:
        content = re.sub(r'from fastapi\.security import.*HTTPBearer.*\n', '', content)
        content = re.sub(r', HTTPBearer', '', content)
        content = re.sub(r'HTTPBearer, ', '', content)
    
    # Remove verify_token imports
    content = re.sub(r'from app\.core\.security import.*verify_token.*\n', '', content)
    
    # Update type hints
    content = re.sub(r'current_user = Depends\(get_current_user\)', 
                     'current_user: Dict[str, Any] = Depends(get_current_user)', content)
    
    # Update current_user.attribute to current_user["attribute"]
    content = re.sub(r'current_user\.(\w+)', r'current_user["\1"]', content)
    
    # Add typing imports if needed
    if 'Dict[str, Any]' in content:
        if 'from typing import' in content and 'Dict' not in content.split('from typing import')[1].split('\n')[0]:
            content = re.sub(r'from typing import ([^\n]*)', r'from typing import \1, Dict, Any', content)
        elif 'from typing import' not in content:
            content = 'from typing import Dict, Any\n' + content
    
    # Write back if changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✅ Fixed: {filepath}")
    else:
        print(f"  ⏭️  No changes: {filepath}")

def main():
    """Fix all remaining files."""
    files = [
        './app/api/system_info.py',
        './app/api/v2/audit_enhanced.py',
        './app/api/v2/log_viewer_simple.py',
        './app/api/v2/jobs_enhanced.py',
        './app/api/v2/system_enhanced.py',
        './app/api/v2/device_types_enhanced.py',
        './app/api/v2/health_enhanced.py',
        './app/api/v2/discovery_enhanced.py',
        './app/api/v2/metrics_enhanced.py',
        './app/api/v2/log_viewer_enhanced.py',
    ]
    
    for filepath in files:
        if os.path.exists(filepath):
            try:
                fix_file(filepath)
            except Exception as e:
                print(f"  ❌ Error fixing {filepath}: {e}")
        else:
            print(f"  ⚠️  File not found: {filepath}")
    
    print("\n🎯 Remaining authentication fixes complete!")

if __name__ == "__main__":
    main()