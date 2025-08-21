"""
Authentication Service
Handles JWT token validation and user authentication
"""

import httpx
import logging
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuthService:
    """Service for handling authentication and authorization"""
    
    def __init__(self):
        self.auth_service_url = settings.auth_service_url
        self.jwt_secret_key = settings.jwt_secret_key
        self.jwt_algorithm = settings.jwt_algorithm
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return user info"""
        try:
            # Decode JWT token
            payload = jwt.decode(
                token, 
                self.jwt_secret_key, 
                algorithms=[self.jwt_algorithm]
            )
            
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID"
                )
            
            # Get additional user info if needed
            user_info = {
                "id": int(user_id),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", [])
            }
            
            return user_info
            
        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed user information from user service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.user_service_url}/api/v1/users/{user_id}",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(f"User service returned {response.status_code} for user {user_id}")
                    return None
                    
        except httpx.RequestError as e:
            logger.error(f"Failed to get user info for {user_id}: {e}")
            return None
    
    async def check_permission(self, user: Dict[str, Any], permission: str) -> bool:
        """Check if user has specific permission"""
        user_permissions = user.get("permissions", [])
        user_roles = user.get("roles", [])
        
        # Check direct permission
        if permission in user_permissions:
            return True
        
        # Check role-based permissions (simplified)
        admin_roles = ["admin", "super_admin"]
        if permission.startswith("job:") and any(role in admin_roles for role in user_roles):
            return True
        
        return False


# Global auth service instance
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    return await auth_service.validate_token(token)


async def require_permission(permission: str):
    """Dependency factory for permission checking"""
    async def check_permission(current_user: Dict[str, Any] = Depends(get_current_user)):
        if not await auth_service.check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return current_user
    return check_permission