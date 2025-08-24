"""
Clean User Schemas
Simple, clear request/response schemas
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# =============================================================================
# Permission Schemas
# =============================================================================

class PermissionResponse(BaseModel):
    """Permission response schema"""
    id: int
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    category: Optional[str] = None
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Role Schemas
# =============================================================================

class RoleResponse(BaseModel):
    """Role response schema"""
    id: int
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    is_system: bool
    permissions: List[PermissionResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoleCreateRequest(BaseModel):
    """Role creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    permission_ids: List[int] = Field(default_factory=list)


class RoleUpdateRequest(BaseModel):
    """Role update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RolePermissionUpdateRequest(BaseModel):
    """Update role permissions request"""
    permission_ids: List[int] = Field(..., description="Permission IDs to assign")


# =============================================================================
# User Schemas
# =============================================================================

class UserResponse(BaseModel):
    """User response schema"""
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    role: Optional[RoleResponse] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreateRequest(BaseModel):
    """User creation request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    role_id: Optional[int] = None


class UserUpdateRequest(BaseModel):
    """User update request"""
    email: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role_id: Optional[int] = None


class UserRoleUpdateRequest(BaseModel):
    """Update user's role request"""
    role_id: Optional[int] = Field(None, description="Role ID to assign (null to remove)")


class UserPasswordChangeRequest(BaseModel):
    """Change user password request"""
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")


# =============================================================================
# List Response Schemas
# =============================================================================

class RoleListResponse(BaseModel):
    """Role list response"""
    roles: List[RoleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PermissionListResponse(BaseModel):
    """Permission list response"""
    permissions: List[PermissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int