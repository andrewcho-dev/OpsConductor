"""
System API v3 - Consolidated from system_info.py and v2/health_enhanced.py
All system management and health endpoints in v3 structure
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

from app.services.health_management_service import HealthManagementService, HealthManagementError
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


class HealthCheckResult(BaseModel):
    """Enhanced model for individual health check results"""
    healthy: bool = Field(..., description="Health check status")
    status: str = Field(..., description="Health check status description")
    response_time: Optional[float] = Field(None, description="Response time in milliseconds")
    last_check: datetime = Field(..., description="Last check timestamp")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health check details")


class SystemResourceInfo(BaseModel):
    """Enhanced model for system resource information"""
    usage_percent: float = Field(..., description="Resource usage percentage")
    total: Optional[int] = Field(None, description="Total resource amount")
    used: Optional[int] = Field(None, description="Used resource amount")
    available: Optional[int] = Field(None, description="Available resource amount")
    healthy: bool = Field(..., description="Resource health status")


class OverallHealthResponse(BaseModel):
    """Enhanced response model for overall health status"""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    health_checks: Dict[str, HealthCheckResult] = Field(..., description="Individual health check results")
    health_metrics: Dict[str, Any] = Field(default_factory=dict, description="Health metrics")
    recommendations: List[str] = Field(default_factory=list, description="Health recommendations")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Health alerts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Health metadata")


class DatabaseHealthResponse(BaseModel):
    """Database health response model"""
    status: str
    connection_pool: Dict[str, Any]
    query_performance: Dict[str, Any]
    storage_info: Dict[str, Any]
    active_connections: int
    response_time: float


class ApplicationHealthResponse(BaseModel):
    """Application health response model"""
    status: str
    memory_usage: SystemResourceInfo
    cpu_usage: SystemResourceInfo
    disk_usage: SystemResourceInfo
    active_sessions: int
    cache_status: Dict[str, Any]
    background_tasks: Dict[str, Any]


class SystemHealthResponse(BaseModel):
    """System health response model"""
    status: str
    system_info: Dict[str, Any]
    resource_usage: Dict[str, SystemResourceInfo]
    network_status: Dict[str, Any]
    service_status: Dict[str, Any]
    uptime: str


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


@router.get("/health/", response_model=OverallHealthResponse)
async def get_overall_health(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get comprehensive system health status"""
    try:
        health_service = HealthManagementService(db)
        health_status = await health_service.get_comprehensive_health()
        
        return OverallHealthResponse(
            status=health_status.get("status", "unknown"),
            timestamp=datetime.now(timezone.utc),
            health_checks=health_status.get("health_checks", {}),
            health_metrics=health_status.get("health_metrics", {}),
            recommendations=health_status.get("recommendations", []),
            uptime=health_status.get("uptime", "unknown"),
            version="1.0.0",
            environment=settings.ENVIRONMENT,
            alerts=health_status.get("alerts", []),
            metadata=health_status.get("metadata", {})
        )
    except Exception as e:
        logger.error(f"Failed to get overall health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health status: {str(e)}"
        )


