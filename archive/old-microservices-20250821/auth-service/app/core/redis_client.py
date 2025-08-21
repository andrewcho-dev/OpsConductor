"""
Redis client for session management
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisSessionManager:
    """Redis-based session management"""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        self.login_attempts_prefix = "login_attempts:"
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def create_session(
        self,
        session_id: str,
        user_id: int,
        user_data: Dict[str, Any],
        expires_in_minutes: int = None
    ) -> bool:
        """Create a new session"""
        if not self.redis_client:
            await self.connect()
        
        try:
            expires_in = expires_in_minutes or settings.SESSION_EXPIRE_MINUTES
            expiry_time = datetime.utcnow() + timedelta(minutes=expires_in)
            
            session_data = {
                "user_id": user_id,
                "user_data": user_data,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expiry_time.isoformat(),
                "last_activity": datetime.utcnow().isoformat()
            }
            
            # Store session
            session_key = f"{self.session_prefix}{session_id}"
            await self.redis_client.setex(
                session_key,
                timedelta(minutes=expires_in),
                json.dumps(session_data)
            )
            
            # Track user sessions
            await self._add_user_session(user_id, session_id, expires_in)
            
            logger.info(f"Session created for user {user_id}: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if not self.redis_client:
            await self.connect()
        
        try:
            session_key = f"{self.session_prefix}{session_id}"
            session_data = await self.redis_client.get(session_key)
            
            if session_data:
                data = json.loads(session_data)
                
                # Update last activity
                data["last_activity"] = datetime.utcnow().isoformat()
                await self.redis_client.setex(
                    session_key,
                    timedelta(minutes=settings.SESSION_EXPIRE_MINUTES),
                    json.dumps(data)
                )
                
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if not self.redis_client:
            await self.connect()
        
        try:
            # Get session to find user_id
            session_data = await self.get_session(session_id)
            if session_data:
                user_id = session_data.get("user_id")
                if user_id:
                    await self._remove_user_session(user_id, session_id)
            
            # Delete session
            session_key = f"{self.session_prefix}{session_id}"
            result = await self.redis_client.delete(session_key)
            
            logger.info(f"Session deleted: {session_id}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    async def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user"""
        if not self.redis_client:
            await self.connect()
        
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            session_ids = await self.redis_client.smembers(user_sessions_key)
            
            deleted_count = 0
            for session_id in session_ids:
                session_key = f"{self.session_prefix}{session_id}"
                if await self.redis_client.delete(session_key):
                    deleted_count += 1
            
            # Clear user sessions set
            await self.redis_client.delete(user_sessions_key)
            
            logger.info(f"Deleted {deleted_count} sessions for user {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete user sessions: {e}")
            return 0
    
    async def get_user_sessions(self, user_id: int) -> List[str]:
        """Get all session IDs for a user"""
        if not self.redis_client:
            await self.connect()
        
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            session_ids = await self.redis_client.smembers(user_sessions_key)
            return list(session_ids)
            
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        if not self.redis_client:
            await self.connect()
        
        try:
            # This is handled automatically by Redis TTL, but we can implement
            # additional cleanup logic here if needed
            logger.info("Session cleanup completed (handled by Redis TTL)")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")
            return 0
    
    # Login attempt tracking
    
    async def record_login_attempt(self, identifier: str, success: bool) -> None:
        """Record a login attempt"""
        if not self.redis_client:
            await self.connect()
        
        try:
            key = f"{self.login_attempts_prefix}{identifier}"
            
            if success:
                # Clear failed attempts on successful login
                await self.redis_client.delete(key)
            else:
                # Increment failed attempts
                attempts = await self.redis_client.incr(key)
                if attempts == 1:
                    # Set expiry on first failed attempt
                    await self.redis_client.expire(key, settings.LOCKOUT_DURATION_MINUTES * 60)
                
                logger.warning(f"Failed login attempt {attempts} for {identifier}")
                
        except Exception as e:
            logger.error(f"Failed to record login attempt: {e}")
    
    async def get_login_attempts(self, identifier: str) -> int:
        """Get number of failed login attempts"""
        if not self.redis_client:
            await self.connect()
        
        try:
            key = f"{self.login_attempts_prefix}{identifier}"
            attempts = await self.redis_client.get(key)
            return int(attempts) if attempts else 0
            
        except Exception as e:
            logger.error(f"Failed to get login attempts: {e}")
            return 0
    
    async def is_locked_out(self, identifier: str) -> bool:
        """Check if identifier is locked out"""
        attempts = await self.get_login_attempts(identifier)
        return attempts >= settings.MAX_LOGIN_ATTEMPTS
    
    # Helper methods
    
    async def _add_user_session(self, user_id: int, session_id: str, expires_in: int):
        """Add session to user's session set"""
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            await self.redis_client.sadd(user_sessions_key, session_id)
            await self.redis_client.expire(user_sessions_key, expires_in * 60)
            
            # Enforce max sessions per user
            session_count = await self.redis_client.scard(user_sessions_key)
            if session_count > settings.MAX_SESSIONS_PER_USER:
                # Remove oldest sessions (this is a simple implementation)
                sessions = await self.redis_client.smembers(user_sessions_key)
                sessions_to_remove = list(sessions)[:session_count - settings.MAX_SESSIONS_PER_USER]
                
                for old_session_id in sessions_to_remove:
                    await self.delete_session(old_session_id)
                    
        except Exception as e:
            logger.error(f"Failed to add user session: {e}")
    
    async def _remove_user_session(self, user_id: int, session_id: str):
        """Remove session from user's session set"""
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            await self.redis_client.srem(user_sessions_key, session_id)
            
        except Exception as e:
            logger.error(f"Failed to remove user session: {e}")


# Global session manager instance
session_manager = RedisSessionManager()