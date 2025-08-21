"""
Job Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.schemas.job_schemas import (
    JobCreate, JobUpdate, JobResponse, JobListResponse,
    JobExecuteRequest, JobExecutionResponse
)
from app.services.job_service import JobService
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job"""
    try:
        job_service = JobService(db)
        job = await job_service.create_job(job_data, current_user["id"])
        
        logger.info(f"Created job '{job.name}' (ID: {job.id}) by user {current_user['id']}")
        return job
        
    except ValueError as e:
        logger.warning(f"Job creation validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job")


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    created_by: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List jobs with filtering and pagination"""
    try:
        job_service = JobService(db)
        result = await job_service.list_jobs(
            page=page,
            size=size,
            status=status,
            job_type=job_type,
            created_by=created_by,
            search=search
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list jobs")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    include_actions: bool = Query(True),
    include_targets: bool = Query(True),
    include_execution_summary: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job by ID with optional related data"""
    try:
        job_service = JobService(db)
        job = await job_service.get_job(
            job_id,
            include_actions=include_actions,
            include_targets=include_targets,
            include_execution_summary=include_execution_summary
        )
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job")


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update job"""
    try:
        job_service = JobService(db)
        job = await job_service.update_job(job_id, job_data, current_user["id"])
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        logger.info(f"Updated job {job_id} by user {current_user['id']}")
        return job
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Job update validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update job")


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    force: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete job (soft delete by default)"""
    try:
        job_service = JobService(db)
        success = await job_service.delete_job(job_id, current_user["id"], force=force)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        
        logger.info(f"Deleted job {job_id} by user {current_user['id']} (force={force})")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete job")


@router.post("/{job_id}/execute", response_model=JobExecutionResponse)
async def execute_job(
    job_id: int,
    execute_data: JobExecuteRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a job"""
    try:
        job_service = JobService(db)
        execution = await job_service.execute_job(
            job_id, 
            execute_data, 
            current_user["id"]
        )
        
        logger.info(f"Started execution {execution.id} for job {job_id} by user {current_user['id']}")
        return execution
        
    except ValueError as e:
        logger.warning(f"Job execution validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute job")


@router.post("/{job_id}/cancel", response_model=dict)
async def cancel_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel running job executions"""
    try:
        job_service = JobService(db)
        result = await job_service.cancel_job(job_id, current_user["id"])
        
        logger.info(f"Cancelled job {job_id} by user {current_user['id']}")
        return result
        
    except ValueError as e:
        logger.warning(f"Job cancellation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel job")


@router.get("/{job_id}/executions", response_model=List[JobExecutionResponse])
async def get_job_executions(
    job_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job execution history"""
    try:
        job_service = JobService(db)
        executions = await job_service.get_job_executions(
            job_id, 
            page=page, 
            size=size
        )
        
        return executions
        
    except Exception as e:
        logger.error(f"Failed to get executions for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job executions")