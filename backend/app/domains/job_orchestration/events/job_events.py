"""
Job Orchestration Domain Events
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
import uuid

from app.shared.infrastructure.events import DomainEvent


@dataclass
class JobCreatedEvent(DomainEvent):
    """Event raised when a job is created."""
    job_id: int
    job_name: str
    job_type: str
    created_by: int
    target_count: int
    
    def __init__(self, job_id: int, job_name: str, job_type: str, created_by: int, target_count: int):
        self.job_id = job_id
        self.job_name = job_name
        self.job_type = job_type
        self.created_by = created_by
        self.target_count = target_count
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(job_id),
            aggregate_type="Job"
        )


@dataclass
class JobUpdatedEvent(DomainEvent):
    """Event raised when a job is updated."""
    job_id: int
    job_name: str
    changes: Dict[str, Any]
    updated_by: int
    
    def __init__(self, job_id: int, job_name: str, changes: Dict[str, Any], updated_by: int):
        self.job_id = job_id
        self.job_name = job_name
        self.changes = changes
        self.updated_by = updated_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(job_id),
            aggregate_type="Job"
        )


@dataclass
class JobDeletedEvent(DomainEvent):
    """Event raised when a job is deleted."""
    job_id: int
    job_name: str
    deleted_by: int
    
    def __init__(self, job_id: int, job_name: str, deleted_by: int):
        self.job_id = job_id
        self.job_name = job_name
        self.deleted_by = deleted_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(job_id),
            aggregate_type="Job"
        )


@dataclass
class JobExecutionStartedEvent(DomainEvent):
    """Event raised when a job execution starts."""
    execution_id: int
    job_id: int
    job_name: str
    executed_by: int
    target_count: int
    
    def __init__(self, execution_id: int, job_id: int, job_name: str, executed_by: int, target_count: int):
        self.execution_id = execution_id
        self.job_id = job_id
        self.job_name = job_name
        self.executed_by = executed_by
        self.target_count = target_count
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(execution_id),
            aggregate_type="JobExecution"
        )


@dataclass
class JobExecutionCompletedEvent(DomainEvent):
    """Event raised when a job execution completes successfully."""
    execution_id: int
    job_id: int
    duration_seconds: float
    success_count: int
    failure_count: int
    result: Dict[str, Any]
    
    def __init__(
        self, 
        execution_id: int, 
        job_id: int, 
        duration_seconds: float,
        success_count: int,
        failure_count: int,
        result: Dict[str, Any]
    ):
        self.execution_id = execution_id
        self.job_id = job_id
        self.duration_seconds = duration_seconds
        self.success_count = success_count
        self.failure_count = failure_count
        self.result = result
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(execution_id),
            aggregate_type="JobExecution"
        )


@dataclass
class JobExecutionFailedEvent(DomainEvent):
    """Event raised when a job execution fails."""
    execution_id: int
    job_id: int
    error_message: str
    duration_seconds: float
    
    def __init__(self, execution_id: int, job_id: int, error_message: str, duration_seconds: float):
        self.execution_id = execution_id
        self.job_id = job_id
        self.error_message = error_message
        self.duration_seconds = duration_seconds
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(execution_id),
            aggregate_type="JobExecution"
        )


@dataclass
class JobExecutionProgressEvent(DomainEvent):
    """Event raised when job execution progress is updated."""
    execution_id: int
    job_id: int
    progress_percentage: float
    current_target: str
    completed_targets: int
    total_targets: int
    
    def __init__(
        self, 
        execution_id: int, 
        job_id: int, 
        progress_percentage: float,
        current_target: str,
        completed_targets: int,
        total_targets: int
    ):
        self.execution_id = execution_id
        self.job_id = job_id
        self.progress_percentage = progress_percentage
        self.current_target = current_target
        self.completed_targets = completed_targets
        self.total_targets = total_targets
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(execution_id),
            aggregate_type="JobExecution"
        )


@dataclass
class JobScheduledEvent(DomainEvent):
    """Event raised when a job is scheduled."""
    job_id: int
    job_name: str
    schedule_config: Dict[str, Any]
    next_run_time: datetime
    
    def __init__(self, job_id: int, job_name: str, schedule_config: Dict[str, Any], next_run_time: datetime):
        self.job_id = job_id
        self.job_name = job_name
        self.schedule_config = schedule_config
        self.next_run_time = next_run_time
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(job_id),
            aggregate_type="Job"
        )