#!/usr/bin/env python3
"""
Functional API Analysis for ENABLEDRM Platform
Categorizes APIs by functional areas and identifies consolidation opportunities
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def extract_endpoints_with_details(file_path):
    """Extract API endpoints with method, path, and function name"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        endpoints = []
        
        # Find all @router.method decorators with function names
        pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\'][^)]*\)\s*(?:async\s+)?def\s+(\w+)'
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        
        for method, path, func_name in matches:
            endpoints.append({
                'method': method.upper(),
                'path': path,
                'function': func_name,
                'file': str(file_path)
            })
        
        # Also find @app.method decorators
        app_pattern = r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\'][^)]*\)\s*(?:async\s+)?def\s+(\w+)'
        app_matches = re.findall(app_pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        
        for method, path, func_name in app_matches:
            endpoints.append({
                'method': method.upper(),
                'path': path,
                'function': func_name,
                'file': str(file_path)
            })
        
        return endpoints
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def categorize_by_functional_area(endpoints):
    """Categorize endpoints by major functional areas"""
    
    functional_areas = {
        'AUTHENTICATION & AUTHORIZATION': {
            'keywords': ['auth', 'login', 'logout', 'token', 'refresh', 'user', 'session', 'permission'],
            'endpoints': []
        },
        'TARGET MANAGEMENT': {
            'keywords': ['target', 'device', 'host', 'server', 'connection', 'communication'],
            'endpoints': []
        },
        'JOB ORCHESTRATION': {
            'keywords': ['job', 'task', 'execute', 'run', 'schedule', 'workflow', 'action'],
            'endpoints': []
        },
        'MONITORING & HEALTH': {
            'keywords': ['health', 'status', 'monitor', 'metrics', 'stats', 'performance'],
            'endpoints': []
        },
        'DISCOVERY & INVENTORY': {
            'keywords': ['discover', 'scan', 'inventory', 'detect', 'import', 'network'],
            'endpoints': []
        },
        'NOTIFICATIONS & ALERTS': {
            'keywords': ['notification', 'alert', 'email', 'message', 'template'],
            'endpoints': []
        },
        'ANALYTICS & REPORTING': {
            'keywords': ['analytics', 'report', 'dashboard', 'trend', 'summary', 'chart'],
            'endpoints': []
        },
        'AUDIT & COMPLIANCE': {
            'keywords': ['audit', 'log', 'compliance', 'event', 'history', 'trace'],
            'endpoints': []
        },
        'SYSTEM ADMINISTRATION': {
            'keywords': ['system', 'config', 'setting', 'admin', 'manage', 'service'],
            'endpoints': []
        },
        'DATA MANAGEMENT': {
            'keywords': ['data', 'export', 'import', 'backup', 'restore', 'migrate'],
            'endpoints': []
        }
    }
    
    # Categorize each endpoint
    for endpoint in endpoints:
        path_lower = endpoint['path'].lower()
        func_lower = endpoint['function'].lower()
        file_lower = endpoint['file'].lower()
        
        categorized = False
        
        for area_name, area_data in functional_areas.items():
            for keyword in area_data['keywords']:
                if (keyword in path_lower or 
                    keyword in func_lower or 
                    keyword in file_lower):
                    area_data['endpoints'].append(endpoint)
                    categorized = True
                    break
            if categorized:
                break
        
        # If not categorized, put in a catch-all
        if not categorized:
            if 'UNCATEGORIZED' not in functional_areas:
                functional_areas['UNCATEGORIZED'] = {'keywords': [], 'endpoints': []}
            functional_areas['UNCATEGORIZED']['endpoints'].append(endpoint)
    
    return functional_areas

def analyze_crud_patterns(functional_areas):
    """Analyze CRUD patterns across functional areas"""
    
    crud_analysis = {}
    
    for area_name, area_data in functional_areas.items():
        if not area_data['endpoints']:
            continue
            
        crud_patterns = {
            'CREATE': [],
            'READ': [],
            'UPDATE': [],
            'DELETE': [],
            'LIST': [],
            'SEARCH': [],
            'BULK_OPS': []
        }
        
        for endpoint in area_data['endpoints']:
            method = endpoint['method']
            path = endpoint['path']
            func = endpoint['function']
            
            # Analyze CRUD patterns
            if method == 'POST':
                if 'search' in func.lower() or 'query' in func.lower():
                    crud_patterns['SEARCH'].append(endpoint)
                elif 'bulk' in func.lower() or 'batch' in func.lower():
                    crud_patterns['BULK_OPS'].append(endpoint)
                else:
                    crud_patterns['CREATE'].append(endpoint)
            elif method == 'GET':
                if '{' in path and path.endswith('}'):  # Single item
                    crud_patterns['READ'].append(endpoint)
                elif 'search' in func.lower():
                    crud_patterns['SEARCH'].append(endpoint)
                else:
                    crud_patterns['LIST'].append(endpoint)
            elif method == 'PUT':
                crud_patterns['UPDATE'].append(endpoint)
            elif method == 'DELETE':
                crud_patterns['DELETE'].append(endpoint)
        
        crud_analysis[area_name] = crud_patterns
    
    return crud_analysis

def identify_consolidation_opportunities(functional_areas, crud_analysis):
    """Identify opportunities for API consolidation"""
    
    opportunities = {
        'DUPLICATE_PATTERNS': [],
        'MISSING_CRUD': [],
        'INCONSISTENT_NAMING': [],
        'CONSOLIDATION_CANDIDATES': []
    }
    
    # Check for duplicate patterns
    all_endpoints = []
    for area_data in functional_areas.values():
        all_endpoints.extend(area_data['endpoints'])
    
    # Group by similar paths
    path_groups = defaultdict(list)
    for endpoint in all_endpoints:
        # Normalize path for comparison
        normalized_path = re.sub(r'\{[^}]+\}', '{id}', endpoint['path'])
        normalized_path = re.sub(r'/\d+', '/{id}', normalized_path)
        path_groups[normalized_path].append(endpoint)
    
    # Find duplicates
    for path, endpoints in path_groups.items():
        if len(endpoints) > 1:
            # Check if they're actually different implementations
            files = set(ep['file'] for ep in endpoints)
            if len(files) > 1:
                opportunities['DUPLICATE_PATTERNS'].append({
                    'path': path,
                    'endpoints': endpoints,
                    'files': list(files)
                })
    
    # Check for missing CRUD operations
    for area_name, crud_ops in crud_analysis.items():
        missing_ops = []
        if not crud_ops['CREATE']:
            missing_ops.append('CREATE')
        if not crud_ops['READ'] and not crud_ops['LIST']:
            missing_ops.append('READ/LIST')
        if not crud_ops['UPDATE']:
            missing_ops.append('UPDATE')
        if not crud_ops['DELETE']:
            missing_ops.append('DELETE')
        
        if missing_ops:
            opportunities['MISSING_CRUD'].append({
                'area': area_name,
                'missing': missing_ops,
                'total_endpoints': len(functional_areas[area_name]['endpoints'])
            })
    
    # Check for naming inconsistencies
    naming_patterns = defaultdict(list)
    for endpoint in all_endpoints:
        func_name = endpoint['function']
        # Extract action from function name
        if func_name.startswith('get_'):
            naming_patterns['get_'].append(endpoint)
        elif func_name.startswith('create_'):
            naming_patterns['create_'].append(endpoint)
        elif func_name.startswith('update_'):
            naming_patterns['update_'].append(endpoint)
        elif func_name.startswith('delete_'):
            naming_patterns['delete_'].append(endpoint)
        else:
            naming_patterns['other'].append(endpoint)
    
    # Identify consolidation candidates
    resource_groups = defaultdict(list)
    for endpoint in all_endpoints:
        # Extract resource name from path
        path_parts = endpoint['path'].strip('/').split('/')
        if path_parts:
            resource = path_parts[0]
            if resource not in ['api', 'v1']:
                resource_groups[resource].append(endpoint)
    
    for resource, endpoints in resource_groups.items():
        if len(endpoints) >= 4:  # Has multiple operations
            files = set(ep['file'] for ep in endpoints)
            if len(files) > 1:
                opportunities['CONSOLIDATION_CANDIDATES'].append({
                    'resource': resource,
                    'endpoints': len(endpoints),
                    'files': list(files),
                    'operations': [ep['method'] + ' ' + ep['path'] for ep in endpoints]
                })
    
    return opportunities

def generate_report():
    """Generate comprehensive functional analysis report"""
    
    print("🔍 ENABLEDRM FUNCTIONAL API ANALYSIS")
    print("=" * 60)
    
    # Collect all endpoints
    all_endpoints = []
    
    # Main routers
    router_dir = Path("backend/app/routers")
    if router_dir.exists():
        for router_file in router_dir.glob("*.py"):
            if router_file.name.startswith("__"):
                continue
            endpoints = extract_endpoints_with_details(router_file)
            all_endpoints.extend(endpoints)
    
    # V1 API routers
    v1_dir = Path("backend/app/api/v1")
    if v1_dir.exists():
        for api_file in v1_dir.glob("*.py"):
            if api_file.name.startswith("__"):
                continue
            endpoints = extract_endpoints_with_details(api_file)
            all_endpoints.extend(endpoints)
    
    # System API
    system_api = Path("backend/app/api/system.py")
    if system_api.exists():
        endpoints = extract_endpoints_with_details(system_api)
        all_endpoints.extend(endpoints)
    
    # Main app
    main_py = Path("backend/main.py")
    if main_py.exists():
        endpoints = extract_endpoints_with_details(main_py)
        all_endpoints.extend(endpoints)
    
    print(f"📊 Total Endpoints Analyzed: {len(all_endpoints)}")
    
    # Categorize by functional areas
    functional_areas = categorize_by_functional_area(all_endpoints)
    
    print("\n🏗️ FUNCTIONAL AREA BREAKDOWN:")
    print("-" * 60)
    
    for area_name, area_data in functional_areas.items():
        if area_data['endpoints']:
            print(f"\n📁 {area_name} ({len(area_data['endpoints'])} endpoints):")
            
            # Group by file
            file_groups = defaultdict(list)
            for endpoint in area_data['endpoints']:
                file_name = Path(endpoint['file']).name
                file_groups[file_name].append(endpoint)
            
            for file_name, endpoints in file_groups.items():
                print(f"  📄 {file_name}: {len(endpoints)} endpoints")
                for ep in endpoints:
                    print(f"    {ep['method']:<6} {ep['path']:<30} ({ep['function']})")
    
    # CRUD Analysis
    crud_analysis = analyze_crud_patterns(functional_areas)
    
    print("\n🔄 CRUD PATTERN ANALYSIS:")
    print("-" * 60)
    
    for area_name, crud_ops in crud_analysis.items():
        if any(crud_ops.values()):
            print(f"\n📁 {area_name}:")
            for op_type, endpoints in crud_ops.items():
                if endpoints:
                    print(f"  {op_type}: {len(endpoints)} endpoints")
    
    # Consolidation Analysis
    opportunities = identify_consolidation_opportunities(functional_areas, crud_analysis)
    
    print("\n🎯 CONSOLIDATION OPPORTUNITIES:")
    print("-" * 60)
    
    print(f"\n🔄 DUPLICATE PATTERNS ({len(opportunities['DUPLICATE_PATTERNS'])}):")
    for dup in opportunities['DUPLICATE_PATTERNS']:
        print(f"  Path: {dup['path']}")
        print(f"  Files: {', '.join(dup['files'])}")
        print(f"  Endpoints: {len(dup['endpoints'])}")
        print()
    
    print(f"\n❌ MISSING CRUD OPERATIONS ({len(opportunities['MISSING_CRUD'])}):")
    for missing in opportunities['MISSING_CRUD']:
        print(f"  Area: {missing['area']}")
        print(f"  Missing: {', '.join(missing['missing'])}")
        print(f"  Total Endpoints: {missing['total_endpoints']}")
        print()
    
    print(f"\n🔧 CONSOLIDATION CANDIDATES ({len(opportunities['CONSOLIDATION_CANDIDATES'])}):")
    for candidate in opportunities['CONSOLIDATION_CANDIDATES']:
        print(f"  Resource: {candidate['resource']}")
        print(f"  Endpoints: {candidate['endpoints']} across {len(candidate['files'])} files")
        print(f"  Files: {', '.join(candidate['files'])}")
        print()
    
    return functional_areas, crud_analysis, opportunities

if __name__ == "__main__":
    os.chdir("/home/enabledrm")
    generate_report()