from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

from app.models.job_models import (
    Job, JobAction, JobExecution, JobExecutionResult,
    JobStatus, ExecutionStatus, ActionType
)
from app.schemas.job_schemas import (
    JobCreate, JobSchedule, JobExecuteRequest
)
from app.models.universal_target_models import UniversalTarget
from app.services.notification_service import NotificationService
from app.models.job_models import JobTarget

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def create_job(self, job_data: JobCreate, created_by: int) -> Job:
        """Create a new job with actions and target associations - SIMPLIFIED"""
        try:
            # Create the main job - NO SERIALIZATION
            job = Job(
                name=job_data.name,
                description=job_data.description,
                job_type=job_data.job_type,
                status=JobStatus.DRAFT if not job_data.scheduled_at else JobStatus.SCHEDULED,
                created_by=created_by,
                scheduled_at=job_data.scheduled_at
            )
            self.db.add(job)
            self.db.flush()  # Get the job ID

            # Create job actions
            for i, action_data in enumerate(job_data.actions, 1):
                action = JobAction(
                    job_id=job.id,
                    action_order=i,
                    action_type=action_data.action_type,
                    action_name=action_data.action_name,
                    action_parameters=action_data.action_parameters,
                    action_config=action_data.action_config
                )
                self.db.add(action)

            # Create target associations
            for target_id in job_data.target_ids:
                job_target = JobTarget(
                    job_id=job.id,
                    target_id=target_id
                )
                self.db.add(job_target)

            self.db.commit()
            logger.info(f"✅ Created job '{job.name}' (ID: {job.id}) with {len(job_data.actions)} actions and {len(job_data.target_ids)} targets")
            return job

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to create job: {str(e)}")
            raise

    def execute_job(self, job_id: int, execute_data: JobExecuteRequest) -> JobExecution:
        """Execute a job - SIMPLIFIED"""
        try:
            job = self.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Get target IDs
            if execute_data.target_ids:
                target_ids = execute_data.target_ids
            else:
                # Use all job targets
                target_ids = [jt.target_id for jt in job.targets]

            if not target_ids:
                raise ValueError("No targets specified for execution")

            # Get next execution number for this job
            max_execution = self.db.query(func.max(JobExecution.execution_number)).filter(
                JobExecution.job_id == job_id
            ).scalar() or 0
            execution_number = max_execution + 1

            # Create execution record - SIMPLE
            execution = JobExecution(
                job_id=job_id,
                execution_number=execution_number,
                status=ExecutionStatus.SCHEDULED,
                total_targets=len(target_ids),
                scheduled_at=datetime.now(timezone.utc)
            )
            self.db.add(execution)
            self.db.flush()

            logger.info(f"✅ Created execution {execution_number} for job {job_id} with {len(target_ids)} targets")

            # Send notification
            self.notification_service.send_job_notification(
                job_id=job_id,
                execution_id=execution.id,
                notification_type="started",
                message=f"Job '{job.name}' execution {execution_number} started",
                details={
                    "job_name": job.name,
                    "execution_number": execution_number,
                    "target_count": len(target_ids)
                }
            )

            self.db.commit()
            return execution

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to execute job {job_id}: {str(e)}")
            raise

    def get_job(self, job_id: int) -> Optional[Job]:
        """Get job by ID with relationships loaded"""
        from sqlalchemy.orm import joinedload
        from app.models.job_models import JobTarget
        return self.db.query(Job).options(
            joinedload(Job.actions),
            joinedload(Job.targets).joinedload(JobTarget.target),
            joinedload(Job.executions)
        ).filter(Job.id == job_id, Job.is_deleted == False).first()

    def get_job_execution(self, execution_id: int) -> Optional[JobExecution]:
        """Get job execution by ID"""
        return self.db.query(JobExecution).filter(JobExecution.id == execution_id).first()

    def get_execution_results(self, execution_id: int, target_id: Optional[int] = None) -> List[JobExecutionResult]:
        """Get execution results - optionally filtered by target"""
        query = self.db.query(JobExecutionResult).filter(JobExecutionResult.execution_id == execution_id)
        
        if target_id:
            query = query.filter(JobExecutionResult.target_id == target_id)
            
        return query.order_by(JobExecutionResult.action_order).all()

    def get_target_results(self, target_id: int, limit: int = 100) -> List[JobExecutionResult]:
        """Get all results for a specific target"""
        return self.db.query(JobExecutionResult).filter(
            JobExecutionResult.target_id == target_id
        ).order_by(JobExecutionResult.created_at.desc()).limit(limit).all()

    def update_execution_status(self, execution_id: int, status: ExecutionStatus):
        """Update execution status"""
        execution = self.get_job_execution(execution_id)
        if execution:
            execution.status = status
            if status == ExecutionStatus.RUNNING and not execution.started_at:
                execution.started_at = datetime.now(timezone.utc)
            elif status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED] and not execution.completed_at:
                execution.completed_at = datetime.now(timezone.utc)
            self.db.commit()

    def create_execution_result(
        self, 
        execution_id: int, 
        target_id: int, 
        target_name: str,
        action_id: int,
        action_order: int,
        action_name: str,
        action_type: ActionType,
        status: ExecutionStatus,
        output_text: Optional[str] = None,
        error_text: Optional[str] = None,
        exit_code: Optional[int] = None,
        command_executed: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> JobExecutionResult:
        """Create a result record - SIMPLE"""
        result = JobExecutionResult(
            execution_id=execution_id,
            target_id=target_id,
            target_name=target_name,
            action_id=action_id,
            action_order=action_order,
            action_name=action_name,
            action_type=action_type,
            status=status,
            output_text=output_text,
            error_text=error_text,
            exit_code=exit_code,
            command_executed=command_executed,
            execution_time_ms=execution_time_ms,
            started_at=datetime.now(timezone.utc) if status == ExecutionStatus.RUNNING else None,
            completed_at=datetime.now(timezone.utc) if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED] else None
        )
        self.db.add(result)
        self.db.commit()
        return result

    def update_execution_summary(self, execution_id: int):
        """Update execution summary counts"""
        execution = self.get_job_execution(execution_id)
        if not execution:
            return

        # Count results by status
        results = self.db.query(JobExecutionResult).filter(
            JobExecutionResult.execution_id == execution_id
        ).all()

        successful = len([r for r in results if r.status == ExecutionStatus.COMPLETED])
        failed = len([r for r in results if r.status == ExecutionStatus.FAILED])
        
        execution.successful_targets = successful
        execution.failed_targets = failed
        
        # Update overall execution status
        if failed > 0:
            execution.status = ExecutionStatus.FAILED
        elif successful == execution.total_targets:
            execution.status = ExecutionStatus.COMPLETED
        else:
            execution.status = ExecutionStatus.RUNNING

        self.db.commit()

    def list_jobs(self, skip: int = 0, limit: int = 100) -> List[Job]:
        """List jobs"""
        return self.db.query(Job).filter(Job.is_deleted == False).offset(skip).limit(limit).all()

    def delete_job(self, job_id: int) -> bool:
        """Soft delete a job"""
        job = self.get_job(job_id)
        if job:
            job.is_deleted = True
            job.deleted_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False