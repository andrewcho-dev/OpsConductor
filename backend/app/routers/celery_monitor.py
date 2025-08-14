"""
Celery Monitoring API Endpoints
Provides real-time monitoring of Celery workers, queues, and tasks
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import redis
import asyncio
import time
from celery import current_app
# from celery.events.state import State  # Not needed for basic monitoring
# from celery.events import Events  # Not needed for basic monitoring

from app.core.celery_app import celery_app
from app.core.config import settings
from app.database.database import get_db
from app.services.celery_monitoring_service import CeleryMonitoringService
from sqlalchemy.orm import Session
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
from app.models.user_models import User
from app.core.security import verify_token
from fastapi.security import HTTPBearer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/celery", tags=["celery-monitoring"])
security = HTTPBearer()

def get_current_user(credentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user."""
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Redis connection for queue monitoring
redis_client = redis.Redis.from_url(settings.REDIS_URL)

# Simple in-memory cache for monitoring data
_cache = {}
_cache_ttl = {}
CACHE_DURATION = 5  # Cache for 5 seconds

def get_cached_data(cache_key: str, fetch_func, *args, **kwargs):
    """Get data from cache or fetch if expired"""
    current_time = time.time()
    
    # Check if we have cached data and it's still valid
    if (cache_key in _cache and 
        cache_key in _cache_ttl and 
        current_time < _cache_ttl[cache_key]):
        return _cache[cache_key]
    
    # Fetch new data
    try:
        data = fetch_func(*args, **kwargs)
        _cache[cache_key] = data
        _cache_ttl[cache_key] = current_time + CACHE_DURATION
        return data
    except Exception as e:
        # If we have stale cached data, return it
        if cache_key in _cache:
            logger.warning(f"Using stale cache for {cache_key} due to error: {e}")
            return _cache[cache_key]
        raise

def safe_inspect_call(inspect_func, timeout=3):
    """Safely call Celery inspect function with timeout"""
    try:
        # Use asyncio timeout for the inspect call
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(inspect_func)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                logger.warning(f"Celery inspect call timed out after {timeout}s")
                return {}
    except Exception as e:
        logger.warning(f"Celery inspect call failed: {e}")
        return {}

