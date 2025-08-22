#!/usr/bin/env python3
"""
Comprehensive script to fix all quote mismatch issues in the codebase.
This script finds and fixes patterns like ['key'] and replaces them with ['key']
"""

import os
import re
import glob

def fix_quote_mismatches(file_path):
    """Fix quote mismatches in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match ['key'] or ["key"] patterns
        patterns = [
            (r"\['([^']+)\"\]", r"['\1']"),  # ['key'] -> ['key']
            (r'\["([^"]+)\'\]', r'["\1"]'),  # ["key"] -> ["key"]
            (r"\['([^']+)\"\)", r"['\1')"),  # ['key') -> ['key')
            (r'\["([^"]+)\'\)', r'["\1")'),  # ["key") -> ["key")
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed quotes in: {file_path}")
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all Python files."""
    backend_dir = "/home/enabledrm/backend"
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(backend_dir):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files to check...")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_quote_mismatches(file_path):
            fixed_count += 1
    
    print(f"Fixed quotes in {fixed_count} files.")

if __name__ == "__main__":
    main()