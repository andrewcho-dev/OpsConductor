"""
Discovery models for Target Discovery Service
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from app.core.database import Base
import uuid


class DiscoveryJobStatus(str, enum.Enum):
    """Discovery job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class DeviceType(str, enum.Enum):
    """Device type enumeration"""
    SERVER = "server"
    WORKSTATION = "workstation"
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    PRINTER = "printer"
    STORAGE = "storage"
    UNKNOWN = "unknown"


class DiscoveryMethod(str, enum.Enum):
    """Discovery method enumeration"""
    PING = "ping"
    PORT_SCAN = "port_scan"
    SNMP = "snmp"
    SSH = "ssh"
    WMI = "wmi"
    HTTP = "http"
    DNS = "dns"


class DiscoveryJob(Base):
    """
    Discovery job model for network discovery operations
    """
    __tablename__ = "discovery_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Job Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Discovery Configuration
    network_ranges = Column(JSONB, nullable=False)  # List of network ranges to scan
    port_ranges = Column(JSONB, nullable=True, default=list)  # List of port ranges
    common_ports = Column(JSONB, nullable=True, default=list)  # List of common ports
    
    # Timing Configuration
    timeout = Column(Float, default=3.0, nullable=False)
    max_concurrent = Column(Integer, default=100, nullable=False)
    
    # SNMP Configuration
    snmp_communities = Column(JSONB, nullable=True, default=list)
    snmp_version = Column(String(10), default="2c")
    snmp_timeout = Column(Float, default=2.0)
    snmp_retries = Column(Integer, default=2)
    
    # Discovery Options
    enable_snmp = Column(Boolean, default=True)
    enable_service_detection = Column(Boolean, default=True)
    enable_hostname_resolution = Column(Boolean, default=True)
    enable_os_detection = Column(Boolean, default=True)
    enable_mac_detection = Column(Boolean, default=True)
    
    # Job Status
    status = Column(String(20), default=DiscoveryJobStatus.PENDING, nullable=False, index=True)
    progress = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0
    
    # Results Summary
    total_ips_scanned = Column(Integer, default=0, nullable=False)
    devices_discovered = Column(Integer, default=0, nullable=False)
    devices_imported = Column(Integer, default=0, nullable=False)
    
    # Error Information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)
    
    # Ownership and Creation
    created_by = Column(Integer, nullable=False, index=True)  # User ID from User Service
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Relationships
    discovered_devices = relationship("DiscoveredDevice", back_populates="discovery_job", cascade="all, delete-orphan")
    schedules = relationship("DiscoverySchedule", back_populates="discovery_job", cascade="all, delete-orphan")


class DiscoveredDevice(Base):
    """
    Discovered device model for storing discovery results
    """
    __tablename__ = "discovered_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    discovery_job_id = Column(Integer, ForeignKey("discovery_jobs.id"), nullable=False, index=True)
    
    # Network Information
    ip_address = Column(INET, nullable=False, index=True)
    hostname = Column(String(255), nullable=True, index=True)
    mac_address = Column(String(17), nullable=True, index=True)  # MAC address format: XX:XX:XX:XX:XX:XX
    
    # Device Classification
    device_type = Column(String(50), default=DeviceType.UNKNOWN, index=True)
    device_category = Column(String(100), nullable=True)
    device_vendor = Column(String(100), nullable=True)
    device_model = Column(String(100), nullable=True)
    
    # Operating System Information
    os_name = Column(String(100), nullable=True)
    os_version = Column(String(100), nullable=True)
    os_family = Column(String(50), nullable=True)  # windows, linux, unix, etc.
    
    # Network Services
    open_ports = Column(JSONB, nullable=True, default=list)  # List of open ports
    services = Column(JSONB, nullable=True, default=dict)    # Port -> service mapping
    
    # SNMP Information
    snmp_community = Column(String(100), nullable=True)
    snmp_system_name = Column(String(255), nullable=True)
    snmp_system_description = Column(Text, nullable=True)
    snmp_system_contact = Column(String(255), nullable=True)
    snmp_system_location = Column(String(255), nullable=True)
    snmp_uptime = Column(Integer, nullable=True)  # Uptime in seconds
    
    # Discovery Information
    discovery_method = Column(String(50), nullable=False, index=True)
    response_time = Column(Float, nullable=True)  # Response time in milliseconds
    is_alive = Column(Boolean, default=True, index=True)
    
    # Import Status
    is_imported = Column(Boolean, default=False, index=True)
    imported_at = Column(DateTime(timezone=True), nullable=True)
    target_id = Column(Integer, nullable=True, index=True)  # ID in Universal Targets Service
    
    # Additional Data
    raw_data = Column(JSONB, nullable=True, default=dict)  # Raw discovery data
    metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    discovered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    discovery_job = relationship("DiscoveryJob", back_populates="discovered_devices")


