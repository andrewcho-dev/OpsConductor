#!/usr/bin/env python3
"""
Direct test to isolate the Celery vs Direct execution issue
"""
import sys
import os

from app.database.database import SessionLocal
from app.services.job_service import JobService
from app.services.job_execution_service import JobExecutionService
from app.models.universal_target_models import UniversalTarget
from app.models.job_models import JobExecution

def test_direct_execution():
    """Test direct execution path"""
    print("=== TESTING DIRECT EXECUTION ===")
    
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
        
        # Test the communication method access that's failing
        comm_method = None
        if hasattr(target, 'communication_methods') and target.communication_methods:
            for method in target.communication_methods:
                if method.is_active:
                    comm_method = method
                    break
        
        if not comm_method:
            print("No communication method found")
            return
            
        print(f"Communication method: {comm_method.method_type}")
        print(f"Config type: {type(comm_method.config)}")
        print(f"Config content: {comm_method.config}")
        
        # This is where the error occurs - test the exact line
        try:
            port = comm_method.config.get('port', 22)
            print(f"Port access successful: {port}")
        except Exception as e:
            print(f"ERROR accessing config.get(): {e}")
            print(f"Error type: {type(e)}")
            
        # Test if config is None
        if comm_method.config is None:
            print("Config is None!")
        elif not hasattr(comm_method.config, 'get'):
            print(f"Config doesn't have 'get' method. Type: {type(comm_method.config)}")
            print(f"Config value: {comm_method.config}")
            
    except Exception as e:
        print(f"Direct execution test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_direct_execution()