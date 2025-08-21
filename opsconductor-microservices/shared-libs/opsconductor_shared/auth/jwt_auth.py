"""
JWT Authentication integration with existing Auth Service
"""

import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


class AuthServiceClient:
    """Client for communicating with the existing Auth Service"""
    
    def __init__(self, auth_service_url: str = "http://auth-service:3000"):
        self.auth_service_url = auth_service_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token with Auth Service"""
        try:
            response = await self.client.post(
                f"{self.auth_service_url}/api/auth/validate",
                headers={"Authorization": f"Bearer {token}"},
                json={"token": token}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Token validation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Auth service communication error: {e}")
            return None
    
    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from token"""
        try:
            response = await self.client.get(
                f"{self.auth_service_url}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"User info retrieval failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Auth service communication error: {e}")
            return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global auth client instance
_auth_client: Optional[AuthServiceClient] = None


def get_auth_client() -> AuthServiceClient:
    """Get or create auth client instance"""
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthServiceClient()
    return _auth_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user from JWT token
    Integrates with existing Auth Service
    """
    try:
        token = credentials.credentials
        auth_client = get_auth_client()
        
        # Validate token with auth service
        validation_result = await auth_client.validate_token(token)
        if not validation_result or not validation_result.get("valid"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user information
        user_info = await auth_client.get_user_info(token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not retrieve user information",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to get current user (optional)
    Returns None if no token provided or invalid
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        auth_client = get_auth_client()
        
        # Validate token with auth service
        validation_result = await auth_client.validate_token(token)
        if not validation_result or not validation_result.get("valid"):
            return None
        
        # Get user information
        user_info = await auth_client.get_user_info(token)
        return user_info
        
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None


def require_permissions(*required_permissions: str):
    """
    Decorator to require specific permissions
    Usage: @require_permissions("jobs:create", "targets:read")
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (injected by FastAPI)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_permissions = current_user.get("permissions", [])
            user_roles = current_user.get("roles", [])
            
            # Check if user has required permissions
            for permission in required_permissions:
                if permission not in user_permissions and "admin" not in user_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission required: {permission}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_roles(*required_roles: str):
    """
    Decorator to require specific roles
    Usage: @require_roles("admin", "operator")
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (injected by FastAPI)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_roles = current_user.get("roles", [])
            
            # Check if user has any of the required roles
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {' or '.join(required_roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator