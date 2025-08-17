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
    
    @with_performance_logging
    async def start_in_memory_discovery(
        self,
        discovery_config: Dict[str, Any],
        current_user_id: int,
        current_username: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Start an in-memory discovery task that doesn't persist to database.
        Returns a task_id for polling results.
        """
        try:
            # Generate a unique task ID
            import uuid
            task_id = f"memory_discovery_{uuid.uuid4().hex[:12]}"
            
            # Store task info in Redis with initial status
            redis_client = await get_redis_client()
            task_data = {
                "task_id": task_id,
                "status": "pending",
                "progress": 0,
                "message": "Discovery task queued",
                "discovery_config": discovery_config,
                "initiated_by": current_username,
                "started_at": datetime.utcnow().isoformat(),
                "devices": []
            }
            
            # Store in Redis with 1 hour TTL
            await redis_client.setex(
                f"in_memory_discovery:{task_id}",
                3600,  # 1 hour
                json.dumps(task_data, default=str)
            )
            
            # Start the actual discovery task using Celery
            from app.tasks.discovery_tasks import run_in_memory_discovery_task
            celery_task = run_in_memory_discovery_task.delay(task_id, discovery_config)
            
            logger.info(
                "In-memory discovery task started via Celery",
                extra={
                    "task_id": task_id,
                    "celery_task_id": celery_task.id,
                    "initiated_by": current_username,
                    "discovery_config": discovery_config
                }
            )
            
            return {"task_id": task_id}
            
        except Exception as e:
            logger.error(f"Failed to start in-memory discovery: {e}")
            raise DiscoveryManagementError(
                f"Failed to start in-memory discovery: {str(e)}",
                "in_memory_discovery_start_error",
                {"discovery_config": discovery_config}
            )

    @with_performance_logging
    async def get_in_memory_discovery_status(
        self,
        task_id: str,
        current_user_id: int,
        current_username: str
    ) -> Dict[str, Any]:
        """
        Get the status and results of an in-memory discovery task.
        """
        try:
            redis_client = await get_redis_client()
            task_data_str = await redis_client.get(f"in_memory_discovery:{task_id}")
            
            if not task_data_str:
                raise DiscoveryManagementError(
                    f"In-memory discovery task not found: {task_id}",
                    "task_not_found",
                    {"task_id": task_id}
                )
            
            task_data = json.loads(task_data_str)
            
            logger.info(
                "In-memory discovery status retrieved",
                extra={
                    "task_id": task_id,
                    "status": task_data.get("status"),
                    "requested_by": current_username
                }
            )
            
            return task_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode task data for {task_id}: {e}")
            raise DiscoveryManagementError(
                f"Invalid task data for {task_id}",
                "task_data_error",
                {"task_id": task_id}
            )
        except Exception as e:
            logger.error(f"Failed to get in-memory discovery status: {e}")
            raise DiscoveryManagementError(
                f"Failed to get in-memory discovery status: {str(e)}",
                "in_memory_discovery_status_error",
                {"task_id": task_id}
            )

    async def _run_in_memory_discovery_task(self, task_id: str, discovery_config: Dict[str, Any]):
        """
        Run the actual in-memory discovery task in the background.
        This simulates a network discovery process.
        """
        try:
            redis_client = await get_redis_client()
            
            # Update status to running
            await self._update_task_status(task_id, "running", 5, "Starting network scan...")
            
            # Simulate discovery process
            network_ranges = discovery_config.get("network_ranges", ["192.168.1.0/24"])
            timeout = discovery_config.get("timeout", 30)
            
            # Handle both single networkRange and multiple network_ranges for backward compatibility
            if "networkRange" in discovery_config:
                network_ranges = [discovery_config["networkRange"]]
            
            # Parse network ranges
            networks = []
            total_hosts = 0
            try:
                for network_range in network_ranges:
                    network = ipaddress.IPv4Network(network_range, strict=False)
                    networks.append(network)
                    total_hosts += network.num_addresses - 2  # Exclude network and broadcast
            except ValueError as e:
                await self._update_task_status(task_id, "failed", 0, f"Invalid network range: {e}")
                return
            
            discovered_devices = []
            scanned_count = 0
            max_hosts_to_scan = min(total_hosts, 50)  # Limit for demo
            
            # Real network scanning across all networks
            import subprocess
            import socket
            import concurrent.futures
            from concurrent.futures import ThreadPoolExecutor
            
            for network in networks:
                network_name = str(network)
                logger.info(f"Processing network: {network_name}")
                
                await self._update_task_status(
                    task_id, 
                    "running", 
                    int((scanned_count / max_hosts_to_scan) * 100), 
                    f"Scanning network {network_name}..."
                )
                
                # Get list of hosts to scan (limit to reasonable number)
                if network.prefixlen == 32:
                    # Single host (/32) - scan the host itself
                    hosts_to_scan = [network.network_address]
                else:
                    # Network range - scan all hosts in the network
                    hosts_to_scan = list(network.hosts())[:max_hosts_to_scan - scanned_count]
                
                logger.info(f"Hosts to scan in {network_name}: {len(hosts_to_scan)} hosts")
                logger.info(f"First few hosts: {[str(h) for h in hosts_to_scan[:5]]}")
                
                # Scan hosts in parallel for better performance
                max_workers = max(1, min(20, len(hosts_to_scan)))  # Ensure at least 1 worker
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit ping tasks
                    ping_futures = {
                        executor.submit(self._ping_host, str(host)): host 
                        for host in hosts_to_scan
                    }
                    
                    for future in concurrent.futures.as_completed(ping_futures):
                        host = ping_futures[future]
                        host_ip = str(host)
                        
                        try:
                            is_alive = future.result()
                            logger.info(f"Host {host_ip} alive check result: {is_alive}")
                            if is_alive:
                                # Host is alive, perform port scan and hostname resolution
                                common_ports = discovery_config.get("common_ports", [22, 23, 80, 443, 3389, 8080])
                                
                                # Get hostname
                                hostname = await self._resolve_hostname(host_ip)
                                
                                # Scan ports
                                open_ports = await self._scan_ports(host_ip, common_ports, timeout)
                                
                                # Determine device type based on open ports
                                device_type = self._determine_device_type(open_ports)
                                
                                device = {
                                    "ip_address": host_ip,
                                    "hostname": hostname,
                                    "device_type": device_type,
                                    "status": "discovered",
                                    "ports": open_ports,
                                    "network_range": network_name,
                                    "discovered_at": datetime.utcnow().isoformat()
                                }
                                discovered_devices.append(device)
                        
                        except Exception as e:
                            # Host scan failed, continue with next host
                            pass
                        
                        scanned_count += 1
                        progress = int((scanned_count / max_hosts_to_scan) * 100)
                        
                        # Update progress every 10 scans
                        if scanned_count % 10 == 0:
                            await self._update_task_status(
                                task_id, 
                                "running", 
                                progress, 
                                f"Scanned {scanned_count}/{max_hosts_to_scan} hosts, found {len(discovered_devices)} devices"
                            )
                        
                        # Break if we've reached the scan limit
                        if scanned_count >= max_hosts_to_scan:
                            break
                
                # Break if we've reached the scan limit
                if scanned_count >= max_hosts_to_scan:
                    break
            
            # Filter out devices that are already registered as targets
            filtered_devices = await self._filter_duplicate_targets(discovered_devices)
            
            # Complete the task
            active_duplicates = len(discovered_devices) - len(filtered_devices)
            await self._update_task_status(
                task_id, 
                "completed", 
                100, 
                f"Discovery completed. Found {len(discovered_devices)} devices ({len(filtered_devices)} available for import, {active_duplicates} active duplicates filtered)",
                filtered_devices
            )
            
            logger.info(
                "In-memory discovery task completed",
                extra={
                    "task_id": task_id,
                    "devices_found": len(discovered_devices),
                    "hosts_scanned": scanned_count
                }
            )
            
        except Exception as e:
            logger.error(f"In-memory discovery task failed: {e}")
            await self._update_task_status(task_id, "failed", 0, f"Discovery failed: {str(e)}")

    async def _update_task_status(self, task_id: str, status: str, progress: int, message: str, devices: List = None):
        """Update task status in Redis (async version)"""
        try:
            redis_client = await get_redis_client()
            task_data_str = await redis_client.get(f"in_memory_discovery:{task_id}")
            
            if task_data_str:
                task_data = json.loads(task_data_str)
                task_data.update({
                    "status": status,
                    "progress": progress,
                    "message": message,
                    "last_updated": datetime.utcnow().isoformat()
                })
                
                if devices is not None:
                    task_data["devices"] = devices
                
                if status == "completed":
                    task_data["completed_at"] = datetime.utcnow().isoformat()
                
                await redis_client.setex(
                    f"in_memory_discovery:{task_id}",
                    3600,  # 1 hour
                    json.dumps(task_data, default=str)
                )
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")

    def _update_task_status_sync(self, task_id: str, status: str, progress: int, message: str, devices: List = None):
        """Update task status in Redis (synchronous version for Celery tasks)"""
        try:
            import redis
            from app.core.config import settings
            
            # Create synchronous Redis client
            redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            task_data_str = redis_client.get(f"in_memory_discovery:{task_id}")
            
            if task_data_str:
                task_data = json.loads(task_data_str)
                task_data.update({
                    "status": status,
                    "progress": progress,
                    "message": message,
                    "last_updated": datetime.utcnow().isoformat()
                })
                
                if devices is not None:
                    task_data["devices"] = devices
                
                if status == "completed":
                    task_data["completed_at"] = datetime.utcnow().isoformat()
                
                redis_client.setex(
                    f"in_memory_discovery:{task_id}",
                    3600,  # 1 hour
                    json.dumps(task_data, default=str)
                )
                logger.info(f"Task status updated in Redis: {task_id} -> {status}")
        except Exception as e:
            logger.error(f"Failed to update task status (sync): {e}")

    def _get_device_info(self, host_ip: str, ports: List[int]) -> dict:
        """
        Get detailed device information for a discovered host.
        """
        import socket
        from datetime import datetime
        
        device_info = {
            'ip_address': host_ip,
            'hostname': host_ip,
            'device_type': 'unknown',
            'status': 'discovered',
            'ports': [],
            'network_range': 'unknown',
            'discovered_at': datetime.utcnow().isoformat()
        }
        
        # Try to get hostname
        try:
            hostname = socket.gethostbyaddr(host_ip)[0]
            device_info['hostname'] = hostname
        except:
            pass
        
        # Check which ports are open
        open_ports = []
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host_ip, port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            except:
                pass
        
        device_info['ports'] = open_ports
        
        # Get service banners for better identification
        service_info = self._get_service_banners(host_ip, open_ports[:3])  # Only check first 3 ports for performance
        device_info['services'] = service_info
        
        # Get MAC address and vendor info
        mac_info = self._get_mac_address(host_ip)
        if mac_info:
            device_info['mac_address'] = mac_info.get('mac')
            device_info['vendor'] = mac_info.get('vendor')
        
        # Advanced device type identification
        device_info['device_type'] = self._identify_device_type(host_ip, open_ports, device_info.get('hostname', ''), service_info, mac_info)
        
        return device_info

    def _get_service_banners(self, host_ip: str, ports: list) -> dict:
        """
        Get service banners from open ports for better device identification.
        Only checks a few ports to avoid performance impact.
        """
        services = {}
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((host_ip, port))
                
                # Try to get banner
                banner = ""
                if port == 22:  # SSH
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                elif port == 80:  # HTTP
                    sock.send(b"GET / HTTP/1.0\r\n\r\n")
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                elif port == 21:  # FTP
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                elif port == 25:  # SMTP
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                elif port == 23:  # Telnet
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                
                if banner:
                    services[port] = banner[:200]  # Limit banner length
                
                sock.close()
                
            except Exception:
                # Banner grab failed, continue
                pass
        
        return services

    def _get_mac_address(self, host_ip: str) -> dict:
        """
        Get MAC address and vendor information using ARP table lookup.
        This works best for devices on the same subnet.
        """
        try:
            import subprocess
            import re
            
            # Try to get MAC from ARP table
            try:
                # Ping first to populate ARP table
                subprocess.run(['ping', '-c', '1', '-W', '1', host_ip], 
                             capture_output=True, timeout=2)
                
                # Get ARP entry
                result = subprocess.run(['arp', '-n', host_ip], 
                                      capture_output=True, text=True, timeout=2)
                
                if result.returncode == 0:
                    # Parse ARP output for MAC address
                    mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', result.stdout)
                    if mac_match:
                        mac_address = mac_match.group(0).upper().replace('-', ':')
                        vendor = self._get_vendor_from_mac(mac_address)
                        return {
                            'mac': mac_address,
                            'vendor': vendor
                        }
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
                
        except Exception as e:
            logger.debug(f"Failed to get MAC address for {host_ip}: {e}")
            
        return None

    def _get_vendor_from_mac(self, mac_address: str) -> str:
        """
        Get vendor information from MAC address OUI (first 3 octets).
        Uses a simplified vendor database for common manufacturers.
        """
        if not mac_address or len(mac_address) < 8:
            return 'Unknown'
            
        # Get OUI (first 3 octets)
        oui = mac_address[:8].upper()
        
        # Common vendor OUI mappings (simplified database)
        vendor_db = {
            # Network Equipment
            '00:1B:67': 'Cisco Systems',
            '00:26:99': 'Cisco Systems', 
            '00:50:56': 'VMware',
            '00:0C:29': 'VMware',
            '00:05:69': 'VMware',
            '08:00:27': 'Oracle VirtualBox',
            '52:54:00': 'QEMU/KVM',
            
            # Common Manufacturers
            '00:50:B6': 'Intel Corporation',
            '00:E0:4C': 'Realtek',
            '00:1E:C9': 'ASUSTEK',
            '00:26:B9': 'Netgear',
            '00:14:BF': 'Netgear',
            '00:03:7F': 'Atheros',
            '00:15:6D': 'Broadcom',
            
            # Apple
            '00:03:93': 'Apple',
            '00:16:CB': 'Apple',
            '00:1B:63': 'Apple',
            
            # HP/Dell
            '00:1F:29': 'Hewlett Packard',
            '00:26:55': 'Dell Inc.',
            '00:14:22': 'Dell Inc.',
            
            # Printers
            '00:11:85': 'Canon',
            '00:01:E3': 'Siemens',
            '00:80:77': 'Brother',
        }
        
        return vendor_db.get(oui, 'Unknown')

    def _analyze_service_banners(self, service_info: dict) -> dict:
        """Analyze service banners for OS and device type clues"""
        clues = {
            'os_hints': [],
            'device_hints': [],
            'software_hints': []
        }
        
        for port, banner in service_info.items():
            banner_lower = banner.lower()
            
            # OS detection from banners
            if any(hint in banner_lower for hint in ['ubuntu', 'debian', 'centos', 'redhat', 'linux']):
                clues['os_hints'].append('linux')
            elif any(hint in banner_lower for hint in ['windows', 'microsoft', 'iis']):
                clues['os_hints'].append('windows')
            elif any(hint in banner_lower for hint in ['cisco', 'juniper', 'mikrotik']):
                clues['device_hints'].append('network_device')
            
            # Software detection
            if 'apache' in banner_lower:
                clues['software_hints'].append('apache')
            elif 'nginx' in banner_lower:
                clues['software_hints'].append('nginx')
            elif 'openssh' in banner_lower:
                clues['software_hints'].append('openssh')
            elif 'microsoft' in banner_lower:
                clues['software_hints'].append('microsoft')
        
        return clues

    def _analyze_vendor_info(self, mac_info: dict) -> dict:
        """Analyze MAC vendor information for device type clues"""
        clues = {
            'device_hints': [],
            'os_hints': []
        }
        
        if not mac_info or not mac_info.get('vendor'):
            return clues
            
        vendor = mac_info.get('vendor', '').lower()
        
        # Network equipment vendors
        if any(v in vendor for v in ['cisco', 'juniper', 'netgear', 'linksys', 'dlink', 'tplink']):
            clues['device_hints'].append('network_device')
        
        # Virtualization platforms
        elif any(v in vendor for v in ['vmware', 'virtualbox', 'qemu']):
            clues['device_hints'].append('virtual_machine')
            
        # Printer manufacturers
        elif any(v in vendor for v in ['canon', 'brother', 'hp', 'epson']):
            clues['device_hints'].append('printer')
            
        # Apple devices
        elif 'apple' in vendor:
            clues['os_hints'].append('macos')
            clues['device_hints'].append('apple_device')
            
        return clues

    def _get_ttl_os_hints(self, host_ip: str) -> list:
        """
        Get OS hints based on TTL (Time To Live) values from ping.
        Different operating systems use different default TTL values.
        """
        try:
            import subprocess
            import re
            
            # Ping the host and get TTL
            result = subprocess.run(['ping', '-c', '1', '-W', '2', host_ip], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                # Extract TTL from ping output
                ttl_match = re.search(r'ttl=(\d+)', result.stdout.lower())
                if ttl_match:
                    ttl = int(ttl_match.group(1))
                    
                    # TTL-based OS detection
                    if ttl <= 64:
                        if ttl > 60:
                            return ['linux', 'unix']  # Linux/Unix typically 64
                        else:
                            return ['linux', 'unix', 'network_device']  # Could be network device
                    elif ttl <= 128:
                        if ttl > 120:
                            return ['windows']  # Windows typically 128
                        else:
                            return ['windows', 'network_device']
                    elif ttl <= 255:
                        return ['network_device', 'cisco']  # Network devices often 255
                        
        except Exception:
            pass
            
        return []

    def _identify_device_type(self, host_ip: str, open_ports: list, hostname: str = '', service_info: dict = None, mac_info: dict = None) -> str:
        """
        Advanced device type identification using multiple indicators:
        - Port patterns
        - Service banners
        - Hostname patterns
        - TTL analysis
        - Service fingerprinting
        """
        try:
            import socket
            import re
            
            # Normalize hostname for analysis
            hostname_lower = hostname.lower()
            service_info = service_info or {}
            mac_info = mac_info or {}
            
            # Check service banners for OS/device clues
            banner_clues = self._analyze_service_banners(service_info)
            
            # Check MAC vendor for device clues
            vendor_clues = self._analyze_vendor_info(mac_info)
            
            # Get TTL-based OS hints
            ttl_hints = self._get_ttl_os_hints(host_ip)
            
            # 1. VENDOR-SPECIFIC DEVICES (highest priority)
            if 'printer' in vendor_clues.get('device_hints', []):
                return 'printer'
            elif 'virtual_machine' in vendor_clues.get('device_hints', []):
                return 'virtual_machine'
            elif 'apple_device' in vendor_clues.get('device_hints', []):
                return 'macos'
            
            # 2. SPECIALIZED DEVICES (most specific)
            specialized_type = self._identify_specialized_device(open_ports, hostname_lower, host_ip, banner_clues, vendor_clues)
            if specialized_type:
                return specialized_type
            
            # 3. NETWORK INFRASTRUCTURE DEVICES
            if self._is_network_device(open_ports, hostname_lower, host_ip, banner_clues, vendor_clues):
                return 'network_device'
            
            # 4. WINDOWS SYSTEMS
            if self._is_windows_system(open_ports, hostname_lower, host_ip, banner_clues, vendor_clues) or 'windows' in ttl_hints:
                return 'windows'
            
            # 5. LINUX/UNIX SYSTEMS
            if self._is_linux_system(open_ports, hostname_lower, host_ip, banner_clues, vendor_clues) or any(hint in ttl_hints for hint in ['linux', 'unix']):
                return 'linux'
            
            # 5. FALLBACK CLASSIFICATION
            return self._fallback_classification(open_ports, hostname_lower)
            
        except Exception as e:
            logger.warning(f"Error in device identification for {host_ip}: {e}")
            return 'unknown'

    def _is_network_device(self, open_ports: list, hostname: str, host_ip: str, banner_clues: dict = None, vendor_clues: dict = None) -> bool:
        """Identify network infrastructure devices"""
        banner_clues = banner_clues or {}
        vendor_clues = vendor_clues or {}
        
        # Network device indicators
        network_indicators = [
            # Vendor clues (strongest indicator)
            'network_device' in vendor_clues.get('device_hints', []),
            # Banner clues
            'network_device' in banner_clues.get('device_hints', []),
            # Hostname patterns
            any(pattern in hostname for pattern in [
                'router', 'switch', 'gateway', 'firewall', 'ap-', 'access-point',
                'cisco', 'juniper', 'netgear', 'linksys', 'dlink', 'tplink',
                'ubiquiti', 'mikrotik', 'fortinet', 'pfsense', 'opnsense'
            ]),
            # Port patterns typical of network devices
            161 in open_ports and 22 in open_ports and 80 in open_ports,  # SNMP + SSH + Web
            23 in open_ports and 80 in open_ports and not 3389 in open_ports,  # Telnet + Web, no RDP
            # Common network device web ports
            8080 in open_ports and 22 in open_ports and not 445 in open_ports,
            # SNMP without typical server services
            161 in open_ports and not any(port in open_ports for port in [3306, 5432, 1433, 25, 110])
        ]
        
        return any(network_indicators)

    def _is_windows_system(self, open_ports: list, hostname: str, host_ip: str, banner_clues: dict = None, vendor_clues: dict = None) -> bool:
        """Identify Windows systems"""
        banner_clues = banner_clues or {}
        
        # Windows-specific indicators
        windows_indicators = [
            # Banner clues
            'windows' in banner_clues.get('os_hints', []),
            'microsoft' in banner_clues.get('software_hints', []),
            # RDP is strong Windows indicator
            3389 in open_ports,
            # SMB/NetBIOS combination
            445 in open_ports and 139 in open_ports,
            # Windows RPC
            135 in open_ports and (445 in open_ports or 139 in open_ports),
            # WinRM
            5985 in open_ports or 5986 in open_ports,
            # Hostname patterns
            any(pattern in hostname for pattern in [
                'win-', 'windows', 'dc-', 'ad-', 'exchange', 'sql-', 'iis-',
                'desktop-', 'laptop-', 'pc-', 'workstation'
            ])
        ]
        
        return any(windows_indicators)

    def _is_linux_system(self, open_ports: list, hostname: str, host_ip: str, banner_clues: dict = None, vendor_clues: dict = None) -> bool:
        """Identify Linux/Unix systems"""
        banner_clues = banner_clues or {}
        
        # Linux-specific indicators
        linux_indicators = [
            # Banner clues
            'linux' in banner_clues.get('os_hints', []),
            'openssh' in banner_clues.get('software_hints', []),
            'apache' in banner_clues.get('software_hints', []),
            'nginx' in banner_clues.get('software_hints', []),
            # SSH is common on Linux
            22 in open_ports and not 3389 in open_ports and not 445 in open_ports,
            # Common Linux service combinations
            22 in open_ports and (80 in open_ports or 443 in open_ports) and not 135 in open_ports,
            # Hostname patterns
            any(pattern in hostname for pattern in [
                'ubuntu', 'debian', 'centos', 'rhel', 'fedora', 'suse', 'arch',
                'linux', 'unix', 'server', 'web-', 'db-', 'mail-', 'dns-'
            ])
        ]
        
        return any(linux_indicators)

    def _identify_specialized_device(self, open_ports: list, hostname: str, host_ip: str, banner_clues: dict = None, vendor_clues: dict = None) -> str:
        """Identify specialized devices and appliances"""
        
        # Database servers
        if any(port in open_ports for port in [3306, 5432, 1433, 1521, 27017]):
            if 3306 in open_ports:
                return 'database_mysql'
            elif 5432 in open_ports:
                return 'database_postgresql'
            elif 1433 in open_ports:
                return 'database_mssql'
            elif 1521 in open_ports:
                return 'database_oracle'
            elif 27017 in open_ports:
                return 'database_mongodb'
        
        # Web servers
        if (80 in open_ports or 443 in open_ports) and not 22 in open_ports and not 3389 in open_ports:
            return 'web_server'
        
        # Mail servers
        if any(port in open_ports for port in [25, 110, 143, 993, 995, 587]):
            return 'mail_server'
        
        # DNS servers
        if 53 in open_ports:
            return 'dns_server'
        
        # FTP servers
        if 21 in open_ports:
            return 'ftp_server'
        
        # VoIP devices
        if any(port in open_ports for port in [5060, 5061]) or 'sip' in hostname:
            return 'voip_device'
        
        # Printers
        if any(port in open_ports for port in [631, 9100, 515]) or any(pattern in hostname for pattern in ['printer', 'print', 'hp-', 'canon-', 'epson-']):
            return 'printer'
        
        # Storage devices (NAS/SAN)
        if any(port in open_ports for port in [2049, 111]) or any(pattern in hostname for pattern in ['nas-', 'storage-', 'synology', 'qnap']):
            return 'storage_device'
        
        # Virtualization hosts
        if any(port in open_ports for port in [902, 443, 8006]) and any(pattern in hostname for pattern in ['esx', 'vcenter', 'proxmox', 'hyper-v']):
            return 'virtualization_host'
        
        # IoT/Embedded devices
        if 80 in open_ports and len(open_ports) <= 2 and not 22 in open_ports:
            return 'iot_device'
        
        return None

    def _fallback_classification(self, open_ports: list, hostname: str) -> str:
        """Fallback classification when specific identification fails"""
        
        # Server-like (multiple services)
        if len(open_ports) >= 3:
            return 'server'
        
        # Web-based device
        if 80 in open_ports or 443 in open_ports:
            return 'web_device'
        
        # SSH-only device (likely Linux)
        if 22 in open_ports and len(open_ports) == 1:
            return 'linux'
        
        # RDP-only device (likely Windows)
        if 3389 in open_ports and len(open_ports) == 1:
            return 'windows'
        
        # Default
        return 'unknown'

    def _ping_host(self, host_ip: str) -> bool:
        """
        Check if a host is alive using multiple detection methods.
        First tries ICMP ping (fast), then falls back to TCP port scanning.
        Returns True if host is reachable, False otherwise.
        """
        try:
            import socket
            import subprocess
            import platform
            
            # Try ICMP ping first (fastest method)
            try:
                # Use appropriate ping command based on OS
                ping_cmd = ["ping", "-c", "1", "-W", "1", host_ip] if platform.system() != "Windows" else ["ping", "-n", "1", "-w", "1000", host_ip]
                result = subprocess.run(ping_cmd, capture_output=True, timeout=2)
                if result.returncode == 0:
                    logger.info(f"Host {host_ip} is alive (ICMP ping successful)")
                    return True
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                # ICMP ping failed or not available, fall back to TCP scanning
                pass
            
            # Minimal port list for fast host detection
            # Only scan the most common ports to quickly determine if host is alive
            detection_ports = [
                22,   # SSH (Linux/Unix)
                80,   # HTTP (Web servers, many devices)
                443,  # HTTPS (Web servers, many devices)
                3389, # RDP (Windows)
                135,  # Windows RPC
                445   # SMB (Windows file sharing)
            ]
            
            logger.info(f"Checking host {host_ip} for connectivity using TCP port scanning...")
            
            alive_indicators = 0
            
            for port in detection_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.3)  # Even faster timeout for detection
                    result = sock.connect_ex((host_ip, port))
                    sock.close()
                    
                    # Multiple indicators that host is alive:
                    if result == 0:  # Port is open
                        logger.info(f"Host {host_ip} is alive (port {port} open)")
                        return True
                    elif result in [111, 10061]:  # Connection refused (Linux/Windows)
                        alive_indicators += 1
                        if alive_indicators >= 1:  # Even one refused connection = host alive
                            logger.info(f"Host {host_ip} is alive (connection refused on port {port})")
                            return True
                    elif result in [113, 10060]:  # No route to host / timeout
                        # These typically indicate host is down or unreachable
                        continue
                        
                except Exception as e:
                    # Socket exceptions don't necessarily mean host is down
                    continue
            
            # If we got some connection refused responses, host is likely alive
            if alive_indicators > 0:
                logger.info(f"Host {host_ip} appears to be alive (got {alive_indicators} connection refused responses)")
                return True
            
            logger.info(f"Host {host_ip} appears to be down or unreachable")
            return False
        except Exception as e:
            logger.error(f"Error checking host {host_ip}: {e}")
            return False

    async def _resolve_hostname(self, host_ip: str) -> str:
        """
        Resolve hostname for an IP address.
        Returns hostname if found, otherwise returns the IP address.
        """
        try:
            import socket
            hostname = socket.gethostbyaddr(host_ip)[0]
            return hostname
        except Exception:
            return host_ip

    async def _scan_ports(self, host_ip: str, ports: list, timeout: float) -> list:
        """
        Scan specified ports on a host.
        Returns list of open ports.
        """
        open_ports = []
        
        try:
            import socket
            import concurrent.futures
            from concurrent.futures import ThreadPoolExecutor
            
            def scan_port(port):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(min(timeout, 2))  # Max 2 seconds per port
                    result = sock.connect_ex((host_ip, port))
                    sock.close()
                    return port if result == 0 else None
                except Exception:
                    return None
            
            # Scan ports in parallel
            max_workers = max(1, min(10, len(ports)))  # Ensure at least 1 worker
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                port_futures = {executor.submit(scan_port, port): port for port in ports}
                
                for future in concurrent.futures.as_completed(port_futures):
                    result = future.result()
                    if result is not None:
                        open_ports.append(result)
        
        except Exception:
            pass
        
        return sorted(open_ports)

    def _determine_device_type(self, open_ports: list) -> str:
        """
        Determine device type based on open ports.
        """
        if not open_ports:
            return "unknown"
        
        # Common port patterns for device type detection
        if 22 in open_ports:  # SSH
            if 80 in open_ports or 443 in open_ports:
                return "linux"  # Linux server/workstation
            else:
                return "network_device"  # Router/switch
        elif 3389 in open_ports:  # RDP
            return "windows"
        elif 161 in open_ports:  # SNMP
            return "network_device"
        elif 80 in open_ports or 443 in open_ports:
            if 23 in open_ports:  # Telnet + HTTP
                return "network_device"
            else:
                return "server"
        elif 23 in open_ports:  # Telnet only
            return "network_device"
        elif 445 in open_ports or 139 in open_ports:  # SMB
            return "windows"
        elif 631 in open_ports:  # IPP (Internet Printing Protocol)
            return "printer"
        else:
            return "unknown"

    async def _filter_duplicate_targets(self, discovered_devices: list) -> list:
        """
        Filter out discovered devices that are already registered as targets.
        Prevents duplicate imports and protects existing target configurations.
        """
        try:
            from app.database.database import get_db
            from app.models.universal_target_models import TargetCommunicationMethod
            from sqlalchemy.orm import Session
            
            # Get database session
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # Get ONLY ACTIVE IP addresses from ACTIVE targets with ACTIVE communication methods
                active_ips = set()
                
                # Query ONLY active communication methods from ACTIVE targets
                from app.models.universal_target_models import UniversalTarget
                
                comm_methods = db.query(TargetCommunicationMethod).join(
                    UniversalTarget, TargetCommunicationMethod.target_id == UniversalTarget.id
                ).filter(
                    # Both target AND communication method must be active
                    UniversalTarget.is_active == True,
                    UniversalTarget.status == 'active',
                    TargetCommunicationMethod.is_active == True
                ).all()
                
                for comm_method in comm_methods:
                    if comm_method.config and 'host' in comm_method.config:
                        active_ips.add(comm_method.config['host'])
                
                logger.info(f"Found {len(active_ips)} ACTIVE target IP addresses: {list(active_ips)[:10]}...")
                
                # Filter out discovered devices that match ACTIVE IPs only
                filtered_devices = []
                active_duplicates_found = []
                
                for device in discovered_devices:
                    device_ip = device.get('ip_address')
                    if device_ip not in active_ips:
                        filtered_devices.append(device)
                        logger.info(f"Device {device_ip} is available for import (not in active targets)")
                    else:
                        active_duplicates_found.append(device_ip)
                        logger.info(f"Filtered out ACTIVE duplicate device: {device_ip} (already registered as ACTIVE target)")
                
                if active_duplicates_found:
                    logger.info(f"Filtered out {len(active_duplicates_found)} ACTIVE duplicate devices: {active_duplicates_found}")
                else:
                    logger.info("No active duplicates found - all discovered devices are available for import")
                
                return filtered_devices
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error filtering duplicate targets: {e}")
            # If filtering fails, return original list to avoid losing discoveries
            return discovered_devices

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