"""
JWT Token validation for User Service
"""
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    username: str
    role: str
    permissions: list[str] = []
    exp: Optional[int] = None
    iat: Optional[int] = None


class CurrentUser(BaseModel):
    """Current authenticated user."""
    user_id: str
    username: str
    role: str
    permissions: list[str] = []
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions or self.role in ["admin", "administrator"]
    
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role in ["admin", "administrator"]


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify JWT token and extract user data.
    This validates the token signature without calling auth service.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role", "user")
        permissions: list = payload.get("permissions", [])
        exp: int = payload.get("exp")
        iat: int = payload.get("iat")
        
        logger.debug(f"Token payload: user_id={user_id}, username={username}, role={role}")
        
        if user_id is None or username is None:
            logger.error(f"Missing required fields: user_id={user_id}, username={username}")
            return None
            
        return TokenData(
            user_id=user_id,
            username=username,
            role=role,
            permissions=permissions,
            exp=exp,
            iat=iat
        )
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Get current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = verify_token(credentials.credentials)
        if token_data is None:
            logger.error("Token verification failed - token_data is None")
            raise credentials_exception
            
        return CurrentUser(
            user_id=token_data.user_id,
            username=token_data.username,
            role=token_data.role,
            permissions=token_data.permissions
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise credentials_exception


async def get_current_admin_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Require admin user.
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_permission(permission: str):
    """
    Create a dependency that requires specific permission.
    """
    def permission_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_checker