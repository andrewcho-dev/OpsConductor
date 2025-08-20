"""
Activity-based session management system.
Replaces JWT token expiration with Redis-based sliding sessions.
"""
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions with activity-based expiration."""
    
    SESSION_PREFIX = "auth_session:"
    ACTIVITY_PREFIX = "auth_activity:"
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    def _get_timeout_settings(self) -> tuple:
        """Get timeout settings from configuration."""
        timeout_seconds = settings.SESSION_TIMEOUT_MINUTES * 60
        warning_seconds = settings.SESSION_WARNING_MINUTES * 60
        
        # Ensure minimum timeout of 8 hours (480 minutes)
        timeout_seconds = max(timeout_seconds, 28800)  # 8 hours in seconds
        
        logger.info(f"Using session timeout: {timeout_seconds // 60} minutes ({timeout_seconds} seconds)")
        return timeout_seconds, warning_seconds
    
    async def create_session(self, user_id: int, user_data: Dict[str, Any]) -> str:
        """Create a new user session."""
        # Get timeout settings
        timeout_seconds, _ = self._get_timeout_settings()
        
        # Generate session ID
        session_id = f"{user_id}_{int(time.time())}"
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        activity_key = f"{self.ACTIVITY_PREFIX}{session_id}"
        
        # Store session data
        session_data = {
            "user_id": user_id,
            "user_data": user_data,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "session_id": session_id
        }
        
        # Store in Redis with TTL
        self.redis_client.setex(
            session_key, 
            timeout_seconds,
            json.dumps(session_data)
        )
        
        # Track last activity separately for faster updates
        self.redis_client.setex(
            activity_key,
            timeout_seconds,
            datetime.utcnow().isoformat()
        )
        
        logger.info(f"Created new session {session_id} for user {user_id} with timeout {timeout_seconds} seconds")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data if valid."""
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_data = self.redis_client.get(session_key)
        
        if not session_data:
            return None
            
        try:
            return json.loads(session_data)
        except json.JSONDecodeError:
            return None
    
    async def update_activity(self, session_id: str) -> bool:
        """Update last activity timestamp and extend session."""
        # Get timeout settings
        timeout_seconds, _ = self._get_timeout_settings()
        
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        activity_key = f"{self.ACTIVITY_PREFIX}{session_id}"
        
        # Check if session exists
        session_data = self.redis_client.get(session_key)
        if not session_data:
            return False
        
        # Update activity timestamp
        current_time = datetime.utcnow().isoformat()
        
        # Set with TTL
        self.redis_client.setex(
            activity_key,
            timeout_seconds,
            current_time
        )
        
        # Update session data with new activity time
        try:
            session_dict = json.loads(session_data)
            session_dict["last_activity"] = current_time
            
            # Set with TTL
            self.redis_client.setex(
                session_key,
                timeout_seconds,
                json.dumps(session_dict)
            )
            
            logger.info(f"Session {session_id} activity updated, extended for {timeout_seconds} seconds")
            return True
        except json.JSONDecodeError:
            logger.error(f"Failed to parse session data for {session_id}")
            return False
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get session status including time remaining."""
        # Get timeout settings
        timeout_seconds, warning_seconds = self._get_timeout_settings()
        
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        
        # Get TTL from Redis
        session_ttl = self.redis_client.ttl(session_key)
        
        if session_ttl <= 0:
            return {
                "valid": False,
                "expired": True,
                "time_remaining": 0,
                "warning": False,
                "warning_threshold": warning_seconds
            }
        
        return {
            "valid": True,
            "expired": False,
            "time_remaining": session_ttl,
            "warning": session_ttl <= warning_seconds,
            "warning_threshold": warning_seconds
        }
    
    async def extend_session(self, session_id: str) -> bool:
        """Extend session by resetting to full timeout."""
        return await self.update_activity(session_id)
    
    async def destroy_session(self, session_id: str) -> bool:
        """Destroy a session."""
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        activity_key = f"{self.ACTIVITY_PREFIX}{session_id}"
        
        # Delete both keys
        deleted_count = self.redis_client.delete(session_key, activity_key)
        
        logger.info(f"Destroyed session {session_id}, deleted {deleted_count} keys")
        return deleted_count > 0


# Global session manager instance
session_manager = SessionManager()