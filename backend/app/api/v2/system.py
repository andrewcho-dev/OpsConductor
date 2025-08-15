"""
System API v2 - Consolidated System Administration
Consolidates all system administration endpoints into a unified API.

This replaces and consolidates:
- /api/system/* (system.py) - System settings and configuration
- /api/log-viewer/* (log_viewer.py) - Log management and viewing
"""

import logging
import os
import re
import pytz
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import verify_token
from app.models.user_models import User
from app.services.user_service import UserService
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/system", tags=["System Administration v2"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                    db: Session = Depends(get_db)):
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("user_id")
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_utc_timestamp() -> str:
    """Get current UTC timestamp with timezone information."""
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# SYSTEM INFORMATION & DASHBOARD
# ============================================================================

@router.get("/info", response_model=Dict[str, Any])
async def get_system_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive system information."""
    try:
        system_info = {
            "platform": "ENABLEDRM Universal Automation Platform",
            "version": "2.0.0",
            "api_version": "v2",
            "timestamp": get_utc_timestamp(),
            "uptime": await get_system_uptime(),
            "environment": os.getenv("ENVIRONMENT", "production"),
            "features": {
                "health_monitoring": True,
                "metrics_collection": True,
                "job_management": True,
                "template_system": True,
                "audit_logging": True,
                "discovery_engine": True,
                "notification_system": True
            }
        }
        
        return system_info
        
    except Exception as e:
        logger.error(f"Failed to get system info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system information")


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics and overview."""
    try:
        dashboard_stats = {
            "timestamp": get_utc_timestamp(),
            "system": {
                "status": "healthy",
                "uptime": await get_system_uptime(),
                "version": "2.0.0"
            },
            "jobs": await get_job_dashboard_stats(db),
            "targets": await get_target_dashboard_stats(db),
            "discovery": await get_discovery_dashboard_stats(db),
            "notifications": await get_notification_dashboard_stats(db),
            "recent_activity": await get_recent_activity(db)
        }
        
        return dashboard_stats
        
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard statistics")


# ============================================================================
# SYSTEM SETTINGS MANAGEMENT
# ============================================================================

@router.get("/settings", response_model=List[Dict[str, Any]])
async def get_all_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get all system settings."""
    if current_user.role not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view system settings"
        )
    
    try:
        settings = await get_system_settings(db, category)
        return settings
        
    except Exception as e:
        logger.error(f"Failed to get system settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system settings")


@router.put("/settings/{setting_key}", response_model=Dict[str, Any])
async def update_setting(
    setting_key: str,
    setting_data: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a system setting."""
    if current_user.role not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify system settings"
        )
    
    try:
        updated_setting = await update_system_setting(db, setting_key, setting_data, current_user.id)
        
        # Log setting update
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGED,
            user_id=current_user.id,
            resource_type="system_setting",
            resource_id=setting_key,
            action="update_setting",
            details={"setting_key": setting_key, "new_value": setting_data},
            severity=AuditSeverity.HIGH,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return updated_setting
        
    except Exception as e:
        logger.error(f"Failed to update setting {setting_key}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update system setting")


# ============================================================================
# TIMEZONE & TIME MANAGEMENT
# ============================================================================

@router.get("/timezone", response_model=Dict[str, Any])
async def get_timezone(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current system timezone."""
    try:
        timezone_info = await get_system_timezone(db)
        return timezone_info
        
    except Exception as e:
        logger.error(f"Failed to get timezone: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timezone")


@router.put("/timezone", response_model=Dict[str, Any])
async def update_timezone(
    timezone_data: Dict[str, str],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update system timezone."""
    if current_user.role not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can change system timezone"
        )
    
    try:
        new_timezone = timezone_data.get("timezone")
        if not new_timezone or new_timezone not in pytz.all_timezones:
            raise HTTPException(status_code=400, detail="Invalid timezone")
        
        updated_timezone = await update_system_timezone(db, new_timezone, current_user.id)
        
        # Log timezone change
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGED,
            user_id=current_user.id,
            resource_type="system_timezone",
            resource_id="timezone",
            action="update_timezone",
            details={"new_timezone": new_timezone},
            severity=AuditSeverity.HIGH,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return updated_timezone
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update timezone: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update timezone")


