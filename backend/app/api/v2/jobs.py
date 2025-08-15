"""
Jobs API v2 - Consolidated Job Management
Consolidates all job-related endpoints into a unified API.

This replaces and consolidates:
- /api/jobs/* (jobs.py) - Core job management
- /api/job-safety/* (job_safety_routes.py) - Job safety operations  
- /api/jobs/schedules/* (job_scheduling_routes.py) - Job scheduling
- /api/celery-monitor/* (celery_monitor.py) - Task monitoring
- /api/discovery/jobs/* (discovery.py) - Discovery jobs
- /api/analytics/jobs/* (analytics.py) - Job analytics
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import verify_token
from app.models.user_models import User
from app.services.job_service import JobService
from app.services.user_service import UserService
from app.schemas.job_schemas import (
    JobCreate, JobResponse, JobListResponse, JobSchedule, JobExecuteRequest,
    JobExecutionResponse, JobWithExecutionsResponse, JobActionResultResponse
)
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
from app.tasks.job_tasks import execute_job_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/jobs", tags=["Jobs Management v2"])
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


def get_utc_timestamp() -> str:
    """Get current UTC timestamp with timezone information."""
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# CORE JOB MANAGEMENT (Consolidates: /api/jobs/*)
# ============================================================================

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job."""
    try:
        job = JobService.create_job(db, job_data, current_user.id)
        
        # Log job creation
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_CREATED,
            user_id=current_user.id,
            resource_type="job",
            resource_id=str(job.id),
            action="create_job",
            details={"job_name": job.name, "job_type": job.job_type},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return JobResponse.from_orm(job)
        
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create job")


