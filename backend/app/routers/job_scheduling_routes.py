"""
Job Scheduling API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.database.database import get_db
from app.services.job_scheduling_service import JobSchedulingService
from app.core.security import verify_token
from app.models.user_models import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity

router = APIRouter(prefix="/api/jobs", tags=["job-scheduling"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


class ScheduleCreateRequest(BaseModel):
    job_id: int
    schedule_type: str  # once, recurring, cron
    enabled: bool = True
    timezone: str = "UTC"
    description: str = None
    max_executions: int = None
    end_date: str = None
    
    # One-time scheduling
    execute_at: str = None
    
    # Recurring scheduling
    recurring_type: str = None  # daily, weekly, monthly
    interval: int = 1
    time: str = None  # HH:MM format
    days_of_week: List[int] = None
    day_of_month: int = None
    
    # Cron scheduling
    cron_expression: str = None


class ScheduleUpdateRequest(BaseModel):
    enabled: bool = None
    description: str = None
    max_executions: int = None
    end_date: str = None
    cron_expression: str = None
    recurring_type: str = None
    interval: int = None
    time: str = None
    days_of_week: List[int] = None
    day_of_month: int = None


@router.post("/schedules", response_model=Dict[str, Any])
async def create_schedule(
    request_data: ScheduleCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new job schedule"""
    try:
        scheduling_service = JobSchedulingService(db)
        
        # Convert request to dict
        schedule_data = request_data.dict(exclude_unset=True)
        
        schedule = scheduling_service.create_schedule(schedule_data)
        
        # Log schedule creation audit event - HIGH SECURITY EVENT
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGED,
            user_id=current_user.id,
            resource_type="job_schedule",
            resource_id=str(schedule.id),
            action="create_schedule",
            details={
                "schedule_id": schedule.id,
                "job_id": schedule.job_id,
                "schedule_type": schedule.schedule_type,
                "enabled": schedule.enabled,
                "created_by": current_user.username
            },
            severity=AuditSeverity.HIGH,  # Job scheduling is high severity
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return {
            "success": True,
            "message": "Schedule created successfully",
            "data": {
                "id": schedule.id,
                "schedule_uuid": str(schedule.schedule_uuid),
                "job_id": schedule.job_id,
                "schedule_type": schedule.schedule_type,
                "enabled": schedule.enabled,
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                "created_at": schedule.created_at.isoformat()
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@router.get("/{job_id}/schedules", response_model=Dict[str, Any])
async def get_job_schedules(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all schedules for a job"""
    try:
        scheduling_service = JobSchedulingService(db)
        schedules = scheduling_service.get_job_schedules(job_id)
        
        schedule_data = []
        for schedule in schedules:
            schedule_data.append({
                "id": schedule.id,
                "schedule_uuid": str(schedule.schedule_uuid),
                "schedule_type": schedule.schedule_type,
                "enabled": schedule.enabled,
                "description": schedule.description,
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
                "execution_count": schedule.execution_count,
                "max_executions": schedule.max_executions,
                "created_at": schedule.created_at.isoformat(),
                "cron_expression": schedule.cron_expression,
                "recurring_type": schedule.recurring_type,
                "interval": schedule.interval,
                "time": schedule.time,
                "days_of_week": schedule.days_of_week,
                "day_of_month": schedule.day_of_month
            })
        
        return {
            "success": True,
            "data": {
                "schedules": schedule_data
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schedules: {str(e)}")


@router.get("/schedules/{schedule_id}", response_model=Dict[str, Any])
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific schedule"""
    try:
        scheduling_service = JobSchedulingService(db)
        schedule = scheduling_service.get_schedule(schedule_id)
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {
            "success": True,
            "data": {
                "id": schedule.id,
                "schedule_uuid": str(schedule.schedule_uuid),
                "job_id": schedule.job_id,
                "schedule_type": schedule.schedule_type,
                "enabled": schedule.enabled,
                "description": schedule.description,
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
                "execution_count": schedule.execution_count,
                "max_executions": schedule.max_executions,
                "end_date": schedule.end_date.isoformat() if schedule.end_date else None,
                "timezone": schedule.timezone,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat(),
                # Type-specific fields
                "execute_at": schedule.execute_at.isoformat() if schedule.execute_at else None,
                "cron_expression": schedule.cron_expression,
                "recurring_type": schedule.recurring_type,
                "interval": schedule.interval,
                "time": schedule.time,
                "days_of_week": schedule.days_of_week,
                "day_of_month": schedule.day_of_month
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schedule: {str(e)}")


@router.put("/schedules/{schedule_id}", response_model=Dict[str, Any])
async def update_schedule(
    schedule_id: int,
    request: ScheduleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a schedule"""
    try:
        scheduling_service = JobSchedulingService(db)
        
        # Convert request to dict, excluding None values
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        schedule = scheduling_service.update_schedule(schedule_id, update_data)
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {
            "success": True,
            "message": "Schedule updated successfully",
            "data": {
                "id": schedule.id,
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                "updated_at": schedule.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update schedule: {str(e)}")


@router.delete("/schedules/{schedule_id}", response_model=Dict[str, Any])
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a schedule"""
    try:
        scheduling_service = JobSchedulingService(db)
        success = scheduling_service.delete_schedule(schedule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {
            "success": True,
            "message": "Schedule deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")


@router.get("/schedules/due/list", response_model=Dict[str, Any])
async def get_due_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get schedules that are due for execution (admin only)"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        scheduling_service = JobSchedulingService(db)
        due_schedules = scheduling_service.get_due_schedules()
        
        schedule_data = []
        for schedule in due_schedules:
            schedule_data.append({
                "id": schedule.id,
                "job_id": schedule.job_id,
                "job_name": schedule.job.name if schedule.job else "Unknown",
                "schedule_type": schedule.schedule_type,
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                "execution_count": schedule.execution_count,
                "max_executions": schedule.max_executions
            })
        
        return {
            "success": True,
            "data": {
                "due_schedules": schedule_data,
                "count": len(schedule_data)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get due schedules: {str(e)}")