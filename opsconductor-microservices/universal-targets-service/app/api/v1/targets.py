"""
Targets API endpoints for Universal Targets Service
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from uuid import uuid4

from app.core.database import get_db
from app.core.auth import get_current_user, require_targets_read, require_targets_write, require_targets_delete
from app.core.events import publish_target_event
from app.schemas.target import (
    TargetCreate, TargetUpdate, TargetResponse, TargetSummary,
    ConnectionTestRequest, ConnectionTestResult, HealthCheckResult,
    BulkOperationRequest, BulkOperationResult, ErrorResponse
)
from app.services.target_service import TargetService
from opsconductor_shared.models.base import EventType

logger = logging.getLogger(__name__)
router = APIRouter()


def get_target_service(db: Session = Depends(get_db)) -> TargetService:
    """Dependency to get target service instance"""
    return TargetService(db)


# =============================================================================
# CRUD Operations
# =============================================================================

@router.get("/", response_model=List[TargetSummary])
async def list_targets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for name or host"),
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    os_type: Optional[str] = Query(None, description="Filter by OS type"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    status: Optional[str] = Query(None, description="Filter by status"),
    health_status: Optional[str] = Query(None, description="Filter by health status"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    current_user: Dict[str, Any] = Depends(require_targets_read),
    target_service: TargetService = Depends(get_target_service)
):
    """List targets with filtering and pagination"""
    try:
        # Parse tags if provided
        tag_list = [tag.strip() for tag in tags.split(',')] if tags else None
        
        # Build filters
        filters = {}
        if target_type:
            filters['target_type'] = target_type
        if os_type:
            filters['os_type'] = os_type
        if environment:
            filters['environment'] = environment
        if status:
            filters['status'] = status
        if health_status:
            filters['health_status'] = health_status
        if tag_list:
            filters['tags'] = tag_list
        
        targets = await target_service.list_targets(
            skip=skip,
            limit=limit,
            search=search,
            filters=filters
        )
        
        return targets
        
    except Exception as e:
        logger.error(f"Failed to list targets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve targets: {str(e)}"
        )


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    current_user: Dict[str, Any] = Depends(require_targets_read),
    target_service: TargetService = Depends(get_target_service)
):
    """Get a specific target by ID"""
    target = await target_service.get_target_by_id(target_id)
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
    current_user: Dict[str, Any] = Depends(require_targets_write),
    target_service: TargetService = Depends(get_target_service)
):
    """Create a new target"""
    try:
        # Create target with user context
        target = await target_service.create_target(
            target_data=target_data,
            created_by=current_user.get("id")
        )
        
        # Publish target created event
        correlation_id = uuid4()
        await publish_target_event(
            event_type=EventType.TARGET_CREATED,
            data={
                "target_id": target.id,
                "name": target.name,
                "target_type": target.target_type,
                "hostname": target_data.host,
                "created_by": current_user.get("id"),
                "connection_methods": [target_data.method_type]
            },
            correlation_id=correlation_id,
            user_id=current_user.get("id")
        )
        
        logger.info(f"Target created: {target.id} by user {current_user.get('id')}")
        return target
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create target: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create target: {str(e)}"
        )


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    target_data: TargetUpdate,
    request: Request,
    current_user: Dict[str, Any] = Depends(require_targets_write),
    target_service: TargetService = Depends(get_target_service)
):
    """Update a target"""
    try:
        # Get original target for event data
        original_target = await target_service.get_target_by_id(target_id)
        if not original_target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target with ID {target_id} not found"
            )
        
        # Update target
        updated_target = await target_service.update_target(
            target_id=target_id,
            target_data=target_data,
            updated_by=current_user.get("id")
        )
        
        # Publish target updated event
        correlation_id = uuid4()
        await publish_target_event(
            event_type=EventType.TARGET_UPDATED,
            data={
                "target_id": target_id,
                "name": updated_target.name,
                "updated_by": current_user.get("id"),
                "changes": target_data.dict(exclude_unset=True)
            },
            correlation_id=correlation_id,
            user_id=current_user.get("id")
        )
        
        logger.info(f"Target updated: {target_id} by user {current_user.get('id')}")
        return updated_target
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update target {target_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update target: {str(e)}"
        )


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(require_targets_delete),
    target_service: TargetService = Depends(get_target_service)
):
    """Delete a target"""
    try:
        # Get target for event data before deletion
        target = await target_service.get_target_by_id(target_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target with ID {target_id} not found"
            )
        
        # Delete target
        success = await target_service.delete_target(target_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete target"
            )
        
        # Publish target deleted event
        correlation_id = uuid4()
        await publish_target_event(
            event_type=EventType.TARGET_DELETED,
            data={
                "target_id": target_id,
                "name": target.name,
                "target_type": target.target_type,
                "deleted_by": current_user.get("id")
            },
            correlation_id=correlation_id,
            user_id=current_user.get("id")
        )
        
        logger.info(f"Target deleted: {target_id} by user {current_user.get('id')}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete target {target_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete target: {str(e)}"
        )


# =============================================================================
# Connection Testing
# =============================================================================

@router.post("/{target_id}/test", response_model=ConnectionTestResult)
async def test_target_connection(
    target_id: int,
    test_request: ConnectionTestRequest = ConnectionTestRequest(),
    current_user: Dict[str, Any] = Depends(require_targets_read),
    target_service: TargetService = Depends(get_target_service)
):
    """Test connection to a specific target"""
    try:
        result = await target_service.test_target_connection(
            target_id=target_id,
            connection_method_id=test_request.connection_method_id,
            test_type=test_request.test_type,
            timeout=test_request.timeout
        )
        
        # Publish connection test event
        correlation_id = uuid4()
        await publish_target_event(
            event_type=EventType.TARGET_CONNECTION_TESTED if result.success else EventType.TARGET_CONNECTION_FAILED,
            data={
                "target_id": target_id,
                "connection_method_id": test_request.connection_method_id,
                "success": result.success,
                "response_time": result.response_time,
                "error_message": result.message if not result.success else None,
                "tested_by": current_user.get("id")
            },
            correlation_id=correlation_id,
            user_id=current_user.get("id")
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to test target connection {target_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test target connection: {str(e)}"
        )


@router.get("/{target_id}/health", response_model=HealthCheckResult)
async def get_target_health(
    target_id: int,
    current_user: Dict[str, Any] = Depends(require_targets_read),
    target_service: TargetService = Depends(get_target_service)
):
    """Get health status for a target"""
    try:
        health_result = await target_service.get_target_health(target_id)
        
        # Publish health check event
        correlation_id = uuid4()
        await publish_target_event(
            event_type=EventType.TARGET_HEALTH_CHECK,
            data={
                "target_id": target_id,
                "health_status": health_result.status,
                "checks_performed": [check.get("type") for check in health_result.checks],
                "response_times": {check.get("type"): check.get("response_time") for check in health_result.checks if check.get("response_time")},
                "errors": [check.get("error") for check in health_result.checks if check.get("error")]
            },
            correlation_id=correlation_id,
            user_id=current_user.get("id")
        )
        
        return health_result
        
    except Exception as e:
        logger.error(f"Failed to get target health {target_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get target health: {str(e)}"
        )


# =============================================================================
# Bulk Operations
# =============================================================================

@router.post("/bulk/test", response_model=BulkOperationResult)
async def bulk_test_connections(
    request_data: BulkOperationRequest,
    current_user: Dict[str, Any] = Depends(require_targets_read),
    target_service: TargetService = Depends(get_target_service)
):
    """Test connections to multiple targets"""
    try:
        results = await target_service.bulk_test_connections(
            target_ids=request_data.target_ids,
            test_options=request_data.operation_data
        )
        
        return BulkOperationResult(
            total_requested=len(request_data.target_ids),
            successful=sum(1 for r in results if r.get("success")),
            failed=sum(1 for r in results if not r.get("success")),
            results=results
        )
        
    except Exception as e:
        logger.error(f"Failed to perform bulk connection tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk connection tests: {str(e)}"
        )


@router.post("/bulk/update", response_model=BulkOperationResult)
async def bulk_update_targets(
    request_data: BulkOperationRequest,
    current_user: Dict[str, Any] = Depends(require_targets_write),
    target_service: TargetService = Depends(get_target_service)
):
    """Update multiple targets with the same data"""
    try:
        results = await target_service.bulk_update_targets(
            target_ids=request_data.target_ids,
            update_data=request_data.operation_data,
            updated_by=current_user.get("id")
        )
        
        return BulkOperationResult(
            total_requested=len(request_data.target_ids),
            successful=sum(1 for r in results if r.get("success")),
            failed=sum(1 for r in results if not r.get("success")),
            results=results
        )
        
    except Exception as e:
        logger.error(f"Failed to perform bulk target updates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk target updates: {str(e)}"
        )


# =============================================================================
# Statistics and Summary
# =============================================================================

@router.get("/summary/stats")
async def get_targets_stats(
    current_user: Dict[str, Any] = Depends(require_targets_read),
    target_service: TargetService = Depends(get_target_service)
):
    """Get target statistics and summary"""
    try:
        stats = await target_service.get_targets_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get targets stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get targets statistics: {str(e)}"
        )


@router.get("/validate/batch")
async def validate_targets_exist(
    target_ids: str = Query(..., description="Comma-separated list of target IDs"),
    current_user: Dict[str, Any] = Depends(require_targets_read),
    target_service: TargetService = Depends(get_target_service)
):
    """Validate that targets exist and are accessible"""
    try:
        # Parse target IDs
        target_id_list = [int(id.strip()) for id in target_ids.split(',')]
        
        validation_result = await target_service.validate_targets_exist(target_id_list)
        return validation_result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target IDs format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to validate targets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate targets: {str(e)}"
        )