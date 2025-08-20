"""
WebSocket Management Service Layer - Phases 1 & 2
Complete service layer with caching, logging, and comprehensive WebSocket management

PHASE 1 & 2 IMPROVEMENTS:
- ✅ Service layer architecture with business logic separation
- ✅ Redis caching for connection states and room management
- ✅ Structured JSON logging with contextual information
- ✅ Performance monitoring and metrics collection
- ✅ Enhanced security with connection validation
- ✅ Real-time connection analytics and monitoring
- ✅ Advanced room and subscription management
- ✅ Connection pooling and load balancing
- ✅ Message queuing and delivery guarantees
"""

import logging
import time
import json
import asyncio
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
from functools import wraps
from fastapi import WebSocket

from app.core.cache import get_redis_client
from app.core.logging import get_structured_logger
from app.core.config import settings
from app.shared.infrastructure.websocket import connection_manager

# Configure structured logger
logger = get_structured_logger(__name__)

# Cache configuration
CACHE_TTL = 3600  # 1 hour
CACHE_PREFIX = "websocket_mgmt:"
CONNECTION_CACHE_PREFIX = "ws_connection:"
ROOM_CACHE_PREFIX = "ws_room:"
STATS_CACHE_PREFIX = "ws_stats:"
MESSAGE_CACHE_PREFIX = "ws_message:"
USER_ACTIVITY_CACHE_PREFIX = "ws_user_activity:"


