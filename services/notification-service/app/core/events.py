"""
Event processing and consumption for Notification Service
"""

import logging
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from opsconductor_shared.events.consumer import EventConsumer
from app.core.config import settings
from app.models.notification import AlertRule, AlertLog, NotificationLog
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# Global event consumer instance
event_consumer: Optional[EventConsumer] = None

try:
    event_consumer = EventConsumer(
        rabbitmq_url=settings.RABBITMQ_URL,
        queue_name="notification_events_queue",
        exchange_name="opsconductor_events"
    )
    logger.info("Event consumer initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize event consumer: {e}")
    event_consumer = None


class NotificationEventProcessor:
    """Process events and trigger notifications"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    async def process_event(self, event_data: Dict[str, Any]) -> bool:
        """Process incoming event and check for notification triggers"""
        try:
            event_type = event_data.get("event_type", "unknown")
            service_name = event_data.get("service_name", "unknown")
            user_id = event_data.get("user_id")
            
            logger.debug(f"Processing event: {event_type} from {service_name}")
            
            # Get active alert rules that match this event
            matching_rules = self._get_matching_alert_rules(event_type, event_data)
            
            for rule in matching_rules:
                await self._evaluate_alert_rule(rule, event_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process notification event: {e}")
            return False
        finally:
            self.db.close()
    
    def _get_matching_alert_rules(self, event_type: str, event_data: Dict[str, Any]) -> list:
        """Get alert rules that match the current event"""
        try:
            # Get all active alert rules
            rules = self.db.query(AlertRule).filter(
                AlertRule.is_active == True,
                AlertRule.is_paused == False
            ).all()
            
            matching_rules = []
            
            for rule in rules:
                # Check if event type matches
                if event_type in rule.event_types:
                    # Check additional conditions
                    if self._evaluate_rule_conditions(rule, event_data):
                        matching_rules.append(rule)
            
            return matching_rules
            
        except Exception as e:
            logger.error(f"Failed to get matching alert rules: {e}")
            return []
    
    def _evaluate_rule_conditions(self, rule: AlertRule, event_data: Dict[str, Any]) -> bool:
        """Evaluate if rule conditions are met"""
        try:
            conditions = rule.conditions or {}
            
            # Check severity condition
            if "severity" in conditions:
                required_severity = conditions["severity"]
                event_severity = event_data.get("severity", "low")
                
                severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                if severity_levels.get(event_severity, 1) < severity_levels.get(required_severity, 1):
                    return False
            
            # Check service condition
            if "services" in conditions:
                required_services = conditions["services"]
                event_service = event_data.get("service_name")
                if event_service not in required_services:
                    return False
            
            # Check user condition
            if "users" in conditions:
                required_users = conditions["users"]
                event_user = event_data.get("user_id")
                if event_user not in required_users:
                    return False
            
            # Check custom conditions
            if "custom" in conditions:
                # Implement custom condition evaluation logic here
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to evaluate rule conditions: {e}")
            return False
    
    async def _evaluate_alert_rule(self, rule: AlertRule, event_data: Dict[str, Any]):
        """Evaluate alert rule and create alert if needed"""
        try:
            # Check cooldown period
            if rule.last_alert_sent:
                from datetime import timedelta
                cooldown_end = rule.last_alert_sent + timedelta(minutes=rule.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    logger.debug(f"Alert rule {rule.name} is in cooldown period")
                    return
            
            # Create alert log
            alert_log = AlertLog(
                alert_rule_id=rule.id,
                alert_title=self._generate_alert_title(rule, event_data),
                alert_message=self._generate_alert_message(rule, event_data),
                severity=rule.severity,
                triggered_by_event=event_data.get("event_type"),
                event_data=event_data,
                correlation_id=event_data.get("correlation_id")
            )
            
            self.db.add(alert_log)
            self.db.commit()
            
            # Send notifications
            await self._send_alert_notifications(rule, alert_log, event_data)
            
            # Update rule statistics
            rule.trigger_count += 1
            rule.last_triggered = datetime.utcnow()
            rule.last_alert_sent = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Alert created for rule: {rule.name}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to evaluate alert rule: {e}")
    
    def _generate_alert_title(self, rule: AlertRule, event_data: Dict[str, Any]) -> str:
        """Generate alert title from rule and event data"""
        try:
            # Use rule name as base title
            title = rule.name
            
            # Add event context
            event_type = event_data.get("event_type", "").replace("_", " ").title()
            service_name = event_data.get("service_name", "")
            
            if event_type and service_name:
                title = f"{title}: {event_type} in {service_name}"
            elif event_type:
                title = f"{title}: {event_type}"
            
            return title[:500]  # Limit title length
            
        except Exception as e:
            logger.error(f"Failed to generate alert title: {e}")
            return rule.name
    
    def _generate_alert_message(self, rule: AlertRule, event_data: Dict[str, Any]) -> str:
        """Generate alert message from rule and event data"""
        try:
            message_parts = []
            
            # Add rule description
            if rule.description:
                message_parts.append(rule.description)
            
            # Add event details
            event_type = event_data.get("event_type")
            service_name = event_data.get("service_name")
            timestamp = event_data.get("timestamp")
            
            if event_type:
                message_parts.append(f"Event Type: {event_type}")
            if service_name:
                message_parts.append(f"Service: {service_name}")
            if timestamp:
                message_parts.append(f"Time: {timestamp}")
            
            # Add error details if present
            error_message = event_data.get("error_message")
            if error_message:
                message_parts.append(f"Error: {error_message}")
            
            # Add user context if present
            username = event_data.get("username")
            if username:
                message_parts.append(f"User: {username}")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate alert message: {e}")
            return f"Alert triggered by {event_data.get('event_type', 'unknown event')}"
    
    async def _send_alert_notifications(self, rule: AlertRule, alert_log: AlertLog, event_data: Dict[str, Any]):
        """Send notifications for the alert"""
        try:
            # Import notification service here to avoid circular imports
            from app.services.notification_service import NotificationService
            
            notification_service = NotificationService(self.db)
            
            # Send notifications to all configured recipients
            for recipient in rule.recipients:
                for template_id in rule.notification_templates:
                    try:
                        await notification_service.send_notification_from_template(
                            template_id=template_id,
                            recipient=recipient,
                            variables={
                                "alert_title": alert_log.alert_title,
                                "alert_message": alert_log.alert_message,
                                "severity": alert_log.severity,
                                "rule_name": rule.name,
                                "event_type": event_data.get("event_type"),
                                "service_name": event_data.get("service_name"),
                                "timestamp": event_data.get("timestamp"),
                                "correlation_id": event_data.get("correlation_id")
                            },
                            correlation_id=event_data.get("correlation_id"),
                            user_id=event_data.get("user_id")
                        )
                        
                        alert_log.notifications_sent += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to send notification to {recipient}: {e}")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")


# Initialize event processor
event_processor = NotificationEventProcessor()


async def process_notification_event(event_data: Dict[str, Any]) -> bool:
    """Process notification event - called by event consumer"""
    return await event_processor.process_event(event_data)


# Set up event consumer callback
if event_consumer:
    # Register handlers for different event types
    event_consumer.register_handler("user_login", process_notification_event)
    event_consumer.register_handler("user_created", process_notification_event)
    event_consumer.register_handler("job_created", process_notification_event)
    event_consumer.register_handler("execution_completed", process_notification_event)
    event_consumer.register_handler("execution_failed", process_notification_event)
    event_consumer.register_handler("system_alert", process_notification_event)