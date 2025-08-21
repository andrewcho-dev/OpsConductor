"""
Device Types API v3 - Consolidated from v2/device_types_enhanced.py
All device type management endpoints in v3 structure
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.core.logging import get_structured_logger

api_base_url = os.getenv("API_BASE_URL", "/api/v1")
router = APIRouter(prefix=f"{api_base_url}/device-types", tags=["Device Types v1"])

# Configure structured logger
logger = get_structured_logger(__name__)


# MODELS

class DeviceTypeRequest(BaseModel):
    """Request model for creating/updating device types"""
    name: str = Field(..., description="Device type name")
    description: Optional[str] = Field(None, description="Device type description")
    category: str = Field(default="general", description="Device category")
    os_family: str = Field(..., description="Operating system family")
    default_port: int = Field(default=22, description="Default connection port")
    connection_protocol: str = Field(default="ssh", description="Default connection protocol")
    authentication_methods: List[str] = Field(default=["password", "key"], description="Supported auth methods")
    capabilities: List[str] = Field(default_factory=list, description="Device capabilities")
    configuration_template: Dict[str, Any] = Field(default_factory=dict, description="Configuration template")
    health_check_commands: List[str] = Field(default_factory=list, description="Health check commands")
    is_active: bool = Field(default=True, description="Whether device type is active")


class DeviceTypeResponse(BaseModel):
    """Response model for device types"""
    id: int
    name: str
    description: Optional[str]
    category: str
    os_family: str
    default_port: int
    connection_protocol: str
    authentication_methods: List[str]
    capabilities: List[str]
    configuration_template: Dict[str, Any]
    health_check_commands: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0


class DeviceTypeStats(BaseModel):
    """Model for device type statistics"""
    total_device_types: int
    active_device_types: int
    inactive_device_types: int
    categories: Dict[str, int]
    os_families: Dict[str, int]
    protocols: Dict[str, int]


# ENDPOINTS

@router.get("/", response_model=List[DeviceTypeResponse])
async def get_device_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    os_family: Optional[str] = Query(None),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get device types with filtering"""
    try:
        # Mock device types data
        mock_device_types = [
            {
                "id": 1,
                "name": "Linux Server",
                "description": "Standard Linux server configuration",
                "category": "server",
                "os_family": "linux",
                "default_port": 22,
                "connection_protocol": "ssh",
                "authentication_methods": ["password", "key"],
                "capabilities": ["shell", "file_transfer", "service_management"],
                "configuration_template": {
                    "shell": "/bin/bash",
                    "sudo_required": True,
                    "package_manager": "apt"
                },
                "health_check_commands": ["uptime", "df -h", "free -m"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "usage_count": 15
            },
            {
                "id": 2,
                "name": "Windows Server",
                "description": "Windows Server configuration",
                "category": "server",
                "os_family": "windows",
                "default_port": 5985,
                "connection_protocol": "winrm",
                "authentication_methods": ["password", "kerberos"],
                "capabilities": ["powershell", "file_transfer", "service_management"],
                "configuration_template": {
                    "shell": "powershell",
                    "admin_required": True,
                    "package_manager": "chocolatey"
                },
                "health_check_commands": ["Get-ComputerInfo", "Get-Disk", "Get-Process"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "usage_count": 8
            },
            {
                "id": 3,
                "name": "Network Switch",
                "description": "Cisco network switch",
                "category": "network",
                "os_family": "cisco_ios",
                "default_port": 22,
                "connection_protocol": "ssh",
                "authentication_methods": ["password"],
                "capabilities": ["cli", "configuration_backup"],
                "configuration_template": {
                    "enable_mode": True,
                    "config_mode": "configure terminal"
                },
                "health_check_commands": ["show version", "show interfaces", "show ip route"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "usage_count": 5
            }
        ]
        
        # Apply filters
        filtered_types = mock_device_types
        if category:
            filtered_types = [dt for dt in filtered_types if dt["category"] == category]
        if os_family:
            filtered_types = [dt for dt in filtered_types if dt["os_family"] == os_family]
        if active_only:
            filtered_types = [dt for dt in filtered_types if dt["is_active"]]
        if search:
            filtered_types = [dt for dt in filtered_types if search.lower() in dt["name"].lower() or search.lower() in dt["description"].lower()]
        
        # Apply pagination
        paginated_types = filtered_types[skip:skip + limit]
        
        return [DeviceTypeResponse(**device_type) for device_type in paginated_types]
        
    except Exception as e:
        logger.error(f"Failed to get device types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device types: {str(e)}"
        )


@router.post("/", response_model=DeviceTypeResponse)
async def create_device_type(
    device_type_request: DeviceTypeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new device type"""
    try:
        # Mock device type creation
        device_type_data = {
            "id": 999,
            "name": device_type_request.name,
            "description": device_type_request.description,
            "category": device_type_request.category,
            "os_family": device_type_request.os_family,
            "default_port": device_type_request.default_port,
            "connection_protocol": device_type_request.connection_protocol,
            "authentication_methods": device_type_request.authentication_methods,
            "capabilities": device_type_request.capabilities,
            "configuration_template": device_type_request.configuration_template,
            "health_check_commands": device_type_request.health_check_commands,
            "is_active": device_type_request.is_active,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "usage_count": 0
        }
        
        return DeviceTypeResponse(**device_type_data)
        
    except Exception as e:
        logger.error(f"Failed to create device type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create device type: {str(e)}"
        )


@router.get("/{device_type_id}", response_model=DeviceTypeResponse)
async def get_device_type(
    device_type_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific device type"""
    try:
        # Mock device type data
        device_type_data = {
            "id": device_type_id,
            "name": "Sample Device Type",
            "description": "This is a sample device type",
            "category": "general",
            "os_family": "linux",
            "default_port": 22,
            "connection_protocol": "ssh",
            "authentication_methods": ["password", "key"],
            "capabilities": ["shell", "file_transfer"],
            "configuration_template": {"shell": "/bin/bash"},
            "health_check_commands": ["uptime"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "usage_count": 3
        }
        
        return DeviceTypeResponse(**device_type_data)
        
    except Exception as e:
        logger.error(f"Failed to get device type {device_type_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device type: {str(e)}"
        )


@router.put("/{device_type_id}", response_model=DeviceTypeResponse)
async def update_device_type(
    device_type_id: int,
    device_type_request: DeviceTypeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a device type"""
    try:
        # Mock device type update
        device_type_data = {
            "id": device_type_id,
            "name": device_type_request.name,
            "description": device_type_request.description,
            "category": device_type_request.category,
            "os_family": device_type_request.os_family,
            "default_port": device_type_request.default_port,
            "connection_protocol": device_type_request.connection_protocol,
            "authentication_methods": device_type_request.authentication_methods,
            "capabilities": device_type_request.capabilities,
            "configuration_template": device_type_request.configuration_template,
            "health_check_commands": device_type_request.health_check_commands,
            "is_active": device_type_request.is_active,
            "created_at": datetime.now(timezone.utc) - timedelta(days=1),  # Mock older creation
            "updated_at": datetime.now(timezone.utc),
            "usage_count": 5
        }
        
        return DeviceTypeResponse(**device_type_data)
        
    except Exception as e:
        logger.error(f"Failed to update device type {device_type_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update device type: {str(e)}"
        )


@router.delete("/{device_type_id}")
async def delete_device_type(
    device_type_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a device type"""
    try:
        # This would typically delete the device type from the database
        return {
            "message": f"Device type {device_type_id} deleted successfully",
            "device_type_id": device_type_id
        }
        
    except Exception as e:
        logger.error(f"Failed to delete device type {device_type_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete device type: {str(e)}"
        )


@router.get("/categories/list")
async def get_device_type_categories(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of device type categories"""
    try:
        categories = [
            {"name": "server", "description": "Server devices", "count": 10},
            {"name": "network", "description": "Network devices", "count": 5},
            {"name": "storage", "description": "Storage devices", "count": 3},
            {"name": "security", "description": "Security devices", "count": 2},
            {"name": "iot", "description": "IoT devices", "count": 8},
            {"name": "general", "description": "General purpose devices", "count": 15}
        ]
        
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"Failed to get device type categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device type categories: {str(e)}"
        )


@router.get("/os-families/list")
async def get_os_families(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of supported OS families"""
    try:
        os_families = [
            {"name": "linux", "description": "Linux distributions", "count": 20},
            {"name": "windows", "description": "Windows operating systems", "count": 8},
            {"name": "cisco_ios", "description": "Cisco IOS devices", "count": 5},
            {"name": "juniper_junos", "description": "Juniper JunOS devices", "count": 3},
            {"name": "vmware_esxi", "description": "VMware ESXi hosts", "count": 4},
            {"name": "freebsd", "description": "FreeBSD systems", "count": 2}
        ]
        
        return {"os_families": os_families}
        
    except Exception as e:
        logger.error(f"Failed to get OS families: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get OS families: {str(e)}"
        )


@router.get("/stats/summary", response_model=DeviceTypeStats)
async def get_device_type_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get device type statistics"""
    try:
        stats = DeviceTypeStats(
            total_device_types=43,
            active_device_types=40,
            inactive_device_types=3,
            categories={
                "server": 15,
                "network": 8,
                "storage": 5,
                "security": 3,
                "iot": 10,
                "general": 2
            },
            os_families={
                "linux": 20,
                "windows": 8,
                "cisco_ios": 5,
                "juniper_junos": 3,
                "vmware_esxi": 4,
                "freebsd": 3
            },
            protocols={
                "ssh": 28,
                "winrm": 8,
                "telnet": 3,
                "snmp": 4
            }
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get device type stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device type stats: {str(e)}"
        )


@router.post("/{device_type_id}/validate")
async def validate_device_type(
    device_type_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate a device type configuration"""
    try:
        # Mock validation result
        validation_result = {
            "device_type_id": device_type_id,
            "is_valid": True,
            "validation_errors": [],
            "warnings": [],
            "recommendations": [
                "Consider adding more health check commands",
                "Update authentication methods to include modern options"
            ],
            "validated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Failed to validate device type {device_type_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate device type: {str(e)}"
        )