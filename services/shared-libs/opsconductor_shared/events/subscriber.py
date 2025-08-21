"""
Event subscriber for inter-service communication
"""

import json
import logging
import pika
from typing import Callable, Dict, Any, List
from threading import Thread

from opsconductor_shared.models.base import BaseEvent, EventType

logger = logging.getLogger(__name__)


class EventSubscriber:
    """Subscriber for inter-service events using RabbitMQ"""
    
    def __init__(self, service_name: str, rabbitmq_url: str = "amqp://localhost:5672"):
        self.service_name = service_name
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.handlers: Dict[str, List[Callable]] = {}
        self._connect()
    
    def _connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange='opsconductor.events',
                exchange_type='topic',
                durable=True
            )
            
            # Declare service-specific queue
            queue_name = f"opsconductor.{self.service_name}.events"
            self.channel.queue_declare(queue=queue_name, durable=True)
            
            logger.info(f"Connected to RabbitMQ for event subscription: {queue_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def subscribe(self, event_types: List[EventType], handler: Callable[[BaseEvent], None]):
        """Subscribe to specific event types"""
        try:
            queue_name = f"opsconductor.{self.service_name}.events"
            
            # Bind queue to exchange for each event type
            for event_type in event_types:
                routing_key = event_type.value.replace('.', '_')
                self.channel.queue_bind(
                    exchange='opsconductor.events',
                    queue=queue_name,
                    routing_key=routing_key
                )
                
                # Store handler
                if routing_key not in self.handlers:
                    self.handlers[routing_key] = []
                self.handlers[routing_key].append(handler)
                
                logger.info(f"Subscribed to event: {event_type.value}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to events: {e}")
            raise
    
    def _handle_message(self, channel, method, properties, body):
        """Handle incoming message"""
        try:
            # Parse event
            event_data = json.loads(body.decode('utf-8'))
            event = BaseEvent(**event_data)
            
            # Get routing key
            routing_key = method.routing_key
            
            # Call handlers
            if routing_key in self.handlers:
                for handler in self.handlers[routing_key]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Handler error for {routing_key}: {e}")
            
            # Acknowledge message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Failed to handle message: {e}")
            # Reject message
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
        """Start consuming events"""
        try:
            queue_name = f"opsconductor.{self.service_name}.events"
            
            self.channel.basic_qos(prefetch_count=10)
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self._handle_message
            )
            
            logger.info(f"Started consuming events for {self.service_name}")
            self.channel.start_consuming()
            
        except Exception as e:
            logger.error(f"Failed to start consuming: {e}")
            raise
    
    def start_consuming_async(self):
        """Start consuming events in background thread"""
        thread = Thread(target=self.start_consuming, daemon=True)
        thread.start()
        return thread
    
    def stop_consuming(self):
        """Stop consuming events"""
        if self.channel:
            self.channel.stop_consuming()
    
    def close(self):
        """Close connection to RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Closed RabbitMQ connection")