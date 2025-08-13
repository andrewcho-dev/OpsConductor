from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.database import get_db
from ..services.notification_service import NotificationService
from ..services.system_service import SystemService
from ..schemas.notification_schemas import (
    NotificationTemplateCreate, NotificationTemplateUpdate, NotificationTemplateResponse,
    EmailSendRequest, EmailSendResponse, EmailTargetConfigRequest, EmailTargetConfigResponse,
    EligibleEmailTarget, AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse, AlertCreateRequest,
    AlertResponse, AlertResolveRequest, NotificationLogResponse,
    NotificationStats, TestEmailRequest, TestEmailResponse
)
from ..models.notification_models import NotificationTemplate, NotificationLog, AlertRule, AlertLog

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# Email Target Configuration endpoints
@router.get("/email-targets/eligible", response_model=List[EligibleEmailTarget])
def get_eligible_email_targets(db: Session = Depends(get_db)):
    """Get list of eligible email targets (SMTP targets that are configured)"""
    notification_service = NotificationService(db)
    targets = notification_service.get_eligible_email_targets()
    
    return [
        EligibleEmailTarget(
            id=target['id'],
            name=target['name'],
            host=target['host'],
            port=target['port'],
            encryption=target['encryption'],
            health_status=target['health_status'],
            username=target.get('username'),
            is_healthy=target['health_status'] == 'healthy'
        )
        for target in targets
    ]


@router.get("/email-target/config", response_model=EmailTargetConfigResponse)
def get_email_target_config(db: Session = Depends(get_db)):
    """Get current email target configuration"""
    notification_service = NotificationService(db)
    config = notification_service.get_email_target_config()
    
    return EmailTargetConfigResponse(
        target_id=config.get('target_id'),
        target_name=config.get('target_name'),
        host=config.get('host'),
        port=config.get('port'),
        encryption=config.get('encryption'),
        health_status=config.get('health_status'),
        is_configured=bool(config.get('target_id'))
    )


@router.post("/email-target/config", response_model=EmailTargetConfigResponse)
def update_email_target_config(
    config: EmailTargetConfigRequest,
    db: Session = Depends(get_db)
):
    """Update email target configuration"""
    notification_service = NotificationService(db)
    
    # Update email target setting
    result = notification_service.set_email_target(config.target_id)
    
    return EmailTargetConfigResponse(
        target_id=result.get('target_id'),
        target_name=result.get('target_name'),
        host=result.get('host'),
        port=result.get('port'),
        encryption=result.get('encryption'),
        health_status=result.get('health_status'),
        is_configured=bool(result.get('target_id'))
    )


@router.post("/email-target/test", response_model=TestEmailResponse)
def test_email_target(
    test_request: TestEmailRequest,
    db: Session = Depends(get_db)
):
    """Test email target configuration by sending a test email"""
    notification_service = NotificationService(db)
    
    # Check if email target is configured
    config = notification_service.get_email_target_config()
    if not config.get('target_id'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email target not configured. Please select an email target first."
        )
    
    # Send test email
    result = notification_service.send_email(
        to_emails=test_request.to_email,
        subject=test_request.subject,
        body=test_request.body,
        html_body=test_request.html_body
    )
    
    if result['success']:
        return TestEmailResponse(
            success=True,
            message="Test email sent successfully",
            details=result
        )
    else:
        return TestEmailResponse(
            success=False,
            message="Failed to send test email",
            details=result
        )


# Email sending endpoints
@router.post("/email/send", response_model=EmailSendResponse)
def send_email(
    email_request: EmailSendRequest,
    db: Session = Depends(get_db)
):
    """Send email via SMTP"""
    notification_service = NotificationService(db)
    
    if email_request.template_name:
        # Send templated email
        if not email_request.template_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template data required when using template"
            )
        
        result = notification_service.send_templated_email(
            template_name=email_request.template_name,
            to_emails=email_request.to_emails,
            template_data=email_request.template_data,
            from_email=email_request.from_email
        )
    else:
        # Send direct email
        result = notification_service.send_email(
            to_emails=email_request.to_emails,
            subject=email_request.subject,
            body=email_request.body,
            html_body=email_request.html_body,
            from_email=email_request.from_email,
            attachments=email_request.attachments
        )
    
    return EmailSendResponse(
        success=result['success'],
        sent_count=result.get('sent_count', 0),
        total_count=result.get('total_count', 0),
        errors=result.get('errors', [])
    )


