"""
Job Schedules API v3 - Handles job scheduling operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.services.job_scheduling_service import JobSchedulingService
from app.models.job_schedule_models import JobSchedule, ScheduleType, RecurringType
import logging

logger = logging.getLogger(__name__)

import os

api_base_url = os.getenv("API_BASE_URL", "/api/v1")
router = APIRouter(prefix=f"{api_base_url}/schedules", tags=["Job Schedules v1"])


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
    recurringType: Optional[str] = None  # minutes, hours, daily, weekly, monthly
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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new job schedule"""
    try:
        logger.info(f"📥 Received schedule creation request: {schedule_data.dict()}")
        
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
        
        logger.info(f"🔄 Basic schedule data: {backend_data}")
        
        # Add schedule-specific fields
        if schedule_data.schedule_type == 'once' and schedule_data.executeAt:
            backend_data['execute_at'] = schedule_data.executeAt
            logger.info(f"⏰ One-time schedule at: {schedule_data.executeAt}")
        elif schedule_data.schedule_type == 'recurring':
            backend_data['recurring_type'] = schedule_data.recurringType
            backend_data['interval'] = schedule_data.interval
            backend_data['time'] = schedule_data.time
            backend_data['days_of_week'] = schedule_data.daysOfWeek
            backend_data['day_of_month'] = schedule_data.dayOfMonth
            
            logger.info(f"🔄 Recurring schedule details: type={schedule_data.recurringType}, " +
                       f"interval={schedule_data.interval}, time={schedule_data.time}, " +
                       f"days_of_week={schedule_data.daysOfWeek}, day_of_month={schedule_data.dayOfMonth}")
        elif schedule_data.schedule_type == 'cron':
            backend_data['cron_expression'] = schedule_data.cronExpression
            logger.info(f"⏱️ Cron schedule: {schedule_data.cronExpression}")
        
        logger.info(f"📤 Sending to scheduling service: {backend_data}")
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


@router.post("/test-minutes", response_model=ScheduleResponse)
async def test_minutes_schedule(
    job_id: int = Query(..., description="Job ID to create test schedule for"),
    interval: int = Query(2, description="Interval in minutes"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Test endpoint to create a minutes-based recurring schedule"""
    try:
        logger.info(f"📊 Creating test minutes schedule for job {job_id} with interval {interval}")
        
        scheduling_service = JobSchedulingService(db)
        
        # Create test schedule data
        backend_data = {
            'job_id': job_id,
            'schedule_type': 'recurring',
            'recurring_type': 'minutes',
            'interval': interval,
            'enabled': True,
            'timezone': 'UTC',
            'description': f'Test minutes schedule every {interval} minutes'
        }
        
        logger.info(f"📊 Test schedule data: {backend_data}")
        
        # Create the schedule
        schedule = scheduling_service.create_schedule(backend_data)
        logger.info(f"📊 Test schedule created with ID {schedule.id} and next run at {schedule.next_run}")
        
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
    except Exception as e:
        logger.error(f"❌ Error creating test minutes schedule: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ScheduleResponse])
async def list_schedules(
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List job schedules"""
    try:
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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a job schedule"""
    try:
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