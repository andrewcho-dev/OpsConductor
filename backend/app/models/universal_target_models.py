from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.database.database import Base
import uuid


class UniversalTarget(Base):
    """
    Universal Target model following the architecture plan.
    Targets are the subjects/objects that jobs act upon.
    """
    __tablename__ = "universal_targets"

    id = Column(Integer, primary_key=True, index=True)
    target_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    target_serial = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), index=True, nullable=False)  # NO UNIQUE CONSTRAINT - Multiple targets can have same name
    target_type = Column(String(20), nullable=False, default="system")  # system, api, database, email, web
    description = Column(Text, nullable=True)
    os_type = Column(String(20), nullable=False)  # linux, windows (simplified for initial release)
    environment = Column(String(20), nullable=False, default="development")  # production, staging, development, testing
    location = Column(String(100), nullable=True)
    data_center = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    status = Column(String(20), nullable=False, default="active")  # active, inactive, maintenance
    health_status = Column(String(20), nullable=False, default="unknown")  # healthy, warning, critical, unknown
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    communication_methods = relationship("TargetCommunicationMethod", back_populates="target", cascade="all, delete-orphan")


class TargetCommunicationMethod(Base):
    """
    Communication methods for targets.
    Defines how to connect to and interact with targets.
    CRITICAL: IP addresses are stored in config.host field only!
    """
    __tablename__ = "target_communication_methods"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("universal_targets.id"), nullable=False)
    method_type = Column(String(20), nullable=False)  # ssh, winrm, mysql, postgresql, mssql, oracle, sqlite, mongodb, redis, elasticsearch
    method_name = Column(String(100), nullable=False)  # auto-generated: method_type_timestamp
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    config = Column(JSON, nullable=False)  # Contains: {host: "IP_ADDRESS", port: 22/5985, additional_params}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    target = relationship("UniversalTarget", back_populates="communication_methods")
    credentials = relationship("TargetCredential", back_populates="communication_method", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        # ONLY constraint: No two active targets can have the same IP address
        # This is enforced at the application level since IP is stored in JSON config
        # and PostgreSQL can't create unique constraints on JSON fields easily
    )


class TargetCredential(Base):
    """
    Credentials for communication methods.
    Stores encrypted authentication information.
    """
    __tablename__ = "target_credentials"

    id = Column(Integer, primary_key=True, index=True)
    communication_method_id = Column(Integer, ForeignKey("target_communication_methods.id"), nullable=False)
    credential_type = Column(String(20), nullable=False)  # password, ssh_key (simplified for initial release)
    credential_name = Column(String(100), nullable=False)
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    encrypted_credentials = Column(Text, nullable=False)  # Encrypted JSON storage
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    communication_method = relationship("TargetCommunicationMethod", back_populates="credentials")