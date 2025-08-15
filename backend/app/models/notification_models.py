from sqlalchemy import (
    Column, Integer, String, Text, JSON, DateTime, Boolean, ForeignKey, Enum, text, Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    metric_type = Column(String(50), nullable=False)
    condition = Column(String(20), nullable=False)  # gt, lt, eq, ne, gte, lte
    threshold_value = Column(Float, nullable=False)  # DOUBLE PRECISION in database
    evaluation_period = Column(Integer, nullable=True, default=5)
    is_active = Column(Integer, nullable=True, default=1)  # Database uses INTEGER not BOOLEAN
    severity = Column(String(20), nullable=True, default='warning')
    notification_channels = Column(JSONB, nullable=True)
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AlertRule(name='{self.name}', metric='{self.metric_type}', active={self.is_active})>"


class AlertLog(Base):
    """Log of triggered alerts"""
    __tablename__ = "alert_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_uuid = Column(UUID, nullable=False, server_default=func.gen_random_uuid())
    alert_serial = Column(String(50), nullable=False, server_default=text("'ALERT-' || LPAD(nextval('alert_logs_id_seq')::text, 8, '0')"))
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=True)
    severity = Column(Enum('low', 'medium', 'high', 'critical', name='alert_severity'), nullable=False)
    status = Column(Enum('active', 'acknowledged', 'resolved', 'suppressed', name='alert_status'), nullable=False, default='active')
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(Integer, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(100), nullable=True)
    context_data = Column(JSONB, nullable=True)
    notification_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    alert_type = Column(String(50), nullable=False)
    
    # Relationships
    alert_rule = relationship("AlertRule", backref="alert_logs")
    
    def __repr__(self):
        return f"<AlertLog(type='{self.alert_type}', severity='{self.severity}', resolved={self.is_resolved})>"
