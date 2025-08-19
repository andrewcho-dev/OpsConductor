#!/usr/bin/env python3
"""
Debug the full stack trace to find where method_config error comes from
"""

import sys
sys.path.append('/app')

from app.database.database import SessionLocal
from app.models.job_models import Job, JobExecution
from app.models.universal_target_models import UniversalTarget
from app.services.job_execution_service import JobExecutionService
from app.services.job_service import JobService
import asyncio
import traceback

async def debug_full_stack():
    db = SessionLocal()
    
    try:
        # Get the Windows job (ID 10)
        job = db.query(Job).filter(Job.id == 10).first()
        execution = db.query(JobExecution).filter(JobExecution.job_id == job.id).order_by(JobExecution.id.desc()).first()
        
        # Get Windows target (ID 6)
        target = db.query(UniversalTarget).filter(UniversalTarget.id == 6).first()
        action = job.actions[0]
        comm_method = target.communication_methods[0]
        
        print(f"🔍 Debugging Windows job execution...")
        print(f"   Target: {target.name}")
        print(f"   Method: {comm_method.method_type}")
        print(f"   Config: {comm_method.config}")
        
        # Create services
        job_service = JobService(db)
        execution_service = JobExecutionService(job_service)
        
        # Try to execute the action with full stack trace
        try:
            print(f"\\n🚀 Attempting to execute action...")
            result = await execution_service._execute_action(execution, target, action, comm_method)
            print(f"✅ Action result: {result}")
        except Exception as e:
            print(f"❌ Action execution failed: {str(e)}")
            print(f"\\n📋 FULL STACK TRACE:")
            traceback.print_exc()
            
            # Let's also try to see what line is causing the issue
            import inspect
            frame = inspect.currentframe()
            try:
                while frame:
                    filename = frame.f_code.co_filename
                    lineno = frame.f_lineno
                    function = frame.f_code.co_name
                    if 'method_config' in str(frame.f_locals):
                        print(f"\\n🎯 Found method_config reference:")
                        print(f"   File: {filename}:{lineno}")
                        print(f"   Function: {function}")
                        print(f"   Locals: {frame.f_locals}")
                    frame = frame.f_back
            finally:
                del frame
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_full_stack())