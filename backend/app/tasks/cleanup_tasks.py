"""
Cleanup tasks for maintaining database integrity and preventing stale data.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List

# Import celery_app at the bottom to avoid circular imports
from app.database.database import get_db, SessionLocal
from app.models.job_models import JobExecution, JobExecutionBranch, ExecutionStatus
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CleanupTasks:
    """Tasks for cleaning up stale data and maintaining system health"""
    
    @staticmethod
    def cleanup_stale_executions(max_runtime_hours: int = 24) -> int:
        """
        Clean up executions that have been running for too long.
        
        Args:
            max_runtime_hours: Maximum hours an execution should run before being considered stale
            
        Returns:
            Number of executions cleaned up
        """
        db: Session = next(get_db())
        cleaned_count = 0
        
        try:
            # Calculate cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_runtime_hours)
            
            # Find stale executions
            stale_executions = db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.RUNNING,
                JobExecution.started_at < cutoff_time,
                JobExecution.completed_at.is_(None)
            ).all()
            
            logger.info(f"Found {len(stale_executions)} stale executions to clean up")
            
            for execution in stale_executions:
                runtime_hours = (datetime.now(timezone.utc) - execution.started_at).total_seconds() / 3600
                logger.warning(f"Cleaning up stale execution {execution.id} (Job {execution.job_id}, "
                             f"Execution #{execution.execution_number}) - Runtime: {runtime_hours:.1f} hours")
                
                # Update execution status
                execution.status = ExecutionStatus.FAILED
                execution.completed_at = datetime.now(timezone.utc)
                
                # Also update any running branches for this execution
                for branch in execution.branches:
                    if branch.status == ExecutionStatus.RUNNING:
                        logger.info(f"Cleaning up stale branch {branch.id} for target {branch.target_id}")
                        branch.status = ExecutionStatus.FAILED
                        branch.completed_at = datetime.now(timezone.utc)
                        branch.result_error = "Execution timed out - marked as failed by cleanup task"
                
                cleaned_count += 1
            
            # Commit changes
            db.commit()
            
            if cleaned_count > 0:
                logger.info(f"Successfully cleaned up {cleaned_count} stale executions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during stale execution cleanup: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    @staticmethod
    def cleanup_old_logs(days_to_keep: int = 30) -> int:
        """
        Clean up old execution logs to prevent database bloat.
        
        Args:
            days_to_keep: Number of days of logs to keep
            
        Returns:
            Number of log entries deleted
        """
        # TODO: Implement log cleanup when log retention policy is defined
        logger.info(f"Log cleanup not yet implemented (would clean logs older than {days_to_keep} days)")
        return 0
    
    @staticmethod
    def get_system_health_metrics() -> dict:
        """
        Get system health metrics for monitoring.
        
        Returns:
            Dictionary with health metrics
        """
        db: Session = next(get_db())
        
        try:
            # Count executions by status
            running_count = db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.RUNNING
            ).count()
            
            scheduled_count = db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.SCHEDULED
            ).count()
            
            # Find long-running executions (over 1 hour)
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            long_running_count = db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.RUNNING,
                JobExecution.started_at < one_hour_ago
            ).count()
            
            # Count executions from last 24 hours
            yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_executions = db.query(JobExecution).filter(
                JobExecution.created_at >= yesterday
            ).count()
            
            return {
                "running_executions": running_count,
                "scheduled_executions": scheduled_count,
                "long_running_executions": long_running_count,
                "recent_executions_24h": recent_executions,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system health metrics: {str(e)}")
            raise
        finally:
            db.close()


# Convenience functions for use in schedulers
def run_stale_execution_cleanup():
    """Run stale execution cleanup - for use in schedulers"""
    try:
        cleaned_count = CleanupTasks.cleanup_stale_executions(max_runtime_hours=24)
        logger.info(f"Scheduled cleanup completed: {cleaned_count} executions cleaned")
        return cleaned_count
    except Exception as e:
        logger.error(f"Scheduled cleanup failed: {str(e)}")
        return 0


def run_system_health_check():
    """Run system health check - for use in schedulers"""
    try:
        metrics = CleanupTasks.get_system_health_metrics()
        logger.info(f"System health check: {metrics}")
        
        # Alert if there are too many long-running executions
        if metrics["long_running_executions"] > 5:
            logger.warning(f"High number of long-running executions: {metrics['long_running_executions']}")
        
        return metrics
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return {}


