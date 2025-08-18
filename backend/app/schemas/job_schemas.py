from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from app.models.job_models import (
    JobType, JobStatus, ExecutionStatus, ActionType, 
    LogPhase, LogLevel, LogCategory
)


# Job Creation Schemas
class JobActionCreate(BaseModel):
    action_order: Optional[int] = None
    action_type: ActionType
    action_name: str = Field(
        ..., min_length=1, max_length=255
    )
    action_parameters: Optional[Dict[str, Any]] = None
    action_config: Optional[Dict[str, Any]] = None


class JobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    job_type: JobType = JobType.COMMAND
    actions: List[JobActionCreate] = Field(..., min_items=1)
    target_ids: List[int] = Field(..., min_items=1)
    scheduled_at: Optional[datetime] = None


class JobSchedule(BaseModel):
    scheduled_at: datetime


# Job Response Schemas
class JobActionResponse(BaseModel):
    id: int
    action_order: int
    action_type: ActionType
    action_name: str
    action_parameters: Optional[Dict[str, Any]] = None
    action_config: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    id: int
    job_uuid: str
    job_serial: str
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
    last_execution: Optional[Dict[str, Any]] = None
    actions: List[JobActionResponse] = []

    @field_validator('job_uuid', mode='before')
    @classmethod
    def convert_uuid_to_string(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class JobExecutionBranchResponse(BaseModel):
    target_name: Optional[str] = None
    ip_address: Optional[str] = None
    os_type: Optional[str] = None
    id: int
    target_id: int
    branch_uuid: str
    branch_serial: str
    branch_id: str
    target_serial_ref: Optional[str] = None
    status: ExecutionStatus
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_output: Optional[str] = None
    result_error: Optional[str] = None
    exit_code: Optional[int] = None

    @field_validator('branch_uuid', mode='before')
    @classmethod
    def convert_branch_uuid_to_string(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class JobExecutionResponse(BaseModel):
    id: int
    execution_uuid: str
    execution_serial: str
    execution_number: int
    status: ExecutionStatus
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    branches: List['JobExecutionBranchResponse'] = []

    @field_validator('execution_uuid', mode='before')
    @classmethod
    def convert_execution_uuid_to_string(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class JobExecutionLogResponse(BaseModel):
    id: int
    branch_id: Optional[int] = None
    log_phase: LogPhase
    log_level: LogLevel
    log_category: LogCategory
    log_message: str
    log_details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class JobWithExecutionsResponse(BaseModel):
    job: JobResponse
    executions: List[JobExecutionResponse] = []

    class Config:
        from_attributes = True


# Job List Schemas
class JobListItem(BaseModel):
    id: int
    job_uuid: str
    job_serial: str
    name: str
    job_type: JobType
    status: JobStatus
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    last_execution: Optional[Dict[str, Any]] = None

    @field_validator('job_uuid', mode='before')
    @classmethod
    def convert_job_uuid_to_string(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: List[JobListItem]
    total: int
    page: int
    per_page: int


# Job Execution Schemas
class JobExecuteRequest(BaseModel):
    target_ids: Optional[List[int]] = None  # If None, use all job targets


class JobExecutionStatus(BaseModel):
    job_id: int
    execution_id: int
    status: ExecutionStatus
    progress: float = Field(..., ge=0, le=100)  # 0-100%
    completed_branches: int
    total_branches: int
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


# Action Result Schemas
class JobActionResultResponse(BaseModel):
    id: int
    branch_id: int
    action_id: int
    action_serial: str
    action_order: int
    action_name: str
    action_type: ActionType
    status: ExecutionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    result_output: Optional[str] = None
    result_error: Optional[str] = None
    exit_code: Optional[int] = None
    command_executed: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Notification Schemas
class JobNotificationRequest(BaseModel):
    job_id: int
    execution_id: int
    notification_type: str  # "started", "completed", "failed"
    message: str
    details: Optional[Dict[str, Any]] = None
