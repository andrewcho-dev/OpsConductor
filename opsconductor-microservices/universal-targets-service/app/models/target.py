"""
Target models for Universal Targets Service
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import uuid


class Target(Base):
    """
    Universal Target model for the microservice.
    Targets are the subjects/objects that jobs act upon.
    """
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    target_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    target_serial = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), index=True, nullable=False)
    target_type = Column(String(20), nullable=False, default="system")  # system, api, database, email, web, communication
    description = Column(Text, nullable=True)
    os_type = Column(String(20), nullable=False)  # linux, windows
    environment = Column(String(20), nullable=False, default="development")  # production, staging, development, testing
    location = Column(String(100), nullable=True)
    data_center = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    status = Column(String(20), nullable=False, default="active")  # active, inactive, maintenance
    health_status = Column(String(20), nullable=False, default="unknown")  # healthy, warning, critical, unknown
    tags = Column(JSONB, nullable=True, default=list)  # Flexible tagging system
    metadata = Column(JSONB, nullable=True, default=dict)  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=True)  # User ID who created the target
    updated_by = Column(Integer, nullable=True)  # User ID who last updated the target

    # Relationships
    connection_methods = relationship("ConnectionMethod", back_populates="target", cascade="all, delete-orphan")


class ConnectionMethod(Base):
    """
    Connection methods for targets.
    Defines how to connect to and interact with targets.
    """
    __tablename__ = "connection_methods"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    method_type = Column(String(50), nullable=False)  # ssh, winrm, mysql, postgresql, etc.
    method_name = Column(String(100), nullable=False)  # auto-generated: method_type_timestamp
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=1)
    config = Column(JSONB, nullable=False, default=dict)  # Connection configuration including host IP
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    target = relationship("Target", back_populates="connection_methods")
    credentials = relationship("Credential", back_populates="connection_method", cascade="all, delete-orphan")

    # Ensure only one primary method per target
    __table_args__ = (
        UniqueConstraint('target_id', 'is_primary', name='uq_target_primary_method'),
    )


class Credential(Base):
    """
    Credentials for connection methods.
    Stores encrypted authentication information.
    """
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)
    connection_method_id = Column(Integer, ForeignKey("connection_methods.id"), nullable=False)
    credential_type = Column(String(50), nullable=False)  # password, ssh_key, api_key, etc.
    credential_name = Column(String(100), nullable=False)
    username = Column(String(100), nullable=True)
    encrypted_data = Column(Text, nullable=False)  # Encrypted credential data
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connection_method = relationship("ConnectionMethod", back_populates="credentials")

    # Ensure only one primary credential per connection method
    __table_args__ = (
        UniqueConstraint('connection_method_id', 'is_primary', name='uq_method_primary_credential'),
    )


class TargetHealthCheck(Base):
    """
    Health check results for targets.
    Stores historical health check data.
    """
    __tablename__ = "target_health_checks"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    connection_method_id = Column(Integer, ForeignKey("connection_methods.id"), nullable=True)
    check_type = Column(String(50), nullable=False)  # ping, ssh, service_check, etc.
    status = Column(String(20), nullable=False)  # healthy, warning, critical, unknown
    response_time = Column(Integer, nullable=True)  # in milliseconds
    details = Column(JSONB, nullable=True, default=dict)  # Check details and results
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    checked_by = Column(Integer, nullable=True)  # User ID who initiated the check

    # Relationships
    target = relationship("Target")
    connection_method = relationship("ConnectionMethod")