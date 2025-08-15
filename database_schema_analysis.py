#!/usr/bin/env python3
"""
Database Schema Analysis Script
Comprehensive review of ENABLEDRM database schema alignment
"""

import subprocess
import json
import re
from typing import Dict, List, Set, Any

class DatabaseSchemaAnalyzer:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.recommendations = []
        
    def run_db_query(self, query: str) -> str:
        """Execute a database query via docker compose"""
        cmd = [
            'docker', 'compose', 'exec', 'postgres', 
            'psql', '-U', 'opsconductor', '-d', 'opsconductor_dev', 
            '-c', query
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='/home/enabledrm')
        return result.stdout
    
    def get_all_tables(self) -> List[str]:
        """Get all tables in the database"""
        query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
        output = self.run_db_query(query)
        tables = []
        for line in output.split('\n'):
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('tablename') and not line.startswith('('):
                tables.append(line)
        return tables
    
    def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """Get detailed table structure"""
        query = f"\\d {table_name}"
        output = self.run_db_query(query)
        return {"raw_output": output}
    
    def check_foreign_key_consistency(self):
        """Check foreign key relationships"""
        print("🔍 Checking Foreign Key Consistency...")
        
        # Check for broken foreign key references
        query = """
        SELECT 
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_name;
        """
        
        output = self.run_db_query(query)
        print("Foreign Key Relationships:")
        print(output)
    
    def check_missing_indexes(self):
        """Check for missing indexes on foreign keys"""
        print("\n🔍 Checking Missing Indexes...")
        
        query = """
        SELECT 
            t.table_name,
            c.column_name,
            'Missing index on foreign key' as issue
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.tables t 
            ON t.table_name = tc.table_name
        JOIN information_schema.columns c 
            ON c.table_name = tc.table_name 
            AND c.column_name = kcu.column_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND NOT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE tablename = tc.table_name 
            AND indexdef LIKE '%' || kcu.column_name || '%'
        )
        ORDER BY t.table_name, c.column_name;
        """
        
        output = self.run_db_query(query)
        print("Missing Indexes on Foreign Keys:")
        print(output)
    
    def check_enum_consistency(self):
        """Check enum type consistency"""
        print("\n🔍 Checking Enum Types...")
        
        query = """
        SELECT 
            t.typname as enum_name,
            e.enumlabel as enum_value
        FROM pg_type t 
        JOIN pg_enum e ON t.oid = e.enumtypid  
        ORDER BY t.typname, e.enumsortorder;
        """
        
        output = self.run_db_query(query)
        print("Enum Types and Values:")
        print(output)
    
    def check_table_constraints(self):
        """Check table constraints"""
        print("\n🔍 Checking Table Constraints...")
        
        query = """
        SELECT 
            tc.table_name, 
            tc.constraint_name, 
            tc.constraint_type,
            cc.check_clause
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.check_constraints cc 
            ON tc.constraint_name = cc.constraint_name
        WHERE tc.table_schema = 'public'
        ORDER BY tc.table_name, tc.constraint_type;
        """
        
        output = self.run_db_query(query)
        print("Table Constraints:")
        print(output)
    
    def check_alembic_status(self):
        """Check Alembic migration status"""
        print("\n🔍 Checking Alembic Status...")
        
        # Check current version
        query = "SELECT version_num FROM alembic_version;"
        output = self.run_db_query(query)
        print("Current Alembic Version:")
        print(output)
        
        # Check if alembic_version table exists and is properly configured
        query = "\\d alembic_version"
        output = self.run_db_query(query)
        print("Alembic Version Table Structure:")
        print(output)
    
    def analyze_model_vs_database_alignment(self):
        """Analyze alignment between SQLAlchemy models and database"""
        print("\n🔍 Analyzing Model vs Database Alignment...")
        
        # Expected tables based on models
        expected_tables = {
            'users', 'user_sessions', 'universal_targets', 'target_communication_methods',
            'target_credentials', 'jobs', 'job_actions', 'job_targets', 'job_executions',
            'job_execution_branches', 'job_action_results', 'job_execution_logs',
            'job_schedules', 'schedule_executions', 'performance_metrics',
            'system_health_snapshots', 'analytics_alert_rules', 'report_templates',
            'generated_reports', 'discovery_jobs', 'discovered_devices',
            'discovery_templates', 'discovery_schedules', 'notification_templates',
            'notification_logs', 'alert_rules', 'alert_logs', 'celery_task_history',
            'celery_metrics_snapshots', 'system_settings', 'device_types',
            'device_type_categories', 'device_type_templates', 'device_type_usage'
        }
        
        actual_tables = set(self.get_all_tables())
        
        missing_tables = expected_tables - actual_tables
        extra_tables = actual_tables - expected_tables
        
        if missing_tables:
            print(f"❌ MISSING TABLES: {missing_tables}")
            self.issues.append(f"Missing tables: {missing_tables}")
        
        if extra_tables:
            print(f"⚠️  EXTRA TABLES: {extra_tables}")
            self.warnings.append(f"Extra tables (possibly orphaned): {extra_tables}")
        
        common_tables = expected_tables & actual_tables
        print(f"✅ ALIGNED TABLES ({len(common_tables)}): {sorted(common_tables)}")
    
    def check_critical_issues(self):
        """Check for critical database issues"""
        print("\n🔍 Checking Critical Issues...")
        
        # Check for tables without primary keys
        query = """
        SELECT table_name 
        FROM information_schema.tables t
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints tc
            WHERE tc.table_name = t.table_name 
            AND tc.constraint_type = 'PRIMARY KEY'
        );
        """
        
        output = self.run_db_query(query)
        if output.strip() and '(0 rows)' not in output:
            print("❌ CRITICAL: Tables without primary keys:")
            print(output)
            self.issues.append("Tables without primary keys found")
        else:
            print("✅ All tables have primary keys")
    
    def check_data_integrity(self):
        """Check basic data integrity"""
        print("\n🔍 Checking Data Integrity...")
        
        # Check for orphaned records
        queries = [
            ("Orphaned job_targets", "SELECT COUNT(*) FROM job_targets jt LEFT JOIN jobs j ON jt.job_id = j.id WHERE j.id IS NULL;"),
            ("Orphaned job_actions", "SELECT COUNT(*) FROM job_actions ja LEFT JOIN jobs j ON ja.job_id = j.id WHERE j.id IS NULL;"),
            ("Orphaned target_credentials", "SELECT COUNT(*) FROM target_credentials tc LEFT JOIN target_communication_methods tcm ON tc.communication_method_id = tcm.id WHERE tcm.id IS NULL;"),
        ]
        
        for check_name, query in queries:
            output = self.run_db_query(query)
            count = 0
            for line in output.split('\n'):
                if line.strip().isdigit():
                    count = int(line.strip())
                    break
            
            if count > 0:
                print(f"❌ {check_name}: {count} orphaned records")
                self.issues.append(f"{check_name}: {count} orphaned records")
            else:
                print(f"✅ {check_name}: No orphaned records")
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "="*80)
        print("📊 DATABASE SCHEMA ANALYSIS REPORT")
        print("="*80)
        
        if self.issues:
            print("\n❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"  • {issue}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for rec in self.recommendations:
                print(f"  • {rec}")
        
        if not self.issues and not self.warnings:
            print("\n✅ DATABASE SCHEMA IS HEALTHY!")
        
        print("\n" + "="*80)
    
    def run_full_analysis(self):
        """Run complete database schema analysis"""
        print("🚀 Starting Comprehensive Database Schema Analysis...")
        print("="*80)
        
        self.analyze_model_vs_database_alignment()
        self.check_foreign_key_consistency()
        self.check_missing_indexes()
        self.check_enum_consistency()
        self.check_table_constraints()
        self.check_alembic_status()
        self.check_critical_issues()
        self.check_data_integrity()
        
        self.generate_report()

if __name__ == "__main__":
    analyzer = DatabaseSchemaAnalyzer()
    analyzer.run_full_analysis()