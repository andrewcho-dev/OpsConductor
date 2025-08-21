"""
Event publishing for Target Discovery Service
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from opsconductor_shared.events.publisher import EventPublisher
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global event publisher instance
event_publisher: Optional[EventPublisher] = None

try:
    event_publisher = EventPublisher(
        rabbitmq_url=settings.RABBITMQ_URL,
        exchange_name="opsconductor_events"
    )
    logger.info("Event publisher initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize event publisher: {e}")
    event_publisher = None


async def publish_discovery_event(event_type: str, data: Dict[str, Any], user_id: Optional[int] = None):
    """Publish discovery-related events"""
    if not event_publisher:
        logger.warning("Event publisher not available")
        return
    
    try:
        await event_publisher.publish_event(
            event_type=event_type,
            service_name="target-discovery-service",
            data=data,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat()
        )
        logger.debug(f"Published discovery event: {event_type}")
    except Exception as e:
        logger.error(f"Failed to publish discovery event: {e}")


async def publish_device_discovered_event(device_data: Dict[str, Any], job_id: int, user_id: Optional[int] = None):
    """Publish device discovered event"""
    await publish_discovery_event(
        event_type="device_discovered",
        data={
            "device": device_data,
            "discovery_job_id": job_id,
            "discovery_method": device_data.get("discovery_method"),
            "ip_address": device_data.get("ip_address"),
            "hostname": device_data.get("hostname"),
            "device_type": device_data.get("device_type")
        },
        user_id=user_id
    )


async def publish_discovery_job_event(event_type: str, job_data: Dict[str, Any], user_id: Optional[int] = None):
    """Publish discovery job events"""
    await publish_discovery_event(
        event_type=f"discovery_job_{event_type}",
        data={
            "job": job_data,
            "job_id": job_data.get("id"),
            "job_name": job_data.get("name"),
            "status": job_data.get("status"),
            "progress": job_data.get("progress")
        },
        user_id=user_id
    )