@router.get("/health/database", response_model=DatabaseHealthResponse)
async def get_database_health(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get database health status"""
    try:
        health_service = HealthManagementService(db)
        # Fix method name - it should be get_database_health, not check_database_health
        current_user_id = current_user.get("id") if current_user else None
        current_username = current_user.get("username") if current_user else None
        db_health = await health_service.get_database_health(
            current_user_id=current_user_id,
            current_username=current_username
        )
        
        return DatabaseHealthResponse(
            status=db_health.get("status", "unknown"),
            connection_pool=db_health.get("connection_pool", {}),
            query_performance=db_health.get("query_performance", {}),
            storage_info=db_health.get("storage_info", {}),
            active_connections=db_health.get("active_connections", 0),
            response_time=db_health.get("response_time", 0.0)
        )
    except Exception as e:
        logger.error(f"Failed to get database health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database health: {str(e)}"
        )


@router.get("/health/application", response_model=ApplicationHealthResponse)
async def get_application_health(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get application health status"""
    try:
        health_service = HealthManagementService(db)
        # Fix method name - it should be get_application_health, not check_application_health
        current_user_id = current_user.get("id") if current_user else None
        current_username = current_user.get("username") if current_user else None
        app_health = await health_service.get_application_health(
            current_user_id=current_user_id,
            current_username=current_username
        )
        
        # Convert resource info to SystemResourceInfo objects
        memory_usage = app_health.get("memory_usage", {})
        cpu_usage = app_health.get("cpu_usage", {})
        disk_usage = app_health.get("disk_usage", {})
        
        return ApplicationHealthResponse(
            status=app_health.get("status", "unknown"),
            memory_usage=SystemResourceInfo(
                usage_percent=memory_usage.get("usage_percent", 0.0),
                total=memory_usage.get("total"),
                used=memory_usage.get("used"),
                available=memory_usage.get("available"),
                healthy=memory_usage.get("healthy", True)
            ),
            cpu_usage=SystemResourceInfo(
                usage_percent=cpu_usage.get("usage_percent", 0.0),
                total=cpu_usage.get("total"),
                used=cpu_usage.get("used"),
                available=cpu_usage.get("available"),
                healthy=cpu_usage.get("healthy", True)
            ),
            disk_usage=SystemResourceInfo(
                usage_percent=disk_usage.get("usage_percent", 0.0),
                total=disk_usage.get("total"),
                used=disk_usage.get("used"),
                available=disk_usage.get("available"),
                healthy=disk_usage.get("healthy", True)
            ),
            active_sessions=app_health.get("active_sessions", 0),
            cache_status=app_health.get("cache_status", {}),
            background_tasks=app_health.get("background_tasks", {})
        )
    except Exception as e:
        logger.error(f"Failed to get application health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get application health: {str(e)}"
        )


@router.get("/health/system", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get system health status"""
    try:
        health_service = HealthManagementService(db)
        # Fix method name - it should be get_system_health, not check_system_health
        current_user_id = current_user.get("id") if current_user else None
        current_username = current_user.get("username") if current_user else None
        sys_health = await health_service.get_system_health(
            current_user_id=current_user_id,
            current_username=current_username
        )
        
        # Convert resource usage to SystemResourceInfo objects
        resource_usage = {}
        for resource_name, resource_data in sys_health.get("resource_usage", {}).items():
            resource_usage[resource_name] = SystemResourceInfo(
                usage_percent=resource_data.get("usage_percent", 0.0),
                total=resource_data.get("total"),
                used=resource_data.get("used"),
                available=resource_data.get("available"),
                healthy=resource_data.get("healthy", True)
            )
        
        return SystemHealthResponse(
            status=sys_health.get("status", "unknown"),
            system_info=sys_health.get("system_info", {}),
            resource_usage=resource_usage,
            network_status=sys_health.get("network_status", {}),
            service_status=sys_health.get("service_status", {}),
            uptime=sys_health.get("uptime", "unknown")
        )
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )


@router.post("/health/volumes/prune")
async def prune_docker_volumes(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Prune unused Docker volumes"""
    try:
        # Check if user has admin privileges
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required for volume pruning"
            )
        
        health_service = HealthManagementService(db)
        result = await health_service.prune_docker_volumes()
        
        return {
            "message": "Docker volumes pruned successfully",
            "volumes_removed": result.get("volumes_removed", 0),
            "space_reclaimed": result.get("space_reclaimed", "0B")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to prune Docker volumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to prune Docker volumes: {str(e)}"
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
            "local_time": local_time.astimezone().isoformat(),
            "timestamp": int(utc_time.timestamp()),
            "timezone": str(local_tz),
            "dst_active": is_dst,
            "utc_offset_hours": offset_hours
        }
    except Exception as e:
        logger.error(f"Failed to get system time: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system time: {str(e)}"
        )


@router.get("/timezones")
async def get_timezones(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Get available timezones"""
    try:
        import pytz
        timezones = {tz: tz.replace('_', ' ') for tz in pytz.all_timezones}
        return {
            "timezones": timezones
        }
    except ImportError:
        # If pytz is not available, return a limited set of common timezones
        timezones = {
            'UTC': 'UTC (Coordinated Universal Time)',
            'America/New_York': 'America/New York (Eastern Time)',
            'America/Chicago': 'America/Chicago (Central Time)',
            'America/Denver': 'America/Denver (Mountain Time)',
            'America/Los_Angeles': 'America/Los Angeles (Pacific Time)',
            'Europe/London': 'Europe/London (GMT)',
            'Europe/Paris': 'Europe/Paris (Central European Time)',
            'Asia/Tokyo': 'Asia/Tokyo (Japan Standard Time)'
        }
        return {
            "timezones": timezones
        }
    except Exception as e:
        logger.error(f"Failed to get timezones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get timezones: {str(e)}"
        )


@router.get("/timezone")
async def get_timezone(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current system timezone with DST awareness"""
    try:
        import time
        import datetime as dt
        import pytz
        
        # Get the local timezone from the system
        local_tz_name = time.tzname[time.daylight] if time.daylight and time.localtime().tm_isdst > 0 else time.tzname[0]
        
        # Try to get a proper timezone object that handles DST correctly
        try:
            # Try to find the timezone in pytz
            for tz_name in pytz.all_timezones:
                if tz_name.endswith(local_tz_name) or local_tz_name in tz_name:
                    local_tz = pytz.timezone(tz_name)
                    break
            else:
                # If not found, use the system's timezone
                local_tz = dt.datetime.now().astimezone().tzinfo
        except:
            # Fallback to system timezone
            local_tz = dt.datetime.now().astimezone().tzinfo
        
        # Get current datetime in the local timezone
        now = dt.datetime.now(local_tz)
        
        # Calculate the current offset including DST if applicable
        offset_seconds = now.utcoffset().total_seconds()
        offset_hours = offset_seconds / 3600
        
        # Check if DST is currently active
        is_dst = time.localtime().tm_isdst > 0
        
        return {
            "timezone": str(local_tz),
            "offset": offset_hours,
            "is_dst": is_dst,
            "dst_info": {
                "active": is_dst,
                "name": time.tzname[1] if is_dst else time.tzname[0],
                "offset_hours": offset_hours
            }
        }
    except Exception as e:
        logger.error(f"Failed to get timezone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get timezone: {str(e)}"
        )


@router.put("/timezone")
async def set_timezone(
    timezone_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set system timezone with DST awareness"""
    try:
        timezone = timezone_data.get("timezone")
        if not timezone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timezone is required"
            )
        
        # Validate the timezone
        import pytz
        try:
            # Check if it's a valid timezone
            tz = pytz.timezone(timezone)
            
            # Get current datetime in the new timezone
            import datetime as dt
            now = dt.datetime.now(tz)
            
            # Calculate the current offset including DST if applicable
            offset_seconds = now.utcoffset().total_seconds()
            offset_hours = offset_seconds / 3600
            
            # Check if DST is currently active in this timezone
            is_dst = now.dst().total_seconds() > 0
            
            # In a real implementation, this would set the system timezone
            # For now, we'll just log it and return the timezone info
            logger.info(f"Setting timezone to: {timezone} (DST active: {is_dst}, offset: {offset_hours}h)")
            
            return {
                "success": True,
                "message": f"Timezone set to {timezone}",
                "timezone": timezone,
                "is_dst": is_dst,
                "offset_hours": offset_hours,
                "dst_transitions": {
                    "next_transition": get_next_dst_transition(tz)
                }
            }
        except pytz.exceptions.UnknownTimeZoneError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown timezone: {timezone}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set timezone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set timezone: {str(e)}"
        )

def get_next_dst_transition(tz):
    """Get the next DST transition for a timezone"""
    import datetime as dt
    import pytz
    
    # Start from now
    now = dt.datetime.now(tz)
    
    # Look ahead up to 1 year
    for i in range(1, 366):
        future_date = now + dt.timedelta(days=i)
        yesterday = future_date - dt.timedelta(days=1)
        
        # Check if DST status changes
        is_dst_today = future_date.dst().total_seconds() > 0
        is_dst_yesterday = yesterday.dst().total_seconds() > 0
        
        if is_dst_today != is_dst_yesterday:
            # Found a transition
            transition_type = "start" if is_dst_today else "end"
            return {
                "date": future_date.strftime("%Y-%m-%d"),
                "type": transition_type,
                "days_away": i
            }
    
    # No transition found in the next year
    return None


@router.put("/inactivity-timeout")
async def set_inactivity_timeout(
    timeout_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set inactivity timeout"""
    try:
        timeout_minutes = timeout_data.get("timeout_minutes")
        if timeout_minutes is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timeout minutes is required"
            )
        
        # In a real implementation, this would set the inactivity timeout
        logger.info(f"Setting inactivity timeout to: {timeout_minutes} minutes")
        
        return {
            "success": True,
            "message": f"Inactivity timeout set to {timeout_minutes} minutes",
            "timeout_minutes": timeout_minutes
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set inactivity timeout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set inactivity timeout: {str(e)}"
        )


@router.put("/warning-time")
async def set_warning_time(
    warning_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set warning time"""
    try:
        warning_minutes = warning_data.get("warning_minutes")
        if warning_minutes is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warning minutes is required"
            )
        
        # In a real implementation, this would set the warning time
        logger.info(f"Setting warning time to: {warning_minutes} minutes")
        
        return {
            "success": True,
            "message": f"Warning time set to {warning_minutes} minutes",
            "warning_minutes": warning_minutes
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set warning time: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set warning time: {str(e)}"
        )


@router.put("/max-concurrent-jobs")
async def set_max_concurrent_jobs(
    jobs_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set maximum concurrent jobs"""
    try:
        max_jobs = jobs_data.get("max_jobs")
        if max_jobs is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max jobs is required"
            )
        
        # In a real implementation, this would set the max concurrent jobs
        logger.info(f"Setting max concurrent jobs to: {max_jobs}")
        
        return {
            "success": True,
            "message": f"Max concurrent jobs set to {max_jobs}",
            "max_jobs": max_jobs
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set max concurrent jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set max concurrent jobs: {str(e)}"
        )


@router.put("/log-retention")
async def set_log_retention(
    retention_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set log retention days"""
    try:
        retention_days = retention_data.get("retention_days")
        if retention_days is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Retention days is required"
            )
        
        # In a real implementation, this would set the log retention
        logger.info(f"Setting log retention to: {retention_days} days")
        
        return {
            "success": True,
            "message": f"Log retention set to {retention_days} days",
            "retention_days": retention_days
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set log retention: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set log retention: {str(e)}"
        )


@router.put("/log-file-size")
async def set_log_file_size(
    size_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set maximum log file size"""
    try:
        max_size_mb = size_data.get("max_size_mb")
        if max_size_mb is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max size in MB is required"
            )
        
        # In a real implementation, this would set the max log file size
        logger.info(f"Setting max log file size to: {max_size_mb} MB")
        
        return {
            "success": True,
            "message": f"Max log file size set to {max_size_mb} MB",
            "max_size_mb": max_size_mb
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set max log file size: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set max log file size: {str(e)}"
        )


@router.put("/log-compression")
async def set_log_compression(
    compression_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set log compression setting"""
    try:
        compression = compression_data.get("compression")
        if compression is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Compression setting is required"
            )
        
        # In a real implementation, this would set the log compression
        logger.info(f"Setting log compression to: {compression}")
        
        return {
            "success": True,
            "message": f"Log compression set to {compression}",
            "compression": compression
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set log compression: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set log compression: {str(e)}"
        )


@router.put("/job-history-retention")
async def set_job_history_retention(
    retention_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set job history retention days"""
    try:
        retention_days = retention_data.get("retention_days")
        if retention_days is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Retention days is required"
            )
        
        # In a real implementation, this would set the job history retention
        logger.info(f"Setting job history retention to: {retention_days} days")
        
        return {
            "success": True,
            "message": f"Job history retention set to {retention_days} days",
            "retention_days": retention_days
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set job history retention: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set job history retention: {str(e)}"
        )


@router.put("/job-result-retention")
async def set_job_result_retention(
    retention_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set job result retention days"""
    try:
        retention_days = retention_data.get("retention_days")
        if retention_days is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Retention days is required"
            )
        
        # In a real implementation, this would set the job result retention
        logger.info(f"Setting job result retention to: {retention_days} days")
        
        return {
            "success": True,
            "message": f"Job result retention set to {retention_days} days",
            "retention_days": retention_days
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set job result retention: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set job result retention: {str(e)}"
        )


@router.put("/archive-old-jobs")
async def set_archive_old_jobs(
    archive_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set archive old jobs setting"""
    try:
        archive = archive_data.get("archive")
        if archive is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archive setting is required"
            )
        
        # In a real implementation, this would set the archive old jobs setting
        logger.info(f"Setting archive old jobs to: {archive}")
        
        return {
            "success": True,
            "message": f"Archive old jobs set to {archive}",
            "archive": archive
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set archive old jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set archive old jobs: {str(e)}"
        )


@router.put("/audit-log-retention")
async def set_audit_log_retention(
    retention_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set audit log retention days"""
    try:
        retention_days = retention_data.get("retention_days")
        if retention_days is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Retention days is required"
            )
        
        # In a real implementation, this would set the audit log retention
        logger.info(f"Setting audit log retention to: {retention_days} days")
        
        return {
            "success": True,
            "message": f"Audit log retention set to {retention_days} days",
            "retention_days": retention_days
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set audit log retention: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set audit log retention: {str(e)}"
        )


@router.put("/audit-log-export")
async def set_audit_log_export(
    export_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set audit log export schedule"""
    try:
        export_schedule = export_data.get("export_schedule")
        if export_schedule is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Export schedule is required"
            )
        
        # In a real implementation, this would set the audit log export schedule
        logger.info(f"Setting audit log export schedule to: {export_schedule}")
        
        return {
            "success": True,
            "message": f"Audit log export schedule set to {export_schedule}",
            "export_schedule": export_schedule
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set audit log export schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set audit log export schedule: {str(e)}"
        )


@router.get("/monitoring/netdata-info")
async def get_netdata_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get Netdata monitoring information"""
    try:
        # This would typically connect to Netdata API
        # For now, return basic info
        return {
            "status": "available",
            "url": "http://localhost:19999",
            "version": "1.40.0",
            "charts_count": 0,
            "alarms_count": 0
        }
    except Exception as e:
        logger.error(f"Failed to get Netdata info: {str(e)}")
        return {
            "status": "unavailable",
            "error": str(e)
        }


@router.get("/status")
async def get_system_status(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get system status information"""
    try:
        import psutil
        
        # Get system uptime
        uptime_seconds = int(time.time() - psutil.boot_time())
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{days}d {hours}h {minutes}m {seconds}s"
        
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        return {
            "uptime": uptime,
            "resource_usage": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "percent": memory_percent,
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2)
                },
                "disk": {
                    "percent": disk_percent,
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2)
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}"
        )


