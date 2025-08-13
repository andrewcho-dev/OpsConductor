"""
Network Discovery API Router
RESTful API endpoints for network discovery functionality.
"""
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.discovery_service import DiscoveryService
from app.schemas.discovery_schemas import (
    DiscoveryJobCreate, DiscoveryJobUpdate, DiscoveryJobResponse, DiscoveryJobSummary,
    DiscoveredDeviceResponse, DiscoveryTemplateCreate, DiscoveryTemplateUpdate, 
    DiscoveryTemplateResponse, DeviceImportRequest, DeviceImportResponse,
    BulkDeviceImportRequest, DeviceTargetConfig,
    DiscoveryStatsResponse, NetworkScanRequest, NetworkScanResponse
)
from app.schemas.target_schemas import ErrorResponse

router = APIRouter(
    prefix="/api/discovery",
    tags=["Network Discovery"],
    responses={
        404: {"model": ErrorResponse, "description": "Resource not found"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)


def get_discovery_service(db: Session = Depends(get_db)) -> DiscoveryService:
    """Dependency to get discovery service instance."""
    return DiscoveryService(db)


# Discovery Jobs

@router.post("/jobs", response_model=DiscoveryJobResponse, status_code=status.HTTP_201_CREATED)
async def create_discovery_job(
    job_data: DiscoveryJobCreate,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Create a new network discovery job.
    
    Args:
        job_data: Discovery job configuration
        
    Returns:
        DiscoveryJobResponse: Created discovery job
    """
    try:
        job = discovery_service.create_discovery_job(job_data)
        return DiscoveryJobResponse.from_orm(job)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create discovery job: {str(e)}"
        )


@router.get("/jobs", response_model=List[DiscoveryJobSummary])
async def list_discovery_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    List discovery jobs with optional filtering.
    
    Args:
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return
        status_filter: Filter by job status
        
    Returns:
        List[DiscoveryJobSummary]: List of discovery jobs
    """
    jobs = discovery_service.list_discovery_jobs(skip=skip, limit=limit, status=status_filter)
    return [
        DiscoveryJobSummary(
            id=job.id,
            name=job.name,
            status=job.status,
            progress=job.progress,
            devices_discovered=job.devices_discovered,
            created_at=job.created_at,
            completed_at=job.completed_at
        )
        for job in jobs
    ]


@router.get("/jobs/{job_id}", response_model=DiscoveryJobResponse)
async def get_discovery_job(
    job_id: int,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Get a specific discovery job by ID.
    
    Args:
        job_id: Discovery job ID
        
    Returns:
        DiscoveryJobResponse: Discovery job details
    """
    job = discovery_service.get_discovery_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery job {job_id} not found"
        )
    
    return DiscoveryJobResponse.from_orm(job)


@router.put("/jobs/{job_id}", response_model=DiscoveryJobResponse)
async def update_discovery_job(
    job_id: int,
    job_data: DiscoveryJobUpdate,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Update a discovery job.
    
    Args:
        job_id: Discovery job ID
        job_data: Updated job data
        
    Returns:
        DiscoveryJobResponse: Updated discovery job
    """
    job = discovery_service.update_discovery_job(job_id, job_data)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery job {job_id} not found"
        )
    
    return DiscoveryJobResponse.from_orm(job)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discovery_job(
    job_id: int,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Delete a discovery job and all associated discovered devices.
    
    Args:
        job_id: Discovery job ID
    """
    success = discovery_service.delete_discovery_job(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery job {job_id} not found or cannot be deleted"
        )


@router.post("/jobs/{job_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_discovery_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Start running a discovery job in the background.
    
    Args:
        job_id: Discovery job ID
        background_tasks: FastAPI background tasks
    """
    job = discovery_service.get_discovery_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery job {job_id} not found"
        )
    
    if job.status != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Discovery job {job_id} is not in pending status"
        )
    
    # Run discovery job in background
    background_tasks.add_task(discovery_service.run_discovery_job, job_id)
    
    return {"message": f"Discovery job {job_id} started"}


@router.post("/jobs/{job_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_discovery_job(
    job_id: int,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Cancel a running discovery job.
    
    Args:
        job_id: Discovery job ID
    """
    success = discovery_service.cancel_discovery_job(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery job {job_id} not found or cannot be cancelled"
        )
    
    return {"message": f"Discovery job {job_id} cancelled"}


# Discovered Devices

@router.get("/devices", response_model=List[DiscoveredDeviceResponse])
async def list_discovered_devices(
    job_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    device_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    List discovered devices with optional filtering.
    
    Args:
        job_id: Filter by discovery job ID
        status_filter: Filter by device status
        device_type: Filter by device type
        skip: Number of devices to skip
        limit: Maximum number of devices to return
        
    Returns:
        List[DiscoveredDeviceResponse]: List of discovered devices
    """
    devices = discovery_service.list_discovered_devices(
        job_id=job_id,
        status=status_filter,
        device_type=device_type,
        skip=skip,
        limit=limit
    )
    
    return [DiscoveredDeviceResponse.from_orm(device) for device in devices]


@router.get("/devices/importable", response_model=List[DiscoveredDeviceResponse])
async def list_importable_devices(
    job_id: Optional[int] = None,
    device_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    List discovered devices that can be imported (not already imported).
    
    Args:
        job_id: Filter by discovery job ID
        device_type: Filter by device type
        skip: Number of devices to skip
        limit: Maximum number of devices to return
        
    Returns:
        List[DiscoveredDeviceResponse]: List of importable discovered devices
    """
    devices = discovery_service.list_importable_devices(
        job_id=job_id,
        device_type=device_type,
        skip=skip,
        limit=limit
    )
    
    return [DiscoveredDeviceResponse.from_orm(device) for device in devices]


@router.get("/devices/{device_id}", response_model=DiscoveredDeviceResponse)
async def get_discovered_device(
    device_id: int,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Get a specific discovered device by ID.
    
    Args:
        device_id: Discovered device ID
        
    Returns:
        DiscoveredDeviceResponse: Discovered device details
    """
    device = discovery_service.get_discovered_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovered device {device_id} not found"
        )
    
    return DiscoveredDeviceResponse.from_orm(device)


@router.put("/devices/{device_id}/status")
async def update_discovered_device_status(
    device_id: int,
    status: str,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Update the status of a discovered device.
    
    Args:
        device_id: Discovered device ID
        status: New status (discovered, imported, ignored)
    """
    device = discovery_service.update_discovered_device_status(device_id, status)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovered device {device_id} not found"
        )
    
    return {"message": f"Device {device_id} status updated to {status}"}


# In-Memory Discovery (no persistence)

@router.post("/discover-memory")
async def run_in_memory_discovery(
    discovery_config: dict
):
    """
    Start network discovery as a Celery task without persisting results.
    Returns task ID for polling progress.
    
    Args:
        discovery_config: Discovery configuration
        
    Returns:
        dict: Task ID and status
    """
    try:
        from app.tasks.discovery_tasks import run_in_memory_discovery_task
        
        # Start Celery task
        task = run_in_memory_discovery_task.delay(discovery_config)
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Discovery task started successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start discovery task: {str(e)}"
        )


@router.get("/discover-memory/{task_id}")
async def get_in_memory_discovery_result(task_id: str):
    """
    Get the result of an in-memory discovery task.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        dict: Task status and results
    """
    try:
        from app.core.celery_app import celery_app
        
        # Get task result
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            return {
                "task_id": task_id,
                "status": "pending",
                "progress": 0,
                "message": "Discovery task is pending..."
            }
        elif task_result.state == 'PROGRESS':
            return {
                "task_id": task_id,
                "status": "running",
                "progress": task_result.info.get('progress', 0),
                "message": task_result.info.get('message', 'Discovery in progress...')
            }
        elif task_result.state == 'SUCCESS':
            result = task_result.result
            devices = result.get('devices', [])
            
            # Convert devices to response format
            device_responses = []
            for device_data in devices:
                if isinstance(device_data, dict):
                    device_responses.append(device_data)
                else:
                    device_responses.append(device_data.__dict__)
            
            return {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "devices": device_responses,
                "message": result.get('message', f'Discovery completed - found {len(devices)} devices')
            }
        else:
            # FAILURE or other states
            return {
                "task_id": task_id,
                "status": "failed",
                "progress": 0,
                "error": str(task_result.info),
                "message": f"Discovery failed: {str(task_result.info)}"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task result: {str(e)}"
        )


# Device Import

@router.post("/devices/import-memory", response_model=DeviceImportResponse)
async def import_in_memory_devices(
    import_request: dict,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Import in-memory discovered devices as targets.
    
    Args:
        import_request: Device import configuration with device_data
        
    Returns:
        DeviceImportResponse: Import results
    """
    try:
        result = discovery_service.import_in_memory_devices(import_request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )

@router.post("/devices/import", response_model=DeviceImportResponse)
async def import_discovered_devices(
    import_request: DeviceImportRequest,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Import discovered devices as targets.
    
    Args:
        import_request: Device import configuration
        
    Returns:
        DeviceImportResponse: Import results
    """
    try:
        result = discovery_service.import_discovered_devices(import_request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import devices: {str(e)}"
        )


@router.post("/devices/import-configured", response_model=DeviceImportResponse)
async def import_configured_devices(
    import_request: BulkDeviceImportRequest,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Import discovered devices as targets with user-provided configuration.
    
    Args:
        import_request: Bulk device import configuration with per-device settings
        
    Returns:
        DeviceImportResponse: Import results
    """
    try:
        result = discovery_service.import_configured_devices(import_request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import configured devices: {str(e)}"
        )


# Discovery Templates

@router.post("/templates", response_model=DiscoveryTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_discovery_template(
    template_data: DiscoveryTemplateCreate,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Create a new discovery template.
    
    Args:
        template_data: Discovery template configuration
        
    Returns:
        DiscoveryTemplateResponse: Created discovery template
    """
    try:
        template = discovery_service.create_discovery_template(template_data)
        return DiscoveryTemplateResponse.from_orm(template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create discovery template: {str(e)}"
        )


@router.get("/templates", response_model=List[DiscoveryTemplateResponse])
async def list_discovery_templates(
    active_only: bool = True,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    List discovery templates.
    
    Args:
        active_only: Only return active templates
        
    Returns:
        List[DiscoveryTemplateResponse]: List of discovery templates
    """
    templates = discovery_service.list_discovery_templates(active_only=active_only)
    return [DiscoveryTemplateResponse.from_orm(template) for template in templates]


@router.get("/templates/{template_id}", response_model=DiscoveryTemplateResponse)
async def get_discovery_template(
    template_id: int,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Get a specific discovery template by ID.
    
    Args:
        template_id: Discovery template ID
        
    Returns:
        DiscoveryTemplateResponse: Discovery template details
    """
    template = discovery_service.get_discovery_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery template {template_id} not found"
        )
    
    return DiscoveryTemplateResponse.from_orm(template)


# Statistics and Quick Scan

@router.get("/stats", response_model=DiscoveryStatsResponse)
async def get_discovery_stats(
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Get discovery statistics and overview.
    
    Returns:
        DiscoveryStatsResponse: Discovery statistics
    """
    return discovery_service.get_discovery_stats()


@router.post("/scan", response_model=NetworkScanResponse)
async def quick_network_scan(
    scan_request: NetworkScanRequest,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Perform a quick network scan without saving results.
    
    Args:
        scan_request: Network scan configuration
        
    Returns:
        NetworkScanResponse: Scan results
    """
    try:
        result = await discovery_service.quick_network_scan(
            network_range=scan_request.network_range,
            ports=scan_request.ports,
            timeout=scan_request.timeout
        )
        
        return NetworkScanResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Network scan failed: {str(e)}"
        )