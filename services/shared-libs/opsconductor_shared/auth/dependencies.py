"""
Authentication dependencies for FastAPI services
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import logging

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service_url: str = "http://auth-service:8000"
) -> dict:
    """
    Validate JWT token with auth service and return current user
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{auth_service_url}/api/auth/validate",
                json={"token": credentials.credentials},
                timeout=5.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            validation_result = response.json()
            
            if not validation_result.get("valid"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return validation_result.get("user")
            
    except httpx.RequestError as e:
        logger.error(f"Failed to validate token with auth service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current active user (must be active)
    """
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current superuser (must be superuser)
    """
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def require_permissions(*required_permissions: str):
    """
    Dependency factory for requiring specific permissions
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_permissions = set(current_user.get("permissions", []))
        required_perms = set(required_permissions)
        
        if not required_perms.issubset(user_permissions):
            missing_perms = required_perms - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_perms)}"
            )
        
        return current_user
    
    return permission_checker


def require_roles(*required_roles: str):
    """
    Dependency factory for requiring specific roles
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_roles = set(current_user.get("roles", []))
        required_role_set = set(required_roles)
        
        if not required_role_set.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker