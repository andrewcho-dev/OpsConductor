"""
Periodic Celery tasks for scheduled operations
"""

import logging
from datetime import datetime, timezone, timedelta
from app.core.celery_app import celery_app
from app.tasks.cleanup_tasks import CleanupTasks

from app.services.celery_monitoring_service import CeleryMonitoringService
from app.services.job_scheduling_service import JobSchedulingService
from app.services.job_service import JobService
from app.models.job_schedule_models import JobSchedule
from app.schemas.job_schemas import JobExecuteRequest
from app.database.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.periodic_tasks.cleanup_stale_executions_task")
def cleanup_stale_executions_task(self):
    """Celery task to clean up stale executions"""
    logger.info("🧹 Running scheduled stale execution cleanup...")
    
    try:
        cleaned_count = CleanupTasks.cleanup_stale_executions(max_runtime_hours=24)
        logger.info(f"✅ Scheduled cleanup completed: {cleaned_count} executions cleaned")
        return {"status": "success", "cleaned_count": cleaned_count}
    except Exception as e:
        logger.error(f"❌ Scheduled cleanup failed: {str(e)}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, name="app.tasks.periodic_tasks.system_health_check_task")
def system_health_check_task(self):
    """Celery task to run system health check"""
    logger.info("🏥 Running scheduled system health check...")
    
    try:
        metrics = CleanupTasks.get_system_health_metrics()
        logger.info(f"📊 System health metrics: {metrics}")
        
        # Alert if there are too many long-running executions
        if metrics.get("long_running_executions", 0) > 5:
            logger.warning(f"⚠️ High number of long-running executions: {metrics['long_running_executions']}")
        
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        logger.error(f"❌ System health check failed: {str(e)}")
        return {"status": "failed", "error": str(e)}





@celery_app.task(bind=True, name="app.tasks.periodic_tasks.collect_celery_metrics_task")
def collect_celery_metrics_task(self):
    """Celery task to collect and store metrics snapshots"""
    logger.info("📊 Running scheduled Celery metrics collection...")
    
    try:
        db = SessionLocal()
        try:
            monitoring_service = CeleryMonitoringService(db)
            
            # Get current Celery stats
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active() or {}
            scheduled_tasks = inspect.scheduled() or {}
            
            total_active = sum(len(tasks) for tasks in active_tasks.values())
            total_scheduled = sum(len(tasks) for tasks in scheduled_tasks.values())
            
            # Get worker stats
            stats_data = inspect.stats() or {}
            total_workers = len(stats_data.keys())
            active_workers = len([w for w in stats_data.keys() if stats_data[w]])
            
            # Calculate average worker load
            worker_loads = []
            for worker_name, worker_stats in stats_data.items():
                pool_info = worker_stats.get('pool', {})
                active_worker_tasks = len(active_tasks.get(worker_name, []))
                pool_size = pool_info.get('max-concurrency', 1)
                load = (active_worker_tasks / pool_size * 100) if pool_size > 0 else 0
                worker_loads.append(load)
            
            avg_worker_load = sum(worker_loads) / len(worker_loads) if worker_loads else 0.0
            
            # Get queue depths (simplified)
            queue_depths = {
                'celery': 0,
                'job_execution': 0,
                'default': 0
            }
            
            # Create metrics snapshot
            snapshot = monitoring_service.create_metrics_snapshot(
                active_tasks=total_active,
                scheduled_tasks=total_scheduled,
                total_workers=total_workers,
                active_workers=active_workers,
                avg_worker_load=avg_worker_load,
                queue_depths=queue_depths
            )
            
            logger.info(f"📈 Metrics snapshot created: {snapshot.id}")
            
            # Cleanup old data (keep 30 days)
            monitoring_service.cleanup_old_data(days=30)
            
            return {
                "status": "success", 
                "snapshot_id": snapshot.id,
                "active_tasks": total_active,
                "total_workers": total_workers
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Celery metrics collection failed: {str(e)}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, name="app.tasks.periodic_tasks.process_recurring_schedules_task")
def process_recurring_schedules_task(self):
    """Celery task to process recurring job schedules"""
    logger.info("⏰ Processing recurring job schedules...")
    
    try:
        db = SessionLocal()
        try:
            # Get current time
            now = datetime.now(timezone.utc)
            
            # Get scheduling service
            scheduling_service = JobSchedulingService(db)
            job_service = JobService(db)
            
            # Get all enabled schedules with next_run <= now
            schedules = db.query(JobSchedule).filter(
                JobSchedule.enabled == True,
                JobSchedule.next_run <= now
            ).all()
            
            logger.info(f"📋 Found {len(schedules)} schedules ready for execution")
            
            executed_count = 0
            for schedule in schedules:
                try:
                    logger.info(f"🚀 Processing schedule {schedule.id} for job {schedule.job_id}")
                    
                    # Get the job
                    job = schedule.job
                    
                    # Execute the job
                    execute_data = JobExecuteRequest(target_ids=None)  # Use all targets
                    execution = job_service.execute_job(
                        job_id=job.id,
                        execute_data=execute_data
                    )
                    
                    # Get target IDs for this job
                    target_ids = [jt.target_id for jt in job.targets]
                    
                    # Queue the execution task
                    from app.tasks.job_tasks import execute_job_task
                    execute_job_task.delay(execution.id, target_ids)
                    
                    # Mark schedule as executed
                    scheduling_service.mark_schedule_executed(schedule.id)
                    
                    # Calculate next run time
                    logger.info(f"🧮 Calculating next run for schedule {schedule.id} with type {schedule.recurring_type}")
                    next_run = scheduling_service._calculate_next_recurring_run(schedule)
                    
                    # Update schedule with next run time
                    if next_run:
                        schedule.next_run = next_run
                        db.commit()
                        logger.info(f"📅 Next run for schedule {schedule.id}: {next_run}")
                    else:
                        logger.error(f"❌ Failed to calculate next run for schedule {schedule.id}")
                        # Set a default next run time for minutes and hours to prevent schedule from being lost
                        if schedule.recurring_type in ['minutes', 'hours']:
                            now = datetime.now(timezone.utc)
                            if schedule.recurring_type == 'minutes':
                                next_run = now + timedelta(minutes=schedule.interval)
                            else:  # hours
                                next_run = now + timedelta(hours=schedule.interval)
                            
                            schedule.next_run = next_run
                            db.commit()
                            logger.info(f"📅 Set fallback next run for {schedule.recurring_type} schedule {schedule.id}: {next_run}")
                    
                    executed_count += 1
                    logger.info(f"✅ Schedule {schedule.id} processed successfully")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing schedule {schedule.id}: {str(e)}")
            
            logger.info(f"✅ Recurring schedule processing completed: {executed_count} schedules executed")
            return {"status": "success", "schedules_executed": executed_count}
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error processing recurring schedules: {str(e)}")
        return {"status": "failed", "error": str(e)}