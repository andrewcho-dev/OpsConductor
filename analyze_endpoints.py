#!/usr/bin/env python3
"""
Comprehensive API Endpoint Analysis Script
Extracts all endpoints from FastAPI routers to identify duplicates and overlaps
"""

import os
import re
import ast
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def extract_endpoints_from_file(file_path: str) -> List[Dict]:
    """Extract endpoint information from a Python router file"""
    endpoints = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all router decorators with regex
        router_pattern = r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']*)["\']'
        matches = re.finditer(router_pattern, content, re.MULTILINE | re.IGNORECASE)
        
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            
            # Find the function name that follows
            start_pos = match.end()
            func_match = re.search(r'async\s+def\s+(\w+)', content[start_pos:start_pos+200])
            func_name = func_match.group(1) if func_match else "unknown"
            
            endpoints.append({
                'file': file_path,
                'method': method,
                'path': path,
                'function': func_name,
                'full_signature': f"{method} {path}"
            })
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return endpoints

def analyze_router_prefixes(main_py_path: str) -> Dict[str, str]:
    """Extract router prefixes from main.py"""
    prefixes = {}
    
    try:
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find include_router calls with prefixes
        pattern = r'app\.include_router\(([^,]+)(?:,\s*prefix=["\']([^"\']*)["\'])?'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            router_name = match.group(1).strip()
            prefix = match.group(2) if match.group(2) else ""
            prefixes[router_name] = prefix
    
    except Exception as e:
        print(f"Error processing main.py: {e}")
    
    return prefixes

