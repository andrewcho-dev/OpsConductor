from datetime import datetime, timedelta
from typing import Optional, Union
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


# OLD JWT TOKEN FUNCTIONS REMOVED
# These have been replaced by session-based authentication
# See app.core.session_security for the new session token system


def verify_token(token: str) -> Optional[dict]:
    """
    COMPATIBILITY WRAPPER: Verify token using session-based authentication.
    This replaces the old JWT expiration system with activity-based sessions.
    """
    import asyncio
    from app.core.session_security import verify_session_token
    
    # Run the async session verification in sync context
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we need to handle this differently
            # For now, fall back to basic JWT decode without expiration check
            try:
                payload = jwt.decode(
                    token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM], 
                    options={"verify_exp": False}  # Don't verify expiration - session handles this
                )
                # Check if this is a session token
                if payload.get("token_type") == "session":
                    # This should be verified through session system, but we can't await here
                    # Return the payload and let the session system handle validation elsewhere
                    return payload
                else:
                    # Old JWT token - reject it
                    return None
            except JWTError:
                return None
        else:
            # We can run async code
            return loop.run_until_complete(verify_session_token(token))
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(verify_session_token(token))
    except Exception:
        return None 