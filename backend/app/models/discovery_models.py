"""
Network Discovery Database Models
Models for storing network discovery results and configurations.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class DiscoveryJob(Base):
    """Model for network discovery jobs."""
    __tablename__ = "discovery_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Configuration
    network_ranges = Column(JSON, nullable=False)  # List of network ranges to scan
    port_ranges = Column(JSON, nullable=True)      # List of port ranges [(start, end), ...]
    common_ports = Column(JSON, nullable=True)     # List of common ports to scan
    timeout = Column(Float, default=3.0)
    max_concurrent = Column(Integer, default=100)
    snmp_communities = Column(JSON, nullable=True) # List of SNMP communities to try
    
    # Options
    enable_snmp = Column(Boolean, default=True)
    enable_service_detection = Column(Boolean, default=True)
    enable_hostname_resolution = Column(Boolean, default=True)
    
    # Status
    status = Column(String(20), default='pending', index=True)  # pending, running, completed, failed
    progress = Column(Float, default=0.0)  # 0.0 to 100.0
    
    # Results summary
    total_ips_scanned = Column(Integer, default=0)
    devices_discovered = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # User who created the job
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    discovered_devices = relationship("DiscoveredDevice", back_populates="discovery_job", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class DiscoveredDevice(Base):
    """Model for discovered devices."""
    __tablename__ = "discovered_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    discovery_job_id = Column(Integer, ForeignKey("discovery_jobs.id"), nullable=False, index=True)
    
    # Basic device information
    ip_address = Column(String(45), nullable=False, index=True)  # IPv4 or IPv6
    hostname = Column(String(255), nullable=True, index=True)
    mac_address = Column(String(17), nullable=True, index=True)  # MAC address if discovered
    
    # Discovered services
    open_ports = Column(JSON, nullable=True)        # List of open ports
    services = Column(JSON, nullable=True)          # Dict of port -> service info
    snmp_info = Column(JSON, nullable=True)         # SNMP discovery results
    
    # Classification
    device_type = Column(String(50), nullable=True, index=True)  # Classified device type
    os_type = Column(String(50), nullable=True, index=True)      # Detected OS type
    confidence_score = Column(Float, default=0.0)               # Classification confidence (0.0-1.0)
    
    # Suggested configuration
    suggested_communication_methods = Column(JSON, nullable=True)  # List of suggested methods
    
    # Status
    status = Column(String(20), default='discovered', index=True)  # discovered, imported, ignored
    
    # Target creation
    target_id = Column(Integer, ForeignKey("universal_targets.id"), nullable=True, index=True)
    imported_at = Column(DateTime(timezone=True), nullable=True)
    imported_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    discovery_job = relationship("DiscoveryJob", back_populates="discovered_devices")
    target = relationship("UniversalTarget", foreign_keys=[target_id])
    importer = relationship("User", foreign_keys=[imported_by])


class DiscoveryTemplate(Base):
    """Model for discovery configuration templates."""
    __tablename__ = "discovery_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Template configuration (same as DiscoveryJob)
    network_ranges = Column(JSON, nullable=False)
    port_ranges = Column(JSON, nullable=True)
    common_ports = Column(JSON, nullable=True)
    timeout = Column(Float, default=3.0)
    max_concurrent = Column(Integer, default=100)
    snmp_communities = Column(JSON, nullable=True)
    
    # Options
    enable_snmp = Column(Boolean, default=True)
    enable_service_detection = Column(Boolean, default=True)
    enable_hostname_resolution = Column(Boolean, default=True)
    
    # Template metadata
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # User who created the template
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    creator = relationship("User", foreign_keys=[created_by])


class DiscoverySchedule(Base):
    """Model for scheduled discovery jobs."""
    __tablename__ = "discovery_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Schedule configuration
    template_id = Column(Integer, ForeignKey("discovery_templates.id"), nullable=False)
    cron_expression = Column(String(100), nullable=False)  # Cron expression for scheduling
    timezone = Column(String(50), default='UTC')
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # User who created the schedule
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    template = relationship("DiscoveryTemplate", foreign_keys=[template_id])
    creator = relationship("User", foreign_keys=[created_by])