class DiscoveryTemplate(Base):
    """
    Discovery template model for reusable discovery configurations
    """
    __tablename__ = "discovery_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Template Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    
    # Template Configuration
    template_data = Column(JSONB, nullable=False)  # Complete discovery configuration
    
    # Template Metadata
    is_public = Column(Boolean, default=False)  # Available to all users
    is_system = Column(Boolean, default=False)  # System template
    
    # Usage Statistics
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Ownership
    created_by = Column(Integer, nullable=False, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DiscoverySchedule(Base):
    """
    Discovery schedule model for automated discovery jobs
    """
    __tablename__ = "discovery_schedules"

    id = Column(Integer, primary_key=True, index=True)
    schedule_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    discovery_job_id = Column(Integer, ForeignKey("discovery_jobs.id"), nullable=False, index=True)
    
    # Schedule Configuration
    schedule_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    
    # Schedule Parameters
    cron_expression = Column(String(100), nullable=True)  # For cron schedules
    interval_minutes = Column(Integer, nullable=True)     # For interval schedules
    
    # Time Configuration
    timezone = Column(String(50), default='UTC')
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Execution Limits
    max_executions = Column(Integer, nullable=True)
    current_executions = Column(Integer, default=0, nullable=False)
    
    # Next Execution
    next_run_time = Column(DateTime(timezone=True), nullable=True, index=True)
    last_run_time = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    
    # Relationships
    discovery_job = relationship("DiscoveryJob", back_populates="schedules")


class NetworkRange(Base):
    """
    Network range model for storing predefined network ranges
    """
    __tablename__ = "network_ranges"

    id = Column(Integer, primary_key=True, index=True)
    range_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Range Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Network Configuration
    network_cidr = Column(String(50), nullable=False, index=True)  # e.g., 192.168.1.0/24
    start_ip = Column(INET, nullable=False, index=True)
    end_ip = Column(INET, nullable=False, index=True)
    
    # Range Metadata
    location = Column(String(255), nullable=True)
    environment = Column(String(100), nullable=True)  # production, staging, development
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Ownership
    created_by = Column(Integer, nullable=False, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DiscoveryCredential(Base):
    """
    Discovery credential model for storing authentication credentials
    """
    __tablename__ = "discovery_credentials"

    id = Column(Integer, primary_key=True, index=True)
    credential_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Credential Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    credential_type = Column(String(50), nullable=False, index=True)  # snmp, ssh, wmi, etc.
    
    # Credential Data (encrypted)
    credential_data = Column(JSONB, nullable=False)  # Encrypted credential information
    
    # Usage Scope
    network_ranges = Column(JSONB, nullable=True, default=list)  # Which networks this applies to
    device_types = Column(JSONB, nullable=True, default=list)    # Which device types this applies to
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Ownership
    created_by = Column(Integer, nullable=False, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DiscoveryRule(Base):
    """
    Discovery rule model for device classification and processing rules
    """
    __tablename__ = "discovery_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Rule Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False, index=True)  # classification, import, alert
    
    # Rule Configuration
    conditions = Column(JSONB, nullable=False)  # Rule conditions
    actions = Column(JSONB, nullable=False)     # Actions to take when rule matches
    
    # Rule Priority and Status
    priority = Column(Integer, default=5, nullable=False, index=True)  # 1-10, 10 is highest
    is_active = Column(Boolean, default=True, index=True)
    
    # Usage Statistics
    match_count = Column(Integer, default=0, nullable=False)
    last_matched = Column(DateTime(timezone=True), nullable=True)
    
    # Ownership
    created_by = Column(Integer, nullable=False, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())