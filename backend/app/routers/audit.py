"""
Simple Audit API v1 Router
Provides basic audit functionality and lookup endpoints for data enrichment.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.database.database import get_db
from app.services.user_service import UserService
from app.core.auth_dependencies import get_current_user
from app.services.universal_target_service import UniversalTargetService
from app.domains.audit.services.audit_service import AuditService

router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Audit v1"],
    responses={
        404: {"description": "Not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)

# Response models
class UserLookupResponse(BaseModel):
    users: Dict[int, Dict[str, Any]]
    metadata: Dict[str, Any]

class TargetLookupResponse(BaseModel):
    targets: Dict[str, Dict[str, Any]]
    metadata: Dict[str, Any]

class AuditEventResponse(BaseModel):
    id: str
    event_type: str
    user_id: Optional[int]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    severity: str
    timestamp: datetime
    ip_address: Optional[str]

class AuditEventsListResponse(BaseModel):
    events: List[AuditEventResponse]
    total: int
    page: int
    limit: int

class EventTypeResponse(BaseModel):
    name: str
    description: str
    category: str

class EventTypesResponse(BaseModel):
    event_types: List[EventTypeResponse]

def require_audit_permissions(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Require audit viewing permissions."""
    if current_user.get("role") not in ["administrator", "operator", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access audit data"
        )
    return current_user

@router.get("/lookups/users", response_model=UserLookupResponse)
async def get_user_lookups(
    user_ids: Optional[str] = Query(None, description="Comma-separated list of user IDs to lookup"),
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
) -> UserLookupResponse:
    """Get user lookup data for audit event enrichment"""
    
    try:
        # Parse user IDs if provided
        target_user_ids = None
        if user_ids:
            try:
                target_user_ids = [int(uid.strip()) for uid in user_ids.split(',') if uid.strip()]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user IDs format. Use comma-separated integers."
                )
        
        # Get users from database
        if target_user_ids:
            # Get specific users
            users_data = {}
            for user_id in target_user_ids:
                user = UserService.get_user_by_id(db, user_id)
                if user:
                    users_data[user_id] = {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "display_name": f"{user.username} ({user.role})",
                        "is_active": user.is_active
                    }
        else:
            # Get all users (limited for performance)
            users = UserService.get_users(db, skip=0, limit=1000)
            users_data = {}
            for user in users:
                users_data[user.id] = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "display_name": f"{user.username} ({user.role})",
                    "is_active": user.is_active
                }
        
        return UserLookupResponse(
            users=users_data,
            metadata={
                "total_users": len(users_data),
                "requested_by": current_user.username,
                "timestamp": datetime.utcnow().isoformat(),
                "filtered": bool(user_ids)
            }
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred while retrieving user lookup data: {str(e)}"
        )

@router.get("/lookups/targets", response_model=TargetLookupResponse)
async def get_target_lookups(
    target_ids: Optional[str] = Query(None, description="Comma-separated list of target IDs to lookup"),
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
) -> TargetLookupResponse:
    """Get target lookup data for audit event enrichment"""
    
    try:
        # Parse target IDs if provided
        target_target_ids = None
        if target_ids:
            try:
                target_target_ids = [int(tid.strip()) for tid in target_ids.split(',') if tid.strip()]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid target IDs format. Use comma-separated integers."
                )
        
        # Get targets from database
        targets_data = {}
        
        try:
            target_service = UniversalTargetService(db)
            
            if target_target_ids:
                # Get specific targets
                for target_id in target_target_ids:
                    try:
                        target = target_service.get_target_by_id(target_id)
                        if target:
                            targets_data[str(target_id)] = {
                                "id": target.id,
                                "name": target.name,
                                "target_type": target.target_type,
                                "os_type": target.os_type,
                                "environment": target.environment,
                                "display_name": f"{target.name} ({target.target_type.title()} {target.environment.title()})",
                                "is_active": target.is_active,
                                "status": target.status
                            }
                    except Exception as e:
                        print(f"Error getting target {target_id}: {e}")
                        continue
            else:
                # Get all targets (limited for performance)
                try:
                    targets = target_service.get_all_targets()  # Use get_all_targets instead
                    for target in targets:
                        targets_data[str(target.id)] = {
                            "id": target.id,
                            "name": target.name,
                            "target_type": target.target_type,
                            "os_type": target.os_type,
                            "environment": target.environment,
                            "display_name": f"{target.name} ({target.target_type.title()} {target.environment.title()})",
                            "is_active": target.is_active,
                            "status": target.status
                        }
                except Exception as e:
                    print(f"Error getting targets summary: {e}")
                    # Return empty targets data if there's an error
                    targets_data = {}
        except Exception as e:
            print(f"Error initializing target service: {e}")
            # Return empty targets data if service initialization fails
            targets_data = {}
        
        return TargetLookupResponse(
            targets=targets_data,
            metadata={
                "total_targets": len(targets_data),
                "requested_by": current_user.username,
                "timestamp": datetime.utcnow().isoformat(),
                "filtered": bool(target_ids)
            }
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred while retrieving target lookup data: {str(e)}"
        )

