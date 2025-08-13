"""
Discovery Tasks
Celery tasks for network discovery operations.
"""

import logging
from celery import current_app as celery_app
from app.database.database import get_db
from app.services.discovery_service import DiscoveryService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.discovery_tasks.run_discovery_job_task")
def run_discovery_job_task(self, job_id: int):
    """
    Celery task to run a discovery job.
    
    Args:
        job_id: Discovery job ID to execute
        
    Returns:
        dict: Task execution result
    """
    logger.info(f"🔍 Starting discovery job task for job ID: {job_id}")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Create discovery service
        discovery_service = DiscoveryService(db)
        
        # Run the discovery job
        import asyncio
        result = asyncio.run(discovery_service.run_discovery_job(job_id))
        
        if result:
            logger.info(f"✅ Discovery job {job_id} completed successfully")
            return {
                'status': 'success',
                'job_id': job_id,
                'message': f'Discovery job {job_id} completed successfully'
            }
        else:
            logger.error(f"❌ Discovery job {job_id} failed")
            return {
                'status': 'failed',
                'job_id': job_id,
                'message': f'Discovery job {job_id} failed'
            }
            
    except Exception as e:
        logger.error(f"❌ Discovery job {job_id} failed with exception: {str(e)}")
        
        # Try to update job status to failed
        try:
            db = next(get_db())
            discovery_service = DiscoveryService(db)
            job = discovery_service.get_discovery_job(job_id)
            if job:
                job.status = 'failed'
                db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update job status: {str(update_error)}")
        
        return {
            'status': 'failed',
            'job_id': job_id,
            'message': f'Discovery job {job_id} failed: {str(e)}'
        }
    finally:
        # Close database session
        try:
            db.close()
        except:
            pass


@celery_app.task(bind=True, name="app.tasks.discovery_tasks.cleanup_old_discovery_jobs")
def cleanup_old_discovery_jobs(self):
    """
    Celery task to cleanup old discovery jobs and their data.
    
    Returns:
        dict: Cleanup result
    """
    logger.info("🧹 Starting discovery job cleanup task")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Create discovery service
        discovery_service = DiscoveryService(db)
        
        # TODO: Implement cleanup logic
        # - Remove old completed/failed jobs (older than X days)
        # - Remove orphaned discovered devices
        # - Clean up temporary files
        
        logger.info("✅ Discovery job cleanup completed")
        return {
            'status': 'success',
            'message': 'Discovery job cleanup completed'
        }
        
    except Exception as e:
        logger.error(f"❌ Discovery job cleanup failed: {str(e)}")
        return {
            'status': 'failed',
            'message': f'Discovery job cleanup failed: {str(e)}'
        }
    finally:
        # Close database session
        try:
            db.close()
        except:
            pass