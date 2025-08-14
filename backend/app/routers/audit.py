"""
Audit API Router
RESTful API endpoints for audit log management and viewing.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
from app.models.user_models import User
from app.core.security import verify_token
from fastapi.security import HTTPBearer

router = APIRouter(
    prefix="/api/audit",
    tags=["Audit"],
    responses={
        404: {"description": "Resource not found"},
        400: {"description": "Bad request"},
        422: {"description": "Validation error"}
    }
)

security = HTTPBearer()

def get_current_user(credentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user."""
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user

def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    """Dependency to get audit service instance."""
    return AuditService(db)


@router.get("/events")
async def get_audit_events(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=10000, description="Maximum number of records to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    start_date: Optional[datetime] = Query(None, description="Filter events from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events until this date"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    action: Optional[str] = Query(None, description="Filter by action"),
    audit_service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit events with optional filtering.
    
    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        event_type: Filter by specific event type
        user_id: Filter by user ID
        severity: Filter by severity level (LOW, MEDIUM, HIGH, CRITICAL)
        start_date: Filter events from this date
        end_date: Filter events until this date
        resource_type: Filter by resource type (target, job, user, etc.)
        action: Filter by specific action
        
    Returns:
        List of audit events matching the criteria
    """
    try:
        # Build filter criteria
        filters = {}
        if event_type:
            filters['event_type'] = event_type
        if user_id:
            filters['user_id'] = user_id
        if severity:
            filters['severity'] = severity
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if resource_type:
            filters['resource_type'] = resource_type
        if action:
            filters['action'] = action
            
        events = await audit_service.get_audit_events(
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        return {
            "events": events,
            "total": len(events),
            "skip": skip,
            "limit": limit,
            "filters": filters
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit events: {str(e)}"
        )


@router.get("/events/{event_id}")
async def get_audit_event(
    event_id: int,
    audit_service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific audit event by ID.
    
    Args:
        event_id: Audit event ID
        
    Returns:
        Detailed audit event information
    """
    try:
        event = await audit_service.get_audit_event(event_id)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit event with ID {event_id} not found"
            )
        
        return event
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit event: {str(e)}"
        )


@router.get("/stats")
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    audit_service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit statistics for the specified time period.
    
    Args:
        days: Number of days to analyze (default: 30)
        
    Returns:
        Audit statistics including event counts by type, severity, user, etc.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        stats = await audit_service.get_audit_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit statistics: {str(e)}"
        )


@router.get("/users/{user_id}/events")
async def get_user_audit_events(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=5000),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    audit_service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit events for a specific user.
    
    Args:
        user_id: User ID to get events for
        skip: Number of records to skip
        limit: Maximum number of records to return
        days: Number of days to look back
        
    Returns:
        List of audit events for the specified user
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        events = await audit_service.get_user_audit_events(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
        return {
            "user_id": user_id,
            "events": events,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "total": len(events),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user audit events: {str(e)}"
        )


@router.get("/export")
async def export_audit_events(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    start_date: Optional[datetime] = Query(None, description="Export events from this date"),
    end_date: Optional[datetime] = Query(None, description="Export events until this date"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    audit_service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user)
):
    """
    Export audit events in the specified format.
    
    Args:
        format: Export format (json or csv)
        start_date: Export events from this date
        end_date: Export events until this date
        event_type: Filter by event type
        severity: Filter by severity level
        
    Returns:
        Exported audit data
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Build filter criteria
        filters = {}
        if event_type:
            filters['event_type'] = event_type
        if severity:
            filters['severity'] = severity
        filters['start_date'] = start_date
        filters['end_date'] = end_date
        
        exported_data = await audit_service.export_audit_events(
            format=format,
            filters=filters
        )
        
        return {
            "format": format,
            "filters": filters,
            "export_timestamp": datetime.utcnow().isoformat(),
            "data": exported_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export audit events: {str(e)}"
        )


@router.delete("/events/cleanup")
async def cleanup_old_audit_events(
    days: int = Query(90, ge=30, le=365, description="Delete events older than this many days"),
    dry_run: bool = Query(True, description="If true, only count events that would be deleted"),
    audit_service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up old audit events.
    
    Args:
        days: Delete events older than this many days
        dry_run: If true, only count events that would be deleted without actually deleting
        
    Returns:
        Information about the cleanup operation
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        if dry_run:
            count = await audit_service.count_old_audit_events(cutoff_date)
            return {
                "dry_run": True,
                "cutoff_date": cutoff_date.isoformat(),
                "events_to_delete": count,
                "message": f"Would delete {count} audit events older than {days} days"
            }
        else:
            deleted_count = await audit_service.cleanup_old_audit_events(cutoff_date)
            
            # Log the cleanup operation
            await audit_service.log_event(
                event_type=AuditEventType.SYSTEM_MAINTENANCE,
                user_id=current_user.id,
                resource_type="audit_events",
                resource_id="cleanup",
                action="cleanup_old_events",
                details={
                    "cutoff_date": cutoff_date.isoformat(),
                    "deleted_count": deleted_count,
                    "retention_days": days,
                    "performed_by": current_user.username
                },
                severity=AuditSeverity.MEDIUM
            )
            
            return {
                "dry_run": False,
                "cutoff_date": cutoff_date.isoformat(),
                "deleted_count": deleted_count,
                "message": f"Successfully deleted {deleted_count} audit events older than {days} days"
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup audit events: {str(e)}"
        )