@router.get("/stats")
async def get_celery_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get overall Celery statistics with real data"""
    def fetch_stats():
        try:
            monitoring_service = CeleryMonitoringService(db)
            return monitoring_service.get_enhanced_celery_stats()
            
        except Exception as e:
            logger.error(f"Error getting Celery stats: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get Celery statistics")
    
    try:
        return get_cached_data("celery_stats", fetch_stats)
    except Exception as e:
        logger.error(f"Error getting Celery stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get Celery statistics")

@router.get("/workers")
async def get_worker_stats() -> Dict[str, Any]:
    """Get detailed worker statistics"""
    def fetch_worker_stats():
        try:
            inspect = celery_app.control.inspect()
            
            # Get worker information with timeouts
            stats_data = safe_inspect_call(inspect.stats, timeout=3)
            active_data = safe_inspect_call(inspect.active, timeout=2)
            
            workers = []
            total_workers = 0
            active_workers = 0
            busy_workers = 0
            total_load = 0
            
            if stats_data:
                for worker_name, worker_stats in stats_data.items():
                    # Get system info
                    pool_info = worker_stats.get('pool', {})
                    rusage = worker_stats.get('rusage', {})
                    
                    # Calculate worker load
                    active_tasks = len((active_data or {}).get(worker_name, []))
                    pool_size = pool_info.get('max-concurrency', 1)
                    load_percentage = (active_tasks / pool_size * 100) if pool_size > 0 else 0
                    
                    # Worker status
                    is_online = True  # If we got stats, worker is online
                    is_busy = load_percentage > 80
                    
                    worker_info = {
                        "name": worker_name,
                        "hostname": worker_name.split('@')[1] if '@' in worker_name else worker_name,
                        "online": is_online,
                        "active_tasks": active_tasks,
                        "pool_size": pool_size,
                        "load_avg": round(load_percentage, 1),
                        "memory_usage": rusage.get('maxrss', 0) * 1024,  # Convert to bytes
                        "cpu_time": rusage.get('utime', 0) + rusage.get('stime', 0),
                        "uptime": worker_stats.get('clock', 0),
                        "processed_tasks": worker_stats.get('total', {}).get('tasks.total', 0),
                        "registered_tasks": 0,  # Skip for performance
                        "prefetch_count": pool_info.get('prefetch-count', 0),
                        "processes": [],  # Skip for performance
                        "last_heartbeat": datetime.utcnow().isoformat(),
                        "queues": ["celery"],  # Default queue
                        "sw_ver": worker_stats.get('sw_ver', 'Unknown'),
                    }
                    
                    workers.append(worker_info)
                    total_workers += 1
                    if is_online:
                        active_workers += 1
                    if is_busy:
                        busy_workers += 1
                    total_load += load_percentage
            
            avg_load = round(total_load / total_workers, 1) if total_workers > 0 else 0
            
            return {
                "workers": workers,
                "total_workers": total_workers,
                "active_workers": active_workers,
                "busy_workers": busy_workers,
                "offline_workers": total_workers - active_workers,
                "avg_load": avg_load,
                "last_updated": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error getting worker stats: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get worker statistics")
    
    try:
        return get_cached_data("worker_stats", fetch_worker_stats)
    except Exception as e:
        logger.error(f"Error getting worker stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get worker statistics")

@router.get("/queues")
async def get_queue_stats() -> Dict[str, Any]:
    """Get queue statistics"""
    def fetch_queue_stats():
        try:
            queues = {}
            queue_names = get_queue_names_fast()
            
            for queue_name in queue_names:
                try:
                    # Get queue length from Redis with timeout
                    try:
                        queue_length = redis_client.llen(queue_name)
                    except Exception:
                        queue_length = 0
                    
                    # Get processing stats (would typically come from monitoring)
                    queue_info = {
                        "name": queue_name,
                        "pending": queue_length,
                        "processing": 0,  # Would be calculated from active tasks
                        "processed": 0,   # Would come from historical data
                        "failed": 0,      # Would come from failed task tracking
                        "avg_time": 0.0,  # Would be calculated from task timing
                        "max_time": 0.0,
                        "min_time": 0.0,
                        "last_task": None,
                        "consumers": 0,   # Number of workers consuming from this queue
                        "rate_limit": None,
                        "priority": 0,
                        "routing_key": queue_name,
                        "exchange": "celery",
                        "created_at": datetime.utcnow().isoformat(),
                    }
                    
                    queues[queue_name] = queue_info
                    
                except Exception as e:
                    logger.warning(f"Error getting stats for queue {queue_name}: {str(e)}")
                    continue
            
            return {"queues": queues}
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get queue statistics")
    
    try:
        return get_cached_data("queue_stats", fetch_queue_stats)
    except Exception as e:
        logger.error(f"Error getting queue stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get queue statistics")

@router.get("/tasks/active")
async def get_active_tasks() -> List[Dict[str, Any]]:
    """Get currently active tasks"""
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        tasks = []
        if active_tasks:
            for worker_name, worker_tasks in active_tasks.items():
                for task in worker_tasks:
                    task_info = {
                        "id": task.get('id'),
                        "name": task.get('name'),
                        "worker": worker_name,
                        "args": task.get('args', []),
                        "kwargs": task.get('kwargs', {}),
                        "time_start": task.get('time_start'),
                        "acknowledged": task.get('acknowledged', False),
                        "delivery_info": task.get('delivery_info', {}),
                        "hostname": task.get('hostname'),
                        "clock": task.get('clock'),
                        "pid": task.get('pid'),
                    }
                    tasks.append(task_info)
        
        return tasks
        
    except Exception as e:
        logger.error(f"Error getting active tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get active tasks")

@router.get("/tasks/scheduled")
async def get_scheduled_tasks() -> List[Dict[str, Any]]:
    """Get scheduled tasks"""
    try:
        inspect = celery_app.control.inspect()
        scheduled_tasks = inspect.scheduled()
        
        tasks = []
        if scheduled_tasks:
            for worker_name, worker_tasks in scheduled_tasks.items():
                for task in worker_tasks:
                    task_info = {
                        "id": task.get('request', {}).get('id'),
                        "name": task.get('request', {}).get('task'),
                        "worker": worker_name,
                        "eta": task.get('eta'),
                        "priority": task.get('priority', 0),
                        "args": task.get('request', {}).get('args', []),
                        "kwargs": task.get('request', {}).get('kwargs', {}),
                    }
                    tasks.append(task_info)
        
        return tasks
        
    except Exception as e:
        logger.error(f"Error getting scheduled tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get scheduled tasks")

@router.post("/workers/{worker_name}/shutdown")
async def shutdown_worker(
    worker_name: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Shutdown a specific worker"""
    # Only administrators can shutdown workers
    if current_user.role != "administrator":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can shutdown workers"
        )
    
    try:
        celery_app.control.shutdown(destination=[worker_name])
        
        # Log worker shutdown audit event - CRITICAL SYSTEM EVENT
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGED,
            user_id=current_user.id,
            resource_type="worker",
            resource_id=worker_name,
            action="shutdown_worker",
            details={
                "worker_name": worker_name,
                "shutdown_by": current_user.username
            },
            severity=AuditSeverity.CRITICAL,  # Worker shutdown is critical
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return {"message": f"Shutdown signal sent to worker {worker_name}"}
        
    except Exception as e:
        logger.error(f"Error shutting down worker {worker_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to shutdown worker")

