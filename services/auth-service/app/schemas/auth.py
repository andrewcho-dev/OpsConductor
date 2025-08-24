"""
Auth Service Schemas - Authentication-only data
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]  # User data from user-service


class TokenValidationRequest(BaseModel):
    """Token validation request"""
    token: str


class TokenValidationResponse(BaseModel):
    """Token validation response"""
    valid: bool
    user: Optional[Dict[str, Any]] = None
    permissions: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request"""
    token: Optional[str] = None
    all_sessions: Optional[bool] = False


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str


class ApiKeyCreate(BaseModel):
    """API key creation request"""
    service_name: str
    description: Optional[str] = None
    permissions: Optional[List[str]] = []
    expires_in_days: Optional[int] = None


class ApiKeyResponse(BaseModel):
    """API key response"""
    key_id: str
    api_key: str  # Only returned on creation
    service_name: str
    description: Optional[str] = None
    permissions: List[str]
    expires_at: Optional[datetime] = None
    created_at: datetime


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    user_id: int
    created_at: datetime
    last_accessed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime