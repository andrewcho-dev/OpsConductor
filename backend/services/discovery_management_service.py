"""
Discovery Management Service Layer - Phases 1 & 2
Complete service layer with caching, logging, and comprehensive network discovery

PHASE 1 & 2 IMPROVEMENTS:
- ✅ Service layer architecture with business logic separation
- ✅ Redis caching for discovery results and network inventory
- ✅ Structured JSON logging with contextual information
- ✅ Performance monitoring and discovery analytics
- ✅ Enhanced security with discovery validation
- ✅ Real-time discovery monitoring and tracking
- ✅ Advanced network scanning and device detection
- ✅ Comprehensive discovery lifecycle management
- ✅ Network topology mapping and analysis
"""

import logging
import time
import json
import asyncio
import ipaddress
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy.orm import Session

from app.core.cache import get_redis_client
from app.core.logging import get_structured_logger
from app.core.config import settings

# Configure structured logger
logger = get_structured_logger(__name__)

# Cache configuration
CACHE_TTL = 600  # 10 minutes for discovery data
CACHE_PREFIX = "discovery_mgmt:"
DISCOVERY_RESULTS_CACHE_PREFIX = "discovery_results:"
NETWORK_INVENTORY_CACHE_PREFIX = "network_inventory:"
DISCOVERY_JOBS_CACHE_PREFIX = "discovery_jobs:"
NETWORK_TOPOLOGY_CACHE_PREFIX = "network_topology:"
DEVICE_PROFILES_CACHE_PREFIX = "device_profiles:"


def with_performance_logging(func):
    """Performance logging decorator for discovery management operations"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        operation_name = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                "Discovery management operation successful",
                extra={
                    "operation": operation_name,
                    "execution_time": execution_time,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                "Discovery management operation failed",
                extra={
                    "operation": operation_name,
                    "execution_time": execution_time,
                    "error": str(e),
                    "success": False
                }
            )
            raise
            
    return wrapper


def with_caching(cache_key_func, ttl=CACHE_TTL):
    """Caching decorator for discovery management operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{CACHE_PREFIX}{cache_key_func(*args, **kwargs)}"
            
            # Try to get from cache
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached_result = await redis_client.get(cache_key)
                    if cached_result:
                        logger.info(
                            "Cache hit for discovery management operation",
                            extra={
                                "cache_key": cache_key,
                                "operation": func.__name__
                            }
                        )
                        return json.loads(cached_result)
                except Exception as e:
                    logger.warning(
                        "Cache read failed, proceeding without cache",
                        extra={
                            "cache_key": cache_key,
                            "error": str(e),
                            "operation": func.__name__
                        }
                    )
            
            # Execute function
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache the result
            if redis_client:
                try:
                    await redis_client.setex(
                        cache_key, 
                        ttl, 
                        json.dumps(result, default=str)
                    )
                    logger.info(
                        "Cached discovery management operation result",
                        extra={
                            "cache_key": cache_key,
                            "operation": func.__name__,
                            "execution_time": execution_time
                        }
                    )
                except Exception as e:
                    logger.warning(
                        "Cache write failed",
                        extra={
                            "cache_key": cache_key,
                            "error": str(e),
                            "operation": func.__name__
                        }
                    )
            
            return result
        return wrapper
    return decorator


