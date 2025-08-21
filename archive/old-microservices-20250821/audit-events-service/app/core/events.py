"""
Event processing and consumption for Audit Events Service
"""

import logging
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
import hmac

from opsconductor_shared.events.consumer import EventConsumer
from app.core.config import settings
from app.models.audit import AuditEvent, SecurityAlert, EventSeverity, EventCategory
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# Global event consumer instance
event_consumer: Optional[EventConsumer] = None

try:
    event_consumer = EventConsumer(
        rabbitmq_url=settings.RABBITMQ_URL,
        queue_name="audit_events_queue",
        exchange_name="opsconductor_events"
    )
    logger.info("Event consumer initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize event consumer: {e}")
    event_consumer = None


class AuditEventProcessor:
    """Process and store audit events"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    async def process_event(self, event_data: Dict[str, Any]) -> bool:
        """Process incoming event and store as audit event"""
        try:
            # Extract event information
            event_type = event_data.get("event_type", "unknown")
            service_name = event_data.get("service_name", "unknown")
            user_id = event_data.get("user_id")
            correlation_id = event_data.get("correlation_id")
            
            # Determine event category and severity
            category = self._determine_category(event_type)
            severity = self._determine_severity(event_type, event_data)
            
            # Create audit event
            audit_event = AuditEvent(
                event_type=event_type,
                event_category=category,
                event_severity=severity,
                event_name=event_data.get("event_name", event_type.replace("_", " ").title()),
                event_description=event_data.get("description"),
                event_message=event_data.get("message"),
                service_name=service_name,
                service_version=event_data.get("service_version"),
                user_id=user_id,
                username=event_data.get("username"),
                user_email=event_data.get("user_email"),
                session_id=event_data.get("session_id"),
                correlation_id=correlation_id,
                ip_address=event_data.get("ip_address"),
                user_agent=event_data.get("user_agent"),
                request_method=event_data.get("request_method"),
                request_url=event_data.get("request_url"),
                request_headers=event_data.get("request_headers"),
                resource_type=event_data.get("resource_type"),
                resource_id=event_data.get("resource_id"),
                resource_name=event_data.get("resource_name"),
                event_data=event_data.get("data", {}),
                before_data=event_data.get("before_data"),
                after_data=event_data.get("after_data"),
                success=event_data.get("success"),
                error_code=event_data.get("error_code"),
                error_message=event_data.get("error_message"),
                compliance_tags=event_data.get("compliance_tags", []),
                security_level=event_data.get("security_level"),
                data_classification=event_data.get("data_classification"),
                metadata=event_data.get("metadata", {}),
                tags=event_data.get("tags", []),
                event_timestamp=datetime.fromisoformat(event_data.get("timestamp", datetime.utcnow().isoformat())),
                retention_date=self._calculate_retention_date()
            )
            
            # Generate event hash for integrity
            if settings.ENABLE_EVENT_SIGNING:
                audit_event.event_hash = self._generate_event_hash(audit_event)
                audit_event.event_signature = self._generate_event_signature(audit_event)
            
            # Store event
            self.db.add(audit_event)
            self.db.commit()
            
            # Check for security alerts
            await self._check_security_alerts(audit_event)
            
            logger.debug(f"Processed audit event: {event_type} from {service_name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to process audit event: {e}")
            return False
        finally:
            self.db.close()
    
    def _determine_category(self, event_type: str) -> str:
        """Determine event category based on event type"""
        category_mapping = {
            "login": EventCategory.AUTHENTICATION,
            "logout": EventCategory.AUTHENTICATION,
            "password": EventCategory.AUTHENTICATION,
            "account": EventCategory.AUTHENTICATION,
            "user": EventCategory.USER_MANAGEMENT,
            "job": EventCategory.JOB_MANAGEMENT,
            "target": EventCategory.TARGET_MANAGEMENT,
            "service": EventCategory.SYSTEM,
            "configuration": EventCategory.SYSTEM,
            "backup": EventCategory.SYSTEM,
            "unauthorized": EventCategory.SECURITY,
            "permission": EventCategory.AUTHORIZATION,
            "suspicious": EventCategory.SECURITY,
            "breach": EventCategory.SECURITY,
            "data": EventCategory.DATA,
            "api": EventCategory.API,
        }
        
        for keyword, category in category_mapping.items():
            if keyword in event_type.lower():
                return category
        
        return EventCategory.SYSTEM
    
    def _determine_severity(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """Determine event severity based on type and data"""
        # Critical events
        critical_events = [
            "data_breach_attempt", "security_policy_violation", 
            "unauthorized_access", "service_error"
        ]
        
        # High severity events
        high_events = [
            "login_failed", "account_locked", "suspicious_activity",
            "job_failed", "target_deleted", "user_deleted"
        ]
        
        # Check if explicitly set
        if "severity" in event_data:
            return event_data["severity"]
        
        if event_type in critical_events:
            return EventSeverity.CRITICAL
        elif event_type in high_events:
            return EventSeverity.HIGH
        elif event_data.get("success") is False:
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW
    
    def _calculate_retention_date(self) -> datetime:
        """Calculate retention date based on configuration"""
        from datetime import timedelta
        return datetime.utcnow() + timedelta(days=settings.AUDIT_RETENTION_DAYS)
    
    def _generate_event_hash(self, event: AuditEvent) -> str:
        """Generate SHA-256 hash of event data for integrity"""
        event_string = f"{event.event_type}:{event.service_name}:{event.user_id}:{event.event_timestamp}:{event.event_data}"
        return hashlib.sha256(event_string.encode()).hexdigest()
    
    def _generate_event_signature(self, event: AuditEvent) -> str:
        """Generate HMAC signature for event"""
        message = f"{event.event_hash}:{event.event_timestamp}"
        signature = hmac.new(
            settings.ENCRYPTION_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _check_security_alerts(self, event: AuditEvent):
        """Check if event should trigger security alerts"""
        try:
            # Define alert conditions
            alert_conditions = {
                "multiple_failed_logins": {
                    "event_types": ["login_failed"],
                    "threshold": 5,
                    "time_window_minutes": 15,
                    "severity": EventSeverity.HIGH
                },
                "suspicious_activity": {
                    "event_types": ["unauthorized_access", "permission_denied"],
                    "threshold": 3,
                    "time_window_minutes": 10,
                    "severity": EventSeverity.CRITICAL
                },
                "data_breach_attempts": {
                    "event_types": ["data_breach_attempt"],
                    "threshold": 1,
                    "time_window_minutes": 1,
                    "severity": EventSeverity.CRITICAL
                }
            }
            
            for alert_type, condition in alert_conditions.items():
                if event.event_type in condition["event_types"]:
                    await self._evaluate_alert_condition(event, alert_type, condition)
                    
        except Exception as e:
            logger.error(f"Failed to check security alerts: {e}")
    
    async def _evaluate_alert_condition(self, event: AuditEvent, alert_type: str, condition: Dict[str, Any]):
        """Evaluate if alert condition is met"""
        try:
            from datetime import timedelta
            
            # Check recent events of same type
            time_threshold = datetime.utcnow() - timedelta(minutes=condition["time_window_minutes"])
            
            recent_events = self.db.query(AuditEvent).filter(
                AuditEvent.event_type.in_(condition["event_types"]),
                AuditEvent.event_timestamp >= time_threshold,
                AuditEvent.user_id == event.user_id if event.user_id else True,
                AuditEvent.ip_address == event.ip_address if event.ip_address else True
            ).count()
            
            if recent_events >= condition["threshold"]:
                # Create security alert
                alert = SecurityAlert(
                    alert_type=alert_type,
                    alert_severity=condition["severity"],
                    alert_title=f"Security Alert: {alert_type.replace('_', ' ').title()}",
                    alert_description=f"Detected {recent_events} {event.event_type} events in {condition['time_window_minutes']} minutes",
                    user_id=event.user_id,
                    ip_address=event.ip_address,
                    service_name=event.service_name,
                    event_count=recent_events,
                    first_occurrence=time_threshold,
                    last_occurrence=event.event_timestamp,
                    alert_data={
                        "condition": condition,
                        "triggering_event_id": event.id,
                        "event_count": recent_events
                    }
                )
                
                self.db.add(alert)
                self.db.commit()
                
                logger.warning(f"Security alert created: {alert_type} for user {event.user_id}")
                
        except Exception as e:
            logger.error(f"Failed to evaluate alert condition: {e}")


# Initialize event processor
event_processor = AuditEventProcessor()


async def process_audit_event(event_data: Dict[str, Any]) -> bool:
    """Process audit event - called by event consumer"""
    return await event_processor.process_event(event_data)


# Set up event consumer callback
if event_consumer:
    event_consumer.set_event_handler(process_audit_event)