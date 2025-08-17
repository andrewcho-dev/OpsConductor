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


@celery_app.task(bind=True, name="app.tasks.discovery_tasks.run_in_memory_discovery_task", time_limit=300, soft_time_limit=240)
def run_in_memory_discovery_task(self, task_id: str, discovery_config: dict):
    """
    Celery task to run in-memory network discovery.
    
    Args:
        task_id: Task ID for tracking progress
        discovery_config: Discovery configuration dictionary
        
    Returns:
        dict: Task execution result with discovered devices
    """
    logger.info(f"🔍 Starting in-memory discovery Celery task: {task_id}")
    
    try:
        # Import the discovery management service
        from app.services.discovery_management_service import DiscoveryManagementService
        from app.database.database import SessionLocal
        
        # Get database session
        db = SessionLocal()
        
        # Create discovery management service instance
        discovery_service = DiscoveryManagementService(db)
        
        # Update status to running
        discovery_service._update_task_status_sync(task_id, "running", 10, "Starting network discovery...")
        
        # Run the actual discovery logic synchronously
        import ipaddress
        import socket
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        discovered_devices = []
        
        # Parse network ranges and discover devices
        for network_range in discovery_config.get('network_ranges', []):
            try:
                network = ipaddress.ip_network(network_range, strict=False)
                hosts = list(network.hosts()) if network.num_addresses > 1 else [network.network_address]
                total_hosts = len(hosts)
                
                logger.info(f"Scanning {total_hosts} hosts in {network_range}")
                
                # Warn about large network ranges
                if total_hosts > 100:
                    logger.warning(f"Large network range detected: {total_hosts} hosts. This may take several minutes.")
                    discovery_service._update_task_status_sync(task_id, "running", 30, f"Scanning large network: {total_hosts} hosts (this may take 3-5 minutes)...")
                else:
                    discovery_service._update_task_status_sync(task_id, "running", 30, f"Scanning {total_hosts} hosts...")
                
                # Use ThreadPoolExecutor for parallel host checking with progress updates
                completed_hosts = 0
                max_workers = min(50, discovery_config.get('max_concurrent', 50))  # Increase concurrency
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_host = {
                        executor.submit(discovery_service._ping_host, str(host)): host 
                        for host in hosts
                    }
                    
                    for future in as_completed(future_to_host):
                        host = future_to_host[future]
                        completed_hosts += 1
                        
                        # Update progress every 10 hosts or at key milestones
                        if completed_hosts % 10 == 0 or completed_hosts in [1, 5, total_hosts]:
                            progress = 30 + int((completed_hosts / total_hosts) * 50)  # 30-80% for scanning
                            discovery_service._update_task_status_sync(
                                task_id, "running", progress, 
                                f"Scanned {completed_hosts}/{total_hosts} hosts, found {len(discovered_devices)} devices"
                            )
                        
                        try:
                            if future.result():
                                # Host is alive, get more details
                                device_info = discovery_service._get_device_info(str(host), discovery_config.get('common_ports', [22, 80, 443]))
                                discovered_devices.append(device_info)
                                logger.info(f"Discovered device: {device_info['ip_address']}")
                        except Exception as e:
                            logger.error(f"Error checking host {host}: {e}")
                
            except Exception as e:
                logger.error(f"Error processing network range {network_range}: {e}")
        
        # Filter duplicates
        discovery_service._update_task_status_sync(task_id, "running", 80, "Filtering duplicate devices...")
        
        # Convert to async context temporarily for filtering
        import asyncio
        async def filter_duplicates():
            return await discovery_service._filter_duplicate_targets(discovered_devices)
        
        filtered_devices = asyncio.run(filter_duplicates())
        
        # Complete the task
        active_duplicates = len(discovered_devices) - len(filtered_devices)
        completion_message = f"Discovery completed. Found {len(discovered_devices)} devices ({len(filtered_devices)} available for import, {active_duplicates} active duplicates filtered)"
        
        discovery_service._update_task_status_sync(task_id, "completed", 100, completion_message, filtered_devices)
        
        logger.info(f"✅ In-memory discovery Celery task {task_id} completed successfully")
        
        return {
            'status': 'success',
            'task_id': task_id,
            'devices_found': len(filtered_devices),
            'message': f'Discovery task {task_id} completed successfully'
        }
        
    except Exception as e:
        logger.error(f"❌ In-memory discovery Celery task {task_id} failed: {str(e)}")
        
        # Try to update task status to failed in Redis
        try:
            discovery_service._update_task_status_sync(
                task_id, 
                "failed", 
                0, 
                f"Discovery failed: {str(e)}"
            )
        except Exception as update_error:
            logger.error(f"Failed to update task status: {str(update_error)}")
        
        return {
            'status': 'failed',
            'task_id': task_id,
            'error': str(e),
            'message': f'Discovery task {task_id} failed: {str(e)}'
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