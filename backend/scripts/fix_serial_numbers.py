#!/usr/bin/env python3
"""
Serial Number Standardization Script
Fixes all serial numbers to conform to the correct formats:
- Jobs: J20250000001 (12 chars: J + 4-digit year + 7-digit number)
- Targets: T20250000001 (12 chars: T + 4-digit year + 7-digit number)
- Executions: J20250000001.0001 (job serial + . + 4-digit execution number)
- Branches: J20250000001.0001.0001 (execution serial + . + 4-digit branch number)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.database import get_db
from app.models.universal_target_models import UniversalTarget
from app.models.job_models import Job, JobExecution, JobExecutionBranch
from datetime import datetime
import re

def fix_target_serials(session: Session):
    """Fix all target serial numbers to T20250000001 format"""
    print("🔧 Fixing target serial numbers...")
    
    # Get all targets with incorrect serial formats
    targets = session.query(UniversalTarget).all()
    
    # Group targets by year for proper sequencing
    targets_by_year = {}
    for target in targets:
        created_year = target.created_at.year if target.created_at else datetime.now().year
        if created_year not in targets_by_year:
            targets_by_year[created_year] = []
        targets_by_year[created_year].append(target)
    
    total_fixed = 0
    
    for year, year_targets in targets_by_year.items():
        print(f"  📅 Processing {len(year_targets)} targets for year {year}")
        
        # Get the highest existing correct serial number for this year
        result = session.execute(text("""
            SELECT COALESCE(MAX(CAST(SUBSTRING(target_serial FROM 6) AS INTEGER)), 0) as max_num
            FROM universal_targets 
            WHERE target_serial ~ :pattern
        """), {"pattern": f"^T{year}[0-9]{{7}}$"})
        
        next_num = result.fetchone()[0] + 1
        
        # Fix each target's serial
        for target in year_targets:
            old_serial = target.target_serial
            
            # Check if serial needs fixing
            needs_fix = False
            if not old_serial:
                needs_fix = True
                reason = "missing serial"
            elif old_serial.startswith('TGT-'):
                needs_fix = True
                reason = "old TGT- format"
            elif re.match(r'^T\d{4}\d{5}$', old_serial):  # T202500001 (5 digits)
                needs_fix = True
                reason = "5-digit format"
            elif not re.match(r'^T\d{4}\d{7}$', old_serial):  # Not T20250000001 (7 digits)
                needs_fix = True
                reason = "invalid format"
            
            if needs_fix:
                new_serial = f"T{year}{next_num:07d}"
                print(f"    🔄 {old_serial or 'NULL'} -> {new_serial} ({reason})")
                
                target.target_serial = new_serial
                next_num += 1
                total_fixed += 1
                
                # Update any job execution branches that reference this target
                branches = session.query(JobExecutionBranch).filter(
                    JobExecutionBranch.target_id == target.id
                ).all()
                
                for branch in branches:
                    if branch.target_serial_ref != new_serial:
                        print(f"      🔗 Updating branch reference: {branch.target_serial_ref} -> {new_serial}")
                        branch.target_serial_ref = new_serial
    
    session.commit()
    print(f"✅ Fixed {total_fixed} target serial numbers")
    return total_fixed

def fix_job_serials(session: Session):
    """Fix all job serial numbers to J20250000001 format"""
    print("🔧 Fixing job serial numbers...")
    
    # Get all jobs
    jobs = session.query(Job).all()
    
    # Group jobs by year for proper sequencing
    jobs_by_year = {}
    for job in jobs:
        created_year = job.created_at.year if job.created_at else datetime.now().year
        if created_year not in jobs_by_year:
            jobs_by_year[created_year] = []
        jobs_by_year[created_year].append(job)
    
    total_fixed = 0
    
    for year, year_jobs in jobs_by_year.items():
        print(f"  📅 Processing {len(year_jobs)} jobs for year {year}")
        
        # Get the highest existing correct serial number for this year
        result = session.execute(text("""
            SELECT COALESCE(MAX(CAST(SUBSTRING(job_serial FROM 6) AS INTEGER)), 0) as max_num
            FROM jobs 
            WHERE job_serial ~ :pattern
        """), {"pattern": f"^J{year}[0-9]{{7}}$"})
        
        next_num = result.fetchone()[0] + 1
        
        # Fix each job's serial
        for job in year_jobs:
            old_serial = job.job_serial
            
            # Check if serial needs fixing
            needs_fix = False
            if not old_serial:
                needs_fix = True
                reason = "missing serial"
            elif not re.match(r'^J\d{4}\d{7}$', old_serial):  # Not J20250000001 (7 digits)
                needs_fix = True
                reason = "invalid format"
            
            if needs_fix:
                new_serial = f"J{year}{next_num:07d}"
                print(f"    🔄 {old_serial or 'NULL'} -> {new_serial} ({reason})")
                
                old_job_serial = job.job_serial
                job.job_serial = new_serial
                next_num += 1
                total_fixed += 1
                
                # Update execution serials that reference this job
                executions = session.query(JobExecution).filter(
                    JobExecution.job_id == job.id
                ).all()
                
                for execution in executions:
                    if execution.execution_serial and old_job_serial in execution.execution_serial:
                        old_exec_serial = execution.execution_serial
                        # Replace the job part of the execution serial
                        exec_parts = old_exec_serial.split('.')
                        if len(exec_parts) >= 2:
                            new_exec_serial = f"{new_serial}.{exec_parts[1]}"
                            if len(exec_parts) == 3:  # Branch serial
                                new_exec_serial += f".{exec_parts[2]}"
                            
                            print(f"      🔗 Updating execution serial: {old_exec_serial} -> {new_exec_serial}")
                            execution.execution_serial = new_exec_serial
                            
                            # Update branch serials
                            branches = session.query(JobExecutionBranch).filter(
                                JobExecutionBranch.job_execution_id == execution.id
                            ).all()
                            
                            for branch in branches:
                                if branch.branch_serial and old_job_serial in branch.branch_serial:
                                    old_branch_serial = branch.branch_serial
                                    branch_parts = old_branch_serial.split('.')
                                    if len(branch_parts) == 3:
                                        # Ensure branch number is 4 digits
                                        branch_num = branch_parts[2].zfill(4)
                                        new_branch_serial = f"{new_serial}.{branch_parts[1]}.{branch_num}"
                                        print(f"        🌿 Updating branch serial: {old_branch_serial} -> {new_branch_serial}")
                                        branch.branch_serial = new_branch_serial
    
    session.commit()
    print(f"✅ Fixed {total_fixed} job serial numbers")
    return total_fixed

def fix_branch_serials(session: Session):
    """Fix all branch serial numbers to have 4-digit branch numbers"""
    print("🔧 Fixing branch serial numbers...")
    
    # Get all branches with incorrect serial formats
    branches = session.query(JobExecutionBranch).filter(
        JobExecutionBranch.branch_serial.isnot(None)
    ).all()
    
    total_fixed = 0
    
    for branch in branches:
        old_serial = branch.branch_serial
        
        # Check if serial needs fixing
        needs_fix = False
        if not re.match(r'^J\d{4}\d{7}\.\d{4}\.\d{4}$', old_serial):
            needs_fix = True
            
            # Try to fix it
            parts = old_serial.split('.')
            if len(parts) == 3:
                job_part = parts[0]
                exec_part = parts[1].zfill(4)  # Ensure 4 digits
                branch_part = parts[2].zfill(4)  # Ensure 4 digits
                
                new_serial = f"{job_part}.{exec_part}.{branch_part}"
                
                if new_serial != old_serial:
                    print(f"    🔄 {old_serial} -> {new_serial}")
                    branch.branch_serial = new_serial
                    total_fixed += 1
    
    session.commit()
    print(f"✅ Fixed {total_fixed} branch serial numbers")
    return total_fixed

def validate_all_serials(session: Session):
    """Validate that all serial numbers are now in correct format"""
    print("🔍 Validating all serial numbers...")
    
    errors = []
    
    # Validate target serials
    targets = session.query(UniversalTarget).all()
    for target in targets:
        if not target.target_serial:
            errors.append(f"Target ID {target.id}: Missing serial number")
        elif not re.match(r'^T\d{4}\d{7}$', target.target_serial):
            errors.append(f"Target ID {target.id}: Invalid serial format '{target.target_serial}'")
    
    # Validate job serials
    jobs = session.query(Job).all()
    for job in jobs:
        if not job.job_serial:
            errors.append(f"Job ID {job.id}: Missing serial number")
        elif not re.match(r'^J\d{4}\d{7}$', job.job_serial):
            errors.append(f"Job ID {job.id}: Invalid serial format '{job.job_serial}'")
    
    # Validate execution serials
    executions = session.query(JobExecution).all()
    for execution in executions:
        if execution.execution_serial:
            if not re.match(r'^J\d{4}\d{7}\.\d{4}$', execution.execution_serial):
                errors.append(f"Execution ID {execution.id}: Invalid serial format '{execution.execution_serial}'")
    
    # Validate branch serials
    branches = session.query(JobExecutionBranch).all()
    for branch in branches:
        if branch.branch_serial:
            if not re.match(r'^J\d{4}\d{7}\.\d{4}\.\d{4}$', branch.branch_serial):
                errors.append(f"Branch ID {branch.id}: Invalid serial format '{branch.branch_serial}'")
    
    if errors:
        print("❌ Validation errors found:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  • {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
        return False
    else:
        print("✅ All serial numbers are valid!")
        return True

def show_serial_summary(session: Session):
    """Show summary of current serial numbers"""
    print("📊 Serial Number Summary:")
    
    # Target serials
    result = session.execute(text("""
        SELECT 
            CASE 
                WHEN target_serial ~ '^T[0-9]{4}[0-9]{7}$' THEN 'Correct (T20250000001)'
                WHEN target_serial LIKE 'TGT-%' THEN 'Old Format (TGT-2025-000001)'
                WHEN target_serial ~ '^T[0-9]{4}[0-9]{5}$' THEN 'Short Format (T202500001)'
                ELSE 'Other/Invalid'
            END as format_type,
            COUNT(*) as count
        FROM universal_targets 
        WHERE target_serial IS NOT NULL
        GROUP BY format_type
        ORDER BY count DESC
    """))
    
    print("  🎯 Target Serials:")
    for row in result:
        print(f"    • {row[0]}: {row[1]} targets")
    
    # Job serials
    result = session.execute(text("""
        SELECT 
            CASE 
                WHEN job_serial ~ '^J[0-9]{4}[0-9]{7}$' THEN 'Correct (J20250000001)'
                ELSE 'Other/Invalid'
            END as format_type,
            COUNT(*) as count
        FROM jobs 
        WHERE job_serial IS NOT NULL
        GROUP BY format_type
        ORDER BY count DESC
    """))
    
    print("  💼 Job Serials:")
    for row in result:
        print(f"    • {row[0]}: {row[1]} jobs")

def main():
    """Main function to fix all serial numbers"""
    print("🚀 Starting Serial Number Standardization")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Show current state
        show_serial_summary(db)
        print()
        
        # Fix target serials
        target_fixes = fix_target_serials(db)
        print()
        
        # Fix job serials
        job_fixes = fix_job_serials(db)
        print()
        
        # Fix branch serials
        branch_fixes = fix_branch_serials(db)
        print()
        
        # Validate all serials
        validation_passed = validate_all_serials(db)
        print()
        
        # Show final summary
        show_serial_summary(db)
        
        print("=" * 50)
        print(f"🎉 Serial Number Standardization Complete!")
        print(f"   • Fixed {target_fixes} target serials")
        print(f"   • Fixed {job_fixes} job serials")
        print(f"   • Fixed {branch_fixes} branch serials")
        print(f"   • Validation: {'✅ PASSED' if validation_passed else '❌ FAILED'}")
        
        if not validation_passed:
            print("⚠️  Some serial numbers still need attention. Check the validation errors above.")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during serial number standardization: {e}")
        db.rollback()
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    exit(main())