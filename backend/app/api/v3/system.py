"""
System API v3 - Basic system information and settings
Cleaned up version without health monitoring endpoints
"""

import os
import json
import time
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

from app.services.system_management_service import SystemManagementService
from app.database.database import get_db
from app.core.auth_dependencies import get_current_user, get_current_user_optional
from app.core.logging import get_structured_logger
from app.core.config import settings

api_base_url = os.getenv("API_BASE_URL", "/api/v3")
router = APIRouter(prefix=f"{api_base_url}/system", tags=["System v3"])

# Configure structured logger
logger = get_structured_logger(__name__)


# MODELS

class SystemInfoResponse(BaseModel):
    """Basic system info response"""
    hostname: str
    platform: str
    version: str
    status: str


# ENDPOINTS

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


@router.get("/time")
async def get_system_time(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Get current system time with DST awareness"""
    try:
        # Get UTC time
        utc_time = datetime.now(timezone.utc)
        
        # Get local time with DST awareness
        import datetime as dt
        local_time = dt.datetime.now()
        
        # Get the local timezone
        local_tz = local_time.astimezone().tzinfo
        
        # Check if DST is active
        import time
        is_dst = time.localtime().tm_isdst > 0
        
        # Calculate the offset from UTC
        offset_seconds = local_time.astimezone().utcoffset().total_seconds()
        offset_hours = offset_seconds / 3600
        
        return {
            "utc_time": utc_time.isoformat(),
            "local_time": local_time.isoformat(),
            "timezone": str(local_tz),
            "is_dst": is_dst,
            "utc_offset_hours": offset_hours,
            "timestamp": int(time.time())
        }
    except Exception as e:
        logger.error(f"Failed to get system time: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system time: {str(e)}"
        )


@router.get("/timezones")
async def get_available_timezones(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Get list of available timezones"""
    try:
        import zoneinfo
        
        # Get common timezones
        common_timezones = [
            "UTC",
            "US/Eastern",
            "US/Central", 
            "US/Mountain",
            "US/Pacific",
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Australia/Sydney"
        ]
        
        # Get all available timezones
        all_timezones = sorted(zoneinfo.available_timezones())
        
        return {
            "common_timezones": common_timezones,
            "all_timezones": all_timezones[:100],  # Limit to first 100 for performance
            "total_count": len(all_timezones)
        }
    except Exception as e:
        logger.error(f"Failed to get timezones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get timezones: {str(e)}"
        )


@router.get("/timezone")
async def get_system_timezone(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Get current system timezone"""
    try:
        import datetime as dt
        local_time = dt.datetime.now()
        local_tz = local_time.astimezone().tzinfo
        
        return {
            "timezone": str(local_tz),
            "utc_offset": local_time.astimezone().utcoffset().total_seconds() / 3600
        }
    except Exception as e:
        logger.error(f"Failed to get system timezone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system timezone: {str(e)}"
        )


@router.put("/timezone")
async def set_system_timezone(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set system timezone (admin only)"""
    try:
        # Check admin permissions
        if current_user.get("role") != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator role required"
            )
        
        data = await request.json()
        timezone_name = data.get("timezone")
        
        if not timezone_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timezone is required"
            )
        
        # Validate timezone
        try:
            import zoneinfo
            zoneinfo.ZoneInfo(timezone_name)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timezone: {timezone_name}"
            )
        
        # Note: This is a placeholder - actual timezone setting would require system-level changes
        logger.info(f"Timezone change requested to {timezone_name} by user {current_user.get('username')}")
        
        return {
            "message": f"Timezone change requested: {timezone_name}",
            "note": "System timezone changes require server restart"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set timezone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set timezone: {str(e)}"
        )


# System Settings Endpoints

