"""
Audit API v1 Enhanced - Phases 1 & 2
Complete transformation with service layer, caching, and comprehensive models

PHASE 1 & 2 IMPROVEMENTS:
- ✅ Comprehensive Pydantic models with validation
- ✅ Service layer integration with business logic separation
- ✅ Redis caching for improved performance
- ✅ Structured JSON logging with contextual information
- ✅ Enhanced error handling with detailed responses
- ✅ Advanced audit search and filtering
- ✅ Compliance reporting and data export
- ✅ Real-time audit analytics and monitoring
- ✅ Audit event correlation and analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator

# Import service layer
from app.services.audit_management_service import AuditManagementService, AuditManagementError
from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.core.logging import get_structured_logger, RequestLogger
from app.domains.audit.services.audit_service import AuditEventType, AuditSeverity

# Configure structured logger
logger = get_structured_logger(__name__)

# Security scheme

# PHASE 1: COMPREHENSIVE PYDANTIC MODELS

class AuditEventResponse(BaseModel):
    """Enhanced response model for audit events"""
    id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of audit event")
    user_id: Optional[int] = Field(None, description="User who triggered the event")
    resource_type: Optional[str] = Field(None, description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="Identifier of affected resource")
    action: str = Field(..., description="Action performed")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event details")
    severity: str = Field(..., description="Event severity level")
    ip_address: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    timestamp: datetime = Field(..., description="Event timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "audit_event_123",
                "event_type": "user_login",
                "user_id": 1,
                "resource_type": "user",
                "resource_id": "1",
                "action": "login",
                "details": {
                    "username": "admin",
                    "login_method": "password"
                },
                "severity": "medium",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "timestamp": "2025-01-01T10:30:00Z",
                "metadata": {
                    "event_category": "authentication",
                    "risk_level": "low",
                    "compliance_relevant": True
                }
            }
        }


class AuditEventsListResponse(BaseModel):
    """Enhanced response model for audit events list"""
    events: List[AuditEventResponse] = Field(..., description="List of audit events")
    total: int = Field(..., description="Total number of events")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of events per page")
    total_pages: int = Field(..., description="Total number of pages")
    filters: Dict[str, Any] = Field(..., description="Applied filters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "events": [
                    {
                        "id": "audit_event_123",
                        "event_type": "user_login",
                        "action": "login",
                        "severity": "medium",
                        "timestamp": "2025-01-01T10:30:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 50,
                "total_pages": 1,
                "filters": {
                    "event_type": None,
                    "user_id": None,
                    "severity": None
                },
                "metadata": {
                    "cache_hit": False,
                    "query_time": 1640995800.0,
                    "requested_by": "admin"
                }
            }
        }


class AuditStatisticsResponse(BaseModel):
    """Enhanced response model for audit statistics"""
    total_events: int = Field(..., description="Total number of audit events")
    events_by_type: Dict[str, int] = Field(..., description="Events grouped by type")
    events_by_severity: Dict[str, int] = Field(..., description="Events grouped by severity")
    events_by_user: Dict[str, int] = Field(..., description="Events grouped by user")
    recent_activity: List[Dict[str, Any]] = Field(..., description="Recent audit activity")
    analytics: Dict[str, Any] = Field(default_factory=dict, description="Advanced analytics")
    trends: Dict[str, Any] = Field(default_factory=dict, description="Trend analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_events": 1500,
                "events_by_type": {
                    "user_login": 450,
                    "target_created": 200,
                    "data_export": 50
                },
                "events_by_severity": {
                    "low": 800,
                    "medium": 600,
                    "high": 90,
                    "critical": 10
                },
                "events_by_user": {
                    "admin": 500,
                    "operator": 300,
                    "user": 700
                },
                "recent_activity": [],
                "analytics": {
                    "events_per_hour": 12.5,
                    "security_incidents": 5,
                    "compliance_score": 95.0
                },
                "trends": {
                    "daily_trend": [],
                    "severity_distribution": {}
                }
            }
        }


class AuditSearchRequest(BaseModel):
    """Enhanced request model for audit search"""
    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    page: int = Field(1, description="Page number", ge=1)
    limit: int = Field(50, description="Results per page", ge=1, le=10000)
    start_date: Optional[datetime] = Field(None, description="Search start date")
    end_date: Optional[datetime] = Field(None, description="Search end date")
    event_types: Optional[List[str]] = Field(None, description="Filter by event types")
    user_ids: Optional[List[int]] = Field(None, description="Filter by user IDs")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date"""
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "login failed",
                "page": 1,
                "limit": 50,
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-01-31T23:59:59Z",
                "event_types": ["user_login", "user_logout"],
                "user_ids": [1, 2, 3]
            }
        }


