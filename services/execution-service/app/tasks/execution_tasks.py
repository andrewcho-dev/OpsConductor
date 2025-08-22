"""
Execution Worker Tasks - Heavy Lifting Job Execution
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from celery import Task
from app.celery_app import app
from app.core.config import settings

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task class with error handling and callbacks"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed: {exc}")
        
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} completed successfully")


@app.task(bind=True, base=CallbackTask, queue='execution')
def execute_job_task(self, execution_id: int, job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a job on target systems - MAIN WORKHORSE TASK
    
    Args:
        execution_id: Unique execution identifier
        job_data: Job configuration and target information
        
    Returns:
        Dict with execution results
    """
    try:
        logger.info(f"Starting job execution {execution_id}")
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'step': 'initializing'})
        
        # Import here to avoid circular imports
        from app.services.execution_service import ExecutionService
        from app.database.database import get_db
        
        # Get database session
        db = next(get_db())
        
        try:
            # Initialize execution service
            execution_service = ExecutionService(db)
            
            # Execute the job
            self.update_state(state='PROGRESS', meta={'step': 'executing'})
            result = asyncio.run(
                execution_service.execute_job(execution_id, job_data)
            )
            
            self.update_state(state='PROGRESS', meta={'step': 'completing'})
            
            return {
                'status': 'success',
                'execution_id': execution_id,
                'result': result,
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Job execution {execution_id} failed: {exc}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'execution_id': execution_id}
        )
        raise exc


@app.task(bind=True, base=CallbackTask, queue='execution')
def execute_single_target_task(self, target_id: int, commands: List[str], job_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute commands on a single target system
    
    Args:
        target_id: Target system identifier
        commands: List of commands to execute
        job_config: Job configuration settings
        
    Returns:
        Dict with execution results for this target
    """
    try:
        logger.info(f"Executing commands on target {target_id}")
        
        self.update_state(state='PROGRESS', meta={'target_id': target_id, 'step': 'connecting'})
        
        from app.services.execution_service import ExecutionService
        from app.database.database import get_db
        
        db = next(get_db())
        
        try:
            execution_service = ExecutionService(db)
            
            self.update_state(state='PROGRESS', meta={'target_id': target_id, 'step': 'executing'})
            
            result = asyncio.run(
                execution_service.execute_on_target(target_id, commands, job_config)
            )
            
            return {
                'status': 'success',
                'target_id': target_id,
                'result': result,
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Target execution {target_id} failed: {exc}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'target_id': target_id}
        )
        raise exc


@app.task(bind=True, queue='execution')
def retry_failed_execution(self, execution_id: int) -> Dict[str, Any]:
    """
    Retry a failed job execution
    
    Args:
        execution_id: Failed execution to retry
        
    Returns:
        Dict with retry results
    """
    try:
        logger.info(f"Retrying failed execution {execution_id}")
        
        from app.services.execution_service import ExecutionService
        from app.database.database import get_db
        
        db = next(get_db())
        
        try:
            execution_service = ExecutionService(db)
            result = asyncio.run(execution_service.retry_execution(execution_id))
            
            return {
                'status': 'success',
                'execution_id': execution_id,
                'retry_result': result,
                'retried_at': datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Retry execution {execution_id} failed: {exc}")
        raise exc


@app.task(bind=True, queue='execution')
def check_execution_timeouts(self) -> Dict[str, Any]:
    """
    Check for and handle execution timeouts
    
    Returns:
        Dict with timeout check results
    """
    try:
        logger.info("Checking for execution timeouts")
        
        from app.services.execution_service import ExecutionService
        from app.database.database import get_db
        
        db = next(get_db())
        
        try:
            execution_service = ExecutionService(db)
            result = asyncio.run(execution_service.check_timeouts())
            
            return {
                'status': 'success',
                'timeouts_handled': result.get('timeouts_handled', 0),
                'checked_at': datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Timeout check failed: {exc}")
        raise exc


@app.task(bind=True, queue='execution')
def upload_execution_artifacts(self, execution_id: int, artifacts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upload execution artifacts to object storage
    
    Args:
        execution_id: Execution identifier
        artifacts: Artifacts to upload (logs, files, etc.)
        
    Returns:
        Dict with upload results
    """
    try:
        logger.info(f"Uploading artifacts for execution {execution_id}")
        
        from app.utils.object_storage_client import ObjectStorageClient
        
        storage_client = ObjectStorageClient()
        
        upload_results = []
        for artifact_name, artifact_data in artifacts.items():
            result = storage_client.upload_artifact(
                execution_id, artifact_name, artifact_data
            )
            upload_results.append(result)
        
        return {
            'status': 'success',
            'execution_id': execution_id,
            'uploads': upload_results,
            'uploaded_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Artifact upload for execution {execution_id} failed: {exc}")
        raise exc