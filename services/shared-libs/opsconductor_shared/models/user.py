"""
Shared User model for inter-service communication
"""

from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    """User model for authentication and authorization"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    organization_id: Optional[int] = None
    
    class Config:
        from_attributes = True