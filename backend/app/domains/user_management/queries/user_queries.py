"""
User Management Queries
"""
from dataclasses import dataclass
from typing import Optional

from app.shared.infrastructure.cqrs import Query


@dataclass
class GetUserByIdQuery(Query):
    """Query to get user by ID."""
    user_id: int


@dataclass
class GetUserByUsernameQuery(Query):
    """Query to get user by username."""
    username: str


@dataclass
class GetUserByEmailQuery(Query):
    """Query to get user by email."""
    email: str


@dataclass
class GetUsersQuery(Query):
    """Query to get users with pagination and filtering."""
    skip: int = 0
    limit: int = 100
    role: Optional[str] = None
    active_only: bool = False


@dataclass
class GetActiveUsersQuery(Query):
    """Query to get active users."""
    skip: int = 0
    limit: int = 100


@dataclass
class GetUsersByRoleQuery(Query):
    """Query to get users by role."""
    role: str
    skip: int = 0
    limit: int = 100