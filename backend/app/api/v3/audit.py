"""
Audit API v3 - Consolidated from v1/audit endpoints
All audit and lookup endpoints in v3 structure
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.domains.audit.services.audit_service import AuditService
from app.clients.auth_service_client import auth_client
from app.services.universal_target_service import UniversalTargetService

api_base_url = os.getenv("API_BASE_URL", "/api/v3")
router = APIRouter(prefix=f"{api_base_url}/audit", tags=["Audit v3"])

logger = logging.getLogger(__name__)


@router.get("/event-types")
async def get_event_types(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get available audit event types."""
    try:
        from app.domains.audit.services.audit_service import AuditEventType
        
        # Get all event types from the enum
        event_types = [
            {
                "name": event_type.name,
                "value": event_type.value,
                "description": event_type.value.replace('_', ' ').title()
            }
            for event_type in AuditEventType
        ]
        
        return {"event_types": event_types}
    except Exception as e:
        logger.error(f"Failed to get event types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get event types: {str(e)}"
        )


@router.get("/lookups/users")
async def get_user_lookups(
    user_ids: Optional[str] = Query(None, description="Comma-separated list of user IDs"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user lookup data for audit enrichment."""
    try:
        if user_ids:
            # Parse comma-separated user IDs
            user_id_list = [int(uid.strip()) for uid in user_ids.split(',') if uid.strip().isdigit()]
            users_data = {}
            
            for user_id in user_id_list:
                try:
                    user = await auth_client.get_user_by_id(user_id)
                    if user:
                        users_data[str(user_id)] = {
                            "id": user["id"],
                            "username": user["username"],
                            "email": user["email"],
                            "role": user["role"],
                            "is_active": user["is_active"]
                        }
                except Exception as e:
                    logger.warning(f"Failed to get user {user_id}: {str(e)}")
                    continue
        else:
            # Get all users
            users_response = await auth_client.get_users(skip=0, limit=1000)  # Reasonable limit
            users = users_response.get("users", [])
            users_data = {
                str(user["id"]): {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "is_active": user["is_active"]
                }
                for user in users
            }
        
        return {"users": users_data}
    except Exception as e:
        logger.error(f"Failed to get user lookups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user lookups: {str(e)}"
        )


@router.get("/lookups/targets")
async def get_target_lookups(
    target_ids: Optional[str] = Query(None, description="Comma-separated list of target IDs"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get target lookup data for audit enrichment."""
    try:
        target_service = UniversalTargetService(db)
        
        if target_ids:
            # Parse comma-separated target IDs
            target_id_list = [int(tid.strip()) for tid in target_ids.split(',') if tid.strip().isdigit()]
            targets_data = {}
            
            for target_id in target_id_list:
                try:
                    target = target_service.get_target_by_id(target_id)
                    if target:
                        targets_data[str(target_id)] = {
                            "id": target.id,
                            "name": target.name,
                            "ip_address": target.ip_address,
                            "os_type": target.os_type,
                            "status": target.status,
                            "environment": target.environment
                        }
                except Exception as e:
                    logger.warning(f"Failed to get target {target_id}: {str(e)}")
                    continue
        else:
            # Get all targets (summary)
            targets = target_service.get_targets_summary(skip=0, limit=1000)  # Reasonable limit
            targets_data = {
                str(target.id): {
                    "id": target.id,
                    "name": target.name,
                    "ip_address": target.ip_address,
                    "os_type": target.os_type,
                    "status": target.status,
                    "environment": getattr(target, 'environment', None)
                }
                for target in targets
            }
        
        return {"targets": targets_data}
    except Exception as e:
        logger.error(f"Failed to get target lookups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get target lookups: {str(e)}"
        )


@router.get("/events")
async def get_audit_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    resource_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit events with filtering."""
    try:
        audit_service = AuditService(db)
        
        # Build filters
        filters = {}
        if event_type:
            filters['event_type'] = event_type
        if user_id:
            filters['user_id'] = user_id
        if resource_type:
            filters['resource_type'] = resource_type
        if severity:
            filters['severity'] = severity
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        
        # Get events (this would need to be implemented in AuditService)
        events = await audit_service.get_events(
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        return {
            "events": events,
            "total": len(events),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Failed to get audit events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit events: {str(e)}"
        )


@router.get("/events/{event_id}")
async def get_audit_event(
    event_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific audit event by ID."""
    try:
        audit_service = AuditService(db)
        
        # Get event (this would need to be implemented in AuditService)
        event = await audit_service.get_event_by_id(event_id)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit event {event_id} not found"
            )
        
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit event {event_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit event: {str(e)}"
        )


@router.get("/stats")
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit statistics for the specified period."""
    try:
        audit_service = AuditService(db)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get statistics (this would need to be implemented in AuditService)
        stats = await audit_service.get_statistics(start_date, end_date)
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get audit stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit statistics: {str(e)}"
        )