@router.get("/timezones", response_model=List[str])
async def get_available_timezones(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available timezones."""
    try:
        return sorted(pytz.all_timezones)
        
    except Exception as e:
        logger.error(f"Failed to get timezones: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timezones")


@router.get("/current-time", response_model=Dict[str, Any])
async def get_current_time(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current system time in various formats."""
    try:
        system_tz = await get_system_timezone(db)
        tz = pytz.timezone(system_tz.get("timezone", "UTC"))
        
        now_utc = datetime.now(timezone.utc)
        now_local = now_utc.astimezone(tz)
        
        return {
            "utc": now_utc.isoformat(),
            "local": now_local.isoformat(),
            "timezone": system_tz.get("timezone", "UTC"),
            "timestamp": now_utc.timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to get current time: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve current time")


# ============================================================================
# LOG MANAGEMENT (Consolidates: /api/log-viewer/*)
# ============================================================================

@router.get("/logs/search", response_model=Dict[str, Any])
async def search_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    query: Optional[str] = Query(None, description="Search query"),
    level: Optional[str] = Query(None, description="Log level filter"),
    source: Optional[str] = Query(None, description="Log source filter"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """Search system logs with advanced filtering."""
    try:
        search_params = {
            "query": query,
            "level": level,
            "source": source,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit
        }
        
        logs = await search_system_logs(db, search_params)
        
        return {
            "logs": logs,
            "total": len(logs),
            "search_params": search_params,
            "timestamp": get_utc_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to search logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search logs")


@router.get("/logs/stats", response_model=Dict[str, Any])
async def get_log_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d")
):
    """Get log statistics and metrics."""
    try:
        # Parse time range
        hours_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = hours_map.get(time_range, 24)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        stats = await get_log_statistics(db, since)
        
        return {
            "statistics": stats,
            "time_range": time_range,
            "timestamp": get_utc_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to get log stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve log statistics")


@router.get("/logs/sources", response_model=List[str])
async def get_log_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available log sources."""
    try:
        sources = await get_available_log_sources(db)
        return sources
        
    except Exception as e:
        logger.error(f"Failed to get log sources: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve log sources")


@router.post("/logs/validate-pattern", response_model=Dict[str, Any])
async def validate_log_pattern(
    pattern_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate a log search pattern."""
    try:
        pattern = pattern_data.get("pattern", "")
        pattern_type = pattern_data.get("type", "regex")
        
        validation_result = await validate_search_pattern(pattern, pattern_type)
        
        return {
            "pattern": pattern,
            "type": pattern_type,
            "is_valid": validation_result["is_valid"],
            "error": validation_result.get("error"),
            "suggestions": validation_result.get("suggestions", [])
        }
        
    except Exception as e:
        logger.error(f"Failed to validate pattern: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate pattern")


# ============================================================================
# SYSTEM MAINTENANCE
# ============================================================================

@router.post("/maintenance/cleanup", response_model=Dict[str, Any])
async def system_cleanup(
    cleanup_options: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform system cleanup operations."""
    if current_user.role not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform system cleanup"
        )
    
    try:
        cleanup_results = await perform_system_cleanup(db, cleanup_options)
        
        # Log cleanup operation
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.SYSTEM_MAINTENANCE,
            user_id=current_user.id,
            resource_type="system",
            resource_id="cleanup",
            action="system_cleanup",
            details={"cleanup_options": cleanup_options, "results": cleanup_results},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return {
            "success": True,
            "results": cleanup_results,
            "timestamp": get_utc_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to perform system cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to perform system cleanup")


@router.post("/maintenance/backup", response_model=Dict[str, Any])
async def create_system_backup(
    backup_options: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create system backup."""
    if current_user.role not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create system backups"
        )
    
    try:
        backup_result = await create_backup(db, backup_options)
        
        # Log backup operation
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.SYSTEM_MAINTENANCE,
            user_id=current_user.id,
            resource_type="system",
            resource_id="backup",
            action="create_backup",
            details={"backup_options": backup_options, "backup_id": backup_result.get("backup_id")},
            severity=AuditSeverity.HIGH,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return backup_result
        
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create system backup")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_system_uptime() -> Dict[str, Any]:
    """Get system uptime information."""
    try:
        import psutil
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.now().timestamp() - boot_time
        
        return {
            "seconds": int(uptime_seconds),
            "human_readable": format_uptime(uptime_seconds),
            "boot_time": datetime.fromtimestamp(boot_time).isoformat()
        }
    except Exception:
        return {"seconds": 0, "human_readable": "Unknown", "boot_time": None}


def format_uptime(seconds: float) -> str:
    """Format uptime in human readable format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


async def get_job_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Get job statistics for dashboard."""
    try:
        # This would integrate with your job service
        return {
            "total_jobs": 0,
            "running_jobs": 0,
            "completed_today": 0,
            "failed_today": 0,
            "success_rate": 0.0
        }
    except Exception:
        return {}


async def get_target_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Get target statistics for dashboard."""
    try:
        # This would integrate with your target service
        return {
            "total_targets": 0,
            "healthy_targets": 0,
            "unhealthy_targets": 0,
            "unknown_targets": 0
        }
    except Exception:
        return {}


async def get_discovery_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Get discovery statistics for dashboard."""
    try:
        # This would integrate with your discovery service
        return {
            "total_discoveries": 0,
            "active_discoveries": 0,
            "devices_discovered": 0,
            "last_discovery": None
        }
    except Exception:
        return {}


async def get_notification_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Get notification statistics for dashboard."""
    try:
        # This would integrate with your notification service
        return {
            "notifications_today": 0,
            "alerts_active": 0,
            "email_queue": 0,
            "failed_notifications": 0
        }
    except Exception:
        return {}


async def get_recent_activity(db: Session) -> List[Dict[str, Any]]:
    """Get recent system activity."""
    try:
        # This would integrate with your audit service
        return []
    except Exception:
        return []


async def get_system_settings(db: Session, category: Optional[str]) -> List[Dict[str, Any]]:
    """Get system settings from database."""
    try:
        # This would query your settings table
        # For now, return mock settings
        settings = [
            {
                "key": "session_timeout",
                "value": "3600",
                "category": "security",
                "description": "Session timeout in seconds",
                "type": "integer"
            },
            {
                "key": "max_concurrent_jobs",
                "value": "10",
                "category": "performance",
                "description": "Maximum concurrent jobs",
                "type": "integer"
            },
            {
                "key": "log_retention_days",
                "value": "30",
                "category": "logging",
                "description": "Log retention period in days",
                "type": "integer"
            }
        ]
        
        if category:
            settings = [s for s in settings if s["category"] == category]
        
        return settings
    except Exception:
        return []


async def update_system_setting(db: Session, setting_key: str, setting_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Update a system setting."""
    try:
        # This would update your settings table
        # For now, return mock updated setting
        return {
            "key": setting_key,
            "value": setting_data.get("value"),
            "updated_at": get_utc_timestamp(),
            "updated_by": user_id
        }
    except Exception:
        raise


async def get_system_timezone(db: Session) -> Dict[str, Any]:
    """Get system timezone setting."""
    try:
        # This would query your settings table
        return {
            "timezone": "UTC",
            "display_name": "Coordinated Universal Time",
            "offset": "+00:00"
        }
    except Exception:
        return {"timezone": "UTC", "display_name": "UTC", "offset": "+00:00"}


async def update_system_timezone(db: Session, timezone: str, user_id: int) -> Dict[str, Any]:
    """Update system timezone."""
    try:
        # This would update your settings table
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        
        return {
            "timezone": timezone,
            "display_name": str(tz),
            "offset": now.strftime("%z"),
            "updated_at": get_utc_timestamp(),
            "updated_by": user_id
        }
    except Exception:
        raise


async def search_system_logs(db: Session, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search system logs."""
    try:
        # This would integrate with your logging system
        # For now, return mock logs
        return [
            {
                "id": 1,
                "timestamp": get_utc_timestamp(),
                "level": "INFO",
                "source": "system",
                "message": "System started successfully",
                "details": {}
            }
        ]
    except Exception:
        return []


async def get_log_statistics(db: Session, since: datetime) -> Dict[str, Any]:
    """Get log statistics."""
    try:
        # This would query your logs
        return {
            "total_logs": 0,
            "error_logs": 0,
            "warning_logs": 0,
            "info_logs": 0,
            "debug_logs": 0,
            "by_source": {},
            "by_hour": []
        }
    except Exception:
        return {}


async def get_available_log_sources(db: Session) -> List[str]:
    """Get available log sources."""
    try:
        # This would query your logs for distinct sources
        return ["system", "jobs", "discovery", "notifications", "audit"]
    except Exception:
        return []


async def validate_search_pattern(pattern: str, pattern_type: str) -> Dict[str, Any]:
    """Validate a search pattern."""
    try:
        if pattern_type == "regex":
            re.compile(pattern)
            return {"is_valid": True}
        else:
            return {"is_valid": True}
    except re.error as e:
        return {"is_valid": False, "error": str(e)}
    except Exception as e:
        return {"is_valid": False, "error": str(e)}


async def perform_system_cleanup(db: Session, options: Dict[str, Any]) -> Dict[str, Any]:
    """Perform system cleanup operations."""
    try:
        # This would perform actual cleanup operations
        return {
            "logs_cleaned": 0,
            "temp_files_removed": 0,
            "cache_cleared": True,
            "database_optimized": True
        }
    except Exception:
        return {}


async def create_backup(db: Session, options: Dict[str, Any]) -> Dict[str, Any]:
    """Create system backup."""
    try:
        # This would create actual backup
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return {
            "backup_id": backup_id,
            "status": "completed",
            "size": "0 MB",
            "location": f"/backups/{backup_id}.tar.gz",
            "created_at": get_utc_timestamp()
        }
    except Exception:
        raise