"""
Health API v2 Enhanced - Phases 1 & 2
Complete transformation with service layer, caching, and comprehensive models

PHASE 1 & 2 IMPROVEMENTS:
- ✅ Comprehensive Pydantic models with validation
- ✅ Service layer integration with business logic separation
- ✅ Redis caching for improved performance
- ✅ Structured JSON logging with contextual information
- ✅ Enhanced error handling with detailed responses
- ✅ Advanced health monitoring and diagnostics
- ✅ Multi-component health aggregation
- ✅ Real-time health alerting and recommendations
- ✅ Comprehensive health lifecycle management
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# Import service layer
from app.services.health_management_service import HealthManagementService, HealthManagementError
from app.database.database import get_db
from app.core.security import verify_token
from app.core.logging import get_structured_logger, RequestLogger

# Configure structured logger
logger = get_structured_logger(__name__)

# Security scheme
security = HTTPBearer()

# PHASE 1: COMPREHENSIVE PYDANTIC MODELS

class HealthCheckResult(BaseModel):
    """Enhanced model for individual health check results"""
    healthy: bool = Field(..., description="Health check status")
    status: str = Field(..., description="Health check status description")
    response_time: Optional[float] = Field(None, description="Response time in milliseconds")
    last_check: datetime = Field(..., description="Last check timestamp")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health check details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "healthy": True,
                "status": "connected",
                "response_time": 5.2,
                "last_check": "2025-01-01T10:30:00Z",
                "error": None,
                "details": {
                    "connection_pool": "healthy",
                    "active_connections": 10
                }
            }
        }


class SystemResourceInfo(BaseModel):
    """Enhanced model for system resource information"""
    usage_percent: float = Field(..., description="Resource usage percentage")
    total: Optional[int] = Field(None, description="Total resource amount")
    used: Optional[int] = Field(None, description="Used resource amount")
    available: Optional[int] = Field(None, description="Available resource amount")
    healthy: bool = Field(..., description="Resource health status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "usage_percent": 65.5,
                "total": 16777216000,
                "used": 10995116032,
                "available": 5782099968,
                "healthy": True
            }
        }


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
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-01-01T10:30:00Z",
                "health_checks": {
                    "database": {
                        "healthy": True,
                        "status": "connected",
                        "response_time": 5.2,
                        "last_check": "2025-01-01T10:30:00Z"
                    },
                    "redis": {
                        "healthy": True,
                        "status": "connected",
                        "response_time": 1.1,
                        "last_check": "2025-01-01T10:30:00Z"
                    }
                },
                "health_metrics": {
                    "total_checks": 5,
                    "passed_checks": 5,
                    "failed_checks": 0
                },
                "recommendations": [],
                "uptime": "5d 12h 30m",
                "version": "2.0.0",
                "environment": "production",
                "alerts": [],
                "metadata": {
                    "source": "health_monitoring",
                    "version": "2.0"
                }
            }
        }


class SystemHealthResponse(BaseModel):
    """Enhanced response model for system health"""
    status: str = Field(..., description="System health status")
    cpu: Dict[str, Any] = Field(..., description="CPU information")
    memory: SystemResourceInfo = Field(..., description="Memory information")
    disk: SystemResourceInfo = Field(..., description="Disk information")
    network: Dict[str, Any] = Field(..., description="Network statistics")
    processes: int = Field(..., description="Number of running processes")
    boot_time: datetime = Field(..., description="System boot time")
    last_check: datetime = Field(..., description="Last check timestamp")
    thresholds: Dict[str, int] = Field(..., description="Health thresholds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="System health metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "cpu": {
                    "usage_percent": 45.8,
                    "count": 8,
                    "load_avg": [1.2, 1.5, 1.8]
                },
                "memory": {
                    "usage_percent": 65.5,
                    "total": 16777216000,
                    "used": 10995116032,
                    "available": 5782099968,
                    "healthy": True
                },
                "disk": {
                    "usage_percent": 45.0,
                    "total": 1000000000000,
                    "used": 450000000000,
                    "available": 550000000000,
                    "healthy": True
                },
                "network": {
                    "bytes_sent": 1048576000,
                    "bytes_recv": 2097152000,
                    "packets_sent": 1000000,
                    "packets_recv": 1500000
                },
                "processes": 150,
                "boot_time": "2025-01-01T00:00:00Z",
                "last_check": "2025-01-01T10:30:00Z",
                "thresholds": {
                    "cpu_warning": 80,
                    "cpu_critical": 95,
                    "memory_warning": 85,
                    "memory_critical": 95
                },
                "metadata": {
                    "source": "system_monitoring",
                    "version": "2.0"
                }
            }
        }


class DatabaseHealthResponse(BaseModel):
    """Enhanced response model for database health"""
    status: str = Field(..., description="Database health status")
    connection: HealthCheckResult = Field(..., description="Database connection health")
    statistics: Dict[str, Any] = Field(..., description="Database statistics")
    connection_pool: Dict[str, Any] = Field(..., description="Connection pool information")
    performance: Dict[str, Any] = Field(..., description="Database performance metrics")
    last_check: datetime = Field(..., description="Last check timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Database health metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "connection": {
                    "healthy": True,
                    "status": "connected",
                    "response_time": 5.2,
                    "last_check": "2025-01-01T10:30:00Z"
                },
                "statistics": {
                    "active_connections": 10,
                    "idle_connections": 15,
                    "total_queries": 50000
                },
                "connection_pool": {
                    "pool_size": 20,
                    "available": 15,
                    "in_use": 5
                },
                "performance": {
                    "query_response_time": 5.2,
                    "active_connections": 10,
                    "idle_connections": 15
                },
                "last_check": "2025-01-01T10:30:00Z",
                "metadata": {
                    "source": "database_monitoring",
                    "version": "2.0"
                }
            }
        }


class ApplicationHealthResponse(BaseModel):
    """Enhanced response model for application health"""
    status: str = Field(..., description="Application health status")
    components: Dict[str, Any] = Field(..., description="Application components health")
    metrics: Dict[str, Any] = Field(..., description="Application metrics")
    services: Dict[str, Any] = Field(..., description="Service status")
    performance: Dict[str, Any] = Field(..., description="Application performance metrics")
    last_check: datetime = Field(..., description="Last check timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Application health metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "components": {
                    "healthy": True,
                    "api_server": {"healthy": True, "status": "running"},
                    "task_queue": {"healthy": True, "status": "running"},
                    "scheduler": {"healthy": True, "status": "running"}
                },
                "metrics": {
                    "avg_response_time": 125.5,
                    "requests_per_second": 50.0,
                    "error_rate": 0.02
                },
                "services": {
                    "web_server": "running",
                    "background_tasks": "running",
                    "scheduler": "running"
                },
                "performance": {
                    "response_time": 125.5,
                    "throughput": 50.0,
                    "error_rate": 0.02
                },
                "last_check": "2025-01-01T10:30:00Z",
                "metadata": {
                    "source": "application_monitoring",
                    "version": "2.0"
                }
            }
        }


class HealthSummaryResponse(BaseModel):
    """Enhanced response model for health summary"""
    overall_status: str = Field(..., description="Overall health status")
    key_metrics: Dict[str, Any] = Field(..., description="Key health metrics")
    health_trends: Dict[str, Any] = Field(..., description="Health trends")
    critical_alerts: List[Dict[str, Any]] = Field(..., description="Critical health alerts")
    component_status: Dict[str, bool] = Field(..., description="Component health status")
    uptime: str = Field(..., description="System uptime")
    last_check: datetime = Field(..., description="Last check timestamp")
    next_check: datetime = Field(..., description="Next scheduled check")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Health summary metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_status": "healthy",
                "key_metrics": {
                    "cpu_usage": 45.8,
                    "memory_usage": 65.5,
                    "disk_usage": 45.0,
                    "response_time": 125.5
                },
                "health_trends": {
                    "cpu_trend": "stable",
                    "memory_trend": "increasing",
                    "response_time_trend": "improving"
                },
                "critical_alerts": [],
                "component_status": {
                    "database": True,
                    "redis": True,
                    "system": True,
                    "application": True
                },
                "uptime": "5d 12h 30m",
                "last_check": "2025-01-01T10:30:00Z",
                "next_check": "2025-01-01T10:31:00Z",
                "metadata": {
                    "source": "health_summary",
                    "version": "2.0"
                }
            }
        }


class HealthErrorResponse(BaseModel):
    """Enhanced error response model for health management errors"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    health_component: Optional[str] = Field(None, description="Related health component")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "health_check_error",
                "message": "Failed to perform health check due to service unavailability",
                "details": {
                    "component": "database",
                    "retry_after": 60
                },
                "timestamp": "2025-01-01T10:30:00Z",
                "health_component": "database"
            }
        }


