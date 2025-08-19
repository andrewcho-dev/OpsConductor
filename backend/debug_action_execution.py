#!/usr/bin/env python3
"""
Debug action execution to find the exact error location
"""

import sys
sys.path.append('/app')

from app.database.database import SessionLocal
from app.models.job_models import Job, JobExecution
from app.models.universal_target_models import UniversalTarget
from app.services.job_execution_service import JobExecutionService
from app.services.job_service import JobService
from app.services.notification_service import NotificationService
import asyncio

async def debug_action_execution():
    db = SessionLocal()
    
    try:
        # Get the latest job
        job = db.query(Job).order_by(Job.id.desc()).first()
        execution = db.query(JobExecution).filter(JobExecution.job_id == job.id).order_by(JobExecution.id.desc()).first()
        
        print(f"🔍 Debugging job {job.id}, execution {execution.id}")
        
        # Get targets and actions
        targets = []
        for jt in job.targets:
            target = db.query(UniversalTarget).filter(UniversalTarget.id == jt.target_id).first()
            targets.append(target)
        
        target = targets[0]
        action = job.actions[0]
        comm_method = target.communication_methods[0]
        
        print(f"🎯 Target: {target.name}")
        print(f"🔧 Action: {action.action_name}")
        print(f"📡 Method: {comm_method.method_type}")
        print(f"📡 Config: {comm_method.config}")
        
        # Create services
        job_service = JobService(db)
        execution_service = JobExecutionService(job_service)
        
        # Try to execute the action directly
        try:
            result = await execution_service._execute_action(execution, target, action, comm_method)
            print(f"✅ Action result: {result}")
        except Exception as e:
            print(f"❌ Action execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_action_execution())