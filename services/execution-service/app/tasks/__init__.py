"""
Task modules for distributed Celery workers
"""

from app.celery_app import app

# Import all task modules to register them with Celery
from . import execution_tasks
from . import system_tasks
from . import discovery_tasks
from . import health_tasks

__all__ = [
    'execution_tasks',
    'system_tasks', 
    'discovery_tasks',
    'health_tasks'
]