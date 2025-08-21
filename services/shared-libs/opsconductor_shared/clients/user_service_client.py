"""
User Service Client for inter-service communication
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

from opsconductor_shared.clients.base_client import BaseServiceClient
from opsconductor_shared.models.base import ServiceType

logger = logging.getLogger(__name__)


class UserServiceClient(BaseServiceClient):
    """Client for communicating with the User Service"""
    
    def __init__(self, user_service_url: str = "http://user-service:3002", auth_token: Optional[str] = None):
        super().__init__(
            service_name=ServiceType.JOB_MANAGEMENT,  # Will be overridden by calling service
            base_url=user_service_url,
            auth_token=auth_token
        )
    
    async def get_user(self, user_id: int, correlation_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            response = await self.get(f"/api/users/{user_id}", correlation_id=correlation_id)
            
            if response.success:
                return response.data
            else:
                logger.warning(f"Failed to get user {user_id}: {response.message}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def get_users_batch(self, user_ids: List[int], correlation_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get multiple users by IDs"""
        try:
            response = await self.post(
                "/api/users/batch",
                data={"user_ids": user_ids},
                correlation_id=correlation_id
            )
            
            if response.success:
                return response.data.get("users", [])
            else:
                logger.warning(f"Failed to get users batch: {response.message}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting users batch: {e}")
            return []
    
    async def get_user_by_email(self, email: str, correlation_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            response = await self.get(f"/api/users/email/{email}", correlation_id=correlation_id)
            
            if response.success:
                return response.data
            else:
                logger.warning(f"Failed to get user by email {email}: {response.message}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def get_user_permissions(self, user_id: int, correlation_id: Optional[UUID] = None) -> List[str]:
        """Get user permissions"""
        try:
            response = await self.get(f"/api/users/{user_id}/permissions", correlation_id=correlation_id)
            
            if response.success:
                return response.data.get("permissions", [])
            else:
                logger.warning(f"Failed to get permissions for user {user_id}: {response.message}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting permissions for user {user_id}: {e}")
            return []
    
    async def get_user_roles(self, user_id: int, correlation_id: Optional[UUID] = None) -> List[str]:
        """Get user roles"""
        try:
            response = await self.get(f"/api/users/{user_id}/roles", correlation_id=correlation_id)
            
            if response.success:
                return response.data.get("roles", [])
            else:
                logger.warning(f"Failed to get roles for user {user_id}: {response.message}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting roles for user {user_id}: {e}")
            return []
    
    async def check_user_permission(
        self, 
        user_id: int, 
        permission: str, 
        correlation_id: Optional[UUID] = None
    ) -> bool:
        """Check if user has specific permission"""
        try:
            response = await self.post(
                f"/api/users/{user_id}/check-permission",
                data={"permission": permission},
                correlation_id=correlation_id
            )
            
            if response.success:
                return response.data.get("has_permission", False)
            else:
                logger.warning(f"Failed to check permission {permission} for user {user_id}: {response.message}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking permission {permission} for user {user_id}: {e}")
            return False
    
    async def check_user_role(
        self, 
        user_id: int, 
        role: str, 
        correlation_id: Optional[UUID] = None
    ) -> bool:
        """Check if user has specific role"""
        try:
            response = await self.post(
                f"/api/users/{user_id}/check-role",
                data={"role": role},
                correlation_id=correlation_id
            )
            
            if response.success:
                return response.data.get("has_role", False)
            else:
                logger.warning(f"Failed to check role {role} for user {user_id}: {response.message}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking role {role} for user {user_id}: {e}")
            return False
    
    async def get_active_users(self, correlation_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get all active users"""
        try:
            response = await self.get("/api/users?status=active", correlation_id=correlation_id)
            
            if response.success:
                return response.data.get("users", [])
            else:
                logger.warning(f"Failed to get active users: {response.message}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    async def update_user_last_activity(
        self, 
        user_id: int, 
        activity_type: str = "api_access",
        correlation_id: Optional[UUID] = None
    ) -> bool:
        """Update user's last activity timestamp"""
        try:
            response = await self.post(
                f"/api/users/{user_id}/activity",
                data={"activity_type": activity_type},
                correlation_id=correlation_id
            )
            
            return response.success
                
        except Exception as e:
            logger.error(f"Error updating last activity for user {user_id}: {e}")
            return False
    
    async def get_user_stats(self, user_id: int, correlation_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            response = await self.get(f"/api/users/{user_id}/stats", correlation_id=correlation_id)
            
            if response.success:
                return response.data
            else:
                logger.warning(f"Failed to get stats for user {user_id}: {response.message}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting stats for user {user_id}: {e}")
            return {}