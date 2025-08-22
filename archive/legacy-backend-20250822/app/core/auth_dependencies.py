"""
Centralized authentication dependencies for all routers.
This ensures consistent authentication across the entire application.
Now uses the auth service client for token validation.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.database import get_db
from app.clients.auth_client import auth_client

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Centralized authentication dependency.
    Returns user information from auth service validation.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Auth dependency called")
    
    if not credentials:
        logger.warning("No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    logger.info(f"Validating token: {token[:50]}...")
    validation_result = await auth_client.validate_token(token)
    
    if not validation_result or not validation_result.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_info = validation_result.get("user")
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return user info from auth service
    return {
        "id": user_info.get("id"),
        "username": user_info.get("username"),
        "email": user_info.get("email"),
        "role": user_info.get("role"),
        "is_active": user_info.get("is_active"),
        "session_info": {
            "session_id": validation_result.get("session_id"),
            "last_activity": None  # Auth service handles this internally
        }
    }


def require_admin_role(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Require administrator role for access."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return current_user


def require_active_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Require active user status."""
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    return current_user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> Dict[str, Any] | None:
    """
    Optional authentication dependency.
    Returns user information if valid token provided, None otherwise.
    Used for endpoints that can work with or without authentication.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        validation_result = await auth_client.validate_token(token)
        
        if validation_result and validation_result.get("valid"):
            user_info = validation_result.get("user")
            if user_info:
                return {
                    "id": user_info.get("id"),
                    "username": user_info.get("username"),
                    "email": user_info.get("email"),
                    "role": user_info.get("role"),
                    "is_active": user_info.get("is_active"),
                    "session_info": {
                        "session_id": validation_result.get("session_id"),
                        "last_activity": None
                    }
                }
        return None
    except Exception:
        # If token is invalid, return None instead of raising error
        return None