from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
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
    """User information schema."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime

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


class UserCreate(BaseModel):
    """User creation schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="user")


class UserUpdate(BaseModel):
    """User update schema."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    """Password change schema."""
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class AdminPasswordReset(BaseModel):
    """Admin password reset schema."""
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        orm_mode = True


