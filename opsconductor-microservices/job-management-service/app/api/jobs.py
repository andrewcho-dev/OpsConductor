"""
Job Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.core.database import get_db
from app.services.job_service import JobService
from opsconductor_shared.auth.jwt_auth import get_current_user
from opsconductor_shared.models.base import PaginatedResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job"""
    try:
        job_service = JobService(db)
        job = await job_service.create_job(job_data, current_user["id"])
        
        logger.info(f"Created job '{job['name']}' (ID: {job['id']}) by user {current_user['id']}")
        return job
        
    except ValueError as e:
        logger.warning(f"Job creation validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job")


@router.get("/")
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


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    include_details: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job by ID"""
    try:
        job_service = JobService(db)
        job = await job_service.get_job(job_id, include_details=include_details)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job")


@router.put("/{job_id}")
async def update_job(
    job_id: int,
    job_data: Dict[str, Any],
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
    """Delete job"""
    try:
        job_service = JobService(db)
        success = await job_service.delete_job(job_id, current_user["id"], force=force)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        
        logger.info(f"Deleted job {job_id} by user {current_user['id']} (force={force})")
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Job deletion error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete job")


@router.post("/{job_id}/execute")
async def execute_job(
    job_id: int,
    execution_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a job"""
    try:
        job_service = JobService(db)
        result = await job_service.execute_job(job_id, execution_data, current_user["id"])
        
        logger.info(f"Started execution for job {job_id} by user {current_user['id']}")
        return result
        
    except ValueError as e:
        logger.warning(f"Job execution validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute job")


@router.get("/{job_id}/validate")
async def validate_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate job configuration"""
    try:
        job_service = JobService(db)
        job = await job_service.get_job(job_id, include_details=True)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Perform validation checks
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check if job has actions
        if not job.get("actions"):
            validation_results["errors"].append("Job must have at least one action")
            validation_results["valid"] = False
        
        # Check if job has targets
        if not job.get("targets"):
            validation_results["errors"].append("Job must have at least one target")
            validation_results["valid"] = False
        
        # Check for dangerous actions
        dangerous_actions = []
        for action in job.get("actions", []):
            if action.get("is_dangerous"):
                dangerous_actions.append(action["action_name"])
        
        if dangerous_actions:
            validation_results["warnings"].append(
                f"Job contains dangerous actions: {', '.join(dangerous_actions)}"
            )
        
        return validation_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate job")