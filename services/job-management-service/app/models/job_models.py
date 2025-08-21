"""
Job Management Service Database Models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import uuid

from app.core.database import Base
from opsconductor_shared.models.base import JobType, JobStatus, ActionType


class Job(Base):
    """Job definition model"""
    __tablename__ = "jobs"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Job configuration
    job_type = Column(String(50), nullable=False, default=JobType.COMMAND.value)
    status = Column(String(50), nullable=False, default=JobStatus.DRAFT.value, index=True)
    priority = Column(Integer, default=5, index=True)
    timeout_seconds = Column(Integer)
    max_retries = Column(Integer, default=0)
    
    # Metadata
    tags = Column(JSON)
    metadata = Column(JSON)
    
    # Audit fields
    created_by = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    
    # Execution tracking
    last_execution_at = Column(DateTime(timezone=True))
    execution_count = Column(Integer, default=0)
    
    # Relationships
    actions = relationship("JobAction", back_populates="job", cascade="all, delete-orphan")
    targets = relationship("JobTarget", back_populates="job", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_jobs_status_created', 'status', 'created_at'),
        Index('idx_jobs_created_by_status', 'created_by', 'status'),
        Index('idx_jobs_type_status', 'job_type', 'status'),
    )


class JobAction(Base):
    """Job action model"""
    __tablename__ = "job_actions"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    action_order = Column(Integer, nullable=False)
    
    # Action definition
    action_type = Column(String(50), nullable=False, default=ActionType.COMMAND.value)
    action_name = Column(String(255), nullable=False)
    action_parameters = Column(JSON)
    action_config = Column(JSON)
    
    # Safety and validation
    is_dangerous = Column(Boolean, default=False)
    requires_confirmation = Column(Boolean, default=False)
    
    # Relationships
    job = relationship("Job", back_populates="actions")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_actions_job_order', 'job_id', 'action_order'),
    )


class JobTarget(Base):
    """Job target association model"""
    __tablename__ = "job_targets"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(Integer, nullable=False, index=True)
    
    # Target metadata (cached from target service)
    target_name = Column(String(255))
    target_type = Column(String(100))
    target_host = Column(String(255))
    
    # Relationships
    job = relationship("Job", back_populates="targets")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_targets_job_target', 'job_id', 'target_id'),
    )