class AuditVerificationResponse(BaseModel):
    """Enhanced response model for audit verification"""
    entry_id: str = Field(..., description="Audit entry identifier")
    is_valid: bool = Field(..., description="Whether the entry is valid")
    verification_details: Dict[str, Any] = Field(..., description="Verification details")
    integrity_checks: Dict[str, Any] = Field(..., description="Integrity check results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Verification metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entry_id": "audit_event_123",
                "is_valid": True,
                "verification_details": {
                    "hash_match": True,
                    "timestamp_valid": True,
                    "signature_valid": True
                },
                "integrity_checks": {
                    "hash_verification": True,
                    "timestamp_validation": True,
                    "chain_integrity": True,
                    "signature_verification": True
                },
                "metadata": {
                    "verification_time": "2025-01-01T10:30:00Z",
                    "verification_method": "comprehensive"
                }
            }
        }


class ComplianceReportResponse(BaseModel):
    """Enhanced response model for compliance reports"""
    report_id: str = Field(..., description="Report identifier")
    period: Dict[str, str] = Field(..., description="Report period")
    summary: Dict[str, Any] = Field(..., description="Report summary")
    events_by_category: Dict[str, int] = Field(..., description="Events by category")
    compliance_metrics: Dict[str, Any] = Field(..., description="Compliance metrics")
    risk_assessment: Dict[str, Any] = Field(..., description="Risk assessment")
    recommendations: List[str] = Field(..., description="Compliance recommendations")
    analytics: Dict[str, Any] = Field(default_factory=dict, description="Advanced analytics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Report metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "compliance_report_202501",
                "period": {
                    "start_date": "2025-01-01T00:00:00Z",
                    "end_date": "2025-01-31T23:59:59Z"
                },
                "summary": {
                    "total_events": 1500,
                    "security_events": 100,
                    "compliance_violations": 5
                },
                "events_by_category": {
                    "authentication": 450,
                    "data_access": 300,
                    "system_changes": 200
                },
                "compliance_metrics": {
                    "compliance_score": 95.0,
                    "audit_coverage": 98.5
                },
                "risk_assessment": {
                    "level": "low",
                    "score": 2.1
                },
                "recommendations": [
                    "Increase monitoring of failed login attempts",
                    "Review data export policies"
                ],
                "analytics": {
                    "compliance_score": 95.0,
                    "trend_analysis": {}
                }
            }
        }


class AuditEventTypesResponse(BaseModel):
    """Enhanced response model for audit event types"""
    event_types: List[Dict[str, Any]] = Field(..., description="Available event types")
    severity_levels: List[Dict[str, Any]] = Field(..., description="Available severity levels")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Configuration metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_types": [
                    {
                        "value": "user_login",
                        "name": "USER_LOGIN",
                        "description": "User Login",
                        "category": "authentication",
                        "severity_recommendation": "medium"
                    }
                ],
                "severity_levels": [
                    {
                        "value": "low",
                        "name": "LOW",
                        "description": "Low",
                        "color": "#28a745",
                        "priority": 1
                    }
                ],
                "metadata": {
                    "total_event_types": 15,
                    "total_severity_levels": 4,
                    "requested_by": "admin",
                    "timestamp": "2025-01-01T10:30:00Z"
                }
            }
        }


