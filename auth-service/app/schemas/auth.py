"""
Authentication schemas - AUTHENTICATION ONLY!
NO user management schemas here!
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserLogin(BaseModel):
    """User login request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    remember_me: bool = False


class TokenRequest(BaseModel):
    """Token validation request schema."""
    token: str


class UserInfo(BaseModel):
    """Basic user information for authentication."""
    id: int
    username: str
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    session_id: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo


class TokenValidationResponse(BaseModel):
    """Token validation response schema."""
    valid: bool
    user: Optional[UserInfo] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


class SessionStatus(BaseModel):
    """Session status response schema."""
    valid: bool
    expired: bool
    time_remaining: int
    warning: bool
    warning_threshold: int


