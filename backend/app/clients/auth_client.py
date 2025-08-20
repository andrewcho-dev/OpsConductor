"""
Auth Service Client for Main Backend
Handles communication with the separate auth microservice.
"""
import httpx
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthClient:
    """Client for communicating with the auth service."""
    
    def __init__(self):
        self.auth_service_url = getattr(settings, 'AUTH_SERVICE_URL', 'http://opsconductor-auth-service:8000')
        self.timeout = 10.0
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate token with auth service.
        
        Args:
            token: JWT token to validate
            
        Returns:
            User information if valid, None if invalid
        """
        try:
            logger.info(f"Validating token with auth service at {self.auth_service_url}")
            logger.info(f"Token being validated: {token[:50]}...")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.auth_service_url}/api/auth/validate",
                    json={"token": token}
                )
                
                logger.info(f"Auth service response: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Token validation result: valid={result.get('valid')}")
                    logger.info(f"Full auth service response: {result}")
                    if result.get("valid"):
                        return result
                    else:
                        logger.warning(f"Token validation failed: {result.get('error')}")
                        return None
                else:
                    logger.error(f"Auth service returned {response.status_code}: {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Auth service timeout during token validation")
            return None
        except httpx.RequestError as e:
            logger.error(f"Auth service request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}")
            return None
    
    async def get_session_status(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get session status from auth service.
        
        Args:
            token: JWT token
            
        Returns:
            Session status information
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.auth_service_url}/api/auth/session/status",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Auth service returned {response.status_code}: {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Auth service timeout during session status check")
            return None
        except httpx.RequestError as e:
            logger.error(f"Auth service request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during session status check: {e}")
            return None
    
    async def extend_session(self, token: str) -> bool:
        """
        Extend session via auth service.
        
        Args:
            token: JWT token
            
        Returns:
            True if session was extended successfully
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.auth_service_url}/api/auth/session/extend",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                return response.status_code == 200
                    
        except httpx.TimeoutException:
            logger.error("Auth service timeout during session extension")
            return False
        except httpx.RequestError as e:
            logger.error(f"Auth service request error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during session extension: {e}")
            return False
    
    async def logout(self, token: str) -> bool:
        """
        Logout user via auth service.
        
        Args:
            token: JWT token
            
        Returns:
            True if logout was successful
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.auth_service_url}/api/auth/logout",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                return response.status_code == 200
                    
        except httpx.TimeoutException:
            logger.error("Auth service timeout during logout")
            return False
        except httpx.RequestError as e:
            logger.error(f"Auth service request error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during logout: {e}")
            return False


# Global auth client instance
auth_client = AuthClient()