def main():
    backend_path = "/home/enabledrm/backend"
    
    # Find all router files
    router_files = []
    
    # Main routers
    routers_dir = os.path.join(backend_path, "app", "routers")
    if os.path.exists(routers_dir):
        for file in os.listdir(routers_dir):
            if file.endswith('.py') and file != '__init__.py':
                router_files.append(os.path.join(routers_dir, file))
    
    # API routers
    api_dir = os.path.join(backend_path, "app", "api")
    for root, dirs, files in os.walk(api_dir):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                router_files.append(os.path.join(root, file))
    
    # Extract all endpoints
    all_endpoints = []
    for file_path in router_files:
        endpoints = extract_endpoints_from_file(file_path)
        all_endpoints.extend(endpoints)
    
    # Get router prefixes from main.py
    main_py = os.path.join(backend_path, "main.py")
    prefixes = analyze_router_prefixes(main_py)
    
    # Group endpoints by functionality
    endpoint_groups = defaultdict(list)
    duplicates = defaultdict(list)
    
    for endpoint in all_endpoints:
        # Group by base functionality
        path_parts = endpoint['path'].strip('/').split('/')
        base_resource = path_parts[0] if path_parts and path_parts[0] else 'root'
        endpoint_groups[base_resource].append(endpoint)
        
        # Check for exact duplicates
        signature = endpoint['full_signature']
        duplicates[signature].append(endpoint)
    
    # Print comprehensive analysis
    print("=" * 80)
    print("🔍 COMPREHENSIVE API ENDPOINT ANALYSIS")
    print("=" * 80)
    print()
    
    print(f"📊 SUMMARY:")
    print(f"  • Total Endpoints: {len(all_endpoints)}")
    print(f"  • Router Files: {len(router_files)}")
    print(f"  • Functional Groups: {len(endpoint_groups)}")
    print()
    
    # Show all endpoints grouped by file
    print("📁 ENDPOINTS BY FILE:")
    print("-" * 50)
    
    file_groups = defaultdict(list)
    for endpoint in all_endpoints:
        file_name = os.path.basename(endpoint['file'])
        file_groups[file_name].append(endpoint)
    
    for file_name in sorted(file_groups.keys()):
        endpoints = file_groups[file_name]
        print(f"\n📄 {file_name} ({len(endpoints)} endpoints):")
        for ep in sorted(endpoints, key=lambda x: (x['method'], x['path'])):
            print(f"  {ep['method']:<6} {ep['path']:<30} → {ep['function']}")
    
    print("\n" + "=" * 80)
    print("🔍 POTENTIAL ISSUES ANALYSIS")
    print("=" * 80)
    
    # Find exact duplicates
    exact_duplicates = {k: v for k, v in duplicates.items() if len(v) > 1}
    if exact_duplicates:
        print("\n❌ EXACT DUPLICATES:")
        print("-" * 30)
        for signature, endpoints in exact_duplicates.items():
            print(f"\n🚨 {signature}")
            for ep in endpoints:
                file_name = os.path.basename(ep['file'])
                print(f"   • {file_name} → {ep['function']}")
    else:
        print("\n✅ No exact duplicates found")
    
    # Find similar paths (potential overlaps)
    print("\n🔍 SIMILAR PATHS ANALYSIS:")
    print("-" * 30)
    
    path_similarities = defaultdict(list)
    for endpoint in all_endpoints:
        # Normalize path for comparison
        normalized = re.sub(r'\{[^}]+\}', '{id}', endpoint['path'])
        normalized = re.sub(r'/+', '/', normalized).strip('/')
        path_similarities[normalized].append(endpoint)
    
    similar_groups = {k: v for k, v in path_similarities.items() if len(v) > 1}
    for pattern, endpoints in similar_groups.items():
        if len(set(ep['method'] for ep in endpoints)) > 1:  # Different methods on same path
            print(f"\n📍 Pattern: /{pattern}")
            for ep in endpoints:
                file_name = os.path.basename(ep['file'])
                print(f"   {ep['method']:<6} {ep['path']:<25} ({file_name} → {ep['function']})")
    
    # Analyze functional overlaps
    print("\n🔍 FUNCTIONAL OVERLAP ANALYSIS:")
    print("-" * 35)
    
    # Group by resource type
    resource_analysis = {
        'users': [],
        'targets': [],
        'jobs': [],
        'system': [],
        'analytics': [],
        'discovery': [],
        'health': [],
        'monitoring': [],
        'audit': [],
        'auth': []
    }
    
    for endpoint in all_endpoints:
        path_lower = endpoint['path'].lower()
        file_lower = os.path.basename(endpoint['file']).lower()
        
        for resource in resource_analysis.keys():
            if resource in path_lower or resource in file_lower:
                resource_analysis[resource].append(endpoint)
    
    for resource, endpoints in resource_analysis.items():
        if len(endpoints) > 5:  # Only show resources with many endpoints
            files = set(os.path.basename(ep['file']) for ep in endpoints)
            if len(files) > 1:  # Multiple files handling same resource
                print(f"\n📦 {resource.upper()} ({len(endpoints)} endpoints across {len(files)} files):")
                for file_name in sorted(files):
                    file_endpoints = [ep for ep in endpoints if os.path.basename(ep['file']) == file_name]
                    print(f"   📄 {file_name}: {len(file_endpoints)} endpoints")
    
    # Check for versioning inconsistencies
    print("\n🔍 VERSIONING ANALYSIS:")
    print("-" * 25)
    
    v1_endpoints = [ep for ep in all_endpoints if '/v1/' in ep['file'] or '/v1/' in ep['path']]
    non_versioned = [ep for ep in all_endpoints if '/v1/' not in ep['file'] and '/v1/' not in ep['path']]
    
    print(f"📊 Versioned (v1): {len(v1_endpoints)} endpoints")
    print(f"📊 Non-versioned: {len(non_versioned)} endpoints")
    
    if v1_endpoints and non_versioned:
        print("\n⚠️  Mixed versioning detected - consider consolidating")
    
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    recommendations = []
    
    if exact_duplicates:
        recommendations.append("🔥 HIGH PRIORITY: Remove exact duplicate endpoints")
    
    if len([f for f in file_groups.keys() if 'system' in f.lower()]) > 2:
        recommendations.append("🔧 MEDIUM: Consolidate system-related endpoints")
    
    if v1_endpoints and non_versioned:
        recommendations.append("📋 MEDIUM: Standardize API versioning approach")
    
    overlapping_resources = [r for r, eps in resource_analysis.items() 
                           if len(set(os.path.basename(ep['file']) for ep in eps)) > 2]
    if overlapping_resources:
        recommendations.append(f"🔄 LOW: Consider consolidating: {', '.join(overlapping_resources)}")
    
    if not recommendations:
        recommendations.append("✅ No major issues detected - API structure looks clean")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()