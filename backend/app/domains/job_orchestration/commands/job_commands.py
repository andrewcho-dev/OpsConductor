"""
Job Orchestration Commands
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from app.shared.infrastructure.cqrs import Command


@dataclass
class CreateJobCommand(Command):
    """Command to create a new job."""
    name: str
    description: str
    job_type: str
    actions: List[Dict[str, Any]]
    target_ids: List[int]
    created_by: int
    schedule_config: Optional[Dict[str, Any]] = None


@dataclass
class UpdateJobCommand(Command):
    """Command to update an existing job."""
    job_id: int
    update_data: Dict[str, Any]
    updated_by: int


@dataclass
class DeleteJobCommand(Command):
    """Command to delete a job."""
    job_id: int
    deleted_by: int


@dataclass
class ExecuteJobCommand(Command):
    """Command to execute a job."""
    job_id: int
    executed_by: int
    execution_params: Optional[Dict[str, Any]] = None


@dataclass
class CompleteJobExecutionCommand(Command):
    """Command to mark job execution as completed."""
    execution_id: int
    result: Dict[str, Any]
    success_count: int = 0
    failure_count: int = 0


@dataclass
class FailJobExecutionCommand(Command):
    """Command to mark job execution as failed."""
    execution_id: int
    error_message: str
    partial_result: Optional[Dict[str, Any]] = None


@dataclass
class UpdateJobExecutionProgressCommand(Command):
    """Command to update job execution progress."""
    execution_id: int
    progress_percentage: float
    current_target: str
    completed_targets: int
    total_targets: int


@dataclass
class ScheduleJobCommand(Command):
    """Command to schedule a job."""
    job_id: int
    schedule_config: Dict[str, Any]
    scheduled_by: int


@dataclass
class UnscheduleJobCommand(Command):
    """Command to unschedule a job."""
    job_id: int
    unscheduled_by: int


@dataclass
class CleanupStaleExecutionsCommand(Command):
    """Command to cleanup stale executions."""
    timeout_minutes: int = 60