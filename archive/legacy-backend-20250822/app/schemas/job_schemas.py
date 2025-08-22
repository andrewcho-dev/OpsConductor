from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.job_models import (
    JobType, JobStatus, ExecutionStatus, ActionType
)


# SIMPLIFIED JOB SCHEMAS - NO SERIALIZATION COMPLEXITY

# Job Creation Schemas
class JobActionCreate(BaseModel):
    action_order: Optional[int] = None
    action_type: ActionType
    action_name: str = Field(..., min_length=1, max_length=255)
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


class JobExecuteRequest(BaseModel):
    target_ids: Optional[List[int]] = None  # If None, use all job targets


# Job Response Schemas
class JobActionResponse(BaseModel):
    id: int
    action_order: int
    action_type: ActionType
    action_name: str
    action_parameters: Optional[Dict[str, Any]] = None
    action_config: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    job_type: JobType
    status: JobStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    actions: List[JobActionResponse] = []

    class Config:
        from_attributes = True


class JobExecutionResponse(BaseModel):
    id: int
    job_id: int
    execution_number: int
    status: ExecutionStatus
    total_targets: int
    successful_targets: int
    failed_targets: int
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobExecutionResultResponse(BaseModel):
    id: int
    execution_id: int
    target_id: int
    target_name: str
    action_name: str
    action_type: ActionType
    status: ExecutionStatus
    output_text: Optional[str] = None
    error_text: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time_ms: Optional[int] = None
    command_executed: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Job List Schemas
class JobListItem(BaseModel):
    id: int
    name: str
    status: JobStatus
    job_type: JobType
    created_at: datetime
    scheduled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: List[JobListItem]
    total: int
    page: int
    per_page: int