"""
Analytics API v3 - Consolidated analytics endpoints for frontend
Different from metrics API - focuses on business analytics and reporting
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.core.logging import get_structured_logger

api_base_url = os.getenv("API_BASE_URL", "/api/v1")
router = APIRouter(prefix=f"{api_base_url}/analytics", tags=["Analytics v1"])

# Configure structured logger
logger = get_structured_logger(__name__)


# MODELS

class DashboardMetrics(BaseModel):
    """Model for dashboard metrics"""
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    active_targets: int
    recent_activity: List[Dict[str, Any]]


class JobPerformanceMetrics(BaseModel):
    """Model for job performance analytics"""
    average_duration: float
    success_rate: float
    failure_rate: float
    jobs_per_hour: float
    peak_hours: List[int]
    performance_trend: List[Dict[str, Any]]





class ExecutionTrends(BaseModel):
    """Model for execution trend analytics"""
    period: str
    total_executions: int
    success_trend: List[Dict[str, Any]]
    failure_trend: List[Dict[str, Any]]
    duration_trend: List[Dict[str, Any]]


class ReportSummary(BaseModel):
    """Model for report summary"""
    report_type: str
    generated_at: datetime
    period: str
    key_metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]


# ENDPOINTS

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard analytics metrics"""
    try:
        # Mock dashboard metrics
        recent_activity = [
            {
                "type": "job_completed",
                "message": "Backup job completed successfully",
                "timestamp": datetime.now(timezone.utc) - timedelta(minutes=5),
                "status": "success"
            },
            {
                "type": "target_added",
                "message": "New target server-01 added",
                "timestamp": datetime.now(timezone.utc) - timedelta(minutes=15),
                "status": "info"
            },
            {
                "type": "job_failed",
                "message": "Update job failed on 2 targets",
                "timestamp": datetime.now(timezone.utc) - timedelta(minutes=30),
                "status": "error"
            }
        ]
        
        metrics = DashboardMetrics(
            total_jobs=156,
            successful_jobs=142,
            failed_jobs=14,
            active_targets=25,
            system_health_score=87.5,
            recent_activity=recent_activity
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard metrics: {str(e)}"
        )


