from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.database import Base


class User(Base):
    """Enhanced user model for comprehensive authentication service."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # administrator, manager, user, guest
    
    # Account status and security
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    must_change_password = Column(Boolean, default=False)
    
    # Password management
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now())
    password_expires_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Activity tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    last_password_change = Column(DateTime(timezone=True), nullable=True)
    
    # Profile information
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    department = Column(String(50), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=True)  # User ID who created this user
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    password_history = relationship("PasswordHistory", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("UserAuditLog", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    """Enhanced user session model for comprehensive session management."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Session timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Session status
    is_active = Column(Boolean, default=True)
    logout_reason = Column(String(50), nullable=True)  # manual, timeout, forced, expired
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class PasswordHistory(Base):
    """Track password history to prevent reuse."""
    __tablename__ = "password_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="password_history")


class UserAuditLog(Base):
    """Comprehensive audit logging for user activities."""
    __tablename__ = "user_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system events
    
    # Event details
    event_type = Column(String(50), nullable=False)  # login, logout, password_change, account_locked, etc.
    event_description = Column(Text, nullable=True)
    
    # Context information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Additional data
    event_metadata = Column(JSON, nullable=True)  # Store additional event-specific data
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class AuthConfiguration(Base):
    """Centralized authentication and security configuration."""
    __tablename__ = "auth_configuration"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(20), nullable=False)  # string, integer, boolean, json
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # session, password, security, etc.
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)  # User ID who last updated this config