@router.get("/events", response_model=AuditEventsListResponse)
async def get_audit_events(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
) -> AuditEventsListResponse:
    """Get paginated list of audit events"""
    
    try:
        audit_service = AuditService(db)
        
        # Convert string filters to enum types if provided
        event_type_enum = None
        if event_type:
            try:
                from app.domains.audit.services.audit_service import AuditEventType
                event_type_enum = AuditEventType(event_type)
            except ValueError:
                pass
        
        severity_enum = None
        if severity:
            try:
                from app.domains.audit.services.audit_service import AuditSeverity
                severity_enum = AuditSeverity(severity)
            except ValueError:
                pass
        
        # Get events with pagination
        result = await audit_service.get_recent_events(
            page=page,
            limit=limit,
            event_type=event_type_enum,
            user_id=user_id,
            severity=severity_enum
        )
        
        # Convert to response format
        event_responses = []
        for event in result.get("events", []):
            event_responses.append(AuditEventResponse(
                id=str(event.get("id", "")),
                event_type=event.get("event_type", ""),
                user_id=event.get("user_id"),
                resource_type=event.get("resource_type"),
                resource_id=event.get("resource_id"),
                action=event.get("action", ""),
                details=event.get("details", {}),
                severity=event.get("severity", ""),
                timestamp=datetime.fromisoformat(event.get("timestamp", datetime.utcnow().isoformat()).replace('Z', '+00:00')),
                ip_address=event.get("ip_address")
            ))
        
        return AuditEventsListResponse(
            events=event_responses,
            total=result.get("total", 0),
            page=page,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred while retrieving audit events: {str(e)}"
        )

@router.get("/event-types", response_model=EventTypesResponse)
async def get_audit_event_types(
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
) -> EventTypesResponse:
    """Get available audit event types"""
    
    try:
        # Return basic event types
        event_types = [
            EventTypeResponse(
                name="user_login",
                description="User login event",
                category="authentication"
            ),
            EventTypeResponse(
                name="user_logout",
                description="User logout event",
                category="authentication"
            ),
            EventTypeResponse(
                name="target_created",
                description="Target creation event",
                category="target_management"
            ),
            EventTypeResponse(
                name="target_updated",
                description="Target update event",
                category="target_management"
            ),
            EventTypeResponse(
                name="target_deleted",
                description="Target deletion event",
                category="target_management"
            ),
            EventTypeResponse(
                name="job_created",
                description="Job creation event",
                category="job_management"
            ),
            EventTypeResponse(
                name="job_executed",
                description="Job execution event",
                category="job_management"
            ),
            EventTypeResponse(
                name="system_maintenance",
                description="System maintenance event",
                category="system"
            )
        ]
        
        return EventTypesResponse(event_types=event_types)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred while retrieving event types: {str(e)}"
        )

@router.post("/search", response_model=AuditEventsListResponse)
async def search_audit_events(
    search_request: dict,
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
) -> AuditEventsListResponse:
    """Search audit events"""
    
    try:
        # Extract search parameters
        query = search_request.get("query", "")
        event_types = search_request.get("event_types", [])
        page = search_request.get("page", 1)
        limit = search_request.get("limit", 50)
        
        audit_service = AuditService(db)
        
        # Convert event types to enum types if provided
        event_type_enums = []
        if event_types:
            from app.domains.audit.services.audit_service import AuditEventType
            for et in event_types:
                try:
                    event_type_enums.append(AuditEventType(et))
                except ValueError:
                    pass
        
        # Perform search
        result = await audit_service.search_audit_events(
            query=query,
            page=page,
            limit=limit,
            event_types=event_type_enums if event_type_enums else None
        )
        
        # Convert to response format
        event_responses = []
        for event in result.get("events", []):
            event_responses.append(AuditEventResponse(
                id=str(event.get("id", "")),
                event_type=event.get("event_type", ""),
                user_id=event.get("user_id"),
                resource_type=event.get("resource_type"),
                resource_id=event.get("resource_id"),
                action=event.get("action", ""),
                details=event.get("details", {}),
                severity=event.get("severity", ""),
                timestamp=datetime.fromisoformat(event.get("timestamp", datetime.utcnow().isoformat()).replace('Z', '+00:00')),
                ip_address=event.get("ip_address")
            ))
        
        return AuditEventsListResponse(
            events=event_responses,
            total=result.get("total", 0),
            page=page,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred while searching audit events: {str(e)}"
        )

# Placeholder endpoints for compatibility
@router.get("/verify/{event_id}")
async def verify_audit_event(
    event_id: str,
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
):
    """Verify audit event (placeholder)"""
    return {"verified": True, "event_id": event_id}

@router.get("/compliance/report")
async def get_compliance_report(
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
):
    """Get compliance report (placeholder)"""
    return {
        "report_id": f"compliance_report_{datetime.utcnow().strftime('%Y%m%d')}",
        "generated_at": datetime.utcnow().isoformat(),
        "events_analyzed": 0,
        "compliance_score": 100.0
    }