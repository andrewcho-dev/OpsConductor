"""
Discovery API v2 Enhanced - Phases 1 & 2
Complete transformation with service layer, caching, and comprehensive models

PHASE 1 & 2 IMPROVEMENTS:
- ✅ Comprehensive Pydantic models with validation
- ✅ Service layer integration with business logic separation
- ✅ Redis caching for improved performance
- ✅ Structured JSON logging with contextual information
- ✅ Enhanced error handling with detailed responses
- ✅ Advanced network discovery and device detection
- ✅ Network topology mapping and analysis
- ✅ Real-time discovery monitoring and tracking
- ✅ Comprehensive discovery lifecycle management
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator

# Import service layer
from app.services.discovery_management_service import DiscoveryManagementService, DiscoveryManagementError
from app.database.database import get_db
from app.core.security import verify_token
from app.core.logging import get_structured_logger, RequestLogger

# Configure structured logger
logger = get_structured_logger(__name__)

# Security scheme
security = HTTPBearer()

# PHASE 1: COMPREHENSIVE PYDANTIC MODELS

class DiscoveryOptionsRequest(BaseModel):
    """Enhanced model for discovery options"""
    scan_types: List[str] = Field(default=["ping", "tcp"], description="Types of scans to perform")
    port_ranges: List[Union[int, str]] = Field(default=[22, 80, 443], description="Port ranges to scan")
    timeout: int = Field(default=30, description="Scan timeout in seconds", ge=1, le=300)
    max_threads: int = Field(default=50, description="Maximum concurrent threads", ge=1, le=200)
    service_detection: bool = Field(default=True, description="Enable service detection")
    os_detection: bool = Field(default=False, description="Enable OS detection")
    vulnerability_scan: bool = Field(default=False, description="Enable vulnerability scanning")
    
    @validator('scan_types')
    def validate_scan_types(cls, v):
        """Validate scan types"""
        valid_types = ["ping", "tcp", "udp", "service", "os", "vulnerability"]
        invalid_types = [t for t in v if t not in valid_types]
        if invalid_types:
            raise ValueError(f'Invalid scan types: {invalid_types}. Valid types: {valid_types}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "scan_types": ["ping", "tcp", "service"],
                "port_ranges": [22, 80, 443, "8000-8100"],
                "timeout": 60,
                "max_threads": 100,
                "service_detection": True,
                "os_detection": True,
                "vulnerability_scan": False
            }
        }


class NetworkDiscoveryRequest(BaseModel):
    """Enhanced request model for network discovery"""
    network_range: str = Field(..., description="Network range to discover (CIDR notation)")
    discovery_options: DiscoveryOptionsRequest = Field(default_factory=DiscoveryOptionsRequest, description="Discovery options")
    priority: int = Field(default=5, description="Discovery priority (1-10)", ge=1, le=10)
    schedule: Optional[Dict[str, Any]] = Field(None, description="Discovery schedule configuration")
    
    @validator('network_range')
    def validate_network_range(cls, v):
        """Validate network range format"""
        import ipaddress
        try:
            network = ipaddress.ip_network(v, strict=False)
            if network.num_addresses > 65536:
                raise ValueError('Network range too large (maximum /16 supported)')
            return v
        except ValueError as e:
            raise ValueError(f'Invalid network range: {str(e)}')
    
    class Config:
        json_schema_extra = {
            "example": {
                "network_range": "192.168.1.0/24",
                "discovery_options": {
                    "scan_types": ["ping", "tcp", "service"],
                    "port_ranges": [22, 80, 443],
                    "timeout": 60,
                    "service_detection": True
                },
                "priority": 7,
                "schedule": {
                    "type": "recurring",
                    "interval": "daily",
                    "time": "02:00"
                }
            }
        }


class DiscoveryJobResponse(BaseModel):
    """Enhanced response model for discovery job initiation"""
    discovery_job_id: str = Field(..., description="Discovery job identifier")
    network_range: str = Field(..., description="Network range being discovered")
    status: str = Field(..., description="Discovery job status")
    estimated_duration: int = Field(..., description="Estimated duration in seconds")
    started_at: datetime = Field(..., description="Discovery start timestamp")
    initiated_by: str = Field(..., description="Username who initiated the discovery")
    discovery_options: DiscoveryOptionsRequest = Field(..., description="Discovery options used")
    progress_url: str = Field(..., description="URL to check discovery progress")
    
    class Config:
        json_schema_extra = {
            "example": {
                "discovery_job_id": "discovery_123456",
                "network_range": "192.168.1.0/24",
                "status": "initiated",
                "estimated_duration": 300,
                "started_at": "2025-01-01T10:30:00Z",
                "initiated_by": "admin",
                "discovery_options": {
                    "scan_types": ["ping", "tcp"],
                    "timeout": 60
                },
                "progress_url": "/api/v2/discovery/jobs/discovery_123456/progress"
            }
        }


class DiscoveredDevice(BaseModel):
    """Enhanced model for discovered devices"""
    device_id: str = Field(..., description="Device identifier")
    ip_address: str = Field(..., description="Device IP address")
    hostname: Optional[str] = Field(None, description="Device hostname")
    mac_address: Optional[str] = Field(None, description="Device MAC address")
    device_type: str = Field(..., description="Device type")
    operating_system: Optional[str] = Field(None, description="Operating system")
    services: List[Dict[str, Any]] = Field(default_factory=list, description="Running services")
    last_seen: datetime = Field(..., description="Last seen timestamp")
    status: str = Field(..., description="Device status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "device_192_168_1_100",
                "ip_address": "192.168.1.100",
                "hostname": "server-01.local",
                "mac_address": "00:11:22:33:44:55",
                "device_type": "server",
                "operating_system": "Linux Ubuntu 20.04",
                "services": [
                    {"port": 22, "service": "ssh", "version": "OpenSSH 8.2"},
                    {"port": 80, "service": "http", "version": "Apache 2.4"}
                ],
                "last_seen": "2025-01-01T10:30:00Z",
                "status": "active"
            }
        }


class DiscoveryProgressInfo(BaseModel):
    """Enhanced model for discovery progress information"""
    completed: int = Field(..., description="Number of completed scans")
    total: int = Field(..., description="Total number of scans")
    current_target: Optional[str] = Field(None, description="Currently scanning target")
    phase: str = Field(..., description="Current discovery phase")
    errors: int = Field(default=0, description="Number of errors encountered")
    
    class Config:
        json_schema_extra = {
            "example": {
                "completed": 150,
                "total": 254,
                "current_target": "192.168.1.150",
                "phase": "service_detection",
                "errors": 2
            }
        }


class DiscoveryJobStatusResponse(BaseModel):
    """Enhanced response model for discovery job status"""
    job_id: str = Field(..., description="Discovery job identifier")
    status: str = Field(..., description="Job status")
    network_range: str = Field(..., description="Network range")
    started_at: datetime = Field(..., description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    progress: DiscoveryProgressInfo = Field(..., description="Discovery progress information")
    completion_percentage: float = Field(..., description="Completion percentage")
    discovered_devices_count: int = Field(..., description="Number of discovered devices")
    discovered_devices: List[DiscoveredDevice] = Field(..., description="List of discovered devices")
    discovery_options: DiscoveryOptionsRequest = Field(..., description="Discovery options used")
    initiated_by: str = Field(..., description="Username who initiated the discovery")
    errors: List[str] = Field(default_factory=list, description="Discovery errors")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Job metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "discovery_123456",
                "status": "running",
                "network_range": "192.168.1.0/24",
                "started_at": "2025-01-01T10:30:00Z",
                "completed_at": None,
                "progress": {
                    "completed": 150,
                    "total": 254,
                    "current_target": "192.168.1.150",
                    "phase": "service_detection"
                },
                "completion_percentage": 59.1,
                "discovered_devices_count": 25,
                "discovered_devices": [],
                "discovery_options": {
                    "scan_types": ["ping", "tcp"],
                    "timeout": 60
                },
                "initiated_by": "admin",
                "errors": [],
                "metadata": {
                    "last_updated": "2025-01-01T10:35:00Z",
                    "version": "2.0"
                }
            }
        }


class NetworkInventoryResponse(BaseModel):
    """Enhanced response model for network inventory"""
    total_devices: int = Field(..., description="Total number of devices")
    devices: List[DiscoveredDevice] = Field(..., description="List of all discovered devices")
    device_statistics: Dict[str, Any] = Field(..., description="Device statistics")
    network_topology: Dict[str, Any] = Field(..., description="Network topology information")
    network_segments: List[Dict[str, Any]] = Field(..., description="Network segments")
    last_discovery: datetime = Field(..., description="Last discovery timestamp")
    inventory_health: str = Field(..., description="Inventory health status")
    recommendations: List[str] = Field(default_factory=list, description="Inventory recommendations")
    last_updated: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Inventory metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_devices": 150,
                "devices": [],
                "device_statistics": {
                    "by_type": {"server": 25, "workstation": 100, "network": 25},
                    "by_os": {"Linux": 50, "Windows": 75, "Unknown": 25}
                },
                "network_topology": {
                    "subnets": ["192.168.1.0/24", "192.168.2.0/24"],
                    "gateways": ["192.168.1.1", "192.168.2.1"]
                },
                "network_segments": [
                    {"segment": "192.168.1.0/24", "device_count": 100},
                    {"segment": "192.168.2.0/24", "device_count": 50}
                ],
                "last_discovery": "2025-01-01T02:00:00Z",
                "inventory_health": "healthy",
                "recommendations": [
                    "Schedule regular discovery scans",
                    "Update device classifications"
                ],
                "last_updated": "2025-01-01T10:30:00Z",
                "metadata": {
                    "source": "network_inventory",
                    "version": "2.0"
                }
            }
        }


class DeviceDetailsResponse(BaseModel):
    """Enhanced response model for device details"""
    device_id: str = Field(..., description="Device identifier")
    basic_info: Dict[str, Any] = Field(..., description="Basic device information")
    services: List[Dict[str, Any]] = Field(..., description="Device services")
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list, description="Device vulnerabilities")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    discovery_history: List[Dict[str, Any]] = Field(default_factory=list, description="Discovery history")
    security_score: float = Field(..., description="Device security score")
    recommendations: List[str] = Field(default_factory=list, description="Device recommendations")
    last_seen: datetime = Field(..., description="Last seen timestamp")
    last_updated: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Device metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "device_192_168_1_100",
                "basic_info": {
                    "ip_address": "192.168.1.100",
                    "hostname": "server-01.local",
                    "device_type": "server",
                    "operating_system": "Linux Ubuntu 20.04"
                },
                "services": [
                    {"port": 22, "service": "ssh", "version": "OpenSSH 8.2"},
                    {"port": 80, "service": "http", "version": "Apache 2.4"}
                ],
                "vulnerabilities": [
                    {"cve": "CVE-2021-1234", "severity": "medium", "description": "Sample vulnerability"}
                ],
                "performance_metrics": {
                    "response_time": 5.2,
                    "availability": 99.9
                },
                "discovery_history": [
                    {"timestamp": "2025-01-01T02:00:00Z", "status": "discovered"}
                ],
                "security_score": 85.5,
                "recommendations": [
                    "Update SSH version",
                    "Enable firewall"
                ],
                "last_seen": "2025-01-01T10:30:00Z",
                "last_updated": "2025-01-01T10:30:00Z",
                "metadata": {
                    "source": "device_discovery",
                    "version": "2.0"
                }
            }
        }


class DiscoveryStatisticsResponse(BaseModel):
    """Enhanced response model for discovery statistics"""
    job_statistics: Dict[str, Any] = Field(..., description="Discovery job statistics")
    device_statistics: Dict[str, Any] = Field(..., description="Device discovery statistics")
    network_coverage: Dict[str, Any] = Field(..., description="Network coverage statistics")
    performance_metrics: Dict[str, Any] = Field(..., description="Discovery performance metrics")
    trends: Dict[str, Any] = Field(default_factory=dict, description="Discovery trends")
    recommendations: List[str] = Field(default_factory=list, description="Discovery recommendations")
    last_updated: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Statistics metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_statistics": {
                    "total_jobs": 50,
                    "completed_jobs": 45,
                    "failed_jobs": 2,
                    "running_jobs": 3
                },
                "device_statistics": {
                    "total_devices": 250,
                    "active_devices": 230,
                    "inactive_devices": 20,
                    "new_devices_today": 5
                },
                "network_coverage": {
                    "coverage_percentage": 85.5,
                    "scanned_subnets": 10,
                    "total_subnets": 12
                },
                "performance_metrics": {
                    "avg_scan_time": 120.5,
                    "avg_devices_per_scan": 25.5,
                    "success_rate": 95.2
                },
                "trends": {
                    "devices_growth": "+5%",
                    "scan_efficiency": "+12%"
                },
                "recommendations": [
                    "Increase scan frequency for critical networks",
                    "Review failed discovery jobs"
                ],
                "last_updated": "2025-01-01T10:30:00Z",
                "metadata": {
                    "source": "discovery_analytics",
                    "version": "2.0"
                }
            }
        }


class DiscoveryErrorResponse(BaseModel):
    """Enhanced error response model for discovery management errors"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    discovery_component: Optional[str] = Field(None, description="Related discovery component")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "discovery_initiation_error",
                "message": "Failed to initiate network discovery due to invalid network range",
                "details": {
                    "network_range": "192.168.1.0/8",
                    "validation_errors": ["Network range too large"]
                },
                "timestamp": "2025-01-01T10:30:00Z",
                "discovery_component": "network_scanner"
            }
        }


