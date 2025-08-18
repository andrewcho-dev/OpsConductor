#!/usr/bin/env python3
"""
Script to fix stuck job executions that have no logs or are stuck in running state
"""

import sys
import os
sys.path.append('/app')

from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.job_models import JobExecution, JobExecutionBranch, JobActionResult, ExecutionStatus
from app.database.database import get_db

# Database connection
DATABASE_URL = "postgresql://opsconductor:opsconductor_secure_password_2024@postgres:5432/opsconductor_dev"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fix_stuck_executions():
    """Fix stuck executions by creating error logs and updating status"""
    db = SessionLocal()
    
    try:
        print("🔍 Finding stuck executions...")
        
        # Find executions that are failed but have branches still running
        stuck_executions = db.execute(text("""
            SELECT DISTINCT je.id, je.execution_serial, je.job_id
            FROM job_executions je 
            JOIN job_execution_branches jeb ON je.id = jeb.job_execution_id
            WHERE je.status = 'failed' 
            AND jeb.status = 'running'
            AND je.completed_at IS NULL
            ORDER BY je.id
        """)).fetchall()
        
        print(f"📋 Found {len(stuck_executions)} stuck executions")
        
        for execution_row in stuck_executions:
            execution_id = execution_row[0]
            execution_serial = execution_row[1]
            job_id = execution_row[2]
            
            print(f"\n🔧 Fixing execution {execution_id} ({execution_serial})")
            
            # Get all branches for this execution
            branches = db.query(JobExecutionBranch).filter(
                JobExecutionBranch.job_execution_id == execution_id
            ).all()
            
            print(f"   Found {len(branches)} branches")
            
            for branch in branches:
                # Check if this branch already has action results
                existing_results = db.query(JobActionResult).filter(
                    JobActionResult.branch_id == branch.id
                ).count()
                
                if existing_results == 0:
                    print(f"   Creating error log for branch {branch.branch_id} (no existing results)")
                    
                    # Create error action result
                    error_serial = f"{branch.branch_serial}.0001"
                    error_record = JobActionResult(
                        branch_id=branch.id,
                        action_id=1,  # Use existing action ID
                        action_serial=error_serial,
                        action_order=1,
                        action_name="Stuck Execution Recovery",
                        action_type="command",
                        status=ExecutionStatus.FAILED,
                        started_at=branch.started_at or datetime.now(timezone.utc),
                        completed_at=datetime.now(timezone.utc),
                        execution_time_ms=0,
                        result_output="",
                        result_error="Execution was stuck in running state. This error log was created during system recovery to provide visibility into the failed execution.",
                        exit_code=-1,
                        command_executed="N/A - Execution stuck before completion"
                    )
                    
                    db.add(error_record)
                else:
                    print(f"   Branch {branch.branch_id} already has {existing_results} results")
                
                # Update branch status to failed and set completion time
                if branch.status == ExecutionStatus.RUNNING:
                    branch.status = ExecutionStatus.FAILED
                    branch.completed_at = datetime.now(timezone.utc)
                    print(f"   Updated branch {branch.branch_id} status to FAILED")
            
            # Update execution completion time
            execution = db.query(JobExecution).filter(JobExecution.id == execution_id).first()
            if execution and not execution.completed_at:
                execution.completed_at = datetime.now(timezone.utc)
                print(f"   Set execution completion time")
        
        # Commit all changes
        db.commit()
        print(f"\n✅ Successfully fixed {len(stuck_executions)} stuck executions")
        
        # Verify the fixes
        print("\n🔍 Verifying fixes...")
        remaining_stuck = db.execute(text("""
            SELECT COUNT(DISTINCT je.id)
            FROM job_executions je 
            JOIN job_execution_branches jeb ON je.id = jeb.job_execution_id
            WHERE je.status = 'failed' 
            AND jeb.status = 'running'
            AND je.completed_at IS NULL
        """)).fetchone()[0]
        
        print(f"📊 Remaining stuck executions: {remaining_stuck}")
        
        # Show summary of action results created
        total_results = db.execute(text("SELECT COUNT(*) FROM job_action_results")).fetchone()[0]
        print(f"📊 Total action results in system: {total_results}")
        
    except Exception as e:
        print(f"❌ Error fixing stuck executions: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_stuck_executions()