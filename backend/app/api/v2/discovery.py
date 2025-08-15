"""
Discovery API v2 - Enhanced Network Discovery & Inventory
Consolidates and enhances discovery functionality into a unified API.

This replaces and enhances:
- /api/discovery/* (discovery.py) - Network discovery operations
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import verify_token
from app.models.user_models import User
from app.services.user_service import UserService
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/discovery", tags=["Network Discovery v2"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                    db: Session = Depends(get_db)):
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("user_id")
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_utc_timestamp() -> str:
    """Get current UTC timestamp with timezone information."""
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# DISCOVERY OPERATIONS
# ============================================================================

@router.post("/scan", response_model=Dict[str, Any])
async def start_discovery_scan(
    scan_config: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new network discovery scan."""
    try:
        # Validate scan configuration
        required_fields = ["name", "target_range", "discovery_method"]
        for field in required_fields:
            if field not in scan_config:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )
        
        # Create discovery job
        discovery_job = await create_discovery_job(db, scan_config, current_user.id)
        
        # Log discovery start
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.DISCOVERY_STARTED,
            user_id=current_user.id,
            resource_type="discovery_job",
            resource_id=str(discovery_job["id"]),
            action="start_discovery",
            details={
                "scan_name": scan_config["name"],
                "target_range": scan_config["target_range"],
                "method": scan_config["discovery_method"]
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return discovery_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start discovery scan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start discovery scan")


@router.get("/scans", response_model=List[Dict[str, Any]])
async def get_discovery_scans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200)
):
    """Get discovery scans with filtering."""
    try:
        scans = await get_discovery_jobs(db, status, limit)
        return scans
        
    except Exception as e:
        logger.error(f"Failed to get discovery scans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discovery scans")


