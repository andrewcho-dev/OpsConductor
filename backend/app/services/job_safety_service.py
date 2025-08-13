"""
Job Safety Service - Handles job timeouts, cleanup, and safety mechanisms
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.job_models import Job, JobExecution, JobStatus, ExecutionStatus
from app.models.universal_target_models import UniversalTarget

logger = logging.getLogger(__name__)


class JobSafetyService:
    """Service for job safety mechanisms and cleanup operations"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Safety thresholds
        self.JOB_TIMEOUT_MINUTES = 30  # Jobs timeout after 30 minutes
        self.EXECUTION_TIMEOUT_MINUTES = 25  # Executions timeout after 25 minutes
        self.STALE_THRESHOLD_HOURS = 2  # Consider jobs stale after 2 hours
    
    def cleanup_stale_jobs(self) -> dict:
        """
        Clean up jobs that are stuck in running state
        Returns summary of cleanup actions
        """
        logger.info("🧹 Starting stale job cleanup...")
        
        cleanup_summary = {
            "stale_jobs_found": 0,
            "stale_executions_found": 0,
            "jobs_cleaned": 0,
            "executions_cleaned": 0,
            "errors": []
        }
        
        try:
            # Find stale jobs (running for more than threshold)
            stale_threshold = datetime.now(timezone.utc) - timedelta(hours=self.STALE_THRESHOLD_HOURS)
            
            stale_jobs = self.db.query(Job).filter(
                Job.status == JobStatus.RUNNING,
                Job.started_at < stale_threshold
            ).all()
            
            cleanup_summary["stale_jobs_found"] = len(stale_jobs)
            logger.info(f"🔍 Found {len(stale_jobs)} stale jobs")
            
            for job in stale_jobs:
                try:
                    logger.warning(f"🚨 Cleaning up stale job {job.id}: {job.name}")
                    
                    # Update job status
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now(timezone.utc)
                    job.updated_at = datetime.now(timezone.utc)
                    
                    # Log the cleanup action
                    logger.warning(f"Job {job.id} cleaned up due to stale state (running for {self.STALE_THRESHOLD_HOURS}+ hours)")
                    
                    cleanup_summary["jobs_cleaned"] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to cleanup job {job.id}: {str(e)}"
                    logger.error(error_msg)
                    cleanup_summary["errors"].append(error_msg)
            
            # Find stale executions
            stale_executions = self.db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.RUNNING,
                JobExecution.started_at < stale_threshold
            ).all()
            
            cleanup_summary["stale_executions_found"] = len(stale_executions)
            logger.info(f"🔍 Found {len(stale_executions)} stale executions")
            
            for execution in stale_executions:
                try:
                    logger.warning(f"🚨 Cleaning up stale execution {execution.id}")
                    
                    # Update execution status
                    execution.status = ExecutionStatus.FAILED
                    execution.completed_at = datetime.now(timezone.utc)
                    execution.updated_at = datetime.now(timezone.utc)
                    execution.error_message = "Execution timed out and was automatically cleaned up"
                    
                    # Log the cleanup action
                    logger.warning(f"Execution {execution.id} cleaned up due to stale state")
                    
                    cleanup_summary["executions_cleaned"] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to cleanup execution {execution.id}: {str(e)}"
                    logger.error(error_msg)
                    cleanup_summary["errors"].append(error_msg)
            
            # Commit all changes
            self.db.commit()
            
            logger.info(f"✅ Cleanup completed: {cleanup_summary}")
            return cleanup_summary
            
        except Exception as e:
            logger.error(f"❌ Error during stale job cleanup: {str(e)}")
            self.db.rollback()
            cleanup_summary["errors"].append(f"General cleanup error: {str(e)}")
            return cleanup_summary
    
    def force_terminate_job(self, job_id: int, reason: str = "Manual termination") -> bool:
        """
        Force terminate a running job
        """
        try:
            job = self.db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"❌ Job {job_id} not found")
                return False
            
            logger.info(f"🔍 Job {job_id} current status: {job.status} (type: {type(job.status)})")
            logger.info(f"🔍 JobStatus.RUNNING: {JobStatus.RUNNING} (type: {type(JobStatus.RUNNING)})")
            
            if job.status != JobStatus.RUNNING:
                logger.warning(f"⚠️ Job {job_id} is not running (status: {job.status})")
                # Let's be more lenient and allow termination of jobs that might be stuck
                if job.status in [JobStatus.SCHEDULED, JobStatus.PAUSED]:
                    logger.info(f"🔄 Allowing termination of job {job_id} with status {job.status}")
                else:
                    return False
            
            logger.info(f"🛑 Force terminating job {job_id}: {job.name}")
            
            # Update job status
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)
            
            # Update any running executions
            running_executions = self.db.query(JobExecution).filter(
                JobExecution.job_id == job_id,
                JobExecution.status == ExecutionStatus.RUNNING
            ).all()
            
            for execution in running_executions:
                execution.status = ExecutionStatus.CANCELLED
                execution.completed_at = datetime.now(timezone.utc)
                execution.updated_at = datetime.now(timezone.utc)
                execution.error_message = reason
            
            # Log the termination
            logger.warning(f"Job {job_id} force terminated: {reason}")
            
            self.db.commit()
            logger.info(f"✅ Job {job_id} successfully terminated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error terminating job {job_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def get_job_health_status(self) -> dict:
        """
        Get overall job system health status
        """
        try:
            # Count jobs by status
            job_counts = {}
            for status in JobStatus:
                count = self.db.query(Job).filter(Job.status == status).count()
                job_counts[status.value] = count
            
            # Count executions by status
            execution_counts = {}
            for status in ExecutionStatus:
                count = self.db.query(JobExecution).filter(JobExecution.status == status).count()
                execution_counts[status.value] = count
            
            # Find long-running jobs
            long_running_threshold = datetime.now(timezone.utc) - timedelta(minutes=self.JOB_TIMEOUT_MINUTES)
            long_running_jobs = self.db.query(Job).filter(
                Job.status == JobStatus.RUNNING,
                Job.started_at < long_running_threshold
            ).count()
            
            # Find long-running executions
            long_running_executions = self.db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.RUNNING,
                JobExecution.started_at < long_running_threshold
            ).count()
            
            return {
                "job_counts": job_counts,
                "execution_counts": execution_counts,
                "long_running_jobs": long_running_jobs,
                "long_running_executions": long_running_executions,
                "health_status": "healthy" if long_running_jobs == 0 and long_running_executions == 0 else "warning"
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting job health status: {str(e)}")
            return {
                "error": str(e),
                "health_status": "error"
            }