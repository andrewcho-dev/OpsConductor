"""
Notification schemas for API requests and responses
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from uuid import UUID
import enum

from app.models.notification import NotificationType, NotificationStatus, NotificationPriority


class NotificationBase(BaseModel):
    """Base notification schema"""
    notification_type: NotificationType = Field(..., description="Type of notification")
    recipient: str = Field(..., description="Recipient address (email, phone, etc.)")
    subject: Optional[str] = Field(None, description="Notification subject")
    message: str = Field(..., description="Notification message content")
    html_content: Optional[str] = Field(None, description="HTML content for rich notifications")
    priority: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Notification priority")
    scheduled_at: Optional[datetime] = Field(None, description="When to send the notification")
    expires_at: Optional[datetime] = Field(None, description="When the notification expires")
    template_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")


class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""
    template_id: Optional[int] = Field(None, description="Template to use for this notification")
    correlation_id: Optional[UUID] = Field(None, description="Correlation ID for tracking")
    
    @validator('recipient')
    def validate_recipient(cls, v, values):
        """Validate recipient format based on notification type"""
        notification_type = values.get('notification_type')
        if notification_type == NotificationType.EMAIL:
            # Basic email validation
            if '@' not in v or '.' not in v.split('@')[-1]:
                raise ValueError('Invalid email format')
        elif notification_type == NotificationType.SMS:
            # Basic phone number validation
            if not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                raise ValueError('Invalid phone number format')
        return v


class NotificationUpdate(BaseModel):
    """Schema for updating a notification"""
    subject: Optional[str] = None
    message: Optional[str] = None
    html_content: Optional[str] = None
    priority: Optional[NotificationPriority] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    template_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class NotificationResponse(NotificationBase):
    """Schema for notification responses"""
    id: int
    notification_uuid: UUID
    status: NotificationStatus
    template_id: Optional[int] = None
    correlation_id: Optional[UUID] = None
    
    # Delivery tracking
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # External service tracking
    external_id: Optional[str] = None
    external_status: Optional[str] = None
    
    # Audit fields
    created_by: int
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    """Schema for notification statistics"""
    total_notifications: int
    sent_notifications: int
    delivered_notifications: int
    failed_notifications: int
    pending_notifications: int
    success_rate: float
    
    class Config:
        from_attributes = True