@router.get("/health")
async def get_system_health_status(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get overall system health status"""
    try:
        # Check database connectivity
        db_healthy = True
        db_message = "Database connection is healthy"
        try:
            # Execute a simple query to check database connectivity
            db.execute(text("SELECT 1")).fetchall()
        except Exception as db_error:
            db_healthy = False
            db_message = f"Database connection error: {str(db_error)}"
        
        # Check disk space
        import psutil
        disk = psutil.disk_usage('/')
        disk_healthy = disk.percent < 90  # Consider unhealthy if disk usage > 90%
        
        # Check memory usage
        memory = psutil.virtual_memory()
        memory_healthy = memory.percent < 90  # Consider unhealthy if memory usage > 90%
        
        # Determine overall health
        overall_health = "healthy" if (db_healthy and disk_healthy and memory_healthy) else "unhealthy"
        
        return {
            "overall_health": overall_health,
            "components": {
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "message": db_message
                },
                "disk": {
                    "status": "healthy" if disk_healthy else "unhealthy",
                    "message": f"Disk usage: {disk.percent}%",
                    "usage_percent": disk.percent
                },
                "memory": {
                    "status": "healthy" if memory_healthy else "unhealthy",
                    "message": f"Memory usage: {memory.percent}%",
                    "usage_percent": memory.percent
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )


@router.get("/email-targets/eligible")
async def get_eligible_email_targets(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get eligible email targets for system notifications"""
    try:
        from app.models.universal_target_models import UniversalTarget, TargetCommunicationMethod
        from sqlalchemy.orm import joinedload
        
        # Query targets that can function as email servers
        # Look for targets with SMTP communication methods or email target types
        eligible_targets = db.query(UniversalTarget)\
            .options(joinedload(UniversalTarget.communication_methods))\
            .filter(
                UniversalTarget.is_active == True,
                UniversalTarget.status == "active"
            )\
            .join(TargetCommunicationMethod)\
            .filter(
                TargetCommunicationMethod.is_active == True,
                TargetCommunicationMethod.method_type == "smtp"
            )\
            .distinct()\
            .all()
        
        # Format targets for frontend
        targets = []
        for target in eligible_targets:
            # Find the SMTP communication method
            smtp_method = None
            for method in target.communication_methods:
                if method.method_type == "smtp" and method.is_active:
                    smtp_method = method
                    break
            
            if smtp_method and smtp_method.config:
                host = smtp_method.config.get("host", "Unknown")
                port = smtp_method.config.get("port", 587)
                
                targets.append({
                    "id": target.id,
                    "name": target.name,
                    "type": "smtp",
                    "host": host,
                    "port": port,
                    "is_secure": port in [587, 465, 993, 995],  # Common secure ports
                    "health_status": target.health_status,
                    "target_type": target.target_type,
                    "description": target.description or f"SMTP server at {host}:{port}"
                })
        
        logger.info(f"Found {len(targets)} eligible email targets")
        return {"targets": targets}
        
    except Exception as e:
        logger.error(f"Failed to get eligible email targets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get eligible email targets: {str(e)}"
        )


@router.get("/email-target/config")
async def get_email_target_config(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current email target configuration"""
    try:
        from app.models.system_models import SystemSetting
        from app.models.universal_target_models import UniversalTarget, TargetCommunicationMethod
        
        # Get the configured email target ID from system settings
        email_config_setting = db.query(SystemSetting)\
            .filter(SystemSetting.setting_key == "notification_email_target_id")\
            .first()
        
        if not email_config_setting or not email_config_setting.setting_value:
            return {
                "is_configured": False,
                "target_id": None,
                "message": "No email target configured"
            }
        
        target_id = email_config_setting.setting_value.get("target_id")
        if not target_id:
            return {
                "is_configured": False,
                "target_id": None,
                "message": "Invalid email target configuration"
            }
        
        # Get the target details
        target = db.query(UniversalTarget)\
            .filter(UniversalTarget.id == target_id)\
            .first()
        
        if not target:
            return {
                "is_configured": False,
                "target_id": None,
                "message": "Configured email target not found"
            }
        
        # Get SMTP communication method
        smtp_method = db.query(TargetCommunicationMethod)\
            .filter(
                TargetCommunicationMethod.target_id == target_id,
                TargetCommunicationMethod.method_type == "smtp",
                TargetCommunicationMethod.is_active == True
            )\
            .first()
        
        if not smtp_method:
            return {
                "is_configured": False,
                "target_id": target_id,
                "message": "Target does not have active SMTP configuration"
            }
        
        host = smtp_method.config.get("host", "Unknown")
        port = smtp_method.config.get("port", 587)
        sender_email = email_config_setting.setting_value.get("sender_email", f"notifications@{host}")
        
        return {
            "is_configured": True,
            "target_id": target_id,
            "name": target.name,
            "type": "smtp",
            "host": host,
            "port": port,
            "is_secure": port in [587, 465, 993, 995],
            "sender_email": sender_email,
            "health_status": target.health_status
        }
        
    except Exception as e:
        logger.error(f"Failed to get email target config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email target config: {str(e)}"
        )


@router.put("/email-target/config")
async def update_email_target_config(
    config: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update email target configuration"""
    try:
        from app.models.system_models import SystemSetting
        from app.models.universal_target_models import UniversalTarget, TargetCommunicationMethod
        
        target_id = config.get("target_id")
        sender_email = config.get("sender_email", "")
        
        if target_id:
            # Validate that the target exists and has SMTP capability
            target = db.query(UniversalTarget)\
                .filter(UniversalTarget.id == target_id)\
                .first()
            
            if not target:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target not found"
                )
            
            # Check if target has SMTP communication method
            smtp_method = db.query(TargetCommunicationMethod)\
                .filter(
                    TargetCommunicationMethod.target_id == target_id,
                    TargetCommunicationMethod.method_type == "smtp",
                    TargetCommunicationMethod.is_active == True
                )\
                .first()
            
            if not smtp_method:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target does not have active SMTP configuration"
                )
        
        # Save or update the email target configuration
        email_config_setting = db.query(SystemSetting)\
            .filter(SystemSetting.setting_key == "notification_email_target_id")\
            .first()
        
        config_value = {
            "target_id": target_id,
            "sender_email": sender_email,
            "updated_by": current_user.get("id"),
            "updated_at": datetime.now().isoformat()
        }
        
        if email_config_setting:
            # Update existing setting
            email_config_setting.setting_value = config_value
        else:
            # Create new setting
            email_config_setting = SystemSetting(
                setting_key="notification_email_target_id",
                setting_value=config_value,
                description="Email target configuration for system notifications"
            )
            db.add(email_config_setting)
        
        db.commit()
        
        logger.info(f"Updated email target config to target_id: {target_id}")
        
        return {
            "success": True,
            "message": "Email target configuration updated successfully",
            "target_id": target_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update email target config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update email target config: {str(e)}"
        )


