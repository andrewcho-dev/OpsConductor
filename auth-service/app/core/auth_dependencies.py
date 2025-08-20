"""
Authentication dependencies for FastAPI endpoints - AUTHENTICATION ONLY!
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    token = authorization.split(" ")[1]
    
    try:
        # Validate token using AuthService
        validation_result = await AuthService.validate_token(token)
        
        if not validation_result.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=validation_result.error or "Invalid token"
            )
        
        # Get the actual User object from database
        user = db.query(User).filter(User.id == validation_result.user.id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role for endpoint access - PLACEHOLDER ONLY."""
    # NOTE: Role checking should be done by user-service
    # This is kept minimal for auth service config endpoints only
    return current_user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if token is provided, otherwise return None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None