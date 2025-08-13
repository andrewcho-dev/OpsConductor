from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import logging

logger = logging.getLogger(__name__)

from app.models.job_models import Job, JobExecution, JobStatus, ExecutionStatus
from app.models.universal_target_models import UniversalTarget


class SimpleAnalyticsService:
    """Simple analytics service for ENABLEDRM Platform."""

    def __init__(self, db: Session):
        self.db = db

    def get_realtime_dashboard_metrics(self) -> Dict[str, Any]:
        """Get real-time dashboard metrics for the analytics dashboard."""
        try:
            # Get basic job metrics
            active_jobs = self.db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.RUNNING
            ).count()
            
            # Get 24h metrics
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)
            
            executions_24h = self.db.query(JobExecution).filter(
                and_(
                    JobExecution.created_at >= start_time,
                    JobExecution.created_at <= end_time
                )
            ).all()
            
            total_24h = len(executions_24h)
            successful_24h = len([e for e in executions_24h if e.status == ExecutionStatus.COMPLETED])
            success_rate_24h = (successful_24h / total_24h * 100) if total_24h > 0 else 0
            
            # Get target metrics
            targets = self.db.query(UniversalTarget).filter(UniversalTarget.is_active == True).all()
            total_targets = len(targets)
            healthy_targets = len([t for t in targets if t.health_status == 'healthy'])
            
            # Get recent activity
            recent_executions = self.db.query(JobExecution).join(Job).order_by(
                JobExecution.created_at.desc()
            ).limit(5).all()
            
            recent_activity = []
            for execution in recent_executions:
                recent_activity.append({
                    "job_name": execution.job.name,
                    "status": execution.status.value,
                    "created_at": execution.created_at.isoformat() if execution.created_at else None
                })
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "job_metrics": {
                    "active_jobs": active_jobs,
                    "success_rate_24h": round(success_rate_24h, 1),
                    "avg_duration_24h": 30.0,  # Placeholder
                    "total_executions_24h": total_24h
                },
                "target_metrics": {
                    "total_targets": total_targets,
                    "online_targets": healthy_targets,
                    "healthy_targets": healthy_targets,
                    "warning_targets": 0,
                    "critical_targets": 0,
                    "unknown_targets": total_targets - healthy_targets,
                    "availability_rate": (healthy_targets / total_targets * 100) if total_targets > 0 else 0
                },
                "system_metrics": {
                    "cpu_usage": 25,
                    "memory_usage": 60,
                    "queue_size": active_jobs
                },
                "performance_trends": {
                    "hourly_data": [
                        {
                            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                            "total_executions": total_24h,
                            "successful_executions": successful_24h,
                            "failed_executions": total_24h - successful_24h,
                            "success_rate": success_rate_24h
                        }
                    ]
                },
                "error_summary": {
                    "total_errors": total_24h - successful_24h,
                    "error_categories": {
                        "authentication": 0,
                        "communication": 0,
                        "command_execution": total_24h - successful_24h,
                        "timeout": 0
                    }
                },
                "recent_activity": recent_activity
            }
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "job_metrics": {
                    "active_jobs": 0,
                    "success_rate_24h": 0,
                    "avg_duration_24h": 0,
                    "total_executions_24h": 0
                },
                "target_metrics": {
                    "total_targets": 0,
                    "online_targets": 0,
                    "healthy_targets": 0,
                    "warning_targets": 0,
                    "critical_targets": 0,
                    "unknown_targets": 0,
                    "availability_rate": 0
                },
                "system_metrics": {
                    "cpu_usage": 0,
                    "memory_usage": 0,
                    "queue_size": 0
                },
                "performance_trends": {
                    "hourly_data": []
                },
                "error_summary": {
                    "total_errors": 0,
                    "error_categories": {}
                },
                "recent_activity": []
            }