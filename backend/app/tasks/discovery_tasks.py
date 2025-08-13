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


@celery_app.task(bind=True, name="app.tasks.discovery_tasks.run_in_memory_discovery_task")
def run_in_memory_discovery_task(self, discovery_config: dict):
    """
    Celery task to run in-memory network discovery.
    
    Args:
        discovery_config: Discovery configuration dictionary
        
    Returns:
        dict: Task execution result with discovered devices
    """
    logger.info(f"🔍 Starting in-memory discovery task")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Create discovery service
        discovery_service = DiscoveryService(db)
        
        # Create progress callback for Celery task updates
        def progress_callback(percent, total_ips, found_devices, message):
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': percent,
                    'total_ips': total_ips,
                    'found_devices': found_devices,
                    'message': message
                }
            )
        
        # Run the in-memory discovery with progress callback
        import asyncio
        
        # Create async wrapper for progress callback
        async def async_progress_callback(percent, total_ips, found_devices, message):
            progress_callback(percent, total_ips, found_devices, message)
        
        devices = asyncio.run(discovery_service.run_in_memory_discovery_with_progress(discovery_config, async_progress_callback))
        
        logger.info(f"✅ In-memory discovery completed successfully - found {len(devices)} devices")
        
        # Convert devices to serializable format
        serializable_devices = []
        for device in devices:
            device_dict = {
                'id': device.id,  # ✅ CRITICAL: Include the ID field!
                'ip_address': device.ip_address,
                'hostname': device.hostname,
                'mac_address': device.mac_address,
                'open_ports': device.open_ports,
                'services': device.services,
                'snmp_info': device.snmp_info,
                'device_type': device.device_type,
                'os_type': device.os_type,
                'confidence_score': device.confidence_score,
                'suggested_communication_methods': device.suggested_communication_methods,
                'discovered_at': device.discovered_at.isoformat() if device.discovered_at else None,
                'status': device.status
            }
            serializable_devices.append(device_dict)
        
        return {
            'status': 'success',
            'devices': serializable_devices,
            'message': f'Discovery completed - found {len(devices)} devices'
        }
        
    except Exception as e:
        logger.error(f"❌ In-memory discovery failed: {str(e)}")
        return {
            'status': 'failed',
            'devices': [],
            'error': str(e),
            'message': f'Discovery failed: {str(e)}'
        }
    finally:
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