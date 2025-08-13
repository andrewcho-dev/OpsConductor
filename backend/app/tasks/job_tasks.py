"""
Celery tasks for job execution
"""

import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import List

from app.core.celery_app import celery_app
from app.database.database import SessionLocal
from app.services.job_service import JobService
from app.services.job_execution_service import JobExecutionService
from app.services.celery_monitoring_service import CeleryMonitoringService
from app.models.universal_target_models import UniversalTarget
from app.models.job_models import Job, JobStatus, ExecutionStatus
from app.schemas.job_schemas import JobExecuteRequest

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.job_tasks.execute_job_task")
def execute_job_task(self, execution_id: int, target_ids: List[int]):
    """
    Celery task to execute a job on targets
    """
    task_start_time = datetime.now(timezone.utc)
    logger.info(f"🚀 CELERY TASK STARTED: execution_id={execution_id}, target_ids={target_ids}")
    
    # Create new database session for task
    db = SessionLocal()
    monitoring_service = CeleryMonitoringService(db)
    
    try:
        logger.info(f"📊 Database session created for execution {execution_id}")
        job_service = JobService(db)
        execution = job_service.get_job_execution(execution_id)
        
        if not execution:
            logger.error(f"❌ ERROR: Execution {execution_id} not found")
            return {"status": "failed", "error": "Execution not found"}
        
        logger.info(f"✅ Found execution {execution_id} for job {execution.job_id}")
        
        # Get targets
        targets = db.query(UniversalTarget).filter(
            UniversalTarget.id.in_(target_ids)
        ).all()
        
        logger.info(f"🎯 Found {len(targets)} targets: {[t.name for t in targets]}")
        
        if not targets:
            logger.error(f"❌ ERROR: No targets found for execution {execution_id}")
            job_service.update_execution_status(
                execution_id,
                ExecutionStatus.FAILED
            )
            return {"status": "failed", "error": "No targets found"}
        
        logger.info(f"⚡ Starting job execution on {len(targets)} targets...")
        
        # Execute job on targets using asyncio.run
        execution_service = JobExecutionService(job_service)
        result = asyncio.run(execution_service.execute_job_on_targets(execution, targets))
        
        logger.info(f"✅ Job execution completed: {result}")
        
        # Record successful task completion
        task_end_time = datetime.now(timezone.utc)
        duration = (task_end_time - task_start_time).total_seconds()
        
        monitoring_service.record_task_completion(
            task_id=self.request.id,
            task_name=self.name,
            status='SUCCESS',
            started_at=task_start_time,
            completed_at=task_end_time,
            duration=duration,
            worker_name=self.request.hostname,
            queue_name='job_execution',
            result=json.dumps({"execution_id": execution_id, "targets_processed": len(target_ids)}),
            args=json.dumps([execution_id, target_ids])
        )
        
        # Return result for Celery
        return {
            "status": "completed",
            "execution_id": execution_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ ERROR in Celery task execution {execution_id}: {str(e)}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        # Record failed task completion
        task_end_time = datetime.now(timezone.utc)
        duration = (task_end_time - task_start_time).total_seconds()
        
        try:
            monitoring_service.record_task_completion(
                task_id=self.request.id,
                task_name=self.name,
                status='FAILURE',
                started_at=task_start_time,
                completed_at=task_end_time,
                duration=duration,
                worker_name=self.request.hostname,
                queue_name='job_execution',
                exception=str(e),
                traceback=error_traceback,
                args=json.dumps([execution_id, target_ids])
            )
        except Exception as monitor_e:
            logger.error(f"Failed to record task failure: {monitor_e}")
        
        # Mark execution as failed
        try:
            job_service.update_execution_status(
                execution_id,
                ExecutionStatus.FAILED
            )
        except Exception as inner_e:
            logger.error(f"❌ Failed to mark execution as failed: {str(inner_e)}")
        
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()
        logger.info(f"🔚 Celery task completed for execution {execution_id}")


@celery_app.task(bind=True, name="app.tasks.job_tasks.check_scheduled_jobs")
def check_scheduled_jobs(self):
    """
    Periodic task to check for scheduled jobs that are ready to execute
    """
    logger.info("🔍 Checking for scheduled jobs...")
    
    db = SessionLocal()
    try:
        current_time = datetime.now(timezone.utc)
        
        # Get jobs that are scheduled and past their scheduled time
        scheduled_jobs = db.query(Job).filter(
            Job.status == JobStatus.SCHEDULED,
            Job.scheduled_at <= current_time
        ).all()
        
        logger.info(f"📋 Found {len(scheduled_jobs)} scheduled jobs ready for execution")
        
        executed_count = 0
        for job in scheduled_jobs:
            try:
                logger.info(f"🚀 Executing scheduled job: {job.name} (ID: {job.id})")
                
                # Update job status to running
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now(timezone.utc)
                db.commit()
                
                # Create job execution
                job_service = JobService(db)
                
                # Execute the job using the job service
                execute_data = JobExecuteRequest(target_ids=None)  # Use all targets
                execution = job_service.execute_job(
                    job_id=job.id,
                    execute_data=execute_data
                )
                
                # Get target IDs for this job
                target_ids = job_service.get_job_target_ids(job.id)
                
                # Queue the job execution task
                task = execute_job_task.delay(execution.id, target_ids)
                logger.info(f"✅ Job {job.name} execution queued: execution_id={execution.id}, task_id={task.id}, targets={target_ids}")
                
                executed_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error executing scheduled job {job.id}: {str(e)}")
                
                # Update job status to failed
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        
        logger.info(f"✅ Scheduled job check completed: {executed_count} jobs executed")
        return {"status": "success", "jobs_executed": executed_count}
        
    except Exception as e:
        logger.error(f"❌ Error in scheduled job check: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.job_tasks.test_task")
def test_task(self, message: str):
    """
    Simple test task to verify Celery is working
    """
    logger.info(f"🧪 Test task received: {message}")
    return {"status": "success", "message": f"Test task completed: {message}"}
