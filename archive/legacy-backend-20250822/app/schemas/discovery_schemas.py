"""
Network Discovery API Schemas
Pydantic schemas for network discovery API endpoints.
"""
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class DiscoveryJobStatus(str, Enum):
    """Discovery job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DiscoveredDeviceStatus(str, Enum):
    """Discovered device status enumeration."""
    DISCOVERED = "discovered"
    IMPORTED = "imported"
    IGNORED = "ignored"


class DiscoveryConfigBase(BaseModel):
    """Base discovery configuration schema."""
    network_ranges: List[str] = Field(..., description="List of network ranges to scan (e.g., ['192.168.1.0/24'])")
    port_ranges: Optional[List[Tuple[int, int]]] = Field(None, description="List of port ranges to scan [(start, end)]")
    common_ports: Optional[List[int]] = Field(None, description="List of common ports to scan")
    timeout: float = Field(3.0, ge=0.1, le=30.0, description="Connection timeout in seconds")
    max_concurrent: int = Field(100, ge=1, le=1000, description="Maximum concurrent connections")
    snmp_communities: Optional[List[str]] = Field(None, description="SNMP communities to try")
    enable_snmp: bool = Field(True, description="Enable SNMP discovery")
    enable_service_detection: bool = Field(True, description="Enable service detection")
    enable_hostname_resolution: bool = Field(True, description="Enable hostname resolution")
    
    @validator('network_ranges')
    def validate_network_ranges(cls, v):
        """Validate network ranges format."""
        if not v:
            raise ValueError("At least one network range is required")
        
        import ipaddress
        for network_range in v:
            try:
                ipaddress.ip_network(network_range, strict=False)
            except ValueError:
                raise ValueError(f"Invalid network range: {network_range}")
        return v
    
    @validator('port_ranges')
    def validate_port_ranges(cls, v):
        """Validate port ranges."""
        if v:
            for start, end in v:
                if not (1 <= start <= 65535) or not (1 <= end <= 65535):
                    raise ValueError(f"Port range {start}-{end} is invalid. Ports must be 1-65535")
                if start > end:
                    raise ValueError(f"Invalid port range {start}-{end}. Start must be <= end")
        return v
    
    @validator('common_ports')
    def validate_common_ports(cls, v):
        """Validate common ports."""
        if v:
            for port in v:
                if not (1 <= port <= 65535):
                    raise ValueError(f"Invalid port {port}. Ports must be 1-65535")
        return v


class DiscoveryJobCreate(DiscoveryConfigBase):
    """Schema for creating a discovery job."""
    name: str = Field(..., min_length=1, max_length=100, description="Discovery job name")
    description: Optional[str] = Field(None, description="Discovery job description")


class DiscoveryJobUpdate(BaseModel):
    """Schema for updating a discovery job."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Discovery job name")
    description: Optional[str] = Field(None, description="Discovery job description")
    status: Optional[DiscoveryJobStatus] = Field(None, description="Job status")


class DiscoveredDeviceInfo(BaseModel):
    """Schema for discovered device information."""
    ip_address: str = Field(..., description="Device IP address")
    hostname: Optional[str] = Field(None, description="Device hostname")
    mac_address: Optional[str] = Field(None, description="Device MAC address")
    open_ports: List[int] = Field(default_factory=list, description="List of open ports")
    services: Dict[int, Dict[str, Any]] = Field(default_factory=dict, description="Services detected on ports")
    snmp_info: Dict[str, Any] = Field(default_factory=dict, description="SNMP discovery information")
    device_type: Optional[str] = Field(None, description="Classified device type")
    os_type: Optional[str] = Field(None, description="Detected OS type")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Classification confidence score")
    suggested_communication_methods: List[str] = Field(default_factory=list, description="Suggested communication methods")
    discovered_at: datetime = Field(..., description="Discovery timestamp")


class DiscoveredDeviceResponse(DiscoveredDeviceInfo):
    """Schema for discovered device API response."""
    id: int = Field(..., description="Device ID")
    discovery_job_id: Optional[int] = Field(None, description="Discovery job ID")
    status: DiscoveredDeviceStatus = Field(..., description="Device status")
    target_id: Optional[int] = Field(None, description="Associated target ID if imported")
    imported_at: Optional[datetime] = Field(None, description="Import timestamp")
    imported_by: Optional[int] = Field(None, description="User ID who imported the device")
    
    class Config:
        from_attributes = True


class DiscoveryJobResponse(BaseModel):
    """Schema for discovery job API response."""
    id: int = Field(..., description="Job ID")
    name: str = Field(..., description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    
    # Configuration
    network_ranges: List[str] = Field(..., description="Network ranges scanned")
    port_ranges: Optional[List[Tuple[int, int]]] = Field(None, description="Port ranges scanned")
    common_ports: Optional[List[int]] = Field(None, description="Common ports scanned")
    timeout: float = Field(..., description="Connection timeout")
    max_concurrent: int = Field(..., description="Maximum concurrent connections")
    snmp_communities: Optional[List[str]] = Field(None, description="SNMP communities tried")
    enable_snmp: bool = Field(..., description="SNMP discovery enabled")
    enable_service_detection: bool = Field(..., description="Service detection enabled")
    enable_hostname_resolution: bool = Field(..., description="Hostname resolution enabled")
    
    # Status
    status: DiscoveryJobStatus = Field(..., description="Job status")
    progress: float = Field(..., ge=0.0, le=100.0, description="Job progress percentage")
    total_ips_scanned: int = Field(..., description="Total IPs scanned")
    devices_discovered: int = Field(..., description="Number of devices discovered")
    
    # Timestamps
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    created_by: Optional[int] = Field(None, description="User ID who created the job")
    
    class Config:
        from_attributes = True


class DiscoveryJobSummary(BaseModel):
    """Schema for discovery job summary."""
    id: int = Field(..., description="Job ID")
    name: str = Field(..., description="Job name")
    status: DiscoveryJobStatus = Field(..., description="Job status")
    progress: float = Field(..., description="Job progress percentage")
    devices_discovered: int = Field(..., description="Number of devices discovered")
    created_at: datetime = Field(..., description="Job creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    
    class Config:
        from_attributes = True


class DiscoveryTemplateCreate(DiscoveryConfigBase):
    """Schema for creating a discovery template."""
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    is_default: bool = Field(False, description="Whether this is a default template")


class DiscoveryTemplateUpdate(BaseModel):
    """Schema for updating a discovery template."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    network_ranges: Optional[List[str]] = Field(None, description="Network ranges to scan")
    port_ranges: Optional[List[Tuple[int, int]]] = Field(None, description="Port ranges to scan")
    common_ports: Optional[List[int]] = Field(None, description="Common ports to scan")
    timeout: Optional[float] = Field(None, ge=0.1, le=30.0, description="Connection timeout")
    max_concurrent: Optional[int] = Field(None, ge=1, le=1000, description="Maximum concurrent connections")
    snmp_communities: Optional[List[str]] = Field(None, description="SNMP communities")
    enable_snmp: Optional[bool] = Field(None, description="Enable SNMP discovery")
    enable_service_detection: Optional[bool] = Field(None, description="Enable service detection")
    enable_hostname_resolution: Optional[bool] = Field(None, description="Enable hostname resolution")
    is_default: Optional[bool] = Field(None, description="Whether this is a default template")
    is_active: Optional[bool] = Field(None, description="Whether this template is active")


class DiscoveryTemplateResponse(BaseModel):
    """Schema for discovery template API response."""
    id: int = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    
    # Configuration
    network_ranges: List[str] = Field(..., description="Network ranges")
    port_ranges: Optional[List[Tuple[int, int]]] = Field(None, description="Port ranges")
    common_ports: Optional[List[int]] = Field(None, description="Common ports")
    timeout: float = Field(..., description="Connection timeout")
    max_concurrent: int = Field(..., description="Maximum concurrent connections")
    snmp_communities: Optional[List[str]] = Field(None, description="SNMP communities")
    enable_snmp: bool = Field(..., description="SNMP discovery enabled")
    enable_service_detection: bool = Field(..., description="Service detection enabled")
    enable_hostname_resolution: bool = Field(..., description="Hostname resolution enabled")
    
    # Metadata
    is_default: bool = Field(..., description="Whether this is a default template")
    is_active: bool = Field(..., description="Whether this template is active")
    created_at: datetime = Field(..., description="Template creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Template update timestamp")
    created_by: Optional[int] = Field(None, description="User ID who created the template")
    
    class Config:
        from_attributes = True


class DeviceTargetConfig(BaseModel):
    """Schema for configuring a discovered device as a target."""
    device_id: int = Field(..., description="Discovered device ID")
    target_name: str = Field(..., description="Name for the target")
    description: Optional[str] = Field(None, description="Target description")
    environment: str = Field("development", description="Target environment")
    
    # Communication method configuration
    communication_method: str = Field(..., description="Primary communication method")
    username: str = Field(..., description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    ssh_key: Optional[str] = Field(None, description="SSH private key content")
    ssh_passphrase: Optional[str] = Field(None, description="SSH key passphrase")
    
    # Method-specific configuration
    port: Optional[int] = Field(None, description="Custom port (if different from default)")
    additional_config: Optional[Dict[str, Any]] = Field(None, description="Additional method-specific configuration")


class BulkDeviceImportRequest(BaseModel):
    """Schema for bulk importing configured discovered devices as targets."""
    device_configs: List[DeviceTargetConfig] = Field(..., description="List of device configurations")


class DeviceImportRequest(BaseModel):
    """Schema for importing discovered devices as targets (legacy - for backward compatibility)."""
    device_ids: List[int] = Field(..., description="List of discovered device IDs to import")
    auto_create_communication_methods: bool = Field(True, description="Automatically create communication methods")
    default_environment: str = Field("development", description="Default environment for created targets")
    default_credentials: Optional[Dict[str, str]] = Field(None, description="Default credentials to use")


class DeviceImportResponse(BaseModel):
    """Schema for device import response."""
    imported_count: int = Field(..., description="Number of devices successfully imported as new targets")
    existing_count: int = Field(..., description="Number of devices that matched existing targets")
    failed_count: int = Field(..., description="Number of devices that failed to import")
    target_ids: List[int] = Field(..., description="List of target IDs (both new and existing)")
    errors: List[str] = Field(default_factory=list, description="List of import errors")


class DiscoveryStatsResponse(BaseModel):
    """Schema for discovery statistics."""
    total_jobs: int = Field(..., description="Total number of discovery jobs")
    active_jobs: int = Field(..., description="Number of active/running jobs")
    total_devices_discovered: int = Field(..., description="Total devices discovered")
    devices_imported: int = Field(..., description="Number of devices imported as targets")
    devices_pending: int = Field(..., description="Number of devices pending import")
    
    # Device type breakdown
    device_type_counts: Dict[str, int] = Field(default_factory=dict, description="Count by device type")
    
    # Recent activity
    recent_jobs: List[DiscoveryJobSummary] = Field(default_factory=list, description="Recent discovery jobs")


class NetworkScanRequest(BaseModel):
    """Schema for quick network scan requests."""
    network_range: str = Field(..., description="Network range to scan (e.g., '192.168.1.0/24')")
    ports: Optional[List[int]] = Field(None, description="Specific ports to scan")
    timeout: float = Field(2.0, ge=0.1, le=10.0, description="Connection timeout")
    
    @validator('network_range')
    def validate_network_range(cls, v):
        """Validate network range format."""
        import ipaddress
        try:
            ipaddress.ip_network(v, strict=False)
        except ValueError:
            raise ValueError(f"Invalid network range: {v}")
        return v


class NetworkScanResponse(BaseModel):
    """Schema for quick network scan response."""
    network_range: str = Field(..., description="Scanned network range")
    total_ips: int = Field(..., description="Total IPs in range")
    responsive_ips: List[str] = Field(..., description="List of responsive IP addresses")
    scan_duration: float = Field(..., description="Scan duration in seconds")
    devices_found: List[DiscoveredDeviceInfo] = Field(default_factory=list, description="Basic device information")