class AuditErrorResponse(BaseModel):
    """Enhanced error response model for audit management errors"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "search_error",
                "message": "Audit search failed due to invalid query parameters",
                "details": {
                    "field_errors": "Invalid date range specified"
                },
                "timestamp": "2025-01-01T10:30:00Z",
                "request_id": "audit_req_abc123"
            }
        }


# PHASE 1 & 2: ENHANCED ROUTER WITH SERVICE LAYER INTEGRATION

router = APIRouter(
    prefix="/api/v2/audit",
    tags=["Audit Management Enhanced v2"],
    responses={
        401: {"model": AuditErrorResponse, "description": "Authentication required"},
        403: {"model": AuditErrorResponse, "description": "Insufficient permissions"},
        404: {"model": AuditErrorResponse, "description": "Resource not found"},
        422: {"model": AuditErrorResponse, "description": "Validation error"},
        500: {"model": AuditErrorResponse, "description": "Internal server error"}
    }
)


# PHASE 2: ENHANCED DEPENDENCY FUNCTIONS

# Local get_current_user removed - using centralized auth_dependencies


def require_audit_permissions(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Require audit viewing permissions."""
    if current_user["role"] not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_permissions",
                "message": "Insufficient permissions to access audit data",
                "required_roles": ["administrator", "operator"],
                "user_role": current_user["role"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    return current_user


def require_admin_permissions(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Require administrator permissions."""
    if current_user["role"] not in ["administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "admin_required",
                "message": "Administrator permissions required",
                "required_roles": ["administrator"],
                "user_role": current_user["role"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    return current_user


# PHASE 1 & 2: ENHANCED ENDPOINTS WITH SERVICE LAYER

@router.get(
    "/events",
    response_model=AuditEventsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Audit Events",
    description="""
    Get paginated list of audit events with advanced filtering and caching.
    
    **Phase 1 & 2 Features:**
    - ✅ Advanced pagination with comprehensive metadata
    - ✅ Multi-field filtering (event type, user, severity, date range)
    - ✅ Redis caching for improved performance
    - ✅ Enhanced audit events with risk analysis
    - ✅ Real-time activity tracking
    
    **Performance:**
    - Redis caching with 5-minute TTL
    - Optimized database queries
    - Structured logging for monitoring
    
    **Security:**
    - Role-based access control (administrator, operator)
    - Comprehensive audit trail
    - Input validation and sanitization
    """,
    responses={
        200: {"description": "Audit events retrieved successfully", "model": AuditEventsListResponse}
    }
)
async def get_audit_events(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=10000, description="Events per page"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    start_date: Optional[datetime] = Query(None, description="Filter start date"),
    end_date: Optional[datetime] = Query(None, description="Filter end date"),
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
) -> AuditEventsListResponse:
    """Enhanced audit events retrieval with service layer and advanced filtering"""
    
    request_logger = RequestLogger(logger, "get_audit_events")
    request_logger.log_request_start("GET", "/api/v1/audit/events", current_user["username"])
    
    try:
        # Initialize service layer
        audit_mgmt_service = AuditManagementService(db)
        
        # Convert string parameters to enums
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "invalid_event_type",
                        "message": f"Invalid event type: {event_type}",
                        "valid_types": [et.value for et in AuditEventType],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        
        severity_enum = None
        if severity:
            try:
                severity_enum = AuditSeverity(severity)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "invalid_severity",
                        "message": f"Invalid severity: {severity}",
                        "valid_severities": [s.value for s in AuditSeverity],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        
        # Get events through service layer (with caching)
        events_result = await audit_mgmt_service.get_audit_events(
            page=page,
            limit=limit,
            event_type=event_type_enum,
            user_id=user_id,
            severity=severity_enum,
            start_date=start_date,
            end_date=end_date,
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        # Convert to response format
        event_responses = []
        for event_data in events_result["events"]:
            event_responses.append(AuditEventResponse(**event_data))
        
        response = AuditEventsListResponse(
            events=event_responses,
            total=events_result["total"],
            page=events_result["page"],
            limit=events_result["limit"],
            total_pages=events_result["total_pages"],
            filters=events_result["filters"],
            metadata=events_result["metadata"]
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Audit events retrieval successful via service layer",
            extra={
                "total_events": events_result["total"],
                "returned_events": len(event_responses),
                "filters_applied": bool(event_type or user_id or severity or start_date or end_date),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except AuditManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Audit events retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
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
            "Audit events retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving audit events",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/statistics",
    response_model=AuditStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Audit Statistics",
    description="""
    Get comprehensive audit statistics with analytics and trends.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 10-minute TTL
    - ✅ Advanced analytics and trend analysis
    - ✅ Real-time metrics and compliance scoring
    - ✅ Enhanced statistics with risk assessment
    """,
    responses={
        200: {"description": "Audit statistics retrieved successfully", "model": AuditStatisticsResponse}
    }
)
async def get_audit_statistics(
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
) -> AuditStatisticsResponse:
    """Enhanced audit statistics with service layer and comprehensive analytics"""
    
    request_logger = RequestLogger(logger, "get_audit_statistics")
    request_logger.log_request_start("GET", "/api/v1/audit/statistics", current_user["username"])
    
    try:
        # Initialize service layer
        audit_mgmt_service = AuditManagementService(db)
        
        # Get statistics through service layer (with caching)
        stats_result = await audit_mgmt_service.get_audit_statistics(
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        response = AuditStatisticsResponse(**stats_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Audit statistics retrieval successful via service layer",
            extra={
                "total_events": stats_result.get("total_events", 0),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except AuditManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Audit statistics retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
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
            "Audit statistics retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving audit statistics",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.post(
    "/search",
    response_model=AuditEventsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Audit Events",
    description="""
    Search audit events with advanced filtering and caching.
    
    **Phase 1 & 2 Features:**
    - ✅ Advanced search with multiple criteria
    - ✅ Redis caching for search results
    - ✅ Enhanced search with correlation analysis
    - ✅ Comprehensive validation and error handling
    """,
    responses={
        200: {"description": "Audit search completed successfully", "model": AuditEventsListResponse}
    }
)
async def search_audit_events(
    search_request: AuditSearchRequest,
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
) -> AuditEventsListResponse:
    """Enhanced audit search with service layer and advanced filtering"""
    
    request_logger = RequestLogger(logger, f"search_audit_events_{search_request.query}")
    request_logger.log_request_start("POST", "/api/v1/audit/search", current_user["username"])
    
    try:
        # Initialize service layer
        audit_mgmt_service = AuditManagementService(db)
        
        # Convert event types to enums
        event_type_enums = None
        if search_request.event_types:
            try:
                event_type_enums = [AuditEventType(et) for et in search_request.event_types]
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "invalid_event_type",
                        "message": f"Invalid event type: {str(e)}",
                        "valid_types": [et.value for et in AuditEventType],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        
        # Search through service layer (with caching)
        search_result = await audit_mgmt_service.search_audit_events(
            query=search_request.query,
            page=search_request.page,
            limit=search_request.limit,
            start_date=search_request.start_date,
            end_date=search_request.end_date,
            event_types=event_type_enums,
            user_ids=search_request.user_ids,
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        # Convert to response format
        event_responses = []
        for event_data in search_result["events"]:
            event_responses.append(AuditEventResponse(**event_data))
        
        response = AuditEventsListResponse(
            events=event_responses,
            total=search_result["total"],
            page=search_result["page"],
            limit=search_result["limit"],
            total_pages=search_result["total_pages"],
            filters=search_result["search_criteria"],
            metadata=search_result["metadata"]
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Audit search successful via service layer",
            extra={
                "query": search_request.query,
                "total_results": search_result["total"],
                "returned_results": len(event_responses),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except AuditManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Audit search failed via service layer",
            extra={
                "query": search_request.query,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
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
            "Audit search error via service layer",
            extra={
                "query": search_request.query,
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred during audit search",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/verify/{entry_id}",
    response_model=AuditVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Audit Entry",
    description="""
    Verify audit entry integrity with comprehensive checks.
    
    **Phase 1 & 2 Features:**
    - ✅ Comprehensive integrity verification
    - ✅ Hash, timestamp, and signature validation
    - ✅ Chain integrity checking
    - ✅ Enhanced verification metadata
    """,
    responses={
        200: {"description": "Audit entry verified successfully", "model": AuditVerificationResponse}
    }
)
async def verify_audit_entry(
    entry_id: str,
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> AuditVerificationResponse:
    """Enhanced audit entry verification with service layer and comprehensive checks"""
    
    request_logger = RequestLogger(logger, f"verify_audit_entry_{entry_id}")
    request_logger.log_request_start("GET", f"/api/v1/audit/verify/{entry_id}", current_user["username"])
    
    try:
        # Initialize service layer
        audit_mgmt_service = AuditManagementService(db)
        
        # Verify through service layer
        verification_result = await audit_mgmt_service.verify_audit_entry(
            entry_id=entry_id,
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        response = AuditVerificationResponse(**verification_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Audit entry verification successful via service layer",
            extra={
                "entry_id": entry_id,
                "is_valid": verification_result.get("is_valid", False),
                "verified_by": current_user["username"]
            }
        )
        
        return response
        
    except AuditManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Audit entry verification failed via service layer",
            extra={
                "entry_id": entry_id,
                "error_code": e.error_code,
                "error_message": e.message,
                "verified_by": current_user["username"]
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
            "Audit entry verification error via service layer",
            extra={
                "entry_id": entry_id,
                "error": str(e),
                "verified_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred during audit verification",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/compliance/report",
    response_model=ComplianceReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Compliance Report",
    description="""
    Generate comprehensive compliance report with analytics.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 30-minute TTL
    - ✅ Advanced compliance analytics and scoring
    - ✅ Risk assessment and recommendations
    - ✅ Comprehensive audit trail for data export
    """,
    responses={
        200: {"description": "Compliance report generated successfully", "model": ComplianceReportResponse}
    }
)
async def get_compliance_report(
    request: Request,
    start_date: Optional[datetime] = Query(None, description="Report start date"),
    end_date: Optional[datetime] = Query(None, description="Report end date"),
    current_user = Depends(require_admin_permissions),
    db: Session = Depends(get_db)
) -> ComplianceReportResponse:
    """Enhanced compliance report generation with service layer and comprehensive analytics"""
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_logger = RequestLogger(logger, "get_compliance_report")
    request_logger.log_request_start("GET", "/api/v1/audit/compliance/report", current_user["username"])
    
    try:
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Initialize service layer
        audit_mgmt_service = AuditManagementService(db)
        
        # Generate report through service layer (with caching)
        report_result = await audit_mgmt_service.get_compliance_report(
            start_date=start_date,
            end_date=end_date,
            current_user_id=current_user["id"],
            current_username=current_user["username"],
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        response = ComplianceReportResponse(**report_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Compliance report generation successful via service layer",
            extra={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "event_count": report_result.get("summary", {}).get("total_events", 0),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except AuditManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Compliance report generation failed via service layer",
            extra={
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
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
            "Compliance report generation error via service layer",
            extra={
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred during compliance report generation",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/event-types",
    response_model=AuditEventTypesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Audit Event Types",
    description="""
    Get available audit event types and severity levels with metadata.
    
    **Phase 1 & 2 Features:**
    - ✅ Enhanced event types with categories and recommendations
    - ✅ Severity levels with colors and priorities
    - ✅ Comprehensive configuration metadata
    """,
    responses={
        200: {"description": "Audit event types retrieved successfully", "model": AuditEventTypesResponse}
    }
)
async def get_audit_event_types(
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
) -> AuditEventTypesResponse:
    """Enhanced audit event types with service layer and comprehensive metadata"""
    
    request_logger = RequestLogger(logger, "get_audit_event_types")
    request_logger.log_request_start("GET", "/api/v1/audit/event-types", current_user["username"])
    
    try:
        # Initialize service layer
        audit_mgmt_service = AuditManagementService(db)
        
        # Get event types through service layer
        event_types_result = await audit_mgmt_service.get_audit_event_types(
            current_user_id=current_user["id"],
            current_username=current_user["username"]
        )
        
        response = AuditEventTypesResponse(**event_types_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Audit event types retrieval successful via service layer",
            extra={
                "event_types_count": len(event_types_result["event_types"]),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except AuditManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Audit event types retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user["username"]
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
            "Audit event types retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving audit event types",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# PHASE 3: DATA ENRICHMENT ENDPOINTS FOR AUDIT INVESTIGATION

class UserLookupResponse(BaseModel):
    """Response model for user lookup"""
    users: Dict[int, Dict[str, Any]] = Field(..., description="User lookup data by ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Lookup metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "users": {
                    "1": {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@example.com",
                        "role": "administrator",
                        "display_name": "Administrator"
                    },
                    "2": {
                        "id": 2,
                        "username": "operator",
                        "email": "operator@example.com", 
                        "role": "manager",
                        "display_name": "System Operator"
                    }
                },
                "metadata": {
                    "total_users": 2,
                    "requested_by": "admin",
                    "timestamp": "2025-01-01T10:30:00Z"
                }
            }
        }


class TargetLookupResponse(BaseModel):
    """Response model for target lookup"""
    targets: Dict[str, Dict[str, Any]] = Field(..., description="Target lookup data by ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Lookup metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "targets": {
                    "123": {
                        "id": 123,
                        "name": "Server-01",
                        "target_type": "system",
                        "os_type": "linux",
                        "environment": "production",
                        "display_name": "Server-01 (Linux Production)"
                    },
                    "124": {
                        "id": 124,
                        "name": "DB-Server",
                        "target_type": "database",
                        "os_type": "linux",
                        "environment": "production",
                        "display_name": "DB-Server (Database Production)"
                    }
                },
                "metadata": {
                    "total_targets": 2,
                    "requested_by": "admin",
                    "timestamp": "2025-01-01T10:30:00Z"
                }
            }
        }


@router.get(
    "/lookups/users",
    response_model=UserLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User Lookup Data",
    description="""
    Get user lookup data for audit event enrichment.
    
    **Purpose:**
    - Provides user ID to name mapping for audit investigation
    - Enables user-friendly display of audit events
    - Supports bulk lookup for efficient data enrichment
    """,
    responses={
        200: {"description": "User lookup data retrieved successfully", "model": UserLookupResponse}
    }
)
async def get_user_lookups(
    user_ids: Optional[str] = Query(None, description="Comma-separated list of user IDs to lookup"),
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
) -> UserLookupResponse:
    """Get user lookup data for audit event enrichment"""
    
    request_logger = RequestLogger(logger, "get_user_lookups")
    request_logger.log_request_start("GET", "/api/v1/audit/lookups/users", current_user["username"])
    
    try:
        from app.services.user_service import UserService
        
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
        
        response = UserLookupResponse(
            users=users_data,
            metadata={
                "total_users": len(users_data),
                "requested_by": current_user["username"],
                "timestamp": datetime.utcnow().isoformat(),
                "filtered": bool(user_ids)
            }
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "User lookup data retrieval successful",
            extra={
                "users_count": len(users_data),
                "filtered": bool(user_ids),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except HTTPException:
        raise
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "User lookup data retrieval error",
            extra={
                "error": str(e),
                "user_ids": user_ids,
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving user lookup data",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/lookups/targets",
    response_model=TargetLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Target Lookup Data",
    description="""
    Get target lookup data for audit event enrichment.
    
    **Purpose:**
    - Provides target ID to name mapping for audit investigation
    - Enables user-friendly display of audit events
    - Supports bulk lookup for efficient data enrichment
    """,
    responses={
        200: {"description": "Target lookup data retrieved successfully", "model": TargetLookupResponse}
    }
)
async def get_target_lookups(
    target_ids: Optional[str] = Query(None, description="Comma-separated list of target IDs to lookup"),
    current_user = Depends(require_audit_permissions),
    db: Session = Depends(get_db)
) -> TargetLookupResponse:
    """Get target lookup data for audit event enrichment"""
    
    request_logger = RequestLogger(logger, "get_target_lookups")
    request_logger.log_request_start("GET", "/api/v1/audit/lookups/targets", current_user["username"])
    
    try:
        from app.services.universal_target_service import UniversalTargetService
        
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
        target_service = UniversalTargetService(db)
        
        if target_target_ids:
            # Get specific targets
            targets_data = {}
            for target_id in target_target_ids:
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
        else:
            # Get all targets (limited for performance)
            targets = target_service.get_targets_summary()
            targets_data = {}
            for target in targets:
                targets_data[str(target["id"])] = {
                    "id": target["id"],
                    "name": target["name"],
                    "target_type": target["target_type"],
                    "os_type": target["os_type"],
                    "environment": target["environment"],
                    "display_name": f"{target['name']} ({target['target_type'].title()} {target['environment'].title()})",
                    "is_active": target["is_active"],
                    "status": target["status"]
                }
        
        response = TargetLookupResponse(
            targets=targets_data,
            metadata={
                "total_targets": len(targets_data),
                "requested_by": current_user["username"],
                "timestamp": datetime.utcnow().isoformat(),
                "filtered": bool(target_ids)
            }
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Target lookup data retrieval successful",
            extra={
                "targets_count": len(targets_data),
                "filtered": bool(target_ids),
                "requested_by": current_user["username"]
            }
        )
        
        return response
        
    except HTTPException:
        raise
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Target lookup data retrieval error",
            extra={
                "error": str(e),
                "target_ids": target_ids,
                "requested_by": current_user["username"]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving target lookup data",
                "timestamp": datetime.utcnow().isoformat()
            }
        )