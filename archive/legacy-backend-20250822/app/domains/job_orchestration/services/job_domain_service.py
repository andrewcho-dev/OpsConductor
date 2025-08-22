"""
Job Domain Service - Contains business logic for job orchestration.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

from app.shared.exceptions.base import ValidationException, ConflictError, NotFoundError
from app.domains.job_orchestration.repositories.job_repository import JobRepository, JobExecutionRepository
from app.models.job_models import Job, JobExecution, ExecutionStatus
from app.shared.infrastructure.container import injectable
from app.shared.infrastructure.events import event_bus
from app.domains.job_orchestration.events.job_events import (
    JobCreatedEvent, JobUpdatedEvent, JobExecutionStartedEvent,
    JobExecutionCompletedEvent, JobExecutionFailedEvent
)


@injectable()
class JobDomainService:
    """Domain service for job orchestration business logic."""
    
    def __init__(
        self, 
        job_repository: JobRepository,
        execution_repository: JobExecutionRepository
    ):
        self.job_repository = job_repository
        self.execution_repository = execution_repository
    
    async def create_job(
        self,
        name: str,
        description: str,
        job_type: str,
        actions: List[Dict[str, Any]],
        target_ids: List[int],
        created_by: int,
        schedule_config: Optional[Dict[str, Any]] = None
    ) -> Job:
        """Create a new job with validation."""
        # Validate input
        await self._validate_job_creation(name, job_type, actions, target_ids)
        
        # Check for name conflicts
        existing_job = await self.job_repository.get_by_name(name)
        if existing_job:
            raise ConflictError(f"Job with name '{name}' already exists")
        
        # Create job data
        job_data = {
            "name": name,
            "description": description,
            "job_type": job_type,
            "actions": actions,
            "target_ids": target_ids,
            "created_by": created_by,
            "status": "active",
            "is_scheduled": bool(schedule_config),
            "schedule_config": schedule_config,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        job = await self.job_repository.create(job_data)
        
        # Publish domain event
        event = JobCreatedEvent(
            job_id=job.id,
            job_name=job.name,
            job_type=job.job_type,
            created_by=created_by,
            target_count=len(target_ids)
        )
        await event_bus.publish(event)
        
        return job
    
    async def update_job(
        self,
        job_id: int,
        update_data: Dict[str, Any],
        updated_by: int
    ) -> Job:
        """Update job with validation."""
        job = await self.job_repository.get_by_id_or_raise(job_id)
        
        # Validate updates
        if "name" in update_data and update_data["name"] != job.name:
            existing_job = await self.job_repository.get_by_name(update_data["name"])
            if existing_job and existing_job.id != job_id:
                raise ConflictError(f"Job with name '{update_data['name']}' already exists")
        
        if "actions" in update_data:
            self._validate_actions(update_data["actions"])
        
        if "target_ids" in update_data:
            self._validate_target_ids(update_data["target_ids"])
        
        # Track changes for event
        changes = {k: v for k, v in update_data.items() if getattr(job, k, None) != v}
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        updated_job = await self.job_repository.update(job_id, update_data)
        
        # Publish domain event
        if changes:
            event = JobUpdatedEvent(
                job_id=job.id,
                job_name=job.name,
                changes=changes,
                updated_by=updated_by
            )
            await event_bus.publish(event)
        
        return updated_job
    
    async def execute_job(
        self,
        job_id: int,
        executed_by: int,
        execution_params: Optional[Dict[str, Any]] = None
    ) -> JobExecution:
        """Start job execution."""
        job = await self.job_repository.get_by_id_or_raise(job_id)
        
        if job.status != "active":
            raise ValidationException(f"Cannot execute inactive job '{job.name}'")
        
        # Create execution record
        execution_data = {
            "job_id": job_id,
            "executed_by": executed_by,
            "status": ExecutionStatus.PENDING,
            "execution_params": execution_params or {},
            "started_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        execution = await self.execution_repository.create(execution_data)
        
        # Publish domain event
        event = JobExecutionStartedEvent(
            execution_id=execution.id,
            job_id=job.id,
            job_name=job.name,
            executed_by=executed_by,
            target_count=len(job.target_ids)
        )
        await event_bus.publish(event)
        
        return execution
    
    async def complete_job_execution(
        self,
        execution_id: int,
        result: Dict[str, Any],
        success_count: int = 0,
        failure_count: int = 0
    ) -> JobExecution:
        """Mark job execution as completed."""
        execution = await self.execution_repository.update_execution_status(
            execution_id=execution_id,
            status=ExecutionStatus.COMPLETED,
            result=result
        )
        
        # Publish domain event
        event = JobExecutionCompletedEvent(
            execution_id=execution.id,
            job_id=execution.job_id,
            duration_seconds=(execution.completed_at - execution.started_at).total_seconds(),
            success_count=success_count,
            failure_count=failure_count,
            result=result
        )
        await event_bus.publish(event)
        
        return execution
    
    async def fail_job_execution(
        self,
        execution_id: int,
        error_message: str,
        partial_result: Optional[Dict[str, Any]] = None
    ) -> JobExecution:
        """Mark job execution as failed."""
        execution = await self.execution_repository.update_execution_status(
            execution_id=execution_id,
            status=ExecutionStatus.FAILED,
            result=partial_result,
            error_message=error_message
        )
        
        # Publish domain event
        event = JobExecutionFailedEvent(
            execution_id=execution.id,
            job_id=execution.job_id,
            error_message=error_message,
            duration_seconds=(execution.completed_at - execution.started_at).total_seconds() if execution.completed_at else 0
        )
        await event_bus.publish(event)
        
        return execution
    
    async def get_job_executions(
        self,
        job_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobExecution]:
        """Get executions for a job."""
        return await self.execution_repository.get_executions_by_job(job_id, skip, limit)
    
    async def get_running_executions(self) -> List[JobExecution]:
        """Get all currently running executions."""
        return await self.execution_repository.get_running_executions()
    
    async def cleanup_stale_executions(self, timeout_minutes: int = 60) -> List[JobExecution]:
        """Find and cleanup stale executions."""
        stale_executions = await self.execution_repository.get_stale_executions(timeout_minutes)
        
        for execution in stale_executions:
            await self.fail_job_execution(
                execution_id=execution.id,
                error_message=f"Execution timed out after {timeout_minutes} minutes"
            )
        
        return stale_executions
    
    async def get_job_statistics(self) -> Dict[str, Any]:
        """Get comprehensive job statistics."""
        job_stats = await self.job_repository.get_job_statistics()
        execution_stats = await self.execution_repository.get_execution_statistics()
        
        return {
            "jobs": job_stats,
            "executions": execution_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def search_jobs(
        self,
        search_term: str = "",
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Job]:
        """Search jobs with filters."""
        return await self.job_repository.search_jobs(search_term, filters, skip, limit)
    
    async def _validate_job_creation(
        self,
        name: str,
        job_type: str,
        actions: List[Dict[str, Any]],
        target_ids: List[int]
    ) -> None:
        """Validate job creation data."""
        if not name or len(name.strip()) < 3:
            raise ValidationException("Job name must be at least 3 characters long")
        
        if not job_type:
            raise ValidationException("Job type is required")
        
        self._validate_actions(actions)
        self._validate_target_ids(target_ids)
    
    def _validate_actions(self, actions: List[Dict[str, Any]]) -> None:
        """Validate job actions."""
        if not actions:
            raise ValidationException("At least one action is required")
        
        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                raise ValidationException(f"Action {i + 1} must be a dictionary")
            
            if "type" not in action:
                raise ValidationException(f"Action {i + 1} must have a 'type' field")
            
            if "parameters" not in action:
                raise ValidationException(f"Action {i + 1} must have a 'parameters' field")
    
    def _validate_target_ids(self, target_ids: List[int]) -> None:
        """Validate target IDs."""
        if not target_ids:
            raise ValidationException("At least one target is required")
        
        if not all(isinstance(tid, int) and tid > 0 for tid in target_ids):
            raise ValidationException("All target IDs must be positive integers")