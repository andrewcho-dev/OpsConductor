"""
Audit API v1 for security and compliance logging.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from app.database.database import get_db
from main import get_current_user
from app.models.user_models import User
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity

router = APIRouter(prefix="/api/v1/audit")


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    """Get audit service with dependencies."""
    return AuditService(db)


@router.get("/events")
async def get_audit_events(
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    severity: Optional[str] = None,
    service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user)
):
    """Get recent audit events."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit events"
        )
    
    # Convert string parameters to enums
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {event_type}"
            )
    
    severity_enum = None
    if severity:
        try:
            severity_enum = AuditSeverity(severity)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}"
            )
    
    events = await service.get_recent_events(
        limit=limit,
        event_type=event_type_enum,
        user_id=user_id,
        severity=severity_enum
    )
    
    return {
        "events": events,
        "total_returned": len(events),
        "filters": {
            "event_type": event_type,
            "user_id": user_id,
            "severity": severity,
            "limit": limit
        }
    }


@router.get("/statistics")
async def get_audit_statistics(
    service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user)
):
    """Get audit statistics."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit statistics"
        )
    
    stats = await service.get_audit_statistics()
    return stats


@router.post("/search")
async def search_audit_events(
    query: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_types: Optional[List[str]] = None,
    user_ids: Optional[List[int]] = None,
    limit: int = Query(100, ge=1, le=1000),
    service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user)
):
    """Search audit events."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to search audit events"
        )
    
    # Convert event types to enums
    event_type_enums = None
    if event_types:
        try:
            event_type_enums = [AuditEventType(et) for et in event_types]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {str(e)}"
            )
    
    events = await service.search_audit_events(
        query=query,
        start_date=start_date,
        end_date=end_date,
        event_types=event_type_enums,
        user_ids=user_ids,
        limit=limit
    )
    
    return {
        "events": events,
        "total_returned": len(events),
        "search_criteria": {
            "query": query,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "event_types": event_types,
            "user_ids": user_ids,
            "limit": limit
        }
    }


@router.get("/verify/{entry_id}")
async def verify_audit_entry(
    entry_id: str,
    service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user)
):
    """Verify audit entry integrity."""
    if current_user.role not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can verify audit entries"
        )
    
    verification = await service.verify_audit_integrity(entry_id)
    return verification


@router.get("/compliance/report")
async def get_compliance_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user)
):
    """Generate compliance report."""
    if current_user.role not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can generate compliance reports"
        )
    
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    report = await service.get_compliance_report(start_date, end_date)
    return report


@router.get("/event-types")
async def get_audit_event_types(
    current_user: User = Depends(get_current_user)
):
    """Get available audit event types."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit configuration"
        )
    
    return {
        "event_types": [
            {
                "value": event_type.value,
                "name": event_type.name,
                "description": event_type.value.replace("_", " ").title()
            }
            for event_type in AuditEventType
        ],
        "severity_levels": [
            {
                "value": severity.value,
                "name": severity.name,
                "description": severity.value.title()
            }
            for severity in AuditSeverity
        ]
    }