"""
Pydantic schemas for User Service
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, validator


# =============================================================================
# Base Schemas
# =============================================================================

class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr = Field(..., description="User email address")
    username: Optional[str] = Field(None, min_length=3, max_length=100, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    display_name: Optional[str] = Field(None, max_length=200, description="Display name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    job_title: Optional[str] = Field(None, max_length=100, description="Job title")
    organization: Optional[str] = Field(None, max_length=200, description="Organization")
    timezone: str = Field("UTC", description="User timezone")
    language: str = Field("en", description="User language")
    theme: str = Field("light", description="UI theme preference")


class RoleBase(BaseModel):
    """Base schema for role data"""
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    display_name: Optional[str] = Field(None, max_length=200, description="Display name")
    description: Optional[str] = Field(None, description="Role description")


class PermissionBase(BaseModel):
    """Base schema for permission data"""
    name: str = Field(..., min_length=1, max_length=100, description="Permission name")
    display_name: Optional[str] = Field(None, max_length=200, description="Display name")
    description: Optional[str] = Field(None, description="Permission description")
    category: Optional[str] = Field(None, max_length=50, description="Permission category")
    resource: Optional[str] = Field(None, max_length=50, description="Resource type")
    action: Optional[str] = Field(None, max_length=50, description="Action type")


# =============================================================================
# Request Schemas
# =============================================================================

class UserCreateRequest(UserBase):
    """Schema for user creation"""
    is_superuser: bool = Field(False, description="Is superuser")
    role_ids: List[int] = Field(default_factory=list, description="Role IDs to assign")
    send_welcome_email: bool = Field(True, description="Send welcome email")


class UserUpdateRequest(BaseModel):
    """Schema for user update"""
    email: Optional[EmailStr] = Field(None, description="User email address")
    username: Optional[str] = Field(None, min_length=3, max_length=100, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    display_name: Optional[str] = Field(None, max_length=200, description="Display name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    job_title: Optional[str] = Field(None, max_length=100, description="Job title")
    organization: Optional[str] = Field(None, max_length=200, description="Organization")
    timezone: Optional[str] = Field(None, description="User timezone")
    language: Optional[str] = Field(None, description="User language")
    theme: Optional[str] = Field(None, description="UI theme preference")
    is_active: Optional[bool] = Field(None, description="Is user active")
    is_verified: Optional[bool] = Field(None, description="Is user verified")
    metadata: Optional[Dict[str, Any]] = Field(None, description="User metadata")
    tags: Optional[List[str]] = Field(None, description="User tags")


class RoleCreateRequest(RoleBase):
    """Schema for role creation"""
    parent_role_id: Optional[int] = Field(None, description="Parent role ID")
    permission_ids: List[int] = Field(default_factory=list, description="Permission IDs")


class RoleUpdateRequest(BaseModel):
    """Schema for role update"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Role name")
    display_name: Optional[str] = Field(None, max_length=200, description="Display name")
    description: Optional[str] = Field(None, description="Role description")
    is_active: Optional[bool] = Field(None, description="Is role active")
    parent_role_id: Optional[int] = Field(None, description="Parent role ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Role metadata")


class PermissionCreateRequest(PermissionBase):
    """Schema for permission creation"""
    pass


class PermissionUpdateRequest(BaseModel):
    """Schema for permission update"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Permission name")
    display_name: Optional[str] = Field(None, max_length=200, description="Display name")
    description: Optional[str] = Field(None, description="Permission description")
    category: Optional[str] = Field(None, max_length=50, description="Permission category")
    resource: Optional[str] = Field(None, max_length=50, description="Resource type")
    action: Optional[str] = Field(None, max_length=50, description="Action type")
    is_active: Optional[bool] = Field(None, description="Is permission active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Permission metadata")


class UserRoleAssignRequest(BaseModel):
    """Schema for assigning roles to user"""
    role_ids: List[int] = Field(..., description="Role IDs to assign")


class RolePermissionAssignRequest(BaseModel):
    """Schema for assigning permissions to role"""
    permission_ids: List[int] = Field(..., description="Permission IDs to assign")


class UserProfileUpdateRequest(BaseModel):
    """Schema for user profile update"""
    bio: Optional[str] = Field(None, description="User bio")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL")
    website: Optional[str] = Field(None, max_length=500, description="Website URL")
    location: Optional[str] = Field(None, max_length=200, description="Location")
    social_links: Optional[Dict[str, str]] = Field(None, description="Social media links")
    email_notifications: Optional[bool] = Field(None, description="Email notifications enabled")
    push_notifications: Optional[bool] = Field(None, description="Push notifications enabled")
    marketing_emails: Optional[bool] = Field(None, description="Marketing emails enabled")
    profile_visibility: Optional[str] = Field(None, description="Profile visibility")
    show_email: Optional[bool] = Field(None, description="Show email in profile")
    show_phone: Optional[bool] = Field(None, description="Show phone in profile")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom profile fields")


# =============================================================================
# Response Schemas
# =============================================================================

class PermissionResponse(PermissionBase):
    """Schema for permission response"""
    id: int
    permission_uuid: UUID
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoleResponse(RoleBase):
    """Schema for role response"""
    id: int
    role_uuid: UUID
    is_active: bool
    is_system: bool
    level: int
    parent_role_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: List[PermissionResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    id: int
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    social_links: Dict[str, str] = Field(default_factory=dict)
    email_notifications: bool
    push_notifications: bool
    marketing_emails: bool
    profile_visibility: str
    show_email: bool
    show_phone: bool
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    user_uuid: UUID
    is_active: bool
    is_verified: bool
    is_superuser: bool
    full_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    roles: List[RoleResponse] = Field(default_factory=list)
    profile: Optional[UserProfileResponse] = None
    permissions: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for user list response"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RoleListResponse(BaseModel):
    """Schema for role list response"""
    roles: List[RoleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PermissionListResponse(BaseModel):
    """Schema for permission list response"""
    permissions: List[PermissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserActivityLogResponse(BaseModel):
    """Schema for user activity log response"""
    id: int
    activity_type: str
    activity_description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Schema for user statistics response"""
    total_users: int
    active_users: int
    verified_users: int
    superusers: int
    users_created_today: int
    users_created_this_week: int
    users_created_this_month: int
    most_common_roles: List[Dict[str, Any]]
    most_active_users: List[Dict[str, Any]]


# =============================================================================
# Error Schemas
# =============================================================================

class UserErrorResponse(BaseModel):
    """Schema for user service error responses"""
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    service: str = "user-service"
    timestamp: datetime


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses"""
    success: bool = False
    error: str = "validation_error"
    message: str
    field_errors: Dict[str, List[str]] = Field(default_factory=dict)
    service: str = "user-service"
    timestamp: datetime