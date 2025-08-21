"""
Celery tasks for job execution
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.job_service import JobService
from app.services.execution_service import JobExecutionService
from app.services.external_services import notification_service, audit_service
from app.models.job_models import JobExecution, JobStatus, ExecutionStatus

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
    
    try:
        logger.info(f"📊 Database session created for execution {execution_id}")
        
        # Get execution record
        execution = db.query(JobExecution).filter(
            JobExecution.id == execution_id
        ).first()
        
        if not execution:
            logger.error(f"❌ ERROR: Execution {execution_id} not found")
            return {"status": "failed", "error": "Execution not found"}
        
        logger.info(f"✅ Found execution {execution_id} for job {execution.job_id}")
        
        if not target_ids:
            logger.error(f"❌ ERROR: No targets specified for execution {execution_id}")
            execution.status = ExecutionStatus.FAILED
            execution.error_message = "No targets specified"
            execution.completed_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "failed", "error": "No targets specified"}
        
        logger.info(f"⚡ Starting job execution on {len(target_ids)} targets...")
        
        # Execute job on targets using asyncio.run
        execution_service = JobExecutionService(db)
        result = asyncio.run(execution_service.execute_job_on_targets(execution, target_ids))
        
        logger.info(f"✅ Job execution completed: {result}")
        
        # Update job status based on execution results
        job = execution.job
        if result.get('failed_targets', 0) > 0:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.COMPLETED
        
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        
        # Send completion notification
        try:
            await notification_service.send_job_notification(
                user_id=execution.triggered_by_user or job.created_by,
                job_id=job.id,
                job_name=job.name,
                event_type="completed" if job.status == JobStatus.COMPLETED else "failed",
                details={
                    "execution_id": execution.id,
                    "total_targets": result.get('total_targets', 0),
                    "successful_targets": result.get('successful_targets', 0),
                    "failed_targets": result.get('failed_targets', 0),
                    "execution_time": result.get('execution_time', 0)
                }
            )
        except Exception as e:
            logger.error(f"Failed to send completion notification: {e}")
        
        # Log audit event
        try:
            await audit_service.log_job_event(
                user_id=execution.triggered_by_user or job.created_by,
                event_type="JOB_EXECUTION_COMPLETED",
                resource_id=str(job.id),
                action="execute",
                details={
                    "execution_id": execution.id,
                    "status": job.status.value,
                    "total_targets": result.get('total_targets', 0),
                    "successful_targets": result.get('successful_targets', 0),
                    "failed_targets": result.get('failed_targets', 0)
                }
            )
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
        
        logger.info(f"🔚 Celery task completed for execution {execution_id}")
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"❌ ERROR in Celery task execution {execution_id}: {str(e)}")
        
        try:
            # Update execution status to failed
            execution = db.query(JobExecution).filter(
                JobExecution.id == execution_id
            ).first()
            
            if execution:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)
                execution.completed_at = datetime.now(timezone.utc)
                
                # Update job status to failed
                job = execution.job
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                
                db.commit()
                
                # Send failure notification
                try:
                    await notification_service.send_job_notification(
                        user_id=execution.triggered_by_user or job.created_by,
                        job_id=job.id,
                        job_name=job.name,
                        event_type="failed",
                        details={"error": str(e)}
                    )
                except Exception as notify_error:
                    logger.error(f"Failed to send failure notification: {notify_error}")
                
        except Exception as inner_e:
            logger.error(f"❌ Failed to mark execution as failed: {str(inner_e)}")
        
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.job_tasks.cancel_job_execution")
def cancel_job_execution(self, execution_id: int):
    """
    Celery task to cancel a running job execution
    """
    logger.info(f"🛑 Cancelling execution {execution_id}")
    
    db = SessionLocal()
    
    try:
        execution = db.query(JobExecution).filter(
            JobExecution.id == execution_id
        ).first()
        
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return {"status": "failed", "error": "Execution not found"}
        
        if execution.status != ExecutionStatus.RUNNING:
            logger.warning(f"Execution {execution_id} is not running (status: {execution.status})")
            return {"status": "failed", "error": "Execution is not running"}
        
        # Update execution status
        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = datetime.now(timezone.utc)
        
        # Update job status
        job = execution.job
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        
        db.commit()
        
        logger.info(f"✅ Cancelled execution {execution_id}")
        return {"status": "success", "execution_id": execution_id}
        
    except Exception as e:
        logger.error(f"Failed to cancel execution {execution_id}: {e}")
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.job_tasks.retry_failed_execution")
def retry_failed_execution(self, execution_id: int, target_ids: List[int] = None):
    """
    Celery task to retry a failed job execution
    """
    logger.info(f"🔄 Retrying execution {execution_id}")
    
    db = SessionLocal()
    
    try:
        execution = db.query(JobExecution).filter(
            JobExecution.id == execution_id
        ).first()
        
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return {"status": "failed", "error": "Execution not found"}
        
        if execution.status != ExecutionStatus.FAILED:
            logger.warning(f"Execution {execution_id} is not failed (status: {execution.status})")
            return {"status": "failed", "error": "Execution is not failed"}
        
        # Get failed targets if not specified
        if not target_ids:
            from app.models.job_models import JobExecutionResult
            failed_results = db.query(JobExecutionResult).filter(
                JobExecutionResult.execution_id == execution_id,
                JobExecutionResult.status == ExecutionStatus.FAILED
            ).all()
            target_ids = list(set(result.target_id for result in failed_results))
        
        if not target_ids:
            logger.warning(f"No failed targets found for execution {execution_id}")
            return {"status": "failed", "error": "No failed targets to retry"}
        
        # Create new execution for retry
        job_service = JobService(db)
        from app.schemas.job_schemas import JobExecuteRequest
        
        execute_data = JobExecuteRequest(
            target_ids=target_ids,
            execution_context={"retry_of": execution_id}
        )
        
        new_execution = await job_service.execute_job(
            execution.job_id,
            execute_data,
            execution.triggered_by_user or execution.job.created_by
        )
        
        logger.info(f"✅ Created retry execution {new_execution.id} for {len(target_ids)} failed targets")
        return {
            "status": "success", 
            "original_execution_id": execution_id,
            "retry_execution_id": new_execution.id,
            "retry_target_count": len(target_ids)
        }
        
    except Exception as e:
        logger.error(f"Failed to retry execution {execution_id}: {e}")
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()