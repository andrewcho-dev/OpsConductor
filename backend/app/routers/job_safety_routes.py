"""
Job Safety API Routes - Endpoints for job safety operations
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from app.database.database import get_db
from app.services.job_safety_service import JobSafetyService
from app.core.security import verify_token
from app.models.user_models import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/jobs/safety", tags=["job-safety"])
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


@router.post("/cleanup-stale", response_model=Dict[str, Any])
async def cleanup_stale_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up stale jobs that are stuck in running state
    """
    try:
        safety_service = JobSafetyService(db)
        result = safety_service.cleanup_stale_jobs()
        return {
            "success": True,
            "message": "Stale job cleanup completed",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


class TerminateJobRequest(BaseModel):
    reason: str = "Manual termination by user"

@router.post("/terminate/{job_identifier}", response_model=Dict[str, Any])
async def force_terminate_job(
    job_identifier: str,
    request: TerminateJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Force terminate a running job
    """
    try:
        safety_service = JobSafetyService(db)
        
        # Try to parse as integer first (job ID), then try as job serial
        job_id = None
        if job_identifier.isdigit():
            job_id = int(job_identifier)
        else:
            # Look up job by serial
            from app.models.job_models import Job
            job = db.query(Job).filter(Job.job_serial == job_identifier).first()
            if job:
                job_id = job.id
            else:
                raise HTTPException(status_code=404, detail=f"Job not found with identifier: {job_identifier}")
        
        username = current_user.get('username', 'unknown') if isinstance(current_user, dict) else getattr(current_user, 'username', 'unknown')
        success = safety_service.force_terminate_job(job_id, f"{request.reason} (by {username})")
        
        if success:
            return {
                "success": True,
                "message": f"Job {job_identifier} terminated successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to terminate job {job_identifier}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Termination failed: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def get_job_health_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get job system health status
    """
    try:
        safety_service = JobSafetyService(db)
        health_status = safety_service.get_job_health_status()
        return {
            "success": True,
            "data": health_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")