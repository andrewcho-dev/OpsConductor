"""
Device Type Service Layer V2 - Phase 3
Enhanced service layer with database persistence and advanced features

PHASE 3 IMPROVEMENTS:
- ✅ Database persistence
- ✅ CRUD operations
- ✅ Advanced search and filtering
- ✅ Usage tracking
- ✅ Template management
"""

import logging
import time
from typing import List, Dict, Optional, Set, Tuple
from functools import wraps
import json

from app.repositories.device_type_repository import DeviceTypeRepository, get_device_type_repository
from app.core.device_types import device_registry, DeviceCategory
from app.core.cache import get_redis_client
from app.core.logging import get_structured_logger
from app.database.database import get_db
from sqlalchemy.orm import Session

# Configure structured logger
logger = get_structured_logger(__name__)

# Cache configuration
CACHE_TTL = 3600  # 1 hour
CACHE_PREFIX = "device_types_v2:"


def with_caching_v2(cache_key_func, ttl=CACHE_TTL):
    """Enhanced caching decorator for V2 service"""
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
                            "Cache hit for device types V2 operation",
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
                        "Cached device types V2 operation result",
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
                "Device types V2 operation completed",
                extra={
                    "operation": func.__name__,
                    "execution_time": execution_time,
                    "result_count": len(result) if isinstance(result, list) else 1
                }
            )
            
            return result
        return wrapper
    return decorator


