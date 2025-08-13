"""
Pydantic schemas for Universal Target API.
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator


class TargetCredentialBase(BaseModel):
    """Base schema for target credentials."""
    credential_type: str = Field(..., description="Type of credential (password, ssh_key, snmp_community, api_key, api_token)")
    credential_name: str = Field(..., description="Name of the credential")


class TargetCredentialResponse(TargetCredentialBase):
    """Schema for credential response (no sensitive data)."""
    id: int
    communication_method_id: int
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CommunicationMethodBase(BaseModel):
    """Base schema for communication methods."""
    method_type: str = Field(..., description="Type of communication method (ssh, winrm, snmp, telnet, rest_api, smtp, mysql, postgresql, mssql, oracle, sqlite, mongodb, redis, elasticsearch)")
    is_primary: bool = Field(False, description="Whether this is the primary method")
    is_active: bool = Field(True, description="Whether this method is active")
    priority: int = Field(1, description="Priority of this method")
    config: Dict[str, Any] = Field(..., description="Method configuration including host IP")


class CommunicationMethodResponse(CommunicationMethodBase):
    """Schema for communication method response."""
    id: int
    target_id: int
    method_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    credentials: List[TargetCredentialResponse] = []
    
    class Config:
        from_attributes = True


class CommunicationMethodCreate(BaseModel):
    """Schema for creating a new communication method."""
    method_type: str = Field(..., description="Type of communication method (ssh, winrm, snmp, telnet, rest_api, smtp, mysql, postgresql, mssql, oracle, sqlite, mongodb, redis, elasticsearch)")
    config: Dict[str, Any] = Field(..., description="Method configuration including host IP")
    is_primary: bool = Field(False, description="Whether this is the primary method")
    is_active: bool = Field(True, description="Whether this method is active")
    priority: int = Field(1, description="Priority of this method")
    
    # Credential information
    credential_type: str = Field(..., description="Type of credential (password, ssh_key, snmp_community, api_key, api_token)")
    username: str = Field(..., description="Username for authentication")
    password: Optional[str] = Field(None, description="Password/Community String/API Key for authentication")
    ssh_key: Optional[str] = Field(None, description="SSH private key/API token for authentication")
    ssh_passphrase: Optional[str] = Field(None, description="SSH key passphrase")


class CommunicationMethodUpdate(BaseModel):
    """Schema for updating a communication method."""
    method_type: Optional[str] = Field(None, description="Type of communication method")
    config: Optional[Dict[str, Any]] = Field(None, description="Method configuration")
    is_primary: Optional[bool] = Field(None, description="Whether this is the primary method")
    is_active: Optional[bool] = Field(None, description="Whether this method is active")
    priority: Optional[int] = Field(None, description="Priority of this method")


class TargetBase(BaseModel):
    """Base schema for targets."""
    name: str = Field(..., min_length=1, max_length=100, description="Unique target name")
    target_type: str = Field("system", description="Type of target")
    description: Optional[str] = Field(None, description="Target description")
    os_type: str = Field(..., description="Device/OS type")
    environment: str = Field("development", description="Environment (production, staging, development, testing)")
    location: Optional[str] = Field(None, description="Physical location")
    data_center: Optional[str] = Field(None, description="Data center name")
    region: Optional[str] = Field(None, description="Geographic region")
    status: str = Field("active", description="Target status (active, inactive, maintenance)")
    
    @validator('os_type')
    def validate_os_type(cls, v):
        """Validate Device/OS type."""
        # Valid device/OS types - expanded list
        valid_types = [
            # Operating Systems
            'linux', 'windows', 'windows_desktop', 'macos', 'freebsd', 'aix', 'solaris',
            # Network Infrastructure
            'cisco_switch', 'cisco_router', 'juniper_switch', 'juniper_router', 'arista_switch',
            'hp_switch', 'dell_switch', 'firewall', 'load_balancer', 'wireless_controller', 'access_point',
            # Virtualization & Cloud
            'vmware_esxi', 'vmware_vcenter', 'hyper_v', 'proxmox', 'xen', 'kubernetes', 'docker',
            # Storage Systems
            'netapp', 'emc_storage', 'hp_storage', 'pure_storage', 'synology', 'qnap',
            # Database Systems
            'mysql', 'postgresql', 'mssql', 'oracle_db', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
            # Application Servers
            'apache', 'nginx', 'iis', 'tomcat', 'jboss', 'websphere',
            # Communication & Email
            'exchange', 'postfix', 'sendmail', 'zimbra', 'asterisk',
            # Infrastructure Services
            'dns_server', 'dhcp_server', 'ntp_server', 'ldap_server', 'backup_server',
            # Power & Environmental
            'ups', 'pdu', 'environmental_monitor', 'generator',
            # Security Appliances
            'ids_ips', 'siem', 'vulnerability_scanner',
            # IoT & Embedded
            'raspberry_pi', 'arduino', 'iot_sensor', 'embedded_linux',
            # Generic/Unknown
            'generic_device', 'unknown',
            # Legacy types for backward compatibility
            'email', 'database'
        ]
        if v not in valid_types:
            raise ValueError(f'Device/OS type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment."""
        if v not in ['production', 'staging', 'development', 'testing']:
            raise ValueError('Environment must be production, staging, development, or testing')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status."""
        if v not in ['active', 'inactive', 'maintenance']:
            raise ValueError('Status must be active, inactive, or maintenance')
        return v


class TargetCreate(TargetBase):
    """Schema for target creation."""
    ip_address: str = Field(..., description="IP address or DNS name of the target")
    method_type: str = Field(..., description="Communication method type (ssh, winrm, snmp, telnet, rest_api, smtp)")
    username: str = Field(..., description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    ssh_key: Optional[str] = Field(None, description="SSH private key content")
    ssh_passphrase: Optional[str] = Field(None, description="SSH key passphrase")
    
    # SMTP-specific fields
    encryption: Optional[str] = Field(None, description="SMTP encryption method (starttls, ssl, none)")
    server_type: Optional[str] = Field(None, description="SMTP server type (smtp, exchange, gmail, outlook)")
    domain: Optional[str] = Field(None, description="Email domain for SMTP")
    test_recipient: Optional[str] = Field(None, description="Test recipient email address")
    connection_security: Optional[str] = Field(None, description="Connection security (auto, ssl, starttls, none)")
    
    # REST API-specific fields
    protocol: Optional[str] = Field(None, description="REST API protocol (http, https)")
    base_path: Optional[str] = Field(None, description="REST API base path")
    verify_ssl: Optional[bool] = Field(None, description="Verify SSL certificates for HTTPS")
    
    # SNMP-specific fields
    snmp_version: Optional[str] = Field(None, description="SNMP version (1, 2c, 3)")
    snmp_community: Optional[str] = Field(None, description="SNMP community string")
    snmp_retries: Optional[int] = Field(None, description="SNMP retry count")
    # SNMPv3-specific fields
    snmp_security_level: Optional[str] = Field(None, description="SNMPv3 security level (noAuthNoPriv, authNoPriv, authPriv)")
    snmp_auth_protocol: Optional[str] = Field(None, description="SNMPv3 authentication protocol (MD5, SHA)")
    snmp_privacy_protocol: Optional[str] = Field(None, description="SNMPv3 privacy protocol (DES, AES)")
    
    # Database-specific fields
    database: Optional[str] = Field(None, description="Database name")
    charset: Optional[str] = Field(None, description="Database charset (MySQL)")
    ssl_mode: Optional[str] = Field(None, description="SSL mode for database connection")
    driver: Optional[str] = Field(None, description="Database driver (SQL Server)")
    encrypt: Optional[str] = Field(None, description="Encryption setting (SQL Server)")
    service_name: Optional[str] = Field(None, description="Oracle service name")
    sid: Optional[str] = Field(None, description="Oracle SID")
    database_path: Optional[str] = Field(None, description="SQLite database file path")
    auth_source: Optional[str] = Field(None, description="MongoDB authentication source")
    ssl: Optional[bool] = Field(None, description="Use SSL (Elasticsearch, MongoDB)")
    verify_certs: Optional[bool] = Field(None, description="Verify SSL certificates (Elasticsearch)")
    
    @validator('method_type')
    def validate_method_type(cls, v):
        """Validate method type."""
        valid_methods = [
            'ssh', 'winrm', 'snmp', 'telnet', 'rest_api', 'smtp',
            'mysql', 'postgresql', 'mssql', 'oracle', 'sqlite', 
            'mongodb', 'redis', 'elasticsearch'
        ]
        if v not in valid_methods:
            raise ValueError(f'Method type must be one of: {", ".join(valid_methods)}')
        return v
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address or DNS name."""
        if v is not None:
            import ipaddress
            import re
            
            # Try IP address first
            try:
                ipaddress.ip_address(v)
                return v
            except ValueError:
                pass
            
            # Validate DNS name format
            dns_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            if re.match(dns_pattern, v) and len(v) <= 253:
                return v
            
            raise ValueError('Invalid IP address or DNS name format')
        return v
    
    @validator('password', 'ssh_key')
    def validate_credentials(cls, v, values):
        """Validate that either password or SSH key is provided."""
        # This is called for each field, so we need to check the complete validation in root_validator
        return v


class TargetUpdate(BaseModel):
    """Schema for target updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Unique target name")
    description: Optional[str] = Field(None, description="Target description")
    os_type: Optional[str] = Field(None, description="Device/OS type")
    environment: Optional[str] = Field(None, description="Environment")
    location: Optional[str] = Field(None, description="Physical location")
    data_center: Optional[str] = Field(None, description="Data center name")
    region: Optional[str] = Field(None, description="Geographic region")
    status: Optional[str] = Field(None, description="Target status")
    
    @validator('os_type')
    def validate_os_type(cls, v):
        """Validate Device/OS type."""
        if v is not None:
            # Valid device/OS types - expanded list
            valid_types = [
                # Operating Systems
                'linux', 'windows', 'windows_desktop', 'macos', 'freebsd', 'aix', 'solaris',
                # Network Infrastructure
                'cisco_switch', 'cisco_router', 'juniper_switch', 'juniper_router', 'arista_switch',
                'hp_switch', 'dell_switch', 'firewall', 'load_balancer', 'wireless_controller', 'access_point',
                # Virtualization & Cloud
                'vmware_esxi', 'vmware_vcenter', 'hyper_v', 'proxmox', 'xen', 'kubernetes', 'docker',
                # Storage Systems
                'netapp', 'emc_storage', 'hp_storage', 'pure_storage', 'synology', 'qnap',
                # Database Systems
                'mysql', 'postgresql', 'mssql', 'oracle_db', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
                # Application Servers
                'apache', 'nginx', 'iis', 'tomcat', 'jboss', 'websphere',
                # Communication & Email
                'exchange', 'postfix', 'sendmail', 'zimbra', 'asterisk',
                # Infrastructure Services
                'dns_server', 'dhcp_server', 'ntp_server', 'ldap_server', 'backup_server',
                # Power & Environmental
                'ups', 'pdu', 'environmental_monitor', 'generator',
                # Security Appliances
                'ids_ips', 'siem', 'vulnerability_scanner',
                # IoT & Embedded
                'raspberry_pi', 'arduino', 'iot_sensor', 'embedded_linux',
                # Generic/Unknown
                'generic_device', 'unknown',
                # Legacy types for backward compatibility
                'email', 'database'
            ]
            if v not in valid_types:
                raise ValueError(f'Device/OS type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment."""
        if v is not None and v not in ['production', 'staging', 'development', 'testing']:
            raise ValueError('Environment must be production, staging, development, or testing')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status."""
        if v is not None and v not in ['active', 'inactive', 'maintenance']:
            raise ValueError('Status must be active, inactive, or maintenance')
        return v


class CommunicationMethodUpdateData(BaseModel):
    """Schema for communication method data in comprehensive updates."""
    id: Optional[int] = Field(None, description="Method ID for existing methods")
    method_type: str = Field(..., description="Communication method type")
    config: Dict[str, Any] = Field(..., description="Method configuration")
    is_primary: bool = Field(False, description="Whether this is the primary method")
    is_active: bool = Field(True, description="Whether this method is active")
    credentials: Optional[List[Dict[str, Any]]] = Field(None, description="Method credentials")


class TargetComprehensiveUpdate(BaseModel):
    """Schema for comprehensive target updates including communication methods and credentials."""
    # Basic target information
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Target name")
    description: Optional[str] = Field(None, description="Target description")
    os_type: Optional[str] = Field(None, description="Device/OS type")
    environment: Optional[str] = Field(None, description="Environment")
    location: Optional[str] = Field(None, description="Physical location")
    data_center: Optional[str] = Field(None, description="Data center name")
    region: Optional[str] = Field(None, description="Geographic region")
    status: Optional[str] = Field(None, description="Target status")
    
    # Multiple communication methods support
    ip_address: Optional[str] = Field(None, description="Primary target IP address")
    communication_methods: Optional[List[CommunicationMethodUpdateData]] = Field(None, description="Communication methods")
    
    # Legacy single method support (for backward compatibility)
    method_type: Optional[str] = Field(None, description="Communication method type")
    port: Optional[int] = Field(None, description="Communication port")
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    ssh_key: Optional[str] = Field(None, description="SSH private key for authentication")
    ssh_passphrase: Optional[str] = Field(None, description="SSH key passphrase")
    
    @validator('os_type')
    def validate_os_type(cls, v):
        """Validate Device/OS type."""
        if v is not None:
            # Valid device/OS types - expanded list
            valid_types = [
                # Operating Systems
                'linux', 'windows', 'windows_desktop', 'macos', 'freebsd', 'aix', 'solaris',
                # Network Infrastructure
                'cisco_switch', 'cisco_router', 'juniper_switch', 'juniper_router', 'arista_switch',
                'hp_switch', 'dell_switch', 'firewall', 'load_balancer', 'wireless_controller', 'access_point',
                # Virtualization & Cloud
                'vmware_esxi', 'vmware_vcenter', 'hyper_v', 'proxmox', 'xen', 'kubernetes', 'docker',
                # Storage Systems
                'netapp', 'emc_storage', 'hp_storage', 'pure_storage', 'synology', 'qnap',
                # Database Systems
                'mysql', 'postgresql', 'mssql', 'oracle_db', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
                # Application Servers
                'apache', 'nginx', 'iis', 'tomcat', 'jboss', 'websphere',
                # Communication & Email
                'exchange', 'postfix', 'sendmail', 'zimbra', 'asterisk',
                # Infrastructure Services
                'dns_server', 'dhcp_server', 'ntp_server', 'ldap_server', 'backup_server',
                # Power & Environmental
                'ups', 'pdu', 'environmental_monitor', 'generator',
                # Security Appliances
                'ids_ips', 'siem', 'vulnerability_scanner',
                # IoT & Embedded
                'raspberry_pi', 'arduino', 'iot_sensor', 'embedded_linux',
                # Generic/Unknown
                'generic_device', 'unknown',
                # Legacy types for backward compatibility
                'email', 'database'
            ]
            if v not in valid_types:
                raise ValueError(f'Device/OS type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment."""
        if v is not None and v not in ['production', 'staging', 'development', 'testing']:
            raise ValueError('Environment must be production, staging, development, or testing')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status."""
        if v is not None and v not in ['active', 'inactive', 'maintenance']:
            raise ValueError('Status must be active, inactive, or maintenance')
        return v
    
    @validator('method_type')
    def validate_method_type(cls, v):
        """Validate communication method type."""
        valid_methods = [
            'ssh', 'winrm', 'snmp', 'telnet', 'rest_api', 'smtp',
            'mysql', 'postgresql', 'mssql', 'oracle', 'sqlite', 
            'mongodb', 'redis', 'elasticsearch'
        ]
        if v is not None and v not in valid_methods:
            raise ValueError(f'Method type must be one of: {", ".join(valid_methods)}')
        return v
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address or DNS name."""
        if v is not None:
            import ipaddress
            import re
            
            # Try IP address first
            try:
                ipaddress.ip_address(v)
                return v
            except ValueError:
                pass
            
            # Validate DNS name format
            dns_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            if re.match(dns_pattern, v) and len(v) <= 253:
                return v
            
            raise ValueError('Invalid IP address or DNS name format')
        return v


class TargetResponse(TargetBase):
    """Schema for target response."""
    id: int
    target_uuid: Union[str, UUID]
    target_serial: str
    is_active: bool
    health_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    communication_methods: List[CommunicationMethodResponse] = []
    
    class Config:
        from_attributes = True


class TargetSummary(BaseModel):
    """Schema for target summary information."""
    id: int
    target_uuid: Union[str, UUID]
    target_serial: str
    name: str
    target_type: str
    os_type: str
    environment: str
    status: str
    health_status: str
    ip_address: Optional[str]
    primary_method: Optional[str]
    communication_methods_count: int
    is_valid: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class ConnectionTestResult(BaseModel):
    """Schema for connection test results."""
    success: bool
    message: str
    ip_address: Optional[str] = None
    method_type: Optional[str] = None


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_type: str = "validation_error"


class BulkTargetOperation(BaseModel):
    """Schema for bulk target operations."""
    target_ids: List[int] = Field(..., min_items=1)
    update_data: Dict[str, Any]


class TargetStatistics(BaseModel):
    """Schema for target statistics."""
    total: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    health_check_coverage: float
    recently_checked_1h: int