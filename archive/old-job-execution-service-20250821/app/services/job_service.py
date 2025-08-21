"""
Job Service
Core business logic for job management
"""

import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.models.job_models import (
    Job, JobAction, JobTarget, JobExecution, JobStatus, ExecutionStatus
)
from app.schemas.job_schemas import (
    JobCreate, JobUpdate, JobResponse, JobListResponse,
    JobExecuteRequest, JobExecutionResponse,
    JobActionResponse, JobTargetResponse
)
from app.services.external_services import target_service, notification_service, audit_service
from app.tasks.job_tasks import execute_job_task

logger = logging.getLogger(__name__)


class JobService:
    """Service for job management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_job(self, job_data: JobCreate, created_by: int) -> JobResponse:
        """Create a new job"""
        try:
            # Validate targets exist
            target_ids = job_data.target_ids
            targets = await target_service.get_targets(target_ids)
            
            if len(targets) != len(target_ids):
                found_ids = {t["id"] for t in targets}
                missing_ids = set(target_ids) - found_ids
                raise ValueError(f"Targets not found: {missing_ids}")
            
            # Create job
            job = Job(
                name=job_data.name,
                description=job_data.description,
                job_type=job_data.job_type,
                status=JobStatus.SCHEDULED if job_data.scheduled_at else JobStatus.DRAFT,
                created_by=created_by,
                scheduled_at=job_data.scheduled_at,
                priority=job_data.priority,
                timeout_seconds=job_data.timeout_seconds,
                max_retries=job_data.max_retries,
                tags=job_data.tags,
                metadata=job_data.metadata
            )
            
            self.db.add(job)
            self.db.flush()  # Get job ID
            
            # Create actions
            for i, action_data in enumerate(job_data.actions, 1):
                action = JobAction(
                    job_id=job.id,
                    action_order=i,
                    action_type=action_data.action_type,
                    action_name=action_data.action_name,
                    action_parameters=action_data.action_parameters,
                    action_config=action_data.action_config,
                    requires_confirmation=action_data.requires_confirmation
                )
                self.db.add(action)
            
            # Create target associations
            for target in targets:
                job_target = JobTarget(
                    job_id=job.id,
                    target_id=target["id"],
                    target_name=target.get("name"),
                    target_type=target.get("type")
                )
                self.db.add(job_target)
            
            self.db.commit()
            
            # Log audit event
            await audit_service.log_job_event(
                user_id=created_by,
                event_type="JOB_CREATED",
                resource_id=str(job.id),
                action="create",
                details={
                    "job_name": job.name,
                    "job_type": job.job_type.value,
                    "target_count": len(target_ids),
                    "action_count": len(job_data.actions)
                }
            )
            
            logger.info(f"Created job '{job.name}' (ID: {job.id}) with {len(job_data.actions)} actions and {len(target_ids)} targets")
            
            return await self.get_job(job.id, include_actions=True, include_targets=True)
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create job: {e}")
            raise
    
    async def get_job(
        self, 
        job_id: int, 
        include_actions: bool = False,
        include_targets: bool = False,
        include_execution_summary: bool = False
    ) -> Optional[JobResponse]:
        """Get job by ID with optional related data"""
        try:
            query = self.db.query(Job).filter(
                Job.id == job_id,
                Job.is_deleted == False
            )
            
            if include_actions:
                query = query.options(joinedload(Job.actions))
            if include_targets:
                query = query.options(joinedload(Job.targets))
            
            job = query.first()
            if not job:
                return None
            
            # Build response
            response_data = {
                "id": job.id,
                "uuid": job.uuid,
                "name": job.name,
                "description": job.description,
                "job_type": job.job_type,
                "status": job.status,
                "created_by": job.created_by,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "scheduled_at": job.scheduled_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "priority": job.priority,
                "timeout_seconds": job.timeout_seconds,
                "max_retries": job.max_retries,
                "tags": job.tags,
                "metadata": job.metadata
            }
            
            # Add actions if requested
            if include_actions and job.actions:
                response_data["actions"] = [
                    JobActionResponse(
                        id=action.id,
                        action_order=action.action_order,
                        action_type=action.action_type,
                        action_name=action.action_name,
                        action_parameters=action.action_parameters,
                        action_config=action.action_config,
                        is_dangerous=action.is_dangerous,
                        requires_confirmation=action.requires_confirmation
                    )
                    for action in sorted(job.actions, key=lambda a: a.action_order)
                ]
            
            # Add targets if requested
            if include_targets and job.targets:
                response_data["targets"] = [
                    JobTargetResponse(
                        id=target.id,
                        target_id=target.target_id,
                        target_name=target.target_name,
                        target_type=target.target_type
                    )
                    for target in job.targets
                ]
            
            # Add execution summary if requested
            if include_execution_summary:
                execution_summary = await self._get_execution_summary(job_id)
                response_data["execution_summary"] = execution_summary
            
            return JobResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            raise
    
    async def list_jobs(
        self,
        page: int = 1,
        size: int = 50,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        created_by: Optional[int] = None,
        search: Optional[str] = None
    ) -> JobListResponse:
        """List jobs with filtering and pagination"""
        try:
            query = self.db.query(Job).filter(Job.is_deleted == False)
            
            # Apply filters
            if status:
                query = query.filter(Job.status == status)
            if job_type:
                query = query.filter(Job.job_type == job_type)
            if created_by:
                query = query.filter(Job.created_by == created_by)
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Job.name.ilike(search_term),
                        Job.description.ilike(search_term)
                    )
                )
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            offset = (page - 1) * size
            jobs = query.order_by(desc(Job.created_at)).offset(offset).limit(size).all()
            
            # Convert to response format
            job_responses = []
            for job in jobs:
                execution_summary = await self._get_execution_summary(job.id)
                
                job_responses.append(JobResponse(
                    id=job.id,
                    uuid=job.uuid,
                    name=job.name,
                    description=job.description,
                    job_type=job.job_type,
                    status=job.status,
                    created_by=job.created_by,
                    created_at=job.created_at,
                    updated_at=job.updated_at,
                    scheduled_at=job.scheduled_at,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    priority=job.priority,
                    timeout_seconds=job.timeout_seconds,
                    max_retries=job.max_retries,
                    tags=job.tags,
                    metadata=job.metadata,
                    execution_summary=execution_summary
                ))
            
            return JobListResponse(
                jobs=job_responses,
                total=total,
                page=page,
                size=size,
                has_next=offset + size < total
            )
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            raise
    
    async def update_job(self, job_id: int, job_data: JobUpdate, updated_by: int) -> Optional[JobResponse]:
        """Update job"""
        try:
            job = self.db.query(Job).filter(
                Job.id == job_id,
                Job.is_deleted == False
            ).first()
            
            if not job:
                return None
            
            # Check if job can be updated
            if job.status in [JobStatus.RUNNING]:
                raise ValueError("Cannot update running job")
            
            # Update basic fields
            update_data = job_data.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                if field not in ["actions", "target_ids"]:
                    setattr(job, field, value)
            
            job.updated_at = datetime.now(timezone.utc)
            
            # Update actions if provided
            if job_data.actions is not None:
                # Remove existing actions
                self.db.query(JobAction).filter(JobAction.job_id == job_id).delete()
                
                # Add new actions
                for i, action_data in enumerate(job_data.actions, 1):
                    action = JobAction(
                        job_id=job.id,
                        action_order=i,
                        action_type=action_data.action_type,
                        action_name=action_data.action_name,
                        action_parameters=action_data.action_parameters,
                        action_config=action_data.action_config,
                        requires_confirmation=action_data.requires_confirmation
                    )
                    self.db.add(action)
            
            # Update targets if provided
            if job_data.target_ids is not None:
                # Validate targets exist
                targets = await target_service.get_targets(job_data.target_ids)
                if len(targets) != len(job_data.target_ids):
                    found_ids = {t["id"] for t in targets}
                    missing_ids = set(job_data.target_ids) - found_ids
                    raise ValueError(f"Targets not found: {missing_ids}")
                
                # Remove existing targets
                self.db.query(JobTarget).filter(JobTarget.job_id == job_id).delete()
                
                # Add new targets
                for target in targets:
                    job_target = JobTarget(
                        job_id=job.id,
                        target_id=target["id"],
                        target_name=target.get("name"),
                        target_type=target.get("type")
                    )
                    self.db.add(job_target)
            
            self.db.commit()
            
            # Log audit event
            await audit_service.log_job_event(
                user_id=updated_by,
                event_type="JOB_UPDATED",
                resource_id=str(job.id),
                action="update",
                details={"updated_fields": list(update_data.keys())}
            )
            
            logger.info(f"Updated job {job_id}")
            
            return await self.get_job(job_id, include_actions=True, include_targets=True)
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update job {job_id}: {e}")
            raise
    
    async def delete_job(self, job_id: int, deleted_by: int, force: bool = False) -> bool:
        """Delete job (soft delete by default)"""
        try:
            job = self.db.query(Job).filter(
                Job.id == job_id,
                Job.is_deleted == False
            ).first()
            
            if not job:
                return False
            
            # Check if job can be deleted
            if job.status == JobStatus.RUNNING and not force:
                raise ValueError("Cannot delete running job without force flag")
            
            if force:
                # Hard delete
                self.db.delete(job)
            else:
                # Soft delete
                job.is_deleted = True
                job.deleted_at = datetime.now(timezone.utc)
                job.status = JobStatus.DELETED
            
            self.db.commit()
            
            # Log audit event
            await audit_service.log_job_event(
                user_id=deleted_by,
                event_type="JOB_DELETED",
                resource_id=str(job.id),
                action="delete",
                details={"force": force}
            )
            
            logger.info(f"Deleted job {job_id} (force={force})")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete job {job_id}: {e}")
            raise
    
    async def execute_job(self, job_id: int, execute_data: JobExecuteRequest, executed_by: int) -> JobExecutionResponse:
        """Execute a job"""
        try:
            job = self.db.query(Job).filter(
                Job.id == job_id,
                Job.is_deleted == False
            ).first()
            
            if not job:
                raise ValueError("Job not found")
            
            if job.status in [JobStatus.RUNNING, JobStatus.DELETED]:
                raise ValueError(f"Cannot execute job with status: {job.status}")
            
            # Get target IDs
            if execute_data.target_ids:
                target_ids = execute_data.target_ids
                # Validate targets are associated with job
                job_target_ids = {jt.target_id for jt in job.targets}
                invalid_targets = set(target_ids) - job_target_ids
                if invalid_targets:
                    raise ValueError(f"Targets not associated with job: {invalid_targets}")
            else:
                target_ids = [jt.target_id for jt in job.targets]
            
            if not target_ids:
                raise ValueError("No targets specified for execution")
            
            # Get next execution number
            max_execution = self.db.query(func.max(JobExecution.execution_number)).filter(
                JobExecution.job_id == job_id
            ).scalar() or 0
            
            # Create execution record
            execution = JobExecution(
                job_id=job_id,
                execution_number=max_execution + 1,
                status=ExecutionStatus.SCHEDULED,
                triggered_by="manual",
                triggered_by_user=executed_by,
                execution_context=execute_data.execution_context,
                scheduled_at=datetime.now(timezone.utc),
                total_targets=len(target_ids)
            )
            
            self.db.add(execution)
            self.db.flush()  # Get execution ID
            
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            # Queue execution task
            execute_job_task.delay(execution.id, target_ids)
            
            # Send notification
            await notification_service.send_job_notification(
                user_id=executed_by,
                job_id=job_id,
                job_name=job.name,
                event_type="started",
                details={"target_count": len(target_ids)}
            )
            
            # Log audit event
            await audit_service.log_job_event(
                user_id=executed_by,
                event_type="JOB_EXECUTED",
                resource_id=str(job.id),
                action="execute",
                details={
                    "execution_id": execution.id,
                    "target_count": len(target_ids)
                }
            )
            
            logger.info(f"Started execution {execution.id} for job {job_id} on {len(target_ids)} targets")
            
            return JobExecutionResponse(
                id=execution.id,
                uuid=execution.uuid,
                job_id=execution.job_id,
                execution_number=execution.execution_number,
                status=execution.status,
                triggered_by=execution.triggered_by,
                triggered_by_user=execution.triggered_by_user,
                scheduled_at=execution.scheduled_at,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                created_at=execution.created_at,
                total_targets=execution.total_targets,
                successful_targets=execution.successful_targets,
                failed_targets=execution.failed_targets,
                execution_time_seconds=execution.execution_time_seconds,
                error_message=execution.error_message,
                retry_count=execution.retry_count
            )
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to execute job {job_id}: {e}")
            raise
    
    async def cancel_job(self, job_id: int, cancelled_by: int) -> Dict[str, Any]:
        """Cancel running job executions"""
        try:
            job = self.db.query(Job).filter(
                Job.id == job_id,
                Job.is_deleted == False
            ).first()
            
            if not job:
                raise ValueError("Job not found")
            
            if job.status != JobStatus.RUNNING:
                raise ValueError("Job is not running")
            
            # Find running executions
            running_executions = self.db.query(JobExecution).filter(
                JobExecution.job_id == job_id,
                JobExecution.status == ExecutionStatus.RUNNING
            ).all()
            
            cancelled_count = 0
            for execution in running_executions:
                execution.status = ExecutionStatus.CANCELLED
                execution.completed_at = datetime.now(timezone.utc)
                cancelled_count += 1
            
            # Update job status
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            # Send notification
            await notification_service.send_job_notification(
                user_id=cancelled_by,
                job_id=job_id,
                job_name=job.name,
                event_type="cancelled",
                details={"cancelled_executions": cancelled_count}
            )
            
            # Log audit event
            await audit_service.log_job_event(
                user_id=cancelled_by,
                event_type="JOB_CANCELLED",
                resource_id=str(job.id),
                action="cancel",
                details={"cancelled_executions": cancelled_count}
            )
            
            logger.info(f"Cancelled job {job_id} with {cancelled_count} running executions")
            
            return {
                "job_id": job_id,
                "cancelled_executions": cancelled_count,
                "status": "cancelled"
            }
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cancel job {job_id}: {e}")
            raise
    
    async def get_job_executions(self, job_id: int, page: int = 1, size: int = 20) -> List[JobExecutionResponse]:
        """Get job execution history"""
        try:
            offset = (page - 1) * size
            executions = self.db.query(JobExecution).filter(
                JobExecution.job_id == job_id
            ).order_by(desc(JobExecution.created_at)).offset(offset).limit(size).all()
            
            return [
                JobExecutionResponse(
                    id=execution.id,
                    uuid=execution.uuid,
                    job_id=execution.job_id,
                    execution_number=execution.execution_number,
                    status=execution.status,
                    triggered_by=execution.triggered_by,
                    triggered_by_user=execution.triggered_by_user,
                    scheduled_at=execution.scheduled_at,
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    created_at=execution.created_at,
                    total_targets=execution.total_targets,
                    successful_targets=execution.successful_targets,
                    failed_targets=execution.failed_targets,
                    execution_time_seconds=execution.execution_time_seconds,
                    error_message=execution.error_message,
                    retry_count=execution.retry_count
                )
                for execution in executions
            ]
            
        except Exception as e:
            logger.error(f"Failed to get executions for job {job_id}: {e}")
            raise
    
    async def _get_execution_summary(self, job_id: int) -> Dict[str, Any]:
        """Get execution summary for a job"""
        try:
            # Get latest execution
            latest_execution = self.db.query(JobExecution).filter(
                JobExecution.job_id == job_id
            ).order_by(desc(JobExecution.created_at)).first()
            
            if not latest_execution:
                return {
                    "total_executions": 0,
                    "last_execution": None
                }
            
            # Get execution counts by status
            execution_counts = self.db.query(
                JobExecution.status,
                func.count(JobExecution.id)
            ).filter(
                JobExecution.job_id == job_id
            ).group_by(JobExecution.status).all()
            
            status_counts = {status.value: count for status, count in execution_counts}
            
            return {
                "total_executions": sum(status_counts.values()),
                "status_counts": status_counts,
                "last_execution": {
                    "id": latest_execution.id,
                    "execution_number": latest_execution.execution_number,
                    "status": latest_execution.status.value,
                    "started_at": latest_execution.started_at,
                    "completed_at": latest_execution.completed_at,
                    "total_targets": latest_execution.total_targets,
                    "successful_targets": latest_execution.successful_targets,
                    "failed_targets": latest_execution.failed_targets
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get execution summary for job {job_id}: {e}")
            return {"total_executions": 0, "last_execution": None}