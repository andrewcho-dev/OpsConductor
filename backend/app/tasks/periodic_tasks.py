"""
Periodic Celery tasks for scheduled operations
"""

import logging
from app.core.celery_app import celery_app
from app.tasks.cleanup_tasks import CleanupTasks
from app.services.health_monitoring_service import HealthMonitoringService
from app.services.celery_monitoring_service import CeleryMonitoringService
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


@celery_app.task(bind=True, name="app.tasks.periodic_tasks.target_health_monitoring_task")
def target_health_monitoring_task(self):
    """Celery task to monitor target health status"""
    logger.info("🎯 Running scheduled target health monitoring...")
    
    try:
        # Get database session
        db = SessionLocal()
        
        try:
            # Create health monitoring service
            health_service = HealthMonitoringService(db)
            
            # Run health check batch
            results = health_service.run_health_check_batch()
            
            logger.info(f"🏥 Target health monitoring completed: {results}")
            
            # Log summary if there were status changes
            if results.get('status_changes', 0) > 0:
                logger.warning(f"⚠️ {results['status_changes']} targets changed health status")
            
            return {"status": "success", "results": results}
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Target health monitoring failed: {str(e)}")
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