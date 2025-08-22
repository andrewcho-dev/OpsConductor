"""
Notification models for Notification Service
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import uuid


class NotificationType(str, enum.Enum):
    """Notification type enumeration"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str, enum.Enum):
    """Notification status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"
    EXPIRED = "expired"


class NotificationPriority(str, enum.Enum):
    """Notification priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AlertSeverity(str, enum.Enum):
    """Alert severity enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    """Alert status enumeration"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLOSED = "closed"


class NotificationTemplate(Base):
    """
    Notification template model for reusable notification formats
    """
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Template Information
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=False, default=NotificationType.EMAIL, index=True)
    
    # Template Content
    subject_template = Column(String(500), nullable=True)  # For email/SMS
    body_template = Column(Text, nullable=False)
    html_template = Column(Text, nullable=True)  # For HTML emails
    
    # Template Configuration
    variables = Column(JSONB, nullable=True, default=list)  # List of template variables
    default_values = Column(JSONB, nullable=True, default=dict)  # Default variable values
    
    # Template Metadata
    is_active = Column(Boolean, default=True, index=True)
    is_system = Column(Boolean, default=False)  # System template
    category = Column(String(100), nullable=True, index=True)
    
    # Usage Statistics
    usage_count = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Ownership
    created_by = Column(Integer, nullable=False, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Metadata
    template_metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    notifications = relationship("NotificationLog", back_populates="template")


class NotificationLog(Base):
    """
    Notification log model for tracking sent notifications
    """
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    notification_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Template Reference
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=True, index=True)
    
    # Notification Details
    notification_type = Column(String(50), nullable=False, index=True)
    recipient = Column(String(500), nullable=False, index=True)  # email, phone, webhook URL, etc.
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=True)
    html_body = Column(Text, nullable=True)
    
    # Status and Delivery
    status = Column(String(20), nullable=False, default=NotificationStatus.PENDING, index=True)
    priority = Column(Integer, default=5, nullable=False, index=True)  # 1-10, 10 is highest
    
    # Retry Configuration
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Delivery Information
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error Information
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    error_details = Column(JSONB, nullable=True)
    
    # Context Information
    user_id = Column(Integer, nullable=True, index=True)  # User who triggered the notification
    correlation_id = Column(String(255), nullable=True, index=True)  # For tracking related notifications
    event_type = Column(String(100), nullable=True, index=True)  # Event that triggered notification
    
    # Notification Data
    template_variables = Column(JSONB, nullable=True, default=dict)  # Variables used in template
    context_metadata = Column(JSONB, nullable=True, default=dict)    # Additional context data
    
    # External References
    external_id = Column(String(255), nullable=True, index=True)  # External service message ID
    external_status = Column(String(50), nullable=True)           # External service status
    
    # Metadata
    template_metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    template = relationship("NotificationTemplate", back_populates="notifications")


class AlertRule(Base):
    """
    Alert rule model for defining when to send notifications
    """
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Rule Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Rule Configuration
    event_types = Column(JSONB, nullable=False, default=list)  # Event types to monitor
    conditions = Column(JSONB, nullable=False, default=dict)   # Conditions to match
    
    # Alert Configuration
    severity = Column(String(20), nullable=False, default=AlertSeverity.MEDIUM, index=True)
    cooldown_minutes = Column(Integer, default=60, nullable=False)  # Cooldown between alerts
    
    # Notification Configuration
    notification_templates = Column(JSONB, nullable=False, default=list)  # Template IDs to use
    recipients = Column(JSONB, nullable=False, default=list)              # Recipients list
    
    # Rule Status
    is_active = Column(Boolean, default=True, index=True)
    is_paused = Column(Boolean, default=False, index=True)
    
    # Statistics
    trigger_count = Column(Integer, default=0, nullable=False)
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    last_alert_sent = Column(DateTime(timezone=True), nullable=True)
    
    # Ownership
    created_by = Column(Integer, nullable=False, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Metadata
    template_metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    alert_logs = relationship("AlertLog", back_populates="alert_rule", cascade="all, delete-orphan")


class AlertLog(Base):
    """
    Alert log model for tracking triggered alerts
    """
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    alert_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False, index=True)
    
    # Alert Information
    alert_title = Column(String(500), nullable=False)
    alert_message = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, index=True)
    
    # Alert Status
    status = Column(String(20), nullable=False, default=AlertStatus.OPEN, index=True)
    acknowledged_by = Column(Integer, nullable=True)  # User ID who acknowledged
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, nullable=True)      # User ID who resolved
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Trigger Information
    triggered_by_event = Column(String(100), nullable=True, index=True)
    event_data = Column(JSONB, nullable=True, default=dict)
    correlation_id = Column(String(255), nullable=True, index=True)
    
    # Notification Information
    notifications_sent = Column(Integer, default=0, nullable=False)
    notification_ids = Column(JSONB, nullable=True, default=list)  # Related notification log IDs
    
    # Metadata
    template_metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    alert_rule = relationship("AlertRule", back_populates="alert_logs")


