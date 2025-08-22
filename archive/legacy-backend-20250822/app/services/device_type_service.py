"""
Device Type Service Layer
Handles business logic for device type operations with caching and logging

PHASE 2 IMPROVEMENTS:
- ✅ Service layer implementation
- ✅ Redis caching strategy
- ✅ Structured logging
- ✅ Performance metrics
- ✅ Enhanced error handling
"""

import logging
import time
from typing import List, Dict, Optional, Set
from functools import wraps
import json

from app.core.device_types import (
    device_registry, 
    DeviceCategory, 
    DeviceType
)
from app.core.cache import get_redis_client
from app.core.logging import get_structured_logger

# Configure structured logger
logger = get_structured_logger(__name__)

# Cache configuration
CACHE_TTL = 3600  # 1 hour
CACHE_PREFIX = "device_types:"


def with_caching(cache_key_func, ttl=CACHE_TTL):
    """Decorator for caching service method results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{CACHE_PREFIX}{cache_key_func(*args, **kwargs)}"
            
            # Try to get from cache
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached_result = await redis_client.get(cache_key)
                    if cached_result:
                        logger.info(
                            "Cache hit for device types operation",
                            extra={
                                "cache_key": cache_key,
                                "operation": func.__name__
                            }
                        )
                        return json.loads(cached_result)
                except Exception as e:
                    logger.warning(
                        "Cache read failed, proceeding without cache",
                        extra={
                            "cache_key": cache_key,
                            "error": str(e),
                            "operation": func.__name__
                        }
                    )
            
            # Execute function
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache the result
            if redis_client:
                try:
                    await redis_client.setex(
                        cache_key, 
                        ttl, 
                        json.dumps(result, default=str)
                    )
                    logger.info(
                        "Cached device types operation result",
                        extra={
                            "cache_key": cache_key,
                            "operation": func.__name__,
                            "execution_time": execution_time
                        }
                    )
                except Exception as e:
                    logger.warning(
                        "Cache write failed",
                        extra={
                            "cache_key": cache_key,
                            "error": str(e),
                            "operation": func.__name__
                        }
                    )
            
            # Log performance metrics
            logger.info(
                "Device types operation completed",
                extra={
                    "operation": func.__name__,
                    "execution_time": execution_time,
                    "result_count": len(result) if isinstance(result, list) else 1
                }
            )
            
            return result
        return wrapper
    return decorator


def with_performance_logging(func):
    """Decorator for performance logging"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                "Device type service operation successful",
                extra={
                    "operation": func.__name__,
                    "execution_time": execution_time,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                "Device type service operation failed",
                extra={
                    "operation": func.__name__,
                    "execution_time": execution_time,
                    "error": str(e),
                    "success": False
                }
            )
            raise
            
    return wrapper


