"""
Analytics API v1 for insights and metrics.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database.database import get_db
from main import get_current_user
from app.models.user_models import User
from app.domains.analytics.services.analytics_service import AnalyticsService
from app.shared.infrastructure.cache import cached

router = APIRouter(prefix="/api/v1/analytics")


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Get analytics service with dependencies."""
    return AnalyticsService(db)


@router.get("/dashboard")
async def get_dashboard_metrics(
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard metrics."""
    metrics = await service.get_dashboard_metrics()
    return metrics


@router.get("/jobs/performance")
async def get_job_performance_analysis(
    job_id: Optional[int] = None,
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user)
):
    """Get detailed job performance analysis."""
    analysis = await service.get_job_performance_analysis(job_id)
    return analysis


@router.get("/system/health")
async def get_system_health_report(
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive system health report."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view system health"
        )
    
    report = await service.get_system_health_report()
    return report


@router.get("/trends/executions")
@cached(ttl=600, key_prefix="analytics_execution_trends")
async def get_execution_trends(
    days: int = 30,
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user)
):
    """Get execution trends over time."""
    # This would be implemented in the analytics service
    return {"message": f"Execution trends for last {days} days"}


@router.get("/reports/summary")
async def get_summary_report(
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user)
):
    """Get summary report for management."""
    if current_user.role not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access summary reports"
        )
    
    dashboard_metrics = await service.get_dashboard_metrics()
    health_report = await service.get_system_health_report()
    
    return {
        "summary": {
            "total_jobs": dashboard_metrics["overview"]["totals"]["jobs"],
            "total_targets": dashboard_metrics["overview"]["totals"]["targets"],
            "total_executions": dashboard_metrics["overview"]["totals"]["executions"],
            "success_rate": dashboard_metrics["job_metrics"]["success_rate_30d"],
            "health_score": health_report["health_score"],
            "system_status": health_report["status"]
        },
        "key_metrics": dashboard_metrics,
        "health_report": health_report
    }