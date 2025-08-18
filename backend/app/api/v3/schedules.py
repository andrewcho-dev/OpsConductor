"""
Job Schedules API v3 - Handles job scheduling operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.core.security import verify_token
from app.services.job_scheduling_service import JobSchedulingService
from app.models.job_schedule_models import JobSchedule, ScheduleType, RecurringType
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/api/schedules", tags=["Job Schedules"])


# MODELS
class ScheduleCreate(BaseModel):
    job_id: int
    schedule_type: str = Field(..., description="Schedule type: once, recurring, cron")
    enabled: bool = Field(default=True)
    timezone: str = Field(default="UTC")
    description: Optional[str] = None
    
    # One-time scheduling
    executeAt: Optional[datetime] = None
    
    # Recurring scheduling
    recurringType: Optional[str] = None  # daily, weekly, monthly
    interval: Optional[int] = Field(default=1)
    time: Optional[str] = None  # HH:MM format
    daysOfWeek: Optional[str] = None  # Comma-separated: 0,1,2,3,4,5,6
    dayOfMonth: Optional[int] = None  # 1-31
    
    # Cron scheduling
    cronExpression: Optional[str] = None
    
    # Advanced options
    maxExecutions: Optional[int] = None
    endDate: Optional[datetime] = None


class ScheduleResponse(BaseModel):
    id: int
    job_id: int
    schedule_type: str
    enabled: bool
    timezone: str
    description: Optional[str]
    
    # One-time scheduling
    execute_at: Optional[datetime]
    
    # Recurring scheduling
    recurring_type: Optional[str]
    interval: Optional[int]
    time: Optional[str]
    days_of_week: Optional[str]
    day_of_month: Optional[int]
    
    # Cron scheduling
    cron_expression: Optional[str]
    
    # Advanced options
    max_executions: Optional[int]
    execution_count: int
    end_date: Optional[datetime]
    
    # Metadata
    next_run: Optional[datetime]
    last_run: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]


@router.post("/", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: Session = Depends(get_db),
    token: str = Depends(security)
):
    """Create a new job schedule"""
    try:
        verify_token(token.credentials)
        scheduling_service = JobSchedulingService(db)
        
        # Convert frontend format to backend format
        backend_data = {
            'job_id': schedule_data.job_id,
            'schedule_type': schedule_data.schedule_type,
            'enabled': schedule_data.enabled,
            'timezone': schedule_data.timezone,
            'description': schedule_data.description,
            'max_executions': schedule_data.maxExecutions,
            'end_date': schedule_data.endDate
        }
        
        # Add schedule-specific fields
        if schedule_data.schedule_type == 'once' and schedule_data.executeAt:
            backend_data['execute_at'] = schedule_data.executeAt
        elif schedule_data.schedule_type == 'recurring':
            backend_data['recurring_type'] = schedule_data.recurringType
            backend_data['interval'] = schedule_data.interval
            backend_data['time'] = schedule_data.time
            backend_data['days_of_week'] = schedule_data.daysOfWeek
            backend_data['day_of_month'] = schedule_data.dayOfMonth
        elif schedule_data.schedule_type == 'cron':
            backend_data['cron_expression'] = schedule_data.cronExpression
        
        schedule = scheduling_service.create_schedule(backend_data)
        
        return ScheduleResponse(
            id=schedule.id,
            job_id=schedule.job_id,
            schedule_type=schedule.schedule_type,
            enabled=schedule.enabled,
            timezone=schedule.timezone,
            description=schedule.description,
            execute_at=schedule.execute_at,
            recurring_type=schedule.recurring_type,
            interval=schedule.interval,
            time=schedule.time,
            days_of_week=schedule.days_of_week,
            day_of_month=schedule.day_of_month,
            cron_expression=schedule.cron_expression,
            max_executions=schedule.max_executions,
            execution_count=schedule.execution_count,
            end_date=schedule.end_date,
            next_run=schedule.next_run,
            last_run=schedule.last_run,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ScheduleResponse])
async def list_schedules(
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    db: Session = Depends(get_db),
    token: str = Depends(security)
):
    """List job schedules"""
    try:
        verify_token(token.credentials)
        scheduling_service = JobSchedulingService(db)
        
        if job_id:
            schedules = scheduling_service.get_job_schedules(job_id)
        else:
            # Get all schedules (you might want to add pagination here)
            schedules = db.query(JobSchedule).all()
        
        return [
            ScheduleResponse(
                id=schedule.id,
                job_id=schedule.job_id,
                schedule_type=schedule.schedule_type,
                enabled=schedule.enabled,
                timezone=schedule.timezone,
                description=schedule.description,
                execute_at=schedule.execute_at,
                recurring_type=schedule.recurring_type,
                interval=schedule.interval,
                time=schedule.time,
                days_of_week=schedule.days_of_week,
                day_of_month=schedule.day_of_month,
                cron_expression=schedule.cron_expression,
                max_executions=schedule.max_executions,
                execution_count=schedule.execution_count,
                end_date=schedule.end_date,
                next_run=schedule.next_run,
                last_run=schedule.last_run,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at
            )
            for schedule in schedules
        ]
        
    except Exception as e:
        logger.error(f"Failed to list schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(security)
):
    """Delete a job schedule"""
    try:
        verify_token(token.credentials)
        scheduling_service = JobSchedulingService(db)
        
        schedule = scheduling_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        db.delete(schedule)
        db.commit()
        
        return {"message": "Schedule deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))