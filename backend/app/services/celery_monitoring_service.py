"""
Celery Task Monitoring Service
Handles task history tracking and metrics collection
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.celery_models import CeleryTaskHistory, CeleryMetricsSnapshot
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

class CeleryMonitoringService:
    def __init__(self, db: Session):
        self.db = db

    def record_task_completion(
        self,
        task_id: str,
        task_name: str,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration: Optional[float] = None,
        worker_name: Optional[str] = None,
        queue_name: Optional[str] = None,
        result: Optional[str] = None,
        exception: Optional[str] = None,
        traceback: Optional[str] = None,
        args: Optional[str] = None,
        kwargs: Optional[str] = None,
        retries: int = 0
    ) -> CeleryTaskHistory:
        """Record a completed task in the history"""
        try:
            # Check if task already exists
            existing_task = self.db.query(CeleryTaskHistory).filter(
                CeleryTaskHistory.task_id == task_id
            ).first()
            
            if existing_task:
                # Update existing record
                existing_task.status = status
                existing_task.completed_at = completed_at or datetime.now(timezone.utc)
                existing_task.duration = duration
                existing_task.result = result
                existing_task.exception = exception
                existing_task.traceback = traceback
                existing_task.retries = retries
                task_record = existing_task
            else:
                # Create new record
                task_record = CeleryTaskHistory(
                    task_id=task_id,
                    task_name=task_name,
                    worker_name=worker_name,
                    queue_name=queue_name,
                    started_at=started_at,
                    completed_at=completed_at or datetime.now(timezone.utc),
                    duration=duration,
                    status=status,
                    result=result,
                    exception=exception,
                    traceback=traceback,
                    args=args,
                    kwargs=kwargs,
                    retries=retries
                )
                self.db.add(task_record)
            
            self.db.commit()
            return task_record
            
        except Exception as e:
            logger.error(f"Error recording task completion: {e}")
            self.db.rollback()
            raise

    def get_recent_tasks(self, limit: int = 10) -> List[CeleryTaskHistory]:
        """Get recent completed tasks"""
        return self.db.query(CeleryTaskHistory).order_by(
            desc(CeleryTaskHistory.completed_at)
        ).limit(limit).all()

    def get_task_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get task statistics for the last N hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get task counts by status
        task_counts = self.db.query(
            CeleryTaskHistory.status,
            func.count(CeleryTaskHistory.id).label('count')
        ).filter(
            CeleryTaskHistory.completed_at >= cutoff_time
        ).group_by(CeleryTaskHistory.status).all()
        
        # Get average duration
        avg_duration = self.db.query(
            func.avg(CeleryTaskHistory.duration)
        ).filter(
            CeleryTaskHistory.completed_at >= cutoff_time,
            CeleryTaskHistory.duration.isnot(None)
        ).scalar() or 0.0
        
        # Get task counts by hour for rate calculation
        hourly_counts = self.db.query(
            func.date_trunc('hour', CeleryTaskHistory.completed_at).label('hour'),
            func.count(CeleryTaskHistory.id).label('count')
        ).filter(
            CeleryTaskHistory.completed_at >= cutoff_time
        ).group_by(func.date_trunc('hour', CeleryTaskHistory.completed_at)).all()
        
        # Calculate tasks per minute
        total_tasks = sum(count for _, count in hourly_counts)
        tasks_per_minute = total_tasks / (hours * 60) if hours > 0 else 0
        
        # Process status counts
        status_counts = {status: count for status, count in task_counts}
        total_completed = sum(status_counts.values())
        
        success_count = status_counts.get('SUCCESS', 0)
        failure_count = status_counts.get('FAILURE', 0)
        
        success_rate = (success_count / total_completed * 100) if total_completed > 0 else 100.0
        error_rate = (failure_count / total_completed * 100) if total_completed > 0 else 0.0
        
        return {
            'total_tasks': total_completed,
            'completed_tasks': success_count,
            'failed_tasks': failure_count,
            'avg_task_time': round(avg_duration, 2),
            'tasks_per_minute': round(tasks_per_minute, 2),
            'success_rate': round(success_rate, 1),
            'error_rate': round(error_rate, 1),
            'status_breakdown': status_counts
        }

    def get_task_types_stats(self, hours: int = 24) -> Dict[str, int]:
        """Get statistics by task type"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        task_types = self.db.query(
            CeleryTaskHistory.task_name,
            func.count(CeleryTaskHistory.id).label('count')
        ).filter(
            CeleryTaskHistory.completed_at >= cutoff_time
        ).group_by(CeleryTaskHistory.task_name).all()
        
        return {task_name: count for task_name, count in task_types}

    def create_metrics_snapshot(
        self,
        active_tasks: int = 0,
        scheduled_tasks: int = 0,
        total_workers: int = 0,
        active_workers: int = 0,
        avg_worker_load: float = 0.0,
        queue_depths: Dict[str, int] = None
    ) -> CeleryMetricsSnapshot:
        """Create a metrics snapshot for historical tracking"""
        try:
            # Get recent task statistics
            stats = self.get_task_statistics(hours=1)  # Last hour
            
            snapshot = CeleryMetricsSnapshot(
                active_tasks=active_tasks,
                scheduled_tasks=scheduled_tasks,
                completed_tasks_last_hour=stats['completed_tasks'],
                failed_tasks_last_hour=stats['failed_tasks'],
                tasks_per_minute=stats['tasks_per_minute'],
                avg_task_duration=stats['avg_task_time'],
                total_workers=total_workers,
                active_workers=active_workers,
                avg_worker_load=avg_worker_load,
                queue_depths=json.dumps(queue_depths or {}),
                error_rate=stats['error_rate'],
                success_rate=stats['success_rate']
            )
            
            self.db.add(snapshot)
            self.db.commit()
            return snapshot
            
        except Exception as e:
            logger.error(f"Error creating metrics snapshot: {e}")
            self.db.rollback()
            raise

    def get_metrics_history(self, hours: int = 24) -> List[CeleryMetricsSnapshot]:
        """Get metrics snapshots for the last N hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        return self.db.query(CeleryMetricsSnapshot).filter(
            CeleryMetricsSnapshot.timestamp >= cutoff_time
        ).order_by(CeleryMetricsSnapshot.timestamp).all()

    def cleanup_old_data(self, days: int = 30):
        """Clean up old task history and metrics data"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Delete old task history
            deleted_tasks = self.db.query(CeleryTaskHistory).filter(
                CeleryTaskHistory.created_at < cutoff_time
            ).delete()
            
            # Delete old metrics snapshots
            deleted_snapshots = self.db.query(CeleryMetricsSnapshot).filter(
                CeleryMetricsSnapshot.timestamp < cutoff_time
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {deleted_tasks} old task records and {deleted_snapshots} old metric snapshots")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            self.db.rollback()
            raise

    def get_enhanced_celery_stats(self) -> Dict[str, Any]:
        """Get enhanced Celery statistics with real data"""
        try:
            # Get current active tasks from Celery
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active() or {}
            scheduled_tasks = inspect.scheduled() or {}
            
            total_active = sum(len(tasks) for tasks in active_tasks.values())
            total_scheduled = sum(len(tasks) for tasks in scheduled_tasks.values())
            
            # Get historical statistics
            stats = self.get_task_statistics(hours=24)
            recent_tasks = self.get_recent_tasks(limit=10)
            task_types = self.get_task_types_stats(hours=24)
            
            # Format recent tasks for frontend
            recent_tasks_formatted = []
            for task in recent_tasks:
                recent_tasks_formatted.append({
                    'id': task.task_id,
                    'name': task.task_name,
                    'worker': task.worker_name or 'Unknown',
                    'status': task.status,
                    'duration': task.duration or 0,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None
                })
            
            return {
                "active_tasks": total_active,
                "scheduled_tasks": total_scheduled,
                "reserved_tasks": 0,
                "total_tasks_today": stats['total_tasks'],
                "completed_tasks_today": stats['completed_tasks'],
                "failed_tasks_today": stats['failed_tasks'],
                "avg_task_time": stats['avg_task_time'],
                "tasks_per_minute": stats['tasks_per_minute'],
                "peak_tasks_per_minute": stats['tasks_per_minute'],  # Could be enhanced
                "worker_count": len(active_tasks.keys()),
                "queue_count": 3,  # Our predefined queues
                "recent_tasks": recent_tasks_formatted,
                "task_types": task_types,
                "error_rate": stats['error_rate'],
                "success_rate": stats['success_rate'],
                "uptime": 0.0,  # Could be enhanced
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced Celery stats: {e}")
            # Return basic stats on error
            return {
                "active_tasks": 0,
                "scheduled_tasks": 0,
                "reserved_tasks": 0,
                "total_tasks_today": 0,
                "completed_tasks_today": 0,
                "failed_tasks_today": 0,
                "avg_task_time": 0.0,
                "tasks_per_minute": 0.0,
                "peak_tasks_per_minute": 0.0,
                "worker_count": 0,
                "queue_count": 3,
                "recent_tasks": [],
                "task_types": {},
                "error_rate": 0.0,
                "success_rate": 100.0,
                "uptime": 0.0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }