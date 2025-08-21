"""
Audit event models for Audit Events Service
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from app.core.database import Base
import uuid


class EventType(str, enum.Enum):
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


class EventSeverity(str, enum.Enum):
    """Event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(str, enum.Enum):
    """Event categories for classification"""
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


class AuditEvent(Base):
    """
    Main audit event model for comprehensive event tracking
    """
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Event Classification
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50), nullable=False, index=True)
    event_severity = Column(String(20), nullable=False, default="medium", index=True)
    
    # Event Details
    event_name = Column(String(255), nullable=False)
    event_description = Column(Text, nullable=True)
    event_message = Column(Text, nullable=True)
    
    # Source Information
    service_name = Column(String(100), nullable=False, index=True)
    service_version = Column(String(50), nullable=True)
    
    # User Context
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(255), nullable=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    
    # Session Context
    session_id = Column(String(255), nullable=True, index=True)
    correlation_id = Column(String(255), nullable=True, index=True)
    
    # Request Context
    ip_address = Column(INET, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_url = Column(Text, nullable=True)
    request_headers = Column(JSONB, nullable=True)
    
    # Resource Context
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    resource_name = Column(String(255), nullable=True, index=True)
    
    # Event Data
    event_data = Column(JSONB, nullable=True)
    before_data = Column(JSONB, nullable=True)  # Data before change
    after_data = Column(JSONB, nullable=True)   # Data after change
    
    # Result Information
    success = Column(Boolean, nullable=True, index=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Compliance and Security
    compliance_tags = Column(JSONB, nullable=True, default=list)
    security_level = Column(String(20), nullable=True, index=True)
    data_classification = Column(String(50), nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Retention and Archival
    retention_date = Column(DateTime(timezone=True), nullable=True, index=True)
    is_archived = Column(Boolean, default=False, index=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    
    # Event Integrity
    event_hash = Column(String(64), nullable=True)  # SHA-256 hash for integrity
    event_signature = Column(Text, nullable=True)   # Digital signature


# Create composite indexes for common queries
Index('idx_audit_events_user_time', AuditEvent.user_id, AuditEvent.event_timestamp)
Index('idx_audit_events_service_time', AuditEvent.service_name, AuditEvent.event_timestamp)
Index('idx_audit_events_type_time', AuditEvent.event_type, AuditEvent.event_timestamp)
Index('idx_audit_events_category_severity', AuditEvent.event_category, AuditEvent.event_severity)
Index('idx_audit_events_resource', AuditEvent.resource_type, AuditEvent.resource_id)
Index('idx_audit_events_ip_time', AuditEvent.ip_address, AuditEvent.event_timestamp)


class SecurityAlert(Base):
    """
    Security alerts generated from audit events
    """
    __tablename__ = "security_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Alert Information
    alert_type = Column(String(100), nullable=False, index=True)
    alert_severity = Column(String(20), nullable=False, index=True)
    alert_title = Column(String(255), nullable=False)
    alert_description = Column(Text, nullable=True)
    
    # Related Events
    related_event_ids = Column(JSONB, nullable=True, default=list)
    event_count = Column(Integer, default=1, nullable=False)
    
    # Alert Context
    user_id = Column(Integer, nullable=True, index=True)
    ip_address = Column(INET, nullable=True, index=True)
    service_name = Column(String(100), nullable=True, index=True)
    
    # Alert Status
    status = Column(String(20), default="open", nullable=False, index=True)  # open, investigating, resolved, false_positive
    assigned_to = Column(Integer, nullable=True)  # User ID
    
    # Alert Data
    alert_data = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    first_occurrence = Column(DateTime(timezone=True), nullable=False, index=True)
    last_occurrence = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)


class ComplianceReport(Base):
    """
    Compliance reports generated from audit events
    """
    __tablename__ = "compliance_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Report Information
    report_name = Column(String(255), nullable=False)
    report_type = Column(String(100), nullable=False, index=True)
    compliance_standard = Column(String(50), nullable=False, index=True)  # SOX, HIPAA, PCI-DSS, etc.
    
    # Report Period
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Report Status
    status = Column(String(20), default="generating", nullable=False, index=True)  # generating, completed, failed
    
    # Report Data
    report_data = Column(JSONB, nullable=True)
    summary_stats = Column(JSONB, nullable=True, default=dict)
    
    # Report Files
    report_file_path = Column(String(500), nullable=True)
    report_format = Column(String(20), nullable=True)  # pdf, csv, json, xml
    
    # Generation Info
    generated_by = Column(Integer, nullable=False, index=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EventStream(Base):
    """
    Real-time event streaming configuration
    """
    __tablename__ = "event_streams"

    id = Column(Integer, primary_key=True, index=True)
    stream_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Stream Configuration
    stream_name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Stream Filters
    event_types = Column(JSONB, nullable=True, default=list)
    event_categories = Column(JSONB, nullable=True, default=list)
    severity_levels = Column(JSONB, nullable=True, default=list)
    service_names = Column(JSONB, nullable=True, default=list)
    
    # Stream Destination
    destination_type = Column(String(50), nullable=False)  # webhook, kafka, sqs, etc.
    destination_config = Column(JSONB, nullable=False)
    
    # Stream Status
    is_active = Column(Boolean, default=True, index=True)
    last_event_sent = Column(DateTime(timezone=True), nullable=True)
    events_sent_count = Column(Integer, default=0, nullable=False)
    
    # Error Handling
    retry_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=False)


class AuditTrail(Base):
    """
    Audit trail for tracking changes to audit configuration
    """
    __tablename__ = "audit_trails"

    id = Column(Integer, primary_key=True, index=True)
    trail_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Trail Information
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=False, index=True)
    
    # Change Information
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    changes = Column(JSONB, nullable=True)
    
    # Context
    user_id = Column(Integer, nullable=False, index=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)