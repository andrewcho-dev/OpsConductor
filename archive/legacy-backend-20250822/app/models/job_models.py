from sqlalchemy import (
    Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
import enum


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


class ActionType(str, enum.Enum):
    COMMAND = "command"
    SCRIPT = "script"
    FILE_TRANSFER = "file_transfer"


class Job(Base):
    """Simplified Job model - just basic info with auto-increment ID"""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
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
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    priority = Column(Integer, default=5, nullable=False)
    timeout = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    actions = relationship("JobAction", back_populates="job", cascade="all, delete-orphan")
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    targets = relationship("JobTarget", back_populates="job", cascade="all, delete-orphan")
    schedules = relationship("JobSchedule", back_populates="job", cascade="all, delete-orphan")


class JobTarget(Base):
    """Which targets this job should run on"""
    __tablename__ = "job_targets"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("universal_targets.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="targets")
    target = relationship("UniversalTarget")


class JobAction(Base):
    """Actions to perform in this job"""
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
    """Each time a job runs, create one execution record"""
    __tablename__ = "job_executions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    execution_number = Column(Integer, nullable=False)  # 1, 2, 3, 4... per job
    status = Column(
        Enum(ExecutionStatus, name='execution_status', values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False, default=ExecutionStatus.SCHEDULED
    )
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_targets = Column(Integer, nullable=False, default=0)
    successful_targets = Column(Integer, nullable=False, default=0)
    failed_targets = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="executions")
    results = relationship("JobExecutionResult", back_populates="execution", cascade="all, delete-orphan")


class JobExecutionResult(Base):
    """One record per target per action per execution - FLAT and SIMPLE"""
    __tablename__ = "job_execution_results"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("job_executions.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("universal_targets.id"), nullable=False)
    target_name = Column(String(255), nullable=False)  # Denormalized for easy searching
    action_id = Column(Integer, ForeignKey("job_actions.id"), nullable=False)
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
    execution_time_ms = Column(Integer, nullable=True)
    output_text = Column(Text, nullable=True)
    error_text = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    command_executed = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    execution = relationship("JobExecution", back_populates="results")
    target = relationship("UniversalTarget")
    action = relationship("JobAction")