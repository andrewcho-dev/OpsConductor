from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

from app.models.job_models import (
    Job, JobAction, JobExecution, JobExecutionBranch, JobExecutionLog,
    JobActionResult, JobStatus, ExecutionStatus, LogPhase, LogLevel, LogCategory
)
from app.schemas.job_schemas import (
    JobCreate, JobSchedule, JobExecuteRequest
)
from app.models.universal_target_models import UniversalTarget
from app.services.notification_service import NotificationService
from app.services.serial_service import SerialService
from app.models.job_models import JobTarget

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def create_job(self, job_data: JobCreate, created_by: int) -> Job:
        """Create a new job with actions and target associations"""
        try:
            # Generate permanent identifiers
            job_serial = SerialService.generate_job_serial(self.db)
            
            # Create the main job
            job = Job(
                job_serial=job_serial,
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

            # Create job target associations
            for target_id in job_data.target_ids:
                job_target = JobTarget(
                    job_id=job.id,
                    target_id=target_id
                )
                self.db.add(job_target)

            # Log job creation
            self._log_job_event(
                job_id=job.id,
                phase=LogPhase.CREATION,
                level=LogLevel.INFO,
                category=LogCategory.SYSTEM,
                message=f"Job '{job.name}' created successfully",
                details={
                    "job_type": job.job_type.value,
                    "action_count": len(job_data.actions),
                    "target_count": len(job_data.target_ids)
                }
            )

            self.db.commit()
            logger.info(f"Job '{job.name}' created with ID {job.id}")
            return job

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create job: {str(e)}")
            raise

    def get_job(self, job_id: int) -> Optional[Job]:
        """Get a job by ID with all related data"""
        from sqlalchemy.orm import joinedload
        return self.db.query(Job).options(joinedload(Job.actions)).filter(Job.id == job_id).first()
    
    def get_job_by_uuid(self, job_uuid: str) -> Optional[Job]:
        """Get a job by UUID (permanent identifier)"""
        return self.db.query(Job).filter(Job.job_uuid == job_uuid).first()
    
    def get_job_by_serial(self, job_serial: str) -> Optional[Job]:
        """Get a job by serial number (human-readable permanent identifier)"""
        return self.db.query(Job).filter(Job.job_serial == job_serial).first()

    def get_jobs(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[JobStatus] = None,
        created_by: Optional[int] = None,
        sort_by: Optional[str] = "created_at",
        sort_order: Optional[str] = "desc"
    ) -> List[Job]:
        """Get jobs with optional filtering and sorting"""
        query = self.db.query(Job)
        
        # Always exclude soft-deleted jobs unless specifically requesting deleted jobs
        if status != JobStatus.DELETED:
            query = query.filter(Job.is_deleted.is_(False))
        
        if status:
            query = query.filter(Job.status == status)
        if created_by:
            query = query.filter(Job.created_by == created_by)
        
        # Add sorting
        if sort_by and hasattr(Job, sort_by):
            sort_column = getattr(Job, sort_by)
            if sort_order and sort_order.lower() == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            # Default sorting by created_at desc
            query = query.order_by(Job.created_at.desc())
            
        return query.offset(skip).limit(limit).all()

    def get_jobs_with_last_execution(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[JobStatus] = None,
        created_by: Optional[int] = None
    ) -> List[tuple]:
        """Get jobs with their last execution in a single query for performance"""
        from sqlalchemy import func
        from sqlalchemy.orm import aliased
        
        # Create subquery to get the latest execution for each job
        latest_execution_subq = self.db.query(
            JobExecution.job_id,
            func.max(JobExecution.execution_number).label('max_execution_number')
        ).group_by(JobExecution.job_id).subquery()
        
        # Alias for the latest execution
        latest_execution = aliased(JobExecution)
        
        # Main query joining jobs with their latest execution
        query = self.db.query(Job, latest_execution).outerjoin(
            latest_execution_subq,
            Job.id == latest_execution_subq.c.job_id
        ).outerjoin(
            latest_execution,
            (latest_execution.job_id == Job.id) & 
            (latest_execution.execution_number == latest_execution_subq.c.max_execution_number)
        )
        
        # Always exclude soft-deleted jobs unless specifically requesting deleted jobs
        if status != JobStatus.DELETED:
            query = query.filter(Job.is_deleted.is_(False))
        
        if status:
            query = query.filter(Job.status == status)
        if created_by:
            query = query.filter(Job.created_by == created_by)
            
        return query.offset(skip).limit(limit).all()

    def schedule_job(self, job_id: int, schedule_data: JobSchedule) -> Job:
        """Schedule a job for execution"""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Frontend sends UTC time directly - no conversion needed
        job.status = JobStatus.SCHEDULED
        job.scheduled_at = schedule_data.scheduled_at
        job.updated_at = datetime.now(timezone.utc)

        # Log scheduling - frontend sends UTC time directly
        self._log_job_event(
            job_id=job.id,
            phase=LogPhase.CREATION,
            level=LogLevel.INFO,
            category=LogCategory.SYSTEM,
            message=f"Job '{job.name}' scheduled for {schedule_data.scheduled_at} UTC",
            details={
                "scheduled_at_utc": schedule_data.scheduled_at.isoformat()
            }
        )

        self.db.commit()
        logger.info(f"Job '{job.name}' scheduled for {schedule_data.scheduled_at} UTC")
        return job

    def execute_job(self, job_id: int, execute_data: JobExecuteRequest) -> JobExecution:
        """Execute a job immediately"""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Get the next execution number
        last_execution = self.db.query(JobExecution).filter(
            JobExecution.job_id == job_id
        ).order_by(JobExecution.execution_number.desc()).first()
        
        execution_number = (last_execution.execution_number + 1) if last_execution else 1

        # Generate execution serial
        execution_serial = SerialService.generate_execution_serial(self.db, job.job_serial)
        
        # Create execution record
        execution = JobExecution(
            job_id=job_id,
            execution_serial=execution_serial,
            execution_number=execution_number,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(execution)
        self.db.flush()

        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)

        # Get targets to execute on
        target_ids = execute_data.target_ids if execute_data and execute_data.target_ids else []
        if not target_ids:
            # Get targets associated with this job
            target_ids = self.get_job_target_ids(job_id)

        # Create execution branches for each target
        for i, target_id in enumerate(target_ids, 1):
            # Get target for serial reference
            target = self.db.query(UniversalTarget).filter(UniversalTarget.id == target_id).first()
            target_serial_ref = target.target_serial if target else None
            
            # Generate branch serial using sequential index (no race conditions)
            branch_id = f"{i:03d}"  # 001, 002, 003, etc.
            branch_serial = f"{execution_serial}.{branch_id}"
            
            branch = JobExecutionBranch(
                job_execution_id=execution.id,
                target_id=target_id,
                branch_serial=branch_serial,
                branch_id=branch_id,
                target_serial_ref=target_serial_ref,
                status=ExecutionStatus.RUNNING,
                started_at=datetime.now(timezone.utc)
            )
            self.db.add(branch)

        # Log execution start
        self._log_job_event(
            job_id=job_id,
            execution_id=execution.id,
            phase=LogPhase.ACTION_EXECUTION,
            level=LogLevel.INFO,
            category=LogCategory.COMMAND_EXECUTION,
            message=f"Job execution {execution_number} started",
            details={
                "execution_number": execution_number,
                "target_count": len(target_ids),
                "target_ids": target_ids
            }
        )

        self.db.commit()
        logger.info(f"Job execution {execution_number} started for job {job_id}")

        # Send notification
        try:
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
        except Exception as e:
            logger.warning(f"Failed to send job notification: {str(e)}")

        return execution

    def update_job(self, job_id: int, job_data: JobCreate) -> Job:
        """Update an existing job"""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Update job fields
        job.name = job_data.name
        job.description = job_data.description
        job.job_type = job_data.job_type
        
        # Handle scheduled_at - frontend sends UTC directly
        if job_data.scheduled_at:
            job.scheduled_at = job_data.scheduled_at
            job.status = JobStatus.SCHEDULED
        else:
            job.scheduled_at = None
            job.status = JobStatus.DRAFT
            
        job.updated_at = datetime.now(timezone.utc)

        # Delete existing actions and recreate them
        # First, delete any action results that reference these actions
        from app.models.job_models import JobActionResult, JobExecutionBranch, JobExecution
        
        # Get all action IDs for this job
        action_ids = self.db.query(JobAction.id).filter(JobAction.job_id == job_id).all()
        action_ids = [aid[0] for aid in action_ids]
        
        if action_ids:
            # Delete action results that reference these actions
            self.db.query(JobActionResult).filter(JobActionResult.action_id.in_(action_ids)).delete(synchronize_session=False)
        
        # Now delete the actions
        self.db.query(JobAction).filter(JobAction.job_id == job_id).delete()

        # Create new actions
        for i, action_data in enumerate(job_data.actions, 1):
            action = JobAction(
                job_id=job_id,
                action_order=i,
                action_type=action_data.action_type,
                action_name=action_data.action_name,
                action_parameters=action_data.action_parameters,
                action_config=action_data.action_config
            )
            self.db.add(action)

        # Update job target associations
        # Delete existing target associations
        self.db.query(JobTarget).filter(JobTarget.job_id == job_id).delete()
        
        # Create new target associations
        for target_id in job_data.target_ids:
            job_target = JobTarget(
                job_id=job_id,
                target_id=target_id
            )
            self.db.add(job_target)

        self.db.commit()
        logger.info(f"Job '{job.name}' updated")
        return job

    def delete_job(self, job_id: int, soft_delete: bool = False) -> bool:
        """Delete a job and all its associated data"""
        job = self.get_job(job_id)
        if not job:
            return False

        try:
            if soft_delete:
                # Soft delete - mark as deleted with proper fields
                job.status = JobStatus.DELETED
                job.is_deleted = True
                job.deleted_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                logger.info(f"Job '{job.name}' soft deleted")
                return True
            
            # Hard delete - remove all associated data
            # Get all execution IDs for this job
            execution_ids = [ex.id for ex in self.db.query(JobExecution.id).filter(JobExecution.job_id == job_id).all()]
            
            if execution_ids:
                # Get all branch IDs for these executions
                branch_ids = [br.id for br in self.db.query(JobExecutionBranch.id).filter(
                    JobExecutionBranch.job_execution_id.in_(execution_ids)
                ).all()]
                
                if branch_ids:
                    # Delete job action results that reference branches
                    self.db.query(JobActionResult).filter(
                        JobActionResult.branch_id.in_(branch_ids)
                    ).delete()
                
                # Delete job execution logs
                self.db.query(JobExecutionLog).filter(
                    JobExecutionLog.job_execution_id.in_(execution_ids)
                ).delete()
                
                # Delete job execution branches
                self.db.query(JobExecutionBranch).filter(
                    JobExecutionBranch.job_execution_id.in_(execution_ids)
                ).delete()
                
                # Delete job executions
                self.db.query(JobExecution).filter(JobExecution.job_id == job_id).delete()
            
            # Delete job actions
            self.db.query(JobAction).filter(JobAction.job_id == job_id).delete()
            
            # Delete job target associations
            self.db.query(JobTarget).filter(JobTarget.job_id == job_id).delete()
            
            # Delete the job itself
            self.db.delete(job)
            
            self.db.commit()
            logger.info(f"Job '{job.name}' deleted")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete job {job_id}: {str(e)}")
            return False

    def get_job_target_ids(self, job_id: int) -> List[int]:
        """Get target IDs associated with a job"""
        # Get targets associated with this job
        job_targets = self.db.query(JobTarget).filter(
            JobTarget.job_id == job_id
        ).all()
        
        if job_targets:
            # Return the stored target associations
            return [target.target_id for target in job_targets]
        else:
            # Fallback to all active targets for backward compatibility
            # This handles existing jobs that were created before the job_targets table
            from app.models.universal_target_models import UniversalTarget
            targets = self.db.query(UniversalTarget).filter(
                UniversalTarget.is_active.is_(True)
            ).all()
            return [target.id for target in targets]

    def get_job_targets(self, job_id: int) -> List[Dict[str, Any]]:
        """Get full target information associated with a job"""
        from app.models.universal_target_models import UniversalTarget
        
        # Get targets associated with this job
        job_targets = self.db.query(JobTarget).filter(
            JobTarget.job_id == job_id
        ).all()
        
        if job_targets:
            # Get full target information
            target_ids = [target.target_id for target in job_targets]
            targets = self.db.query(UniversalTarget).filter(
                UniversalTarget.id.in_(target_ids)
            ).all()
        else:
            # Fallback to all active targets for backward compatibility
            targets = self.db.query(UniversalTarget).filter(
                UniversalTarget.is_active.is_(True)
            ).all()
        
        # Convert to dictionary format
        target_list = []
        for target in targets:
            target_dict = {
                "id": target.id,
                "target_uuid": str(target.target_uuid),
                "target_serial": target.target_serial,
                "name": target.name,
                "target_type": target.target_type,
                "description": target.description,
                "os_type": target.os_type,
                "environment": target.environment,
                "location": target.location,
                "data_center": target.data_center,
                "region": target.region,
                "is_active": target.is_active,
                "status": target.status,
                "health_status": target.health_status,
                "created_at": target.created_at.isoformat() if target.created_at else None,
                "updated_at": target.updated_at.isoformat() if target.updated_at else None
            }
            target_list.append(target_dict)
        
        return target_list

    def get_job_execution(self, execution_id: int) -> Optional[JobExecution]:
        """Get a job execution by ID with all branches"""
        return self.db.query(JobExecution).filter(
            JobExecution.id == execution_id
        ).first()

    def get_execution_by_serial(self, execution_serial: str) -> Optional[JobExecution]:
        """Get a job execution by serial number with all branches"""
        return self.db.query(JobExecution).filter(
            JobExecution.execution_serial == execution_serial
        ).first()

    def get_job_executions(self, job_id: int) -> List[JobExecution]:
        """Get all executions for a job"""
        return self.db.query(JobExecution).filter(
            JobExecution.job_id == job_id
        ).order_by(JobExecution.execution_number.desc()).all()

    def get_execution_action_results(self, execution_id: int) -> List:
        """Get individual action results for a job execution"""
        from app.models.job_models import JobActionResult
        
        return self.db.query(JobActionResult).join(
            JobExecutionBranch, JobActionResult.branch_id == JobExecutionBranch.id
        ).filter(
            JobExecutionBranch.job_execution_id == execution_id
        ).order_by(
            JobExecutionBranch.branch_id, JobActionResult.action_order
        ).all()

    def update_execution_status(
        self,
        execution_id: int,
        status: ExecutionStatus,
        completed_at: Optional[datetime] = None
    ) -> JobExecution:
        """Update execution status"""
        execution = self.get_job_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        execution.status = status
        if completed_at:
            execution.completed_at = completed_at

        # Update job status if all executions are complete
        if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            self._update_job_status_from_executions(execution.job_id)

        self.db.commit()
        return execution

    def update_branch_status(
        self,
        branch_id: int,
        status: ExecutionStatus,
        result_output: Optional[str] = None,
        result_error: Optional[str] = None,
        exit_code: Optional[int] = None,
        completed_at: Optional[datetime] = None
    ) -> JobExecutionBranch:
        """Update branch execution status and results"""
        branch = self.db.query(JobExecutionBranch).filter(
            JobExecutionBranch.id == branch_id
        ).first()
        
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")

        branch.status = status
        if result_output is not None:
            branch.result_output = result_output
        if result_error is not None:
            branch.result_error = result_error
        if exit_code is not None:
            branch.exit_code = exit_code
        if completed_at:
            branch.completed_at = completed_at

        # Log branch completion
        self._log_job_event(
            job_id=branch.execution.job_id,
            execution_id=branch.job_execution_id,
            branch_id=branch_id,
            phase=LogPhase.COMPLETION,
            level=LogLevel.INFO if status == ExecutionStatus.COMPLETED else LogLevel.ERROR,
            category=LogCategory.COMMAND_EXECUTION,
            message=f"Branch {branch.branch_id} {status.value}",
            details={
                "exit_code": exit_code,
                "has_output": bool(result_output),
                "has_error": bool(result_error)
            }
        )

        self.db.commit()
        return branch

    def _update_job_status_from_executions(self, job_id: int):
        """Update job status based on execution statuses"""
        job = self.get_job(job_id)
        if not job:
            return

        # Get the latest execution
        latest_execution = self.db.query(JobExecution).filter(
            JobExecution.job_id == job_id
        ).order_by(JobExecution.execution_number.desc()).first()

        if not latest_execution:
            return

        logger.info(f"🔍 Updating job {job_id} status based on latest execution {latest_execution.id} with status {latest_execution.status}")

        if latest_execution.status == ExecutionStatus.COMPLETED:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            logger.info(f"✅ Set job {job_id} status to COMPLETED")
        elif latest_execution.status == ExecutionStatus.FAILED:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            logger.info(f"❌ Set job {job_id} status to FAILED")
        elif latest_execution.status == ExecutionStatus.CANCELLED:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            logger.info(f"🚫 Set job {job_id} status to CANCELLED")

    def _log_job_event(
        self,
        job_id: int,
        execution_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        phase: LogPhase = LogPhase.CREATION,
        level: LogLevel = LogLevel.INFO,
        category: LogCategory = LogCategory.SYSTEM,
        message: str = "",
        details: Optional[Dict[str, Any]] = None
    ):
        """Log job-related events"""
        # Skip logging if no execution_id (job creation logs are handled by enhanced service layer)
        if execution_id is None:
            logger.info(f"Skipping job event log (no execution): {message}")
            return
            
        log = JobExecutionLog(
            job_execution_id=execution_id,
            branch_id=branch_id,
            log_phase=phase.value,
            log_level=level.value,
            log_category=category.value,
            log_message=message,
            log_details=details,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(log)