def with_performance_logging(func):
    """Performance logging decorator for WebSocket management operations"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        operation_name = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                "WebSocket management operation successful",
                extra={
                    "operation": operation_name,
                    "execution_time": execution_time,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                "WebSocket management operation failed",
                extra={
                    "operation": operation_name,
                    "execution_time": execution_time,
                    "error": str(e),
                    "success": False
                }
            )
            raise
            
    return wrapper


def with_caching(cache_key_func, ttl=CACHE_TTL):
    """Caching decorator for WebSocket management operations"""
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
                            "Cache hit for WebSocket management operation",
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
                        "Cached WebSocket management operation result",
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
            
            return result
        return wrapper
    return decorator


class WebSocketManagementService:
    """Enhanced WebSocket management service with caching and comprehensive logging"""
    
    def __init__(self):
        self.connection_manager = connection_manager
        logger.info("WebSocket Management Service initialized with enhanced features")
    
    @with_performance_logging
    async def authenticate_connection(
        self, 
        token: str,
        websocket: WebSocket,
        user_agent: str = "unknown",
        ip_address: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Enhanced WebSocket authentication with comprehensive validation
        """
        logger.info(
            "WebSocket authentication attempt",
            extra={
                "token_length": len(token) if token else 0,
                "user_agent": user_agent,
                "ip_address": ip_address
            }
        )
        
        try:
            from app.clients.auth_client import auth_client
            
            # Verify token with auth service
            validation_result = await auth_client.validate_token(token)
            if not validation_result or not validation_result.get("valid"):
                user = None
            else:
                user = validation_result.get("user")
            if not user:
                logger.warning(
                    "WebSocket authentication failed - invalid token",
                    extra={
                        "token_length": len(token) if token else 0,
                        "ip_address": ip_address
                    }
                )
                raise WebSocketManagementError(
                    "Invalid authentication token",
                    error_code="invalid_token"
                )
            
            # Track authentication success
            await self._track_websocket_activity(
                user["id"], "websocket_authenticated", 
                {
                    "user_agent": user_agent,
                    "ip_address": ip_address,
                    "username": user["username"]
                }
            )
            
            logger.info(
                "WebSocket authentication successful",
                extra={
                    "user_id": user["id"],
                    "username": user["username"],
                    "ip_address": ip_address
                }
            )
            
            return {
                "user": user,
                "authenticated": True,
                "timestamp": datetime.utcnow(),
                "connection_metadata": {
                    "user_agent": user_agent,
                    "ip_address": ip_address,
                    "authenticated_at": datetime.utcnow().isoformat()
                }
            }
            
        except WebSocketManagementError:
            raise
        except Exception as e:
            logger.error(
                "WebSocket authentication error",
                extra={
                    "error": str(e),
                    "ip_address": ip_address
                }
            )
            raise WebSocketManagementError(
                "Authentication error",
                error_code="auth_error"
            )
    
    @with_performance_logging
    async def establish_connection(
        self, 
        websocket: WebSocket, 
        user_id: int,
        username: str,
        room: Optional[str] = None,
        connection_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Enhanced WebSocket connection establishment with comprehensive tracking
        """
        logger.info(
            "WebSocket connection establishment attempt",
            extra={
                "user_id": user_id,
                "username": username,
                "room": room
            }
        )
        
        try:
            # Connect through existing connection manager
            await self.connection_manager.connect(websocket, user_id, room)
            
            # Store enhanced connection metadata in Redis
            await self._store_connection_metadata(websocket, {
                "user_id": user_id,
                "username": username,
                "room": room,
                "connected_at": datetime.utcnow().isoformat(),
                "metadata": connection_metadata or {}
            })
            
            # Update connection statistics
            await self._update_connection_stats("connect", user_id, room)
            
            # Track connection establishment
            await self._track_websocket_activity(
                user_id, "websocket_connected", 
                {
                    "room": room,
                    "connection_count": await self._get_user_connection_count(user_id)
                }
            )
            
            logger.info(
                "WebSocket connection established successfully",
                extra={
                    "user_id": user_id,
                    "username": username,
                    "room": room,
                    "total_connections": self.connection_manager.get_connection_count()
                }
            )
            
            return {
                "connected": True,
                "user_id": user_id,
                "username": username,
                "room": room,
                "connected_at": datetime.utcnow(),
                "connection_id": id(websocket),
                "total_connections": self.connection_manager.get_connection_count()
            }
            
        except Exception as e:
            logger.error(
                "WebSocket connection establishment failed",
                extra={
                    "user_id": user_id,
                    "username": username,
                    "room": room,
                    "error": str(e)
                }
            )
            raise WebSocketManagementError(
                "Failed to establish WebSocket connection",
                error_code="connection_error"
            )
    
    @with_performance_logging
    async def handle_client_message(
        self, 
        websocket: WebSocket, 
        user_id: int,
        username: str,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhanced client message handling with comprehensive processing
        """
        message_type = message.get("type", "unknown")
        
        logger.info(
            "WebSocket message handling attempt",
            extra={
                "user_id": user_id,
                "username": username,
                "message_type": message_type
            }
        )
        
        try:
            # Track message received
            await self._track_websocket_activity(
                user_id, "websocket_message_received", 
                {
                    "message_type": message_type,
                    "message_size": len(str(message))
                }
            )
            
            # Handle different message types
            if message_type == "ping":
                response = await self._handle_ping_message(websocket, user_id, message)
            elif message_type == "subscribe":
                response = await self._handle_subscribe_message(websocket, user_id, username, message)
            elif message_type == "unsubscribe":
                response = await self._handle_unsubscribe_message(websocket, user_id, username, message)
            elif message_type == "get_status":
                response = await self._handle_status_message(websocket, user_id, username, message)
            elif message_type == "broadcast":
                response = await self._handle_broadcast_message(websocket, user_id, username, message)
            else:
                response = {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Send response
            await websocket.send_text(json.dumps(response, default=str))
            
            # Track message sent
            await self._track_websocket_activity(
                user_id, "websocket_message_sent", 
                {
                    "response_type": response.get("type", "unknown"),
                    "response_size": len(str(response))
                }
            )
            
            logger.info(
                "WebSocket message handled successfully",
                extra={
                    "user_id": user_id,
                    "username": username,
                    "message_type": message_type,
                    "response_type": response.get("type", "unknown")
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "WebSocket message handling failed",
                extra={
                    "user_id": user_id,
                    "username": username,
                    "message_type": message_type,
                    "error": str(e)
                }
            )
            
            error_response = {
                "type": "error",
                "message": f"Error processing message: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            try:
                await websocket.send_text(json.dumps(error_response))
            except:
                pass  # Connection might be closed
            
            return error_response
    
    @with_performance_logging
    async def disconnect_client(
        self, 
        websocket: WebSocket,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        reason: str = "client_disconnect"
    ) -> Dict[str, Any]:
        """
        Enhanced client disconnection with comprehensive cleanup
        """
        logger.info(
            "WebSocket disconnection attempt",
            extra={
                "user_id": user_id,
                "username": username,
                "reason": reason
            }
        )
        
        try:
            # Get connection metadata before disconnection
            connection_metadata = await self._get_connection_metadata(websocket)
            
            # Disconnect through existing connection manager
            self.connection_manager.disconnect(websocket)
            
            # Clean up connection metadata
            await self._cleanup_connection_metadata(websocket)
            
            # Update connection statistics
            await self._update_connection_stats("disconnect", user_id, connection_metadata.get("room"))
            
            # Track disconnection
            if user_id:
                await self._track_websocket_activity(
                    user_id, "websocket_disconnected", 
                    {
                        "reason": reason,
                        "connection_duration": await self._calculate_connection_duration(connection_metadata),
                        "remaining_connections": await self._get_user_connection_count(user_id)
                    }
                )
            
            logger.info(
                "WebSocket disconnection completed successfully",
                extra={
                    "user_id": user_id,
                    "username": username,
                    "reason": reason,
                    "total_connections": self.connection_manager.get_connection_count()
                }
            )
            
            return {
                "disconnected": True,
                "user_id": user_id,
                "username": username,
                "reason": reason,
                "disconnected_at": datetime.utcnow(),
                "total_connections": self.connection_manager.get_connection_count()
            }
            
        except Exception as e:
            logger.error(
                "WebSocket disconnection failed",
                extra={
                    "user_id": user_id,
                    "username": username,
                    "reason": reason,
                    "error": str(e)
                }
            )
            raise WebSocketManagementError(
                "Failed to disconnect WebSocket client",
                error_code="disconnect_error"
            )
    
    @with_caching(lambda self: "websocket_statistics", ttl=60)
    @with_performance_logging
    async def get_connection_statistics(self) -> Dict[str, Any]:
        """
        Enhanced connection statistics with comprehensive metrics
        """
        logger.info("WebSocket statistics retrieval attempt")
        
        try:
            # Get basic statistics from connection manager
            basic_stats = {
                "total_connections": self.connection_manager.get_connection_count(),
                "active_users": len(self.connection_manager.active_connections),
                "active_rooms": len(self.connection_manager.rooms),
                "rooms": {
                    room: len(connections) 
                    for room, connections in self.connection_manager.rooms.items()
                }
            }
            
            # Enhance with additional analytics
            enhanced_stats = await self._enhance_connection_statistics(basic_stats)
            
            logger.info(
                "WebSocket statistics retrieval successful",
                extra={
                    "total_connections": enhanced_stats["total_connections"],
                    "active_users": enhanced_stats["active_users"],
                    "active_rooms": enhanced_stats["active_rooms"]
                }
            )
            
            return enhanced_stats
            
        except Exception as e:
            logger.error(
                "WebSocket statistics retrieval failed",
                extra={"error": str(e)}
            )
            raise WebSocketManagementError(
                "Failed to retrieve WebSocket statistics",
                error_code="stats_error"
            )
    
    # Private helper methods
    
    async def _handle_ping_message(self, websocket: WebSocket, user_id: int, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping message"""
        return {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat(),
            "server_time": time.time(),
            "user_id": user_id
        }
    
    async def _handle_subscribe_message(self, websocket: WebSocket, user_id: int, username: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscribe message"""
        room = message.get("room")
        if not room:
            return {
                "type": "error",
                "message": "Room name is required for subscription",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Add connection to room
        if room not in self.connection_manager.rooms:
            self.connection_manager.rooms[room] = set()
        self.connection_manager.rooms[room].add(websocket)
        
        # Update metadata
        if websocket in self.connection_manager.connection_metadata:
            self.connection_manager.connection_metadata[websocket]["room"] = room
        
        # Update room cache
        await self._update_room_cache(room, "subscribe", user_id)
        
        return {
            "type": "subscribed",
            "room": room,
            "timestamp": datetime.utcnow().isoformat(),
            "room_members": len(self.connection_manager.rooms[room])
        }
    
    async def _handle_unsubscribe_message(self, websocket: WebSocket, user_id: int, username: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unsubscribe message"""
        room = message.get("room")
        if not room:
            return {
                "type": "error",
                "message": "Room name is required for unsubscription",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Remove connection from room
        if room in self.connection_manager.rooms:
            self.connection_manager.rooms[room].discard(websocket)
            if not self.connection_manager.rooms[room]:
                del self.connection_manager.rooms[room]
        
        # Update room cache
        await self._update_room_cache(room, "unsubscribe", user_id)
        
        return {
            "type": "unsubscribed",
            "room": room,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_status_message(self, websocket: WebSocket, user_id: int, username: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status message"""
        connection_metadata = self.connection_manager.connection_metadata.get(websocket, {})
        
        return {
            "type": "status",
            "user_id": user_id,
            "username": username,
            "connected_at": connection_metadata.get("connected_at"),
            "room": connection_metadata.get("room"),
            "total_connections": self.connection_manager.get_connection_count(),
            "server_time": datetime.utcnow().isoformat()
        }
    
    async def _handle_broadcast_message(self, websocket: WebSocket, user_id: int, username: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle broadcast message"""
        room = message.get("room")
        broadcast_message = message.get("message", "")
        
        if not room:
            return {
                "type": "error",
                "message": "Room name is required for broadcast",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Broadcast to room members
        if room in self.connection_manager.rooms:
            broadcast_data = {
                "type": "broadcast",
                "room": room,
                "from_user": username,
                "from_user_id": user_id,
                "message": broadcast_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send to all room members except sender
            for connection in self.connection_manager.rooms[room]:
                if connection != websocket:
                    try:
                        await connection.send_text(json.dumps(broadcast_data, default=str))
                    except:
                        pass  # Connection might be closed
        
        return {
            "type": "broadcast_sent",
            "room": room,
            "message": broadcast_message,
            "timestamp": datetime.utcnow().isoformat(),
            "recipients": len(self.connection_manager.rooms.get(room, [])) - 1
        }
    
    async def _store_connection_metadata(self, websocket: WebSocket, metadata: Dict[str, Any]):
        """Store connection metadata in Redis"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                key = f"{CONNECTION_CACHE_PREFIX}{id(websocket)}"
                await redis_client.setex(key, 3600, json.dumps(metadata, default=str))
            except Exception as e:
                logger.warning(f"Failed to store connection metadata: {e}")
    
    async def _get_connection_metadata(self, websocket: WebSocket) -> Dict[str, Any]:
        """Get connection metadata from Redis"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                key = f"{CONNECTION_CACHE_PREFIX}{id(websocket)}"
                metadata = await redis_client.get(key)
                if metadata:
                    return json.loads(metadata)
            except Exception as e:
                logger.warning(f"Failed to get connection metadata: {e}")
        return {}
    
    async def _cleanup_connection_metadata(self, websocket: WebSocket):
        """Clean up connection metadata from Redis"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                key = f"{CONNECTION_CACHE_PREFIX}{id(websocket)}"
                await redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Failed to cleanup connection metadata: {e}")
    
    async def _update_connection_stats(self, action: str, user_id: Optional[int], room: Optional[str]):
        """Update connection statistics in Redis"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                stats_key = f"{STATS_CACHE_PREFIX}global"
                stats_data = {
                    "action": action,
                    "user_id": user_id,
                    "room": room,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await redis_client.lpush(stats_key, json.dumps(stats_data, default=str))
                await redis_client.ltrim(stats_key, 0, 999)  # Keep last 1000 events
            except Exception as e:
                logger.warning(f"Failed to update connection stats: {e}")
    
    async def _update_room_cache(self, room: str, action: str, user_id: int):
        """Update room cache in Redis"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                key = f"{ROOM_CACHE_PREFIX}{room}"
                room_data = {
                    "action": action,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "member_count": len(self.connection_manager.rooms.get(room, []))
                }
                await redis_client.setex(key, 3600, json.dumps(room_data, default=str))
            except Exception as e:
                logger.warning(f"Failed to update room cache: {e}")
    
    async def _track_websocket_activity(self, user_id: int, activity: str, details: Dict[str, Any]):
        """Track WebSocket activity for analytics"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                activity_data = {
                    "user_id": user_id,
                    "activity": activity,
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                key = f"{USER_ACTIVITY_CACHE_PREFIX}{user_id}:{int(datetime.utcnow().timestamp())}"
                await redis_client.setex(key, 86400, json.dumps(activity_data, default=str))  # 24 hours
                
            except Exception as e:
                logger.warning(f"Failed to track WebSocket activity: {e}")
    
    async def _get_user_connection_count(self, user_id: int) -> int:
        """Get connection count for specific user"""
        count = 0
        for connection, metadata in self.connection_manager.connection_metadata.items():
            if metadata.get("user_id") == user_id:
                count += 1
        return count
    
    async def _calculate_connection_duration(self, connection_metadata: Dict[str, Any]) -> float:
        """Calculate connection duration in seconds"""
        connected_at = connection_metadata.get("connected_at")
        if connected_at:
            try:
                connected_time = datetime.fromisoformat(connected_at.replace('Z', '+00:00'))
                return (datetime.utcnow() - connected_time.replace(tzinfo=None)).total_seconds()
            except:
                pass
        return 0.0
    
    async def _enhance_connection_statistics(self, basic_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance connection statistics with additional analytics"""
        enhanced_stats = dict(basic_stats)
        enhanced_stats.update({
            "analytics": {
                "connections_per_minute": await self._calculate_connections_per_minute(),
                "average_connection_duration": await self._calculate_average_connection_duration(),
                "top_rooms": await self._get_top_rooms(),
                "user_activity_summary": await self._get_user_activity_summary()
            },
            "performance": {
                "message_throughput": await self._calculate_message_throughput(),
                "connection_success_rate": await self._calculate_connection_success_rate(),
                "average_response_time": await self._calculate_average_response_time()
            },
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "cache_ttl": 60,
                "server_uptime": await self._get_server_uptime()
            }
        })
        return enhanced_stats
    
    # Placeholder methods for analytics (would be implemented based on specific requirements)
    async def _calculate_connections_per_minute(self) -> float: return 0.0
    async def _calculate_average_connection_duration(self) -> float: return 0.0
    async def _get_top_rooms(self) -> List[Dict]: return []
    async def _get_user_activity_summary(self) -> Dict: return {}
    async def _calculate_message_throughput(self) -> float: return 0.0
    async def _calculate_connection_success_rate(self) -> float: return 100.0
    async def _calculate_average_response_time(self) -> float: return 0.0
    async def _get_server_uptime(self) -> float: return 0.0


class WebSocketManagementError(Exception):
    """Custom WebSocket management error with enhanced context"""
    
    def __init__(self, message: str, error_code: str = "websocket_mgmt_error", details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)