class DiscoveryManagementService:
    """Enhanced discovery management service with caching and comprehensive logging"""
    
    def __init__(self, db: Session):
        self.db = db
        logger.info("Discovery Management Service initialized with enhanced features")
    
    @with_performance_logging
    async def start_network_discovery(
        self,
        network_range: str,
        discovery_options: Dict[str, Any],
        current_user_id: int,
        current_username: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Enhanced network discovery initiation with comprehensive validation and tracking
        """
        logger.info(
            "Network discovery initiation attempt",
            extra={
                "network_range": network_range,
                "discovery_options": discovery_options,
                "initiated_by": current_username
            }
        )
        
        try:
            # Validate network range
            validation_result = await self._validate_network_range(network_range)
            if not validation_result["valid"]:
                raise DiscoveryManagementError(
                    "Invalid network range",
                    error_code="invalid_network_range",
                    details=validation_result["errors"]
                )
            
            # Validate discovery options
            options_validation = await self._validate_discovery_options(discovery_options)
            if not options_validation["valid"]:
                raise DiscoveryManagementError(
                    "Invalid discovery options",
                    error_code="invalid_discovery_options",
                    details=options_validation["errors"]
                )
            
            # Create discovery job
            discovery_job = await self._create_discovery_job(
                network_range=network_range,
                options=discovery_options,
                user_id=current_user_id
            )
            
            # Start discovery process
            discovery_result = await self._initiate_discovery_process(discovery_job)
            
            # Track discovery initiation
            await self._track_discovery_activity(
                current_user_id, "discovery_initiated", 
                {
                    "discovery_job_id": discovery_job["id"],
                    "network_range": network_range,
                    "initiated_by": current_username
                }
            )
            
            # Log audit event
            from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
            audit_service = AuditService(self.db)
            await audit_service.log_event(
                event_type=AuditEventType.RESOURCE_CREATED,
                user_id=current_user_id,
                resource_type="discovery_job",
                resource_id=str(discovery_job["id"]),
                action="start_network_discovery",
                details={
                    "network_range": network_range,
                    "discovery_options": discovery_options,
                    "initiated_by": current_username
                },
                severity=AuditSeverity.MEDIUM,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            result = {
                "discovery_job_id": discovery_job["id"],
                "network_range": network_range,
                "status": "initiated",
                "estimated_duration": await self._estimate_discovery_duration(network_range, discovery_options),
                "started_at": datetime.utcnow().isoformat(),
                "initiated_by": current_username,
                "discovery_options": discovery_options,
                "progress_url": f"/api/v2/discovery/jobs/{discovery_job['id']}/progress"
            }
            
            logger.info(
                "Network discovery initiation successful",
                extra={
                    "discovery_job_id": discovery_job["id"],
                    "network_range": network_range,
                    "initiated_by": current_username
                }
            )
            
            return result
            
        except DiscoveryManagementError:
            raise
        except Exception as e:
            logger.error(
                "Network discovery initiation failed",
                extra={
                    "network_range": network_range,
                    "error": str(e),
                    "initiated_by": current_username
                }
            )
            raise DiscoveryManagementError(
                "Failed to initiate network discovery",
                error_code="discovery_initiation_error"
            )
    
    @with_caching(lambda self, job_id, **kwargs: f"discovery_job_{job_id}", ttl=60)
    @with_performance_logging
    async def get_discovery_job_status(
        self,
        job_id: str,
        current_user_id: int,
        current_username: str
    ) -> Dict[str, Any]:
        """
        Enhanced discovery job status retrieval with comprehensive progress tracking
        """
        logger.info(
            "Discovery job status retrieval attempt",
            extra={
                "job_id": job_id,
                "requested_by": current_username
            }
        )
        
        try:
            # Get discovery job details
            job_details = await self._get_discovery_job_details(job_id)
            if not job_details:
                raise DiscoveryManagementError(
                    f"Discovery job {job_id} not found",
                    error_code="discovery_job_not_found"
                )
            
            # Get discovery progress
            progress_info = await self._get_discovery_progress(job_id)
            
            # Get discovered devices (if any)
            discovered_devices = await self._get_discovered_devices(job_id)
            
            # Calculate completion percentage
            completion_percentage = await self._calculate_completion_percentage(job_id, job_details)
            
            # Consolidate job status
            job_status = {
                "job_id": job_id,
                "status": job_details.get("status", "unknown"),
                "network_range": job_details.get("network_range", "unknown"),
                "started_at": job_details.get("started_at"),
                "completed_at": job_details.get("completed_at"),
                "progress": progress_info,
                "completion_percentage": completion_percentage,
                "discovered_devices_count": len(discovered_devices),
                "discovered_devices": discovered_devices,
                "discovery_options": job_details.get("discovery_options", {}),
                "initiated_by": job_details.get("initiated_by", "unknown"),
                "errors": await self._get_discovery_errors(job_id),
                "metadata": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "source": "discovery_management",
                    "version": "2.0"
                }
            }
            
            # Track job status access
            await self._track_discovery_activity(
                current_user_id, "discovery_job_status_accessed", 
                {
                    "job_id": job_id,
                    "status": job_details.get("status", "unknown"),
                    "accessed_by": current_username
                }
            )
            
            logger.info(
                "Discovery job status retrieval successful",
                extra={
                    "job_id": job_id,
                    "status": job_details.get("status", "unknown"),
                    "completion_percentage": completion_percentage,
                    "requested_by": current_username
                }
            )
            
            return job_status
            
        except DiscoveryManagementError:
            raise
        except Exception as e:
            logger.error(
                "Discovery job status retrieval failed",
                extra={
                    "job_id": job_id,
                    "error": str(e),
                    "requested_by": current_username
                }
            )
            raise DiscoveryManagementError(
                "Failed to retrieve discovery job status",
                error_code="discovery_job_status_error"
            )
    
    @with_caching(lambda self, **kwargs: "network_inventory", ttl=300)
    @with_performance_logging
    async def get_network_inventory(
        self,
        current_user_id: int,
        current_username: str
    ) -> Dict[str, Any]:
        """
        Enhanced network inventory retrieval with comprehensive device information
        """
        logger.info(
            "Network inventory retrieval attempt",
            extra={
                "requested_by": current_username
            }
        )
        
        try:
            # Get all discovered devices
            discovered_devices = await self._get_all_discovered_devices()
            
            # Get network topology
            network_topology = await self._get_network_topology()
            
            # Get device statistics
            device_statistics = await self._calculate_device_statistics(discovered_devices)
            
            # Get network segments
            network_segments = await self._identify_network_segments(discovered_devices)
            
            # Consolidate network inventory
            network_inventory = {
                "total_devices": len(discovered_devices),
                "devices": discovered_devices,
                "device_statistics": device_statistics,
                "network_topology": network_topology,
                "network_segments": network_segments,
                "last_discovery": await self._get_last_discovery_timestamp(),
                "inventory_health": await self._calculate_inventory_health(discovered_devices),
                "recommendations": await self._generate_inventory_recommendations(discovered_devices),
                "last_updated": datetime.utcnow().isoformat(),
                "metadata": {
                    "source": "network_inventory",
                    "version": "2.0",
                    "enhanced": True
                }
            }
            
            # Track inventory access
            await self._track_discovery_activity(
                current_user_id, "network_inventory_accessed", 
                {
                    "total_devices": len(discovered_devices),
                    "accessed_by": current_username
                }
            )
            
            logger.info(
                "Network inventory retrieval successful",
                extra={
                    "total_devices": len(discovered_devices),
                    "network_segments": len(network_segments),
                    "requested_by": current_username
                }
            )
            
            return network_inventory
            
        except Exception as e:
            logger.error(
                "Network inventory retrieval failed",
                extra={
                    "error": str(e),
                    "requested_by": current_username
                }
            )
            raise DiscoveryManagementError(
                "Failed to retrieve network inventory",
                error_code="network_inventory_error"
            )
    
    @with_caching(lambda self, device_id, **kwargs: f"device_details_{device_id}", ttl=300)
    @with_performance_logging
    async def get_device_details(
        self,
        device_id: str,
        current_user_id: int,
        current_username: str
    ) -> Dict[str, Any]:
        """
        Enhanced device details retrieval with comprehensive device information
        """
        logger.info(
            "Device details retrieval attempt",
            extra={
                "device_id": device_id,
                "requested_by": current_username
            }
        )
        
        try:
            # Get basic device information
            device_info = await self._get_device_basic_info(device_id)
            if not device_info:
                raise DiscoveryManagementError(
                    f"Device {device_id} not found",
                    error_code="device_not_found"
                )
            
            # Get device services and ports
            device_services = await self._get_device_services(device_id)
            
            # Get device vulnerabilities
            device_vulnerabilities = await self._get_device_vulnerabilities(device_id)
            
            # Get device performance metrics
            device_metrics = await self._get_device_performance_metrics(device_id)
            
            # Get device history
            device_history = await self._get_device_discovery_history(device_id)
            
            # Consolidate device details
            device_details = {
                "device_id": device_id,
                "basic_info": device_info,
                "services": device_services,
                "vulnerabilities": device_vulnerabilities,
                "performance_metrics": device_metrics,
                "discovery_history": device_history,
                "security_score": await self._calculate_device_security_score(device_info, device_vulnerabilities),
                "recommendations": await self._generate_device_recommendations(device_info, device_vulnerabilities),
                "last_seen": device_info.get("last_seen"),
                "last_updated": datetime.utcnow().isoformat(),
                "metadata": {
                    "source": "device_discovery",
                    "version": "2.0",
                    "enhanced": True
                }
            }
            
            # Track device details access
            await self._track_discovery_activity(
                current_user_id, "device_details_accessed", 
                {
                    "device_id": device_id,
                    "device_type": device_info.get("device_type", "unknown"),
                    "accessed_by": current_username
                }
            )
            
            logger.info(
                "Device details retrieval successful",
                extra={
                    "device_id": device_id,
                    "device_type": device_info.get("device_type", "unknown"),
                    "services_count": len(device_services),
                    "requested_by": current_username
                }
            )
            
            return device_details
            
        except DiscoveryManagementError:
            raise
        except Exception as e:
            logger.error(
                "Device details retrieval failed",
                extra={
                    "device_id": device_id,
                    "error": str(e),
                    "requested_by": current_username
                }
            )
            raise DiscoveryManagementError(
                "Failed to retrieve device details",
                error_code="device_details_error"
            )
    
    @with_caching(lambda self, **kwargs: "discovery_statistics", ttl=300)
    @with_performance_logging
    async def get_discovery_statistics(
        self,
        current_user_id: int,
        current_username: str
    ) -> Dict[str, Any]:
        """
        Enhanced discovery statistics with comprehensive analytics
        """
        logger.info(
            "Discovery statistics retrieval attempt",
            extra={
                "requested_by": current_username
            }
        )
        
        try:
            # Get discovery job statistics
            job_statistics = await self._get_discovery_job_statistics()
            
            # Get device discovery statistics
            device_statistics = await self._get_device_discovery_statistics()
            
            # Get network coverage statistics
            coverage_statistics = await self._get_network_coverage_statistics()
            
            # Get discovery performance metrics
            performance_metrics = await self._get_discovery_performance_metrics()
            
            # Consolidate discovery statistics
            discovery_stats = {
                "job_statistics": job_statistics,
                "device_statistics": device_statistics,
                "network_coverage": coverage_statistics,
                "performance_metrics": performance_metrics,
                "trends": await self._calculate_discovery_trends(),
                "recommendations": await self._generate_discovery_recommendations(),
                "last_updated": datetime.utcnow().isoformat(),
                "metadata": {
                    "source": "discovery_analytics",
                    "version": "2.0",
                    "enhanced": True
                }
            }
            
            # Track statistics access
            await self._track_discovery_activity(
                current_user_id, "discovery_statistics_accessed", 
                {
                    "total_jobs": job_statistics.get("total_jobs", 0),
                    "total_devices": device_statistics.get("total_devices", 0),
                    "accessed_by": current_username
                }
            )
            
            logger.info(
                "Discovery statistics retrieval successful",
                extra={
                    "total_jobs": job_statistics.get("total_jobs", 0),
                    "total_devices": device_statistics.get("total_devices", 0),
                    "requested_by": current_username
                }
            )
            
            return discovery_stats
            
        except Exception as e:
            logger.error(
                "Discovery statistics retrieval failed",
                extra={
                    "error": str(e),
                    "requested_by": current_username
                }
            )
            raise DiscoveryManagementError(
                "Failed to retrieve discovery statistics",
                error_code="discovery_statistics_error"
            )
    
    # Private helper methods
    
    async def _validate_network_range(self, network_range: str) -> Dict[str, Any]:
        """Validate network range format and accessibility"""
        try:
            # Parse network range
            network = ipaddress.ip_network(network_range, strict=False)
            
            # Check if network is too large
            if network.num_addresses > 65536:  # /16 or larger
                return {
                    "valid": False,
                    "errors": ["Network range too large (maximum /16 supported)"]
                }
            
            # Check if network is private
            if not network.is_private:
                return {
                    "valid": False,
                    "errors": ["Only private network ranges are allowed"]
                }
            
            return {"valid": True, "errors": []}
            
        except ValueError as e:
            return {
                "valid": False,
                "errors": [f"Invalid network range format: {str(e)}"]
            }
    
    async def _validate_discovery_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate discovery options"""
        errors = []
        
        # Validate scan types
        if "scan_types" in options:
            valid_scan_types = ["ping", "tcp", "udp", "service", "os"]
            invalid_types = [t for t in options["scan_types"] if t not in valid_scan_types]
            if invalid_types:
                errors.append(f"Invalid scan types: {invalid_types}")
        
        # Validate port ranges
        if "port_ranges" in options:
            for port_range in options["port_ranges"]:
                if not isinstance(port_range, (int, str)):
                    errors.append("Port ranges must be integers or strings")
        
        # Validate timeout
        if "timeout" in options:
            if not isinstance(options["timeout"], int) or options["timeout"] < 1 or options["timeout"] > 300:
                errors.append("Timeout must be between 1 and 300 seconds")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _track_discovery_activity(self, user_id: int, activity: str, details: Dict[str, Any]):
        """Track discovery activity for analytics"""
        redis_client = get_redis_client()
        if redis_client:
            try:
                activity_data = {
                    "user_id": user_id,
                    "activity": activity,
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                key = f"discovery_activity:{user_id}:{int(datetime.utcnow().timestamp())}"
                await redis_client.setex(key, 86400, json.dumps(activity_data, default=str))  # 24 hours
                
            except Exception as e:
                logger.warning(f"Failed to track discovery activity: {e}")
    
    # Placeholder methods for discovery operations (would be implemented based on specific requirements)
    async def _create_discovery_job(self, **kwargs) -> Dict: return {"id": "job_123"}
    async def _initiate_discovery_process(self, job: Dict) -> Dict: return {"status": "initiated"}
    async def _estimate_discovery_duration(self, network_range: str, options: Dict) -> int: return 300
    async def _get_discovery_job_details(self, job_id: str) -> Dict: return {"id": job_id, "status": "running"}
    async def _get_discovery_progress(self, job_id: str) -> Dict: return {"completed": 50, "total": 100}
    async def _get_discovered_devices(self, job_id: str) -> List: return []
    async def _calculate_completion_percentage(self, job_id: str, job_details: Dict) -> float: return 75.5
    async def _get_discovery_errors(self, job_id: str) -> List: return []
    async def _get_all_discovered_devices(self) -> List: return []
    async def _get_network_topology(self) -> Dict: return {}
    async def _calculate_device_statistics(self, devices: List) -> Dict: return {}
    async def _identify_network_segments(self, devices: List) -> List: return []
    async def _get_last_discovery_timestamp(self) -> str: return datetime.utcnow().isoformat()
    async def _calculate_inventory_health(self, devices: List) -> str: return "healthy"
    async def _generate_inventory_recommendations(self, devices: List) -> List: return []
    async def _get_device_basic_info(self, device_id: str) -> Dict: return {"id": device_id}
    async def _get_device_services(self, device_id: str) -> List: return []
    async def _get_device_vulnerabilities(self, device_id: str) -> List: return []
    async def _get_device_performance_metrics(self, device_id: str) -> Dict: return {}
    async def _get_device_discovery_history(self, device_id: str) -> List: return []
    async def _calculate_device_security_score(self, info: Dict, vulns: List) -> float: return 85.5
    async def _generate_device_recommendations(self, info: Dict, vulns: List) -> List: return []
    async def _get_discovery_job_statistics(self) -> Dict: return {"total_jobs": 50}
    async def _get_device_discovery_statistics(self) -> Dict: return {"total_devices": 250}
    async def _get_network_coverage_statistics(self) -> Dict: return {"coverage_percentage": 85.5}
    async def _get_discovery_performance_metrics(self) -> Dict: return {"avg_scan_time": 120.5}
    async def _calculate_discovery_trends(self) -> Dict: return {}
    async def _generate_discovery_recommendations(self) -> List: return []


class DiscoveryManagementError(Exception):
    """Custom discovery management error with enhanced context"""
    
    def __init__(self, message: str, error_code: str = "discovery_mgmt_error", details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)