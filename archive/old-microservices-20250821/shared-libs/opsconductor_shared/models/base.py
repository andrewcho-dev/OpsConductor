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
    # Existing Services
    AUTH_SERVICE = "auth-service"
    USER_SERVICE = "user-service"
    UNIVERSAL_TARGETS = "universal-targets"
    FRONTEND = "frontend"
    # New Microservices
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
    
    # Authentication Events
    USER_LOGIN = "auth.user.login"
    USER_LOGOUT = "auth.user.logout"
    TOKEN_CREATED = "auth.token.created"
    TOKEN_REFRESHED = "auth.token.refreshed"
    TOKEN_REVOKED = "auth.token.revoked"
    SESSION_EXPIRED = "auth.session.expired"
    
    # User Management Events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"
    USER_ROLE_ASSIGNED = "user.role.assigned"
    USER_ROLE_REMOVED = "user.role.removed"
    USER_PERMISSION_GRANTED = "user.permission.granted"
    USER_PERMISSION_REVOKED = "user.permission.revoked"
    
    # Universal Targets Events
    TARGET_CREATED = "target.created"
    TARGET_UPDATED = "target.updated"
    TARGET_DELETED = "target.deleted"
    TARGET_CONNECTION_TESTED = "target.connection.tested"
    TARGET_CONNECTION_FAILED = "target.connection.failed"
    TARGET_HEALTH_CHECK = "target.health.check"
    TARGET_CREDENTIALS_UPDATED = "target.credentials.updated"
    
    # Job Management Events
    JOB_CREATED = "job.created"
    JOB_UPDATED = "job.updated"
    JOB_DELETED = "job.deleted"
    JOB_VALIDATED = "job.validated"
    JOB_VALIDATION_FAILED = "job.validation.failed"
    JOB_APPROVED = "job.approved"
    JOB_REJECTED = "job.rejected"
    
    # Job Execution Events
    JOB_EXECUTED = "job.executed"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_CANCELLED = "execution.cancelled"
    EXECUTION_TIMEOUT = "execution.timeout"
    EXECUTION_RETRY = "execution.retry"
    
    # Job Scheduling Events
    SCHEDULE_CREATED = "schedule.created"
    SCHEDULE_UPDATED = "schedule.updated"
    SCHEDULE_DELETED = "schedule.deleted"
    SCHEDULE_TRIGGERED = "schedule.triggered"
    SCHEDULE_MISSED = "schedule.missed"
    SCHEDULE_PAUSED = "schedule.paused"
    SCHEDULE_RESUMED = "schedule.resumed"
    
    # Audit & Events
    AUDIT_LOG_CREATED = "audit.log.created"
    SYSTEM_HEALTH_CHECK = "system.health.check"
    SYSTEM_ALERT = "system.alert"
    SYSTEM_ERROR = "system.error"
    
    # General System Events
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    SERVICE_HEALTH_CHECK = "service.health.check"
    SERVICE_ERROR = "service.error"


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