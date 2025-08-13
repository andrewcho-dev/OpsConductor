"""
User Management Domain Events
"""
from dataclasses import dataclass
from datetime import datetime
import uuid

from app.shared.infrastructure.events import DomainEvent


@dataclass
class UserCreatedEvent(DomainEvent):
    """Event raised when a user is created."""
    user_id: int
    username: str
    email: str
    role: str
    created_by: str
    
    def __init__(self, user_id: int, username: str, email: str, role: str, created_by: str):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.created_by = created_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(user_id),
            aggregate_type="User"
        )


@dataclass
class UserUpdatedEvent(DomainEvent):
    """Event raised when a user is updated."""
    user_id: int
    username: str
    changes: dict
    updated_by: str
    
    def __init__(self, user_id: int, username: str, changes: dict, updated_by: str):
        self.user_id = user_id
        self.username = username
        self.changes = changes
        self.updated_by = updated_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(user_id),
            aggregate_type="User"
        )


@dataclass
class UserPasswordChangedEvent(DomainEvent):
    """Event raised when a user's password is changed."""
    user_id: int
    username: str
    changed_by: str
    
    def __init__(self, user_id: int, username: str, changed_by: str):
        self.user_id = user_id
        self.username = username
        self.changed_by = changed_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(user_id),
            aggregate_type="User"
        )


@dataclass
class UserDeactivatedEvent(DomainEvent):
    """Event raised when a user is deactivated."""
    user_id: int
    username: str
    deactivated_by: str
    
    def __init__(self, user_id: int, username: str, deactivated_by: str):
        self.user_id = user_id
        self.username = username
        self.deactivated_by = deactivated_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(user_id),
            aggregate_type="User"
        )


@dataclass
class UserActivatedEvent(DomainEvent):
    """Event raised when a user is activated."""
    user_id: int
    username: str
    activated_by: str
    
    def __init__(self, user_id: int, username: str, activated_by: str):
        self.user_id = user_id
        self.username = username
        self.activated_by = activated_by
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(user_id),
            aggregate_type="User"
        )


@dataclass
class UserLoggedInEvent(DomainEvent):
    """Event raised when a user logs in."""
    user_id: int
    username: str
    ip_address: str
    user_agent: str
    
    def __init__(self, user_id: int, username: str, ip_address: str, user_agent: str):
        self.user_id = user_id
        self.username = username
        self.ip_address = ip_address
        self.user_agent = user_agent
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=str(user_id),
            aggregate_type="User"
        )