#!/usr/bin/env python3
"""
Comprehensive API Analysis for ENABLEDRM Platform
Analyzes all API endpoints and their testing status
"""

import os
import re
import ast
from pathlib import Path

def extract_endpoints_from_file(file_path):
    """Extract API endpoints from a Python router file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find all @router.method decorators
        endpoint_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
        endpoints = re.findall(endpoint_pattern, content, re.IGNORECASE)
        
        # Also find @app.method decorators
        app_pattern = r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
        app_endpoints = re.findall(app_pattern, content, re.IGNORECASE)
        
        return endpoints + app_endpoints
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def analyze_apis():
    """Analyze all APIs in the platform"""
    
    print("🔍 ENABLEDRM API ANALYSIS")
    print("=" * 50)
    
    total_endpoints = 0
    api_groups = {}
    
    # Main routers
    router_dir = Path("backend/app/routers")
    if router_dir.exists():
        print("\n📁 MAIN ROUTERS:")
        for router_file in router_dir.glob("*.py"):
            if router_file.name.startswith("__"):
                continue
            
            endpoints = extract_endpoints_from_file(router_file)
            api_groups[f"routers/{router_file.name}"] = endpoints
            total_endpoints += len(endpoints)
            
            print(f"  📄 {router_file.name}: {len(endpoints)} endpoints")
            for method, path in endpoints:
                print(f"    {method.upper():<6} {path}")
    
    # V1 API routers
    v1_dir = Path("backend/app/api/v1")
    if v1_dir.exists():
        print("\n📁 V1 API ROUTERS:")
        for api_file in v1_dir.glob("*.py"):
            if api_file.name.startswith("__"):
                continue
            
            endpoints = extract_endpoints_from_file(api_file)
            api_groups[f"api/v1/{api_file.name}"] = endpoints
            total_endpoints += len(endpoints)
            
            print(f"  📄 {api_file.name}: {len(endpoints)} endpoints")
            for method, path in endpoints:
                print(f"    {method.upper():<6} {path}")
    
    # System API
    system_api = Path("backend/app/api/system.py")
    if system_api.exists():
        print("\n📁 SYSTEM API:")
        endpoints = extract_endpoints_from_file(system_api)
        api_groups["api/system.py"] = endpoints
        total_endpoints += len(endpoints)
        
        print(f"  📄 system.py: {len(endpoints)} endpoints")
        for method, path in endpoints:
            print(f"    {method.upper():<6} {path}")
    
    # Main app endpoints
    main_py = Path("backend/main.py")
    if main_py.exists():
        print("\n📁 MAIN APP ENDPOINTS:")
        endpoints = extract_endpoints_from_file(main_py)
        api_groups["main.py"] = endpoints
        total_endpoints += len(endpoints)
        
        print(f"  📄 main.py: {len(endpoints)} endpoints")
        for method, path in endpoints:
            print(f"    {method.upper():<6} {path}")
    
    print("\n" + "=" * 50)
    print(f"📊 SUMMARY:")
    print(f"   Total API Groups: {len(api_groups)}")
    print(f"   Total Endpoints: {total_endpoints}")
    
    # Check for test files
    print(f"\n🧪 TESTING STATUS:")
    test_files = []
    
    # Look for test files
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    
    print(f"   Test Files Found: {len(test_files)}")
    for test_file in test_files:
        print(f"     📝 {test_file}")
    
    # Check for comprehensive test coverage
    if len(test_files) == 0:
        print("   ❌ NO TEST FILES FOUND!")
        print("   ⚠️  APIs are NOT TESTED")
    elif len(test_files) < len(api_groups):
        print("   ⚠️  INCOMPLETE TEST COVERAGE")
        print(f"   📊 {len(test_files)} test files for {len(api_groups)} API groups")
    else:
        print("   ✅ Good test file coverage")
    
    return api_groups, total_endpoints, test_files

if __name__ == "__main__":
    os.chdir("/home/enabledrm")
    analyze_apis()