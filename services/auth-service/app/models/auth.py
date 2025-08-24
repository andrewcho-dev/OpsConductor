"""
Auth Service Models - Authentication-only data
Does NOT contain user data - that's in user-service
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class AuthSession(Base):
    """Active authentication sessions"""
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # References user-service
    token_hash = Column(String(255), nullable=False, index=True)
    refresh_token_hash = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


class BlacklistedToken(Base):
    """Blacklisted tokens (logout, security)"""
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    reason = Column(String(100), default='logout')


class LoginAttempt(Base):
    """Login attempts for rate limiting and security"""
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(INET, nullable=False, index=True)
    success = Column(Boolean, nullable=False)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_agent = Column(Text, nullable=True)
    failure_reason = Column(String(100), nullable=True)


class PasswordResetToken(Base):
    """Password reset tokens"""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)
    is_used = Column(Boolean, default=False)


class ApiKey(Base):
    """API keys for service-to-service authentication"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(255), unique=True, nullable=False, index=True)
    key_hash = Column(String(255), nullable=False)
    service_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=True)  # References user who created the key