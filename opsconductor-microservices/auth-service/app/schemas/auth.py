"""
Pydantic schemas for Auth Service
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


# =============================================================================
# Request Schemas
# =============================================================================

class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(False, description="Remember login for extended period")


class RegisterRequest(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, description="User password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordChangeRequest(BaseModel):
    """Schema for password change"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="New password confirmation")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="New password confirmation")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh"""
    refresh_token: str = Field(..., description="Refresh token")


class TokenValidationRequest(BaseModel):
    """Schema for token validation"""
    token: str = Field(..., description="Access token to validate")


class EmailVerificationRequest(BaseModel):
    """Schema for email verification"""
    token: str = Field(..., description="Verification token")


class LogoutRequest(BaseModel):
    """Schema for logout request"""
    all_sessions: bool = Field(False, description="Logout from all sessions")


# =============================================================================
# Response Schemas
# =============================================================================

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    session_id: str = Field(..., description="Session ID")


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    user_uuid: UUID
    is_active: bool
    is_verified: bool
    is_locked: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Schema for login response"""
    success: bool = True
    message: str = "Login successful"
    user: UserResponse
    tokens: TokenResponse
    session_info: Dict[str, Any] = Field(default_factory=dict)


class RegisterResponse(BaseModel):
    """Schema for registration response"""
    success: bool = True
    message: str = "Registration successful"
    user: UserResponse
    verification_required: bool = True


class TokenValidationResponse(BaseModel):
    """Schema for token validation response"""
    valid: bool
    user: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


class SessionInfo(BaseModel):
    """Schema for session information"""
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool
    expires_at: datetime
    last_activity: datetime
    created_at: datetime


class UserSessionsResponse(BaseModel):
    """Schema for user sessions response"""
    sessions: List[SessionInfo]
    total_sessions: int
    active_sessions: int


class LoginHistoryEntry(BaseModel):
    """Schema for login history entry"""
    id: int
    email: str
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoginHistoryResponse(BaseModel):
    """Schema for login history response"""
    history: List[LoginHistoryEntry]
    total_entries: int
    successful_logins: int
    failed_attempts: int


class PasswordStrengthResponse(BaseModel):
    """Schema for password strength validation"""
    is_strong: bool
    score: int = Field(..., ge=0, le=100, description="Password strength score")
    errors: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    requirements: str


class ApiKeyResponse(BaseModel):
    """Schema for API key response"""
    key_id: str
    name: str
    description: Optional[str] = None
    service_name: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreateRequest(BaseModel):
    """Schema for API key creation"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    service_name: Optional[str] = Field(None, max_length=100)
    permissions: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class ApiKeyCreateResponse(BaseModel):
    """Schema for API key creation response"""
    key_id: str
    api_key: str = Field(..., description="The actual API key (only shown once)")
    key_info: ApiKeyResponse


# =============================================================================
# Error Schemas
# =============================================================================

class AuthErrorResponse(BaseModel):
    """Schema for authentication error responses"""
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    service: str = "auth-service"
    timestamp: datetime


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses"""
    success: bool = False
    error: str = "validation_error"
    message: str
    field_errors: Dict[str, List[str]] = Field(default_factory=dict)
    service: str = "auth-service"
    timestamp: datetime


# =============================================================================
# Internal Schemas (for service communication)
# =============================================================================

class InternalUserData(BaseModel):
    """Internal user data for token payload"""
    id: int
    email: str
    username: Optional[str] = None
    is_active: bool
    is_verified: bool
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)


class ServiceAuthRequest(BaseModel):
    """Schema for service-to-service authentication"""
    service_name: str
    api_key: str
    requested_permissions: List[str] = Field(default_factory=list)


class ServiceAuthResponse(BaseModel):
    """Schema for service authentication response"""
    authenticated: bool
    service_name: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    error: Optional[str] = None