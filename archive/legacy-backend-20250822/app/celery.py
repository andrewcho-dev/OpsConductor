"""
Celery app instance for OpsConductor - BULLETPROOF VERSION
"""

from app.core.celery_app import celery_app

# Import tasks to register them - NO COMPLEX IMPORTS
try:
    from app.tasks import simple_tasks
    print("✅ Successfully imported simple_tasks")
except Exception as e:
    print(f"❌ Failed to import simple_tasks: {e}")

try:
    from app.tasks import job_tasks
    print("✅ Successfully imported job_tasks")
except Exception as e:
    print(f"❌ Failed to import job_tasks: {e}")

try:
    from app.tasks import periodic_tasks
    print("✅ Successfully imported periodic_tasks")
except Exception as e:
    print(f"❌ Failed to import periodic_tasks: {e}")

# Export the celery app so it can be found by workers
__all__ = ['celery_app']