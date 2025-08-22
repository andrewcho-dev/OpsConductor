"""
FastAPI dependencies for authentication
"""

from .jwt_auth import get_current_user, get_optional_user, require_permissions, require_roles

__all__ = [
    "get_current_user",
    "get_optional_user", 
    "require_permissions",
    "require_roles"
]