# PHASE 1 & 2: ENHANCED ROUTER WITH SERVICE LAYER INTEGRATION

router = APIRouter(
    prefix="/api/v2/health",
    tags=["Health & Monitoring Enhanced v2"],
    responses={
        401: {"model": HealthErrorResponse, "description": "Authentication required"},
        403: {"model": HealthErrorResponse, "description": "Insufficient permissions"},
        404: {"model": HealthErrorResponse, "description": "Resource not found"},
        422: {"model": HealthErrorResponse, "description": "Validation error"},
        500: {"model": HealthErrorResponse, "description": "Internal server error"}
    }
)


# PHASE 2: ENHANCED DEPENDENCY FUNCTIONS

def get_current_user_optional(credentials = Depends(security), 
                             db: Session = Depends(get_db)):
    """Get current authenticated user (optional for health endpoints)."""
    try:
        if not credentials:
            return None
            
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        from app.services.user_service import UserService
        user = UserService.get_user_by_id(db, user_id)
        
        return user
        
    except Exception:
        return None


def get_current_user(credentials = Depends(security), 
                    db: Session = Depends(get_db)):
    """Get current authenticated user with enhanced error handling."""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            logger.warning("Invalid token in health management request")
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


# PHASE 1 & 2: ENHANCED ENDPOINTS WITH SERVICE LAYER