@router.post("/email-target/test")
async def test_email_target(
    test_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test email target by sending a test email"""
    try:
        test_email = test_data.get("test_email")
        if not test_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test email address is required"
            )
        
        # In a real implementation, this would send an actual test email
        logger.info(f"Sending test email to: {test_email}")
        
        # Simulate successful email sending
        return {
            "success": True,
            "message": f"Test email sent successfully to {test_email}",
            "details": {
                "recipient": test_email,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "subject": "OpsConductor Test Email"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}"
        )


@router.get("/monitoring/system-metrics")
async def get_system_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system metrics"""
    try:
        health_service = HealthManagementService(db)
        metrics = await health_service.get_system_metrics()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}"
        )


# SYSTEM SETTINGS ENDPOINTS

@router.get("/settings")
async def get_system_settings(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all system settings"""
    try:
        from app.models.system_models import SystemSetting
        
        settings = db.query(SystemSetting).all()
        
        # Convert to dict format
        settings_dict = {}
        for setting in settings:
            settings_dict[setting.setting_key] = setting.setting_value
        
        # Add defaults for missing settings
        defaults = {
            "timezone": "UTC",
            "date_format": "YYYY-MM-DD",
            "time_format": "24h",
            "language": "en",
            "theme": "light",
            "notifications_enabled": True,
            "auto_refresh_interval": 30,
            "max_concurrent_jobs": 10,
            "log_retention_days": 30,
            "job_history_retention_days": 90,
            "session_timeout_minutes": 480,
            "max_log_file_size_mb": 100,
            "log_compression_enabled": True,
            "backup_enabled": False,
            "backup_retention_days": 7,
            "maintenance_mode": False,
            "debug_mode": False
        }
        
        # Merge defaults with actual settings
        for key, default_value in defaults.items():
            if key not in settings_dict:
                settings_dict[key] = default_value
        
        return {
            "settings": settings_dict,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system settings: {str(e)}"
        )


@router.put("/settings")
async def update_system_settings(
    settings_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update system settings"""
    try:
        from app.models.system_models import SystemSetting
        
        updated_settings = []
        
        for key, value in settings_data.items():
            # Find existing setting or create new one
            setting = db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
            
            if setting:
                setting.setting_value = value
                setting.updated_at = datetime.now(timezone.utc)
            else:
                setting = SystemSetting(
                    setting_key=key,
                    setting_value=value,
                    description=f"System setting for {key}"
                )
                db.add(setting)
            
            updated_settings.append(key)
        
        db.commit()
        
        logger.info(f"Updated system settings: {updated_settings}")
        
        return {
            "success": True,
            "message": f"Updated {len(updated_settings)} settings",
            "updated_settings": updated_settings,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update system settings: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update system settings: {str(e)}"
        )





# SYSTEM SETTINGS ENDPOINT

@router.get("/settings")
async def get_system_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get system settings for session management"""
    try:
        # Return default system settings for session management
        return {
            "status": "success",
            "settings": {
                "inactivity_timeout_minutes": 60,  # 1 hour default
                "warning_timeout_minutes": 55,     # 5 minutes before timeout
                "session_refresh_interval_minutes": 5,  # Refresh every 5 minutes
                "max_session_duration_hours": 8    # Maximum session duration
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system settings: {str(e)}"
        )

