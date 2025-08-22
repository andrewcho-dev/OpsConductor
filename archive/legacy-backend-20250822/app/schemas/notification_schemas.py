from pydantic import BaseModel, EmailStr, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SYSTEM = "system"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    JOB_FAILURE = "job_failure"
    SYSTEM_ERROR = "system_error"
    PERFORMANCE = "performance"
    SECURITY = "security"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Base schemas
class NotificationTemplateBase(BaseModel):
    name: str
    subject_template: str
    body_template: str
    template_type: NotificationType = NotificationType.EMAIL
    description: Optional[str] = None


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    template_type: Optional[NotificationType] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class NotificationTemplateResponse(NotificationTemplateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailSendRequest(BaseModel):
    to_emails: Union[str, List[str]]
    subject: str
    body: str
    html_body: Optional[str] = None
    from_email: Optional[str] = None
    template_name: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None

    @validator('to_emails')
    def validate_emails(cls, v):
        if isinstance(v, str):
            v = [v]
        if not v:
            raise ValueError("At least one email address is required")
        return v


class EmailSendResponse(BaseModel):
    success: bool
    sent_count: int
    total_count: int
    errors: List[str] = []


class EmailTargetConfigRequest(BaseModel):
    target_id: Optional[int] = None

    @validator('target_id')
    def validate_target_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Target ID must be positive")
        return v


class EmailTargetConfigResponse(BaseModel):
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    encryption: Optional[str] = None
    health_status: Optional[str] = None
    is_configured: bool


class EligibleEmailTarget(BaseModel):
    id: int
    name: str
    host: str
    port: int
    encryption: str
    health_status: str
    username: Optional[str] = None
    is_healthy: bool


class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    alert_type: AlertType
    trigger_condition: Dict[str, Any]
    recipients: List[str]
    notification_template_id: Optional[int] = None

    @validator('recipients')
    def validate_recipients(cls, v):
        if not v:
            raise ValueError("At least one recipient is required")
        return v


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    alert_type: Optional[AlertType] = None
    trigger_condition: Optional[Dict[str, Any]] = None
    recipients: Optional[List[str]] = None
    notification_template_id: Optional[int] = None
    is_active: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertCreateRequest(BaseModel):
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    context_data: Optional[Dict[str, Any]] = None
    alert_rule_id: Optional[int] = None


class AlertResponse(BaseModel):
    id: int
    alert_rule_id: Optional[int]
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    context_data: Optional[Dict[str, Any]]
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertResolveRequest(BaseModel):
    resolved_by: str


class NotificationLogResponse(BaseModel):
    id: int
    template_id: Optional[int]
    notification_type: NotificationType
    recipient: str
    subject: Optional[str]
    body: Optional[str]
    status: NotificationStatus
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationLogFilter(BaseModel):
    status: Optional[NotificationStatus] = None
    notification_type: Optional[NotificationType] = None
    limit: int = 100
    offset: int = 0


class AlertLogFilter(BaseModel):
    severity: Optional[AlertSeverity] = None
    alert_type: Optional[AlertType] = None
    is_resolved: Optional[bool] = None
    limit: int = 100
    offset: int = 0


class NotificationStats(BaseModel):
    total_notifications: int
    sent_notifications: int
    failed_notifications: int
    pending_notifications: int
    total_alerts: int
    active_alerts: int
    resolved_alerts: int


class TestEmailRequest(BaseModel):
    to_email: EmailStr
    subject: str = "Test Email from EnableDRM"
    body: str = "This is a test email to verify SMTP configuration."
    html_body: Optional[str] = None


class TestEmailResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
