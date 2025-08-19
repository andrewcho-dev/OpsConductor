"""
Discovery API v3 - Consolidated from v2/discovery_enhanced.py
All network discovery endpoints in v3 structure
"""

import os
import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator

from app.services.discovery_management_service import DiscoveryManagementService, DiscoveryManagementError
from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.core.logging import get_structured_logger

router = APIRouter(prefix=f"{os.getenv(\'API_BASE_URL\', \'/api/v3\')}/discovery", tags=["Discovery v3"])

# Configure structured logger
logger = get_structured_logger(__name__)


# MODELS

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


class DiscoveredDeviceInfo(BaseModel):
    """Model for discovered device information"""
    ip_address: str
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    open_ports: List[int] = Field(default_factory=list)
    services: Dict[str, Any] = Field(default_factory=dict)
    response_time: Optional[float] = None
    last_seen: datetime
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class DiscoveryJobResponse(BaseModel):
    """Response model for discovery jobs"""
    id: int
    network_range: str
    status: str
    progress: float = Field(ge=0.0, le=100.0)
    devices_found: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    discovery_options: Dict[str, Any]


class DiscoveryResultsResponse(BaseModel):
    """Response model for discovery results"""
    job_id: int
    total_devices: int
    devices: List[DiscoveredDeviceInfo]
    network_topology: Dict[str, Any] = Field(default_factory=dict)
    scan_statistics: Dict[str, Any] = Field(default_factory=dict)


# ENDPOINTS

@router.post("/jobs", response_model=DiscoveryJobResponse)
async def create_discovery_job(
    discovery_request: NetworkDiscoveryRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new network discovery job"""
    try:
        discovery_service = DiscoveryManagementService(db)
        
        # Create discovery job
        job = await discovery_service.create_discovery_job(
            network_range=discovery_request.network_range,
            discovery_options=discovery_request.discovery_options.dict(),
            priority=discovery_request.priority,
            schedule=discovery_request.schedule,
            user_id=current_user["id"]
        )
        
        return DiscoveryJobResponse(
            id=job.get("id"),
            network_range=job.get("network_range"),
            status=job.get("status"),
            progress=job.get("progress", 0.0),
            devices_found=job.get("devices_found", 0),
            created_at=job.get("created_at"),
            started_at=job.get("started_at"),
            completed_at=job.get("completed_at"),
            error_message=job.get("error_message"),
            discovery_options=job.get("discovery_options", {})
        )
    except DiscoveryManagementError as e:
        logger.error(f"Discovery management error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create discovery job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create discovery job: {str(e)}"
        )


@router.get("/jobs", response_model=List[DiscoveryJobResponse])
async def get_discovery_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get discovery jobs with filtering"""
    try:
        discovery_service = DiscoveryManagementService(db)
        
        jobs = await discovery_service.get_discovery_jobs(
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            user_id=current_user["id"]
        )
        
        return [
            DiscoveryJobResponse(
                id=job.get("id"),
                network_range=job.get("network_range"),
                status=job.get("status"),
                progress=job.get("progress", 0.0),
                devices_found=job.get("devices_found", 0),
                created_at=job.get("created_at"),
                started_at=job.get("started_at"),
                completed_at=job.get("completed_at"),
                error_message=job.get("error_message"),
                discovery_options=job.get("discovery_options", {})
            )
            for job in jobs
        ]
    except Exception as e:
        logger.error(f"Failed to get discovery jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get discovery jobs: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=DiscoveryJobResponse)
async def get_discovery_job(
    job_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific discovery job"""
    try:
        discovery_service = DiscoveryManagementService(db)
        
        job = await discovery_service.get_discovery_job(job_id, current_user["id"])
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery job {job_id} not found"
            )
        
        return DiscoveryJobResponse(
            id=job.get("id"),
            network_range=job.get("network_range"),
            status=job.get("status"),
            progress=job.get("progress", 0.0),
            devices_found=job.get("devices_found", 0),
            created_at=job.get("created_at"),
            started_at=job.get("started_at"),
            completed_at=job.get("completed_at"),
            error_message=job.get("error_message"),
            discovery_options=job.get("discovery_options", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get discovery job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get discovery job: {str(e)}"
        )


@router.get("/jobs/{job_id}/results", response_model=DiscoveryResultsResponse)
async def get_discovery_results(
    job_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get discovery results for a job"""
    try:
        discovery_service = DiscoveryManagementService(db)
        
        results = await discovery_service.get_discovery_results(job_id, current_user["id"])
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery results for job {job_id} not found"
            )
        
        # Convert devices to DiscoveredDeviceInfo objects
        devices = []
        for device_data in results.get("devices", []):
            devices.append(DiscoveredDeviceInfo(
                ip_address=device_data.get("ip_address"),
                hostname=device_data.get("hostname"),
                mac_address=device_data.get("mac_address"),
                os_type=device_data.get("os_type"),
                os_version=device_data.get("os_version"),
                open_ports=device_data.get("open_ports", []),
                services=device_data.get("services", {}),
                response_time=device_data.get("response_time"),
                last_seen=device_data.get("last_seen", datetime.now(timezone.utc)),
                confidence_score=device_data.get("confidence_score", 0.0)
            ))
        
        return DiscoveryResultsResponse(
            job_id=job_id,
            total_devices=len(devices),
            devices=devices,
            network_topology=results.get("network_topology", {}),
            scan_statistics=results.get("scan_statistics", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get discovery results for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get discovery results: {str(e)}"
        )


@router.post("/jobs/{job_id}/start")
async def start_discovery_job(
    job_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a discovery job"""
    try:
        discovery_service = DiscoveryManagementService(db)
        
        result = await discovery_service.start_discovery_job(job_id, current_user["id"])
        
        return {
            "message": f"Discovery job {job_id} started successfully",
            "job_id": job_id,
            "status": result.get("status"),
            "started_at": result.get("started_at")
        }
    except DiscoveryManagementError as e:
        logger.error(f"Discovery management error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to start discovery job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start discovery job: {str(e)}"
        )


@router.post("/jobs/{job_id}/stop")
async def stop_discovery_job(
    job_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop a discovery job"""
    try:
        discovery_service = DiscoveryManagementService(db)
        
        result = await discovery_service.stop_discovery_job(job_id, current_user["id"])
        
        return {
            "message": f"Discovery job {job_id} stopped successfully",
            "job_id": job_id,
            "status": result.get("status"),
            "stopped_at": result.get("stopped_at")
        }
    except DiscoveryManagementError as e:
        logger.error(f"Discovery management error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to stop discovery job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop discovery job: {str(e)}"
        )


@router.delete("/jobs/{job_id}")
async def delete_discovery_job(
    job_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a discovery job"""
    try:
        discovery_service = DiscoveryManagementService(db)
        
        await discovery_service.delete_discovery_job(job_id, current_user["id"])
        
        return {
            "message": f"Discovery job {job_id} deleted successfully",
            "job_id": job_id
        }
    except DiscoveryManagementError as e:
        logger.error(f"Discovery management error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete discovery job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete discovery job: {str(e)}"
        )


@router.get("/network-topology")
async def get_network_topology(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get network topology information"""
    try:
        discovery_service = DiscoveryManagementService(db)
        
        topology = await discovery_service.get_network_topology(current_user["id"])
        
        return {
            "topology": topology,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get network topology: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get network topology: {str(e)}"
        )