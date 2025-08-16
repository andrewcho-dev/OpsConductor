"""
Redis Cache Utility
Provides Redis connection and caching functionality for the application

PHASE 2 IMPROVEMENTS:
- ✅ Redis connection management
- ✅ Connection pooling
- ✅ Error handling
- ✅ Health checks
"""

import logging
from typing import Optional
import os
from functools import lru_cache

# Handle Redis import gracefully
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    # Create mock Redis for graceful fallback
    class MockRedis:
        async def ping(self): return True
        async def get(self, key): return None
        async def setex(self, key, ttl, value): return True
        async def delete(self, *keys): return len(keys)
        async def keys(self, pattern): return []
        async def close(self): pass
        async def info(self): return {"redis_version": "mock", "connected_clients": 1}
    
    class MockConnectionPool:
        async def disconnect(self): pass
    
    # Mock redis module
    class redis:
        ConnectionPool = MockConnectionPool
        Redis = MockRedis

logger = logging.getLogger(__name__)

# Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


@lru_cache(maxsize=1)
def get_redis_config():
    """Get Redis configuration from environment"""
    # Check for REDIS_URL first, then fall back to individual settings
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        # Parse redis://redis:6379 format
        if redis_url.startswith('redis://'):
            url_parts = redis_url.replace('redis://', '').split(':')
            host = url_parts[0] if len(url_parts) > 0 else 'localhost'
            port = int(url_parts[1]) if len(url_parts) > 1 else 6379
        else:
            host = 'localhost'
            port = 6379
    else:
        host = os.getenv('REDIS_HOST', 'redis')  # Default to 'redis' service name
        port = int(os.getenv('REDIS_PORT', 6379))
    
    return {
        'host': host,
        'port': port,
        'db': int(os.getenv('REDIS_DB', 0)),
        'password': os.getenv('REDIS_PASSWORD'),
        'decode_responses': True,
        'socket_connect_timeout': 5,
        'socket_timeout': 5,
        'retry_on_timeout': True,
        'health_check_interval': 30
    }


async def initialize_redis():
    """Initialize Redis connection pool"""
    global _redis_pool, _redis_client
    
    if not REDIS_AVAILABLE:
        logger.warning("Redis not available, using mock implementation")
        _redis_client = redis.Redis()
        return
    
    try:
        config = get_redis_config()
        
        # Create connection pool
        _redis_pool = redis.ConnectionPool(**config)
        
        # Create Redis client
        _redis_client = redis.Redis(connection_pool=_redis_pool)
        
        # Test connection
        await _redis_client.ping()
        
        logger.info(
            "Redis connection initialized successfully",
            extra={
                "host": config['host'],
                "port": config['port'],
                "db": config['db']
            }
        )
        
    except Exception as e:
        logger.warning(
            "Redis connection failed, using mock implementation",
            extra={"error": str(e)}
        )
        _redis_client = redis.Redis()  # Use mock
        _redis_pool = None


async def close_redis():
    """Close Redis connections"""
    global _redis_pool, _redis_client
    
    try:
        if _redis_client and REDIS_AVAILABLE:
            await _redis_client.close()
            _redis_client = None
            
        if _redis_pool and REDIS_AVAILABLE:
            await _redis_pool.disconnect()
            _redis_pool = None
            
        logger.info("Redis connections closed")
        
    except Exception as e:
        logger.error(
            "Error closing Redis connections",
            extra={"error": str(e)}
        )


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance"""
    return _redis_client


async def is_redis_available() -> bool:
    """Check if Redis is available"""
    if not _redis_client:
        return False
    
    try:
        await _redis_client.ping()
        return True
    except Exception:
        return False


async def get_redis_info() -> dict:
    """Get Redis server information"""
    if not _redis_client:
        return {"status": "unavailable", "error": "Redis client not initialized"}
    
    try:
        info = await _redis_client.info()
        return {
            "status": "available",
            "version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory": info.get("used_memory_human"),
            "uptime": info.get("uptime_in_seconds")
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


class CacheManager:
    """High-level cache management utility"""
    
    def __init__(self, prefix: str = "", default_ttl: int = 3600):
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.client = get_redis_client()
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.prefix}:{key}" if self.prefix else key
    
    async def get(self, key: str, default=None):
        """Get value from cache"""
        if not self.client:
            return default
        
        try:
            value = await self.client.get(self._make_key(key))
            return value if value is not None else default
        except Exception as e:
            logger.warning(
                "Cache get failed",
                extra={"key": key, "error": str(e)}
            )
            return default
    
    async def set(self, key: str, value: str, ttl: int = None):
        """Set value in cache"""
        if not self.client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            await self.client.setex(self._make_key(key), ttl, value)
            return True
        except Exception as e:
            logger.warning(
                "Cache set failed",
                extra={"key": key, "error": str(e)}
            )
            return False
    
    async def delete(self, key: str):
        """Delete value from cache"""
        if not self.client:
            return False
        
        try:
            await self.client.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.warning(
                "Cache delete failed",
                extra={"key": key, "error": str(e)}
            )
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.client:
            return False
        
        try:
            return bool(await self.client.exists(self._make_key(key)))
        except Exception as e:
            logger.warning(
                "Cache exists check failed",
                extra={"key": key, "error": str(e)}
            )
            return False
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.client:
            return 0
        
        try:
            full_pattern = self._make_key(pattern)
            keys = await self.client.keys(full_pattern)
            if keys:
                await self.client.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.warning(
                "Cache pattern clear failed",
                extra={"pattern": pattern, "error": str(e)}
            )
            return 0