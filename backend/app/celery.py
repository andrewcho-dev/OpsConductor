"""
Celery app instance for OpsConductor
This module provides the main Celery app instance that can be imported by workers
"""

from app.core.celery_app import celery_app

# Export the celery app so it can be found by workers
__all__ = ['celery_app']