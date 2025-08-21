"""
Job models for Job Service
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import uuid


class JobType(str, enum.Enum):
    """Job type enumeration"""
    COMMAND = "command"
    SCRIPT = "script"
    FILE_TRANSFER = "file_transfer"
    COMPOSITE = "composite"
    DISCOVERY = "discovery"
    HEALTH_CHECK = "health_check"


class JobStatus(str, enum.Enum):
    """Job status enumeration"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    DELETED = "deleted"


class ExecutionStatus(str, enum.Enum):
    """Execution status enumeration"""
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRY = "retry"


class ActionType(str, enum.Enum):
    """Action type enumeration"""
    COMMAND = "command"
    SCRIPT = "script"
    FILE_TRANSFER = "file_transfer"
    WAIT = "wait"
    CONDITION = "condition"


class ScheduleType(str, enum.Enum):
    """Schedule type enumeration"""
    ONCE = "once"
    RECURRING = "recurring"
    CRON = "cron"
    INTERVAL = "interval"


class Job(Base):
    """
    Job model for job management
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    job_type = Column(Enum(JobType), nullable=False, default=JobType.COMMAND, index=True)
    
    # Status and Lifecycle
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.DRAFT, index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    
    # Ownership and Creation
    created_by = Column(Integer, nullable=False, index=True)  # User ID from User Service
    organization_id = Column(Integer, nullable=True, index=True)  # Organization ID
    
    # Execution Configuration
    priority = Column(Integer, default=5, nullable=False, index=True)  # 1-10, 10 is highest
    timeout_minutes = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Execution Control
    parallel_execution = Column(Boolean, default=False)  # Execute on targets in parallel
    continue_on_error = Column(Boolean, default=False)   # Continue if one target fails
    
    # Metadata and Configuration
    metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    environment_variables = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Execution Timestamps
    last_executed_at = Column(DateTime(timezone=True), nullable=True)
    next_execution_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Statistics
    total_executions = Column(Integer, default=0, nullable=False)
    successful_executions = Column(Integer, default=0, nullable=False)
    failed_executions = Column(Integer, default=0, nullable=False)
    
    # Relationships
    actions = relationship("JobAction", back_populates="job", cascade="all, delete-orphan", order_by="JobAction.action_order")
    targets = relationship("JobTarget", back_populates="job", cascade="all, delete-orphan")
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    schedules = relationship("JobSchedule", back_populates="job", cascade="all, delete-orphan")


class JobAction(Base):
    """
    Actions to perform in a job
    """
    __tablename__ = "job_actions"

    id = Column(Integer, primary_key=True, index=True)
    action_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Action Configuration
    action_order = Column(Integer, nullable=False, index=True)
    action_type = Column(Enum(ActionType), nullable=False, index=True)
    action_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Action Parameters
    command = Column(Text, nullable=True)  # For command actions
    script_content = Column(Text, nullable=True)  # For script actions
    script_language = Column(String(50), nullable=True)  # bash, python, powershell, etc.
    
    # File Transfer Parameters
    source_path = Column(String(1000), nullable=True)
    destination_path = Column(String(1000), nullable=True)
    transfer_mode = Column(String(20), nullable=True)  # upload, download
    
    # Execution Configuration
    timeout_minutes = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    continue_on_error = Column(Boolean, default=False)
    
    # Conditions and Dependencies
    condition_expression = Column(Text, nullable=True)  # For conditional execution
    depends_on_actions = Column(JSONB, nullable=True, default=list)  # Action IDs this depends on
    
    # Parameters and Configuration
    parameters = Column(JSONB, nullable=True, default=dict)
    environment_variables = Column(JSONB, nullable=True, default=dict)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="actions")


class JobTarget(Base):
    """
    Targets where the job should be executed
    """
    __tablename__ = "job_targets"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    target_id = Column(Integer, nullable=False, index=True)  # Target ID from Universal Targets Service
    
    # Target Information (denormalized for performance)
    target_name = Column(String(255), nullable=False, index=True)
    target_type = Column(String(50), nullable=True)
    target_host = Column(String(255), nullable=True)
    
    # Execution Configuration
    is_active = Column(Boolean, default=True)
    execution_order = Column(Integer, nullable=True)  # For sequential execution
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="targets")


class JobExecution(Base):
    """
    Job execution instances
    """
    __tablename__ = "job_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Execution Information
    execution_number = Column(Integer, nullable=False, index=True)  # Sequential number per job
    status = Column(Enum(ExecutionStatus), nullable=False, default=ExecutionStatus.SCHEDULED, index=True)
    
    # Execution Context
    triggered_by = Column(Integer, nullable=True)  # User ID who triggered the execution
    trigger_type = Column(String(50), nullable=True)  # manual, scheduled, api, webhook
    
    # Execution Configuration (snapshot from job at execution time)
    job_configuration = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Execution Statistics
    total_targets = Column(Integer, nullable=False, default=0)
    successful_targets = Column(Integer, nullable=False, default=0)
    failed_targets = Column(Integer, nullable=False, default=0)
    skipped_targets = Column(Integer, nullable=False, default=0)
    
    # Execution Results
    exit_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    
    # Relationships
    job = relationship("Job", back_populates="executions")
    results = relationship("JobExecutionResult", back_populates="execution", cascade="all, delete-orphan")


class JobExecutionResult(Base):
    """
    Detailed execution results per target per action
    """
    __tablename__ = "job_execution_results"

    id = Column(Integer, primary_key=True, index=True)
    result_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    execution_id = Column(Integer, ForeignKey("job_executions.id"), nullable=False, index=True)
    
    # Target Information
    target_id = Column(Integer, nullable=False, index=True)
    target_name = Column(String(255), nullable=False, index=True)
    
    # Action Information
    action_id = Column(Integer, ForeignKey("job_actions.id"), nullable=False, index=True)
    action_order = Column(Integer, nullable=False, index=True)
    action_name = Column(String(255), nullable=False)
    action_type = Column(Enum(ActionType), nullable=False, index=True)
    
    # Execution Status
    status = Column(Enum(ExecutionStatus), nullable=False, default=ExecutionStatus.SCHEDULED, index=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Execution Results
    exit_code = Column(Integer, nullable=True)
    output_text = Column(Text, nullable=True)
    error_text = Column(Text, nullable=True)
    command_executed = Column(Text, nullable=True)
    
    # File Transfer Results
    bytes_transferred = Column(Integer, nullable=True)
    transfer_rate_bps = Column(Integer, nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    
    # Relationships
    execution = relationship("JobExecution", back_populates="results")
    action = relationship("JobAction")


class JobSchedule(Base):
    """
    Job scheduling configuration
    """
    __tablename__ = "job_schedules"

    id = Column(Integer, primary_key=True, index=True)
    schedule_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Schedule Configuration
    schedule_type = Column(Enum(ScheduleType), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Schedule Parameters
    cron_expression = Column(String(100), nullable=True)  # For cron schedules
    interval_minutes = Column(Integer, nullable=True)     # For interval schedules
    
    # Time Configuration
    timezone = Column(String(50), default='UTC')
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Execution Limits
    max_executions = Column(Integer, nullable=True)  # Maximum number of executions
    current_executions = Column(Integer, default=0, nullable=False)
    
    # Next Execution
    next_run_time = Column(DateTime(timezone=True), nullable=True, index=True)
    last_run_time = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    
    # Relationships
    job = relationship("Job", back_populates="schedules")


class JobTemplate(Base):
    """
    Job templates for reusable job configurations
    """
    __tablename__ = "job_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Template Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    
    # Template Configuration
    job_type = Column(Enum(JobType), nullable=False, index=True)
    template_data = Column(JSONB, nullable=False)  # Complete job configuration
    
    # Template Metadata
    is_public = Column(Boolean, default=False)  # Available to all users
    is_system = Column(Boolean, default=False)  # System template
    
    # Usage Statistics
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Ownership
    created_by = Column(Integer, nullable=False, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class JobQueue(Base):
    """
    Job queue management for execution ordering
    """
    __tablename__ = "job_queues"

    id = Column(Integer, primary_key=True, index=True)
    queue_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Queue Information
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Queue Configuration
    max_concurrent_jobs = Column(Integer, default=5, nullable=False)
    current_running_jobs = Column(Integer, default=0, nullable=False)
    priority = Column(Integer, default=5, nullable=False)  # Queue priority
    
    # Queue Status
    is_active = Column(Boolean, default=True, index=True)
    is_paused = Column(Boolean, default=False, index=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=True)