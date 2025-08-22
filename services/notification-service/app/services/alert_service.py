"""
Alert Service - Business logic for alert rules and logs
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid

from app.models.notification import AlertRule, AlertLog, AlertStatus
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing alert rules and logs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_alert_rule(
        self,
        rule_data: AlertRuleCreate,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> AlertRule:
        """Create a new alert rule"""
        try:
            # Check for duplicate name
            existing = self.db.query(AlertRule).filter(
                AlertRule.name == rule_data.name
            ).first()
            
            if existing:
                raise ValueError(f"Alert rule with name '{rule_data.name}' already exists")
            
            # Create alert rule
            rule = AlertRule(
                rule_uuid=uuid.uuid4(),
                name=rule_data.name,
                description=rule_data.description,
                event_type=rule_data.event_type,
                conditions=rule_data.conditions,
                severity=rule_data.severity,
                is_active=rule_data.is_active,
                notification_template_id=rule_data.notification_template_id,
                recipients=rule_data.recipients,
                throttle_minutes=rule_data.throttle_minutes,
                max_alerts_per_hour=rule_data.max_alerts_per_hour,
                template_metadata=rule_data.template_metadata or {},
                tags=rule_data.tags or [],
                created_by=user_id,
                organization_id=organization_id
            )
            
            self.db.add(rule)
            self.db.commit()
            self.db.refresh(rule)
            
            logger.info(f"Created alert rule {rule.id}: {rule.name}")
            return rule
            
        except Exception as e:
            logger.error(f"Failed to create alert rule: {e}")
            self.db.rollback()
            raise
    
    async def list_alert_rules(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        user_id: Optional[int] = None
    ) -> List[AlertRule]:
        """List alert rules with filtering"""
        query = self.db.query(AlertRule)
        
        if active_only:
            query = query.filter(AlertRule.is_active == True)
        if user_id:
            query = query.filter(AlertRule.created_by == user_id)
        
        return query.order_by(AlertRule.created_at.desc()).offset(skip).limit(limit).all()
    
    async def get_alert_rule(self, rule_id: int) -> Optional[AlertRule]:
        """Get a specific alert rule"""
        return self.db.query(AlertRule).filter(
            AlertRule.id == rule_id
        ).first()
    
    async def update_alert_rule(
        self,
        rule_id: int,
        update_data: AlertRuleUpdate,
        user_id: int
    ) -> Optional[AlertRule]:
        """Update an alert rule"""
        rule = self.db.query(AlertRule).filter(
            AlertRule.id == rule_id
        ).first()
        
        if not rule:
            return None
        
        # Check for duplicate name if name is being updated
        if update_data.name and update_data.name != rule.name:
            existing = self.db.query(AlertRule).filter(
                AlertRule.name == update_data.name,
                AlertRule.id != rule_id
            ).first()
            
            if existing:
                raise ValueError(f"Alert rule with name '{update_data.name}' already exists")
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(rule, field, value)
        
        rule.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rule)
        
        logger.info(f"Updated alert rule {rule.id}: {rule.name}")
        return rule
    
    async def delete_alert_rule(self, rule_id: int, user_id: int) -> bool:
        """Delete an alert rule"""
        rule = self.db.query(AlertRule).filter(
            AlertRule.id == rule_id
        ).first()
        
        if not rule:
            return False
        
        # Mark as inactive instead of deleting to preserve history
        rule.is_active = False
        rule.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Deactivated alert rule {rule.id}: {rule.name}")
        return True
    
    async def list_alert_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[AlertLog]:
        """List alert logs with filtering"""
        query = self.db.query(AlertLog)
        
        if severity:
            query = query.filter(AlertLog.severity == severity)
        if status:
            query = query.filter(AlertLog.status == status)
        if user_id:
            query = query.filter(AlertLog.created_by == user_id)
        
        return query.order_by(AlertLog.created_at.desc()).offset(skip).limit(limit).all()
    
    async def get_alert_log(self, log_id: int) -> Optional[AlertLog]:
        """Get a specific alert log"""
        return self.db.query(AlertLog).filter(
            AlertLog.id == log_id
        ).first()
    
    async def acknowledge_alert(self, log_id: int, user_id: int) -> Optional[AlertLog]:
        """Acknowledge an alert"""
        alert_log = self.db.query(AlertLog).filter(
            AlertLog.id == log_id
        ).first()
        
        if not alert_log:
            return None
        
        if alert_log.status != AlertStatus.OPEN:
            raise ValueError("Can only acknowledge open alerts")
        
        alert_log.status = AlertStatus.ACKNOWLEDGED
        alert_log.acknowledged_at = datetime.utcnow()
        alert_log.acknowledged_by = user_id
        alert_log.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert_log)
        
        logger.info(f"Acknowledged alert {alert_log.id}")
        return alert_log
    
    async def resolve_alert(self, log_id: int, user_id: int) -> Optional[AlertLog]:
        """Resolve an alert"""
        alert_log = self.db.query(AlertLog).filter(
            AlertLog.id == log_id
        ).first()
        
        if not alert_log:
            return None
        
        if alert_log.status in [AlertStatus.RESOLVED, AlertStatus.CLOSED]:
            raise ValueError("Alert is already resolved or closed")
        
        alert_log.status = AlertStatus.RESOLVED
        alert_log.resolved_at = datetime.utcnow()
        alert_log.resolved_by = user_id
        alert_log.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert_log)
        
        logger.info(f"Resolved alert {alert_log.id}")
        return alert_log
    
    async def create_alert_log(
        self,
        rule_id: int,
        alert_title: str,
        alert_message: str,
        event_data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        user_id: int = 1,  # System user
        organization_id: Optional[int] = None
    ) -> AlertLog:
        """Create a new alert log entry"""
        try:
            # Get the rule to determine severity
            rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
            if not rule:
                raise ValueError(f"Alert rule {rule_id} not found")
            
            # Create alert log
            alert_log = AlertLog(
                log_uuid=uuid.uuid4(),
                rule_id=rule_id,
                alert_title=alert_title,
                alert_message=alert_message,
                severity=rule.severity,
                status=AlertStatus.OPEN,
                event_data=event_data,
                correlation_id=correlation_id,
                context_metadata={},
                created_by=user_id,
                organization_id=organization_id
            )
            
            self.db.add(alert_log)
            self.db.commit()
            self.db.refresh(alert_log)
            
            # Update rule statistics
            rule.total_alerts += 1
            rule.last_triggered_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Created alert log {alert_log.id} for rule {rule_id}")
            return alert_log
            
        except Exception as e:
            logger.error(f"Failed to create alert log: {e}")
            self.db.rollback()
            raise