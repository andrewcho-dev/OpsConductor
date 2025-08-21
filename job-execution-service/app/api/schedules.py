"""
Job Scheduling API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.schemas.job_schemas import (
    JobScheduleCreate, JobScheduleUpdate, JobScheduleResponse
)
from app.services.scheduling_service import JobSchedulingService
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=JobScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    job_id: int,
    schedule_data: JobScheduleCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job schedule"""
    try:
        scheduling_service = JobSchedulingService(db)
        schedule = await scheduling_service.create_schedule(
            job_id, schedule_data, current_user["id"]
        )
        
        logger.info(f"Created schedule for job {job_id} by user {current_user['id']}")
        return schedule
        
    except ValueError as e:
        logger.warning(f"Schedule creation validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule")


@router.get("/job/{job_id}", response_model=List[JobScheduleResponse])
async def get_job_schedules(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all schedules for a job"""
    try:
        scheduling_service = JobSchedulingService(db)
        schedules = await scheduling_service.get_job_schedules(job_id)
        
        return schedules
        
    except Exception as e:
        logger.error(f"Failed to get schedules for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job schedules")


@router.get("/{schedule_id}", response_model=JobScheduleResponse)
async def get_schedule(
    schedule_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get schedule by ID"""
    try:
        scheduling_service = JobSchedulingService(db)
        schedule = await scheduling_service.get_schedule(schedule_id)
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get schedule")


@router.put("/{schedule_id}", response_model=JobScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: JobScheduleUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update schedule"""
    try:
        scheduling_service = JobSchedulingService(db)
        schedule = await scheduling_service.update_schedule(
            schedule_id, schedule_data, current_user["id"]
        )
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        logger.info(f"Updated schedule {schedule_id} by user {current_user['id']}")
        return schedule
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Schedule update validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule")


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete schedule"""
    try:
        scheduling_service = JobSchedulingService(db)
        success = await scheduling_service.delete_schedule(schedule_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        logger.info(f"Deleted schedule {schedule_id} by user {current_user['id']}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete schedule")