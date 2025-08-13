#!/usr/bin/env python3
"""
ENABLEDRM Job Scheduler
Handles execution of scheduled jobs according to the architecture plan.
"""

import logging
import time
import sys
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.job_models import Job, JobStatus
from app.services.job_service import JobService
from app.schemas.job_schemas import JobExecuteRequest
from app.tasks.cleanup_tasks import run_stale_execution_cleanup, run_system_health_check

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobScheduler:
    """Job scheduler that monitors and executes scheduled jobs"""
    
    def __init__(self):
        self.running = False
        self.check_interval = 30  # Check every 30 seconds
        self.cleanup_interval = 3600  # Run cleanup every hour (3600 seconds)
        self.last_cleanup = 0  # Track last cleanup time
        
    def get_db(self) -> Session:
        """Get database session"""
        return SessionLocal()
    
    def get_scheduled_jobs(self, db: Session) -> List[Job]:
        """Get all jobs that are scheduled and ready to execute"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Get jobs that are scheduled and past their scheduled time
            scheduled_jobs = db.query(Job).filter(
                Job.status == JobStatus.SCHEDULED,
                Job.scheduled_at <= current_time
            ).all()
            
            logger.info(
                f"Found {len(scheduled_jobs)} scheduled jobs ready for execution"
            )
            return scheduled_jobs
            
        except Exception as e:
            logger.error(f"Error getting scheduled jobs: {str(e)}")
            return []
    
    def execute_job(self, job: Job, db: Session) -> bool:
        """Execute a scheduled job"""
        try:
            logger.info(f"Executing scheduled job: {job.name} (ID: {job.id})")
            
            # Update job status to running
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            db.commit()
            
            # Create job execution
            job_service = JobService(db)
            
            # Execute the job using the job service
            execute_data = JobExecuteRequest(target_ids=None)  # Use all targets
            execution = job_service.execute_job(
                job_id=job.id,
                execute_data=execute_data
            )
            # Determine targets
            target_ids = job_service.get_job_target_ids(job.id)
            from app.tasks.job_tasks import execute_job_task
            task = execute_job_task.delay(execution.id, target_ids)
            logger.info(f"Job {job.name} execution queued: execution_id={execution.id}, task_id={task.id}, targets={target_ids}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing job {job.id}: {str(e)}")
            
            # Update job status to failed
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            
            return False
    
    def process_scheduled_jobs(self):
        """Process all scheduled jobs that are ready to execute"""
        db = self.get_db()
        try:
            scheduled_jobs = self.get_scheduled_jobs(db)
            
            for job in scheduled_jobs:
                success = self.execute_job(job, db)
                if success:
                    logger.info(
                f"Successfully started execution of job: {job.name}"
            )
                else:
                    logger.error(f"Failed to execute job: {job.name}")
                    
        except Exception as e:
            logger.error(f"Error processing scheduled jobs: {str(e)}")
        finally:
            db.close()
    
    def run_maintenance_tasks(self):
        """Run periodic maintenance tasks"""
        current_time = time.time()
        
        # Run cleanup tasks every hour
        if current_time - self.last_cleanup >= self.cleanup_interval:
            logger.info("Running scheduled maintenance tasks...")
            
            try:
                # Clean up stale executions
                cleaned_count = run_stale_execution_cleanup()
                if cleaned_count > 0:
                    logger.warning(f"Cleaned up {cleaned_count} stale executions")
                
                # Run system health check
                health_metrics = run_system_health_check()
                logger.info(f"System health: {health_metrics.get('running_executions', 0)} running, "
                           f"{health_metrics.get('long_running_executions', 0)} long-running")
                
                self.last_cleanup = current_time
                
            except Exception as e:
                logger.error(f"Error running maintenance tasks: {str(e)}")
                # Still update last_cleanup to prevent continuous retries
                self.last_cleanup = current_time
    
    def run(self):
        """Main scheduler loop"""
        logger.info("🚀 ENABLEDRM Job Scheduler starting up...")
        self.running = True
        
        while self.running:
            try:
                # Process scheduled jobs
                self.process_scheduled_jobs()
                
                # Run maintenance tasks (cleanup, health checks)
                self.run_maintenance_tasks()
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Scheduler shutting down...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(self.check_interval)
        
        logger.info("Scheduler stopped")


def main():
    """Main entry point for the scheduler"""
    scheduler = JobScheduler()
    scheduler.run()


if __name__ == "__main__":
    main()
