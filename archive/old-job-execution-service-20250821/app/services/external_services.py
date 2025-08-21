"""
External Service Clients
Handles communication with other microservices
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class TargetServiceClient:
    """Client for Target Management Service"""
    
    def __init__(self):
        self.base_url = settings.target_service_url
        self.timeout = 30.0
    
    async def get_target(self, target_id: int) -> Optional[Dict[str, Any]]:
        """Get target details by ID"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v3/targets/{target_id}",
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(f"Target service returned {response.status_code} for target {target_id}")
                    return None
                    
        except httpx.RequestError as e:
            logger.error(f"Failed to get target {target_id}: {e}")
            return None
    
    async def get_targets(self, target_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple targets by IDs"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v3/targets/batch",
                    json={"target_ids": target_ids},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json().get("targets", [])
                else:
                    logger.warning(f"Target service returned {response.status_code} for batch request")
                    return []
                    
        except httpx.RequestError as e:
            logger.error(f"Failed to get targets {target_ids}: {e}")
            return []
    
    async def get_target_credentials(self, target_id: int) -> Optional[Dict[str, Any]]:
        """Get target credentials for connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v3/targets/{target_id}/credentials",
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(f"Target service returned {response.status_code} for credentials {target_id}")
                    return None
                    
        except httpx.RequestError as e:
            logger.error(f"Failed to get credentials for target {target_id}: {e}")
            return None
    
    async def test_target_connection(self, target_id: int) -> Dict[str, Any]:
        """Test connection to target"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v3/targets/{target_id}/test",
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "success": False,
                        "error": f"Target service returned {response.status_code}"
                    }
                    
        except httpx.RequestError as e:
            logger.error(f"Failed to test target {target_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class NotificationServiceClient:
    """Client for Notification Service"""
    
    def __init__(self):
        self.base_url = settings.notification_service_url
        self.timeout = 10.0
    
    async def send_job_notification(
        self, 
        user_id: int, 
        job_id: int, 
        job_name: str,
        event_type: str,
        details: Dict[str, Any]
    ) -> bool:
        """Send job-related notification"""
        try:
            notification_data = {
                "user_id": user_id,
                "type": "job_notification",
                "title": f"Job {event_type}: {job_name}",
                "message": self._format_job_message(event_type, job_name, details),
                "data": {
                    "job_id": job_id,
                    "job_name": job_name,
                    "event_type": event_type,
                    **details
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/notifications",
                    json=notification_data,
                    timeout=self.timeout
                )
                
                return response.status_code == 201
                
        except httpx.RequestError as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def _format_job_message(self, event_type: str, job_name: str, details: Dict[str, Any]) -> str:
        """Format job notification message"""
        if event_type == "started":
            return f"Job '{job_name}' has started execution on {details.get('target_count', 0)} targets"
        elif event_type == "completed":
            success = details.get('successful_targets', 0)
            failed = details.get('failed_targets', 0)
            return f"Job '{job_name}' completed: {success} successful, {failed} failed"
        elif event_type == "failed":
            return f"Job '{job_name}' failed: {details.get('error', 'Unknown error')}"
        elif event_type == "cancelled":
            return f"Job '{job_name}' was cancelled"
        else:
            return f"Job '{job_name}' status: {event_type}"


class AuditServiceClient:
    """Client for Audit Service"""
    
    def __init__(self):
        self.base_url = settings.notification_service_url  # Assuming audit is part of main service
        self.timeout = 10.0
    
    async def log_job_event(
        self,
        user_id: int,
        event_type: str,
        resource_id: str,
        action: str,
        details: Dict[str, Any]
    ) -> bool:
        """Log job-related audit event"""
        try:
            audit_data = {
                "user_id": user_id,
                "event_type": event_type,
                "resource_type": "job",
                "resource_id": resource_id,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "job-execution-service"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/audit/events",
                    json=audit_data,
                    timeout=self.timeout
                )
                
                return response.status_code in [200, 201]
                
        except httpx.RequestError as e:
            logger.error(f"Failed to log audit event: {e}")
            return False


# Global service clients
target_service = TargetServiceClient()
notification_service = NotificationServiceClient()
audit_service = AuditServiceClient()