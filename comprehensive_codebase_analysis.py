#!/usr/bin/env python3
"""
OpsConductor Comprehensive Codebase Analysis
Analyzes the entire codebase to identify duplications, legacy code, and consolidation opportunities
"""

import os
import ast
import re
from pathlib import Path
from collections import defaultdict
import json

class CodebaseAnalyzer:
    def __init__(self, root_path="/home/enabledrm"):
        self.root_path = Path(root_path)
        self.backend_path = self.root_path / "backend"
        self.analysis = {
            "apis": {
                "v1": [],
                "v2": [],
                "routers": [],
                "legacy": []
            },
            "services": {
                "app_services": [],
                "backend_services": [],
                "duplicates": []
            },
            "models": [],
            "schemas": [],
            "duplications": [],
            "recommendations": []
        }
    
    def analyze_python_file(self, file_path):
        """Analyze a Python file for classes, functions, and endpoints"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            info = {
                "path": str(file_path),
                "classes": [],
                "functions": [],
                "endpoints": [],
                "imports": [],
                "decorators": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    info["classes"].append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    info["functions"].append(node.name)
                    # Check for FastAPI decorators
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Attribute):
                            if decorator.attr in ['get', 'post', 'put', 'delete', 'patch']:
                                info["decorators"].append(f"{decorator.attr}")
                        elif isinstance(decorator, ast.Name):
                            if decorator.id in ['get', 'post', 'put', 'delete', 'patch']:
                                info["decorators"].append(decorator.id)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        info["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            info["imports"].append(f"{node.module}.{alias.name}")
            
            # Extract endpoint patterns from content
            endpoint_patterns = re.findall(r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content)
            for method, path in endpoint_patterns:
                info["endpoints"].append(f"{method.upper()} {path}")
            
            return info
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def analyze_apis(self):
        """Analyze all API files"""
        print("🔍 Analyzing API structure...")
        
        # V1 APIs
        v1_path = self.backend_path / "app" / "api" / "v1"
        if v1_path.exists():
            for file_path in v1_path.glob("*.py"):
                if file_path.name != "__init__.py":
                    info = self.analyze_python_file(file_path)
                    if info:
                        self.analysis["apis"]["v1"].append(info)
        
        # V2 APIs
        v2_path = self.backend_path / "app" / "api" / "v2"
        if v2_path.exists():
            for file_path in v2_path.glob("*.py"):
                if file_path.name != "__init__.py":
                    info = self.analyze_python_file(file_path)
                    if info:
                        self.analysis["apis"]["v2"].append(info)
        
        # Routers
        routers_path = self.backend_path / "app" / "routers"
        if routers_path.exists():
            for file_path in routers_path.glob("*.py"):
                if file_path.name != "__init__.py":
                    info = self.analyze_python_file(file_path)
                    if info:
                        self.analysis["apis"]["routers"].append(info)
        
        # Backend routers (legacy)
        backend_routers_path = self.backend_path / "routers"
        if backend_routers_path.exists():
            for file_path in backend_routers_path.glob("*.py"):
                if file_path.name != "__init__.py":
                    info = self.analyze_python_file(file_path)
                    if info:
                        self.analysis["apis"]["legacy"].append(info)
    
    def analyze_services(self):
        """Analyze all service files"""
        print("🔍 Analyzing service structure...")
        
        # App services
        app_services_path = self.backend_path / "app" / "services"
        if app_services_path.exists():
            for file_path in app_services_path.glob("*.py"):
                if file_path.name != "__init__.py":
                    info = self.analyze_python_file(file_path)
                    if info:
                        self.analysis["services"]["app_services"].append(info)
        
        # Backend services
        backend_services_path = self.backend_path / "services"
        if backend_services_path.exists():
            for file_path in backend_services_path.glob("*.py"):
                if file_path.name != "__init__.py":
                    info = self.analyze_python_file(file_path)
                    if info:
                        self.analysis["services"]["backend_services"].append(info)
    
    def analyze_models_and_schemas(self):
        """Analyze models and schemas"""
        print("🔍 Analyzing models and schemas...")
        
        # Models
        models_path = self.backend_path / "app" / "models"
        if models_path.exists():
            for file_path in models_path.glob("*.py"):
                if file_path.name != "__init__.py":
                    info = self.analyze_python_file(file_path)
                    if info:
                        self.analysis["models"].append(info)
        
        # Schemas
        schemas_path = self.backend_path / "app" / "schemas"
        if schemas_path.exists():
            for file_path in schemas_path.glob("*.py"):
                if file_path.name != "__init__.py":
                    info = self.analyze_python_file(file_path)
                    if info:
                        self.analysis["schemas"].append(info)
    
    def find_duplications(self):
        """Find duplicate functionality across services"""
        print("🔍 Finding duplications...")
        
        # Compare service classes
        app_service_classes = {}
        backend_service_classes = {}
        
        for service in self.analysis["services"]["app_services"]:
            for class_name in service["classes"]:
                app_service_classes[class_name] = service["path"]
        
        for service in self.analysis["services"]["backend_services"]:
            for class_name in service["classes"]:
                backend_service_classes[class_name] = service["path"]
        
        # Find duplicates
        for class_name in app_service_classes:
            if class_name in backend_service_classes:
                self.analysis["services"]["duplicates"].append({
                    "class": class_name,
                    "app_path": app_service_classes[class_name],
                    "backend_path": backend_service_classes[class_name]
                })
    
    def generate_recommendations(self):
        """Generate consolidation recommendations"""
        print("🔍 Generating recommendations...")
        
        recommendations = []
        
        # Service duplications
        if self.analysis["services"]["duplicates"]:
            recommendations.append({
                "category": "Service Duplications",
                "priority": "HIGH",
                "description": f"Found {len(self.analysis['services']['duplicates'])} duplicate service classes",
                "action": "Consolidate duplicate services - keep app/services versions, remove backend/services",
                "files_affected": [dup["backend_path"] for dup in self.analysis["services"]["duplicates"]]
            })
        
        # API analysis
        v1_count = len(self.analysis["apis"]["v1"])
        v2_count = len(self.analysis["apis"]["v2"])
        router_count = len(self.analysis["apis"]["routers"])
        legacy_count = len(self.analysis["apis"]["legacy"])
        
        if v1_count > 0:
            recommendations.append({
                "category": "V1 APIs",
                "priority": "MEDIUM",
                "description": f"Found {v1_count} V1 API files that could be migrated to V2",
                "action": "Review V1 APIs for migration to V2 or deprecation",
                "files_affected": [api["path"] for api in self.analysis["apis"]["v1"]]
            })
        
        if legacy_count > 0:
            recommendations.append({
                "category": "Legacy Routers",
                "priority": "HIGH",
                "description": f"Found {legacy_count} legacy router files in backend/routers",
                "action": "Remove legacy routers - functionality should be in app/routers or V2 APIs",
                "files_affected": [api["path"] for api in self.analysis["apis"]["legacy"]]
            })
        
        # Count total endpoints
        total_endpoints = 0
        for api_type in ["v1", "v2", "routers", "legacy"]:
            for api in self.analysis["apis"][api_type]:
                total_endpoints += len(api["endpoints"])
        
        recommendations.append({
            "category": "API Consolidation Status",
            "priority": "INFO",
            "description": f"Total endpoints: {total_endpoints} across {v1_count + v2_count + router_count + legacy_count} files",
            "action": f"V2 APIs: {v2_count} files, V1 APIs: {v1_count} files, Routers: {router_count} files, Legacy: {legacy_count} files",
            "files_affected": []
        })
        
        self.analysis["recommendations"] = recommendations
    
    def print_summary(self):
        """Print analysis summary"""
        print("\n" + "="*80)
        print("🎯 OPSCONDUCTOR CODEBASE ANALYSIS SUMMARY")
        print("="*80)
        
        print(f"\n📊 API STRUCTURE:")
        print(f"  • V2 APIs: {len(self.analysis['apis']['v2'])} files")
        print(f"  • V1 APIs: {len(self.analysis['apis']['v1'])} files")
        print(f"  • App Routers: {len(self.analysis['apis']['routers'])} files")
        print(f"  • Legacy Routers: {len(self.analysis['apis']['legacy'])} files")
        
        print(f"\n🔧 SERVICES:")
        print(f"  • App Services: {len(self.analysis['services']['app_services'])} files")
        print(f"  • Backend Services: {len(self.analysis['services']['backend_services'])} files")
        print(f"  • Duplicate Services: {len(self.analysis['services']['duplicates'])} classes")
        
        print(f"\n📋 DATA LAYER:")
        print(f"  • Models: {len(self.analysis['models'])} files")
        print(f"  • Schemas: {len(self.analysis['schemas'])} files")
        
        print(f"\n🚨 RECOMMENDATIONS ({len(self.analysis['recommendations'])}):")
        for i, rec in enumerate(self.analysis["recommendations"], 1):
            priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "INFO": "ℹ️"}
            emoji = priority_emoji.get(rec["priority"], "❓")
            print(f"  {i}. {emoji} [{rec['priority']}] {rec['category']}")
            print(f"     {rec['description']}")
            print(f"     Action: {rec['action']}")
            if rec["files_affected"]:
                print(f"     Files: {len(rec['files_affected'])} affected")
            print()
    
    def save_detailed_report(self):
        """Save detailed analysis to JSON file"""
        report_path = self.root_path / "codebase_analysis_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.analysis, f, indent=2)
        print(f"📄 Detailed report saved to: {report_path}")
    
    def run_analysis(self):
        """Run complete analysis"""
        print("🚀 Starting OpsConductor Codebase Analysis...")
        
        self.analyze_apis()
        self.analyze_services()
        self.analyze_models_and_schemas()
        self.find_duplications()
        self.generate_recommendations()
        
        self.print_summary()
        self.save_detailed_report()
        
        print("\n✅ Analysis complete!")

if __name__ == "__main__":
    analyzer = CodebaseAnalyzer()
    analyzer.run_analysis()