class NotificationChannel(Base):
    """
    Notification channel model for managing delivery channels
    """
    __tablename__ = "notification_channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Channel Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    channel_type = Column(String(50), nullable=False, index=True)
    
    # Channel Configuration
    configuration = Column(JSONB, nullable=False, default=dict)  # Channel-specific config
    credentials = Column(JSONB, nullable=True, default=dict)     # Encrypted credentials
    
    # Channel Status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False, index=True)
    
    # Health Information
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(20), default="unknown")  # healthy, unhealthy, unknown
    health_message = Column(Text, nullable=True)
    
    # Usage Statistics
    messages_sent = Column(Integer, default=0, nullable=False)
    messages_failed = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Rate Limiting
    rate_limit_per_minute = Column(Integer, nullable=True)
    rate_limit_per_hour = Column(Integer, nullable=True)
    rate_limit_per_day = Column(Integer, nullable=True)
    
    # Ownership
    created_by = Column(Integer, nullable=False, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Metadata
    template_metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NotificationPreference(Base):
    """
    User notification preferences model
    """
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    preference_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # User Information
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    
    # Email Preferences
    email_enabled = Column(Boolean, default=True)
    email_address = Column(String(255), nullable=True)
    email_frequency = Column(String(20), default="immediate")  # immediate, hourly, daily, weekly
    
    # SMS Preferences
    sms_enabled = Column(Boolean, default=False)
    phone_number = Column(String(20), nullable=True)
    sms_frequency = Column(String(20), default="critical")  # never, critical, high, all
    
    # Push Notification Preferences
    push_enabled = Column(Boolean, default=True)
    push_frequency = Column(String(20), default="immediate")
    
    # In-App Notification Preferences
    in_app_enabled = Column(Boolean, default=True)
    
    # Event Type Preferences
    event_preferences = Column(JSONB, nullable=True, default=dict)  # Per-event-type preferences
    
    # Quiet Hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format
    quiet_hours_end = Column(String(5), nullable=True)    # HH:MM format
    quiet_hours_timezone = Column(String(50), default="UTC")
    
    # Metadata
    template_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NotificationQueue(Base):
    """
    Notification queue model for managing notification delivery queues
    """
    __tablename__ = "notification_queues"

    id = Column(Integer, primary_key=True, index=True)
    queue_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Queue Information
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    queue_type = Column(String(50), nullable=False, index=True)  # priority, fifo, delay
    
    # Queue Configuration
    max_size = Column(Integer, default=10000, nullable=False)
    current_size = Column(Integer, default=0, nullable=False)
    processing_rate = Column(Integer, default=100, nullable=False)  # Messages per minute
    
    # Queue Status
    is_active = Column(Boolean, default=True, index=True)
    is_paused = Column(Boolean, default=False, index=True)
    
    # Statistics
    messages_processed = Column(Integer, default=0, nullable=False)
    messages_failed = Column(Integer, default=0, nullable=False)
    average_processing_time = Column(Float, nullable=True)  # In seconds
    
    # Metadata
    template_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=True)