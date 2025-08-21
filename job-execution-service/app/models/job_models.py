"""
Job Execution Service - Database Models
Clean, optimized models for job management and execution
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, JSON, ForeignKey, 
    Enum, Boolean, Float, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum
import uuid


# =============================================================================
# ENUMS
# =============================================================================

class JobType(str, enum.Enum):
    COMMAND = "command"
    SCRIPT = "script"
    FILE_TRANSFER = "file_transfer"
    COMPOSITE = "composite"


class JobStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DELETED = "deleted"


class ExecutionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ActionType(str, enum.Enum):
    COMMAND = "command"
    SCRIPT = "script"
    FILE_TRANSFER = "file_transfer"


class ScheduleType(str, enum.Enum):
    ONCE = "once"
    RECURRING = "recurring"
    CRON = "cron"


class RecurringType(str, enum.Enum):
    MINUTES = "minutes"
    HOURS = "hours"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# =============================================================================
# CORE JOB MODELS
# =============================================================================

class Job(Base):
    """Job definition and metadata"""
    __tablename__ = "jobs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Basic info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    job_type = Column(Enum(JobType), nullable=False, default=JobType.COMMAND)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.DRAFT, index=True)
    
    # User tracking
    created_by = Column(Integer, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Execution settings
    priority = Column(Integer, default=5, nullable=False)
    timeout_seconds = Column(Integer, nullable=True)
    max_retries = Column(Integer, default=0, nullable=False)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)  # For categorization and filtering
    metadata = Column(JSON, nullable=True)  # Additional job metadata
    
    # Relationships
    actions = relationship("JobAction", back_populates="job", cascade="all, delete-orphan")
    targets = relationship("JobTarget", back_populates="job", cascade="all, delete-orphan")
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    schedules = relationship("JobSchedule", back_populates="job", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_jobs_status_created', 'status', 'created_at'),
        Index('idx_jobs_created_by_status', 'created_by', 'status'),
        Index('idx_jobs_scheduled_at_status', 'scheduled_at', 'status'),
    )


class JobAction(Base):
    """Actions to perform in a job"""
    __tablename__ = "job_actions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    # Action definition
    action_order = Column(Integer, nullable=False)
    action_type = Column(Enum(ActionType), nullable=False)
    action_name = Column(String(255), nullable=False)
    
    # Action configuration
    action_parameters = Column(JSON, nullable=True)  # Command, script content, etc.
    action_config = Column(JSON, nullable=True)      # Timeout, retry, etc.
    
    # Validation and safety
    is_dangerous = Column(Boolean, default=False)    # Flagged as potentially dangerous
    requires_confirmation = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="actions")

    # Indexes
    __table_args__ = (
        Index('idx_job_actions_job_order', 'job_id', 'action_order'),
    )


class JobTarget(Base):
    """Target associations for jobs"""
    __tablename__ = "job_targets"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(Integer, nullable=False)  # Reference to target in target service
    
    # Target metadata (cached for performance)
    target_name = Column(String(255), nullable=True)
    target_type = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="targets")

    # Indexes
    __table_args__ = (
        Index('idx_job_targets_job_id', 'job_id'),
        Index('idx_job_targets_target_id', 'target_id'),
    )


# =============================================================================
# EXECUTION MODELS
# =============================================================================

class JobExecution(Base):
    """Job execution instance"""
    __tablename__ = "job_executions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    # Execution metadata
    execution_number = Column(Integer, nullable=False)  # Sequential per job
    status = Column(Enum(ExecutionStatus), nullable=False, default=ExecutionStatus.SCHEDULED, index=True)
    
    # Execution context
    triggered_by = Column(String(50), nullable=True)  # 'manual', 'schedule', 'api'
    triggered_by_user = Column(Integer, nullable=True)
    execution_context = Column(JSON, nullable=True)  # Additional context
    
    # Timestamps
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Execution summary
    total_targets = Column(Integer, nullable=False, default=0)
    successful_targets = Column(Integer, nullable=False, default=0)
    failed_targets = Column(Integer, nullable=False, default=0)
    
    # Performance metrics
    execution_time_seconds = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    job = relationship("Job", back_populates="executions")
    results = relationship("JobExecutionResult", back_populates="execution", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_job_executions_job_status', 'job_id', 'status'),
        Index('idx_job_executions_started_at', 'started_at'),
        Index('idx_job_executions_status_created', 'status', 'created_at'),
    )


class JobExecutionResult(Base):
    """Detailed execution results per target per action"""
    __tablename__ = "job_execution_results"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("job_executions.id", ondelete="CASCADE"), nullable=False)
    
    # Target information
    target_id = Column(Integer, nullable=False)
    target_name = Column(String(255), nullable=False)  # Denormalized for performance
    
    # Action information
    action_id = Column(Integer, ForeignKey("job_actions.id"), nullable=False)
    action_order = Column(Integer, nullable=False)
    action_name = Column(String(255), nullable=False)
    action_type = Column(Enum(ActionType), nullable=False)
    
    # Execution details
    status = Column(Enum(ExecutionStatus), nullable=False, default=ExecutionStatus.SCHEDULED, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    
    # Results
    output_text = Column(Text, nullable=True)
    error_text = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    command_executed = Column(Text, nullable=True)
    
    # Connection details
    connection_method = Column(String(50), nullable=True)  # ssh, winrm
    connection_host = Column(String(255), nullable=True)
    connection_port = Column(Integer, nullable=True)
    
    # Retry information
    retry_count = Column(Integer, default=0)
    is_retry = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    execution = relationship("JobExecution", back_populates="results")
    action = relationship("JobAction")

    # Indexes
    __table_args__ = (
        Index('idx_execution_results_execution_id', 'execution_id'),
        Index('idx_execution_results_target_id', 'target_id'),
        Index('idx_execution_results_status', 'status'),
        Index('idx_execution_results_execution_target', 'execution_id', 'target_id'),
    )


# =============================================================================
# SCHEDULING MODELS
# =============================================================================

class JobSchedule(Base):
    """Job scheduling configuration"""
    __tablename__ = "job_schedules"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    # Schedule configuration
    schedule_type = Column(Enum(ScheduleType), nullable=False)
    enabled = Column(Boolean, default=True, index=True)
    
    # One-time scheduling
    execute_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Recurring scheduling
    recurring_type = Column(Enum(RecurringType), nullable=True)
    interval = Column(Integer, default=1)
    time = Column(String(8), nullable=True)  # HH:MM format
    days_of_week = Column(String(20), nullable=True)  # Comma-separated: 0,1,2,3,4,5,6
    day_of_month = Column(Integer, nullable=True)  # 1-31
    
    # Cron scheduling
    cron_expression = Column(String(100), nullable=True)
    
    # Advanced options
    timezone = Column(String(50), default="UTC")
    max_executions = Column(Integer, nullable=True)
    execution_count = Column(Integer, default=0)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Schedule state
    next_run = Column(DateTime(timezone=True), nullable=True, index=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    last_execution_id = Column(Integer, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="schedules")
    executions = relationship("ScheduleExecution", back_populates="schedule", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_job_schedules_enabled_next_run', 'enabled', 'next_run'),
        Index('idx_job_schedules_job_id', 'job_id'),
    )


class ScheduleExecution(Base):
    """Track individual schedule executions"""
    __tablename__ = "schedule_executions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Schedule relationship
    schedule_id = Column(Integer, ForeignKey("job_schedules.id", ondelete="CASCADE"), nullable=False)
    job_execution_id = Column(Integer, ForeignKey("job_executions.id"), nullable=True)
    
    # Execution details
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(ExecutionStatus), nullable=False, default=ExecutionStatus.SCHEDULED, index=True)
    
    # Results
    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_context = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    schedule = relationship("JobSchedule", back_populates="executions")
    job_execution = relationship("JobExecution")

    # Indexes
    __table_args__ = (
        Index('idx_schedule_executions_schedule_id', 'schedule_id'),
        Index('idx_schedule_executions_scheduled_at', 'scheduled_at'),
        Index('idx_schedule_executions_status', 'status'),
    )