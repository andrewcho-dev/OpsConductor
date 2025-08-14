"""
Enhanced Targets API v1 with domain-driven architecture.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.database.database import get_db
from main import get_current_user
from app.models.user_models import User
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
from app.domains.target_management.services.target_domain_service import TargetDomainService
from app.domains.target_management.repositories.target_repository import TargetRepository
from app.shared.infrastructure.container import container
from app.shared.infrastructure.cache import cached
from app.schemas.target_schemas import (
    TargetCreate, TargetUpdate, TargetResponse, 
    BulkTargetOperation, ConnectionTestResult
)

router = APIRouter(prefix="/api/v1/targets")


def get_target_service(db: Session = Depends(get_db)) -> TargetDomainService:
    """Get target domain service with dependencies."""
    target_repository = TargetRepository(db)
    return TargetDomainService(target_repository)


@router.get("/", response_model=Dict[str, Any])
async def get_targets(
    skip: int = 0,
    limit: int = 100,
    search: str = "",
    target_type: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
    service: TargetDomainService = Depends(get_target_service),
    current_user: User = Depends(get_current_user)
):
    """Get targets with filtering and pagination."""
    filters = {}
    if target_type:
        filters["target_type"] = target_type
    if status:
        filters["status"] = status
    if tags:
        filters["tags"] = tags
    
    targets = await service.search_targets(
        search_term=search,
        filters=filters,
        skip=skip,
        limit=limit
    )
    
    # Get total count for pagination
    total_count = len(await service.search_targets(search_term=search, filters=filters, skip=0, limit=10000))
    
    return {
        "data": targets,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total_count": total_count,
            "has_more": skip + limit < total_count
        }
    }


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    service: TargetDomainService = Depends(get_target_service),
    current_user: User = Depends(get_current_user)
):
    """Get target by ID."""
    target = await service.target_repository.get_by_id_or_raise(target_id)
    return target


@router.post("/", response_model=TargetResponse)
async def create_target(
    target_data: TargetCreate,
    request: Request,
    service: TargetDomainService = Depends(get_target_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new target."""
    target = await service.create_target(
        name=target_data.name,
        host=target_data.host,
        target_type=target_data.target_type,
        port=target_data.port,
        credentials=target_data.credentials.dict() if target_data.credentials else {},
        created_by=current_user.id,
        description=target_data.description or "",
        tags=target_data.tags or [],
        custom_config=target_data.custom_config or {}
    )
    
    # Log target creation audit event
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    await audit_service.log_event(
        event_type=AuditEventType.TARGET_CREATED,
        user_id=current_user.id,
        resource_type="target",
        resource_id=str(target.id),
        action="create_target_v1",
        details={
            "target_name": target_data.name,
            "host": target_data.host,
            "target_type": target_data.target_type,
            "port": target_data.port,
            "created_by": current_user.username,
            "api_version": "v1"
        },
        severity=AuditSeverity.MEDIUM,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return target


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    target_data: TargetUpdate,
    request: Request,
    service: TargetDomainService = Depends(get_target_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update target."""
    update_dict = target_data.dict(exclude_unset=True)
    if target_data.credentials:
        update_dict["credentials"] = target_data.credentials.dict()
    
    target = await service.update_target(
        target_id=target_id,
        update_data=update_dict,
        updated_by=current_user.id
    )
    
    # Log target update audit event
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    await audit_service.log_event(
        event_type=AuditEventType.TARGET_UPDATED,
        user_id=current_user.id,
        resource_type="target",
        resource_id=str(target_id),
        action="update_target_v1",
        details={
            "target_id": target_id,
            "updated_fields": update_dict,
            "updated_by": current_user.username,
            "api_version": "v1"
        },
        severity=AuditSeverity.MEDIUM,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return target


@router.delete("/{target_id}")
async def delete_target(
    target_id: int,
    request: Request,
    service: TargetDomainService = Depends(get_target_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete target."""
    if current_user.role not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete targets"
        )
    
    # Get target info before deletion for audit
    try:
        target = await service.target_repository.get_by_id_or_raise(target_id)
        target_name = target.name
    except:
        target_name = f"target_{target_id}"
    
    success = await service.delete_target(target_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found"
        )
    
    # Log target deletion audit event
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    await audit_service.log_event(
        event_type=AuditEventType.TARGET_DELETED,
        user_id=current_user.id,
        resource_type="target",
        resource_id=str(target_id),
        action="delete_target_v1",
        details={
            "target_id": target_id,
            "target_name": target_name,
            "deleted_by": current_user.username,
            "api_version": "v1"
        },
        severity=AuditSeverity.HIGH,  # Target deletion is high severity
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return {"message": "Target deleted successfully"}


@router.post("/{target_id}/test", response_model=ConnectionTestResult)
async def test_target_connection(
    target_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    service: TargetDomainService = Depends(get_target_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test connection to target."""
    result = await service.test_target_connection(target_id, current_user.id)
    
    # Log connection test audit event
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Get target info for audit
    try:
        target = await service.target_repository.get_by_id_or_raise(target_id)
        target_name = target.name
    except:
        target_name = f"target_{target_id}"
    
    await audit_service.log_event(
        event_type=AuditEventType.TARGET_CONNECTION_TEST,
        user_id=current_user.id,
        resource_type="target",
        resource_id=str(target_id),
        action="test_connection_v1",
        details={
            "target_id": target_id,
            "target_name": target_name,
            "test_result": result.get("success", "unknown"),
            "tested_by": current_user.username,
            "api_version": "v1"
        },
        severity=AuditSeverity.LOW,  # Connection tests are low severity
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return ConnectionTestResult(**result)


@router.post("/bulk/test")
async def bulk_test_connections(
    target_ids: List[int],
    background_tasks: BackgroundTasks,
    request: Request,
    service: TargetDomainService = Depends(get_target_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test connections to multiple targets."""
    result = await service.bulk_test_connections(target_ids, current_user.id)
    
    # Log bulk operation audit event
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    await audit_service.log_event(
        event_type=AuditEventType.BULK_OPERATION,
        user_id=current_user.id,
        resource_type="target",
        resource_id=f"bulk_{len(target_ids)}_targets",
        action="bulk_test_connections",
        details={
            "operation_type": "bulk_connection_test",
            "target_count": len(target_ids),
            "target_ids": target_ids,
            "performed_by": current_user.username,
            "results": result
        },
        severity=AuditSeverity.MEDIUM,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return result


@router.post("/bulk/update")
async def bulk_update_targets(
    operation: BulkTargetOperation,
    request: Request,
    service: TargetDomainService = Depends(get_target_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk update multiple targets."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for bulk operations"
        )
    
    result = await service.bulk_update_targets(
        target_ids=operation.target_ids,
        update_data=operation.update_data,
        updated_by=current_user.id
    )
    
    # Log bulk operation audit event
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    await audit_service.log_event(
        event_type=AuditEventType.BULK_OPERATION,
        user_id=current_user.id,
        resource_type="target",
        resource_id=f"bulk_{len(operation.target_ids)}_targets",
        action="bulk_update_targets",
        details={
            "operation_type": "bulk_update",
            "target_count": len(operation.target_ids),
            "target_ids": operation.target_ids,
            "update_data": operation.update_data,
            "performed_by": current_user.username,
            "affected_targets": result.get("updated_count", 0)
        },
        severity=AuditSeverity.HIGH,  # Bulk updates are high severity
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return result


@router.get("/statistics/overview")
@cached(ttl=300, key_prefix="target_stats")
async def get_target_statistics(
    service: TargetDomainService = Depends(get_target_service),
    current_user: User = Depends(get_current_user)
):
    """Get target statistics."""
    stats = await service.get_target_statistics()
    return stats


@router.get("/health/check")
async def get_targets_needing_health_check(
    minutes_since_last_check: int = 30,
    service: TargetDomainService = Depends(get_target_service),
    current_user: User = Depends(get_current_user)
):
    """Get targets that need health check."""
    targets = await service.get_targets_needing_health_check(minutes_since_last_check)
    return {
        "targets_needing_check": len(targets),
        "targets": targets
    }


@router.post("/health/perform")
async def perform_health_checks(
    background_tasks: BackgroundTasks,
    service: TargetDomainService = Depends(get_target_service),
    current_user: User = Depends(get_current_user)
):
    """Perform health checks on targets that need it."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for health checks"
        )
    
    # Run health checks in background
    background_tasks.add_task(service.perform_health_checks)
    
    return {"message": "Health checks started in background"}


@router.get("/types")
async def get_target_types(
    current_user: User = Depends(get_current_user)
):
    """Get available target types."""
    return {
        "target_types": [
            {"value": "ssh", "label": "SSH Server", "default_port": 22},
            {"value": "http", "label": "HTTP Server", "default_port": 80},
            {"value": "https", "label": "HTTPS Server", "default_port": 443},
            {"value": "rdp", "label": "Remote Desktop", "default_port": 3389},
            {"value": "database", "label": "Database Server", "default_port": 5432},
            {"value": "snmp", "label": "SNMP Device", "default_port": 161},
            {"value": "custom", "label": "Custom Service", "default_port": 8080}
        ]
    }