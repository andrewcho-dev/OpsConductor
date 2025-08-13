#!/usr/bin/env python3
"""
Populate Execution Serialization Script
Generates execution and branch serials for existing records using the new compact format.
"""

import sys
import os
import uuid
from datetime import datetime

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.job_models import Job, JobExecution, JobExecutionBranch
from app.models.universal_target_models import UniversalTarget
from app.services.serial_service import SerialService

def populate_execution_serials():
    """Populate execution and branch serials for existing records"""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🚀 Starting execution serialization population...")
        
        # Update existing jobs to use compact format if needed
        jobs_updated = 0
        jobs = db.query(Job).all()
        for job in jobs:
            if job.job_serial and (job.job_serial.startswith('JOB-') or len(job.job_serial) > 9):
                # Convert old format to new compact format
                year = datetime.now().year
                # Extract number from old format or generate new
                try:
                    if 'JOB-' in job.job_serial:
                        old_parts = job.job_serial.split('-')
                        if len(old_parts) >= 3:
                            old_number = int(old_parts[2])
                        else:
                            old_number = job.id
                    else:
                        old_number = job.id
                except:
                    old_number = job.id
                
                new_serial = f"J{year}{old_number:05d}"
                print(f"  Converting job serial: {job.job_serial} → {new_serial}")
                job.job_serial = new_serial
                jobs_updated += 1
        
        # Update existing targets to use compact format if needed
        targets_updated = 0
        targets = db.query(UniversalTarget).all()
        for target in targets:
            if target.target_serial and (target.target_serial.startswith('TGT-') or len(target.target_serial) > 9):
                # Convert old format to new compact format
                year = datetime.now().year
                try:
                    if 'TGT-' in target.target_serial:
                        old_parts = target.target_serial.split('-')
                        if len(old_parts) >= 3:
                            old_number = int(old_parts[2])
                        else:
                            old_number = target.id
                    else:
                        old_number = target.id
                except:
                    old_number = target.id
                
                new_serial = f"T{year}{old_number:05d}"
                print(f"  Converting target serial: {target.target_serial} → {new_serial}")
                target.target_serial = new_serial
                targets_updated += 1
        
        # Populate execution serials
        executions_updated = 0
        executions = db.query(JobExecution).join(Job).order_by(Job.id, JobExecution.id).all()
        
        # Track execution numbers per job to ensure uniqueness
        job_exec_counters = {}
        
        for execution in executions:
            if not execution.execution_uuid:
                execution.execution_uuid = uuid.uuid4()
            
            if not execution.execution_serial:
                job_serial = execution.job.job_serial
                
                # Get or initialize counter for this job
                if job_serial not in job_exec_counters:
                    job_exec_counters[job_serial] = 0
                
                job_exec_counters[job_serial] += 1
                exec_num = job_exec_counters[job_serial]
                
                # Update the execution number to ensure consistency
                execution.execution_number = exec_num
                
                execution_serial = f"{job_serial}.{exec_num:04d}"
                execution.execution_serial = execution_serial
                print(f"  Generated execution serial: {execution_serial}")
                executions_updated += 1
        
        # Populate branch serials
        branches_updated = 0
        branches = db.query(JobExecutionBranch).join(JobExecution).join(Job).join(UniversalTarget).all()
        for branch in branches:
            if not branch.branch_uuid:
                branch.branch_uuid = uuid.uuid4()
            
            if not branch.branch_serial:
                execution_serial = branch.execution.execution_serial
                branch_num = int(branch.branch_id) if branch.branch_id.isdigit() else 1
                branch_serial = f"{execution_serial}.{branch_num:04d}"
                branch.branch_serial = branch_serial
                
                # Set target serial reference
                if branch.target and branch.target.target_serial:
                    branch.target_serial_ref = branch.target.target_serial
                
                print(f"  Generated branch serial: {branch_serial} → {branch.target_serial_ref}")
                branches_updated += 1
        
        # Commit all changes
        db.commit()
        
        print(f"\n✅ Execution serialization population completed!")
        print(f"   📊 Jobs updated: {jobs_updated}")
        print(f"   🎯 Targets updated: {targets_updated}")
        print(f"   🔄 Executions updated: {executions_updated}")
        print(f"   🌿 Branches updated: {branches_updated}")
        
        # Verify the results
        print(f"\n🔍 Verification:")
        sample_execution = db.query(JobExecution).filter(JobExecution.execution_serial.isnot(None)).first()
        if sample_execution:
            print(f"   Sample execution serial: {sample_execution.execution_serial}")
        
        sample_branch = db.query(JobExecutionBranch).filter(JobExecutionBranch.branch_serial.isnot(None)).first()
        if sample_branch:
            print(f"   Sample branch serial: {sample_branch.branch_serial}")
            print(f"   Target reference: {sample_branch.target_serial_ref}")
        
    except Exception as e:
        print(f"❌ Error during population: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_execution_serials()