# Notification templates endpoints
@router.get("/templates", response_model=List[NotificationTemplateResponse])
def get_notification_templates(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get notification templates"""
    from sqlalchemy import select
    
    stmt = select(NotificationTemplate)
    if active_only:
        stmt = stmt.where(NotificationTemplate.is_active == True)
    stmt = stmt.order_by(NotificationTemplate.name)
    
    templates = db.execute(stmt).scalars().all()
    return list(templates)


@router.post("/templates", response_model=NotificationTemplateResponse)
def create_notification_template(
    template: NotificationTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create notification template"""
    # Check if template name already exists
    existing = db.query(NotificationTemplate).filter(
        NotificationTemplate.name == template.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with name '{template.name}' already exists"
        )
    
    db_template = NotificationTemplate(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template


@router.get("/templates/{template_id}", response_model=NotificationTemplateResponse)
def get_notification_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Get notification template by ID"""
    template = db.get(NotificationTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.put("/templates/{template_id}", response_model=NotificationTemplateResponse)
def update_notification_template(
    template_id: int,
    template_update: NotificationTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update notification template"""
    template = db.get(NotificationTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Update fields
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return template


@router.delete("/templates/{template_id}")
def delete_notification_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Delete notification template"""
    template = db.get(NotificationTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    db.delete(template)
    db.commit()
    
    return {"message": "Template deleted successfully"}


# Alert rules endpoints
@router.get("/alerts/rules", response_model=List[AlertRuleResponse])
def get_alert_rules(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get alert rules"""
    from sqlalchemy import select
    
    stmt = select(AlertRule)
    if active_only:
        stmt = stmt.where(AlertRule.is_active == True)
    stmt = stmt.order_by(AlertRule.name)
    
    rules = db.execute(stmt).scalars().all()
    return list(rules)


@router.post("/alerts/rules", response_model=AlertRuleResponse)
def create_alert_rule(
    rule: AlertRuleCreate,
    db: Session = Depends(get_db)
):
    """Create alert rule"""
    # Check if rule name already exists
    existing = db.query(AlertRule).filter(
        AlertRule.name == rule.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alert rule with name '{rule.name}' already exists"
        )
    
    db_rule = AlertRule(**rule.dict())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    return db_rule


@router.get("/alerts/rules/{rule_id}", response_model=AlertRuleResponse)
def get_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Get alert rule by ID"""
    rule = db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )
    
    return rule


@router.put("/alerts/rules/{rule_id}", response_model=AlertRuleResponse)
def update_alert_rule(
    rule_id: int,
    rule_update: AlertRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update alert rule"""
    rule = db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )
    
    # Update fields
    update_data = rule_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    db.commit()
    db.refresh(rule)
    
    return rule


@router.delete("/alerts/rules/{rule_id}")
def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Delete alert rule"""
    rule = db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )
    
    db.delete(rule)
    db.commit()
    
    return {"message": "Alert rule deleted successfully"}


# Alert management endpoints
@router.post("/alerts", response_model=AlertResponse)
def create_alert(
    alert: AlertCreateRequest,
    db: Session = Depends(get_db)
):
    """Create and log an alert"""
    notification_service = NotificationService(db)
    
    db_alert = notification_service.create_alert(
        alert_type=alert.alert_type,
        severity=alert.severity,
        message=alert.message,
        context_data=alert.context_data,
        alert_rule_id=alert.alert_rule_id
    )
    
    return db_alert


@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get alerts with filtering"""
    notification_service = NotificationService(db)
    
    alerts = notification_service.get_alert_logs(
        limit=limit,
        offset=offset,
        severity=severity,
        alert_type=alert_type,
        is_resolved=is_resolved
    )
    
    return alerts


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Get alert by ID"""
    alert = db.get(AlertLog, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return alert


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    resolve_request: AlertResolveRequest,
    db: Session = Depends(get_db)
):
    """Mark alert as resolved"""
    notification_service = NotificationService(db)
    
    success = notification_service.resolve_alert(
        alert_id=alert_id,
        resolved_by=resolve_request.resolved_by
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {"message": "Alert resolved successfully"}


# Notification logs endpoints
@router.get("/logs", response_model=List[NotificationLogResponse])
def get_notification_logs(
    status: Optional[str] = None,
    notification_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get notification logs with filtering"""
    notification_service = NotificationService(db)
    
    logs = notification_service.get_notification_logs(
        limit=limit,
        offset=offset,
        status=status,
        notification_type=notification_type
    )
    
    return logs


# Statistics endpoint
@router.get("/stats", response_model=NotificationStats)
def get_notification_stats(db: Session = Depends(get_db)):
    """Get notification and alert statistics"""
    
    # Simple counts for now
    total_notifications = db.query(NotificationLog).count()
    sent_notifications = db.query(NotificationLog).filter(NotificationLog.status == 'sent').count()
    failed_notifications = db.query(NotificationLog).filter(NotificationLog.status == 'failed').count()
    pending_notifications = db.query(NotificationLog).filter(NotificationLog.status == 'pending').count()
    
    total_alerts = db.query(AlertLog).count()
    active_alerts = db.query(AlertLog).filter(AlertLog.is_resolved == False).count()
    resolved_alerts = db.query(AlertLog).filter(AlertLog.is_resolved == True).count()
    
    return NotificationStats(
        total_notifications=total_notifications,
        sent_notifications=sent_notifications,
        failed_notifications=failed_notifications,
        pending_notifications=pending_notifications,
        total_alerts=total_alerts,
        active_alerts=active_alerts,
        resolved_alerts=resolved_alerts
    )
