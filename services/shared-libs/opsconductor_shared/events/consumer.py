"""
Event consumer for RabbitMQ integration
"""

import asyncio
import json
import logging
from typing import Callable, Dict, Any, Optional
import pika
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.exchange_type import ExchangeType

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Asynchronous event consumer for RabbitMQ
    """
    
    def __init__(self, rabbitmq_url: str, queue_name: str, exchange_name: str = "opsconductor_events"):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.connection: Optional[AsyncioConnection] = None
        self.channel = None
        self.handlers: Dict[str, Callable] = {}
        self.is_consuming = False
        
    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = AsyncioConnection(
                parameters,
                on_open_callback=self._on_connection_open,
                on_open_error_callback=self._on_connection_open_error,
                on_close_callback=self._on_connection_closed
            )
            logger.info(f"Connecting to RabbitMQ: {self.rabbitmq_url}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
            
    def _on_connection_open(self, connection):
        """Called when connection is opened"""
        logger.info("RabbitMQ connection opened")
        connection.channel(on_open_callback=self._on_channel_open)
        
    def _on_connection_open_error(self, connection, err):
        """Called when connection fails to open"""
        logger.error(f"RabbitMQ connection failed: {err}")
        
    def _on_connection_closed(self, connection, reason):
        """Called when connection is closed"""
        logger.warning(f"RabbitMQ connection closed: {reason}")
        self.is_consuming = False
        
    def _on_channel_open(self, channel):
        """Called when channel is opened"""
        logger.info("RabbitMQ channel opened")
        self.channel = channel
        self.channel.add_on_close_callback(self._on_channel_closed)
        
        # Declare exchange
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type=ExchangeType.topic,
            callback=self._on_exchange_declare_ok
        )
        
    def _on_channel_closed(self, channel, reason):
        """Called when channel is closed"""
        logger.warning(f"RabbitMQ channel closed: {reason}")
        
    def _on_exchange_declare_ok(self, unused_frame):
        """Called when exchange is declared"""
        logger.info(f"Exchange '{self.exchange_name}' declared")
        
        # Declare queue
        self.channel.queue_declare(
            queue=self.queue_name,
            durable=True,
            callback=self._on_queue_declare_ok
        )
        
    def _on_queue_declare_ok(self, method_frame):
        """Called when queue is declared"""
        logger.info(f"Queue '{self.queue_name}' declared")
        
        # Bind queue to exchange with routing patterns
        for event_type in self.handlers.keys():
            self.channel.queue_bind(
                exchange=self.exchange_name,
                queue=self.queue_name,
                routing_key=f"*.{event_type}",
                callback=self._on_bind_ok
            )
            
    def _on_bind_ok(self, unused_frame):
        """Called when queue is bound"""
        logger.info("Queue bound to exchange")
        self._start_consuming()
        
    def _start_consuming(self):
        """Start consuming messages"""
        if not self.is_consuming:
            logger.info("Starting to consume messages")
            self.channel.add_on_cancel_callback(self._on_consumer_cancelled)
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self._on_message,
                auto_ack=False
            )
            self.is_consuming = True
            
    def _on_consumer_cancelled(self, method_frame):
        """Called when consumer is cancelled"""
        logger.info("Consumer was cancelled")
        self.is_consuming = False
        
    def _on_message(self, channel, basic_deliver, properties, body):
        """Called when a message is received"""
        try:
            # Parse message
            message = json.loads(body.decode('utf-8'))
            event_type = message.get('event_type')
            
            logger.info(f"Received event: {event_type}")
            
            # Find and call handler
            if event_type in self.handlers:
                handler = self.handlers[event_type]
                
                # Call handler asynchronously
                asyncio.create_task(self._handle_message(handler, message))
                
            # Acknowledge message
            channel.basic_ack(basic_deliver.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Reject message
            channel.basic_nack(basic_deliver.delivery_tag, requeue=False)
            
    async def _handle_message(self, handler: Callable, message: Dict[str, Any]):
        """Handle message with async handler"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(message)
            else:
                handler(message)
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            
    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler for an event type"""
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
        
    async def start_consuming(self):
        """Start the consumer"""
        try:
            await self.connect()
            logger.info("Event consumer started successfully")
        except Exception as e:
            logger.error(f"Failed to start event consumer: {e}")
            raise
            
    async def stop_consuming(self):
        """Stop consuming messages"""
        await self.stop()
    
    async def stop(self):
        """Stop the consumer"""
        if self.is_consuming:
            self.channel.stop_consuming()
            self.is_consuming = False
            
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            
        logger.info("Consumer stopped")