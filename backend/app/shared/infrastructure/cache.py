"""
Caching infrastructure for ENABLEDRM platform.
"""
import json
import pickle
import asyncio
from typing import Any, Optional, Union, Callable, Dict
from datetime import datetime, timedelta
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Multi-level caching service with Redis and in-memory cache."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.redis_url = redis_url
        self.default_ttl = 3600  # 1 hour
        self.memory_cache_max_size = 1000
    
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
            await self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache only: {e}")
            self.redis_client = None
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache (memory first, then Redis)."""
        # Check memory cache first
        if key in self.memory_cache:
            cache_entry = self.memory_cache[key]
            if cache_entry["expires_at"] > datetime.now():
                logger.debug(f"Cache hit (memory): {key}")
                return cache_entry["value"]
            else:
                # Expired, remove from memory cache
                del self.memory_cache[key]
        
        # Check Redis cache
        if self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value is not None:
                    logger.debug(f"Cache hit (Redis): {key}")
                    # Deserialize value
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return pickle.loads(value)
            except Exception as e:
                logger.error(f"Redis get error for key {key}: {e}")
        
        logger.debug(f"Cache miss: {key}")
        return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        memory_cache: bool = True
    ) -> bool:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        
        # Store in memory cache
        if memory_cache:
            # Clean up memory cache if it's getting too large
            if len(self.memory_cache) >= self.memory_cache_max_size:
                await self._cleanup_memory_cache()
            
            self.memory_cache[key] = {
                "value": value,
                "expires_at": datetime.now() + timedelta(seconds=ttl)
            }
        
        # Store in Redis cache
        if self.redis_client:
            try:
                # Serialize value
                try:
                    serialized_value = json.dumps(value)
                except (TypeError, ValueError):
                    serialized_value = pickle.dumps(value)
                
                await self.redis_client.setex(key, ttl, serialized_value)
                logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
                return True
            except Exception as e:
                logger.error(f"Redis set error for key {key}: {e}")
        
        return memory_cache  # Return True if at least memory cache worked
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        # Remove from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Remove from Redis cache
        if self.redis_client:
            try:
                result = await self.redis_client.delete(key)
                logger.debug(f"Cache delete: {key}")
                return bool(result)
            except Exception as e:
                logger.error(f"Redis delete error for key {key}: {e}")
        
        return True
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        # Check memory cache
        if key in self.memory_cache:
            cache_entry = self.memory_cache[key]
            if cache_entry["expires_at"] > datetime.now():
                return True
            else:
                del self.memory_cache[key]
        
        # Check Redis cache
        if self.redis_client:
            try:
                return bool(await self.redis_client.exists(key))
            except Exception as e:
                logger.error(f"Redis exists error for key {key}: {e}")
        
        return False
    
    async def get_or_set(
        self, 
        key: str, 
        factory: Callable[[], Any], 
        ttl: Optional[int] = None
    ) -> Any:
        """Get value from cache or set it using factory function."""
        value = await self.get(key)
        if value is not None:
            return value
        
        # Generate value using factory
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        await self.set(key, value, ttl)
        return value
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value in cache."""
        if self.redis_client:
            try:
                return await self.redis_client.incrby(key, amount)
            except Exception as e:
                logger.error(f"Redis increment error for key {key}: {e}")
        
        # Fallback to memory cache
        current_value = await self.get(key, 0)
        new_value = int(current_value) + amount
        await self.set(key, new_value)
        return new_value
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key."""
        if self.redis_client:
            try:
                return bool(await self.redis_client.expire(key, ttl))
            except Exception as e:
                logger.error(f"Redis expire error for key {key}: {e}")
        
        # Update memory cache expiration
        if key in self.memory_cache:
            self.memory_cache[key]["expires_at"] = datetime.now() + timedelta(seconds=ttl)
            return True
        
        return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        count = 0
        
        # Clear from memory cache
        keys_to_delete = []
        for key in self.memory_cache.keys():
            if self._match_pattern(key, pattern):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.memory_cache[key]
            count += 1
        
        # Clear from Redis cache
        if self.redis_client:
            try:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    count += deleted
            except Exception as e:
                logger.error(f"Redis clear pattern error for pattern {pattern}: {e}")
        
        logger.debug(f"Cleared {count} keys matching pattern: {pattern}")
        return count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_max_size": self.memory_cache_max_size,
            "redis_available": self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                stats.update({
                    "redis_used_memory": info.get("used_memory_human"),
                    "redis_connected_clients": info.get("connected_clients"),
                    "redis_total_commands_processed": info.get("total_commands_processed")
                })
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")
        
        return stats
    
    async def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry["expires_at"] <= now
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # If still too large, remove oldest entries
        if len(self.memory_cache) >= self.memory_cache_max_size:
            # Sort by expiration time and remove oldest
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1]["expires_at"]
            )
            
            # Remove oldest 20% of entries
            remove_count = len(sorted_items) // 5
            for key, _ in sorted_items[:remove_count]:
                del self.memory_cache[key]
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for memory cache."""
        if "*" not in pattern:
            return key == pattern
        
        # Simple wildcard matching
        parts = pattern.split("*")
        if len(parts) == 2:
            prefix, suffix = parts
            return key.startswith(prefix) and key.endswith(suffix)
        
        return False


# Global cache service instance
from app.core.config import settings
cache_service = CacheService(redis_url=settings.REDIS_URL)


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_parts = []
    
    # Add positional arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            key_parts.append(str(hash(str(arg))))
    
    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}:{v}")
        else:
            key_parts.append(f"{k}:{hash(str(v))}")
    
    return ":".join(key_parts)


def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            func_name = f"{func.__module__}.{func.__name__}"
            key = f"{key_prefix}:{func_name}:{cache_key(*args, **kwargs)}" if key_prefix else f"{func_name}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            result = await cache_service.get(key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(key, result, ttl)
            return result
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async cache easily
            # This is a simplified version
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator