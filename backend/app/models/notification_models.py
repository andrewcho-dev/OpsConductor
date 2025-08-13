from sqlalchemy import (
    Column, Integer, String, Text, JSON, DateTime, Boolean, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.database import Base


class NotificationTemplate(Base):
    """Email notification templates for system alerts"""
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    subject_template = Column(String(200), nullable=False)
    body_template = Column(Text, nullable=False)
    template_type = Column(
        String(50), nullable=False, default="email"
    )  # email, sms, webhook
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    def __repr__(self):
        return (f"<NotificationTemplate(name='{self.name}', "
                f"type='{self.template_type}')>")


class NotificationLog(Base):
    """Log of all sent notifications for audit trail"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=True)
    notification_type = Column(String(50), nullable=False)  # email, sms, webhook, system
    recipient = Column(String(200), nullable=False)  # email address, phone, webhook URL
    subject = Column(String(200), nullable=True)
    body = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, failed, cancelled
    error_message = Column(Text, nullable=True)
    context_metadata = Column(JSON, nullable=True)  # Additional context data
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    # Relationships
    template = relationship("NotificationTemplate", backref="notification_logs")
    
    def __repr__(self):
        return f"<NotificationLog(type='{self.notification_type}', recipient='{self.recipient}', status='{self.status}')>"


class AlertRule(Base):
    """Rules for triggering automated alerts"""
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    alert_type = Column(String(50), nullable=False)  # job_failure, system_error, performance, security
    trigger_condition = Column(JSON, nullable=False)  # Condition configuration
    notification_template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=True)
    recipients = Column(JSON, nullable=False)  # List of recipient emails
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    template = relationship("NotificationTemplate", backref="alert_rules")
    
    def __repr__(self):
        return f"<AlertRule(name='{self.name}', type='{self.alert_type}', active={self.is_active})>"


class AlertLog(Base):
    """Log of triggered alerts"""
    __tablename__ = "alert_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default="info")  # info, warning, error, critical
    message = Column(Text, nullable=False)
    context_data = Column(JSON, nullable=True)  # Additional context
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    # Relationships
    alert_rule = relationship("AlertRule", backref="alert_logs")
    
    def __repr__(self):
        return f"<AlertLog(type='{self.alert_type}', severity='{self.severity}', resolved={self.is_resolved})>"
