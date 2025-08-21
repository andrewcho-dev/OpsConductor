"""
Celery application configuration
"""

from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "job-execution-service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.job_tasks",
        "app.tasks.schedule_tasks",
        "app.tasks.cleanup_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks configuration
celery_app.conf.beat_schedule = {
    # Check for scheduled jobs every minute
    'check-scheduled-jobs': {
        'task': 'app.tasks.schedule_tasks.check_scheduled_jobs',
        'schedule': 60.0,  # Every minute
    },
    
    # Process recurring schedules every 5 minutes
    'process-recurring-schedules': {
        'task': 'app.tasks.schedule_tasks.process_recurring_schedules',
        'schedule': 300.0,  # Every 5 minutes
    },
    
    # Cleanup stale executions every hour
    'cleanup-stale-executions': {
        'task': 'app.tasks.cleanup_tasks.cleanup_stale_executions',
        'schedule': 3600.0,  # Every hour
    },
    
    # Health check every 5 minutes
    'service-health-check': {
        'task': 'app.tasks.cleanup_tasks.service_health_check',
        'schedule': 300.0,  # Every 5 minutes
    },
}