"""
Dependency Injection Container for ENABLEDRM platform.
"""
from typing import Dict, Any, Callable, TypeVar, Type, Optional
from functools import wraps
import inspect

T = TypeVar('T')


class DIContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a singleton service."""
        key = self._get_key(interface)
        self._factories[key] = implementation
        self._singletons[key] = None
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a transient service (new instance each time)."""
        key = self._get_key(interface)
        self._factories[key] = implementation
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a specific instance."""
        key = self._get_key(interface)
        self._services[key] = instance
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service instance."""
        key = self._get_key(interface)
        
        # Check if we have a direct instance
        if key in self._services:
            return self._services[key]
        
        # Check if it's a singleton
        if key in self._singletons:
            if self._singletons[key] is None:
                self._singletons[key] = self._create_instance(key)
            return self._singletons[key]
        
        # Create transient instance
        if key in self._factories:
            return self._create_instance(key)
        
        raise ValueError(f"Service {interface.__name__} not registered")
    
    def _create_instance(self, key: str) -> Any:
        """Create an instance using dependency injection."""
        factory = self._factories[key]
        
        # Get constructor signature
        sig = inspect.signature(factory.__init__)
        params = {}
        
        # Resolve dependencies
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != inspect.Parameter.empty:
                # Try to resolve the dependency
                try:
                    params[param_name] = self.resolve(param.annotation)
                except ValueError:
                    # If we can't resolve it, skip it (might have default value)
                    pass
        
        return factory(**params)
    
    def _get_key(self, interface: Type) -> str:
        """Get string key for interface."""
        return f"{interface.__module__}.{interface.__name__}"


# Global container instance
container = DIContainer()


def inject(interface: Type[T]) -> T:
    """Decorator for dependency injection."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Inject the dependency
            dependency = container.resolve(interface)
            return func(dependency, *args, **kwargs)
        return wrapper
    return decorator


def injectable(interface: Optional[Type] = None):
    """Mark a class as injectable."""
    def decorator(cls):
        # Register the class in the container
        target_interface = interface or cls
        container.register_transient(target_interface, cls)
        return cls
    return decorator


def singleton(interface: Optional[Type] = None):
    """Mark a class as singleton."""
    def decorator(cls):
        # Register the class as singleton in the container
        target_interface = interface or cls
        container.register_singleton(target_interface, cls)
        return cls
    return decorator