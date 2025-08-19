#!/usr/bin/env python3
"""
Fix quote mismatches in Python files caused by the authentication migration script.
"""
import re
import os
import glob

def fix_quote_mismatches(content):
    """Fix common quote mismatch patterns."""
    
    # Fix dictionary key access with mismatched quotes
    # Pattern: ['key'] -> ['key']
    content = re.sub(r"\['([^']+)\"\]", r"['\1']", content)
    
    # Pattern: ["key"] -> ["key"]
    content = re.sub(r'\["([^"]+)\'\]', r'["\1"]', content)
    
    # Fix string literals in lists with mismatched quotes
    # Pattern: 'item"] -> 'item']
    content = re.sub(r"'([^']+)\"\]", r"'\1']", content)
    
    # Pattern: "item'] -> "item"]
    content = re.sub(r'"([^"]+)\'\]', r'"\1"]', content)
    
    return content

def process_file(filepath):
    """Process a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content = fix_quote_mismatches(content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed quotes in: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Main function to process all Python files."""
    # Find all Python files in the app directory
    python_files = []
    for root, dirs, files in os.walk('app'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    fixed_count = 0
    for filepath in python_files:
        if process_file(filepath):
            fixed_count += 1
    
    print(f"Fixed quotes in {fixed_count} files")

if __name__ == "__main__":
    main()