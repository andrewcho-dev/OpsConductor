"""
Pydantic schemas for configuration management - AUTHENTICATION ONLY!
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ConfigurationBase(BaseModel):
    """Base configuration schema."""
    config_key: str = Field(..., max_length=100)
    config_value: str
    config_type: str = Field(..., regex="^(string|integer|boolean|json)$")
    description: Optional[str] = None
    category: str = Field(..., max_length=50)


class ConfigurationCreate(ConfigurationBase):
    """Schema for creating configuration."""
    pass


class ConfigurationUpdate(BaseModel):
    """Schema for updating configuration."""
    config_value: str
    description: Optional[str] = None


class ConfigurationResponse(ConfigurationBase):
    """Schema for configuration response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]

    class Config:
        from_attributes = True


class ConfigurationValueResponse(BaseModel):
    """Schema for configuration value with metadata."""
    value: Any
    type: str
    description: Optional[str]
    updated_at: Optional[datetime]


class ConfigurationCategoryResponse(BaseModel):
    """Schema for configuration by category."""
    category: str
    configurations: Dict[str, ConfigurationValueResponse]


class SessionConfigResponse(BaseModel):
    """Schema for session configuration."""
    timeout_minutes: int
    warning_minutes: int
    max_concurrent: int
    idle_timeout_minutes: int
    remember_me_days: int


class PasswordPolicyResponse(BaseModel):
    """Schema for password policy configuration."""
    min_length: int
    max_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_numbers: bool
    require_special: bool
    special_chars: str
    expiry_days: int
    history_count: int
    min_age_hours: int


class SecurityConfigResponse(BaseModel):
    """Schema for security configuration."""
    max_failed_attempts: int
    lockout_duration_minutes: int
    progressive_lockout: bool
    require_email_verification: bool
    force_password_change_first_login: bool
    enable_two_factor: bool