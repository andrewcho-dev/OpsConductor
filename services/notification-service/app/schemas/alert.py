"""
Alert schemas for API requests and responses
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.notification import AlertSeverity, AlertStatus


class AlertRuleBase(BaseModel):
    """Base alert rule schema"""
    name: str = Field(..., description="Alert rule name")
    description: Optional[str] = Field(None, description="Alert rule description")
    event_type: str = Field(..., description="Event type to monitor")
    conditions: Dict[str, Any] = Field(..., description="Alert conditions")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    is_active: bool = Field(True, description="Whether the rule is active")
    
    # Notification settings
    notification_template_id: Optional[int] = Field(None, description="Template for notifications")
    recipients: List[str] = Field(..., description="List of notification recipients")
    
    # Throttling settings
    throttle_minutes: int = Field(0, description="Minutes to throttle repeated alerts")
    max_alerts_per_hour: Optional[int] = Field(None, description="Maximum alerts per hour")
    
    template_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")


class AlertRuleCreate(AlertRuleBase):
    """Schema for creating an alert rule"""
    pass


class AlertRuleUpdate(BaseModel):
    """Schema for updating an alert rule"""
    name: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    severity: Optional[AlertSeverity] = None
    is_active: Optional[bool] = None
    notification_template_id: Optional[int] = None
    recipients: Optional[List[str]] = None
    throttle_minutes: Optional[int] = None
    max_alerts_per_hour: Optional[int] = None
    template_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class AlertRuleResponse(AlertRuleBase):
    """Schema for alert rule responses"""
    id: int
    rule_uuid: UUID
    
    # Statistics
    total_alerts: int = 0
    last_triggered_at: Optional[datetime] = None
    
    # Audit fields
    created_by: int
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlertLogBase(BaseModel):
    """Base alert log schema"""
    alert_title: str = Field(..., description="Alert title")
    alert_message: str = Field(..., description="Alert message")
    severity: AlertSeverity = Field(..., description="Alert severity")
    status: AlertStatus = Field(AlertStatus.OPEN, description="Alert status")
    event_data: Dict[str, Any] = Field(..., description="Event data that triggered the alert")
    context_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class AlertLogResponse(AlertLogBase):
    """Schema for alert log responses"""
    id: int
    log_uuid: UUID
    rule_id: int
    correlation_id: Optional[UUID] = None
    
    # Notification tracking
    notifications_sent: int = 0
    notification_ids: List[int] = Field(default_factory=list)
    
    # Resolution tracking
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    
    # Audit fields
    created_by: int
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True