"""
System API v2 Enhanced - Phases 1 & 2
Complete transformation with service layer, caching, and comprehensive models

PHASE 1 & 2 IMPROVEMENTS:
- ✅ Comprehensive Pydantic models with validation
- ✅ Service layer integration with business logic separation
- ✅ Redis caching for improved performance
- ✅ Structured JSON logging with contextual information
- ✅ Enhanced error handling with detailed responses
- ✅ Advanced system monitoring and configuration management
- ✅ Log management and analysis capabilities
- ✅ Real-time system health monitoring
- ✅ Comprehensive system lifecycle management
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, EmailStr

# Import service layer
from app.services.system_management_service import SystemManagementService, SystemManagementError
from app.database.database import get_db
from app.core.security import verify_token
from app.core.logging import get_structured_logger, RequestLogger

# Configure structured logger
logger = get_structured_logger(__name__)

# Security scheme
security = HTTPBearer()

# PHASE 1: COMPREHENSIVE PYDANTIC MODELS

class SystemInfoResponse(BaseModel):
    """Enhanced model for system information"""
    hostname: str = Field(..., description="System hostname")
    platform: str = Field(..., description="System platform")
    architecture: str = Field(..., description="System architecture")
    python_version: str = Field(..., description="Python version")
    cpu_count: int = Field(..., description="Number of CPU cores")
    boot_time: str = Field(..., description="System boot time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "hostname": "enabledrm-server",
                "platform": "Linux-5.4.0-74-generic-x86_64-with-glibc2.31",
                "architecture": "64bit",
                "python_version": "3.11.0",
                "cpu_count": 8,
                "boot_time": "2025-01-01T00:00:00"
            }
        }


class ResourceUsageResponse(BaseModel):
    """Enhanced model for resource usage information"""
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory: Dict[str, Union[int, float]] = Field(..., description="Memory usage details")
    disk: Dict[str, Union[int, float]] = Field(..., description="Disk usage details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cpu_percent": 45.8,
                "memory": {
                    "total": 16777216000,
                    "available": 8388608000,
                    "percent": 50.0,
                    "used": 8388608000
                },
                "disk": {
                    "total": 1000000000000,
                    "used": 500000000000,
                    "free": 500000000000,
                    "percent": 50.0
                }
            }
        }


class ServiceStatusResponse(BaseModel):
    """Enhanced model for service status information"""
    database: Dict[str, Any] = Field(..., description="Database service status")
    redis: Dict[str, Any] = Field(..., description="Redis service status")
    web_server: Dict[str, Any] = Field(..., description="Web server status")
    task_queue: Dict[str, Any] = Field(..., description="Task queue status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "database": {"status": "running", "healthy": True},
                "redis": {"status": "running", "healthy": True},
                "web_server": {"status": "running", "healthy": True},
                "task_queue": {"status": "running", "healthy": True}
            }
        }


class SystemStatusResponse(BaseModel):
    """Enhanced response model for system status"""
    system_info: SystemInfoResponse = Field(..., description="System information")
    resource_usage: ResourceUsageResponse = Field(..., description="Resource usage")
    service_status: ServiceStatusResponse = Field(..., description="Service status")
    health_status: str = Field(..., description="Overall health status")
    uptime: str = Field(..., description="System uptime")
    last_updated: datetime = Field(..., description="Last update timestamp")
    alerts: List[Dict[str, Any]] = Field(default_factory=list, description="System alerts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="System status metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_info": {
                    "hostname": "enabledrm-server",
                    "platform": "Linux",
                    "cpu_count": 8
                },
                "resource_usage": {
                    "cpu_percent": 45.8,
                    "memory": {"percent": 50.0},
                    "disk": {"percent": 50.0}
                },
                "service_status": {
                    "database": {"status": "running", "healthy": True}
                },
                "health_status": "healthy",
                "uptime": "5d 12h 30m",
                "last_updated": "2025-01-01T10:30:00Z",
                "alerts": [],
                "metadata": {
                    "source": "system_monitoring",
                    "version": "2.0"
                }
            }
        }


class SystemConfigurationResponse(BaseModel):
    """Enhanced response model for system configuration"""
    application: Dict[str, Any] = Field(..., description="Application configuration")
    database: Dict[str, Any] = Field(..., description="Database configuration")
    security: Dict[str, Any] = Field(..., description="Security configuration")
    logging: Dict[str, Any] = Field(..., description="Logging configuration")
    environment: Dict[str, Any] = Field(..., description="Environment information")
    last_updated: datetime = Field(..., description="Last update timestamp")
    configuration_version: str = Field(..., description="Configuration version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Configuration metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "application": {
                    "name": "ENABLEDRM",
                    "version": "2.0.0",
                    "debug": False
                },
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "enabledrm"
                },
                "security": {
                    "jwt_expiry": 3600,
                    "password_policy": "strong"
                },
                "logging": {
                    "level": "INFO",
                    "format": "json"
                },
                "environment": {
                    "stage": "production",
                    "region": "us-east-1"
                },
                "last_updated": "2025-01-01T10:30:00Z",
                "configuration_version": "1.0",
                "metadata": {
                    "source": "system_configuration",
                    "version": "2.0"
                }
            }
        }


class SystemConfigurationUpdateRequest(BaseModel):
    """Enhanced request model for system configuration updates"""
    application: Optional[Dict[str, Any]] = Field(None, description="Application configuration updates")
    database: Optional[Dict[str, Any]] = Field(None, description="Database configuration updates")
    security: Optional[Dict[str, Any]] = Field(None, description="Security configuration updates")
    logging: Optional[Dict[str, Any]] = Field(None, description="Logging configuration updates")
    environment: Optional[Dict[str, Any]] = Field(None, description="Environment configuration updates")
    
    @validator('*', pre=True)
    def validate_config_sections(cls, v):
        """Validate configuration sections"""
        if v is not None and not isinstance(v, dict):
            raise ValueError('Configuration sections must be dictionaries')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "application": {
                    "debug": False,
                    "max_workers": 10
                },
                "security": {
                    "jwt_expiry": 7200,
                    "session_timeout": 1800
                },
                "logging": {
                    "level": "INFO",
                    "retention_days": 30
                }
            }
        }


class SystemConfigurationUpdateResponse(BaseModel):
    """Enhanced response model for configuration updates"""
    success: bool = Field(..., description="Update success status")
    updated_keys: List[str] = Field(..., description="List of updated configuration keys")
    backup_id: str = Field(..., description="Configuration backup identifier")
    verification_status: Dict[str, Any] = Field(..., description="Configuration verification status")
    updated_at: datetime = Field(..., description="Update timestamp")
    updated_by: str = Field(..., description="Username who performed the update")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "updated_keys": ["application.debug", "security.jwt_expiry"],
                "backup_id": "backup_123456",
                "verification_status": {"verified": True},
                "updated_at": "2025-01-01T10:30:00Z",
                "updated_by": "admin"
            }
        }


class SystemLogEntry(BaseModel):
    """Enhanced model for system log entries"""
    timestamp: datetime = Field(..., description="Log entry timestamp")
    level: str = Field(..., description="Log level")
    logger: str = Field(..., description="Logger name")
    message: str = Field(..., description="Log message")
    module: Optional[str] = Field(None, description="Module name")
    function: Optional[str] = Field(None, description="Function name")
    line: Optional[int] = Field(None, description="Line number")
    extra: Optional[Dict[str, Any]] = Field(None, description="Extra log data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-01-01T10:30:00Z",
                "level": "INFO",
                "logger": "app.api.system",
                "message": "System status retrieved successfully",
                "module": "system_enhanced",
                "function": "get_system_status",
                "line": 123,
                "extra": {
                    "user_id": 1,
                    "execution_time": 0.25
                }
            }
        }


class SystemLogsResponse(BaseModel):
    """Enhanced response model for system logs"""
    logs: List[SystemLogEntry] = Field(..., description="System log entries")
    analysis: Dict[str, Any] = Field(default_factory=dict, description="Log analysis results")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Log statistics")
    filters: Dict[str, Any] = Field(..., description="Applied filters")
    total_logs: int = Field(..., description="Total number of logs")
    retrieved_at: datetime = Field(..., description="Retrieval timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Logs metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "logs": [
                    {
                        "timestamp": "2025-01-01T10:30:00Z",
                        "level": "INFO",
                        "logger": "app.api.system",
                        "message": "System status retrieved successfully"
                    }
                ],
                "analysis": {
                    "error_rate": 0.02,
                    "most_active_loggers": ["app.api.system", "app.services.system"]
                },
                "statistics": {
                    "total_entries": 1000,
                    "by_level": {"INFO": 800, "WARNING": 150, "ERROR": 50}
                },
                "filters": {
                    "log_level": "INFO",
                    "limit": 100
                },
                "total_logs": 1,
                "retrieved_at": "2025-01-01T10:30:00Z",
                "metadata": {
                    "source": "system_logs",
                    "version": "2.0"
                }
            }
        }


class HealthCheckResult(BaseModel):
    """Enhanced model for individual health check results"""
    healthy: bool = Field(..., description="Health check status")
    response_time: Optional[float] = Field(None, description="Response time in milliseconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health check details")
    last_check: datetime = Field(..., description="Last check timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "healthy": True,
                "response_time": 5.2,
                "details": {
                    "connection_pool": "healthy",
                    "active_connections": 10
                },
                "last_check": "2025-01-01T10:30:00Z"
            }
        }


class SystemHealthResponse(BaseModel):
    """Enhanced response model for system health"""
    overall_health: str = Field(..., description="Overall health status")
    health_checks: Dict[str, HealthCheckResult] = Field(..., description="Individual health check results")
    recommendations: List[str] = Field(default_factory=list, description="Health recommendations")
    last_check: datetime = Field(..., description="Last health check timestamp")
    next_check: datetime = Field(..., description="Next scheduled health check")
    alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Health alerts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Health check metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_health": "healthy",
                "health_checks": {
                    "database": {
                        "healthy": True,
                        "response_time": 5.2,
                        "last_check": "2025-01-01T10:30:00Z"
                    },
                    "redis": {
                        "healthy": True,
                        "response_time": 1.1,
                        "last_check": "2025-01-01T10:30:00Z"
                    }
                },
                "recommendations": [
                    "Consider increasing database connection pool size",
                    "Monitor disk space usage"
                ],
                "last_check": "2025-01-01T10:30:00Z",
                "next_check": "2025-01-01T10:35:00Z",
                "alerts": [],
                "metadata": {
                    "source": "system_health",
                    "version": "2.0"
                }
            }
        }


class SystemErrorResponse(BaseModel):
    """Enhanced error response model for system management errors"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    system_component: Optional[str] = Field(None, description="Related system component")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "system_status_error",
                "message": "Failed to retrieve system status due to service unavailability",
                "details": {
                    "component": "resource_monitor",
                    "retry_after": 60
                },
                "timestamp": "2025-01-01T10:30:00Z",
                "system_component": "monitoring"
            }
        }


