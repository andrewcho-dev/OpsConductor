"""
Fallback models when opsconductor_shared is not available
"""

from enum import Enum
from typing import Any, Dict


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class EventType(str, Enum):
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed" 
    JOB_FAILED = "job_failed"
    TARGET_CONNECTED = "target_connected"
    TARGET_DISCONNECTED = "target_disconnected"
    HEALTH_CHECK = "health_check"
    SYSTEM_ALERT = "system_alert"


class ServiceType(str, Enum):
    AUTH = "auth-service"
    USER_MANAGEMENT = "user-service"
    TARGET_MANAGEMENT = "targets-service"
    JOB_MANAGEMENT = "jobs-service"
    JOB_EXECUTION = "execution-service"
    TARGET_DISCOVERY = "target-discovery-service"
    AUDIT_EVENTS = "audit-events-service"
    NOTIFICATION = "notification-service"


class EventPublisher:
    """Fallback event publisher"""
    
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url
        # For now, just log events instead of publishing
        import logging
        self.logger = logging.getLogger(__name__)
    
    async def publish_event(self, event_type: EventType, data: Dict[str, Any]):
        """Log event instead of publishing to message broker"""
        self.logger.info(f"EVENT: {event_type.value} - {data}")
    
    def publish_event_sync(self, event_type: EventType, data: Dict[str, Any]):
        """Synchronous version for non-async contexts"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"EVENT: {event_type.value} - {data}")


class BaseServiceClient:
    """Fallback service client for HTTP requests"""
    
    def __init__(self, service_type: ServiceType, base_url: str):
        self.service_type = service_type
        self.base_url = base_url
        import logging
        self.logger = logging.getLogger(__name__)
    
    def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback GET method - returns mock response"""
        self.logger.warning(f"FALLBACK: GET {self.base_url}{endpoint} (shared libs not available)")
        return {"status": "error", "error": "Service client not available (shared libs missing)"}
    
    def post(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback POST method - returns mock response"""
        self.logger.warning(f"FALLBACK: POST {self.base_url}{endpoint} (shared libs not available)")
        return {"status": "error", "error": "Service client not available (shared libs missing)"}
    
    def put(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback PUT method - returns mock response"""
        self.logger.warning(f"FALLBACK: PUT {self.base_url}{endpoint} (shared libs not available)")
        return {"status": "error", "error": "Service client not available (shared libs missing)"}
    
    def delete(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback DELETE method - returns mock response"""
        self.logger.warning(f"FALLBACK: DELETE {self.base_url}{endpoint} (shared libs not available)")
        return {"status": "error", "error": "Service client not available (shared libs missing)"}