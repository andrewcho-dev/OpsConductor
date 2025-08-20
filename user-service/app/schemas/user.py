"""
User Service Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field, validator
import uuid


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    role: str = Field("user", regex="^(admin|user|viewer)$")
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, regex="^(admin|user|viewer)$")
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    user_id: str
    username: str
    email: str
    full_name: Optional[str]
    role: str
    permissions: List[str]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]
    
    @validator('id', 'created_by', 'updated_by', pre=True)
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string."""
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        orm_mode = True


class UserListResponse(BaseModel):
    """Schema for paginated user list."""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class UserSettingsBase(BaseModel):
    """Base user settings schema."""
    preferences: Dict[str, Any] = Field(default_factory=dict)
    timezone: str = Field("UTC", max_length=50)
    theme: str = Field("light", regex="^(light|dark)$")
    language: str = Field("en", max_length=10)
    notifications_enabled: bool = True


class UserSettingsCreate(UserSettingsBase):
    """Schema for creating user settings."""
    pass


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""
    preferences: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = Field(None, max_length=50)
    theme: Optional[str] = Field(None, regex="^(light|dark)$")
    language: Optional[str] = Field(None, max_length=10)
    notifications_enabled: Optional[bool] = None


class UserSettingsResponse(UserSettingsBase):
    """Schema for user settings response."""
    id: str
    user_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True


class UserActivityBase(BaseModel):
    """Base user activity schema."""
    action: str = Field(..., max_length=100)
    resource_type: Optional[str] = Field(None, max_length=50)
    resource_id: Optional[str] = Field(None, max_length=255)
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class UserActivityCreate(UserActivityBase):
    """Schema for creating user activity."""
    pass


class UserActivityResponse(UserActivityBase):
    """Schema for user activity response."""
    id: str
    user_id: str
    created_at: Optional[datetime]
    
    class Config:
        orm_mode = True


class UserActivityListResponse(BaseModel):
    """Schema for paginated user activity list."""
    activities: List[UserActivityResponse]
    total: int
    page: int
    size: int
    pages: int


class UserStatsResponse(BaseModel):
    """Schema for user statistics."""
    total_users: int
    active_users: int
    inactive_users: int
    admin_users: int
    regular_users: int
    recent_signups: int


class BulkUserAction(BaseModel):
    """Schema for bulk user actions."""
    user_ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., regex="^(activate|deactivate|delete)$")


class BulkUserActionResponse(BaseModel):
    """Schema for bulk user action response."""
    success_count: int
    failed_count: int
    failed_users: List[str] = Field(default_factory=list)
    message: str


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    service: str
    version: str
    database: str
    timestamp: datetime