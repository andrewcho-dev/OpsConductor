from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

from ..database.database import get_db
from ..services.system_service import SystemService
from ..tasks.cleanup_tasks import CleanupTasks
from ..models.user_models import User
from ..models.universal_target_models import UniversalTarget
from ..models.job_models import Job, JobExecution, ExecutionStatus

router = APIRouter(prefix="/api/system", tags=["system"])


class SystemSettingResponse(BaseModel):
    id: int
    setting_key: str
    setting_value: Any
    description: str
    updated_at: datetime


class TimezoneUpdateRequest(BaseModel):
    timezone: str


class DSTRulesUpdateRequest(BaseModel):
    dst_rules: Dict[str, Any]


class SessionTimeoutUpdateRequest(BaseModel):
    timeout_seconds: int


class MaxJobsUpdateRequest(BaseModel):
    max_jobs: int


class LogRetentionUpdateRequest(BaseModel):
    retention_days: int


class JobScheduleValidationRequest(BaseModel):
    local_time: datetime


@router.get("/settings", response_model=List[SystemSettingResponse])
async def get_all_settings(db: Session = Depends(get_db)):
    """Get all system settings"""
    service = SystemService(db)
    settings = service.get_all_settings()
    return settings


@router.get("/info")
async def get_system_info(db: Session = Depends(get_db)):
    """Get comprehensive system information"""
    service = SystemService(db)
    return service.get_system_info()


@router.get("/dashboard-stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics for active users, targets, and jobs"""
    try:
        # Count only active users
        total_users = db.query(User).filter(User.is_active == True).count()
        
        # Count only active targets
        total_targets = db.query(UniversalTarget).filter(UniversalTarget.is_active == True).count()
        
        # Count active jobs (running executions)
        active_jobs = db.query(JobExecution).filter(JobExecution.status == ExecutionStatus.RUNNING).count()
        
        # Get system health status
        system_health = "healthy"  # This could be enhanced with actual health checks
        
        # Calculate uptime (placeholder - could be enhanced with actual system start time)
        uptime = "5d 12h"  # This could be calculated from actual system start time
        
        # Get last activity timestamp
        last_execution = db.query(JobExecution).order_by(JobExecution.created_at.desc()).first()
        last_activity = last_execution.created_at.strftime("%H:%M:%S") if last_execution else "N/A"
        
        return {
            "totalTargets": total_targets,
            "activeJobs": active_jobs,
            "totalUsers": total_users,
            "systemHealth": system_health,
            "uptime": uptime,
            "lastActivity": last_activity
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting dashboard statistics: {str(e)}"
        )


@router.get("/timezone")
async def get_timezone(db: Session = Depends(get_db)):
    """Get current system timezone"""
    service = SystemService(db)
    return {
        "timezone": service.get_timezone(),
        "display_name": service.get_timezone_display_name(),
        "is_dst_active": service.is_dst_active(),
        "current_utc_offset": service.get_current_utc_offset()
    }


@router.put("/timezone")
async def update_timezone(
    request: TimezoneUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update system timezone"""
    service = SystemService(db)
    success = service.set_timezone(request.timezone)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timezone name"
        )
    
    return {
        "message": "Timezone updated successfully",
        "timezone": service.get_timezone(),
        "display_name": service.get_timezone_display_name()
    }


@router.get("/timezones")
async def get_available_timezones(db: Session = Depends(get_db)):
    """Get list of available timezones"""
    service = SystemService(db)
    return service.get_available_timezones()


@router.get("/dst-rules")
async def get_dst_rules(db: Session = Depends(get_db)):
    """Get DST rules configuration"""
    service = SystemService(db)
    return {"dst_rules": service.get_dst_rules()}


@router.put("/dst-rules")
async def update_dst_rules(
    request: DSTRulesUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update DST rules configuration"""
    service = SystemService(db)
    success = service.set_dst_rules(request.dst_rules)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid DST rules format"
        )
    
    return {
        "message": "DST rules updated successfully",
        "dst_rules": service.get_dst_rules()
    }


@router.get("/session-timeout")
async def get_session_timeout(db: Session = Depends(get_db)):
    """Get user session timeout"""
    service = SystemService(db)
    return {"timeout_seconds": service.get_session_timeout()}


@router.put("/session-timeout")
async def update_session_timeout(
    request: SessionTimeoutUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update user session timeout"""
    service = SystemService(db)
    success = service.set_session_timeout(request.timeout_seconds)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timeout value (must be 60-86400 seconds)"
        )
    
    return {
        "message": "Session timeout updated successfully",
        "timeout_seconds": service.get_session_timeout()
    }


@router.get("/max-concurrent-jobs")
async def get_max_concurrent_jobs(db: Session = Depends(get_db)):
    """Get maximum concurrent jobs"""
    service = SystemService(db)
    return {"max_jobs": service.get_max_concurrent_jobs()}


@router.put("/max-concurrent-jobs")
async def update_max_concurrent_jobs(
    request: MaxJobsUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update maximum concurrent jobs"""
    service = SystemService(db)
    success = service.set_max_concurrent_jobs(request.max_jobs)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid max jobs value (must be 1-1000)"
        )
    
    return {
        "message": "Max concurrent jobs updated successfully",
        "max_jobs": service.get_max_concurrent_jobs()
    }


@router.get("/log-retention")
async def get_log_retention(db: Session = Depends(get_db)):
    """Get log retention period"""
    service = SystemService(db)
    return {"retention_days": service.get_log_retention_days()}


@router.put("/log-retention")
async def update_log_retention(
    request: LogRetentionUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update log retention period"""
    service = SystemService(db)
    success = service.set_log_retention_days(request.retention_days)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid retention days (must be 1-3650 days)"
        )
    
    return {
        "message": "Log retention updated successfully",
        "retention_days": service.get_log_retention_days()
    }


@router.post("/validate-schedule-time")
async def validate_job_schedule_time(
    request: JobScheduleValidationRequest,
    db: Session = Depends(get_db)
):
    """Validate a job schedule time and get conversion info"""
    service = SystemService(db)
    result = service.validate_job_schedule_time(request.local_time)
    
    if not result['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid schedule time: {result['error']}"
        )
    
    return result


@router.get("/current-time")
async def get_current_time(db: Session = Depends(get_db)):
    """Get current system time in UTC and local timezone"""
    service = SystemService(db)
    now = datetime.now()
    
    return {
        "utc": now.isoformat(),
        "local": service.utc_to_local_string(now),
        "timezone": service.get_timezone(),
        "is_dst": service.is_dst_active()
    }


@router.get("/health")
async def get_system_health():
    """Get system health metrics including execution status"""
    try:
        metrics = CleanupTasks.get_system_health_metrics()
        return {
            "status": "healthy",
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system health: {str(e)}"
        )


@router.post("/cleanup/stale-executions")
async def cleanup_stale_executions():
    """Manually trigger cleanup of stale job executions"""
    try:
        cleaned_count = CleanupTasks.cleanup_stale_executions(max_runtime_hours=24)
        return {
            "message": "Stale execution cleanup completed",
            "cleaned_executions": cleaned_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during cleanup: {str(e)}"
        )


@router.get("/executions/running")
async def get_running_executions():
    """Get list of currently running executions for monitoring"""
    from ..models.job_models import JobExecution, ExecutionStatus
    from ..database.database import get_db
    
    db = next(get_db())
    try:
        running_executions = db.query(JobExecution).filter(
            JobExecution.status == ExecutionStatus.RUNNING
        ).all()
        
        execution_list = []
        for execution in running_executions:
            runtime = None
            if execution.started_at:
                runtime_seconds = (datetime.now().replace(tzinfo=execution.started_at.tzinfo) - execution.started_at).total_seconds()
                runtime = f"{runtime_seconds/3600:.1f} hours" if runtime_seconds > 3600 else f"{runtime_seconds/60:.1f} minutes"
            
            execution_list.append({
                "execution_id": execution.id,
                "job_id": execution.job_id,
                "execution_number": execution.execution_number,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "runtime": runtime
            })
        
        return {
            "running_executions": execution_list,
            "count": len(execution_list)
        }
    finally:
        db.close() 