"""
BULLETPROOF Celery configuration - NO DEPENDENCIES VERSION
"""

import os
from celery import Celery

# Get environment variables directly - NO PYDANTIC BULLSHIT
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://opsconductor:opsconductor_secure_password_2024@postgres:5432/opsconductor_dev")

# Create Celery app - MINIMAL CONFIG
celery_app = Celery("opsconductor")

# BASIC configuration that actually works
celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=False,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    result_expires=3600,
    # Disable all the complex shit
    task_ignore_result=False,
    worker_disable_rate_limits=True,
)

# Auto-discover tasks from the tasks package
celery_app.autodiscover_tasks(['app.tasks'])

# MINIMAL beat schedule
celery_app.conf.beat_schedule = {
    'test-task-every-minute': {
        'task': 'app.tasks.simple_tasks.health_check',
        'schedule': 60.0,  # Every minute for testing
    },
    'check-scheduled-jobs': {
        'task': 'app.tasks.job_tasks.check_scheduled_jobs',
        'schedule': 30.0,  # Every 30 seconds to check for scheduled jobs
    },
    'process-recurring-schedules': {
        'task': 'app.tasks.periodic_tasks.process_recurring_schedules_task',
        'schedule': 30.0,  # Every 30 seconds to check for recurring schedules
    },
}

if __name__ == "__main__":
    celery_app.start()