@router.get("/jobs/performance", response_model=JobPerformanceMetrics)
async def get_job_performance_metrics(
    days: int = Query(7, ge=1, le=90),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job performance analytics"""
    try:
        # Mock performance trend data
        performance_trend = []
        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=i)
            performance_trend.append({
                "date": date.date().isoformat(),
                "avg_duration": 45.5 + (i % 10),
                "success_rate": 90.0 + (i % 8),
                "job_count": 20 + (i % 5)
            })
        
        metrics = JobPerformanceMetrics(
            average_duration=47.3,
            success_rate=91.2,
            failure_rate=8.8,
            jobs_per_hour=6.5,
            peak_hours=[9, 10, 14, 15, 16],
            performance_trend=performance_trend
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get job performance metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job performance metrics: {str(e)}"
        )





@router.get("/trends/executions", response_model=ExecutionTrends)
async def get_execution_trends(
    period: str = Query("week", regex="^(day|week|month)$"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get execution trend analytics"""
    try:
        # Determine data points based on period
        if period == "day":
            data_points = 24  # Hours
            time_unit = "hour"
        elif period == "week":
            data_points = 7   # Days
            time_unit = "day"
        else:  # month
            data_points = 30  # Days
            time_unit = "day"
        
        # Mock trend data
        success_trend = []
        failure_trend = []
        duration_trend = []
        
        for i in range(data_points):
            if period == "day":
                timestamp = datetime.now(timezone.utc) - timedelta(hours=i)
            else:
                timestamp = datetime.now(timezone.utc) - timedelta(days=i)
            
            success_trend.append({
                "timestamp": timestamp.isoformat(),
                "value": 15 + (i % 8)
            })
            
            failure_trend.append({
                "timestamp": timestamp.isoformat(),
                "value": 2 + (i % 3)
            })
            
            duration_trend.append({
                "timestamp": timestamp.isoformat(),
                "value": 45.0 + (i % 15)
            })
        
        trends = ExecutionTrends(
            period=period,
            total_executions=sum(point["value"] for point in success_trend) + sum(point["value"] for point in failure_trend),
            success_trend=success_trend,
            failure_trend=failure_trend,
            duration_trend=duration_trend
        )
        
        return trends
        
    except Exception as e:
        logger.error(f"Failed to get execution trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution trends: {str(e)}"
        )


@router.get("/reports/summary", response_model=ReportSummary)
async def get_report_summary(
    report_type: str = Query("weekly", regex="^(daily|weekly|monthly)$"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics report summary"""
    try:
        # Mock key metrics based on report type
        if report_type == "daily":
            key_metrics = {
                "jobs_executed": 24,
                "success_rate": 91.7,
                "avg_duration": 42.3,
                "targets_active": 25,
                "system_uptime": 99.8
            }
            insights = [
                "Job success rate improved by 2.3% compared to yesterday",
                "Peak execution time was between 2-4 PM",
                "No critical system alerts in the last 24 hours"
            ]
        elif report_type == "weekly":
            key_metrics = {
                "jobs_executed": 168,
                "success_rate": 89.3,
                "avg_duration": 45.7,
                "targets_active": 25,
                "system_uptime": 99.2
            }
            insights = [
                "Weekly job volume increased by 12% compared to last week",
                "Monday and Tuesday showed highest activity",
                "2 minor system alerts resolved automatically"
            ]
        else:  # monthly
            key_metrics = {
                "jobs_executed": 720,
                "success_rate": 87.8,
                "avg_duration": 48.2,
                "targets_active": 25,
                "system_uptime": 98.7
            }
            insights = [
                "Monthly job success rate within acceptable range",
                "System performance stable throughout the month",
                "Target health checks show consistent results"
            ]
        
        recommendations = [
            "Consider optimizing job scripts to reduce execution time",
            "Schedule maintenance during low-activity periods",
            "Monitor disk usage trends for capacity planning"
        ]
        
        summary = ReportSummary(
            report_type=report_type,
            generated_at=datetime.now(timezone.utc),
            period=report_type,
            key_metrics=key_metrics,
            insights=insights,
            recommendations=recommendations
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get report summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report summary: {str(e)}"
        )





@router.get("/jobs/category-breakdown")
async def get_job_category_breakdown(
    days: int = Query(30, ge=1, le=90),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job execution breakdown by category"""
    try:
        breakdown = {
            "categories": {
                "maintenance": {"count": 45, "success_rate": 93.3, "avg_duration": 35.2},
                "backup": {"count": 38, "success_rate": 97.4, "avg_duration": 120.5},
                "monitoring": {"count": 52, "success_rate": 88.5, "avg_duration": 15.8},
                "deployment": {"count": 23, "success_rate": 82.6, "avg_duration": 180.3},
                "security": {"count": 18, "success_rate": 94.4, "avg_duration": 45.7}
            },
            "period_days": days,
            "total_jobs": 176,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return breakdown
        
    except Exception as e:
        logger.error(f"Failed to get job category breakdown: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job category breakdown: {str(e)}"
        )


@router.get("/usage/patterns")
async def get_usage_patterns(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system usage patterns analytics"""
    try:
        patterns = {
            "peak_hours": {
                "weekday": [9, 10, 14, 15, 16],
                "weekend": [10, 11, 15]
            },
            "busiest_days": ["Tuesday", "Wednesday", "Thursday"],
            "job_frequency": {
                "hourly": 6.5,
                "daily": 156,
                "weekly": 1092
            },
            "user_activity": {
                "most_active_users": [
                    {"user_id": 1, "username": "admin", "job_count": 45},
                    {"user_id": 2, "username": "operator1", "job_count": 38},
                    {"user_id": 3, "username": "operator2", "job_count": 32}
                ],
                "total_active_users": 8
            },
            "resource_utilization": {
                "avg_cpu_during_jobs": 65.2,
                "avg_memory_during_jobs": 72.8,
                "peak_concurrent_jobs": 12
            },
            "analysis_period": "last_30_days",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return patterns
        
    except Exception as e:
        logger.error(f"Failed to get usage patterns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage patterns: {str(e)}"
        )