"""
User Management Commands
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.shared.infrastructure.cqrs import Command


@dataclass
class CreateUserCommand(Command):
    """Command to create a new user."""
    username: str
    email: str
    password: str
    role: str = "user"


@dataclass
class UpdateUserCommand(Command):
    """Command to update an existing user."""
    user_id: int
    update_data: Dict[str, Any]


@dataclass
class ChangePasswordCommand(Command):
    """Command to change user password."""
    user_id: int
    current_password: str
    new_password: str


@dataclass
class DeactivateUserCommand(Command):
    """Command to deactivate a user."""
    user_id: int


@dataclass
class ActivateUserCommand(Command):
    """Command to activate a user."""
    user_id: int


@dataclass
class AuthenticateUserCommand(Command):
    """Command to authenticate a user."""
    username: str
    password: str