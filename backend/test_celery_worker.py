#!/usr/bin/env python3
"""
Test the same code path but within Celery worker environment
"""
import sys
import os

from app.database.database import SessionLocal
from app.services.job_service import JobService
from app.services.job_execution_service import JobExecutionService
from app.models.universal_target_models import UniversalTarget
from app.models.job_models import JobExecution

def test_celery_worker_execution():
    """Test execution path within Celery worker context"""
    print("=== TESTING CELERY WORKER EXECUTION ===")
    
    db = SessionLocal()
    try:
        job_service = JobService(db)
        
        # Get the first job execution
        executions = db.query(JobExecution).limit(1).all()
        if not executions:
            print("No job executions found")
            return
            
        execution = executions[0]
        print(f"Testing execution {execution.id} for job {execution.job_id}")
        
        # Get targets for this job
        targets = db.query(UniversalTarget).filter(
            UniversalTarget.id.in_([jt.target_id for jt in execution.job.targets])
        ).all()
        
        print(f"Found {len(targets)} targets")
        
        if not targets:
            print("No targets found")
            return
            
        target = targets[0]
        print(f"Testing with target: {target.name}")
        
        # Now test the JobExecutionService path that Celery uses
        execution_service = JobExecutionService(job_service)
        
        # Test the _get_primary_communication_method
        comm_method = execution_service._get_primary_communication_method(target)
        
        if not comm_method:
            print("No communication method found")
            return
            
        print(f"Communication method: {comm_method.method_type}")
        print(f"Config type: {type(comm_method.config)}")
        print(f"Config content: {comm_method.config}")
        
        # Test the exact line that's failing in Celery
        try:
            port = comm_method.config.get('port', 22)
            print(f"Port access successful: {port}")
        except Exception as e:
            print(f"ERROR accessing config.get(): {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            
        # Test the full _execute_ssh_action or _execute_winrm_action path
        if execution.job.actions:
            action = execution.job.actions[0]
            print(f"Testing action: {action.action_name}")
            
            try:
                if comm_method.method_type == "ssh":
                    import asyncio
                    result = asyncio.run(execution_service._execute_ssh_action(target, action, comm_method))
                    print(f"SSH action result: {result}")
                elif comm_method.method_type == "winrm":
                    import asyncio
                    result = asyncio.run(execution_service._execute_winrm_action(target, action, comm_method))
                    print(f"WinRM action result: {result}")
            except Exception as e:
                print(f"ERROR in action execution: {e}")
                import traceback
                traceback.print_exc()
            
    except Exception as e:
        print(f"Celery worker test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_celery_worker_execution()