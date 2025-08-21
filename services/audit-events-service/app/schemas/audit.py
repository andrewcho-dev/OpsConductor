"""
Pydantic schemas for Audit Events Service
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, IPvAnyAddress
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class EventTypeEnum(str, Enum):
    """Event type enumeration"""
    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    
    # User Management Events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    USER_ROLES_ASSIGNED = "user_roles_assigned"
    USER_ROLES_REMOVED = "user_roles_removed"
    
    # Job Events
    JOB_CREATED = "job_created"
    JOB_UPDATED = "job_updated"
    JOB_DELETED = "job_deleted"
    JOB_EXECUTED = "job_executed"
    JOB_SCHEDULED = "job_scheduled"
    JOB_CANCELLED = "job_cancelled"
    JOB_FAILED = "job_failed"
    JOB_COMPLETED = "job_completed"
    
    # Target Events
    TARGET_CREATED = "target_created"
    TARGET_UPDATED = "target_updated"
    TARGET_DELETED = "target_deleted"
    TARGET_CONNECTION_TEST = "target_connection_test"
    TARGET_CREDENTIALS_UPDATED = "target_credentials_updated"
    
    # System Events
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_ERROR = "service_error"
    CONFIGURATION_CHANGED = "configuration_changed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    
    # Security Events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    SECURITY_POLICY_VIOLATION = "security_policy_violation"
    
    # Data Events
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    
    # API Events
    API_REQUEST = "api_request"
    API_ERROR = "api_error"
    API_RATE_LIMIT_EXCEEDED = "api_rate_limit_exceeded"


class EventSeverityEnum(str, Enum):
    """Event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategoryEnum(str, Enum):
    """Event categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    USER_MANAGEMENT = "user_management"
    JOB_MANAGEMENT = "job_management"
    TARGET_MANAGEMENT = "target_management"
    SYSTEM = "system"
    SECURITY = "security"
    DATA = "data"
    API = "api"
    COMPLIANCE = "compliance"


class AlertStatusEnum(str, Enum):
    """Security alert status"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


# =============================================================================
# Base Schemas
# =============================================================================

class AuditEventBase(BaseModel):
    """Base schema for audit events"""
    event_type: str = Field(..., description="Type of event")
    event_category: str = Field(..., description="Event category")
    event_severity: str = Field("medium", description="Event severity")
    event_name: str = Field(..., description="Human-readable event name")
    event_description: Optional[str] = Field(None, description="Event description")
    event_message: Optional[str] = Field(None, description="Event message")
    service_name: str = Field(..., description="Source service name")
    service_version: Optional[str] = Field(None, description="Source service version")


class SecurityAlertBase(BaseModel):
    """Base schema for security alerts"""
    alert_type: str = Field(..., description="Type of alert")
    alert_severity: str = Field(..., description="Alert severity")
    alert_title: str = Field(..., description="Alert title")
    alert_description: Optional[str] = Field(None, description="Alert description")


# =============================================================================
# Request Schemas
# =============================================================================

