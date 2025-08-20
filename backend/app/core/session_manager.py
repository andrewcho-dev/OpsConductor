"""
Activity-based session management system.
Replaces JWT token expiration with Redis-based sliding sessions.
"""
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.shared.infrastructure.cache import cache_service
from app.core.config import settings
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions with activity-based expiration."""
    
    # Default session configuration (will be overridden by system settings)
    DEFAULT_SESSION_TIMEOUT_MINUTES = 60  # 60 minutes of inactivity
    DEFAULT_WARNING_THRESHOLD_MINUTES = 2  # 2 minutes before timeout
    SESSION_PREFIX = "user_session:"
    ACTIVITY_PREFIX = "user_activity:"
    
    @classmethod
    async def _log_session_event(cls, event_type: AuditEventType, user_id: int, session_id: str, details: Dict[str, Any], ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
        """
        Log a session-related audit event.
        
        Args:
            event_type: Type of audit event
            user_id: ID of the user
            session_id: ID of the session
            details: Additional details about the event
            ip_address: IP address of the client
            user_agent: User agent of the client
        """
        try:
            # Create a database session
            db = SessionLocal()
            
            # Create audit service
            audit_service = AuditService(db)
            
            # Log the event
            await audit_service.log_event(
                event_type=event_type,
                user_id=user_id,
                resource_type="session",
                resource_id=session_id,
                action=event_type.value,
                details=details,
                severity=AuditSeverity.INFO,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Close the database session
            db.close()
        except Exception as e:
            logger.error(f"Failed to log session event: {str(e)}")
    
    @classmethod
    async def _get_timeout_settings(cls) -> tuple:
        """Get timeout settings from system settings or use defaults."""
        try:
            # Create a database session
            db = SessionLocal()
            
            # Get system settings
            from app.services.system_service import SystemService
            system_service = SystemService(db)
            
            # Get timeout settings
            timeout_minutes = system_service.get_inactivity_timeout()
            warning_minutes = system_service.get_warning_time()
            
            # Close the database session
            db.close()
            
            # Ensure minimum timeout of 480 minutes (8 hours)
            timeout_minutes = max(timeout_minutes, 480)
            
            # Convert to seconds
            timeout_seconds = timeout_minutes * 60
            warning_seconds = warning_minutes * 60
            
            logger.info(f"Using session timeout: {timeout_minutes} minutes ({timeout_seconds} seconds)")
            return timeout_seconds, warning_seconds
        except Exception as e:
            logger.error(f"Failed to get timeout settings: {str(e)}")
            # Use defaults - minimum 8 hours (480 minutes)
            default_timeout = max(cls.DEFAULT_SESSION_TIMEOUT_MINUTES, 480) * 60
            default_warning = cls.DEFAULT_WARNING_THRESHOLD_MINUTES * 60
            logger.info(f"Using default session timeout: {default_timeout // 60} minutes ({default_timeout} seconds)")
            return default_timeout, default_warning
    
    @classmethod
    async def create_session(cls, user_id: int, user_data: Dict[str, Any]) -> str:
        """Create a new user session."""
        await cache_service.initialize()
        
        # Get timeout settings
        timeout_seconds, _ = await cls._get_timeout_settings()
        
        # Ensure minimum timeout of 8 hours (480 minutes) to prevent quick expiration
        timeout_seconds = max(timeout_seconds, 28800)  # 8 hours in seconds
        
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
        
        # Store in Redis with longer TTL to ensure session doesn't expire quickly
        await cache_service.set(
            session_key, 
            json.dumps(session_data), 
            ttl=timeout_seconds
        )
        
        # Track last activity separately for faster updates
        await cache_service.set(
            activity_key,
            datetime.utcnow().isoformat(),
            ttl=timeout_seconds
        )
        
        # Log session creation with timeout
        logger.info(f"Created new session {session_id} for user {user_id} with timeout {timeout_seconds} seconds")
        
        # Log session creation
        ip_address = user_data.get("client_ip")
        user_agent = user_data.get("user_agent")
        
        await cls._log_session_event(
            event_type=AuditEventType.SESSION_CREATED,
            user_id=user_id,
            session_id=session_id,
            details={
                "username": user_data.get("username"),
                "created_at": session_data["created_at"],
                "expires_in_seconds": timeout_seconds,
                "timeout_minutes": timeout_seconds // 60
            },
            ip_address=ip_address,
            user_agent=user_agent
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
        
        # Get timeout settings - use a longer default timeout to prevent quick expiration
        timeout_seconds, _ = await cls._get_timeout_settings()
        
        # Ensure minimum timeout of 8 hours (480 minutes) to prevent quick expiration
        timeout_seconds = max(timeout_seconds, 28800)  # 8 hours in seconds
        
        session_key = f"{cls.SESSION_PREFIX}{session_id}"
        activity_key = f"{cls.ACTIVITY_PREFIX}{session_id}"
        
        # Check if session exists
        session_data = await cache_service.get(session_key)
        if not session_data:
            return False
        
        # Update activity timestamp
        current_time = datetime.utcnow().isoformat()
        
        # Set with longer TTL to ensure session doesn't expire quickly
        await cache_service.set(
            activity_key,
            current_time,
            ttl=timeout_seconds
        )
        
        # Update session data with new activity time
        try:
            session_dict = json.loads(session_data)
            session_dict["last_activity"] = current_time
            
            # Set with longer TTL to ensure session doesn't expire quickly
            await cache_service.set(
                session_key,
                json.dumps(session_dict),
                ttl=timeout_seconds
            )
            
            # Log successful session extension
            logger.info(f"Session {session_id} activity updated, extended for {timeout_seconds} seconds")
            return True
        except json.JSONDecodeError:
            logger.error(f"Failed to parse session data for {session_id}")
            return False
    
    @classmethod
    async def get_session_status(cls, session_id: str) -> Dict[str, Any]:
        """Get session status including time remaining."""
        await cache_service.initialize()
        
        # Get timeout settings
        timeout_seconds, warning_seconds = await cls._get_timeout_settings()
        
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
                "warning": False,
                "warning_threshold": warning_seconds
            }
        
        # Use the shorter TTL (should be the same, but safety check)
        time_remaining = min(session_ttl, activity_ttl) if activity_ttl > 0 else session_ttl
        
        return {
            "valid": True,
            "expired": False,
            "time_remaining": time_remaining,
            "warning": time_remaining <= warning_seconds,
            "warning_threshold": warning_seconds
        }
    
    @classmethod
    async def extend_session(cls, session_id: str, extend_by_seconds: int = None, user_id: Optional[int] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """
        Extend session by specified time or reset to full timeout.
        
        Args:
            session_id: ID of the session to extend
            extend_by_seconds: Number of seconds to extend the session by
            user_id: ID of the user (for audit logging)
            ip_address: IP address of the client (for audit logging)
            user_agent: User agent of the client (for audit logging)
            
        Returns:
            bool: True if session was extended
        """
        # Get timeout settings from system settings
        timeout_seconds, _ = await cls._get_timeout_settings()
        
        # Ensure minimum timeout of 8 hours (480 minutes) to prevent quick expiration
        timeout_seconds = max(timeout_seconds, 28800)  # 8 hours in seconds
        
        if extend_by_seconds is None:
            extend_by_seconds = timeout_seconds
        else:
            # Ensure minimum extension time
            extend_by_seconds = max(extend_by_seconds, 28800)  # 8 hours in seconds
        
        # Update activity
        result = await cls.update_activity(session_id)
        
        if result:
            # Get session data for audit logging
            session_data = None
            try:
                session_key = f"{cls.SESSION_PREFIX}{session_id}"
                session_json = await cache_service.get(session_key)
                if session_json:
                    session_data = json.loads(session_json)
            except Exception as e:
                logger.warning(f"Failed to get session data for audit logging: {str(e)}")
            
            # Log session extension
            if session_data:
                # Use user_id from session data if not provided
                if user_id is None:
                    user_id = session_data.get("user_id")
                
                # Log the event
                await cls._log_session_event(
                    event_type=AuditEventType.SESSION_EXTENDED,
                    user_id=user_id,
                    session_id=session_id,
                    details={
                        "username": session_data.get("user_data", {}).get("username"),
                        "created_at": session_data.get("created_at"),
                        "last_activity": session_data.get("last_activity"),
                        "extended_at": datetime.utcnow().isoformat(),
                        "extended_by_seconds": extend_by_seconds
                    },
                    ip_address=ip_address,
                    user_agent=user_agent
                )
        
        return result
    
    @classmethod
    async def destroy_session(cls, session_id: str, user_id: Optional[int] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """
        Destroy a session.
        
        Args:
            session_id: ID of the session to destroy
            user_id: ID of the user (for audit logging)
            ip_address: IP address of the client (for audit logging)
            user_agent: User agent of the client (for audit logging)
            
        Returns:
            bool: True if session was destroyed
        """
        await cache_service.initialize()
        
        session_key = f"{cls.SESSION_PREFIX}{session_id}"
        activity_key = f"{cls.ACTIVITY_PREFIX}{session_id}"
        
        # Get session data for audit logging before deletion
        session_data = None
        try:
            session_json = await cache_service.get(session_key)
            if session_json:
                session_data = json.loads(session_json)
        except Exception as e:
            logger.warning(f"Failed to get session data for audit logging: {str(e)}")
        
        # Delete both keys
        await cache_service.delete(session_key)
        await cache_service.delete(activity_key)
        
        # Log session termination
        if session_data:
            # Use user_id from session data if not provided
            if user_id is None:
                user_id = session_data.get("user_id")
            
            # Log the event
            await cls._log_session_event(
                event_type=AuditEventType.SESSION_TERMINATED,
                user_id=user_id,
                session_id=session_id,
                details={
                    "username": session_data.get("user_data", {}).get("username"),
                    "created_at": session_data.get("created_at"),
                    "last_activity": session_data.get("last_activity"),
                    "terminated_at": datetime.utcnow().isoformat()
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        return True
    
    @classmethod
    async def cleanup_expired_sessions(cls):
        """
        Cleanup expired sessions.
        
        Redis TTL automatically handles cleanup of expired keys, but this method
        can be used to perform additional cleanup tasks or logging.
        """
        # Redis TTL automatically handles cleanup, but we can log the event
        # for audit purposes if we have a way to detect expired sessions
        
        # This is a placeholder for future implementation
        # We could scan Redis for sessions that are about to expire and log them
        
        # For now, we'll just log a system maintenance event
        try:
            # Create a database session
            db = SessionLocal()
            
            # Create audit service
            audit_service = AuditService(db)
            
            # Log the event
            await audit_service.log_event(
                event_type=AuditEventType.SYSTEM_MAINTENANCE,
                user_id=None,  # System operation
                resource_type="session",
                resource_id="cleanup",
                action="cleanup_expired_sessions",
                details={
                    "timestamp": datetime.utcnow().isoformat(),
                    "note": "Redis TTL automatically handles session expiration"
                },
                severity=AuditSeverity.INFO
            )
            
            # Close the database session
            db.close()
        except Exception as e:
            logger.error(f"Failed to log session cleanup event: {str(e)}")

# Global session manager instance
session_manager = SessionManager()