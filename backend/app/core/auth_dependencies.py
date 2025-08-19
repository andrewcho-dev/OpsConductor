"""
Centralized authentication dependencies for all routers.
This ensures consistent authentication across the entire application.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.database import get_db
from app.core.session_security import verify_session_token
from app.services.user_service import UserService

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Centralized authentication dependency.
    Returns user information from session-based authentication.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user_info = await verify_session_token(token)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get full user details from database
    user_id = user_info.get("user_id")
    if user_id:
        user = UserService.get_user_by_id(db, user_id)
        if user:
            # Return combined user info with session data
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "session_info": {
                    "session_id": user_info.get("session_id"),
                    "last_activity": user_info.get("last_activity")
                }
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


def require_admin_role(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Require administrator role for access."""
    if current_user.get("role") != "administrator":
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
        user_info = await verify_session_token(token)
        return user_info
    except Exception:
        # If token is invalid, return None instead of raising error
        return None