"""
Event schemas for inter-service communication
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

from opsconductor_shared.models.base import BaseEvent, EventType, ServiceType


# =============================================================================
# Authentication Event Schemas
# =============================================================================

class UserLoginEvent(BaseEvent):
    """User login event"""
    event_type: EventType = EventType.USER_LOGIN
    service_name: ServiceType = ServiceType.AUTH_SERVICE
    
    class EventData(BaseModel):
        user_id: int
        email: str
        ip_address: Optional[str] = None
        user_agent: Optional[str] = None
        login_method: str = "password"  # password, sso, api_key
    
    data: EventData


class UserLogoutEvent(BaseEvent):
    """User logout event"""
    event_type: EventType = EventType.USER_LOGOUT
    service_name: ServiceType = ServiceType.AUTH_SERVICE
    
    class EventData(BaseModel):
        user_id: int
        session_duration: Optional[int] = None  # in seconds
        logout_reason: str = "user_initiated"  # user_initiated, timeout, forced
    
    data: EventData


class TokenCreatedEvent(BaseEvent):
    """Token creation event"""
    event_type: EventType = EventType.TOKEN_CREATED
    service_name: ServiceType = ServiceType.AUTH_SERVICE
    
    class EventData(BaseModel):
        user_id: int
        token_type: str  # access, refresh
        expires_at: datetime
        scopes: List[str] = []
    
    data: EventData


# =============================================================================
# User Management Event Schemas
# =============================================================================

class UserCreatedEvent(BaseEvent):
    """User creation event"""
    event_type: EventType = EventType.USER_CREATED
    service_name: ServiceType = ServiceType.USER_SERVICE
    
    class EventData(BaseModel):
        user_id: int
        email: str
        full_name: str
        roles: List[str] = []
        is_active: bool = True
        created_by: Optional[int] = None
    
    data: EventData


class UserUpdatedEvent(BaseEvent):
    """User update event"""
    event_type: EventType = EventType.USER_UPDATED
    service_name: ServiceType = ServiceType.USER_SERVICE
    
    class EventData(BaseModel):
        user_id: int
        updated_fields: List[str]
        old_values: Dict[str, Any] = {}
        new_values: Dict[str, Any] = {}
        updated_by: Optional[int] = None
    
    data: EventData


class UserRoleAssignedEvent(BaseEvent):
    """User role assignment event"""
    event_type: EventType = EventType.USER_ROLE_ASSIGNED
    service_name: ServiceType = ServiceType.USER_SERVICE
    
    class EventData(BaseModel):
        user_id: int
        role: str
        assigned_by: Optional[int] = None
        effective_date: Optional[datetime] = None
    
    data: EventData


# =============================================================================
# Universal Targets Event Schemas
# =============================================================================

class TargetCreatedEvent(BaseEvent):
    """Target creation event"""
    event_type: EventType = EventType.TARGET_CREATED
    service_name: ServiceType = ServiceType.UNIVERSAL_TARGETS
    
    class EventData(BaseModel):
        target_id: int
        name: str
        target_type: str  # linux, windows, network_device
        hostname: str
        created_by: Optional[int] = None
        connection_methods: List[str] = []
    
    data: EventData


class TargetConnectionTestedEvent(BaseEvent):
    """Target connection test event"""
    event_type: EventType = EventType.TARGET_CONNECTION_TESTED
    service_name: ServiceType = ServiceType.UNIVERSAL_TARGETS
    
    class EventData(BaseModel):
        target_id: int
        connection_method_id: int
        success: bool
        response_time: Optional[float] = None  # in seconds
        error_message: Optional[str] = None
        tested_by: Optional[int] = None
    
    data: EventData


class TargetHealthCheckEvent(BaseEvent):
    """Target health check event"""
    event_type: EventType = EventType.TARGET_HEALTH_CHECK
    service_name: ServiceType = ServiceType.UNIVERSAL_TARGETS
    
    class EventData(BaseModel):
        target_id: int
        health_status: str  # healthy, unhealthy, unknown
        checks_performed: List[str] = []
        response_times: Dict[str, float] = {}
        errors: List[str] = []
    
    data: EventData


# =============================================================================
# Job Management Event Schemas
# =============================================================================

class JobCreatedEvent(BaseEvent):
    """Job creation event"""
    event_type: EventType = EventType.JOB_CREATED
    service_name: ServiceType = ServiceType.JOB_MANAGEMENT
    
    class EventData(BaseModel):
        job_id: int
        name: str
        job_type: str  # command, script, file_transfer, composite
        target_ids: List[int] = []
        created_by: Optional[int] = None
        scheduled: bool = False
        priority: int = 5
    
    data: EventData


class JobValidatedEvent(BaseEvent):
    """Job validation event"""
    event_type: EventType = EventType.JOB_VALIDATED
    service_name: ServiceType = ServiceType.JOB_MANAGEMENT
    
    class EventData(BaseModel):
        job_id: int
        validation_result: bool
        validation_errors: List[str] = []
        validated_by: Optional[int] = None
        target_validation_results: Dict[int, bool] = {}
    
    data: EventData


# =============================================================================
# Job Execution Event Schemas
# =============================================================================

class ExecutionStartedEvent(BaseEvent):
    """Job execution started event"""
    event_type: EventType = EventType.EXECUTION_STARTED
    service_name: ServiceType = ServiceType.JOB_EXECUTION
    
    class EventData(BaseModel):
        execution_id: int
        job_id: int
        target_ids: List[int]
        started_by: Optional[int] = None
        execution_mode: str = "parallel"  # parallel, sequential
        estimated_duration: Optional[int] = None  # in seconds
    
    data: EventData


class ExecutionCompletedEvent(BaseEvent):
    """Job execution completed event"""
    event_type: EventType = EventType.EXECUTION_COMPLETED
    service_name: ServiceType = ServiceType.JOB_EXECUTION
    
    class EventData(BaseModel):
        execution_id: int
        job_id: int
        duration: int  # in seconds
        success_count: int
        failure_count: int
        target_results: Dict[int, str] = {}  # target_id -> status
        output_summary: Optional[str] = None
    
    data: EventData


class ExecutionFailedEvent(BaseEvent):
    """Job execution failed event"""
    event_type: EventType = EventType.EXECUTION_FAILED
    service_name: ServiceType = ServiceType.JOB_EXECUTION
    
    class EventData(BaseModel):
        execution_id: int
        job_id: int
        failure_reason: str
        failed_targets: List[int] = []
        error_details: Dict[str, Any] = {}
        retry_count: int = 0
        will_retry: bool = False
    
    data: EventData


# =============================================================================
# Job Scheduling Event Schemas
# =============================================================================

class ScheduleCreatedEvent(BaseEvent):
    """Schedule creation event"""
    event_type: EventType = EventType.SCHEDULE_CREATED
    service_name: ServiceType = ServiceType.JOB_SCHEDULING
    
    class EventData(BaseModel):
        schedule_id: int
        job_id: int
        schedule_type: str  # once, recurring, cron
        cron_expression: Optional[str] = None
        next_run: Optional[datetime] = None
        created_by: Optional[int] = None
        timezone: str = "UTC"
    
    data: EventData


class ScheduleTriggeredEvent(BaseEvent):
    """Schedule triggered event"""
    event_type: EventType = EventType.SCHEDULE_TRIGGERED
    service_name: ServiceType = ServiceType.JOB_SCHEDULING
    
    class EventData(BaseModel):
        schedule_id: int
        job_id: int
        trigger_time: datetime
        next_run: Optional[datetime] = None
        execution_id: Optional[int] = None
        trigger_source: str = "scheduler"  # scheduler, manual, api
    
    data: EventData


# =============================================================================
# System Event Schemas
# =============================================================================

class ServiceHealthCheckEvent(BaseEvent):
    """Service health check event"""
    event_type: EventType = EventType.SERVICE_HEALTH_CHECK
    
    class EventData(BaseModel):
        service_name: str
        health_status: str  # healthy, unhealthy, degraded
        response_time: Optional[float] = None
        checks: Dict[str, Any] = {}  # database, redis, external_services
        errors: List[str] = []
        uptime: Optional[int] = None  # in seconds
    
    data: EventData


class SystemAlertEvent(BaseEvent):
    """System alert event"""
    event_type: EventType = EventType.SYSTEM_ALERT
    service_name: ServiceType = ServiceType.AUDIT_EVENTS
    
    class EventData(BaseModel):
        alert_type: str  # error, warning, info
        alert_source: str
        message: str
        severity: int = 1  # 1-5, 5 being most severe
        affected_services: List[str] = []
        resolution_steps: List[str] = []
        auto_resolve: bool = False
    
    data: EventData


# =============================================================================
# Event Factory Functions
# =============================================================================

def create_user_login_event(
    user_id: int,
    email: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    correlation_id: Optional[UUID] = None
) -> UserLoginEvent:
    """Create a user login event"""
    return UserLoginEvent(
        data=UserLoginEvent.EventData(
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent
        ),
        correlation_id=correlation_id,
        user_id=user_id
    )


def create_target_created_event(
    target_id: int,
    name: str,
    target_type: str,
    hostname: str,
    created_by: Optional[int] = None,
    correlation_id: Optional[UUID] = None
) -> TargetCreatedEvent:
    """Create a target created event"""
    return TargetCreatedEvent(
        data=TargetCreatedEvent.EventData(
            target_id=target_id,
            name=name,
            target_type=target_type,
            hostname=hostname,
            created_by=created_by
        ),
        correlation_id=correlation_id,
        user_id=created_by
    )


def create_job_created_event(
    job_id: int,
    name: str,
    job_type: str,
    target_ids: List[int],
    created_by: Optional[int] = None,
    correlation_id: Optional[UUID] = None
) -> JobCreatedEvent:
    """Create a job created event"""
    return JobCreatedEvent(
        data=JobCreatedEvent.EventData(
            job_id=job_id,
            name=name,
            job_type=job_type,
            target_ids=target_ids,
            created_by=created_by
        ),
        correlation_id=correlation_id,
        user_id=created_by
    )


def create_execution_started_event(
    execution_id: int,
    job_id: int,
    target_ids: List[int],
    started_by: Optional[int] = None,
    correlation_id: Optional[UUID] = None
) -> ExecutionStartedEvent:
    """Create an execution started event"""
    return ExecutionStartedEvent(
        data=ExecutionStartedEvent.EventData(
            execution_id=execution_id,
            job_id=job_id,
            target_ids=target_ids,
            started_by=started_by
        ),
        correlation_id=correlation_id,
        user_id=started_by
    )