@router.get(
    "/",
    response_model=OverallHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Overall Health Status",
    description="""
    Get comprehensive overall health status with all component checks.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 30-second TTL
    - ✅ Comprehensive health checks for all components
    - ✅ Health recommendations and alerts
    - ✅ Enhanced health monitoring
    
    **Public Endpoint:**
    - No authentication required for basic health checks
    - Enhanced information available for authenticated users
    """,
    responses={
        200: {"description": "Overall health status retrieved successfully", "model": OverallHealthResponse}
    }
)
async def get_overall_health(
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> OverallHealthResponse:
    """Enhanced overall health with service layer and comprehensive monitoring"""
    
    username = current_user.username if current_user else "anonymous"
    user_id = current_user.id if current_user else None
    
    request_logger = RequestLogger(logger, "get_overall_health")
    request_logger.log_request_start("GET", "/api/v2/health/", username)
    
    try:
        # Initialize service layer
        health_mgmt_service = HealthManagementService(db)
        
        # Get overall health through service layer (with caching)
        health_result = await health_mgmt_service.get_overall_health(
            current_user_id=user_id,
            current_username=username
        )
        
        response = OverallHealthResponse(**health_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Overall health check successful via service layer",
            extra={
                "overall_status": health_result.get("status", "unknown"),
                "failed_checks": len([k for k, v in health_result.get("health_checks", {}).items() if not v.get("healthy", True)]),
                "requested_by": username
            }
        )
        
        return response
        
    except HealthManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Overall health check failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": username
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
            "Overall health check error via service layer",
            extra={
                "error": str(e),
                "requested_by": username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while checking overall health",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/system",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Health",
    description="""
    Get detailed system health with resource monitoring.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 1-minute TTL
    - ✅ Detailed system resource monitoring
    - ✅ Resource usage thresholds and alerts
    - ✅ Enhanced system diagnostics
    """,
    responses={
        200: {"description": "System health retrieved successfully", "model": SystemHealthResponse}
    }
)
async def get_system_health(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SystemHealthResponse:
    """Enhanced system health with service layer and detailed resource monitoring"""
    
    request_logger = RequestLogger(logger, "get_system_health")
    request_logger.log_request_start("GET", "/api/v2/health/system", current_user.username)
    
    try:
        # Initialize service layer
        health_mgmt_service = HealthManagementService(db)
        
        # Get system health through service layer (with caching)
        health_result = await health_mgmt_service.get_system_health(
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = SystemHealthResponse(**health_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "System health check successful via service layer",
            extra={
                "system_status": health_result.get("status", "unknown"),
                "cpu_usage": health_result.get("cpu", {}).get("usage_percent", 0),
                "memory_usage": health_result.get("memory", {}).get("usage_percent", 0),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except HealthManagementError as e:
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


@router.get(
    "/database",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Database Health",
    description="""
    Get detailed database health with connection and performance monitoring.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 1-minute TTL
    - ✅ Database connection and performance monitoring
    - ✅ Connection pool information
    - ✅ Enhanced database diagnostics
    """,
    responses={
        200: {"description": "Database health retrieved successfully", "model": DatabaseHealthResponse}
    }
)
async def get_database_health(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DatabaseHealthResponse:
    """Enhanced database health with service layer and comprehensive monitoring"""
    
    request_logger = RequestLogger(logger, "get_database_health")
    request_logger.log_request_start("GET", "/api/v2/health/database", current_user.username)
    
    try:
        # Initialize service layer
        health_mgmt_service = HealthManagementService(db)
        
        # Get database health through service layer (with caching)
        health_result = await health_mgmt_service.get_database_health(
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = DatabaseHealthResponse(**health_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Database health check successful via service layer",
            extra={
                "database_status": health_result.get("status", "unknown"),
                "response_time": health_result.get("connection", {}).get("response_time", 0),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except HealthManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Database health check failed via service layer",
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
            "Database health check error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while checking database health",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/application",
    response_model=ApplicationHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Application Health",
    description="""
    Get detailed application health with component and service monitoring.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 1-minute TTL
    - ✅ Application component monitoring
    - ✅ Service status and performance metrics
    - ✅ Enhanced application diagnostics
    """,
    responses={
        200: {"description": "Application health retrieved successfully", "model": ApplicationHealthResponse}
    }
)
async def get_application_health(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ApplicationHealthResponse:
    """Enhanced application health with service layer and comprehensive monitoring"""
    
    request_logger = RequestLogger(logger, "get_application_health")
    request_logger.log_request_start("GET", "/api/v2/health/application", current_user.username)
    
    try:
        # Initialize service layer
        health_mgmt_service = HealthManagementService(db)
        
        # Get application health through service layer (with caching)
        health_result = await health_mgmt_service.get_application_health(
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = ApplicationHealthResponse(**health_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Application health check successful via service layer",
            extra={
                "application_status": health_result.get("status", "unknown"),
                "response_time": health_result.get("metrics", {}).get("avg_response_time", 0),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except HealthManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Application health check failed via service layer",
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
            "Application health check error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while checking application health",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/summary",
    response_model=HealthSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Health Summary",
    description="""
    Get consolidated health summary with key metrics and trends.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 30-second TTL
    - ✅ Consolidated health overview
    - ✅ Key metrics and trends
    - ✅ Critical alerts and recommendations
    """,
    responses={
        200: {"description": "Health summary retrieved successfully", "model": HealthSummaryResponse}
    }
)
async def get_health_summary(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> HealthSummaryResponse:
    """Enhanced health summary with service layer and consolidated monitoring"""
    
    request_logger = RequestLogger(logger, "get_health_summary")
    request_logger.log_request_start("GET", "/api/v2/health/summary", current_user.username)
    
    try:
        # Initialize service layer
        health_mgmt_service = HealthManagementService(db)
        
        # Get health summary through service layer (with caching)
        summary_result = await health_mgmt_service.get_health_summary(
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = HealthSummaryResponse(**summary_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Health summary retrieval successful via service layer",
            extra={
                "overall_status": summary_result.get("overall_status", "unknown"),
                "critical_alerts": len(summary_result.get("critical_alerts", [])),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except HealthManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Health summary retrieval failed via service layer",
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
            "Health summary retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving health summary",
                "timestamp": datetime.utcnow().isoformat()
            }
        )