class DeviceTypeService:
    """Service layer for device type operations"""
    
    def __init__(self):
        self.registry = device_registry
        logger.info("Device Type Service initialized")
    
    @with_caching(lambda self: "all_device_types")
    @with_performance_logging
    async def get_all_device_types(self) -> List[Dict]:
        """Get all device types with comprehensive information"""
        logger.debug("Retrieving all device types")
        
        device_types = self.registry.get_all_device_types()
        
        result = []
        for device_type in device_types:
            result.append({
                "value": device_type.value,
                "label": device_type.label,
                "category": device_type.category.value,
                "description": device_type.description,
                "communication_methods": list(device_type.communication_methods),
                "discovery_ports": device_type.discovery_ports or [],
                "discovery_services": device_type.discovery_services or [],
                "discovery_keywords": device_type.discovery_keywords or []
            })
        
        logger.info(
            "Retrieved all device types",
            extra={"device_type_count": len(result)}
        )
        
        return result
    
    @with_caching(lambda self: "device_categories")
    @with_performance_logging
    async def get_device_categories(self) -> List[Dict]:
        """Get all device categories with statistics"""
        logger.debug("Retrieving device categories")
        
        categories = []
        for category in DeviceCategory:
            device_types = self.registry.get_device_types_by_category(category)
            
            categories.append({
                "value": category.value,
                "label": category.value.replace("_", " ").title(),
                "device_count": len(device_types),
                "device_types": [dt.value for dt in device_types]
            })
        
        logger.info(
            "Retrieved device categories",
            extra={"category_count": len(categories)}
        )
        
        return categories
    
    @with_caching(lambda self, category: f"category_{category}")
    @with_performance_logging
    async def get_device_types_by_category(self, category: str) -> List[Dict]:
        """Get device types by category with validation"""
        logger.debug(
            "Retrieving device types by category",
            extra={"category": category}
        )
        
        # Validate category
        try:
            device_category = DeviceCategory(category)
        except ValueError:
            available_categories = [cat.value for cat in DeviceCategory]
            logger.warning(
                "Invalid category requested",
                extra={
                    "requested_category": category,
                    "available_categories": available_categories
                }
            )
            raise ValueError(f"Invalid category '{category}'. Available: {available_categories}")
        
        device_types = self.registry.get_device_types_by_category(device_category)
        
        result = []
        for device_type in device_types:
            result.append({
                "value": device_type.value,
                "label": device_type.label,
                "category": device_type.category.value,
                "description": device_type.description,
                "communication_methods": list(device_type.communication_methods)
            })
        
        logger.info(
            "Retrieved device types by category",
            extra={
                "category": category,
                "device_type_count": len(result)
            }
        )
        
        return result
    
    @with_caching(lambda self, device_type: f"communication_methods_{device_type}")
    @with_performance_logging
    async def get_communication_methods(self, device_type: str) -> List[str]:
        """Get communication methods for a device type"""
        logger.debug(
            "Retrieving communication methods",
            extra={"device_type": device_type}
        )
        
        methods = self.registry.get_communication_methods_for_device(device_type)
        if not methods:
            logger.warning(
                "Device type not found",
                extra={"device_type": device_type}
            )
            raise ValueError(f"Device type '{device_type}' not found")
        
        result = list(methods)
        
        logger.info(
            "Retrieved communication methods",
            extra={
                "device_type": device_type,
                "method_count": len(result)
            }
        )
        
        return result
    
    @with_caching(lambda self, method: f"device_types_for_method_{method}")
    @with_performance_logging
    async def get_device_types_for_method(self, method: str) -> List[Dict]:
        """Get device types that support a communication method"""
        logger.debug(
            "Retrieving device types for method",
            extra={"method": method}
        )
        
        device_types = self.registry.get_device_types_for_method(method)
        
        result = []
        for device_type in device_types:
            result.append({
                "value": device_type.value,
                "label": device_type.label,
                "category": device_type.category.value,
                "description": device_type.description,
                "communication_methods": list(device_type.communication_methods)
            })
        
        logger.info(
            "Retrieved device types for method",
            extra={
                "method": method,
                "device_type_count": len(result)
            }
        )
        
        return result
    
    @with_caching(lambda self, device_type: f"discovery_hints_{device_type}")
    @with_performance_logging
    async def get_discovery_hints(self, device_type: str) -> Dict:
        """Get discovery hints for a device type"""
        logger.debug(
            "Retrieving discovery hints",
            extra={"device_type": device_type}
        )
        
        hints = self.registry.get_discovery_hints(device_type)
        if not hints:
            logger.warning(
                "Device type not found for discovery hints",
                extra={"device_type": device_type}
            )
            raise ValueError(f"Device type '{device_type}' not found")
        
        result = {
            "ports": hints.get('ports', []),
            "services": hints.get('services', []),
            "keywords": hints.get('keywords', [])
        }
        
        logger.info(
            "Retrieved discovery hints",
            extra={
                "device_type": device_type,
                "port_count": len(result["ports"]),
                "service_count": len(result["services"]),
                "keyword_count": len(result["keywords"])
            }
        )
        
        return result
    
    @with_performance_logging
    async def suggest_device_types(self, ports: List[int], services: List[str], banner: str = "") -> List[Dict]:
        """Suggest device types based on discovery information"""
        logger.debug(
            "Suggesting device types from discovery",
            extra={
                "port_count": len(ports),
                "service_count": len(services),
                "has_banner": bool(banner)
            }
        )
        
        suggestions = self.registry.suggest_device_type(ports, services, banner)
        
        result = []
        for device_type_value in suggestions:
            device_type = self.registry.get_device_type(device_type_value)
            if device_type:
                result.append({
                    "value": device_type.value,
                    "label": device_type.label,
                    "category": device_type.category.value,
                    "description": device_type.description,
                    "communication_methods": list(device_type.communication_methods)
                })
        
        logger.info(
            "Generated device type suggestions",
            extra={
                "suggestion_count": len(result),
                "input_ports": ports,
                "input_services": services
            }
        )
        
        return result
    
    @with_caching(lambda self: "valid_device_types")
    @with_performance_logging
    async def get_valid_device_types(self) -> List[str]:
        """Get list of valid device type values"""
        logger.debug("Retrieving valid device types")
        
        result = list(self.registry._device_types.keys())
        
        logger.info(
            "Retrieved valid device types",
            extra={"device_type_count": len(result)}
        )
        
        return result
    
    @with_caching(lambda self: "all_communication_methods")
    @with_performance_logging
    async def get_all_communication_methods(self) -> List[str]:
        """Get all available communication methods"""
        logger.debug("Retrieving all communication methods")
        
        all_methods = set()
        for device_type in self.registry.get_all_device_types():
            all_methods.update(device_type.communication_methods)
        
        result = sorted(list(all_methods))
        
        logger.info(
            "Retrieved all communication methods",
            extra={"method_count": len(result)}
        )
        
        return result
    
    async def invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries"""
        redis_client = get_redis_client()
        if not redis_client:
            logger.warning("Redis not available for cache invalidation")
            return
        
        try:
            if pattern:
                cache_pattern = f"{CACHE_PREFIX}{pattern}"
            else:
                cache_pattern = f"{CACHE_PREFIX}*"
            
            # Get all matching keys
            keys = await redis_client.keys(cache_pattern)
            if keys:
                await redis_client.delete(*keys)
                logger.info(
                    "Cache invalidated",
                    extra={
                        "pattern": cache_pattern,
                        "keys_deleted": len(keys)
                    }
                )
            else:
                logger.debug(
                    "No cache keys found for pattern",
                    extra={"pattern": cache_pattern}
                )
                
        except Exception as e:
            logger.error(
                "Cache invalidation failed",
                extra={
                    "pattern": pattern,
                    "error": str(e)
                }
            )


# Global service instance
device_type_service = DeviceTypeService()