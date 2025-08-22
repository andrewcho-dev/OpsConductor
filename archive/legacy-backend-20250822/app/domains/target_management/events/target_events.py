"""
Target Management Domain Events
"""
# Removed dataclass import as we're using regular classes
from datetime import datetime
from typing import Dict, Any, List
import uuid

from app.shared.infrastructure.events import DomainEvent


class TargetCreatedEvent(DomainEvent):
    """Event raised when a target is created."""
    
    def __init__(self, target_id: int, target_name: str, target_type: str, host: str, port: int, created_by: int):
        self.target_id = target_id
        self.target_name = target_name
        self.target_type = target_type
        self.host = host
        self.port = port
        self.created_by = created_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(target_id),
            aggregate_type="Target"
        )


class TargetUpdatedEvent(DomainEvent):
    """Event raised when a target is updated."""
    
    def __init__(self, target_id: int, target_name: str, changes: Dict[str, Any], updated_by: int):
        self.target_id = target_id
        self.target_name = target_name
        self.changes = changes
        self.updated_by = updated_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(target_id),
            aggregate_type="Target"
        )


class TargetDeletedEvent(DomainEvent):
    """Event raised when a target is deleted."""
    target_id: int
    target_name: str
    target_type: str
    deleted_by: int
    
    def __init__(self, target_id: int, target_name: str, target_type: str, deleted_by: int):
        self.target_id = target_id
        self.target_name = target_name
        self.target_type = target_type
        self.deleted_by = deleted_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(target_id),
            aggregate_type="Target"
        )


@dataclass
class TargetConnectionTestEvent(DomainEvent):
    """Event raised when a target connection is tested."""
    target_id: int
    target_name: str
    test_result: Dict[str, Any]
    tested_by: int
    
    def __init__(self, target_id: int, target_name: str, test_result: Dict[str, Any], tested_by: int):
        self.target_id = target_id
        self.target_name = target_name
        self.test_result = test_result
        self.tested_by = tested_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(target_id),
            aggregate_type="Target"
        )


@dataclass
class TargetStatusChangedEvent(DomainEvent):
    """Event raised when a target status changes."""
    target_id: int
    target_name: str
    old_status: str
    new_status: str
    reason: str
    
    def __init__(self, target_id: int, target_name: str, old_status: str, new_status: str, reason: str):
        self.target_id = target_id
        self.target_name = target_name
        self.old_status = old_status
        self.new_status = new_status
        self.reason = reason
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(target_id),
            aggregate_type="Target"
        )


@dataclass
class BulkTargetOperationEvent(DomainEvent):
    """Event raised when a bulk operation is performed on targets."""
    operation_type: str
    target_ids: List[int]
    results: Dict[str, Any]
    performed_by: int
    
    def __init__(self, operation_type: str, target_ids: List[int], results: Dict[str, Any], performed_by: int):
        self.operation_type = operation_type
        self.target_ids = target_ids
        self.results = results
        self.performed_by = performed_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=f"bulk_{operation_type}",
            aggregate_type="BulkTargetOperation"
        )


@dataclass
class TargetHealthCheckEvent(DomainEvent):
    """Event raised during automated health checks."""
    target_id: int
    target_name: str
    health_status: str
    response_time: float
    check_timestamp: datetime
    
    def __init__(self, target_id: int, target_name: str, health_status: str, response_time: float):
        self.target_id = target_id
        self.target_name = target_name
        self.health_status = health_status
        self.response_time = response_time
        self.check_timestamp = datetime.now()
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(target_id),
            aggregate_type="Target"
        )


@dataclass
class TargetDiscoveredEvent(DomainEvent):
    """Event raised when a new target is discovered."""
    discovered_host: str
    discovered_port: int
    discovery_method: str
    target_type: str
    additional_info: Dict[str, Any]
    discovered_by: int
    
    def __init__(
        self, 
        discovered_host: str, 
        discovered_port: int, 
        discovery_method: str,
        target_type: str,
        additional_info: Dict[str, Any],
        discovered_by: int
    ):
        self.discovered_host = discovered_host
        self.discovered_port = discovered_port
        self.discovery_method = discovery_method
        self.target_type = target_type
        self.additional_info = additional_info
        self.discovered_by = discovered_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=f"{discovered_host}:{discovered_port}",
            aggregate_type="DiscoveredTarget"
        )