class AuditEventCreateRequest(AuditEventBase):
    """Schema for creating audit events"""
    user_id: Optional[int] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    user_email: Optional[str] = Field(None, description="User email")
    session_id: Optional[str] = Field(None, description="Session ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    request_method: Optional[str] = Field(None, description="HTTP method")
    request_url: Optional[str] = Field(None, description="Request URL")
    request_headers: Optional[Dict[str, Any]] = Field(None, description="Request headers")
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    resource_name: Optional[str] = Field(None, description="Resource name")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Event data")
    before_data: Optional[Dict[str, Any]] = Field(None, description="Data before change")
    after_data: Optional[Dict[str, Any]] = Field(None, description="Data after change")
    success: Optional[bool] = Field(None, description="Operation success")
    error_code: Optional[str] = Field(None, description="Error code")
    error_message: Optional[str] = Field(None, description="Error message")
    compliance_tags: List[str] = Field(default_factory=list, description="Compliance tags")
    security_level: Optional[str] = Field(None, description="Security level")
    data_classification: Optional[str] = Field(None, description="Data classification")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Event tags")
    event_timestamp: Optional[datetime] = Field(None, description="Event timestamp")


class EventSearchRequest(BaseModel):
    """Schema for event search requests"""
    event_types: Optional[List[str]] = Field(None, description="Filter by event types")
    event_categories: Optional[List[str]] = Field(None, description="Filter by categories")
    severity_levels: Optional[List[str]] = Field(None, description="Filter by severity")
    service_names: Optional[List[str]] = Field(None, description="Filter by services")
    user_ids: Optional[List[int]] = Field(None, description="Filter by user IDs")
    ip_addresses: Optional[List[str]] = Field(None, description="Filter by IP addresses")
    resource_types: Optional[List[str]] = Field(None, description="Filter by resource types")
    resource_ids: Optional[List[str]] = Field(None, description="Filter by resource IDs")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    success: Optional[bool] = Field(None, description="Filter by success status")
    search_text: Optional[str] = Field(None, description="Text search in event data")
    compliance_tags: Optional[List[str]] = Field(None, description="Filter by compliance tags")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")


class ComplianceReportRequest(BaseModel):
    """Schema for compliance report requests"""
    report_name: str = Field(..., description="Report name")
    report_type: str = Field(..., description="Report type")
    compliance_standard: str = Field(..., description="Compliance standard")
    start_date: datetime = Field(..., description="Report start date")
    end_date: datetime = Field(..., description="Report end date")
    report_format: str = Field("json", description="Report format")
    include_details: bool = Field(True, description="Include detailed events")
    filters: Optional[EventSearchRequest] = Field(None, description="Additional filters")


class SecurityAlertUpdateRequest(BaseModel):
    """Schema for updating security alerts"""
    status: Optional[AlertStatusEnum] = Field(None, description="Alert status")
    assigned_to: Optional[int] = Field(None, description="Assigned user ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class EventStreamCreateRequest(BaseModel):
    """Schema for creating event streams"""
    stream_name: str = Field(..., description="Stream name")
    description: Optional[str] = Field(None, description="Stream description")
    event_types: List[str] = Field(default_factory=list, description="Event types to stream")
    event_categories: List[str] = Field(default_factory=list, description="Event categories to stream")
    severity_levels: List[str] = Field(default_factory=list, description="Severity levels to stream")
    service_names: List[str] = Field(default_factory=list, description="Service names to stream")
    destination_type: str = Field(..., description="Destination type")
    destination_config: Dict[str, Any] = Field(..., description="Destination configuration")


# =============================================================================
# Response Schemas
# =============================================================================

class AuditEventResponse(AuditEventBase):
    """Schema for audit event responses"""
    id: int
    event_uuid: UUID
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_email: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_url: Optional[str] = None
    request_headers: Optional[Dict[str, Any]] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None
    before_data: Optional[Dict[str, Any]] = None
    after_data: Optional[Dict[str, Any]] = None
    success: Optional[bool] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    compliance_tags: List[str] = Field(default_factory=list)
    security_level: Optional[str] = None
    data_classification: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    event_timestamp: datetime
    created_at: datetime
    retention_date: Optional[datetime] = None
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    event_hash: Optional[str] = None
    event_signature: Optional[str] = None

    class Config:
        from_attributes = True


class SecurityAlertResponse(SecurityAlertBase):
    """Schema for security alert responses"""
    id: int
    alert_uuid: UUID
    related_event_ids: List[int] = Field(default_factory=list)
    event_count: int
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    service_name: Optional[str] = None
    status: str
    assigned_to: Optional[int] = None
    alert_data: Dict[str, Any] = Field(default_factory=dict)
    first_occurrence: datetime
    last_occurrence: datetime
    created_at: datetime
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ComplianceReportResponse(BaseModel):
    """Schema for compliance report responses"""
    id: int
    report_uuid: UUID
    report_name: str
    report_type: str
    compliance_standard: str
    start_date: datetime
    end_date: datetime
    status: str
    report_data: Optional[Dict[str, Any]] = None
    summary_stats: Dict[str, Any] = Field(default_factory=dict)
    report_file_path: Optional[str] = None
    report_format: Optional[str] = None
    generated_by: int
    generated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class EventStreamResponse(BaseModel):
    """Schema for event stream responses"""
    id: int
    stream_uuid: UUID
    stream_name: str
    description: Optional[str] = None
    event_types: List[str] = Field(default_factory=list)
    event_categories: List[str] = Field(default_factory=list)
    severity_levels: List[str] = Field(default_factory=list)
    service_names: List[str] = Field(default_factory=list)
    destination_type: str
    destination_config: Dict[str, Any]
    is_active: bool
    last_event_sent: Optional[datetime] = None
    events_sent_count: int
    retry_count: int
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Schema for event list responses"""
    events: List[AuditEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SecurityAlertListResponse(BaseModel):
    """Schema for security alert list responses"""
    alerts: List[SecurityAlertResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ComplianceReportListResponse(BaseModel):
    """Schema for compliance report list responses"""
    reports: List[ComplianceReportResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EventStatsResponse(BaseModel):
    """Schema for event statistics responses"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_category: Dict[str, int]
    events_by_severity: Dict[str, int]
    events_by_service: Dict[str, int]
    events_today: int
    events_this_week: int
    events_this_month: int
    top_users: List[Dict[str, Any]]
    top_ip_addresses: List[Dict[str, Any]]
    recent_security_alerts: List[SecurityAlertResponse]


class AuditHealthResponse(BaseModel):
    """Schema for audit service health responses"""
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime
    checks: Dict[str, Any]
    event_processing_stats: Dict[str, Any]


# =============================================================================
# Error Schemas
# =============================================================================

class AuditErrorResponse(BaseModel):
    """Schema for audit service error responses"""
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    service: str = "audit-events-service"
    timestamp: datetime