# PHASE 1 & 2: ENHANCED ROUTER WITH SERVICE LAYER INTEGRATION

router = APIRouter(
    prefix="/api/v2/discovery",
    tags=["Network Discovery Enhanced v2"],
    responses={
        401: {"model": DiscoveryErrorResponse, "description": "Authentication required"},
        403: {"model": DiscoveryErrorResponse, "description": "Insufficient permissions"},
        404: {"model": DiscoveryErrorResponse, "description": "Resource not found"},
        422: {"model": DiscoveryErrorResponse, "description": "Validation error"},
        500: {"model": DiscoveryErrorResponse, "description": "Internal server error"}
    }
)


# PHASE 2: ENHANCED DEPENDENCY FUNCTIONS

def get_current_user(credentials = Depends(security), 
                    db: Session = Depends(get_db)):
    """Get current authenticated user with enhanced error handling."""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            logger.warning("Invalid token in discovery management request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Invalid or expired token",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        user_id = payload.get("user_id")
        from app.services.user_service import UserService
        user = UserService.get_user_by_id(db, user_id)
        
        if not user:
            logger.warning(f"User not found for token: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "user_not_found",
                    "message": "User not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Internal error during authentication",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def require_discovery_permissions(current_user = Depends(get_current_user)):
    """Require discovery permissions."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_permissions",
                "message": "Insufficient permissions to perform network discovery",
                "required_roles": ["administrator", "operator"],
                "user_role": current_user.role,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    return current_user


# PHASE 1 & 2: ENHANCED ENDPOINTS WITH SERVICE LAYER

@router.post(
    "/start",
    response_model=DiscoveryJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start Network Discovery",
    description="""
    Start a comprehensive network discovery scan with advanced options.
    
    **Phase 1 & 2 Features:**
    - ✅ Advanced network range validation
    - ✅ Comprehensive discovery options
    - ✅ Real-time progress tracking
    - ✅ Enhanced discovery job management
    
    **Security:**
    - Network range validation and restrictions
    - Comprehensive audit logging
    - Role-based access control
    """,
    responses={
        201: {"description": "Network discovery started successfully", "model": DiscoveryJobResponse}
    }
)
async def start_network_discovery(
    discovery_request: NetworkDiscoveryRequest,
    request: Request,
    current_user = Depends(require_discovery_permissions),
    db: Session = Depends(get_db)
) -> DiscoveryJobResponse:
    """Enhanced network discovery with service layer and comprehensive validation"""
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_logger = RequestLogger(logger, f"start_discovery_{discovery_request.network_range}")
    request_logger.log_request_start("POST", "/api/v2/discovery/start", current_user.username)
    
    try:
        # Initialize service layer
        discovery_mgmt_service = DiscoveryManagementService(db)
        
        # Start network discovery through service layer
        discovery_result = await discovery_mgmt_service.start_network_discovery(
            network_range=discovery_request.network_range,
            discovery_options=discovery_request.discovery_options.model_dump(),
            current_user_id=current_user.id,
            current_username=current_user.username,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        response = DiscoveryJobResponse(**discovery_result)
        
        request_logger.log_request_end(status.HTTP_201_CREATED, len(str(response)))
        
        logger.info(
            "Network discovery started successfully via service layer",
            extra={
                "discovery_job_id": discovery_result["discovery_job_id"],
                "network_range": discovery_request.network_range,
                "initiated_by": current_user.username
            }
        )
        
        return response
        
    except DiscoveryManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Network discovery start failed via service layer",
            extra={
                "network_range": discovery_request.network_range,
                "error_code": e.error_code,
                "error_message": e.message,
                "initiated_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Network discovery start error via service layer",
            extra={
                "network_range": discovery_request.network_range,
                "error": str(e),
                "initiated_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while starting network discovery",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/jobs/{job_id}/status",
    response_model=DiscoveryJobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Discovery Job Status",
    description="""
    Get comprehensive discovery job status with progress tracking.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 1-minute TTL
    - ✅ Real-time progress tracking
    - ✅ Comprehensive job information
    - ✅ Enhanced discovery monitoring
    """,
    responses={
        200: {"description": "Discovery job status retrieved successfully", "model": DiscoveryJobStatusResponse}
    }
)
async def get_discovery_job_status(
    job_id: str,
    current_user = Depends(require_discovery_permissions),
    db: Session = Depends(get_db)
) -> DiscoveryJobStatusResponse:
    """Enhanced discovery job status with service layer and comprehensive tracking"""
    
    request_logger = RequestLogger(logger, f"get_discovery_status_{job_id}")
    request_logger.log_request_start("GET", f"/api/v2/discovery/jobs/{job_id}/status", current_user.username)
    
    try:
        # Initialize service layer
        discovery_mgmt_service = DiscoveryManagementService(db)
        
        # Get discovery job status through service layer (with caching)
        status_result = await discovery_mgmt_service.get_discovery_job_status(
            job_id=job_id,
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = DiscoveryJobStatusResponse(**status_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Discovery job status retrieval successful via service layer",
            extra={
                "job_id": job_id,
                "status": status_result.get("status", "unknown"),
                "completion_percentage": status_result.get("completion_percentage", 0),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except DiscoveryManagementError as e:
        request_logger.log_request_end(status.HTTP_404_NOT_FOUND if e.error_code == "discovery_job_not_found" else status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Discovery job status retrieval failed via service layer",
            extra={
                "job_id": job_id,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        status_code = status.HTTP_404_NOT_FOUND if e.error_code == "discovery_job_not_found" else status.HTTP_500_INTERNAL_SERVER_ERROR
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Discovery job status retrieval error via service layer",
            extra={
                "job_id": job_id,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving discovery job status",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/inventory",
    response_model=NetworkInventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Network Inventory",
    description="""
    Get comprehensive network inventory with device information and topology.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 5-minute TTL
    - ✅ Comprehensive device inventory
    - ✅ Network topology mapping
    - ✅ Enhanced inventory analytics
    """,
    responses={
        200: {"description": "Network inventory retrieved successfully", "model": NetworkInventoryResponse}
    }
)
async def get_network_inventory(
    current_user = Depends(require_discovery_permissions),
    db: Session = Depends(get_db)
) -> NetworkInventoryResponse:
    """Enhanced network inventory with service layer and comprehensive device information"""
    
    request_logger = RequestLogger(logger, "get_network_inventory")
    request_logger.log_request_start("GET", "/api/v2/discovery/inventory", current_user.username)
    
    try:
        # Initialize service layer
        discovery_mgmt_service = DiscoveryManagementService(db)
        
        # Get network inventory through service layer (with caching)
        inventory_result = await discovery_mgmt_service.get_network_inventory(
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = NetworkInventoryResponse(**inventory_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Network inventory retrieval successful via service layer",
            extra={
                "total_devices": inventory_result.get("total_devices", 0),
                "inventory_health": inventory_result.get("inventory_health", "unknown"),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except DiscoveryManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Network inventory retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Network inventory retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving network inventory",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/devices/{device_id}",
    response_model=DeviceDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Device Details",
    description="""
    Get comprehensive device details with services, vulnerabilities, and recommendations.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 5-minute TTL
    - ✅ Comprehensive device information
    - ✅ Security scoring and recommendations
    - ✅ Enhanced device analytics
    """,
    responses={
        200: {"description": "Device details retrieved successfully", "model": DeviceDetailsResponse}
    }
)
async def get_device_details(
    device_id: str,
    current_user = Depends(require_discovery_permissions),
    db: Session = Depends(get_db)
) -> DeviceDetailsResponse:
    """Enhanced device details with service layer and comprehensive information"""
    
    request_logger = RequestLogger(logger, f"get_device_details_{device_id}")
    request_logger.log_request_start("GET", f"/api/v2/discovery/devices/{device_id}", current_user.username)
    
    try:
        # Initialize service layer
        discovery_mgmt_service = DiscoveryManagementService(db)
        
        # Get device details through service layer (with caching)
        device_result = await discovery_mgmt_service.get_device_details(
            device_id=device_id,
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = DeviceDetailsResponse(**device_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Device details retrieval successful via service layer",
            extra={
                "device_id": device_id,
                "security_score": device_result.get("security_score", 0),
                "services_count": len(device_result.get("services", [])),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except DiscoveryManagementError as e:
        request_logger.log_request_end(status.HTTP_404_NOT_FOUND if e.error_code == "device_not_found" else status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Device details retrieval failed via service layer",
            extra={
                "device_id": device_id,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        status_code = status.HTTP_404_NOT_FOUND if e.error_code == "device_not_found" else status.HTTP_500_INTERNAL_SERVER_ERROR
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Device details retrieval error via service layer",
            extra={
                "device_id": device_id,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving device details",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/statistics",
    response_model=DiscoveryStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Discovery Statistics",
    description="""
    Get comprehensive discovery statistics with analytics and trends.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 5-minute TTL
    - ✅ Comprehensive discovery analytics
    - ✅ Performance metrics and trends
    - ✅ Enhanced discovery insights
    """,
    responses={
        200: {"description": "Discovery statistics retrieved successfully", "model": DiscoveryStatisticsResponse}
    }
)
async def get_discovery_statistics(
    current_user = Depends(require_discovery_permissions),
    db: Session = Depends(get_db)
) -> DiscoveryStatisticsResponse:
    """Enhanced discovery statistics with service layer and comprehensive analytics"""
    
    request_logger = RequestLogger(logger, "get_discovery_statistics")
    request_logger.log_request_start("GET", "/api/v2/discovery/statistics", current_user.username)
    
    try:
        # Initialize service layer
        discovery_mgmt_service = DiscoveryManagementService(db)
        
        # Get discovery statistics through service layer (with caching)
        stats_result = await discovery_mgmt_service.get_discovery_statistics(
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = DiscoveryStatisticsResponse(**stats_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Discovery statistics retrieval successful via service layer",
            extra={
                "total_jobs": stats_result.get("job_statistics", {}).get("total_jobs", 0),
                "total_devices": stats_result.get("device_statistics", {}).get("total_devices", 0),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except DiscoveryManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Discovery statistics retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Discovery statistics retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving discovery statistics",
                "timestamp": datetime.utcnow().isoformat()
            }
        )