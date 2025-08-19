"""
Session-based security system replacing JWT token expiration.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.session_manager import session_manager

# Password hashing (keep existing)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_session_token(user_id: int, session_id: str) -> str:
    """
    Create a JWT token that contains session ID instead of expiration.
    This token doesn't expire - the session in Redis controls validity.
    """
    to_encode = {
        "user_id": user_id,
        "session_id": session_id,
        "token_type": "session",
        "issued_at": datetime.utcnow().isoformat()
    }
    
    # Create token without expiration
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify session token and check if session is still valid.
    Returns user data if valid, None if invalid.
    """
    try:
        # Decode JWT (no expiration check)
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        
        session_id = payload.get("session_id")
        user_id = payload.get("user_id")
        
        if not session_id or not user_id:
            return None
        
        # Check if session is still valid in Redis
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            return None
        
        # Verify user_id matches
        if session_data.get("user_id") != user_id:
            return None
        
        # Update activity (this extends the session)
        await session_manager.update_activity(session_id)
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "user_data": session_data.get("user_data", {}),
            "last_activity": session_data.get("last_activity")
        }
        
    except JWTError:
        return None


async def create_user_session(user_id: int, user_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Create a new user session and return session token.
    """
    # Create session in Redis
    session_id = await session_manager.create_session(user_id, user_data)
    
    # Create JWT token with session ID
    access_token = create_session_token(user_id, session_id)
    
    return {
        "access_token": access_token,
        "session_id": session_id,
        "token_type": "bearer"
    }


async def destroy_user_session(session_id: str) -> bool:
    """Destroy a user session."""
    return await session_manager.destroy_session(session_id)


async def get_session_status(session_id: str) -> Dict[str, Any]:
    """Get session status for frontend."""
    return await session_manager.get_session_status(session_id)


async def extend_user_session(session_id: str) -> bool:
    """Extend user session (reset timeout)."""
    return await session_manager.extend_session(session_id)


# Legacy JWT functions removed - all authentication now uses session-based system
# The main verify_token function in app.core.security handles compatibility