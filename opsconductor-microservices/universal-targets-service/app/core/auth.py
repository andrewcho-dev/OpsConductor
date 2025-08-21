"""
Authentication dependencies for Universal Targets Service
"""

from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from opsconductor_shared.auth.jwt_auth import get_current_user as shared_get_current_user
from opsconductor_shared.clients.user_service_client import UserServiceClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# User service client for additional user operations
user_service_client = UserServiceClient(settings.USER_SERVICE_URL)


async def get_current_user(
    current_user: Dict[str, Any] = Depends(shared_get_current_user)
) -> Dict[str, Any]:
    """
    Get current authenticated user with additional validation
    """
    try:
        # The shared auth dependency already validates the token
        # We can add additional service-specific validation here if needed
        
        # Update user activity
        if current_user.get("id"):
            try:
                await user_service_client.update_user_last_activity(
                    user_id=current_user["id"],
                    activity_type="targets_api_access"
                )
            except Exception as e:
                logger.warning(f"Failed to update user activity: {e}")
        
        return current_user
        
    except Exception as e:
        logger.error(f"Authentication error in targets service: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    current_user: Optional[Dict[str, Any]] = Depends(shared_get_current_user)
) -> Optional[Dict[str, Any]]:
    """
    Get current user (optional) - for endpoints that work with or without auth
    """
    return current_user


def require_permission(permission: str):
    """
    Dependency factory to require specific permission
    """
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_permissions = current_user.get("permissions", [])
        user_roles = current_user.get("roles", [])
        
        # Check if user has required permission or is admin
        if permission not in user_permissions and "admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        
        return current_user
    
    return permission_checker


def require_role(role: str):
    """
    Dependency factory to require specific role
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])
        
        # Check if user has required role
        if role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role}"
            )
        
        return current_user
    
    return role_checker


# Common permission dependencies
require_targets_read = require_permission("targets:read")
require_targets_write = require_permission("targets:write")
require_targets_delete = require_permission("targets:delete")
require_targets_test = require_permission("targets:test")
require_admin_role = require_role("admin")