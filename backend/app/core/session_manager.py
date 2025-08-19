"""
Activity-based session management system.
Replaces JWT token expiration with Redis-based sliding sessions.
"""
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.shared.infrastructure.cache import cache_service
from app.core.config import settings

class SessionManager:
    """Manages user sessions with activity-based expiration."""
    
    # Session configuration
    SESSION_TIMEOUT_SECONDS = 3600  # 1 hour of inactivity
    WARNING_THRESHOLD_SECONDS = 120  # 2 minutes before timeout
    SESSION_PREFIX = "user_session:"
    ACTIVITY_PREFIX = "user_activity:"
    
    @classmethod
    async def create_session(cls, user_id: int, user_data: Dict[str, Any]) -> str:
        """Create a new user session."""
        await cache_service.initialize()
        
        # Generate session ID (can be simple timestamp + user_id for now)
        session_id = f"{user_id}_{int(time.time())}"
        session_key = f"{cls.SESSION_PREFIX}{session_id}"
        activity_key = f"{cls.ACTIVITY_PREFIX}{session_id}"
        
        # Store session data
        session_data = {
            "user_id": user_id,
            "user_data": user_data,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "session_id": session_id
        }
        
        # Store in Redis with TTL
        await cache_service.set(
            session_key, 
            json.dumps(session_data), 
            ttl=cls.SESSION_TIMEOUT_SECONDS
        )
        
        # Track last activity separately for faster updates
        await cache_service.set(
            activity_key,
            datetime.utcnow().isoformat(),
            ttl=cls.SESSION_TIMEOUT_SECONDS
        )
        
        return session_id
    
    @classmethod
    async def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data if valid."""
        await cache_service.initialize()
        
        session_key = f"{cls.SESSION_PREFIX}{session_id}"
        session_data = await cache_service.get(session_key)
        
        if not session_data:
            return None
            
        try:
            return json.loads(session_data)
        except json.JSONDecodeError:
            return None
    
    @classmethod
    async def update_activity(cls, session_id: str) -> bool:
        """Update last activity timestamp and extend session."""
        await cache_service.initialize()
        
        session_key = f"{cls.SESSION_PREFIX}{session_id}"
        activity_key = f"{cls.ACTIVITY_PREFIX}{session_id}"
        
        # Check if session exists
        session_data = await cache_service.get(session_key)
        if not session_data:
            return False
        
        # Update activity timestamp
        current_time = datetime.utcnow().isoformat()
        await cache_service.set(
            activity_key,
            current_time,
            ttl=cls.SESSION_TIMEOUT_SECONDS
        )
        
        # Update session data with new activity time
        try:
            session_dict = json.loads(session_data)
            session_dict["last_activity"] = current_time
            
            await cache_service.set(
                session_key,
                json.dumps(session_dict),
                ttl=cls.SESSION_TIMEOUT_SECONDS
            )
            return True
        except json.JSONDecodeError:
            return False
    
    @classmethod
    async def get_session_status(cls, session_id: str) -> Dict[str, Any]:
        """Get session status including time remaining."""
        await cache_service.initialize()
        
        session_key = f"{cls.SESSION_PREFIX}{session_id}"
        activity_key = f"{cls.ACTIVITY_PREFIX}{session_id}"
        
        # Get TTL from Redis
        session_ttl = await cache_service.get_ttl(session_key)
        activity_ttl = await cache_service.get_ttl(activity_key)
        
        if session_ttl <= 0:
            return {
                "valid": False,
                "expired": True,
                "time_remaining": 0,
                "warning": False
            }
        
        # Use the shorter TTL (should be the same, but safety check)
        time_remaining = min(session_ttl, activity_ttl) if activity_ttl > 0 else session_ttl
        
        return {
            "valid": True,
            "expired": False,
            "time_remaining": time_remaining,
            "warning": time_remaining <= cls.WARNING_THRESHOLD_SECONDS,
            "warning_threshold": cls.WARNING_THRESHOLD_SECONDS
        }
    
    @classmethod
    async def extend_session(cls, session_id: str, extend_by_seconds: int = None) -> bool:
        """Extend session by specified time or reset to full timeout."""
        if extend_by_seconds is None:
            extend_by_seconds = cls.SESSION_TIMEOUT_SECONDS
            
        return await cls.update_activity(session_id)
    
    @classmethod
    async def destroy_session(cls, session_id: str) -> bool:
        """Destroy a session."""
        await cache_service.initialize()
        
        session_key = f"{cls.SESSION_PREFIX}{session_id}"
        activity_key = f"{cls.ACTIVITY_PREFIX}{session_id}"
        
        # Delete both keys
        await cache_service.delete(session_key)
        await cache_service.delete(activity_key)
        
        return True
    
    @classmethod
    async def cleanup_expired_sessions(cls):
        """Cleanup expired sessions (Redis TTL handles this automatically)."""
        # Redis TTL automatically handles cleanup, but we could add
        # additional cleanup logic here if needed
        pass

# Global session manager instance
session_manager = SessionManager()