"""
Job management API endpoints for Jobs Service
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_jobs():
    """List all jobs"""
    return {
        "success": True,
        "message": "Jobs endpoint - implementation pending",
        "data": []
    }


@router.post("/")
async def create_job():
    """Create a new job"""
    return {
        "success": True,
        "message": "Create job endpoint - implementation pending"
    }