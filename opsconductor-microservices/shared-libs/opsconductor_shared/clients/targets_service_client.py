"""
Universal Targets Service Client for inter-service communication
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

from opsconductor_shared.clients.base_client import BaseServiceClient
from opsconductor_shared.models.base import ServiceType

logger = logging.getLogger(__name__)


class TargetsServiceClient(BaseServiceClient):
    """Client for communicating with the Universal Targets Service"""
    
    def __init__(self, targets_service_url: str = "http://universal-targets-service:3001", auth_token: Optional[str] = None):
        super().__init__(
            service_name=ServiceType.JOB_MANAGEMENT,  # Will be overridden by calling service
            base_url=targets_service_url,
            auth_token=auth_token
        )
    
    async def get_target(self, target_id: int, correlation_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """Get target by ID"""
        try:
            response = await self.get(f"/api/v3/targets/{target_id}", correlation_id=correlation_id)
            
            if response.success:
                return response.data
            else:
                logger.warning(f"Failed to get target {target_id}: {response.message}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting target {target_id}: {e}")
            return None
    
    async def get_targets_batch(self, target_ids: List[int], correlation_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get multiple targets by IDs"""
        try:
            response = await self.post(
                "/api/v3/targets/batch",
                data={"target_ids": target_ids},
                correlation_id=correlation_id
            )
            
            if response.success:
                return response.data.get("targets", [])
            else:
                logger.warning(f"Failed to get targets batch: {response.message}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting targets batch: {e}")
            return []
    
    async def list_targets(
        self, 
        skip: int = 0, 
        limit: int = 100,
        target_type: Optional[str] = None,
        status: Optional[str] = None,
        correlation_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """List targets with filtering"""
        try:
            params = {"skip": skip, "limit": limit}
            if target_type:
                params["type"] = target_type
            if status:
                params["status"] = status
            
            response = await self.get("/api/v3/targets", params=params, correlation_id=correlation_id)
            
            if response.success:
                return response.data if isinstance(response.data, list) else response.data.get("targets", [])
            else:
                logger.warning(f"Failed to list targets: {response.message}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing targets: {e}")
            return []
    
    async def get_target_connection_methods(
        self, 
        target_id: int, 
        correlation_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get connection methods for a target"""
        try:
            response = await self.get(f"/api/v3/targets/{target_id}/connection-methods", correlation_id=correlation_id)
            
            if response.success:
                return response.data.get("connection_methods", [])
            else:
                logger.warning(f"Failed to get connection methods for target {target_id}: {response.message}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting connection methods for target {target_id}: {e}")
            return []
    
    async def test_target_connection(
        self, 
        target_id: int, 
        connection_method_id: Optional[int] = None,
        correlation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Test connection to a target"""
        try:
            data = {}
            if connection_method_id:
                data["connection_method_id"] = connection_method_id
            
            response = await self.post(
                f"/api/v3/targets/{target_id}/test-connection",
                data=data,
                correlation_id=correlation_id
            )
            
            if response.success:
                return response.data
            else:
                logger.warning(f"Failed to test connection for target {target_id}: {response.message}")
                return {"success": False, "error": response.message}
                
        except Exception as e:
            logger.error(f"Error testing connection for target {target_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_target_credentials(
        self, 
        target_id: int, 
        connection_method_id: int,
        correlation_id: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """Get credentials for target connection (sensitive operation)"""
        try:
            response = await self.get(
                f"/api/v3/targets/{target_id}/connection-methods/{connection_method_id}/credentials",
                correlation_id=correlation_id
            )
            
            if response.success:
                return response.data
            else:
                logger.warning(f"Failed to get credentials for target {target_id}, method {connection_method_id}: {response.message}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting credentials for target {target_id}, method {connection_method_id}: {e}")
            return None
    
    async def get_targets_by_type(
        self, 
        target_type: str, 
        correlation_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get all targets of a specific type"""
        try:
            response = await self.get(f"/api/v3/targets?type={target_type}", correlation_id=correlation_id)
            
            if response.success:
                return response.data if isinstance(response.data, list) else response.data.get("targets", [])
            else:
                logger.warning(f"Failed to get targets by type {target_type}: {response.message}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting targets by type {target_type}: {e}")
            return []
    
    async def get_healthy_targets(self, correlation_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get all healthy/active targets"""
        try:
            response = await self.get("/api/v3/targets?status=healthy", correlation_id=correlation_id)
            
            if response.success:
                return response.data if isinstance(response.data, list) else response.data.get("targets", [])
            else:
                logger.warning(f"Failed to get healthy targets: {response.message}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting healthy targets: {e}")
            return []
    
    async def validate_targets_exist(
        self, 
        target_ids: List[int], 
        correlation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Validate that targets exist and are accessible"""
        try:
            response = await self.post(
                "/api/v3/targets/validate",
                data={"target_ids": target_ids},
                correlation_id=correlation_id
            )
            
            if response.success:
                return response.data
            else:
                logger.warning(f"Failed to validate targets: {response.message}")
                return {"valid": False, "error": response.message}
                
        except Exception as e:
            logger.error(f"Error validating targets: {e}")
            return {"valid": False, "error": str(e)}
    
    async def get_target_health_status(
        self, 
        target_id: int, 
        correlation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get health status for a target"""
        try:
            response = await self.get(f"/api/v3/targets/{target_id}/health", correlation_id=correlation_id)
            
            if response.success:
                return response.data
            else:
                logger.warning(f"Failed to get health status for target {target_id}: {response.message}")
                return {"healthy": False, "error": response.message}
                
        except Exception as e:
            logger.error(f"Error getting health status for target {target_id}: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def get_targets_summary(self, correlation_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get summary statistics for all targets"""
        try:
            response = await self.get("/api/v3/targets/summary", correlation_id=correlation_id)
            
            if response.success:
                return response.data
            else:
                logger.warning(f"Failed to get targets summary: {response.message}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting targets summary: {e}")
            return {}