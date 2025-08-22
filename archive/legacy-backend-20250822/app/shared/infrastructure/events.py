"""
Event-driven architecture implementation for ENABLEDRM platform.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent(ABC):
    """Base class for all domain events."""
    event_id: str
    occurred_at: datetime
    aggregate_id: str
    aggregate_type: str
    event_version: int = 1
    
    def __post_init__(self):
        if not self.occurred_at:
            self.occurred_at = datetime.now(timezone.utc)


class EventHandler(ABC):
    """Base class for event handlers."""
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle the domain event."""
        pass


class EventBus:
    """Event bus for publishing and subscribing to domain events."""
    
    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}
        self._middleware: List[Callable] = []
    
    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler):
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def add_middleware(self, middleware: Callable):
        """Add middleware to the event bus."""
        self._middleware.append(middleware)
    
    async def publish(self, event: DomainEvent):
        """Publish an event to all registered handlers."""
        event_type = type(event)
        
        # Apply middleware
        for middleware in self._middleware:
            await middleware(event)
        
        # Get handlers for this event type
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.warning(f"No handlers registered for event {event_type.__name__}")
            return
        
        # Execute all handlers concurrently
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._handle_event_safely(handler, event))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _handle_event_safely(self, handler: EventHandler, event: DomainEvent):
        """Handle event with error handling."""
        try:
            await handler.handle(event)
            logger.debug(f"Event {type(event).__name__} handled by {type(handler).__name__}")
        except Exception as e:
            logger.error(f"Error handling event {type(event).__name__} with {type(handler).__name__}: {str(e)}")


# Global event bus instance
event_bus = EventBus()


def event_handler(event_type: Type[DomainEvent]):
    """Decorator to register event handlers."""
    def decorator(handler_class):
        handler_instance = handler_class()
        event_bus.subscribe(event_type, handler_instance)
        return handler_class
    return decorator


# Event middleware for logging
async def logging_middleware(event: DomainEvent):
    """Middleware to log all events."""
    logger.info(f"Event published: {type(event).__name__} for {event.aggregate_type}:{event.aggregate_id}")


# Event middleware for metrics
async def metrics_middleware(event: DomainEvent):
    """Middleware to collect event metrics."""
    # This could integrate with Prometheus or other metrics systems
    pass


# Register default middleware
event_bus.add_middleware(logging_middleware)
event_bus.add_middleware(metrics_middleware)