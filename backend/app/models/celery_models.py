"""
Celery Task History Models
For tracking task execution statistics and metrics
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
from app.database.database import Base

class CeleryTaskHistory(Base):
    """Store completed Celery task information for metrics"""
    __tablename__ = "celery_task_history"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, index=True, nullable=False)
    task_name = Column(String(255), index=True, nullable=False)
    worker_name = Column(String(255), index=True)
    queue_name = Column(String(100), index=True)
    
    # Timing information
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration = Column(Float)  # Duration in seconds
    
    # Status and result
    status = Column(String(50), index=True)  # SUCCESS, FAILURE, RETRY, REVOKED
    result = Column(Text)  # Task result or error message
    exception = Column(Text)  # Exception details if failed
    traceback = Column(Text)  # Full traceback if failed
    
    # Task details
    args = Column(Text)  # JSON string of task arguments
    kwargs = Column(Text)  # JSON string of task keyword arguments
    retries = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<CeleryTaskHistory(task_id='{self.task_id}', name='{self.task_name}', status='{self.status}')>"

class CeleryMetricsSnapshot(Base):
    """Store periodic snapshots of Celery metrics for historical charts"""
    __tablename__ = "celery_metrics_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    # Task metrics
    active_tasks = Column(Integer, default=0)
    scheduled_tasks = Column(Integer, default=0)
    completed_tasks_last_hour = Column(Integer, default=0)
    failed_tasks_last_hour = Column(Integer, default=0)
    tasks_per_minute = Column(Float, default=0.0)
    avg_task_duration = Column(Float, default=0.0)
    
    # Worker metrics
    total_workers = Column(Integer, default=0)
    active_workers = Column(Integer, default=0)
    avg_worker_load = Column(Float, default=0.0)
    
    # Queue metrics (JSON string with queue depths)
    queue_depths = Column(Text)  # JSON: {"celery": 5, "job_execution": 2}
    
    # Error rates
    error_rate = Column(Float, default=0.0)
    success_rate = Column(Float, default=100.0)
    
    def __repr__(self):
        return f"<CeleryMetricsSnapshot(timestamp='{self.timestamp}', active_tasks={self.active_tasks})>"