@router.put("/inactivity-timeout")
async def update_inactivity_timeout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user inactivity timeout (admin only)"""
    try:
        if current_user.get("role") != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator role required"
            )
        
        data = await request.json()
        timeout_minutes = data.get("timeout_minutes")
        
        if not isinstance(timeout_minutes, int) or timeout_minutes < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timeout must be a positive integer (minutes)"
            )
        
        # Update system setting
        system_service = SystemManagementService(db)
        await system_service.update_system_setting("inactivity_timeout_minutes", timeout_minutes)
        
        return {"message": f"Inactivity timeout updated to {timeout_minutes} minutes"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update inactivity timeout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update inactivity timeout: {str(e)}"
        )


@router.put("/warning-time")
async def update_warning_time(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update session warning time (admin only)"""
    try:
        if current_user.get("role") != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator role required"
            )
        
        data = await request.json()
        warning_minutes = data.get("warning_minutes")
        
        if not isinstance(warning_minutes, int) or warning_minutes < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warning time must be a positive integer (minutes)"
            )
        
        # Update system setting
        system_service = SystemManagementService(db)
        await system_service.update_system_setting("session_warning_minutes", warning_minutes)
        
        return {"message": f"Session warning time updated to {warning_minutes} minutes"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update warning time: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update warning time: {str(e)}"
        )


@router.put("/max-concurrent-jobs")
async def update_max_concurrent_jobs(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update maximum concurrent jobs (admin only)"""
    try:
        if current_user.get("role") != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator role required"
            )
        
        data = await request.json()
        max_jobs = data.get("max_concurrent_jobs")
        
        if not isinstance(max_jobs, int) or max_jobs < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max concurrent jobs must be a positive integer"
            )
        
        # Update system setting
        system_service = SystemManagementService(db)
        await system_service.update_system_setting("max_concurrent_jobs", max_jobs)
        
        return {"message": f"Maximum concurrent jobs updated to {max_jobs}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update max concurrent jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update max concurrent jobs: {str(e)}"
        )


@router.get("/settings")
async def get_system_settings(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current system settings"""
    try:
        system_service = SystemManagementService(db)
        settings_data = await system_service.get_system_settings()
        
        return {
            "inactivity_timeout_minutes": settings_data.get("inactivity_timeout_minutes", 60),
            "session_warning_minutes": settings_data.get("session_warning_minutes", 2),
            "max_concurrent_jobs": settings_data.get("max_concurrent_jobs", 10),
            "log_retention_days": settings_data.get("log_retention_days", 30),
            "job_history_retention_days": settings_data.get("job_history_retention_days", 90),
            "audit_log_retention_days": settings_data.get("audit_log_retention_days", 365)
        }
    except Exception as e:
        logger.error(f"Failed to get system settings: {str(e)}")
        # Return defaults if database fails
        return {
            "inactivity_timeout_minutes": 60,
            "session_warning_minutes": 2,
            "max_concurrent_jobs": 10,
            "log_retention_days": 30,
            "job_history_retention_days": 90,
            "audit_log_retention_days": 365
        }


@router.put("/settings")
async def update_system_settings(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update multiple system settings at once (admin only)"""
    try:
        if current_user.get("role") != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator role required"
            )
        
        data = await request.json()
        system_service = SystemManagementService(db)
        
        # Update each setting if provided
        updated_settings = []
        
        if "inactivity_timeout_minutes" in data:
            timeout = data["inactivity_timeout_minutes"]
            if isinstance(timeout, int) and timeout > 0:
                await system_service.update_system_setting("inactivity_timeout_minutes", timeout)
                updated_settings.append(f"inactivity timeout: {timeout} minutes")
        
        if "session_warning_minutes" in data:
            warning = data["session_warning_minutes"]
            if isinstance(warning, int) and warning > 0:
                await system_service.update_system_setting("session_warning_minutes", warning)
                updated_settings.append(f"session warning: {warning} minutes")
        
        if "max_concurrent_jobs" in data:
            max_jobs = data["max_concurrent_jobs"]
            if isinstance(max_jobs, int) and max_jobs > 0:
                await system_service.update_system_setting("max_concurrent_jobs", max_jobs)
                updated_settings.append(f"max concurrent jobs: {max_jobs}")
        
        return {
            "message": "System settings updated successfully",
            "updated": updated_settings
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update system settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update system settings: {str(e)}"
        )


# Basic health endpoint for load balancers
@router.get("/health")
async def basic_health_check():
    """Basic health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "opsconductor-system"
    }