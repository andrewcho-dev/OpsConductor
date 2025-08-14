from sqlalchemy import (
    Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.database.database import Base
import enum
import uuid


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


class ExecutionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionType(str, enum.Enum):
    COMMAND = "command"
    SCRIPT = "script"
    FILE_TRANSFER = "file_transfer"


class LogPhase(str, enum.Enum):
    CREATION = "creation"
    TARGET_SELECTION = "target_selection"
    AUTHENTICATION = "authentication"
    COMMUNICATION = "communication"
    ACTION_EXECUTION = "action_execution"
    RESULT_COLLECTION = "result_collection"
    COMPLETION = "completion"


class LogLevel(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class LogCategory(str, enum.Enum):
    AUTHENTICATION = "authentication"
    COMMUNICATION = "communication"
    COMMAND_EXECUTION = "command_execution"
    FILE_TRANSFER = "file_transfer"
    SYSTEM = "system"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    job_serial = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    job_type = Column(
        Enum(JobType, name='job_type', values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False, default=JobType.COMMAND
    )
    status = Column(
        Enum(JobStatus, name='job_status', values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False, default=JobStatus.DRAFT
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    actions = relationship("JobAction", back_populates="job", cascade="all, delete-orphan")
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    targets = relationship("JobTarget", back_populates="job", cascade="all, delete-orphan")
    schedules = relationship("JobSchedule", back_populates="job", cascade="all, delete-orphan")


class JobTarget(Base):
    __tablename__ = "job_targets"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("universal_targets.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="targets")
    target = relationship("UniversalTarget")


class JobAction(Base):
    __tablename__ = "job_actions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    action_order = Column(Integer, nullable=False)
    action_type = Column(
        Enum(ActionType, name='action_type', values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False
    )
    action_name = Column(String(255), nullable=False)
    action_parameters = Column(JSON, nullable=True)
    action_config = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="actions")


class JobExecution(Base):
    __tablename__ = "job_executions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    execution_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    execution_serial = Column(String(50), unique=True, nullable=False, index=True)
    execution_number = Column(Integer, nullable=False)
    status = Column(
        Enum(ExecutionStatus, name='execution_status', values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False, default=ExecutionStatus.SCHEDULED
    )
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="executions")
    branches = relationship("JobExecutionBranch", back_populates="execution", cascade="all, delete-orphan")
    logs = relationship("JobExecutionLog", back_populates="execution", cascade="all, delete-orphan")


class JobExecutionBranch(Base):
    __tablename__ = "job_execution_branches"

    id = Column(Integer, primary_key=True, index=True)
    job_execution_id = Column(Integer, ForeignKey("job_executions.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("universal_targets.id"), nullable=False)
    branch_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    branch_serial = Column(String(100), unique=True, nullable=False, index=True)
    branch_id = Column(String(10), nullable=False)  # 001, 002, 003, etc.
    target_serial_ref = Column(String(50), nullable=True, index=True)  # Reference to target serial
    status = Column(
        Enum(ExecutionStatus, name='execution_status', values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False, default=ExecutionStatus.SCHEDULED
    )
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result_output = Column(Text, nullable=True)
    result_error = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    execution = relationship("JobExecution", back_populates="branches")
    target = relationship("UniversalTarget")
    logs = relationship("JobExecutionLog", back_populates="branch", cascade="all, delete-orphan")
    action_results = relationship("JobActionResult", back_populates="branch", cascade="all, delete-orphan")


class JobActionResult(Base):
    __tablename__ = "job_action_results"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("job_execution_branches.id"), nullable=False)
    action_id = Column(Integer, ForeignKey("job_actions.id"), nullable=False)
    action_serial = Column(String(100), unique=True, nullable=False, index=True)  # J20250000001.0001.0001.0001
    action_order = Column(Integer, nullable=False)
    action_name = Column(String(255), nullable=False)
    action_type = Column(
        Enum(ActionType, name='action_type', values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False
    )
    status = Column(
        Enum(ExecutionStatus, name='execution_status', values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False, default=ExecutionStatus.SCHEDULED
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_time_ms = Column(Integer, nullable=True)  # Execution time in milliseconds
    result_output = Column(Text, nullable=True)
    result_error = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    command_executed = Column(Text, nullable=True)  # The actual command that was executed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    branch = relationship("JobExecutionBranch", back_populates="action_results")
    action = relationship("JobAction")


class JobExecutionLog(Base):
    __tablename__ = "job_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_execution_id = Column(Integer, ForeignKey("job_executions.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("job_execution_branches.id"), nullable=True)
    log_phase = Column(Enum(LogPhase, name='logphase', values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    log_level = Column(Enum(LogLevel, name='loglevel', values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=LogLevel.INFO)
    log_category = Column(Enum(LogCategory, name='logcategory', values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    log_message = Column(Text, nullable=False)
    log_details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    execution = relationship("JobExecution", back_populates="logs")
    branch = relationship("JobExecutionBranch", back_populates="logs")
