"""
Celery Application Configuration for Execution Service
"""

import os
from celery import Celery
from kombu import Queue, Exchange

# Import configuration
from app.core.config import settings

# Create Celery instance
app = Celery('execution-service')

# Configure broker and backend
app.conf.broker_url = settings.redis_url
app.conf.result_backend = settings.redis_url

# Configure serialization
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'

# Configure timezone
app.conf.timezone = 'UTC'
app.conf.enable_utc = True

# Configure task routing and queues
app.conf.task_routes = {
    # Execution tasks - high priority, heavy workload
    'app.tasks.execution_tasks.*': {'queue': 'execution'},
    
    # System tasks - background maintenance
    'app.tasks.system_tasks.*': {'queue': 'system'},
    
    # Discovery tasks - network scanning  
    'app.tasks.discovery_tasks.*': {'queue': 'system'},
    
    # Health monitoring tasks
    'app.tasks.health_tasks.*': {'queue': 'system'},
}

# Define queues with different priorities
app.conf.task_default_queue = 'system'
app.conf.task_queues = (
    Queue('execution', 
          Exchange('execution'), 
          routing_key='execution',
          queue_arguments={'x-max-priority': 10}),
    Queue('system', 
          Exchange('system'), 
          routing_key='system',
          queue_arguments={'x-max-priority': 5}),
)

# Configure worker settings
app.conf.worker_prefetch_multiplier = 1
app.conf.task_acks_late = True
app.conf.worker_disable_rate_limits = False

# Configure retry settings
app.conf.task_reject_on_worker_lost = True
app.conf.task_acks_on_failure_or_timeout = True

# Configure result expiration
app.conf.result_expires = 3600  # 1 hour

# Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # System health checks every 5 minutes
    'health-check-all-services': {
        'task': 'app.tasks.health_tasks.check_all_services_health',
        'schedule': 300.0,  # 5 minutes
        'options': {'queue': 'system'}
    },
    
    # Clean up old executions every hour
    'cleanup-old-executions': {
        'task': 'app.tasks.system_tasks.cleanup_old_executions',
        'schedule': 3600.0,  # 1 hour
        'options': {'queue': 'system'}
    },
    
    # Collect system metrics every 10 minutes
    'collect-system-metrics': {
        'task': 'app.tasks.system_tasks.collect_system_metrics',
        'schedule': 600.0,  # 10 minutes
        'options': {'queue': 'system'}
    },
    
    # Auto-discover targets every 30 minutes
    'auto-discovery-scan': {
        'task': 'app.tasks.discovery_tasks.auto_discovery_scan',
        'schedule': 1800.0,  # 30 minutes
        'options': {'queue': 'system'}
    },
    
    # Check execution timeouts every 2 minutes
    'check-execution-timeouts': {
        'task': 'app.tasks.execution_tasks.check_execution_timeouts',
        'schedule': 120.0,  # 2 minutes
        'options': {'queue': 'execution'}
    },
}

# Auto-discover tasks
app.autodiscover_tasks([
    'app.tasks.execution_tasks',
    'app.tasks.system_tasks', 
    'app.tasks.discovery_tasks',
    'app.tasks.health_tasks',
])

# Configure logging
app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

if __name__ == '__main__':
    app.start()