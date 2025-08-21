"""
Event publishing integration for Universal Targets Service
"""

import logging
from typing import Optional
from opsconductor_shared.events.publisher import EventPublisher
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global event publisher instance
event_publisher: Optional[EventPublisher] = None

try:
    event_publisher = EventPublisher(settings.RABBITMQ_URL)
    logger.info("Event publisher initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize event publisher: {e}")
    event_publisher = None


async def publish_target_event(event_type, data, correlation_id=None, user_id=None):
    """Helper function to publish target-related events"""
    if event_publisher:
        try:
            from opsconductor_shared.models.base import ServiceType
            return await event_publisher.publish_event(
                event_type=event_type,
                service_name=ServiceType.UNIVERSAL_TARGETS,
                data=data,
                correlation_id=correlation_id,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False
    return False