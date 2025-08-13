"""
CQRS (Command Query Responsibility Segregation) pattern implementation.
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Dict, Type, Any
from dataclasses import dataclass

# Type variables for commands, queries, and results
TCommand = TypeVar('TCommand')
TQuery = TypeVar('TQuery')
TResult = TypeVar('TResult')


class Command(ABC):
    """Base class for all commands (write operations)."""
    pass


class Query(ABC):
    """Base class for all queries (read operations)."""
    pass


class CommandHandler(Generic[TCommand, TResult], ABC):
    """Base class for command handlers."""
    
    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        """Handle the command and return result."""
        pass


class QueryHandler(Generic[TQuery, TResult], ABC):
    """Base class for query handlers."""
    
    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        """Handle the query and return result."""
        pass


class Mediator:
    """Mediator pattern implementation for CQRS."""
    
    def __init__(self):
        self._command_handlers: Dict[Type, CommandHandler] = {}
        self._query_handlers: Dict[Type, QueryHandler] = {}
    
    def register_command_handler(self, command_type: Type[TCommand], handler: CommandHandler[TCommand, TResult]):
        """Register a command handler."""
        self._command_handlers[command_type] = handler
    
    def register_query_handler(self, query_type: Type[TQuery], handler: QueryHandler[TQuery, TResult]):
        """Register a query handler."""
        self._query_handlers[query_type] = handler
    
    async def send_command(self, command: TCommand) -> TResult:
        """Send a command to its handler."""
        command_type = type(command)
        if command_type not in self._command_handlers:
            raise ValueError(f"No handler registered for command {command_type.__name__}")
        
        handler = self._command_handlers[command_type]
        return await handler.handle(command)
    
    async def send_query(self, query: TQuery) -> TResult:
        """Send a query to its handler."""
        query_type = type(query)
        if query_type not in self._query_handlers:
            raise ValueError(f"No handler registered for query {query_type.__name__}")
        
        handler = self._query_handlers[query_type]
        return await handler.handle(query)


# Global mediator instance
mediator = Mediator()


def command_handler(command_type: Type[TCommand]):
    """Decorator to register command handlers."""
    def decorator(handler_class):
        handler_instance = handler_class()
        mediator.register_command_handler(command_type, handler_instance)
        return handler_class
    return decorator


def query_handler(query_type: Type[TQuery]):
    """Decorator to register query handlers."""
    def decorator(handler_class):
        handler_instance = handler_class()
        mediator.register_query_handler(query_type, handler_instance)
        return handler_class
    return decorator


@dataclass
class CommandResult:
    """Standard result wrapper for commands."""
    success: bool
    data: Any = None
    message: str = ""
    errors: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = {}


@dataclass
class QueryResult:
    """Standard result wrapper for queries."""
    data: Any = None
    total_count: int = 0
    page: int = 1
    page_size: int = 100
    has_next: bool = False
    has_previous: bool = False