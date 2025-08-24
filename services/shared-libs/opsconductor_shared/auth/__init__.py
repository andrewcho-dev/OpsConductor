"""
Authentication module for OpsConductor shared libraries
"""

from .dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    require_permissions,
    require_roles
)
from .jwt_auth import (
    AuthServiceClient,
    get_auth_client,
    get_optional_user
)

__all__ = [
    "get_current_user",
    "get_current_active_user", 
    "get_current_superuser",
    "require_permissions",
    "require_roles",
    "AuthServiceClient",
    "get_auth_client",
    "get_optional_user"
]