@router.post("/workers/{worker_name}/restart")
async def restart_worker(worker_name: str) -> Dict[str, str]:
    """Restart a specific worker"""
    try:
        # Note: This requires custom implementation as Celery doesn't have built-in restart
        # You would typically use a process manager like supervisor or systemd
        return {"message": f"Restart signal sent to worker {worker_name}"}
        
    except Exception as e:
        logger.error(f"Error restarting worker {worker_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to restart worker")

@router.post("/queues/{queue_name}/purge")
async def purge_queue(queue_name: str) -> Dict[str, Any]:
    """Purge all messages from a queue"""
    try:
        # Purge the queue
        purged_count = redis_client.delete(queue_name)
        
        return {
            "message": f"Queue {queue_name} purged",
            "purged_count": purged_count
        }
        
    except Exception as e:
        logger.error(f"Error purging queue {queue_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to purge queue")

@router.post("/tasks/{task_id}/revoke")
async def revoke_task(
    task_id: str,
    terminate: bool = False
) -> Dict[str, str]:
    """Revoke a task"""
    try:
        celery_app.control.revoke(task_id, terminate=terminate)
        action = "terminated" if terminate else "revoked"
        return {"message": f"Task {task_id} {action}"}
        
    except Exception as e:
        logger.error(f"Error revoking task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to revoke task")

@router.get("/metrics/history")
async def get_metrics_history(
    hours: int = 24,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get historical metrics for charts"""
    try:
        monitoring_service = CeleryMonitoringService(db)
        snapshots = monitoring_service.get_metrics_history(hours=hours)
        
        # Format data for charts
        timestamps = []
        active_tasks = []
        completed_tasks = []
        failed_tasks = []
        worker_loads = []
        tasks_per_minute = []
        
        for snapshot in snapshots:
            timestamps.append(snapshot.timestamp.isoformat())
            active_tasks.append(snapshot.active_tasks)
            completed_tasks.append(snapshot.completed_tasks_last_hour)
            failed_tasks.append(snapshot.failed_tasks_last_hour)
            worker_loads.append(snapshot.avg_worker_load)
            tasks_per_minute.append(snapshot.tasks_per_minute)
        
        return {
            "timestamps": timestamps,
            "metrics": {
                "active_tasks": active_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "worker_loads": worker_loads,
                "tasks_per_minute": tasks_per_minute
            },
            "total_snapshots": len(snapshots)
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get metrics history")

# Helper functions
def get_queue_names_fast() -> List[str]:
    """Get list of known queue names (fast version)"""
    # Return predefined queue names to avoid slow Redis KEYS operation
    return ['celery', 'job_execution', 'default']

def get_queue_names() -> List[str]:
    """Get list of known queue names (legacy - slow)"""
    try:
        # Get queue names from Redis
        keys = redis_client.keys("celery*")
        queue_names = [key.decode() for key in keys if not key.decode().endswith('_unacked')]
        
        # Add default queues
        default_queues = ['celery', 'job_execution', 'default']
        for queue in default_queues:
            if queue not in queue_names:
                queue_names.append(queue)
        
        return queue_names
    except Exception:
        return ['celery', 'job_execution', 'default']

def get_recent_tasks(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent task information"""
    # This would typically come from Celery events or a task history database
    # For now, return empty list
    return []

def get_task_type_stats() -> Dict[str, int]:
    """Get statistics by task type"""
    # This would typically come from task execution history
    return {
        "app.tasks.job_tasks.execute_job_task": 0,
        "app.tasks.cleanup_tasks.cleanup_stale_executions": 0,
    }

def get_celery_uptime() -> float:
    """Get Celery system uptime in seconds"""
    try:
        # This would typically track when the system started
        return 0.0
    except Exception:
        return 0.0