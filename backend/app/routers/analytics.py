from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import redis
from datetime import datetime

from app.database.database import get_db
from app.core.config import settings
from app.services.analytics_service import AnalyticsService
from app.services.simple_analytics_service import SimpleAnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Real-Time Dashboard Metrics
# ---------------------------------------------------------------------

@router.get("/dashboard")
async def get_dashboard_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get real-time dashboard metrics."""
    try:
        analytics_service = SimpleAnalyticsService(db)
        return analytics_service.get_realtime_dashboard_metrics()
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get dashboard metrics")

# ---------------------------------------------------------------------
# Executive summary endpoint
# ---------------------------------------------------------------------

@router.get("/summary")
async def get_executive_summary(db: Session = Depends(get_db)):
    try:
        service = AnalyticsService(db)
        return service.get_executive_summary()
    except Exception as e:
        logger.error(f"Failed to build executive summary: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to build analytics summary")

# ---------------------------------------------------------------------
# Job Performance Analytics
# ---------------------------------------------------------------------

@router.get("/jobs/performance")
async def get_job_performance_analytics(
    job_id: Optional[int] = Query(None, description="Specific job ID to analyze"),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed job performance analytics."""
    try:
        analytics_service = AnalyticsService(db)
        return analytics_service.get_job_performance_analytics(job_id=job_id, days=days)
    except Exception as e:
        logger.error(f"Failed to get job performance analytics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get job performance analytics")

# ---------------------------------------------------------------------
# Target Performance Analytics
# ---------------------------------------------------------------------

@router.get("/targets/performance")
async def get_target_performance_analytics(
    target_id: Optional[int] = Query(None, description="Specific target ID to analyze"),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed target performance analytics."""
    try:
        analytics_service = AnalyticsService(db)
        return analytics_service.get_target_performance_analytics(target_id=target_id, days=days)
    except Exception as e:
        logger.error(f"Failed to get target performance analytics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get target performance analytics")

# ---------------------------------------------------------------------
# Reporting Endpoints
# ---------------------------------------------------------------------

@router.get("/reports/executive")
async def generate_executive_report(
    days: int = Query(30, description="Number of days to include in report", ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generate executive summary report."""
    try:
        analytics_service = AnalyticsService(db)
        return analytics_service.generate_executive_report(days=days)
    except Exception as e:
        logger.error(f"Failed to generate executive report: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate executive report")

# ---------------------------------------------------------------------
# Trends and Error Analysis
# ---------------------------------------------------------------------

@router.get("/trends/performance")
async def get_performance_trends(
    hours: int = Query(24, description="Number of hours to analyze", ge=1, le=168),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get performance trends over specified time period."""
    try:
        analytics_service = AnalyticsService(db)
        return analytics_service._get_performance_trends(hours=hours)
    except Exception as e:
        logger.error(f"Failed to get performance trends: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get performance trends")

@router.get("/errors/summary")
async def get_error_summary(
    hours: int = Query(24, description="Number of hours to analyze", ge=1, le=168),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get error summary and categorization."""
    try:
        analytics_service = AnalyticsService(db)
        return analytics_service._get_error_summary(hours=hours)
    except Exception as e:
        logger.error(f"Failed to get error summary: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get error summary")

# ---------------------------------------------------------------------
# Resource utilization endpoint (Enhanced)
# ---------------------------------------------------------------------

@router.get("/resources")
async def get_resource_utilization():
    """Return basic resource stats: Celery queue depth. (CPU/mem placeholders.)"""
    try:
        r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        queue_len = r.llen("job_execution")
    except Exception as e:
        logger.error(f"Redis error: {e}")
        queue_len = None

    # CPU/memory placeholders (need psutil inside container)
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "celery_queue_length": queue_len,
        "cpu_percent_backend": None,
        "mem_percent_backend": None,
    }

