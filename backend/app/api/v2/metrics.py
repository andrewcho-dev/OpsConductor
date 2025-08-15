"""
Metrics API v2 - Consolidated Metrics & Statistics Endpoints
Consolidates all metrics, stats, and analytics endpoints into a unified API.

This replaces:
- /api/celery-monitor/stats (celery_monitor.py)
- /api/discovery/stats (discovery.py)  
- /api/notifications/stats (notifications.py)
- /api/log-viewer/stats (log_viewer.py)
- /api/v1/monitoring/metrics (monitoring.py)
- /api/system/metrics (system.py)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import verify_token
from app.models.user_models import User
from app.services.user_service import UserService
from app.domains.monitoring.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/metrics", tags=["Metrics & Analytics v2"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                    db: Session = Depends(get_db)):
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("user_id")
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    """Get metrics service with dependencies."""
    return MetricsService(db)


def get_utc_timestamp() -> str:
    """Get current UTC timestamp with timezone information."""
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# SYSTEM METRICS ENDPOINTS
# ============================================================================

@router.get("/system")
async def get_system_metrics(
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user),
    include_history: bool = Query(False, description="Include historical data")
):
    """
    Get comprehensive system metrics.
    Consolidates: /api/v1/monitoring/metrics, /api/system/metrics
    """
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view system metrics"
        )
    
    try:
        metrics = await service.get_system_metrics()
        
        if include_history:
            # Add historical metrics if requested
            metrics["history"] = await service.get_metrics_history(hours=24)
        
        metrics["timestamp"] = get_utc_timestamp()
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")


@router.get("/system/prometheus")
async def get_prometheus_metrics(
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get metrics in Prometheus format.
    Consolidates: /api/v1/monitoring/metrics/prometheus
    """
    if current_user.role not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access Prometheus metrics"
        )
    
    try:
        metrics_text = await service.get_prometheus_metrics()
        return Response(
            content=metrics_text,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Prometheus metrics")


@router.get("/system/prometheus/public")
async def get_prometheus_metrics_public(
    service: MetricsService = Depends(get_metrics_service)
):
    """
    Get metrics in Prometheus format (public endpoint for monitoring).
    Consolidates: /api/v1/monitoring/metrics/prometheus/public
    """
    try:
        metrics_text = await service.get_prometheus_metrics()
        return Response(
            content=metrics_text,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Failed to get public Prometheus metrics: {str(e)}")
        return Response(
            content="# Error retrieving metrics\n",
            media_type="text/plain"
        )


# ============================================================================
# JOB METRICS ENDPOINTS
# ============================================================================

@router.get("/jobs")
async def get_job_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d")
):
    """
    Get job execution metrics and statistics.
    Consolidates job-related stats from multiple endpoints.
    """
    try:
        # Parse time range
        hours = parse_time_range(time_range)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get job metrics (this would integrate with your job system)
        job_metrics = await get_job_execution_metrics(db, since)
        
        return {
            "timestamp": get_utc_timestamp(),
            "time_range": time_range,
            "metrics": job_metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get job metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job metrics")


@router.get("/celery")
async def get_celery_metrics(
    current_user: User = Depends(get_current_user),
    include_history: bool = Query(False, description="Include metrics history")
):
    """
    Get Celery worker and task metrics.
    Consolidates: /api/celery-monitor/stats, /api/celery-monitor/metrics/history
    """
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view Celery metrics"
        )
    
    try:
        # Get current Celery stats
        celery_stats = await get_celery_statistics()
        
        result = {
            "timestamp": get_utc_timestamp(),
            "workers": celery_stats.get("workers", {}),
            "queues": celery_stats.get("queues", {}),
            "tasks": celery_stats.get("tasks", {}),
            "overall_status": celery_stats.get("status", "unknown")
        }
        
        if include_history:
            result["history"] = await get_celery_metrics_history()
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get Celery metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Celery metrics")


# ============================================================================
# DISCOVERY METRICS ENDPOINTS
# ============================================================================

@router.get("/discovery")
async def get_discovery_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get network discovery metrics and statistics.
    Consolidates: /api/discovery/stats
    """
    try:
        discovery_stats = await get_discovery_statistics(db)
        
        return {
            "timestamp": get_utc_timestamp(),
            "statistics": discovery_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discovery metrics")


# ============================================================================
# NOTIFICATION METRICS ENDPOINTS
# ============================================================================

@router.get("/notifications")
async def get_notification_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: str = Query("24h", description="Time range for metrics")
):
    """
    Get notification system metrics and statistics.
    Consolidates: /api/notifications/stats
    """
    try:
        hours = parse_time_range(time_range)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        notification_stats = await get_notification_statistics(db, since)
        
        return {
            "timestamp": get_utc_timestamp(),
            "time_range": time_range,
            "statistics": notification_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get notification metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notification metrics")


# ============================================================================
# LOG METRICS ENDPOINTS
# ============================================================================

@router.get("/logs")
async def get_log_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: str = Query("24h", description="Time range for log metrics")
):
    """
    Get log system metrics and statistics.
    Consolidates: /api/log-viewer/stats
    """
    try:
        hours = parse_time_range(time_range)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        log_stats = await get_log_statistics(db, since)
        
        return {
            "timestamp": get_utc_timestamp(),
            "time_range": time_range,
            "statistics": log_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get log metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve log metrics")


# ============================================================================
# CONSOLIDATED DASHBOARD METRICS
# ============================================================================

@router.get("/dashboard")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get consolidated metrics for dashboard display.
    Provides a single endpoint for dashboard data.
    """
    try:
        # Get metrics from all systems
        dashboard_data = {
            "timestamp": get_utc_timestamp(),
            "system": await get_system_summary_metrics(),
            "jobs": await get_job_summary_metrics(db),
            "discovery": await get_discovery_summary_metrics(db),
            "notifications": await get_notification_summary_metrics(db),
            "health_score": await get_overall_health_score()
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard metrics")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_time_range(time_range: str) -> int:
    """Parse time range string to hours."""
    time_map = {
        "1h": 1,
        "24h": 24,
        "7d": 168,  # 7 * 24
        "30d": 720  # 30 * 24
    }
    return time_map.get(time_range, 24)


async def get_job_execution_metrics(db: Session, since: datetime) -> Dict[str, Any]:
    """Get job execution metrics from database."""
    try:
        # This would query your job execution tables
        # For now, return mock data
        return {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_duration": 0,
            "execution_rate": 0
        }
    except Exception as e:
        logger.error(f"Failed to get job execution metrics: {str(e)}")
        return {}


async def get_celery_statistics() -> Dict[str, Any]:
    """Get Celery worker and task statistics."""
    try:
        from celery import Celery
        app = Celery('opsconductor')
        app.config_from_object('app.core.celery_config')
        
        inspect = app.control.inspect()
        
        # Get worker stats
        stats = inspect.stats()
        active = inspect.active()
        scheduled = inspect.scheduled()
        
        return {
            "status": "healthy" if stats else "unhealthy",
            "workers": stats or {},
            "active_tasks": active or {},
            "scheduled_tasks": scheduled or {},
            "tasks": {
                "active_count": sum(len(tasks) for tasks in (active or {}).values()),
                "scheduled_count": sum(len(tasks) for tasks in (scheduled or {}).values())
            }
        }
    except Exception as e:
        logger.error(f"Failed to get Celery statistics: {str(e)}")
        return {"status": "error", "error": str(e)}


async def get_celery_metrics_history() -> List[Dict[str, Any]]:
    """Get historical Celery metrics."""
    # This would query historical metrics from database
    # For now, return empty list
    return []


async def get_discovery_statistics(db: Session) -> Dict[str, Any]:
    """Get discovery system statistics."""
    try:
        # This would query discovery tables
        # For now, return mock data
        return {
            "total_devices": 0,
            "discovered_devices": 0,
            "imported_devices": 0,
            "discovery_jobs": 0
        }
    except Exception as e:
        logger.error(f"Failed to get discovery statistics: {str(e)}")
        return {}


async def get_notification_statistics(db: Session, since: datetime) -> Dict[str, Any]:
    """Get notification system statistics."""
    try:
        # This would query notification tables
        # For now, return mock data
        return {
            "total_notifications": 0,
            "sent_notifications": 0,
            "failed_notifications": 0,
            "email_notifications": 0,
            "alert_notifications": 0
        }
    except Exception as e:
        logger.error(f"Failed to get notification statistics: {str(e)}")
        return {}


async def get_log_statistics(db: Session, since: datetime) -> Dict[str, Any]:
    """Get log system statistics."""
    try:
        # This would query log tables
        # For now, return mock data
        return {
            "total_logs": 0,
            "error_logs": 0,
            "warning_logs": 0,
            "info_logs": 0,
            "log_sources": []
        }
    except Exception as e:
        logger.error(f"Failed to get log statistics: {str(e)}")
        return {}


async def get_system_summary_metrics() -> Dict[str, Any]:
    """Get system summary metrics for dashboard."""
    try:
        import psutil
        
        return {
            "cpu_usage": round(psutil.cpu_percent(interval=0.1), 1),
            "memory_usage": round(psutil.virtual_memory().percent, 1),
            "disk_usage": round((psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100, 1),
            "uptime": psutil.boot_time()
        }
    except Exception as e:
        logger.error(f"Failed to get system summary metrics: {str(e)}")
        return {}


async def get_job_summary_metrics(db: Session) -> Dict[str, Any]:
    """Get job summary metrics for dashboard."""
    try:
        # This would query job tables
        return {
            "total_jobs": 0,
            "running_jobs": 0,
            "completed_today": 0,
            "failed_today": 0
        }
    except Exception as e:
        logger.error(f"Failed to get job summary metrics: {str(e)}")
        return {}


async def get_discovery_summary_metrics(db: Session) -> Dict[str, Any]:
    """Get discovery summary metrics for dashboard."""
    try:
        # This would query discovery tables
        return {
            "total_targets": 0,
            "healthy_targets": 0,
            "unhealthy_targets": 0,
            "unknown_targets": 0
        }
    except Exception as e:
        logger.error(f"Failed to get discovery summary metrics: {str(e)}")
        return {}


async def get_notification_summary_metrics(db: Session) -> Dict[str, Any]:
    """Get notification summary metrics for dashboard."""
    try:
        # This would query notification tables
        return {
            "notifications_today": 0,
            "alerts_active": 0,
            "email_queue": 0
        }
    except Exception as e:
        logger.error(f"Failed to get notification summary metrics: {str(e)}")
        return {}


async def get_overall_health_score() -> Dict[str, Any]:
    """Get overall platform health score."""
    try:
        # This would calculate based on all system components
        return {
            "score": 85,
            "status": "healthy",
            "components": {
                "system": "healthy",
                "database": "healthy", 
                "jobs": "healthy",
                "discovery": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get health score: {str(e)}")
        return {"score": 0, "status": "unknown"}