@router.get("/", response_model=JobListResponse)
async def get_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    job_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get jobs with filtering and pagination."""
    try:
        jobs, total = JobService.get_jobs_paginated(
            db, skip=skip, limit=limit, 
            job_type=job_type, status=status, search=search
        )
        
        return JobListResponse(
            jobs=[JobResponse.from_orm(job) for job in jobs],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve jobs")


@router.get("/{job_id}", response_model=JobWithExecutionsResponse)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_executions: bool = Query(True)
):
    """Get job by ID with optional execution history."""
    try:
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if include_executions:
            executions = JobService.get_job_executions(db, job_id)
            return JobWithExecutionsResponse(
                **JobResponse.from_orm(job).dict(),
                executions=[JobExecutionResponse.from_orm(exec) for exec in executions]
            )
        else:
            return JobWithExecutionsResponse(**JobResponse.from_orm(job).dict(), executions=[])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job")


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing job."""
    try:
        job = JobService.update_job(db, job_id, job_data, current_user.id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Log job update
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_UPDATED,
            user_id=current_user.id,
            resource_type="job",
            resource_id=str(job.id),
            action="update_job",
            details={"job_name": job.name, "updated_fields": list(job_data.dict().keys())},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return JobResponse.from_orm(job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update job")


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a job."""
    try:
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        success = JobService.delete_job(db, job_id, current_user.id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete job")
        
        # Log job deletion
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_DELETED,
            user_id=current_user.id,
            resource_type="job",
            resource_id=str(job_id),
            action="delete_job",
            details={"job_name": job.name},
            severity=AuditSeverity.HIGH,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete job")


# ============================================================================
# JOB EXECUTION (Consolidates: /api/jobs/{id}/execute, /api/jobs/{id}/executions/*)
# ============================================================================

@router.post("/{job_id}/execute", response_model=JobExecutionResponse)
async def execute_job(
    job_id: int,
    execute_request: JobExecuteRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a job immediately."""
    try:
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Create execution record
        execution = JobService.create_job_execution(
            db, job_id, current_user.id, execute_request
        )
        
        # Queue the job for execution
        task = execute_job_task.delay(execution.id)
        
        # Update execution with task ID
        JobService.update_execution_task_id(db, execution.id, task.id)
        
        # Log job execution
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.JOB_EXECUTED,
            user_id=current_user.id,
            resource_type="job_execution",
            resource_id=str(execution.id),
            action="execute_job",
            details={"job_name": job.name, "execution_id": execution.id},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return JobExecutionResponse.from_orm(execution)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to execute job")


@router.get("/{job_id}/executions", response_model=List[JobExecutionResponse])
async def get_job_executions(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None)
):
    """Get job execution history."""
    try:
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        executions = JobService.get_job_executions_paginated(
            db, job_id, skip=skip, limit=limit, status=status
        )
        
        return [JobExecutionResponse.from_orm(exec) for exec in executions]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get executions for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve executions")


@router.get("/{job_id}/executions/{execution_id}", response_model=JobExecutionResponse)
async def get_job_execution(
    job_id: int,
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific job execution details."""
    try:
        execution = JobService.get_job_execution_by_id(db, execution_id)
        if not execution or execution.job_id != job_id:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return JobExecutionResponse.from_orm(execution)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve execution")


# ============================================================================
# JOB SCHEDULING (Consolidates: /api/jobs/schedules/*)
# ============================================================================

@router.post("/{job_id}/schedules", response_model=Dict[str, Any])
async def create_job_schedule(
    job_id: int,
    schedule_data: JobSchedule,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a schedule for a job."""
    try:
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        schedule = JobService.create_job_schedule(db, job_id, schedule_data, current_user.id)
        
        # Log schedule creation
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_CREATED,
            user_id=current_user.id,
            resource_type="job_schedule",
            resource_id=str(schedule.id),
            action="create_schedule",
            details={"job_name": job.name, "schedule_type": schedule_data.schedule_type},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return {
            "id": schedule.id,
            "job_id": job_id,
            "schedule_type": schedule.schedule_type,
            "cron_expression": schedule.cron_expression,
            "is_active": schedule.is_active,
            "created_at": schedule.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create schedule for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create schedule")


@router.get("/{job_id}/schedules", response_model=List[Dict[str, Any]])
async def get_job_schedules(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all schedules for a job."""
    try:
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        schedules = JobService.get_job_schedules(db, job_id)
        
        return [
            {
                "id": schedule.id,
                "job_id": job_id,
                "schedule_type": schedule.schedule_type,
                "cron_expression": schedule.cron_expression,
                "is_active": schedule.is_active,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None
            }
            for schedule in schedules
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schedules for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve schedules")


@router.put("/{job_id}/schedules/{schedule_id}", response_model=Dict[str, Any])
async def update_job_schedule(
    job_id: int,
    schedule_id: int,
    schedule_data: JobSchedule,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a job schedule."""
    try:
        schedule = JobService.update_job_schedule(db, schedule_id, schedule_data, current_user.id)
        if not schedule or schedule.job_id != job_id:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Log schedule update
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_UPDATED,
            user_id=current_user.id,
            resource_type="job_schedule",
            resource_id=str(schedule_id),
            action="update_schedule",
            details={"schedule_id": schedule_id, "updated_fields": list(schedule_data.dict().keys())},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return {
            "id": schedule.id,
            "job_id": job_id,
            "schedule_type": schedule.schedule_type,
            "cron_expression": schedule.cron_expression,
            "is_active": schedule.is_active,
            "updated_at": schedule.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update schedule")


@router.delete("/{job_id}/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_schedule(
    job_id: int,
    schedule_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a job schedule."""
    try:
        success = JobService.delete_job_schedule(db, schedule_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Log schedule deletion
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_DELETED,
            user_id=current_user.id,
            resource_type="job_schedule",
            resource_id=str(schedule_id),
            action="delete_schedule",
            details={"schedule_id": schedule_id, "job_id": job_id},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete schedule")


# ============================================================================
# JOB SAFETY & MANAGEMENT (Consolidates: /api/job-safety/*)
# ============================================================================

@router.post("/cleanup/stale", response_model=Dict[str, Any])
async def cleanup_stale_jobs(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    max_age_hours: int = Query(24, ge=1, le=168, description="Maximum age in hours for stale jobs")
):
    """Clean up stale job executions."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to cleanup stale jobs"
        )
    
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        cleaned_count = JobService.cleanup_stale_executions(db, cutoff_time)
        
        # Log cleanup operation
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.SYSTEM_MAINTENANCE,
            user_id=current_user.id,
            resource_type="job_execution",
            resource_id="bulk",
            action="cleanup_stale_jobs",
            details={"cleaned_count": cleaned_count, "max_age_hours": max_age_hours},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "cutoff_time": cutoff_time.isoformat(),
            "timestamp": get_utc_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup stale jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cleanup stale jobs")


@router.post("/{job_id}/terminate", response_model=Dict[str, Any])
async def terminate_job_execution(
    job_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    execution_id: Optional[int] = Query(None, description="Specific execution ID to terminate")
):
    """Force terminate a running job execution."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to terminate jobs"
        )
    
    try:
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        terminated_count = JobService.terminate_job_executions(db, job_id, execution_id)
        
        # Log termination
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.JOB_TERMINATED,
            user_id=current_user.id,
            resource_type="job_execution",
            resource_id=str(execution_id) if execution_id else str(job_id),
            action="terminate_job",
            details={"job_name": job.name, "terminated_count": terminated_count},
            severity=AuditSeverity.HIGH,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "terminated_count": terminated_count,
            "timestamp": get_utc_timestamp()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to terminate job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to terminate job")


# ============================================================================
# JOB ANALYTICS & REPORTING (Consolidates: /api/analytics/jobs/*)
# ============================================================================

@router.get("/analytics/performance", response_model=Dict[str, Any])
async def get_job_performance_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: str = Query("7d", description="Time range: 1d, 7d, 30d"),
    job_type: Optional[str] = Query(None, description="Filter by job type")
):
    """Get job performance analytics."""
    try:
        # Parse time range
        hours_map = {"1d": 24, "7d": 168, "30d": 720}
        hours = hours_map.get(time_range, 168)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        analytics = JobService.get_job_performance_analytics(db, since, job_type)
        
        return {
            "timestamp": get_utc_timestamp(),
            "time_range": time_range,
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get job performance analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@router.get("/analytics/summary", response_model=Dict[str, Any])
async def get_job_summary_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job summary analytics for dashboard."""
    try:
        summary = JobService.get_job_summary_analytics(db)
        
        return {
            "timestamp": get_utc_timestamp(),
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get job summary analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve summary")


# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/bulk/execute", response_model=Dict[str, Any])
async def bulk_execute_jobs(
    job_ids: List[int],
    execute_request: JobExecuteRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute multiple jobs at once."""
    try:
        results = []
        for job_id in job_ids:
            try:
                job = JobService.get_job_by_id(db, job_id)
                if job:
                    execution = JobService.create_job_execution(
                        db, job_id, current_user.id, execute_request
                    )
                    task = execute_job_task.delay(execution.id)
                    JobService.update_execution_task_id(db, execution.id, task.id)
                    results.append({"job_id": job_id, "execution_id": execution.id, "status": "queued"})
                else:
                    results.append({"job_id": job_id, "status": "not_found"})
            except Exception as e:
                results.append({"job_id": job_id, "status": "error", "error": str(e)})
        
        # Log bulk execution
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.BULK_OPERATION,
            user_id=current_user.id,
            resource_type="job",
            resource_id="bulk",
            action="bulk_execute_jobs",
            details={"job_ids": job_ids, "results_count": len(results)},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return {
            "success": True,
            "results": results,
            "timestamp": get_utc_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk execute jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to bulk execute jobs")


# ============================================================================
# SEARCH & FILTERING
# ============================================================================

@router.post("/search", response_model=JobListResponse)
async def search_jobs(
    search_params: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Advanced job search with complex filtering."""
    try:
        jobs, total = JobService.search_jobs(db, search_params, skip=skip, limit=limit)
        
        return JobListResponse(
            jobs=[JobResponse.from_orm(job) for job in jobs],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to search jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search jobs")