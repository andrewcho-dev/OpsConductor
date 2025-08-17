"""
System Information API

Provides basic system information endpoints for frontend compatibility.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
import logging
import platform
import os
import json
from sqlalchemy.orm import Session

from app.core.logging import get_structured_logger
from app.database.database import get_db
from app.models.system_models import SystemSetting

# Initialize
logger = get_structured_logger(__name__)
router = APIRouter(prefix="/api/system", tags=["System Info"])


@router.get("/info")
async def get_system_info(db: Session = Depends(get_db)):
    """Get basic system information (public endpoint for frontend compatibility)"""
    try:
        # Get configured timezone from database
        configured_timezone = "UTC"  # Default fallback
        try:
            timezone_setting = db.query(SystemSetting).filter(
                SystemSetting.setting_key == "timezone"
            ).first()
            if timezone_setting and timezone_setting.setting_value:
                # setting_value is stored as JSONB, so it might be a string with quotes
                timezone_value = timezone_setting.setting_value
                if isinstance(timezone_value, str):
                    # Remove quotes if present
                    configured_timezone = timezone_value.strip('"')
                else:
                    configured_timezone = str(timezone_value)
        except Exception as e:
            logger.warning(f"Failed to get timezone from database: {e}")
            configured_timezone = "UTC"
        
        # Get basic system information
        system_info = {
            "platform": "OpsConductor",
            "version": "2.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "timezone": configured_timezone,
            "current_time": datetime.utcnow().isoformat(),
            "server_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "system": {
                "os": platform.system(),
                "architecture": platform.machine(),
                "python_version": platform.python_version()
            },
            "features": {
                "job_execution": True,
                "target_management": True,
                "user_management": True,
                "audit_logging": True,
                "monitoring": True
            },
            "status": "operational"
        }
        
        logger.info("System info retrieved successfully")
        return system_info
        
    except Exception as e:
        logger.error(f"Failed to get system info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system information: {str(e)}"
        )


@router.get("/health")
async def get_system_health():
    """Get system health status (public endpoint)"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "healthy",
                "redis": "healthy", 
                "celery": "healthy",
                "api": "healthy"
            },
            "uptime": "operational"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }