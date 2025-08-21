"""
Job Execution Service Database Models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime, timezone
import uuid

from app.core.database import Base
from opsconductor_shared.models.base import ExecutionStatus, ActionType


class JobExecution(Base):
    """Job execution instance model"""
    __tablename__ = "job_executions"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Job reference (from job management service)
    job_id = Column(Integer, nullable=False, index=True)
    job_uuid = Column(UUID(as_uuid=True), nullable=False, index=True)
    execution_number = Column(Integer, nullable=False)
    
    # Execution metadata
    status = Column(String(50), nullable=False, default=ExecutionStatus.SCHEDULED.value, index=True)
    triggered_by = Column(String(100))  # manual, schedule, api, etc.
    triggered_by_user = Column(Integer, index=True)
    execution_context = Column(JSON)
    
    # Timing
    scheduled_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True), index=True)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Results summary
    total_targets = Column(Integer, default=0)
    successful_targets = Column(Integer, default=0)
    failed_targets = Column(Integer, default=0)
    execution_time_seconds = Column(Float)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Indexes
    __table_args__ = (
        Index('idx_executions_job_status', 'job_id', 'status'),
        Index('idx_executions_status_created', 'status', 'created_at'),
        Index('idx_executions_user_created', 'triggered_by_user', 'created_at'),
    )


class JobExecutionResult(Base):
    """Individual target execution result model"""
    __tablename__ = "job_execution_results"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, nullable=False, index=True)
    
    # Target information
    target_id = Column(Integer, nullable=False, index=True)
    target_name = Column(String(255), nullable=False)
    
    # Action information
    action_id = Column(Integer, nullable=False)
    action_order = Column(Integer, nullable=False)
    action_name = Column(String(255), nullable=False)
    action_type = Column(String(50), nullable=False)
    
    # Execution details
    status = Column(String(50), nullable=False, default=ExecutionStatus.SCHEDULED.value, index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    execution_time_ms = Column(Integer)
    
    # Results
    output_text = Column(Text)
    error_text = Column(Text)
    exit_code = Column(Integer)
    command_executed = Column(Text)
    
    # Connection details
    connection_method = Column(String(50))  # ssh, winrm, etc.
    connection_host = Column(String(255))
    connection_port = Column(Integer)
    
    # Retry information
    retry_count = Column(Integer, default=0)
    is_retry = Column(Boolean, default=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_results_execution_target', 'execution_id', 'target_id'),
        Index('idx_results_execution_action', 'execution_id', 'action_order'),
        Index('idx_results_status_completed', 'status', 'completed_at'),
    )