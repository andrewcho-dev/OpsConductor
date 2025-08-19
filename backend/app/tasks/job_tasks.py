"""
Celery tasks for job execution - SIMPLIFIED
"""

import asyncio
import logging
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
    Celery task to execute a job on targets - SIMPLIFIED
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
            job_service.update_execution_status(execution_id, ExecutionStatus.FAILED)
            return {"status": "failed", "error": "No targets found"}
        
        logger.info(f"⚡ Starting job execution on {len(targets)} targets...")
        
        # Execute job on targets using asyncio.run
        execution_service = JobExecutionService(job_service)
        result = asyncio.run(execution_service.execute_job_on_targets(execution, targets))
        
        logger.info(f"✅ Job execution completed: {result}")
        
        # Record successful task completion
        task_end_time = datetime.now(timezone.utc)
        duration = (task_end_time - task_start_time).total_seconds()
        
        try:
            monitoring_service.record_task_completion(
                task_id=self.request.id,
                task_name=self.name,
                duration=duration,
                status="success"
            )
        except Exception as e:
            logger.error(f"Error recording task completion: {str(e)}")
        
        # Update job status based on execution results
        job = execution.job
        if result.get('failed_targets', 0) > 0:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.COMPLETED
        
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(f"🔚 Celery task completed for execution {execution_id}")
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"❌ ERROR in Celery task execution {execution_id}: {str(e)}")
        
        try:
            # Update execution status to failed
            job_service.update_execution_status(execution_id, ExecutionStatus.FAILED)
            
            # Update job status to failed
            execution = job_service.get_job_execution(execution_id)
            if execution:
                job = execution.job
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
                
        except Exception as inner_e:
            logger.error(f"❌ Failed to mark execution as failed: {str(inner_e)}")
        
        try:
            monitoring_service.record_task_failure(
                task_id=self.request.id,
                task_name=self.name,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to record task failure: {str(e)}")
        
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()
        logger.info(f"🔚 Celery task completed for execution {execution_id}")


@celery_app.task(bind=True, name="app.tasks.job_tasks.check_scheduled_jobs")
def check_scheduled_jobs(self):
    """
    Periodic task to check for scheduled jobs that are ready to execute - SIMPLIFIED
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
                target_ids = [jt.target_id for jt in job.targets]
                
                # Queue the execution task
                execute_job_task.delay(execution.id, target_ids)
                
                executed_count += 1
                logger.info(f"✅ Job {job.name} execution queued: execution_id={execution.id}, task_id={execute_job_task.request.id}, targets={target_ids}")
                
            except Exception as e:
                logger.error(f"❌ Failed to execute scheduled job {job.name}: {str(e)}")
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        
        logger.info(f"✅ Scheduled job check completed: {executed_count} jobs executed")
        return {"status": "success", "jobs_executed": executed_count}
        
    except Exception as e:
        logger.error(f"❌ Error in scheduled job check: {str(e)}")
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()