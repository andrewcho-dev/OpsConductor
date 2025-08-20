from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_session_token(user_id: int, session_id: str, user_data: Dict[str, Any] = None) -> str:
    """
    Create a JWT token that contains session ID and user info.
    This token doesn't expire - the session in Redis controls validity.
    """
    to_encode = {
        "user_id": user_id,
        "session_id": session_id,
        "token_type": "session",
        "issued_at": datetime.utcnow().isoformat()
    }
    
    # Add user information for microservices compatibility
    if user_data:
        to_encode.update({
            "sub": str(user_id),  # Standard JWT subject field
            "username": user_data.get("username"),
            "role": user_data.get("role", "user"),
            "permissions": user_data.get("permissions", []),
            "email": user_data.get("email")
        })
    
    # Create token without expiration
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token without expiration check.
    Returns payload if valid, None if invalid.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None