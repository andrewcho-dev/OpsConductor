"""
Targets API v3 - Consolidated from routers/universal_targets.py and missing v1 endpoints
All target management endpoints in v3 structure
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.universal_target_service import UniversalTargetService
from app.services.health_monitoring_service import HealthMonitoringService
from app.services.target_management_service import TargetManagementService
from app.utils.target_utils import getTargetIpAddress
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
from app.core.auth_dependencies import get_current_user
from app.schemas.target_schemas import (
    TargetCreate, 
    TargetUpdate, 
    TargetComprehensiveUpdate,
    TargetResponse, 
    TargetSummary, 
    ConnectionTestResult,
    ErrorResponse,
    CommunicationMethodCreate,
    CommunicationMethodUpdate,
    CommunicationMethodResponse
)
from app.models.universal_target_models import UniversalTarget

router = APIRouter(prefix=f"{os.getenv(\'API_BASE_URL\', \'/api/v3\')}/targets", tags=["Targets v3"])

logger = logging.getLogger(__name__)


def get_target_service(db: Session = Depends(get_db)) -> UniversalTargetService:
    """Dependency to get target service instance."""
    return UniversalTargetService(db)


# BASIC CRUD OPERATIONS

@router.get("/", response_model=List[TargetSummary])
async def list_targets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    target_type: str = Query(None),
    status: str = Query(None),
    tags: str = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """Get all targets with optional filtering and pagination."""
    try:
        # Parse tags if provided
        tag_list = tags.split(',') if tags else []
        
        summaries = target_service.get_targets_summary(
            skip=skip,
            limit=limit,
            search=search,
            target_type=target_type,
            status=status,
            tags=tag_list
        )
        return summaries
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve targets: {str(e)}"
        )


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """Get a specific target by ID with full details."""
    target = target_service.get_target_by_id(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target with ID {target_id} not found"
        )
    return target


@router.post("/", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetCreate,
    request: Request,
    target_service: UniversalTargetService = Depends(get_target_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new target with communication method and credentials."""
    try:
        # Validate credential requirements based on method type
        if target_data.method_type in ['ssh', 'winrm', 'telnet']:
            if target_data.method_type == 'ssh' and target_data.ssh_key:
                if not target_data.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username is required for SSH key authentication"
                    )
            elif target_data.password:
                if not target_data.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username is required for password authentication"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either password or SSH key must be provided for authentication"
                )
        
        target = target_service.create_target(
            name=target_data.name,
            os_type=target_data.os_type,
            ip_address=target_data.ip_address,
            method_type=target_data.method_type,
            username=target_data.username,
            password=target_data.password,
            ssh_key=target_data.ssh_key,
            ssh_passphrase=target_data.ssh_passphrase,
            description=target_data.description,
            environment=target_data.environment,
            location=target_data.location,
            data_center=target_data.data_center,
            region=target_data.region
        )
        
        # Log target creation audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.TARGET_CREATED,
            user_id=current_user["id"],
            resource_type="target",
            resource_id=str(target.id),
            action="create_target",
            details={
                "target_name": target.name,
                "target_ip": target.ip_address,
                "method_type": target_data.method_type,
                "created_by": current_user.get("username", "unknown")
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return target
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create target: {str(e)}"
        )


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    target_data: TargetUpdate,
    request: Request,
    target_service: UniversalTargetService = Depends(get_target_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a target."""
    try:
        target = target_service.update_target(target_id, target_data)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target with ID {target_id} not found"
            )
        
        # Log target update audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.TARGET_UPDATED,
            user_id=current_user["id"],
            resource_type="target",
            resource_id=str(target.id),
            action="update_target",
            details={
                "target_name": target.name,
                "target_ip": target.ip_address,
                "updated_by": current_user.get("username", "unknown"),
                "changes": target_data.dict(exclude_unset=True)
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return target
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update target: {str(e)}"
        )


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: int,
    request: Request,
    target_service: UniversalTargetService = Depends(get_target_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a target."""
    try:
        # Get target for audit logging before deletion
        target = target_service.get_target_by_id(target_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target with ID {target_id} not found"
            )
        
        success = target_service.delete_target(target_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete target"
            )
        
        # Log target deletion audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.TARGET_DELETED,
            user_id=current_user["id"],
            resource_type="target",
            resource_id=str(target.id),
            action="delete_target",
            details={
                "target_name": target.name,
                "target_ip": target.ip_address,
                "deleted_by": current_user.get("username", "unknown")
            },
            severity=AuditSeverity.HIGH,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete target: {str(e)}"
        )


# CONNECTION TESTING

@router.post("/{target_id}/test", response_model=ConnectionTestResult)
async def test_target_connection(
    target_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """Test connection to a specific target."""
    try:
        result = target_service.test_target_connection(target_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test target connection: {str(e)}"
        )


# BULK OPERATIONS (from v1)

@router.post("/bulk/test")
async def bulk_test_connections(
    target_ids: List[int],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test connections to multiple targets."""
    try:
        target_service = UniversalTargetService(db)
        results = []
        
        for target_id in target_ids:
            try:
                result = target_service.test_target_connection(target_id)
                results.append({
                    "target_id": target_id,
                    "success": result.success,
                    "message": result.message,
                    "response_time": result.response_time
                })
            except Exception as e:
                results.append({
                    "target_id": target_id,
                    "success": False,
                    "message": str(e),
                    "response_time": None
                })
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk connection tests: {str(e)}"
        )


@router.post("/bulk/update")
async def bulk_update_targets(
    update_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update multiple targets with the same data."""
    try:
        target_ids = update_data.get("target_ids", [])
        update_fields = update_data.get("update_data", {})
        
        if not target_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="target_ids is required"
            )
        
        target_service = UniversalTargetService(db)
        results = []
        
        for target_id in target_ids:
            try:
                # Create TargetUpdate object from update_fields
                target_update = TargetUpdate(**update_fields)
                target = target_service.update_target(target_id, target_update)
                results.append({
                    "target_id": target_id,
                    "success": True,
                    "message": "Target updated successfully"
                })
            except Exception as e:
                results.append({
                    "target_id": target_id,
                    "success": False,
                    "message": str(e)
                })
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk update: {str(e)}"
        )


