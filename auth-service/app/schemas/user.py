"""
Pydantic schemas for user management.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    role: str = Field(default="user", regex="^(administrator|manager|operator|user|guest)$")
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=128)
    is_active: bool = True
    is_verified: bool = False
    must_change_password: bool = True


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[str] = None
    role: Optional[str] = Field(None, regex="^(administrator|manager|operator|user|guest)$")
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    must_change_password: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    """Schema for password updates."""
    current_password: Optional[str] = None  # Not required for admin resets
    new_password: str = Field(..., min_length=8, max_length=128)
    force_change: bool = False


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_locked: bool
    is_verified: bool
    must_change_password: bool
    password_expires_at: Optional[datetime]
    failed_login_attempts: int
    locked_until: Optional[datetime]
    last_login: Optional[datetime]
    last_login_ip: Optional[str]
    last_password_change: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]

    class Config:
        orm_mode = True


class UserListResponse(BaseModel):
    """Schema for paginated user list."""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class UserSessionResponse(BaseModel):
    """Schema for user session information."""
    id: int
    session_token: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_fingerprint: Optional[str]
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    is_active: bool
    logout_reason: Optional[str]

    class Config:
        from_attributes = True


class UserAuditLogResponse(BaseModel):
    """Schema for user audit log entries."""
    id: int
    user_id: Optional[int]
    event_type: str
    event_description: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Schema for user statistics."""
    total_users: int
    active_users: int
    locked_users: int
    unverified_users: int
    users_requiring_password_change: int
    recent_logins_24h: int
    failed_attempts_24h: int


class UserActivityResponse(BaseModel):
    """Schema for user activity information."""
    user_id: int
    username: str
    last_login: Optional[datetime]
    last_login_ip: Optional[str]
    active_sessions: int
    failed_attempts: int
    is_locked: bool
    locked_until: Optional[datetime]
    recent_activity: List[UserAuditLogResponse]

    class Config:
        from_attributes = True


class BulkUserAction(BaseModel):
    """Schema for bulk user actions."""
    user_ids: List[int]
    action: str = Field(..., regex="^(activate|deactivate|lock|unlock|force_password_change|delete)$")
    reason: Optional[str] = None


class BulkUserActionResponse(BaseModel):
    """Schema for bulk action results."""
    successful: List[int]
    failed: List[Dict[str, Any]]  # {"user_id": int, "error": str}
    total_processed: int


class PasswordPolicyValidation(BaseModel):
    """Schema for password policy validation results."""
    valid: bool
    errors: List[str]
    suggestions: Optional[List[str]] = None


class UserSecuritySettings(BaseModel):
    """Schema for user security settings."""
    two_factor_enabled: bool = False
    backup_codes_generated: bool = False
    trusted_devices: List[str] = []
    notification_preferences: Dict[str, bool] = {
        "login_alerts": True,
        "password_changes": True,
        "account_lockouts": True
    }