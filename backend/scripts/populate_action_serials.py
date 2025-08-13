#!/usr/bin/env python3
"""
Populate Action Serialization Script
Generates action serials for existing JobActionResult records using the new format.
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
from app.models.job_models import Job, JobExecution, JobExecutionBranch, JobActionResult
from app.services.serial_service import SerialService

def populate_action_serials():
    """Populate action serials for existing records"""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🚀 Starting action serialization population...")
        
        # Get all action results that need serials
        action_results = db.query(JobActionResult).join(
            JobExecutionBranch, JobActionResult.branch_id == JobExecutionBranch.id
        ).join(
            JobExecution, JobExecutionBranch.job_execution_id == JobExecution.id
        ).join(
            Job, JobExecution.job_id == Job.id
        ).filter(
            JobActionResult.action_serial.is_(None)
        ).order_by(
            Job.id, JobExecution.id, JobExecutionBranch.id, JobActionResult.action_order
        ).all()
        
        print(f"   Found {len(action_results)} action results to process...")
        
        actions_updated = 0
        branch_counters = {}  # Track action counters per branch
        
        for action_result in action_results:
            branch = action_result.branch
            branch_serial = branch.branch_serial
            
            if not branch_serial:
                print(f"   ⚠️  Skipping action result {action_result.id} - branch has no serial")
                continue
            
            # Get or initialize counter for this branch
            if branch_serial not in branch_counters:
                branch_counters[branch_serial] = 0
            
            branch_counters[branch_serial] += 1
            action_num = branch_counters[branch_serial]
            
            # Generate action serial: J20250000001.0001.0001.0001
            action_serial = f"{branch_serial}.{action_num:04d}"
            
            # Update the action result
            action_result.action_serial = action_serial
            
            print(f"   Generated action serial: {action_serial} (order: {action_result.action_order})")
            actions_updated += 1
        
        # Commit all changes
        db.commit()
        
        print(f"\n✅ Action serialization population completed!")
        print(f"   🎯 Action results updated: {actions_updated}")
        
        # Add unique constraint now that all records have serials
        if actions_updated > 0:
            print(f"\n🔧 Adding unique constraint...")
            try:
                db.execute(text("""
                    ALTER TABLE job_action_results 
                    ADD CONSTRAINT uq_job_action_results_action_serial 
                    UNIQUE (action_serial)
                """))
                db.commit()
                print(f"   ✅ Unique constraint added successfully")
            except Exception as e:
                print(f"   ⚠️  Could not add unique constraint: {e}")
                print(f"   This might be normal if constraint already exists")
        
        # Verify the results
        print(f"\n🔍 Verification:")
        sample_action = db.query(JobActionResult).filter(
            JobActionResult.action_serial.isnot(None)
        ).first()
        
        if sample_action:
            print(f"   Sample action serial: {sample_action.action_serial}")
            
            # Validate the serial format
            if SerialService.validate_action_serial(sample_action.action_serial):
                print(f"   ✅ Serial format validation: PASSED")
                
                # Parse the serial
                parsed = SerialService.parse_action_serial(sample_action.action_serial)
                if parsed:
                    print(f"   📊 Parsed components:")
                    print(f"      Job: {parsed['job_serial']}")
                    print(f"      Execution: {parsed['execution_number']}")
                    print(f"      Branch: {parsed['branch_number']}")
                    print(f"      Action: {parsed['action_number']}")
            else:
                print(f"   ❌ Serial format validation: FAILED")
        
        # Show hierarchy example
        print(f"\n📋 Complete Hierarchy Example:")
        sample_branch = db.query(JobExecutionBranch).join(JobExecution).join(Job).filter(
            JobExecutionBranch.branch_serial.isnot(None)
        ).first()
        
        if sample_branch:
            job_serial = sample_branch.execution.job.job_serial
            execution_serial = sample_branch.execution.execution_serial
            branch_serial = sample_branch.branch_serial
            
            sample_action = db.query(JobActionResult).filter(
                JobActionResult.branch_id == sample_branch.id,
                JobActionResult.action_serial.isnot(None)
            ).first()
            
            print(f"   Job:       {job_serial}")
            print(f"   Execution: {execution_serial}")
            print(f"   Branch:    {branch_serial}")
            if sample_action:
                print(f"   Action:    {sample_action.action_serial}")
        
    except Exception as e:
        print(f"❌ Error during population: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_action_serials()