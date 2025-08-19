#!/usr/bin/env python3
"""
Test direct execution without Celery to isolate the method_config error
"""

import sys
sys.path.append('/app')

from app.database.database import SessionLocal
from app.models.job_models import Job, JobExecution, JobExecutionResult, ExecutionStatus
from app.models.universal_target_models import UniversalTarget
from app.services.job_execution_service import JobExecutionService
from app.services.job_service import JobService
import asyncio
import traceback

async def test_direct_execution():
    db = SessionLocal()
    
    try:
        # Get Windows target (ID 6)
        target = db.query(UniversalTarget).filter(UniversalTarget.id == 6).first()
        print(f"🎯 Target: {target.name}")
        
        # Get the latest job
        job = db.query(Job).order_by(Job.id.desc()).first()
        print(f"📋 Job: {job.name} (ID: {job.id})")
        
        # Get existing execution
        job_service = JobService(db)
        execution = db.query(JobExecution).filter(JobExecution.job_id == job.id).order_by(JobExecution.id.desc()).first()
        print(f"🔄 Using execution: {execution.id}")
        
        # Create execution service
        execution_service = JobExecutionService(job_service)
        
        # Execute directly without Celery
        print(f"🚀 Starting direct execution...")
        result = await execution_service.execute_job_on_targets(execution, [target])
        print(f"✅ Direct execution result: {result}")
        
        # Check the results
        results = db.query(JobExecutionResult).filter(
            JobExecutionResult.execution_id == execution.id
        ).all()
        
        print(f"📊 Results: {len(results)}")
        for result in results:
            print(f"   Target: {result.target_name}")
            print(f"   Status: {result.status}")
            print(f"   Error: {result.error_text or 'No error'}")
            print(f"   Output: {result.output_text or 'No output'}")
        
    except Exception as e:
        print(f"❌ Direct execution failed: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_direct_execution())