def with_performance_logging_v2(func):
    """Enhanced performance logging decorator"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                "Device type service V2 operation successful",
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
                "Device type service V2 operation failed",
                extra={
                    "operation": func.__name__,
                    "execution_time": execution_time,
                    "error": str(e),
                    "success": False
                }
            )
            raise
            
    return wrapper


class DeviceTypeServiceV2:
    """Enhanced service layer for device type operations with database persistence"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.repository = DeviceTypeRepository(self.db)
        self.registry = device_registry  # Fallback to registry
        logger.info("Device Type Service V2 initialized with database persistence")
    
    # CRUD Operations
    
    @with_performance_logging_v2
    async def create_device_type(self, device_type_data: Dict, user_id: int) -> Dict:
        """Create a new custom device type"""
        logger.info(
            "Creating custom device type",
            extra={
                "device_type_value": device_type_data.get("value"),
                "user_id": user_id
            }
        )
        
        # Validate required fields
        required_fields = ["value", "label", "category"]
        for field in required_fields:
            if field not in device_type_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Check if device type already exists
        existing = await self.repository.get_device_type_by_value(device_type_data["value"])
        if existing:
            raise ValueError(f"Device type '{device_type_data['value']}' already exists")
        
        # Create device type
        device_type = await self.repository.create_device_type(device_type_data, user_id)
        
        # Track usage
        await self.repository.track_usage(
            device_type.value, 
            user_id, 
            "creation",
            {"action": "create_custom_device_type"}
        )
        
        # Invalidate cache
        await self.invalidate_cache()
        
        return device_type.to_dict()
    
    @with_performance_logging_v2
    async def update_device_type(self, device_type_id: int, update_data: Dict, user_id: int) -> Optional[Dict]:
        """Update an existing device type"""
        logger.info(
            "Updating device type",
            extra={
                "device_type_id": device_type_id,
                "user_id": user_id,
                "update_fields": list(update_data.keys())
            }
        )
        
        device_type = await self.repository.update_device_type(device_type_id, update_data, user_id)
        if not device_type:
            return None
        
        # Track usage
        await self.repository.track_usage(
            device_type.value, 
            user_id, 
            "modification",
            {"action": "update_device_type", "fields": list(update_data.keys())}
        )
        
        # Invalidate cache
        await self.invalidate_cache()
        
        return device_type.to_dict()
    
    @with_performance_logging_v2
    async def delete_device_type(self, device_type_id: int, user_id: int) -> bool:
        """Delete a device type"""
        logger.info(
            "Deleting device type",
            extra={
                "device_type_id": device_type_id,
                "user_id": user_id
            }
        )
        
        success = await self.repository.delete_device_type(device_type_id, user_id)
        
        if success:
            # Invalidate cache
            await self.invalidate_cache()
        
        return success
    
    # Enhanced Read Operations
    
    @with_caching_v2(lambda self, **kwargs: f"search_{hash(str(sorted(kwargs.items())))}")
    @with_performance_logging_v2
    async def search_device_types(
        self,
        query: str = None,
        category: str = None,
        communication_method: str = None,
        tags: List[str] = None,
        is_system: bool = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "label",
        sort_order: str = "asc",
        user_id: int = None
    ) -> Dict:
        """Advanced search for device types"""
        logger.info(
            "Searching device types with advanced filters",
            extra={
                "query": query,
                "category": category,
                "communication_method": communication_method,
                "tags": tags,
                "user_id": user_id
            }
        )
        
        # Perform search
        results, total_count = await self.repository.search_device_types(
            query=query,
            category=category,
            communication_method=communication_method,
            tags=tags,
            is_system=is_system,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert to dictionaries
        device_types = [dt.to_dict() for dt in results]
        
        # Track search usage if user provided
        if user_id and query:
            await self.repository.track_usage(
                f"search:{query}", 
                user_id, 
                "search",
                {
                    "query": query,
                    "category": category,
                    "results_count": len(device_types)
                }
            )
        
        return {
            "device_types": device_types,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(device_types)) < total_count
        }
    
    @with_caching_v2(lambda self, include_stats=False: f"all_device_types_stats_{include_stats}")
    @with_performance_logging_v2
    async def get_all_device_types(self, include_stats: bool = False) -> List[Dict]:
        """Get all device types with optional statistics"""
        logger.debug("Retrieving all device types from database")
        
        # Get from database first
        db_device_types = await self.repository.get_all_device_types()
        
        # If no database types, fall back to registry
        if not db_device_types:
            logger.info("No database device types found, using registry fallback")
            registry_types = self.registry.get_all_device_types()
            result = []
            for device_type in registry_types:
                result.append({
                    "value": device_type.value,
                    "label": device_type.label,
                    "category": device_type.category.value,
                    "description": device_type.description,
                    "communication_methods": list(device_type.communication_methods),
                    "discovery_ports": device_type.discovery_ports or [],
                    "discovery_services": device_type.discovery_services or [],
                    "discovery_keywords": device_type.discovery_keywords or [],
                    "is_system": True,
                    "is_active": True
                })
        else:
            result = [dt.to_dict() for dt in db_device_types]
        
        # Add statistics if requested
        if include_stats:
            # Get usage statistics
            popular_types = await self.repository.get_popular_device_types()
            usage_map = {pt["device_type_value"]: pt["total_usage"] for pt in popular_types}
            
            for device_type in result:
                device_type["usage_count"] = usage_map.get(device_type["value"], 0)
        
        logger.info(
            "Retrieved all device types",
            extra={
                "device_type_count": len(result),
                "include_stats": include_stats
            }
        )
        
        return result
    
    @with_caching_v2(lambda self: "device_categories_with_stats")
    @with_performance_logging_v2
    async def get_device_categories(self) -> List[Dict]:
        """Get all device categories with statistics"""
        logger.debug("Retrieving device categories with statistics")
        
        # Get category statistics from database
        category_stats = await self.repository.get_category_statistics()
        stats_map = {cs["category"]: cs["device_count"] for cs in category_stats}
        
        # Get all categories (fallback to enum if no database categories)
        db_categories = await self.repository.get_all_categories()
        
        if db_categories:
            result = [cat.to_dict() for cat in db_categories]
            # Add device counts
            for category in result:
                category["device_count"] = stats_map.get(category["value"], 0)
        else:
            # Fallback to enum
            result = []
            for category in DeviceCategory:
                result.append({
                    "value": category.value,
                    "label": category.value.replace("_", " ").title(),
                    "device_count": stats_map.get(category.value, 0),
                    "is_system": True,
                    "is_active": True
                })
        
        logger.info(
            "Retrieved device categories",
            extra={"category_count": len(result)}
        )
        
        return result
    
    # Usage Tracking and Analytics
    
    @with_performance_logging_v2
    async def track_device_type_usage(
        self, 
        device_type_value: str, 
        user_id: int, 
        context: str = "general",
        context_data: Dict = None
    ):
        """Track device type usage"""
        await self.repository.track_usage(device_type_value, user_id, context, context_data)
        
        logger.info(
            "Device type usage tracked",
            extra={
                "device_type_value": device_type_value,
                "user_id": user_id,
                "context": context
            }
        )
    
    @with_caching_v2(lambda self, limit=10: f"popular_device_types_{limit}")
    @with_performance_logging_v2
    async def get_popular_device_types(self, limit: int = 10) -> List[Dict]:
        """Get most popular device types"""
        popular_types = await self.repository.get_popular_device_types(limit)
        
        # Enrich with device type details
        result = []
        for pt in popular_types:
            device_type = await self.repository.get_device_type_by_value(pt["device_type_value"])
            if device_type:
                dt_dict = device_type.to_dict()
                dt_dict["usage_count"] = pt["total_usage"]
                result.append(dt_dict)
        
        logger.info(
            "Retrieved popular device types",
            extra={"count": len(result)}
        )
        
        return result
    
    @with_performance_logging_v2
    async def get_user_device_type_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's device type usage history"""
        history = await self.repository.get_user_device_type_history(user_id, limit)
        
        result = [h.to_dict() for h in history]
        
        logger.info(
            "Retrieved user device type history",
            extra={
                "user_id": user_id,
                "history_count": len(result)
            }
        )
        
        return result
    
    # Legacy Compatibility Methods
    
    async def get_device_types_by_category(self, category: str) -> List[Dict]:
        """Get device types by category (legacy compatibility)"""
        search_result = await self.search_device_types(category=category, limit=1000)
        return search_result["device_types"]
    
    async def get_communication_methods(self, device_type: str) -> List[str]:
        """Get communication methods for a device type (legacy compatibility)"""
        device_type_obj = await self.repository.get_device_type_by_value(device_type)
        if device_type_obj:
            return device_type_obj.communication_methods or []
        
        # Fallback to registry
        methods = self.registry.get_communication_methods_for_device(device_type)
        if not methods:
            raise ValueError(f"Device type '{device_type}' not found")
        return list(methods)
    
    async def get_device_types_for_method(self, method: str) -> List[Dict]:
        """Get device types for communication method (legacy compatibility)"""
        search_result = await self.search_device_types(communication_method=method, limit=1000)
        return search_result["device_types"]
    
    async def get_discovery_hints(self, device_type: str) -> Dict:
        """Get discovery hints for a device type (legacy compatibility)"""
        device_type_obj = await self.repository.get_device_type_by_value(device_type)
        if device_type_obj:
            return {
                "ports": device_type_obj.discovery_ports or [],
                "services": device_type_obj.discovery_services or [],
                "keywords": device_type_obj.discovery_keywords or []
            }
        
        # Fallback to registry
        hints = self.registry.get_discovery_hints(device_type)
        if not hints:
            raise ValueError(f"Device type '{device_type}' not found")
        return {
            "ports": hints.get('ports', []),
            "services": hints.get('services', []),
            "keywords": hints.get('keywords', [])
        }
    
    async def suggest_device_types(self, ports: List[int], services: List[str], banner: str = "") -> List[Dict]:
        """Suggest device types based on discovery (enhanced with database)"""
        # Use registry for suggestions (could be enhanced with ML in future)
        suggestions = self.registry.suggest_device_type(ports, services, banner)
        
        result = []
        for device_type_value in suggestions:
            # Try database first
            device_type_obj = await self.repository.get_device_type_by_value(device_type_value)
            if device_type_obj:
                result.append(device_type_obj.to_dict())
            else:
                # Fallback to registry
                registry_type = self.registry.get_device_type(device_type_value)
                if registry_type:
                    result.append({
                        "value": registry_type.value,
                        "label": registry_type.label,
                        "category": registry_type.category.value,
                        "description": registry_type.description,
                        "communication_methods": list(registry_type.communication_methods),
                        "is_system": True
                    })
        
        return result
    
    async def get_valid_device_types(self) -> List[str]:
        """Get list of valid device type values (legacy compatibility)"""
        device_types = await self.get_all_device_types()
        return [dt["value"] for dt in device_types]
    
    async def get_all_communication_methods(self) -> List[str]:
        """Get all available communication methods (legacy compatibility)"""
        device_types = await self.get_all_device_types()
        all_methods = set()
        for dt in device_types:
            all_methods.update(dt.get("communication_methods", []))
        return sorted(list(all_methods))
    
    # Cache Management
    
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
    
    # Initialization
    
    async def initialize_database(self):
        """Initialize database with system device types"""
        await self.repository.initialize_system_device_types()
        await self.invalidate_cache()  # Clear cache after initialization


# Global service instance
device_type_service_v2 = DeviceTypeServiceV2()