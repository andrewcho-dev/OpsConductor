#!/usr/bin/env python3
"""
Debug job execution to find the exact error location
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

async def debug_execution():
    db = SessionLocal()
    
    try:
        # Get the latest job
        job = db.query(Job).order_by(Job.id.desc()).first()
        execution = db.query(JobExecution).filter(JobExecution.job_id == job.id).order_by(JobExecution.id.desc()).first()
        
        print(f"🔍 Debugging job {job.id}, execution {execution.id}")
        
        # Get targets
        targets = []
        for jt in job.targets:
            target = db.query(UniversalTarget).filter(UniversalTarget.id == jt.target_id).first()
            targets.append(target)
        
        print(f"🎯 Target: {targets[0].name}")
        print(f"🔧 Communication methods: {len(targets[0].communication_methods)}")
        
        comm_method = targets[0].communication_methods[0]
        print(f"📡 Method type: {comm_method.method_type}")
        print(f"📡 Method attributes: {[attr for attr in dir(comm_method) if not attr.startswith('_')]}")
        print(f"📡 Has config: {hasattr(comm_method, 'config')}")
        print(f"📡 Config: {comm_method.config}")
        
        # Try to create the execution service
        job_service = JobService(db)
        notification_service = NotificationService(db)
        execution_service = JobExecutionService(job_service)
        
        print("✅ Services created successfully")
        
        # Try to execute on the target
        try:
            result = await execution_service._execute_on_target(execution, targets[0])
            print(f"✅ Execution result: {result}")
        except Exception as e:
            print(f"❌ Execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_execution())