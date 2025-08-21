"""
Shared base models and enums
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID, uuid4


class ServiceType(str, Enum):
    """Service types in the microservice architecture"""
    JOB_MANAGEMENT = "job-management"
    JOB_EXECUTION = "job-execution"
    JOB_SCHEDULING = "job-scheduling"
    AUDIT_EVENTS = "audit-events"
    API_GATEWAY = "api-gateway"


class JobType(str, Enum):
    """Types of jobs that can be executed"""
    COMMAND = "command"
    SCRIPT = "script"
    FILE_TRANSFER = "file_transfer"
    COMPOSITE = "composite"


class JobStatus(str, Enum):
    """Job lifecycle status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DELETED = "deleted"


class ExecutionStatus(str, Enum):
    """Execution status for individual runs"""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ActionType(str, Enum):
    """Types of actions within jobs"""
    COMMAND = "command"
    SCRIPT = "script"
    FILE_TRANSFER = "file_transfer"
    WAIT = "wait"
    CONDITION = "condition"


class ScheduleType(str, Enum):
    """Types of job schedules"""
    ONCE = "once"
    RECURRING = "recurring"
    CRON = "cron"


class RecurringType(str, Enum):
    """Recurring schedule intervals"""
    MINUTES = "minutes"
    HOURS = "hours"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class EventType(str, Enum):
    """Event types for inter-service communication"""
    JOB_CREATED = "job.created"
    JOB_UPDATED = "job.updated"
    JOB_DELETED = "job.deleted"
    JOB_EXECUTED = "job.executed"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_CANCELLED = "execution.cancelled"
    SCHEDULE_CREATED = "schedule.created"
    SCHEDULE_TRIGGERED = "schedule.triggered"


class BaseEvent(BaseModel):
    """Base event model for inter-service communication"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    service_name: ServiceType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[UUID] = None
    user_id: Optional[int] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ServiceResponse(BaseModel):
    """Standard service response format"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    service: ServiceType
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Standard paginated response format"""
    items: List[Any]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool