"""
User Service Client for Auth Service
AUTHENTICATION ONLY - NO USER MANAGEMENT!
"""
import logging
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserServiceClient:
    """Client for communicating with User Service - AUTH ONLY."""
    
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.timeout = 30.0
    
    async def verify_user_exists(self, username: str) -> bool:
        """Verify if user exists in User Service (for auth validation only)."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/users/exists/{username}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("exists", False)
                else:
                    logger.error(f"User service error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error calling user service: {e}")
            return False


# Global instance
user_service_client = UserServiceClient()