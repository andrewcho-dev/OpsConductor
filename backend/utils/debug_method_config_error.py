#!/usr/bin/env python3
"""
Debug the method_config error by tracing the exact call stack
"""

import sys
sys.path.append('/app')

from app.database.database import SessionLocal
from app.models.job_models import Job, JobExecution
from app.models.universal_target_models import UniversalTarget
from app.services.job_execution_service import JobExecutionService
from app.services.job_service import JobService
from app.utils.connection_test_utils import test_ssh_connection
from app.utils.target_utils import getTargetIpAddress
import asyncio
import traceback

async def debug_method_config():
    db = SessionLocal()
    
    try:
        # Get the latest job
        job = db.query(Job).order_by(Job.id.desc()).first()
        execution = db.query(JobExecution).filter(JobExecution.job_id == job.id).order_by(JobExecution.id.desc()).first()
        
        # Get target and action
        target = db.query(UniversalTarget).filter(UniversalTarget.id == 10).first()
        action = job.actions[0]
        comm_method = target.communication_methods[0]
        
        print(f"🔍 Testing components individually...")
        print(f"   Target: {target.name}")
        print(f"   Action: {action.action_name}")
        print(f"   Method: {comm_method.method_type}")
        print(f"   Config: {comm_method.config}")
        
        # Test getTargetIpAddress
        try:
            host = getTargetIpAddress(target)
            print(f"✅ getTargetIpAddress: {host}")
        except Exception as e:
            print(f"❌ getTargetIpAddress failed: {str(e)}")
            traceback.print_exc()
            return
        
        # Test port extraction
        try:
            port = comm_method.config.get('port', 22)
            print(f"✅ Port extraction: {port}")
        except Exception as e:
            print(f"❌ Port extraction failed: {str(e)}")
            traceback.print_exc()
            return
        
        # Test credential extraction
        try:
            job_service = JobService(db)
            execution_service = JobExecutionService(job_service)
            credentials = execution_service._get_credentials(comm_method)
            print(f"✅ Credentials: {credentials}")
        except Exception as e:
            print(f"❌ Credentials failed: {str(e)}")
            traceback.print_exc()
            return
        
        # Test SSH connection function directly
        try:
            result = test_ssh_connection(host, port, credentials, timeout=10)
            print(f"✅ SSH test result: {result}")
        except Exception as e:
            print(f"❌ SSH test failed: {str(e)}")
            traceback.print_exc()
            return
        
        # Test the full action execution
        try:
            result = await execution_service._execute_ssh_action(target, action, comm_method)
            print(f"✅ Full action result: {result}")
        except Exception as e:
            print(f"❌ Full action failed: {str(e)}")
            traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_method_config())