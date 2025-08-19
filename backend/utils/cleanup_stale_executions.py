#!/usr/bin/env python3
"""
Script to clean up stale job executions that are stuck in 'running' status.

This script identifies executions that have been running for too long and marks them as failed.
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import get_db
from app.models.job_models import JobExecution, ExecutionStatus
from sqlalchemy.orm import Session


def cleanup_stale_executions(max_runtime_hours: int = 24):
    """
    Clean up executions that have been running for more than max_runtime_hours.
    
    Args:
        max_runtime_hours: Maximum hours an execution should run before being considered stale
    """
    db: Session = next(get_db())
    
    try:
        # Calculate cutoff time
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_runtime_hours)
        
        # Find stale executions
        stale_executions = db.query(JobExecution).filter(
            JobExecution.status == ExecutionStatus.RUNNING,
            JobExecution.started_at < cutoff_time,
            JobExecution.completed_at.is_(None)
        ).all()
        
        print(f"Found {len(stale_executions)} stale executions")
        
        for execution in stale_executions:
            runtime_hours = (datetime.now(timezone.utc) - execution.started_at).total_seconds() / 3600
            print(f"Execution {execution.id} (Job {execution.job_id}, Execution #{execution.execution_number})")
            print(f"  Started: {execution.started_at}")
            print(f"  Runtime: {runtime_hours:.1f} hours")
            print(f"  Marking as FAILED...")
            
            # Update execution status
            execution.status = ExecutionStatus.FAILED
            execution.completed_at = datetime.now(timezone.utc)
            
            # Also update any running branches for this execution
            for branch in execution.branches:
                if branch.status == ExecutionStatus.RUNNING:
                    print(f"    Branch {branch.id} (Target {branch.target_id}) also marked as FAILED")
                    branch.status = ExecutionStatus.FAILED
                    branch.completed_at = datetime.now(timezone.utc)
                    branch.result_error = "Execution timed out - marked as failed by cleanup script"
        
        # Commit changes
        db.commit()
        print(f"Successfully cleaned up {len(stale_executions)} stale executions")
        
        return len(stale_executions)
        
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def list_running_executions():
    """List all currently running executions for inspection"""
    db: Session = next(get_db())
    
    try:
        running_executions = db.query(JobExecution).filter(
            JobExecution.status == ExecutionStatus.RUNNING
        ).all()
        
        print(f"Currently running executions: {len(running_executions)}")
        
        for execution in running_executions:
            runtime = "Unknown"
            if execution.started_at:
                runtime_seconds = (datetime.now(timezone.utc) - execution.started_at).total_seconds()
                runtime_hours = runtime_seconds / 3600
                if runtime_hours < 1:
                    runtime = f"{runtime_seconds/60:.1f} minutes"
                else:
                    runtime = f"{runtime_hours:.1f} hours"
            
            print(f"  Execution {execution.id}: Job {execution.job_id}, Execution #{execution.execution_number}")
            print(f"    Started: {execution.started_at}")
            print(f"    Runtime: {runtime}")
            print()
            
    except Exception as e:
        print(f"Error listing executions: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up stale job executions")
    parser.add_argument("--list", action="store_true", help="List running executions without cleaning")
    parser.add_argument("--max-hours", type=int, default=24, help="Maximum runtime hours before marking as stale (default: 24)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without making changes")
    
    args = parser.parse_args()
    
    if args.list:
        list_running_executions()
    else:
        if args.dry_run:
            print("DRY RUN MODE - No changes will be made")
            # TODO: Implement dry run logic
        
        cleaned_count = cleanup_stale_executions(args.max_hours)
        print(f"Cleanup complete. {cleaned_count} executions were cleaned up.")