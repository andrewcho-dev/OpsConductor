"""
Celery Task History Models
For tracking task execution statistics and metrics
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
from app.database.database import Base

class CeleryTaskHistory(Base):
    """Store completed Celery task information for metrics"""
    __tablename__ = "celery_task_history"
    
    id = Column(Integer, primary_key=True, index=True)
    task_uuid = Column(UUID, nullable=False, server_default=text("gen_random_uuid()"))
    task_serial = Column(String(50), nullable=False, server_default=text("'TASK-' || LPAD(nextval('celery_task_history_id_seq')::text, 8, '0')"))
    task_id = Column(String(255), nullable=False)
    task_name = Column(String(255), nullable=False)
    status = Column(Enum('pending', 'started', 'retry', 'failure', 'success', 'revoked', name='task_status'), nullable=False, default='pending')
    result = Column(Text, nullable=True)
    traceback = Column(Text, nullable=True)
    args = Column(JSONB, nullable=True)
    kwargs = Column(JSONB, nullable=True)
    eta = Column(DateTime(timezone=True), nullable=True)
    expires = Column(DateTime(timezone=True), nullable=True)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    queue = Column(String(100), nullable=True)
    routing_key = Column(String(100), nullable=True)
    worker = Column(String(255), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    
    def __repr__(self):
        return f"<CeleryTaskHistory(task_id='{self.task_id}', name='{self.task_name}', status='{self.status}')>"

class CeleryMetricsSnapshot(Base):
    """Store periodic snapshots of Celery metrics for historical charts"""
    __tablename__ = "celery_metrics_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    snapshot_uuid = Column(UUID, nullable=False, server_default=text("gen_random_uuid()"))
    snapshot_serial = Column(String(50), nullable=False, server_default=text("'SNAP-' || LPAD(nextval('celery_metrics_snapshots_id_seq')::text, 8, '0')"))
    worker_name = Column(String(255), nullable=False)
    active_tasks = Column(Integer, default=0)
    processed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    retried_tasks = Column(Integer, default=0)
    queue_lengths = Column(JSONB, nullable=True)
    worker_stats = Column(JSONB, nullable=True)
    system_load = Column(JSONB, nullable=True)
    memory_usage = Column(JSONB, nullable=True)
    snapshot_time = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    
    def __repr__(self):
        return f"<CeleryMetricsSnapshot(worker='{self.worker_name}', active_tasks={self.active_tasks})>"