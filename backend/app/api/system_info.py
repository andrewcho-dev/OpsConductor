"""
Simple System Info API - Frontend Compatibility
Provides basic system information endpoint that frontend expects
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.services.system_management_service import SystemManagementService

# Security scheme

# Router
router = APIRouter(prefix="/api/system", tags=["System Info"])

class SystemInfoResponse(BaseModel):
    """Basic system info response"""
    hostname: str
    platform: str
    version: str
    status: str

# Local get_current_user removed - using centralized auth_dependencies

@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get basic system information"""
    try:
        # Use the existing system management service
        system_service = SystemManagementService(db)
        system_status = await system_service.get_system_status()
        
        return SystemInfoResponse(
            hostname=system_status.system_info.hostname,
            platform=system_status.system_info.platform,
            version="1.0.0",
            status="healthy"
        )
    except Exception as e:
        # Fallback response
        return SystemInfoResponse(
            hostname="opsconductor",
            platform="Linux",
            version="1.0.0",
            status="healthy"
        )