# STATISTICS (from v1)

@router.get("/statistics/overview")
async def get_target_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get target statistics overview."""
    try:
        target_service = UniversalTargetService(db)
        
        # Get all targets for statistics
        all_targets = target_service.get_all_targets()
        
        # Calculate statistics
        total_targets = len(all_targets)
        active_targets = len([t for t in all_targets if t.status == "active"])
        inactive_targets = len([t for t in all_targets if t.status == "inactive"])
        
        # Group by OS type
        os_stats = {}
        for target in all_targets:
            os_type = target.os_type or "unknown"
            os_stats[os_type] = os_stats.get(os_type, 0) + 1
        
        # Group by method type
        method_stats = {}
        for target in all_targets:
            # Get primary communication method
            if target.communication_methods:
                method_type = target.communication_methods[0].method_type
                method_stats[method_type] = method_stats.get(method_type, 0) + 1
        
        return {
            "total_targets": total_targets,
            "active_targets": active_targets,
            "inactive_targets": inactive_targets,
            "os_distribution": os_stats,
            "method_distribution": method_stats,
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get target statistics: {str(e)}"
        )


# HEALTH MONITORING (from v1)

@router.get("/health/check")
async def get_targets_needing_health_check(
    minutes_since_last_check: int = Query(30, ge=1),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get targets that need health checks."""
    try:
        health_service = HealthMonitoringService(db)
        targets = health_service.get_targets_needing_health_check(minutes_since_last_check)
        
        return {
            "targets": [
                {
                    "id": target.id,
                    "name": target.name,
                    "ip_address": target.ip_address,
                    "last_health_check": target.last_health_check,
                    "health_status": target.health_status
                }
                for target in targets
            ],
            "count": len(targets)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get targets needing health check: {str(e)}"
        )


@router.post("/health/perform")
async def perform_health_checks(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform health checks on targets that need them."""
    try:
        health_service = HealthMonitoringService(db)
        results = health_service.perform_health_checks()
        
        return {
            "message": "Health checks initiated",
            "targets_checked": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform health checks: {str(e)}"
        )


@router.post("/health-check-batch")
async def health_check_batch(
    target_ids: List[int],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform health checks on specific targets."""
    try:
        health_service = HealthMonitoringService(db)
        results = []
        
        for target_id in target_ids:
            try:
                result = health_service.check_target_health(target_id)
                results.append({
                    "target_id": target_id,
                    "success": True,
                    "health_status": result.get("status", "unknown"),
                    "response_time": result.get("response_time"),
                    "message": result.get("message", "Health check completed")
                })
            except Exception as e:
                results.append({
                    "target_id": target_id,
                    "success": False,
                    "health_status": "error",
                    "response_time": None,
                    "message": str(e)
                })
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform batch health checks: {str(e)}"
        )


# TARGET TYPES (from v1)

@router.get("/types")
async def get_target_types(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get available target types and communication methods."""
    try:
        target_types = [
            {
                "name": "Linux Server",
                "os_type": "linux",
                "supported_methods": ["ssh", "snmp", "rest_api"]
            },
            {
                "name": "Windows Server",
                "os_type": "windows",
                "supported_methods": ["winrm", "ssh", "snmp", "rest_api"]
            },
            {
                "name": "Network Device",
                "os_type": "network",
                "supported_methods": ["snmp", "telnet", "ssh", "rest_api"]
            },
            {
                "name": "Database Server",
                "os_type": "database",
                "supported_methods": ["mysql", "postgresql", "mssql", "oracle", "mongodb", "redis"]
            },
            {
                "name": "Application Server",
                "os_type": "application",
                "supported_methods": ["rest_api", "ssh", "winrm"]
            },
            {
                "name": "Email Server",
                "os_type": "email",
                "supported_methods": ["smtp", "rest_api", "ssh", "winrm"]
            },
            {
                "name": "Storage System",
                "os_type": "storage",
                "supported_methods": ["snmp", "rest_api", "ssh"]
            },
            {
                "name": "Virtualization Host",
                "os_type": "virtualization",
                "supported_methods": ["rest_api", "ssh", "winrm"]
            },
            {
                "name": "Container Platform",
                "os_type": "container",
                "supported_methods": ["rest_api", "ssh"]
            },
            {
                "name": "Cloud Service",
                "os_type": "cloud",
                "supported_methods": ["rest_api"]
            }
        ]
        
        return {"target_types": target_types}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get target types: {str(e)}"
        )


# ADDITIONAL ENDPOINTS FROM ORIGINAL ROUTER

@router.get("/uuid/{target_uuid}", response_model=TargetResponse)
async def get_target_by_uuid(
    target_uuid: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """Get target by UUID."""
    target = target_service.get_target_by_uuid(target_uuid)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target with UUID {target_uuid} not found"
        )
    return target


@router.get("/serial/{target_serial}", response_model=TargetResponse)
async def get_target_by_serial(
    target_serial: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    target_service: UniversalTargetService = Depends(get_target_service)
):
    """Get target by serial number."""
    target = target_service.get_target_by_serial(target_serial)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target with serial {target_serial} not found"
        )
    return target