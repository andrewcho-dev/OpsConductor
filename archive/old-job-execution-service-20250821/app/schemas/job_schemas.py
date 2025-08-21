"""
Job Execution Service - Pydantic Schemas
Clean, modern schemas for API requests and responses
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.job_models import (
    JobType, JobStatus, ExecutionStatus, ActionType,
    ScheduleType, RecurringType
)


# =============================================================================
# JOB SCHEMAS
# =============================================================================

class JobActionCreate(BaseModel):
    """Schema for creating job actions"""
    action_type: ActionType
    action_name: str = Field(..., min_length=1, max_length=255)
    action_parameters: Optional[Dict[str, Any]] = None
    action_config: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False


class JobActionResponse(BaseModel):
    """Schema for job action responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    action_order: int
    action_type: ActionType
    action_name: str
    action_parameters: Optional[Dict[str, Any]] = None
    action_config: Optional[Dict[str, Any]] = None
    is_dangerous: bool = False
    requires_confirmation: bool = False


class JobTargetCreate(BaseModel):
    """Schema for creating job targets"""
    target_id: int
    target_name: Optional[str] = None
    target_type: Optional[str] = None


class JobTargetResponse(BaseModel):
    """Schema for job target responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    target_id: int
    target_name: Optional[str] = None
    target_type: Optional[str] = None


class JobCreate(BaseModel):
    """Schema for creating jobs"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    job_type: JobType = JobType.COMMAND
    actions: List[JobActionCreate] = Field(..., min_items=1)
    target_ids: List[int] = Field(..., min_items=1)
    scheduled_at: Optional[datetime] = None
    priority: int = Field(default=5, ge=1, le=10)
    timeout_seconds: Optional[int] = Field(None, gt=0)
    max_retries: int = Field(default=0, ge=0, le=10)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class JobUpdate(BaseModel):
    """Schema for updating jobs"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    actions: Optional[List[JobActionCreate]] = Field(None, min_items=1)
    target_ids: Optional[List[int]] = Field(None, min_items=1)
    scheduled_at: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    timeout_seconds: Optional[int] = Field(None, gt=0)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class JobResponse(BaseModel):
    """Schema for job responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: UUID
    name: str
    description: Optional[str] = None
    job_type: JobType
    status: JobStatus
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    priority: int
    timeout_seconds: Optional[int] = None
    max_retries: int
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Optional relationships
    actions: Optional[List[JobActionResponse]] = None
    targets: Optional[List[JobTargetResponse]] = None
    execution_summary: Optional[Dict[str, Any]] = None


class JobListResponse(BaseModel):
    """Schema for job list responses"""
    jobs: List[JobResponse]
    total: int
    page: int
    size: int
    has_next: bool


# =============================================================================
# EXECUTION SCHEMAS
# =============================================================================

class JobExecuteRequest(BaseModel):
    """Schema for job execution requests"""
    target_ids: Optional[List[int]] = None  # If None, use all job targets
    execution_context: Optional[Dict[str, Any]] = None


class JobExecutionResponse(BaseModel):
    """Schema for job execution responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: UUID
    job_id: int
    execution_number: int
    status: ExecutionStatus
    triggered_by: Optional[str] = None
    triggered_by_user: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    total_targets: int
    successful_targets: int
    failed_targets: int
    execution_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class JobExecutionResultResponse(BaseModel):
    """Schema for job execution result responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    execution_id: int
    target_id: int
    target_name: str
    action_id: int
    action_order: int
    action_name: str
    action_type: ActionType
    status: ExecutionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    output_text: Optional[str] = None
    error_text: Optional[str] = None
    exit_code: Optional[int] = None
    command_executed: Optional[str] = None
    connection_method: Optional[str] = None
    connection_host: Optional[str] = None
    retry_count: int = 0
    is_retry: bool = False


class JobExecutionDetailResponse(BaseModel):
    """Schema for detailed job execution responses"""
    execution: JobExecutionResponse
    results: List[JobExecutionResultResponse]
    job_info: Dict[str, Any]


# =============================================================================
# SCHEDULING SCHEMAS
# =============================================================================

class JobScheduleCreate(BaseModel):
    """Schema for creating job schedules"""
    schedule_type: ScheduleType
    enabled: bool = True
    
    # One-time scheduling
    execute_at: Optional[datetime] = None
    
    # Recurring scheduling
    recurring_type: Optional[RecurringType] = None
    interval: int = Field(default=1, ge=1)
    time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    days_of_week: Optional[str] = Field(None, pattern=r'^[0-6](,[0-6])*$')
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    
    # Cron scheduling
    cron_expression: Optional[str] = None
    
    # Advanced options
    timezone: str = "UTC"
    max_executions: Optional[int] = Field(None, gt=0)
    end_date: Optional[datetime] = None
    description: Optional[str] = None


class JobScheduleUpdate(BaseModel):
    """Schema for updating job schedules"""
    enabled: Optional[bool] = None
    execute_at: Optional[datetime] = None
    recurring_type: Optional[RecurringType] = None
    interval: Optional[int] = Field(None, ge=1)
    time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    days_of_week: Optional[str] = Field(None, pattern=r'^[0-6](,[0-6])*$')
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    max_executions: Optional[int] = Field(None, gt=0)
    end_date: Optional[datetime] = None
    description: Optional[str] = None


class JobScheduleResponse(BaseModel):
    """Schema for job schedule responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: UUID
    job_id: int
    schedule_type: ScheduleType
    enabled: bool
    execute_at: Optional[datetime] = None
    recurring_type: Optional[RecurringType] = None
    interval: int
    time: Optional[str] = None
    days_of_week: Optional[str] = None
    day_of_month: Optional[int] = None
    cron_expression: Optional[str] = None
    timezone: str
    max_executions: Optional[int] = None
    execution_count: int
    end_date: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    description: Optional[str] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# =============================================================================
# SYSTEM SCHEMAS
# =============================================================================

class HealthCheckResponse(BaseModel):
    """Schema for health check responses"""
    status: str
    timestamp: datetime
    version: str
    database: str
    redis: str
    external_services: Dict[str, str]


class ServiceMetricsResponse(BaseModel):
    """Schema for service metrics responses"""
    active_jobs: int
    running_executions: int
    queued_tasks: int
    total_executions_today: int
    success_rate_24h: float
    average_execution_time: float
    worker_status: Dict[str, Any]


class JobStatsResponse(BaseModel):
    """Schema for job statistics responses"""
    total_jobs: int
    jobs_by_status: Dict[str, int]
    jobs_by_type: Dict[str, int]
    executions_last_24h: int
    success_rate: float
    most_active_users: List[Dict[str, Any]]