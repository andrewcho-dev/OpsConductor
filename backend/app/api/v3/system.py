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
        db_health = await health_service.check_database_health()
        
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
        app_health = await health_service.check_application_health()
        
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
        sys_health = await health_service.check_system_health()
        
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