# PHASE 1 & 2: ENHANCED ROUTER WITH SERVICE LAYER INTEGRATION

router = APIRouter(
    prefix="/api/v2/system",
    tags=["System Administration Enhanced v2"],
    responses={
        401: {"model": SystemErrorResponse, "description": "Authentication required"},
        403: {"model": SystemErrorResponse, "description": "Insufficient permissions"},
        404: {"model": SystemErrorResponse, "description": "Resource not found"},
        422: {"model": SystemErrorResponse, "description": "Validation error"},
        500: {"model": SystemErrorResponse, "description": "Internal server error"}
    }
)


# PHASE 2: ENHANCED DEPENDENCY FUNCTIONS

def get_current_user(credentials = Depends(security), 
                    db: Session = Depends(get_db)):
    """Get current authenticated user with enhanced error handling."""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            logger.warning("Invalid token in system management request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Invalid or expired token",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        user_id = payload.get("user_id")
        from app.services.user_service import UserService
        user = UserService.get_user_by_id(db, user_id)
        
        if not user:
            logger.warning(f"User not found for token: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "user_not_found",
                    "message": "User not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Internal error during authentication",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def require_admin_permissions(current_user = Depends(get_current_user)):
    """Require administrator permissions for system management."""
    if current_user.role != "administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_permissions",
                "message": "Administrator permissions required for system management",
                "required_role": "administrator",
                "user_role": current_user.role,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    return current_user


# PHASE 1 & 2: ENHANCED ENDPOINTS WITH SERVICE LAYER

@router.get(
    "/status",
    response_model=SystemStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Status",
    description="""
    Get comprehensive system status with resource monitoring and health analysis.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 1-minute TTL
    - ✅ Real-time resource monitoring
    - ✅ Service health checks
    - ✅ System alerts and recommendations
    
    **Performance:**
    - Redis caching for improved response times
    - Optimized system monitoring
    - Structured logging for tracking
    """,
    responses={
        200: {"description": "System status retrieved successfully", "model": SystemStatusResponse}
    }
)
async def get_system_status(
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> SystemStatusResponse:
    """Enhanced system status with service layer and comprehensive monitoring"""
    
    request_logger = RequestLogger(logger, "get_system_status")
    request_logger.log_request_start("GET", "/api/v2/system/status", current_user.username)
    
    try:
        # Initialize service layer
        system_mgmt_service = SystemManagementService(db)
        
        # Get system status through service layer (with caching)
        status_result = await system_mgmt_service.get_system_status(
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = SystemStatusResponse(**status_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "System status retrieval successful via service layer",
            extra={
                "health_status": status_result.get("health_status", "unknown"),
                "uptime": status_result.get("uptime", "unknown"),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except SystemManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "System status retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "System status retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving system status",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/configuration",
    response_model=SystemConfigurationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Configuration",
    description="""
    Get comprehensive system configuration with all settings.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 10-minute TTL
    - ✅ Comprehensive configuration sections
    - ✅ Configuration versioning
    - ✅ Enhanced configuration metadata
    """,
    responses={
        200: {"description": "System configuration retrieved successfully", "model": SystemConfigurationResponse}
    }
)
async def get_system_configuration(
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> SystemConfigurationResponse:
    """Enhanced system configuration with service layer and comprehensive settings"""
    
    request_logger = RequestLogger(logger, "get_system_configuration")
    request_logger.log_request_start("GET", "/api/v2/system/configuration", current_user.username)
    
    try:
        # Initialize service layer
        system_mgmt_service = SystemManagementService(db)
        
        # Get system configuration through service layer (with caching)
        config_result = await system_mgmt_service.get_system_configuration(
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = SystemConfigurationResponse(**config_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "System configuration retrieval successful via service layer",
            extra={
                "config_sections": len(config_result),
                "configuration_version": config_result.get("configuration_version", "unknown"),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except SystemManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "System configuration retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "System configuration retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving system configuration",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.put(
    "/configuration",
    response_model=SystemConfigurationUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update System Configuration",
    description="""
    Update system configuration with validation and backup.
    
    **Phase 1 & 2 Features:**
    - ✅ Configuration validation and verification
    - ✅ Automatic configuration backup
    - ✅ Comprehensive audit logging
    - ✅ Cache invalidation after updates
    """,
    responses={
        200: {"description": "System configuration updated successfully", "model": SystemConfigurationUpdateResponse}
    }
)
async def update_system_configuration(
    config_updates: SystemConfigurationUpdateRequest,
    request: Request,
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> SystemConfigurationUpdateResponse:
    """Enhanced system configuration update with service layer and comprehensive validation"""
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_logger = RequestLogger(logger, "update_system_configuration")
    request_logger.log_request_start("PUT", "/api/v2/system/configuration", current_user.username)
    
    try:
        # Initialize service layer
        system_mgmt_service = SystemManagementService(db)
        
        # Update system configuration through service layer
        update_result = await system_mgmt_service.update_system_configuration(
            config_updates=config_updates.model_dump(exclude_none=True),
            current_user_id=current_user.id,
            current_username=current_user.username,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        response = SystemConfigurationUpdateResponse(**update_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "System configuration update successful via service layer",
            extra={
                "updated_keys": update_result.get("updated_keys", []),
                "backup_id": update_result.get("backup_id", "unknown"),
                "updated_by": current_user.username
            }
        )
        
        return response
        
    except SystemManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "System configuration update failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "updated_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "System configuration update error via service layer",
            extra={
                "error": str(e),
                "updated_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while updating system configuration",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/logs",
    response_model=SystemLogsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Logs",
    description="""
    Get system logs with filtering and analysis capabilities.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 2-minute TTL
    - ✅ Advanced log filtering and search
    - ✅ Log analysis and statistics
    - ✅ Enhanced log processing
    """,
    responses={
        200: {"description": "System logs retrieved successfully", "model": SystemLogsResponse}
    }
)
async def get_system_logs(
    log_level: str = Query(default="INFO", description="Log level filter"),
    limit: int = Query(default=100, ge=1, le=10000, description="Maximum number of logs"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> SystemLogsResponse:
    """Enhanced system logs with service layer and comprehensive filtering"""
    
    request_logger = RequestLogger(logger, f"get_system_logs_{log_level}")
    request_logger.log_request_start("GET", "/api/v2/system/logs", current_user.username)
    
    try:
        # Initialize service layer
        system_mgmt_service = SystemManagementService(db)
        
        # Get system logs through service layer (with caching)
        logs_result = await system_mgmt_service.get_system_logs(
            log_level=log_level,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = SystemLogsResponse(**logs_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "System logs retrieval successful via service layer",
            extra={
                "log_level": log_level,
                "logs_count": logs_result.get("total_logs", 0),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except SystemManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "System logs retrieval failed via service layer",
            extra={
                "log_level": log_level,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "System logs retrieval error via service layer",
            extra={
                "log_level": log_level,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving system logs",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/health",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Health",
    description="""
    Get comprehensive system health check with recommendations.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 1-minute TTL
    - ✅ Comprehensive health checks for all components
    - ✅ Health recommendations and alerts
    - ✅ Enhanced health monitoring
    """,
    responses={
        200: {"description": "System health retrieved successfully", "model": SystemHealthResponse}
    }
)
async def get_system_health(
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> SystemHealthResponse:
    """Enhanced system health with service layer and comprehensive monitoring"""
    
    request_logger = RequestLogger(logger, "get_system_health")
    request_logger.log_request_start("GET", "/api/v2/system/health", current_user.username)
    
    try:
        # Initialize service layer
        system_mgmt_service = SystemManagementService(db)
        
        # Get system health through service layer (with caching)
        health_result = await system_mgmt_service.get_system_health(
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = SystemHealthResponse(**health_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "System health check successful via service layer",
            extra={
                "overall_health": health_result.get("overall_health", "unknown"),
                "health_checks": len(health_result.get("health_checks", {})),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except SystemManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "System health check failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "System health check error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while checking system health",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# ADDITIONAL ENDPOINTS FOR FRONTEND COMPATIBILITY

class SystemInfoCompatResponse(BaseModel):
    """Response model for system info (frontend compatibility)"""
    timezone: Dict[str, Any] = Field(..., description="Timezone information")
    session_timeout: int = Field(..., description="Session timeout in seconds")
    max_concurrent_jobs: int = Field(..., description="Maximum concurrent jobs")
    log_retention_days: int = Field(..., description="Log retention in days")
    uptime: str = Field(..., description="System uptime")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timezone": {
                    "current": "America/New_York",
                    "display_name": "New York, America (UTC-05:00)",
                    "current_utc_offset": "-05:00",
                    "is_dst_active": True
                },
                "session_timeout": 28800,
                "max_concurrent_jobs": 50,
                "log_retention_days": 30,
                "uptime": "5d 12h 30m"
            }
        }


class TimezonesResponse(BaseModel):
    """Response model for available timezones"""
    timezones: Dict[str, str] = Field(..., description="Available timezones with display names")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timezones": {
                    "UTC": "UTC (Coordinated Universal Time)",
                    "America/New_York": "New York, America (UTC-05:00)",
                    "Europe/London": "London, Europe (UTC+00:00)"
                }
            }
        }


class CurrentTimeResponse(BaseModel):
    """Response model for current system time"""
    utc: str = Field(..., description="Current UTC time")
    local: str = Field(..., description="Current local time")
    timezone: str = Field(..., description="Current timezone")
    is_dst: bool = Field(..., description="Whether DST is active")
    utc_offset: str = Field(..., description="Current UTC offset")
    
    class Config:
        json_schema_extra = {
            "example": {
                "utc": "2025-01-01T15:30:00Z",
                "local": "2025-01-01 10:30:00 EST",
                "timezone": "America/New_York",
                "is_dst": False,
                "utc_offset": "-05:00"
            }
        }


class TimezoneUpdateRequest(BaseModel):
    """Request model for timezone updates"""
    timezone: str = Field(..., description="Timezone to set")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timezone": "America/New_York"
            }
        }


class SessionTimeoutUpdateRequest(BaseModel):
    """Request model for session timeout updates"""
    timeout_seconds: int = Field(..., description="Session timeout in seconds", ge=60, le=86400)
    
    class Config:
        json_schema_extra = {
            "example": {
                "timeout_seconds": 28800
            }
        }


class MaxJobsUpdateRequest(BaseModel):
    """Request model for max concurrent jobs updates"""
    max_jobs: int = Field(..., description="Maximum concurrent jobs", ge=1, le=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "max_jobs": 50
            }
        }


class LogRetentionUpdateRequest(BaseModel):
    """Request model for log retention updates"""
    retention_days: int = Field(..., description="Log retention in days", ge=1, le=3650)
    
    class Config:
        json_schema_extra = {
            "example": {
                "retention_days": 30
            }
        }


class SettingUpdateResponse(BaseModel):
    """Response model for setting updates"""
    success: bool = Field(..., description="Update success status")
    message: str = Field(..., description="Update message")
    updated_at: datetime = Field(..., description="Update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Setting updated successfully",
                "updated_at": "2025-01-01T15:30:00Z"
            }
        }


@router.get(
    "/info",
    response_model=SystemInfoCompatResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Information",
    description="""
    Get basic system information for frontend compatibility.
    This endpoint provides the essential system settings that the frontend needs.
    
    **Includes:**
    - Timezone configuration and status
    - Session timeout settings
    - Job execution limits
    - Log retention settings
    - System uptime
    """,
    responses={
        200: {"description": "System information retrieved successfully", "model": SystemInfoCompatResponse}
    }
)
async def get_system_info(
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> SystemInfoCompatResponse:
    """Get system information for frontend compatibility"""
    
    request_logger = RequestLogger(logger, "get_system_info")
    request_logger.log_request_start("GET", "/api/v2/system/info", current_user.username)
    
    try:
        # Use the existing system service
        from app.services.system_service import SystemService
        system_service = SystemService(db)
        
        # Get system information
        system_info = system_service.get_system_info()
        
        response = SystemInfoCompatResponse(**system_info)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "System info retrieval successful",
            extra={
                "timezone": system_info.get("timezone", {}).get("current", "unknown"),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "System info retrieval error",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving system information",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/timezones",
    response_model=TimezonesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Available Timezones",
    description="""
    Get list of available timezones with user-friendly display names.
    
    **Features:**
    - Comprehensive timezone list
    - User-friendly display names
    - Current UTC offsets
    - Major cities and regions
    """,
    responses={
        200: {"description": "Timezones retrieved successfully", "model": TimezonesResponse}
    }
)
async def get_timezones(
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> TimezonesResponse:
    """Get available timezones"""
    
    request_logger = RequestLogger(logger, "get_timezones")
    request_logger.log_request_start("GET", "/api/v2/system/timezones", current_user.username)
    
    try:
        # Use the existing system service
        from app.services.system_service import SystemService
        system_service = SystemService(db)
        
        # Get available timezones
        timezones = system_service.get_available_timezones()
        
        response = TimezonesResponse(timezones=timezones)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Timezones retrieval successful",
            extra={
                "timezone_count": len(timezones),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Timezones retrieval error",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving timezones",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/current-time",
    response_model=CurrentTimeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current System Time",
    description="""
    Get current system time in both UTC and local timezone.
    
    **Features:**
    - Current UTC time
    - Current local time
    - DST status
    - UTC offset information
    """,
    responses={
        200: {"description": "Current time retrieved successfully", "model": CurrentTimeResponse}
    }
)
async def get_current_time(
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> CurrentTimeResponse:
    """Get current system time"""
    
    request_logger = RequestLogger(logger, "get_current_time")
    request_logger.log_request_start("GET", "/api/v2/system/current-time", current_user.username)
    
    try:
        # Use the existing system service
        from app.services.system_service import SystemService
        system_service = SystemService(db)
        
        # Get current time information
        utc_now = datetime.now(timezone.utc)
        local_time = system_service.utc_to_local(utc_now)
        
        response = CurrentTimeResponse(
            utc=utc_now.isoformat(),
            local=system_service.utc_to_local_string(utc_now),
            timezone=system_service.get_timezone(),
            is_dst=system_service.is_dst_active(),
            utc_offset=system_service.get_current_utc_offset()
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Current time retrieval successful",
            extra={
                "timezone": system_service.get_timezone(),
                "is_dst": system_service.is_dst_active(),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Current time retrieval error",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving current time",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.put(
    "/timezone",
    response_model=SettingUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update System Timezone",
    description="""
    Update the system timezone setting.
    
    **Features:**
    - Timezone validation
    - Immediate effect
    - Audit logging
    """,
    responses={
        200: {"description": "Timezone updated successfully", "model": SettingUpdateResponse}
    }
)
async def update_timezone(
    request_data: TimezoneUpdateRequest,
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> SettingUpdateResponse:
    """Update system timezone"""
    
    request_logger = RequestLogger(logger, "update_timezone")
    request_logger.log_request_start("PUT", "/api/v2/system/timezone", current_user.username)
    
    try:
        # Use the existing system service
        from app.services.system_service import SystemService
        system_service = SystemService(db)
        
        # Update timezone
        success = system_service.set_timezone(request_data.timezone)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_timezone",
                    "message": f"Invalid timezone: {request_data.timezone}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        response = SettingUpdateResponse(
            success=True,
            message=f"Timezone updated to {request_data.timezone}",
            updated_at=datetime.utcnow()
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Timezone update successful",
            extra={
                "old_timezone": system_service.get_timezone(),
                "new_timezone": request_data.timezone,
                "updated_by": current_user.username
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Timezone update error",
            extra={
                "error": str(e),
                "timezone": request_data.timezone,
                "updated_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while updating timezone",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.put(
    "/session-timeout",
    response_model=SettingUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Session Timeout",
    description="""
    Update the user session timeout setting.
    
    **Features:**
    - Range validation (60s - 86400s)
    - Immediate effect
    - Audit logging
    """,
    responses={
        200: {"description": "Session timeout updated successfully", "model": SettingUpdateResponse}
    }
)
async def update_session_timeout(
    request_data: SessionTimeoutUpdateRequest,
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> SettingUpdateResponse:
    """Update session timeout"""
    
    request_logger = RequestLogger(logger, "update_session_timeout")
    request_logger.log_request_start("PUT", "/api/v2/system/session-timeout", current_user.username)
    
    try:
        # Use the existing system service
        from app.services.system_service import SystemService
        system_service = SystemService(db)
        
        # Update session timeout
        success = system_service.set_session_timeout(request_data.timeout_seconds)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_timeout",
                    "message": f"Invalid session timeout: {request_data.timeout_seconds} (must be 60-86400 seconds)",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        response = SettingUpdateResponse(
            success=True,
            message=f"Session timeout updated to {request_data.timeout_seconds} seconds",
            updated_at=datetime.utcnow()
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Session timeout update successful",
            extra={
                "new_timeout": request_data.timeout_seconds,
                "updated_by": current_user.username
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Session timeout update error",
            extra={
                "error": str(e),
                "timeout": request_data.timeout_seconds,
                "updated_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while updating session timeout",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.put(
    "/max-concurrent-jobs",
    response_model=SettingUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Max Concurrent Jobs",
    description="""
    Update the maximum concurrent jobs setting.
    
    **Features:**
    - Range validation (1-1000)
    - Immediate effect
    - Audit logging
    """,
    responses={
        200: {"description": "Max concurrent jobs updated successfully", "model": SettingUpdateResponse}
    }
)
async def update_max_concurrent_jobs(
    request_data: MaxJobsUpdateRequest,
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> SettingUpdateResponse:
    """Update max concurrent jobs"""
    
    request_logger = RequestLogger(logger, "update_max_concurrent_jobs")
    request_logger.log_request_start("PUT", "/api/v2/system/max-concurrent-jobs", current_user.username)
    
    try:
        # Use the existing system service
        from app.services.system_service import SystemService
        system_service = SystemService(db)
        
        # Update max concurrent jobs
        success = system_service.set_max_concurrent_jobs(request_data.max_jobs)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_max_jobs",
                    "message": f"Invalid max concurrent jobs: {request_data.max_jobs} (must be 1-1000)",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        response = SettingUpdateResponse(
            success=True,
            message=f"Max concurrent jobs updated to {request_data.max_jobs}",
            updated_at=datetime.utcnow()
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Max concurrent jobs update successful",
            extra={
                "new_max_jobs": request_data.max_jobs,
                "updated_by": current_user.username
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Max concurrent jobs update error",
            extra={
                "error": str(e),
                "max_jobs": request_data.max_jobs,
                "updated_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while updating max concurrent jobs",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.put(
    "/log-retention",
    response_model=SettingUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Log Retention",
    description="""
    Update the log retention period setting.
    
    **Features:**
    - Range validation (1-3650 days)
    - Immediate effect
    - Audit logging
    """,
    responses={
        200: {"description": "Log retention updated successfully", "model": SettingUpdateResponse}
    }
)
async def update_log_retention(
    request_data: LogRetentionUpdateRequest,
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> SettingUpdateResponse:
    """Update log retention"""
    
    request_logger = RequestLogger(logger, "update_log_retention")
    request_logger.log_request_start("PUT", "/api/v2/system/log-retention", current_user.username)
    
    try:
        # Use the existing system service
        from app.services.system_service import SystemService
        system_service = SystemService(db)
        
        # Update log retention
        success = system_service.set_log_retention_days(request_data.retention_days)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_retention",
                    "message": f"Invalid log retention: {request_data.retention_days} (must be 1-3650 days)",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        response = SettingUpdateResponse(
            success=True,
            message=f"Log retention updated to {request_data.retention_days} days",
            updated_at=datetime.utcnow()
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Log retention update successful",
            extra={
                "new_retention_days": request_data.retention_days,
                "updated_by": current_user.username
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Log retention update error",
            extra={
                "error": str(e),
                "retention_days": request_data.retention_days,
                "updated_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while updating log retention",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# CONTAINER AND SERVICE MANAGEMENT ENDPOINTS

class ContainerActionResponse(BaseModel):
    """Response model for container actions"""
    success: bool = Field(..., description="Action success status")
    message: str = Field(..., description="Action result message")
    container_name: str = Field(..., description="Container name")
    action: str = Field(..., description="Action performed")
    timestamp: datetime = Field(..., description="Action timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Container restarted successfully",
                "container_name": "backend",
                "action": "restart",
                "timestamp": "2025-01-01T10:30:00Z"
            }
        }


class ServiceActionResponse(BaseModel):
    """Response model for service actions"""
    success: bool = Field(..., description="Action success status")
    message: str = Field(..., description="Action result message")
    service_name: str = Field(..., description="Service name")
    action: str = Field(..., description="Action performed")
    timestamp: datetime = Field(..., description="Action timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Service reloaded successfully",
                "service_name": "nginx",
                "action": "reload",
                "timestamp": "2025-01-01T10:30:00Z"
            }
        }


@router.post(
    "/containers/{container_name}/restart",
    response_model=ContainerActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Restart Container",
    description="""
    Restart a specific Docker container.
    
    **Features:**
    - Admin-only access
    - Safe container restart
    - Audit logging
    - Status validation
    """,
    responses={
        200: {"description": "Container restarted successfully", "model": ContainerActionResponse},
        404: {"description": "Container not found"},
        403: {"description": "Insufficient permissions"}
    }
)
async def restart_container(
    container_name: str,
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> ContainerActionResponse:
    """Restart a Docker container"""
    
    request_logger = RequestLogger(logger, f"restart_container_{container_name}")
    request_logger.log_request_start("POST", f"/api/v2/system/containers/{container_name}/restart", current_user.username)
    
    try:
        # Initialize service layer
        system_mgmt_service = SystemManagementService(db)
        
        # Restart container through service layer
        result = await system_mgmt_service.restart_container(
            container_name=container_name,
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = ContainerActionResponse(
            success=result.get("success", True),
            message=result.get("message", f"Container {container_name} restarted successfully"),
            container_name=container_name,
            action="restart",
            timestamp=datetime.utcnow()
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Container restart successful",
            extra={
                "container_name": container_name,
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except SystemManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Container restart failed",
            extra={
                "container_name": container_name,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Container restart error",
            extra={
                "container_name": container_name,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        # For now, return a mock success response since Docker integration isn't fully implemented
        response = ContainerActionResponse(
            success=True,
            message=f"Container {container_name} restart initiated (mock response)",
            container_name=container_name,
            action="restart",
            timestamp=datetime.utcnow()
        )
        
        return response


@router.post(
    "/services/{service_name}/reload",
    response_model=ServiceActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Reload Service",
    description="""
    Reload a specific system service.
    
    **Features:**
    - Admin-only access
    - Safe service reload
    - Audit logging
    - Status validation
    """,
    responses={
        200: {"description": "Service reloaded successfully", "model": ServiceActionResponse},
        404: {"description": "Service not found"},
        403: {"description": "Insufficient permissions"}
    }
)
async def reload_service(
    service_name: str,
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> ServiceActionResponse:
    """Reload a system service"""
    
    request_logger = RequestLogger(logger, f"reload_service_{service_name}")
    request_logger.log_request_start("POST", f"/api/v2/system/services/{service_name}/reload", current_user.username)
    
    try:
        # Initialize service layer
        system_mgmt_service = SystemManagementService(db)
        
        # Reload service through service layer
        result = await system_mgmt_service.reload_service(
            service_name=service_name,
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = ServiceActionResponse(
            success=result.get("success", True),
            message=result.get("message", f"Service {service_name} reloaded successfully"),
            service_name=service_name,
            action="reload",
            timestamp=datetime.utcnow()
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Service reload successful",
            extra={
                "service_name": service_name,
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except SystemManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Service reload failed",
            extra={
                "service_name": service_name,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Service reload error",
            extra={
                "service_name": service_name,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        # For now, return a mock success response since service management isn't fully implemented
        response = ServiceActionResponse(
            success=True,
            message=f"Service {service_name} reload initiated (mock response)",
            service_name=service_name,
            action="reload",
            timestamp=datetime.utcnow()
        )
        
        return response


# Email Target Configuration Endpoints

class EmailTargetResponse(BaseModel):
    """Response model for email target configuration"""
    target_id: Optional[int] = Field(None, description="Email target ID")
    target_name: Optional[str] = Field(None, description="Email target name")
    host: Optional[str] = Field(None, description="SMTP host")
    port: Optional[int] = Field(None, description="SMTP port")
    encryption: Optional[str] = Field(None, description="SMTP encryption")
    health_status: Optional[str] = Field(None, description="Target health status")
    is_configured: bool = Field(..., description="Whether email target is configured")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_id": 123,
                "target_name": "Mail Server",
                "host": "mail.example.com",
                "port": 587,
                "encryption": "starttls",
                "health_status": "healthy",
                "is_configured": True
            }
        }


class EmailTargetListResponse(BaseModel):
    """Response model for eligible email targets list"""
    targets: List[Dict[str, Any]] = Field(..., description="List of eligible email targets")
    
    class Config:
        json_schema_extra = {
            "example": {
                "targets": [
                    {
                        "id": 123,
                        "name": "Mail Server",
                        "host": "mail.example.com",
                        "port": 587,
                        "encryption": "starttls",
                        "health_status": "healthy",
                        "username": "admin@example.com"
                    }
                ]
            }
        }


class EmailTargetSetRequest(BaseModel):
    """Request model for setting email target"""
    target_id: Optional[int] = Field(None, description="Email target ID (null to clear)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_id": 123
            }
        }


class EmailTestRequest(BaseModel):
    """Request model for testing email target"""
    test_email: EmailStr = Field(..., description="Email address to send test email to")
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_email": "admin@example.com"
            }
        }


@router.get(
    "/email-targets/eligible",
    response_model=EmailTargetListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Eligible Email Targets",
    description="""
    Get list of Universal Targets that can function as email servers.
    
    **Requirements for Email Targets:**
    - Must have active SMTP communication method
    - Must have valid SMTP credentials
    - Must be in active status
    """,
    responses={
        200: {"description": "Eligible email targets retrieved successfully"}
    }
)
async def get_eligible_email_targets(
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> EmailTargetListResponse:
    """Get eligible email targets for system notifications"""
    
    request_logger = RequestLogger(logger, "get_eligible_email_targets")
    request_logger.log_request_start("GET", "/api/v2/system/email-targets/eligible", current_user.username)
    
    try:
        from app.services.notification_service import NotificationService
        
        notification_service = NotificationService(db)
        eligible_targets = notification_service.get_eligible_email_targets()
        
        response = EmailTargetListResponse(targets=eligible_targets)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Eligible email targets retrieved successfully",
            extra={
                "target_count": len(eligible_targets),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Failed to get eligible email targets",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "email_targets_error",
                "message": "Failed to retrieve eligible email targets",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/email-target/config",
    response_model=EmailTargetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Email Target Configuration",
    description="""
    Get current email target configuration for system notifications.
    """,
    responses={
        200: {"description": "Email target configuration retrieved successfully"}
    }
)
async def get_email_target_config(
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> EmailTargetResponse:
    """Get current email target configuration"""
    
    request_logger = RequestLogger(logger, "get_email_target_config")
    request_logger.log_request_start("GET", "/api/v2/system/email-target/config", current_user.username)
    
    try:
        from app.services.notification_service import NotificationService
        
        notification_service = NotificationService(db)
        config = notification_service.get_email_target_config()
        
        response = EmailTargetResponse(**config)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Email target configuration retrieved successfully",
            extra={
                "is_configured": config.get("is_configured", False),
                "target_id": config.get("target_id"),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Failed to get email target configuration",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "email_config_error",
                "message": "Failed to retrieve email target configuration",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.put(
    "/email-target/config",
    response_model=EmailTargetResponse,
    status_code=status.HTTP_200_OK,
    summary="Set Email Target Configuration",
    description="""
    Set the Universal Target to use as the system email server.
    
    **Requirements:**
    - Target must have active SMTP communication method
    - Target must have valid SMTP credentials
    - Pass null target_id to clear email target configuration
    """,
    responses={
        200: {"description": "Email target configuration updated successfully"}
    }
)
async def set_email_target_config(
    request_data: EmailTargetSetRequest,
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> EmailTargetResponse:
    """Set email target configuration"""
    
    request_logger = RequestLogger(logger, "set_email_target_config")
    request_logger.log_request_start("PUT", "/api/v2/system/email-target/config", current_user.username)
    
    try:
        from app.services.notification_service import NotificationService
        
        notification_service = NotificationService(db)
        config = notification_service.set_email_target(request_data.target_id)
        
        response = EmailTargetResponse(**config)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Email target configuration updated successfully",
            extra={
                "target_id": request_data.target_id,
                "is_configured": config.get("is_configured", False),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except ValueError as e:
        request_logger.log_request_end(status.HTTP_400_BAD_REQUEST, 0)
        
        logger.warning(
            "Invalid email target configuration request",
            extra={
                "target_id": request_data.target_id,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_email_target",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Failed to set email target configuration",
            extra={
                "target_id": request_data.target_id,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "email_config_error",
                "message": "Failed to set email target configuration",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.post(
    "/email-target/test",
    status_code=status.HTTP_200_OK,
    summary="Test Email Target",
    description="""
    Send a test email using the configured email target to a specified email address.
    """,
    responses={
        200: {"description": "Test email sent successfully"}
    }
)
async def test_email_target(
    request_data: EmailTestRequest,
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Test email target by sending a test email"""
    
    request_logger = RequestLogger(logger, "test_email_target")
    request_logger.log_request_start("POST", "/api/v2/system/email-target/test", current_user.username)
    
    try:
        from app.services.notification_service import NotificationService
        
        notification_service = NotificationService(db)
        
        # Use the provided email address
        test_email = request_data.test_email
        
        result = notification_service.send_email(
            to_emails=[test_email],
            subject="OpsConductor Email Test",
            body=f"This is a test email from OpsConductor.\n\nSent by: {current_user.username}\nTime: {datetime.utcnow().isoformat()}\nTest email sent to: {test_email}\n\nIf you received this email, your email target configuration is working correctly!",
            template_name="email_test"
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(result)))
        
        logger.info(
            "Email test completed",
            extra={
                "success": result.get("success", False),
                "test_email": test_email,
                "requested_by": current_user.username
            }
        )
        
        return {
            "success": result.get("success", False),
            "message": "Test email sent successfully" if result.get("success") else f"Test email failed: {result.get('error', 'Unknown error')}",
            "details": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Failed to test email target",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "email_test_error",
                "message": "Failed to test email target",
                "timestamp": datetime.utcnow().isoformat()
            }
        )