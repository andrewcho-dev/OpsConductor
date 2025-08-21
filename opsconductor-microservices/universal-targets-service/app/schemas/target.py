"""
Pydantic schemas for Universal Targets Service
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator


# =============================================================================
# Base Schemas
# =============================================================================

class TargetBase(BaseModel):
    """Base schema for target data"""
    name: str = Field(..., min_length=1, max_length=100, description="Target name")
    target_type: str = Field("system", description="Type of target")
    description: Optional[str] = Field(None, description="Target description")
    os_type: str = Field(..., description="Operating system type")
    environment: str = Field("development", description="Environment")
    location: Optional[str] = Field(None, description="Physical location")
    data_center: Optional[str] = Field(None, description="Data center")
    region: Optional[str] = Field(None, description="Region")
    tags: List[str] = Field(default_factory=list, description="Target tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('os_type')
    def validate_os_type(cls, v):
        allowed_os_types = ['linux', 'windows']
        if v not in allowed_os_types:
            raise ValueError(f'os_type must be one of: {allowed_os_types}')
        return v

    @validator('environment')
    def validate_environment(cls, v):
        allowed_environments = ['production', 'staging', 'development', 'testing']
        if v not in allowed_environments:
            raise ValueError(f'environment must be one of: {allowed_environments}')
        return v


class ConnectionMethodBase(BaseModel):
    """Base schema for connection methods"""
    method_type: str = Field(..., description="Connection method type")
    is_primary: bool = Field(False, description="Is this the primary connection method")
    is_active: bool = Field(True, description="Is this method active")
    priority: int = Field(1, ge=1, le=10, description="Method priority")
    config: Dict[str, Any] = Field(..., description="Connection configuration")

    @validator('method_type')
    def validate_method_type(cls, v):
        allowed_methods = [
            'ssh', 'winrm', 'telnet', 'snmp', 'rest_api', 'smtp',
            'mysql', 'postgresql', 'mssql', 'oracle', 'sqlite',
            'mongodb', 'redis', 'elasticsearch'
        ]
        if v not in allowed_methods:
            raise ValueError(f'method_type must be one of: {allowed_methods}')
        return v

    @validator('config')
    def validate_config(cls, v, values):
        """Validate that config contains required fields"""
        if 'host' not in v:
            raise ValueError('config must contain host field')
        
        method_type = values.get('method_type')
        if method_type in ['ssh', 'winrm', 'telnet']:
            if 'port' not in v:
                # Set default ports
                default_ports = {'ssh': 22, 'winrm': 5985, 'telnet': 23}
                v['port'] = default_ports.get(method_type, 22)
        
        return v


class CredentialBase(BaseModel):
    """Base schema for credentials"""
    credential_type: str = Field(..., description="Type of credential")
    credential_name: str = Field(..., description="Name of the credential")
    username: Optional[str] = Field(None, description="Username")
    is_primary: bool = Field(False, description="Is this the primary credential")
    is_active: bool = Field(True, description="Is this credential active")
    expires_at: Optional[datetime] = Field(None, description="Credential expiration")

    @validator('credential_type')
    def validate_credential_type(cls, v):
        allowed_types = ['password', 'ssh_key', 'api_key', 'api_token', 'certificate']
        if v not in allowed_types:
            raise ValueError(f'credential_type must be one of: {allowed_types}')
        return v


# =============================================================================
# Request Schemas
# =============================================================================

class TargetCreate(TargetBase):
    """Schema for creating a target"""
    # Connection method data (for convenience)
    method_type: str = Field(..., description="Primary connection method type")
    host: str = Field(..., description="Target host/IP address")
    port: Optional[int] = Field(None, description="Connection port")
    
    # Credential data (for convenience)
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    ssh_key: Optional[str] = Field(None, description="SSH private key")
    ssh_passphrase: Optional[str] = Field(None, description="SSH key passphrase")


class TargetUpdate(BaseModel):
    """Schema for updating a target"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    target_type: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    environment: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    data_center: Optional[str] = Field(None)
    region: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)


class ConnectionMethodCreate(ConnectionMethodBase):
    """Schema for creating a connection method"""
    pass


class ConnectionMethodUpdate(BaseModel):
    """Schema for updating a connection method"""
    is_primary: Optional[bool] = Field(None)
    is_active: Optional[bool] = Field(None)
    priority: Optional[int] = Field(None, ge=1, le=10)
    config: Optional[Dict[str, Any]] = Field(None)


class CredentialCreate(CredentialBase):
    """Schema for creating a credential"""
    password: Optional[str] = Field(None, description="Password (will be encrypted)")
    ssh_key: Optional[str] = Field(None, description="SSH private key (will be encrypted)")
    ssh_passphrase: Optional[str] = Field(None, description="SSH key passphrase (will be encrypted)")
    api_key: Optional[str] = Field(None, description="API key (will be encrypted)")


class CredentialUpdate(BaseModel):
    """Schema for updating a credential"""
    credential_name: Optional[str] = Field(None)
    username: Optional[str] = Field(None)
    is_primary: Optional[bool] = Field(None)
    is_active: Optional[bool] = Field(None)
    expires_at: Optional[datetime] = Field(None)
    # Note: Sensitive data updates require separate endpoints


# =============================================================================
# Response Schemas
# =============================================================================

class CredentialResponse(CredentialBase):
    """Schema for credential response (no sensitive data)"""
    id: int
    connection_method_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConnectionMethodResponse(ConnectionMethodBase):
    """Schema for connection method response"""
    id: int
    target_id: int
    method_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    credentials: List[CredentialResponse] = []

    class Config:
        from_attributes = True


class TargetResponse(TargetBase):
    """Schema for target response"""
    id: int
    target_uuid: UUID
    target_serial: str
    status: str
    health_status: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    connection_methods: List[ConnectionMethodResponse] = []

    class Config:
        from_attributes = True


class TargetSummary(BaseModel):
    """Schema for target summary (list view)"""
    id: int
    target_uuid: UUID
    target_serial: str
    name: str
    target_type: str
    os_type: str
    environment: str
    status: str
    health_status: str
    is_active: bool
    primary_host: Optional[str] = None
    primary_method_type: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConnectionTestRequest(BaseModel):
    """Schema for connection test request"""
    connection_method_id: Optional[int] = Field(None, description="Specific method to test")
    test_type: str = Field("basic", description="Type of test to perform")
    timeout: int = Field(30, ge=5, le=300, description="Test timeout in seconds")


class ConnectionTestResult(BaseModel):
    """Schema for connection test result"""
    success: bool
    message: str
    response_time: Optional[float] = None  # in seconds
    details: Dict[str, Any] = Field(default_factory=dict)
    tested_at: datetime
    connection_method_id: Optional[int] = None


class HealthCheckResult(BaseModel):
    """Schema for health check result"""
    target_id: int
    status: str  # healthy, warning, critical, unknown
    checks: List[Dict[str, Any]] = []
    overall_response_time: Optional[float] = None
    checked_at: datetime
    next_check_at: Optional[datetime] = None


class BulkOperationRequest(BaseModel):
    """Schema for bulk operations"""
    target_ids: List[int] = Field(..., min_items=1, max_items=100)
    operation_data: Dict[str, Any] = Field(default_factory=dict)


class BulkOperationResult(BaseModel):
    """Schema for bulk operation results"""
    total_requested: int
    successful: int
    failed: int
    results: List[Dict[str, Any]] = []


# =============================================================================
# Error Schemas
# =============================================================================

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    success: bool = False
    message: str
    details: Optional[Dict[str, Any]] = None
    service: str = "universal-targets"
    timestamp: datetime