"""
System API Endpoints
Health checks, metrics, and system information
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
import logging

from app.core.database import get_db
from app.core.config import settings
from app.schemas.job_schemas import (
    HealthCheckResponse, ServiceMetricsResponse, JobStatsResponse
)
from app.services.auth_service import get_current_user
from app.models.job_models import Job, JobExecution, ExecutionStatus, JobStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Test Redis connection (simplified)
    redis_status = "healthy"  # TODO: Implement actual Redis health check
    
    # Test external services
    external_services = {
        "target_service": "unknown",  # TODO: Implement service health checks
        "user_service": "unknown",
        "notification_service": "unknown"
    }
    
    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy"
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        version=settings.version,
        database=db_status,
        redis=redis_status,
        external_services=external_services
    )


@router.get("/metrics", response_model=ServiceMetricsResponse)
async def get_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get service metrics"""
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        
        # Active jobs count
        active_jobs = db.query(func.count(Job.id)).filter(
            Job.status.in_([JobStatus.RUNNING, JobStatus.SCHEDULED]),
            Job.is_deleted == False
        ).scalar() or 0
        
        # Running executions count
        running_executions = db.query(func.count(JobExecution.id)).filter(
            JobExecution.status == ExecutionStatus.RUNNING
        ).scalar() or 0
        
        # Total executions today
        executions_today = db.query(func.count(JobExecution.id)).filter(
            JobExecution.created_at >= today_start
        ).scalar() or 0
        
        # Success rate last 24 hours
        executions_24h = db.query(func.count(JobExecution.id)).filter(
            JobExecution.created_at >= yesterday_start,
            JobExecution.status.in_([ExecutionStatus.COMPLETED, ExecutionStatus.FAILED])
        ).scalar() or 0
        
        successful_24h = db.query(func.count(JobExecution.id)).filter(
            JobExecution.created_at >= yesterday_start,
            JobExecution.status == ExecutionStatus.COMPLETED
        ).scalar() or 0
        
        success_rate_24h = (successful_24h / executions_24h * 100) if executions_24h > 0 else 0
        
        # Average execution time
        avg_execution_time = db.query(func.avg(JobExecution.execution_time_seconds)).filter(
            JobExecution.created_at >= yesterday_start,
            JobExecution.status == ExecutionStatus.COMPLETED,
            JobExecution.execution_time_seconds.isnot(None)
        ).scalar() or 0
        
        # Worker status (simplified)
        worker_status = {
            "active_workers": 1,  # TODO: Get actual worker count
            "queued_tasks": 0,    # TODO: Get actual queue depth
            "failed_tasks": 0     # TODO: Get failed task count
        }
        
        return ServiceMetricsResponse(
            active_jobs=active_jobs,
            running_executions=running_executions,
            queued_tasks=worker_status["queued_tasks"],
            total_executions_today=executions_today,
            success_rate_24h=round(success_rate_24h, 2),
            average_execution_time=round(float(avg_execution_time or 0), 2),
            worker_status=worker_status
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@router.get("/stats", response_model=JobStatsResponse)
async def get_job_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job statistics"""
    try:
        now = datetime.now(timezone.utc)
        yesterday_start = now - timedelta(days=1)
        
        # Total jobs
        total_jobs = db.query(func.count(Job.id)).filter(
            Job.is_deleted == False
        ).scalar() or 0
        
        # Jobs by status
        status_counts = db.query(
            Job.status,
            func.count(Job.id)
        ).filter(
            Job.is_deleted == False
        ).group_by(Job.status).all()
        
        jobs_by_status = {status.value: count for status, count in status_counts}
        
        # Jobs by type
        type_counts = db.query(
            Job.job_type,
            func.count(Job.id)
        ).filter(
            Job.is_deleted == False
        ).group_by(Job.job_type).all()
        
        jobs_by_type = {job_type.value: count for job_type, count in type_counts}
        
        # Executions last 24h
        executions_24h = db.query(func.count(JobExecution.id)).filter(
            JobExecution.created_at >= yesterday_start
        ).scalar() or 0
        
        # Success rate
        completed_executions = db.query(func.count(JobExecution.id)).filter(
            JobExecution.created_at >= yesterday_start,
            JobExecution.status == ExecutionStatus.COMPLETED
        ).scalar() or 0
        
        success_rate = (completed_executions / executions_24h * 100) if executions_24h > 0 else 0
        
        # Most active users (simplified)
        most_active_users = db.query(
            Job.created_by,
            func.count(Job.id).label('job_count')
        ).filter(
            Job.is_deleted == False,
            Job.created_at >= yesterday_start
        ).group_by(Job.created_by).order_by(
            func.count(Job.id).desc()
        ).limit(5).all()
        
        active_users = [
            {"user_id": user_id, "job_count": count}
            for user_id, count in most_active_users
        ]
        
        return JobStatsResponse(
            total_jobs=total_jobs,
            jobs_by_status=jobs_by_status,
            jobs_by_type=jobs_by_type,
            executions_last_24h=executions_24h,
            success_rate=round(success_rate, 2),
            most_active_users=active_users
        )
        
    except Exception as e:
        logger.error(f"Failed to get job stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job stats")


@router.get("/version")
async def get_version():
    """Get service version information"""
    return {
        "service": settings.service_name,
        "version": settings.version,
        "environment": settings.environment,
        "debug": settings.debug
    }