@router.get("/scans/{scan_id}", response_model=Dict[str, Any])
async def get_discovery_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_results: bool = Query(True, description="Include scan results")
):
    """Get discovery scan details."""
    try:
        scan = await get_discovery_job_by_id(db, scan_id, include_results)
        if not scan:
            raise HTTPException(status_code=404, detail="Discovery scan not found")
        
        return scan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get discovery scan {scan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discovery scan")


@router.post("/scans/{scan_id}/stop", response_model=Dict[str, Any])
async def stop_discovery_scan(
    scan_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop a running discovery scan."""
    try:
        result = await stop_discovery_job(db, scan_id, current_user.id)
        
        # Log discovery stop
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.DISCOVERY_STOPPED,
            user_id=current_user.id,
            resource_type="discovery_job",
            resource_id=str(scan_id),
            action="stop_discovery",
            details={"scan_id": scan_id, "stopped_by": current_user.username},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to stop discovery scan {scan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop discovery scan")


@router.delete("/scans/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discovery_scan(
    scan_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a discovery scan and its results."""
    try:
        success = await delete_discovery_job(db, scan_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Discovery scan not found")
        
        # Log discovery deletion
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.RESOURCE_DELETED,
            user_id=current_user.id,
            resource_type="discovery_job",
            resource_id=str(scan_id),
            action="delete_discovery",
            details={"scan_id": scan_id, "deleted_by": current_user.username},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete discovery scan {scan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete discovery scan")


# ============================================================================
# DISCOVERED DEVICES MANAGEMENT
# ============================================================================

@router.get("/devices", response_model=List[Dict[str, Any]])
async def get_discovered_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scan_id: Optional[int] = Query(None, description="Filter by scan ID"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in hostname/IP"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get discovered devices with filtering and pagination."""
    try:
        devices = await get_discovered_devices_list(
            db, scan_id, device_type, status, search, skip, limit
        )
        return devices
        
    except Exception as e:
        logger.error(f"Failed to get discovered devices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discovered devices")


@router.get("/devices/{device_id}", response_model=Dict[str, Any])
async def get_discovered_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get discovered device details."""
    try:
        device = await get_discovered_device_by_id(db, device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Discovered device not found")
        
        return device
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get discovered device {device_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discovered device")


@router.post("/devices/{device_id}/import", response_model=Dict[str, Any])
async def import_discovered_device(
    device_id: int,
    import_config: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import a discovered device as a managed target."""
    try:
        imported_target = await import_device_as_target(db, device_id, import_config, current_user.id)
        
        # Log device import
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.DEVICE_IMPORTED,
            user_id=current_user.id,
            resource_type="target",
            resource_id=str(imported_target["id"]),
            action="import_device",
            details={
                "device_id": device_id,
                "target_id": imported_target["id"],
                "hostname": imported_target.get("hostname")
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return imported_target
        
    except Exception as e:
        logger.error(f"Failed to import device {device_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to import discovered device")


@router.post("/devices/bulk-import", response_model=Dict[str, Any])
async def bulk_import_devices(
    device_ids: List[int],
    import_config: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import multiple discovered devices as managed targets."""
    try:
        results = []
        for device_id in device_ids:
            try:
                imported_target = await import_device_as_target(db, device_id, import_config, current_user.id)
                results.append({"device_id": device_id, "target_id": imported_target["id"], "status": "imported"})
            except Exception as e:
                results.append({"device_id": device_id, "status": "error", "error": str(e)})
        
        # Log bulk import
        audit_service = AuditService(db)
        await audit_service.log_event(
            event_type=AuditEventType.BULK_OPERATION,
            user_id=current_user.id,
            resource_type="target",
            resource_id="bulk",
            action="bulk_import_devices",
            details={"device_ids": device_ids, "results_count": len(results)},
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return {
            "success": True,
            "results": results,
            "timestamp": get_utc_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk import devices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to bulk import devices")


# ============================================================================
# DISCOVERY ANALYTICS & REPORTING
# ============================================================================

@router.get("/analytics/summary", response_model=Dict[str, Any])
async def get_discovery_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d")
):
    """Get discovery analytics and summary."""
    try:
        # Parse time range
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(time_range, 30)
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        analytics = await get_discovery_analytics_data(db, since)
        
        return {
            "timestamp": get_utc_timestamp(),
            "time_range": time_range,
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discovery analytics")


@router.get("/analytics/trends", response_model=Dict[str, Any])
async def get_discovery_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    metric: str = Query("devices_discovered", description="Metric to analyze"),
    time_range: str = Query("30d", description="Time range for trends")
):
    """Get discovery trends and patterns."""
    try:
        trends = await get_discovery_trends_data(db, metric, time_range)
        
        return {
            "metric": metric,
            "time_range": time_range,
            "trends": trends,
            "timestamp": get_utc_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discovery trends")


# ============================================================================
# DISCOVERY CONFIGURATION
# ============================================================================

@router.get("/methods", response_model=List[Dict[str, Any]])
async def get_discovery_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available discovery methods and their configurations."""
    try:
        methods = await get_available_discovery_methods()
        return methods
        
    except Exception as e:
        logger.error(f"Failed to get discovery methods: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discovery methods")


@router.post("/validate-config", response_model=Dict[str, Any])
async def validate_discovery_config(
    config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate a discovery configuration."""
    try:
        validation_result = await validate_discovery_configuration(config)
        
        return {
            "is_valid": validation_result["is_valid"],
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "suggestions": validation_result.get("suggestions", [])
        }
        
    except Exception as e:
        logger.error(f"Failed to validate discovery config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate discovery configuration")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def create_discovery_job(db: Session, config: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Create a new discovery job."""
    try:
        # This would integrate with your discovery service
        job_id = 999  # Mock ID
        return {
            "id": job_id,
            "name": config["name"],
            "target_range": config["target_range"],
            "discovery_method": config["discovery_method"],
            "status": "queued",
            "created_at": get_utc_timestamp(),
            "created_by": user_id
        }
    except Exception:
        raise


async def get_discovery_jobs(db: Session, status_filter: Optional[str], limit: int) -> List[Dict[str, Any]]:
    """Get discovery jobs from database."""
    try:
        # This would query your discovery jobs table
        jobs = [
            {
                "id": 1,
                "name": "Network Scan 192.168.1.0/24",
                "target_range": "192.168.1.0/24",
                "discovery_method": "ping_sweep",
                "status": "completed",
                "devices_found": 15,
                "created_at": get_utc_timestamp(),
                "completed_at": get_utc_timestamp()
            }
        ]
        
        if status_filter:
            jobs = [j for j in jobs if j["status"] == status_filter]
        
        return jobs[:limit]
    except Exception:
        return []


async def get_discovery_job_by_id(db: Session, job_id: int, include_results: bool) -> Optional[Dict[str, Any]]:
    """Get discovery job by ID."""
    try:
        # This would query your discovery jobs table
        if job_id == 1:
            job = {
                "id": 1,
                "name": "Network Scan 192.168.1.0/24",
                "target_range": "192.168.1.0/24",
                "discovery_method": "ping_sweep",
                "status": "completed",
                "devices_found": 15,
                "created_at": get_utc_timestamp(),
                "completed_at": get_utc_timestamp()
            }
            
            if include_results:
                job["results"] = await get_discovery_results(db, job_id)
            
            return job
        return None
    except Exception:
        return None


async def stop_discovery_job(db: Session, job_id: int, user_id: int) -> Dict[str, Any]:
    """Stop a running discovery job."""
    try:
        # This would stop the actual discovery job
        return {
            "job_id": job_id,
            "status": "stopped",
            "stopped_at": get_utc_timestamp(),
            "stopped_by": user_id
        }
    except Exception:
        raise


async def delete_discovery_job(db: Session, job_id: int, user_id: int) -> bool:
    """Delete a discovery job."""
    try:
        # This would delete from your discovery jobs table
        return True
    except Exception:
        return False


async def get_discovered_devices_list(db: Session, scan_id: Optional[int], device_type: Optional[str], 
                                    status: Optional[str], search: Optional[str], 
                                    skip: int, limit: int) -> List[Dict[str, Any]]:
    """Get discovered devices with filtering."""
    try:
        # This would query your discovered devices table
        devices = [
            {
                "id": 1,
                "scan_id": 1,
                "hostname": "router.local",
                "ip_address": "192.168.1.1",
                "mac_address": "00:11:22:33:44:55",
                "device_type": "router",
                "vendor": "Cisco",
                "model": "ISR4321",
                "status": "discovered",
                "services": ["ssh", "http", "snmp"],
                "discovered_at": get_utc_timestamp()
            }
        ]
        
        # Apply filters
        if scan_id:
            devices = [d for d in devices if d["scan_id"] == scan_id]
        if device_type:
            devices = [d for d in devices if d["device_type"] == device_type]
        if status:
            devices = [d for d in devices if d["status"] == status]
        if search:
            devices = [d for d in devices if search.lower() in d["hostname"].lower() or search in d["ip_address"]]
        
        return devices[skip:skip+limit]
    except Exception:
        return []


async def get_discovered_device_by_id(db: Session, device_id: int) -> Optional[Dict[str, Any]]:
    """Get discovered device by ID."""
    try:
        # This would query your discovered devices table
        if device_id == 1:
            return {
                "id": 1,
                "scan_id": 1,
                "hostname": "router.local",
                "ip_address": "192.168.1.1",
                "mac_address": "00:11:22:33:44:55",
                "device_type": "router",
                "vendor": "Cisco",
                "model": "ISR4321",
                "status": "discovered",
                "services": ["ssh", "http", "snmp"],
                "discovered_at": get_utc_timestamp(),
                "details": {
                    "os": "IOS XE",
                    "version": "16.09.04",
                    "uptime": "45 days",
                    "interfaces": ["GigabitEthernet0/0/0", "GigabitEthernet0/0/1"]
                }
            }
        return None
    except Exception:
        return None


async def import_device_as_target(db: Session, device_id: int, config: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Import discovered device as managed target."""
    try:
        # This would create a new target from discovered device
        target_id = 999  # Mock ID
        return {
            "id": target_id,
            "hostname": "router.local",
            "ip_address": "192.168.1.1",
            "device_type": "router",
            "status": "imported",
            "imported_at": get_utc_timestamp(),
            "imported_by": user_id
        }
    except Exception:
        raise


async def get_discovery_results(db: Session, job_id: int) -> List[Dict[str, Any]]:
    """Get discovery results for a job."""
    try:
        # This would query discovery results
        return [
            {
                "device_id": 1,
                "hostname": "router.local",
                "ip_address": "192.168.1.1",
                "status": "discovered"
            }
        ]
    except Exception:
        return []


async def get_discovery_analytics_data(db: Session, since: datetime) -> Dict[str, Any]:
    """Get discovery analytics data."""
    try:
        # This would calculate analytics from your data
        return {
            "total_scans": 10,
            "devices_discovered": 150,
            "devices_imported": 120,
            "success_rate": 95.5,
            "by_device_type": {
                "router": 25,
                "switch": 45,
                "server": 50,
                "workstation": 30
            },
            "by_vendor": {
                "Cisco": 70,
                "HP": 30,
                "Dell": 25,
                "Other": 25
            }
        }
    except Exception:
        return {}


async def get_discovery_trends_data(db: Session, metric: str, time_range: str) -> Dict[str, Any]:
    """Get discovery trends data."""
    try:
        # This would calculate trends from your data
        return {
            "data_points": [
                {"date": "2024-01-01", "value": 10},
                {"date": "2024-01-02", "value": 15},
                {"date": "2024-01-03", "value": 12}
            ],
            "trend": "increasing",
            "change_percentage": 15.5
        }
    except Exception:
        return {}


async def get_available_discovery_methods() -> List[Dict[str, Any]]:
    """Get available discovery methods."""
    try:
        return [
            {
                "name": "ping_sweep",
                "display_name": "Ping Sweep",
                "description": "Basic ping-based network discovery",
                "parameters": [
                    {"name": "target_range", "type": "string", "required": True, "description": "Network range (CIDR)"},
                    {"name": "timeout", "type": "integer", "default": 5, "description": "Ping timeout in seconds"}
                ]
            },
            {
                "name": "port_scan",
                "display_name": "Port Scan",
                "description": "TCP port scanning for service discovery",
                "parameters": [
                    {"name": "target_range", "type": "string", "required": True, "description": "Network range (CIDR)"},
                    {"name": "ports", "type": "string", "default": "22,80,443,8080", "description": "Comma-separated port list"}
                ]
            },
            {
                "name": "snmp_walk",
                "display_name": "SNMP Walk",
                "description": "SNMP-based device discovery",
                "parameters": [
                    {"name": "target_range", "type": "string", "required": True, "description": "Network range (CIDR)"},
                    {"name": "community", "type": "string", "default": "public", "description": "SNMP community string"}
                ]
            }
        ]
    except Exception:
        return []


async def validate_discovery_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate discovery configuration."""
    try:
        errors = []
        warnings = []
        suggestions = []
        
        # Basic validation
        if not config.get("name"):
            errors.append("Discovery name is required")
        
        if not config.get("target_range"):
            errors.append("Target range is required")
        
        if not config.get("discovery_method"):
            errors.append("Discovery method is required")
        
        # Method-specific validation
        method = config.get("discovery_method")
        if method == "ping_sweep":
            if not config.get("timeout"):
                warnings.append("Using default timeout of 5 seconds")
        elif method == "port_scan":
            if not config.get("ports"):
                warnings.append("Using default ports: 22,80,443,8080")
        elif method == "snmp_walk":
            if not config.get("community"):
                warnings.append("Using default SNMP community 'public'")
        
        # Suggestions
        if config.get("target_range") and "/" not in config["target_range"]:
            suggestions.append("Consider using CIDR notation for target range (e.g., 192.168.1.0/24)")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }
    except Exception:
        return {"is_valid": False, "errors": ["Validation failed"], "warnings": [], "suggestions": []}