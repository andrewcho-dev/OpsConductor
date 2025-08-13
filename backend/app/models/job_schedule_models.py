"""
Job Schedule Models - Database models for job scheduling
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum

from app.database.database import Base


class ScheduleType(enum.Enum):
    ONCE = "once"
    RECURRING = "recurring"
    CRON = "cron"


class RecurringType(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class JobSchedule(Base):
    """Job scheduling configuration"""
    __tablename__ = "job_schedules"

    id = Column(Integer, primary_key=True, index=True)
    schedule_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Job relationship
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    job = relationship("Job", back_populates="schedules")
    
    # Schedule configuration
    schedule_type = Column(String(20), nullable=False)  # once, recurring, cron
    enabled = Column(Boolean, default=True)
    
    # One-time scheduling
    execute_at = Column(DateTime(timezone=True), nullable=True)
    
    # Recurring scheduling
    recurring_type = Column(String(20), nullable=True)  # daily, weekly, monthly
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
    
    # Metadata
    description = Column(Text, nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<JobSchedule(id={self.id}, job_id={self.job_id}, type={self.schedule_type})>"


class ScheduleExecution(Base):
    """Track individual schedule executions"""
    __tablename__ = "schedule_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Schedule relationship
    schedule_id = Column(Integer, ForeignKey("job_schedules.id"), nullable=False)
    schedule = relationship("JobSchedule")
    
    # Job execution relationship
    job_execution_id = Column(Integer, ForeignKey("job_executions.id"), nullable=True)
    job_execution = relationship("JobExecution")
    
    # Execution details
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="pending")  # pending, executed, failed, skipped
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ScheduleExecution(id={self.id}, schedule_id={self.schedule_id}, status={self.status})>"