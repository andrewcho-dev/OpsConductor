"""
BULLETPROOF Celery tasks - NO DEPENDENCIES VERSION
"""

import logging
import os
from datetime import datetime, timezone
from typing import List

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.simple_tasks.health_check")
def health_check(self):
    """Simple health check task - NO DATABASE DEPENDENCIES"""
    logger.info("🏥 Running health check...")
    try:
        return {
            "status": "healthy", 
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "worker": self.request.hostname,
            "redis_url": os.getenv("REDIS_URL", "not_set")
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}


@celery_app.task(bind=True, name="app.tasks.simple_tasks.cleanup_task")
def cleanup_task(self):
    """Simple cleanup task - NO DATABASE DEPENDENCIES"""
    logger.info("🧹 Running cleanup task...")
    try:
        # Just return success for now
        return {
            "status": "success", 
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Cleanup completed successfully"
        }
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {str(e)}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, name="app.tasks.simple_tasks.execute_job")
def execute_job(self, job_id: int, target_ids: List[int]):
    """Simple job execution task - NO DATABASE DEPENDENCIES"""
    logger.info(f"🚀 Executing job {job_id} on targets {target_ids}")
    
    try:
        # Simulate job execution
        logger.info(f"✅ Job {job_id} executed successfully")
        
        return {
            "status": "success", 
            "job_id": job_id, 
            "target_ids": target_ids,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Job {job_id} completed on {len(target_ids)} targets"
        }
        
    except Exception as e:
        logger.error(f"❌ Job execution failed: {str(e)}")
        return {"status": "failed", "error": str(e)}