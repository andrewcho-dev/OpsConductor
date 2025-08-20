"""
Auth Service Client for communicating with the auth microservice.
"""
import httpx
import os
from typing import Dict, Any, List, Optional
from app.core.logging import get_structured_logger

logger = get_structured_logger(__name__)

class AuthServiceClient:
    def __init__(self):
        self.base_url = os.getenv("AUTH_SERVICE_URL", "http://opsconductor-auth-service:8000")
        self.timeout = 30.0
        
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """Make HTTP request to auth service."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Auth service request failed: {method} {url} - {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling auth service: {str(e)}")
            raise
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID from auth service."""
        try:
            return await self._make_request("GET", f"/users/{user_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def get_users(self, skip: int = 0, limit: int = 100, **filters) -> Dict[str, Any]:
        """Get users list from auth service."""
        params = {"skip": skip, "limit": limit, **filters}
        return await self._make_request("GET", "/users/", params=params)
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics from auth service."""
        return await self._make_request("GET", "/users/stats")
    
    async def create_user(self, user_data: Dict[str, Any], created_by: int) -> Dict[str, Any]:
        """Create user via auth service."""
        headers = {"X-Created-By": str(created_by)}
        return await self._make_request("POST", "/users/", json=user_data, headers=headers)
    
    async def update_user(self, user_id: int, user_data: Dict[str, Any], updated_by: int) -> Dict[str, Any]:
        """Update user via auth service."""
        headers = {"X-Updated-By": str(updated_by)}
        return await self._make_request("PUT", f"/users/{user_id}", json=user_data, headers=headers)
    
    async def delete_user(self, user_id: int, deleted_by: int) -> bool:
        """Delete user via auth service."""
        headers = {"X-Deleted-By": str(deleted_by)}
        try:
            await self._make_request("DELETE", f"/users/{user_id}", headers=headers)
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate token with auth service."""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            return await self._make_request("GET", "/api/auth/me", headers=headers)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [401, 403]:
                return None
            raise

# Singleton instance
auth_client = AuthServiceClient()