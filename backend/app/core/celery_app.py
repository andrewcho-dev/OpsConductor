"""
Celery configuration for ENABLEDRM background task processing
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "enabledrm",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.job_tasks", "app.tasks.periodic_tasks", "app.tasks.discovery_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_always_eager=False,  # Set to True for testing
)

# Celery Beat Schedule - Periodic Tasks
celery_app.conf.beat_schedule = {
    # Check for scheduled jobs every 30 seconds
    'check-scheduled-jobs': {
        'task': 'app.tasks.job_tasks.check_scheduled_jobs',
        'schedule': 30.0,  # Every 30 seconds
    },
    # Run cleanup tasks every hour
    'cleanup-stale-executions': {
        'task': 'app.tasks.periodic_tasks.cleanup_stale_executions_task',
        'schedule': crontab(minute=0),  # Every hour at minute 0
    },
    # System health check every 5 minutes
    'system-health-check': {
        'task': 'app.tasks.periodic_tasks.system_health_check_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    # Target health monitoring every 10 minutes
    'target-health-monitoring': {
        'task': 'app.tasks.periodic_tasks.target_health_monitoring_task',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
    # Collect Celery metrics every 5 minutes
    'collect-celery-metrics': {
        'task': 'app.tasks.periodic_tasks.collect_celery_metrics_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}

# Task routing - use default queue for now
# celery_app.conf.task_routes = {
#     "app.tasks.job_tasks.*": {"queue": "job_execution"},
# }

if __name__ == "__main__":
    celery_app.start()
