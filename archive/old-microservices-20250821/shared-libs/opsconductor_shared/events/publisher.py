"""
Event publisher for inter-service communication
"""

import json
import logging
import pika
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from opsconductor_shared.models.base import BaseEvent, EventType, ServiceType

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publisher for inter-service events using RabbitMQ"""
    
    def __init__(self, rabbitmq_url: str = "amqp://localhost:5672"):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            
            # Declare exchange for events
            self.channel.exchange_declare(
                exchange='opsconductor.events',
                exchange_type='topic',
                durable=True
            )
            
            logger.info("Connected to RabbitMQ for event publishing")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def publish_event(
        self,
        event_type: EventType,
        service_name: ServiceType,
        data: Dict[str, Any],
        correlation_id: Optional[UUID] = None,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Publish an event to the message broker"""
        try:
            event = BaseEvent(
                event_type=event_type,
                service_name=service_name,
                data=data,
                correlation_id=correlation_id,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # Create routing key from event type
            routing_key = event_type.value.replace('.', '_')
            
            # Publish event
            self.channel.basic_publish(
                exchange='opsconductor.events',
                routing_key=routing_key,
                body=event.model_dump_json(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json',
                    headers={
                        'event_type': event_type.value,
                        'service_name': service_name.value,
                        'correlation_id': str(correlation_id) if correlation_id else None
                    }
                )
            )
            
            logger.info(f"Published event: {event_type.value} from {service_name.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type.value}: {e}")
            return False
    
    def close(self):
        """Close connection to RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Closed RabbitMQ connection")