"""
Celery API v3 - Consolidated from v1/celery_monitor.py
All Celery monitoring endpoints in v3 structure
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from celery import Celery
from celery.events.state import State
import redis
import json

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.core.logging import get_structured_logger

# Initialize
logger = get_structured_logger(__name__)
router = APIRouter(prefix=f"{os.getenv(\'API_BASE_URL\', \'/api/v3\')}/celery", tags=["Celery v3"])

# Celery app instance
from celery import current_app as celery_app

# Redis connection for metrics
try:
    import redis
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None


@router.get("/stats")
async def get_celery_stats(
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get general Celery statistics"""
    try:
        # Get active tasks
        active_tasks = celery_app.control.inspect().active()
        scheduled_tasks = celery_app.control.inspect().scheduled()
        reserved_tasks = celery_app.control.inspect().reserved()
        
        # Calculate totals
        total_active = sum(len(tasks) for tasks in (active_tasks or {}).values())
        total_scheduled = sum(len(tasks) for tasks in (scheduled_tasks or {}).values())
        total_reserved = sum(len(tasks) for tasks in (reserved_tasks or {}).values())
        
        # Get task statistics from database
        from app.models.celery_models import CeleryTaskHistory
        completed_count = 0
        failed_count = 0
        completed_today = 0
        failed_today = 0
        
        try:
            from datetime import timezone as tz
            
            # Last 24 hours
            now = datetime.now(tz.utc)
            completed_count = db.query(CeleryTaskHistory).filter(
                CeleryTaskHistory.status == 'success',
                CeleryTaskHistory.completed_at >= now - timedelta(hours=24)
            ).count()
            
            failed_count = db.query(CeleryTaskHistory).filter(
                CeleryTaskHistory.status == 'failure',
                CeleryTaskHistory.completed_at >= now - timedelta(hours=24)
            ).count()
            
            # Today (since midnight)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            completed_today = db.query(CeleryTaskHistory).filter(
                CeleryTaskHistory.status == 'success',
                CeleryTaskHistory.completed_at >= today_start
            ).count()
            
            failed_today = db.query(CeleryTaskHistory).filter(
                CeleryTaskHistory.status == 'failure',
                CeleryTaskHistory.completed_at >= today_start
            ).count()
            
        except Exception as e:
            logger.warning(f"Could not get task statistics: {e}")
        
        # Calculate success rate
        total_tasks = completed_count + failed_count
        success_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate average task time (mock data for now)
        avg_task_time = 2.5  # seconds
        tasks_per_minute = completed_count / (24 * 60) if completed_count > 0 else 0
        
        stats = {
            "active_tasks": total_active,
            "scheduled_tasks": total_scheduled,
            "reserved_tasks": total_reserved,
            "pending_tasks": total_active + total_scheduled + total_reserved,
            "total_pending": total_active + total_scheduled + total_reserved,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "completed_today": completed_today,
            "failed_today": failed_today,
            "success_rate": round(success_rate, 2),
            "avg_task_time": avg_task_time,
            "tasks_per_minute": round(tasks_per_minute, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting Celery stats: {e}")
        # Return fallback stats
        return {
            "active_tasks": 0,
            "scheduled_tasks": 0,
            "reserved_tasks": 0,
            "pending_tasks": 0,
            "total_pending": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "completed_today": 0,
            "failed_today": 0,
            "success_rate": 0,
            "avg_task_time": 0,
            "tasks_per_minute": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Could not connect to Celery"
        }


@router.get("/queues")
async def get_queue_stats(
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get queue statistics"""
    try:
        # Get queue information from Celery
        active_queues = celery_app.control.inspect().active_queues()
        
        queue_stats = {}
        
        if active_queues:
            for worker, queues in active_queues.items():
                for queue in queues:
                    queue_name = queue.get('name', 'default')
                    if queue_name not in queue_stats:
                        queue_stats[queue_name] = {
                            "name": queue_name,
                            "pending": 0,
                            "workers": [],
                            "routing_key": queue.get('routing_key', queue_name)
                        }
                    queue_stats[queue_name]["workers"].append(worker)
        
        # Get pending tasks per queue from Redis if available
        if redis_client:
            try:
                for queue_name in queue_stats.keys():
                    pending_count = redis_client.llen(queue_name)
                    queue_stats[queue_name]["pending"] = pending_count
            except Exception as e:
                logger.warning(f"Could not get queue lengths from Redis: {e}")
        
        # If no queues found, provide default structure
        if not queue_stats:
            queue_stats = {
                "default": {
                    "name": "default",
                    "pending": 0,
                    "workers": [],
                    "routing_key": "default"
                },
                "celery": {
                    "name": "celery",
                    "pending": 0,
                    "workers": [],
                    "routing_key": "celery"
                }
            }
        
        return queue_stats
        
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        return {
            "default": {
                "name": "default",
                "pending": 0,
                "workers": [],
                "routing_key": "default",
                "error": "Could not connect to Celery"
            }
        }


@router.get("/workers")
async def get_worker_stats(
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get worker statistics"""
    try:
        # Get worker information
        stats = celery_app.control.inspect().stats()
        active = celery_app.control.inspect().active()
        registered = celery_app.control.inspect().registered()
        
        worker_info = {}
        active_workers = 0
        
        if stats:
            for worker_name, worker_stats in stats.items():
                active_workers += 1
                worker_info[worker_name] = {
                    "name": worker_name,
                    "status": "online",
                    "active_tasks": len(active.get(worker_name, [])) if active else 0,
                    "processed_tasks": worker_stats.get("total", {}).get("tasks.job_tasks.execute_job_task", 0),
                    "load_avg": worker_stats.get("rusage", {}).get("utime", 0),
                    "memory_usage": worker_stats.get("rusage", {}).get("maxrss", 0),
                    "registered_tasks": len(registered.get(worker_name, [])) if registered else 0,
                    "pool": worker_stats.get("pool", {}).get("implementation", "unknown"),
                    "processes": worker_stats.get("pool", {}).get("processes", []),
                    "broker": worker_stats.get("broker", {}),
                    "clock": worker_stats.get("clock", 0)
                }
        
        return {
            "active_workers": active_workers,
            "total_workers": len(worker_info),
            "workers": worker_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting worker stats: {e}")
        return {
            "active_workers": 0,
            "total_workers": 0,
            "workers": {},
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Could not connect to Celery"
        }


@router.get("/active-tasks")
async def get_active_tasks(
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get currently active tasks"""
    try:
        active_tasks = celery_app.control.inspect().active()
        
        tasks = []
        if active_tasks:
            for worker, worker_tasks in active_tasks.items():
                for task in worker_tasks:
                    tasks.append({
                        "id": task.get("id"),
                        "name": task.get("name"),
                        "worker": worker,
                        "args": task.get("args", []),
                        "kwargs": task.get("kwargs", {}),
                        "time_start": task.get("time_start"),
                        "acknowledged": task.get("acknowledged", False),
                        "delivery_info": task.get("delivery_info", {})
                    })
        
        return {
            "active_tasks": tasks,
            "count": len(tasks),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        return {
            "active_tasks": [],
            "count": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Could not connect to Celery"
        }


@router.get("/metrics/history")
async def get_metrics_history(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get historical metrics for the specified time period"""
    try:
        from app.models.celery_models import CeleryTaskHistory
        from datetime import timezone as tz
        
        now = datetime.now(tz.utc)
        start_time = now - timedelta(hours=hours)
        
        # Get task history from database
        tasks = db.query(CeleryTaskHistory).filter(
            CeleryTaskHistory.started_at >= start_time
        ).all()
        
        # Group by hour
        hourly_stats = {}
        for task in tasks:
            if task.started_at:
                hour_key = task.started_at.replace(minute=0, second=0, microsecond=0)
                hour_str = hour_key.isoformat()
                
                if hour_str not in hourly_stats:
                    hourly_stats[hour_str] = {
                        "timestamp": hour_str,
                        "completed": 0,
                        "failed": 0,
                        "total": 0,
                        "avg_duration": 0,
                        "durations": []
                    }
                
                hourly_stats[hour_str]["total"] += 1
                
                if task.status == "success":
                    hourly_stats[hour_str]["completed"] += 1
                elif task.status == "failure":
                    hourly_stats[hour_str]["failed"] += 1
                
                if task.duration:
                    hourly_stats[hour_str]["durations"].append(task.duration)
        
        # Calculate averages
        for hour_data in hourly_stats.values():
            if hour_data["durations"]:
                hour_data["avg_duration"] = sum(hour_data["durations"]) / len(hour_data["durations"])
            del hour_data["durations"]  # Remove raw durations from response
        
        # Convert to list and sort by timestamp
        metrics_list = list(hourly_stats.values())
        metrics_list.sort(key=lambda x: x["timestamp"])
        
        return {
            "metrics": metrics_list,
            "period_hours": hours,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "total_records": len(metrics_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        return {
            "metrics": [],
            "period_hours": hours,
            "start_time": (datetime.utcnow() - timedelta(hours=hours)).isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "total_records": 0,
            "error": str(e)
        }


@router.post("/workers/shutdown")
async def shutdown_worker(
    worker_name: str,
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Shutdown a specific worker (admin only)"""
    try:
        # Check if user has admin privileges
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required for worker management"
            )
        
        # Send shutdown signal to worker
        celery_app.control.broadcast('shutdown', destination=[worker_name])
        
        return {
            "message": f"Shutdown signal sent to worker {worker_name}",
            "worker": worker_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error shutting down worker {worker_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to shutdown worker: {str(e)}"
        )


@router.post("/tasks/{task_id}/revoke")
async def revoke_task(
    task_id: str,
    terminate: bool = Query(False),
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Revoke a specific task"""
    try:
        # Revoke the task
        celery_app.control.revoke(task_id, terminate=terminate)
        
        return {
            "message": f"Task {task_id} revoked",
            "task_id": task_id,
            "terminated": terminate,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error revoking task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke task: {str(e)}"
        )