"""
Discovery Service
Service layer for managing network discovery operations and database interactions.
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.discovery_models import (
    DiscoveryJob, DiscoveredDevice, DiscoveryTemplate, DiscoverySchedule
)
from app.schemas.discovery_schemas import (
    DiscoveryJobCreate, DiscoveryJobUpdate, DiscoveryJobResponse,
    DiscoveredDeviceResponse, DiscoveryTemplateCreate, DiscoveryTemplateUpdate,
    DeviceImportRequest, DeviceImportResponse, DiscoveryStatsResponse
)
from app.services.network_discovery_service import (
    NetworkDiscoveryService, DiscoveryConfig, DiscoveredDevice as NetworkDiscoveredDevice
)
from app.services.universal_target_service import UniversalTargetService

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Service for managing network discovery operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.network_service = NetworkDiscoveryService()
        self.target_service = UniversalTargetService(db)
    
    # Discovery Job Management
    
    def create_discovery_job(self, job_data: DiscoveryJobCreate, user_id: Optional[int] = None) -> DiscoveryJob:
        """Create a new discovery job."""
        job = DiscoveryJob(
            name=job_data.name,
            description=job_data.description,
            network_ranges=job_data.network_ranges,
            port_ranges=job_data.port_ranges or [],
            common_ports=job_data.common_ports or [],
            timeout=job_data.timeout,
            max_concurrent=job_data.max_concurrent,
            snmp_communities=job_data.snmp_communities or ['public'],
            enable_snmp=job_data.enable_snmp,
            enable_service_detection=job_data.enable_service_detection,
            enable_hostname_resolution=job_data.enable_hostname_resolution,
            created_by=user_id,
            status='pending'
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        logger.info(f"Created discovery job {job.id}: {job.name}")
        
        # Automatically start the discovery job
        try:
            from app.tasks.discovery_tasks import run_discovery_job_task
            run_discovery_job_task.delay(job.id)
            logger.info(f"Queued discovery job {job.id} for execution")
        except Exception as e:
            logger.error(f"Failed to queue discovery job {job.id}: {str(e)}")
        
        return job
    
    def get_discovery_job(self, job_id: int) -> Optional[DiscoveryJob]:
        """Get a discovery job by ID."""
        return self.db.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
    
    def list_discovery_jobs(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[DiscoveryJob]:
        """List discovery jobs with optional filtering."""
        query = self.db.query(DiscoveryJob)
        
        if status:
            query = query.filter(DiscoveryJob.status == status)
        
        return query.order_by(desc(DiscoveryJob.created_at)).offset(skip).limit(limit).all()
    
    def update_discovery_job(self, job_id: int, job_data: DiscoveryJobUpdate) -> Optional[DiscoveryJob]:
        """Update a discovery job."""
        job = self.get_discovery_job(job_id)
        if not job:
            return None
        
        update_data = job_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)
        
        self.db.commit()
        self.db.refresh(job)
        
        logger.info(f"Updated discovery job {job_id}")
        return job
    
    def delete_discovery_job(self, job_id: int) -> bool:
        """Delete a discovery job and all associated discovered devices."""
        job = self.get_discovery_job(job_id)
        if not job:
            return False
        
        # Check if job is running
        if job.status == 'running':
            logger.warning(f"Cannot delete running discovery job {job_id}")
            return False
        
        self.db.delete(job)
        self.db.commit()
        
        logger.info(f"Deleted discovery job {job_id}")
        return True
    
    # Discovery Execution
    
    async def run_discovery_job(self, job_id: int) -> bool:
        """Run a discovery job asynchronously."""
        job = self.get_discovery_job(job_id)
        if not job:
            logger.error(f"Discovery job {job_id} not found")
            return False
        
        if job.status != 'pending':
            logger.warning(f"Discovery job {job_id} is not in pending status")
            return False
        
        try:
            # Update job status
            job.status = 'running'
            job.started_at = datetime.utcnow()
            job.progress = 0.0
            self.db.commit()
            
            logger.info(f"Starting discovery job {job_id}: {job.name}")
            
            # Create discovery configuration
            config = DiscoveryConfig(
                network_ranges=job.network_ranges,
                port_ranges=job.port_ranges or [(1, 1024)],
                common_ports=job.common_ports or [],
                timeout=job.timeout,
                max_concurrent=job.max_concurrent,
                snmp_communities=job.snmp_communities or ['public'],
                enable_snmp=job.enable_snmp,
                enable_service_detection=job.enable_service_detection,
                enable_hostname_resolution=job.enable_hostname_resolution
            )
            
            # Calculate total IPs for progress tracking
            total_ips = 0
            import ipaddress
            for network_range in job.network_ranges:
                network = ipaddress.ip_network(network_range, strict=False)
                total_ips += network.num_addresses - 2  # Exclude network and broadcast
            
            job.total_ips_scanned = total_ips
            self.db.commit()
            
            # Run network discovery
            discovered_devices = await self.network_service.discover_network(config)
            
            # Save discovered devices to database
            device_count = 0
            for device in discovered_devices:
                db_device = DiscoveredDevice(
                    discovery_job_id=job.id,
                    ip_address=device.ip_address,
                    hostname=device.hostname,
                    mac_address=device.mac_address,
                    open_ports=device.open_ports,
                    services=device.services,
                    snmp_info=device.snmp_info,
                    device_type=device.device_type,
                    os_type=device.os_type,
                    confidence_score=device.confidence_score,
                    suggested_communication_methods=device.suggested_communication_methods,
                    discovered_at=device.discovery_time,
                    status='discovered'
                )
                self.db.add(db_device)
                device_count += 1
            
            # Update job completion
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            job.progress = 100.0
            job.devices_discovered = device_count
            
            self.db.commit()
            
            logger.info(f"Discovery job {job_id} completed. Found {device_count} devices")
            return True
            
        except Exception as e:
            logger.error(f"Discovery job {job_id} failed: {str(e)}")
            
            # Update job status to failed
            job.status = 'failed'
            job.completed_at = datetime.utcnow()
            self.db.commit()
            
            return False
    
    def cancel_discovery_job(self, job_id: int) -> bool:
        """Cancel a running discovery job."""
        job = self.get_discovery_job(job_id)
        if not job:
            return False
        
        if job.status != 'running':
            logger.warning(f"Discovery job {job_id} is not running")
            return False
        
        # TODO: Implement actual cancellation mechanism
        # For now, just mark as cancelled
        job.status = 'cancelled'
        job.completed_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Cancelled discovery job {job_id}")
        return True
    
    # Discovered Device Management
    
    def get_discovered_device(self, device_id: int) -> Optional[DiscoveredDevice]:
        """Get a discovered device by ID."""
        return self.db.query(DiscoveredDevice).filter(DiscoveredDevice.id == device_id).first()
    
    def list_discovered_devices(
        self, 
        job_id: Optional[int] = None,
        status: Optional[str] = None,
        device_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DiscoveredDevice]:
        """List discovered devices with optional filtering."""
        query = self.db.query(DiscoveredDevice)
        
        if job_id:
            query = query.filter(DiscoveredDevice.discovery_job_id == job_id)
        
        if status:
            query = query.filter(DiscoveredDevice.status == status)
        
        if device_type:
            query = query.filter(DiscoveredDevice.device_type == device_type)
        
        return query.order_by(desc(DiscoveredDevice.discovered_at)).offset(skip).limit(limit).all()
    
    def list_importable_devices(
        self, 
        job_id: Optional[int] = None,
        device_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DiscoveredDevice]:
        """List discovered devices that can be imported (not already imported or linked to existing targets)."""
        query = self.db.query(DiscoveredDevice)
        
        # Only include devices that haven't been imported yet
        query = query.filter(DiscoveredDevice.status == 'discovered')
        query = query.filter(DiscoveredDevice.target_id.is_(None))
        
        # TODO: Add IP-based filtering to prevent conflicts with existing targets
        # For now, just rely on target_id being None to identify importable devices
        
        if job_id:
            query = query.filter(DiscoveredDevice.discovery_job_id == job_id)
        
        if device_type:
            query = query.filter(DiscoveredDevice.device_type == device_type)
        
        return query.order_by(desc(DiscoveredDevice.discovered_at)).offset(skip).limit(limit).all()
    
    async def run_in_memory_discovery(self, discovery_config: dict) -> List[DiscoveredDevice]:
        """
        Run network discovery without persisting results to database.
        Returns discovered devices as in-memory objects for immediate use.
        """
        # Create discovery config
        config = DiscoveryConfig(
            network_ranges=discovery_config.get('network_ranges', []),
            port_ranges=[],
            common_ports=discovery_config.get('common_ports', [22, 80, 443]),
            timeout=discovery_config.get('timeout', 3.0),
            max_concurrent=discovery_config.get('max_concurrent', 50),
            snmp_communities=['public'] if discovery_config.get('enable_snmp', False) else [],
            enable_snmp=discovery_config.get('enable_snmp', False),
            enable_service_detection=discovery_config.get('enable_service_detection', True),
            enable_hostname_resolution=discovery_config.get('enable_hostname_resolution', True)
        )
        
        # Run discovery and get results
        discovered_hosts = await self.network_service.discover_network(config)
        
        # Ensure we have a valid list
        if not discovered_hosts or not isinstance(discovered_hosts, list):
            discovered_hosts = []
        
        # Convert NetworkDiscoveryService DiscoveredDevice objects to database model objects (in-memory only)
        devices = []
        for i, network_device in enumerate(discovered_hosts):
            device = DiscoveredDevice(
                ip_address=network_device.ip_address,
                hostname=network_device.hostname,
                mac_address=network_device.mac_address,
                open_ports=network_device.open_ports,
                services=network_device.services,
                snmp_info=network_device.snmp_info,
                device_type=network_device.device_type or 'unknown',
                os_type=network_device.os_type,
                confidence_score=network_device.confidence_score,
                suggested_communication_methods=network_device.suggested_communication_methods,
                discovered_at=datetime.utcnow(),
                status='discovered',
                discovery_job_id=None,  # No job ID for in-memory discovery
                target_id=None,
                imported_at=None,
                imported_by=None
            )
            # Set a temporary ID for frontend use (negative to avoid conflicts)
            device.id = -(i + 1)
            devices.append(device)
        
        return devices
    
    def import_in_memory_devices(self, import_request: dict) -> dict:
        """
        Import in-memory discovered devices as targets.
        """
        device_configs = import_request.get('device_configs', [])
        
        imported_count = 0
        existing_count = 0
        failed_count = 0
        errors = []
        target_ids = []
        
        for config in device_configs:
            try:
                device_data = config['device_data']
                
                # Skip duplicate check for now - just import
                # TODO: Add proper duplicate detection later
                
                # Create the target using the correct method signature
                target = self.target_service.create_target(
                    name=config['target_name'],
                    os_type=self._map_device_type_to_os(device_data['device_type']),
                    ip_address=device_data['ip_address'],
                    method_type=config['communication_method'],
                    username=config.get('username'),
                    password=config.get('password'),
                    ssh_key=config.get('ssh_key'),
                    ssh_passphrase=config.get('ssh_passphrase'),
                    description=config.get('description'),
                    environment=config.get('environment', 'development')
                )
                imported_count += 1
                target_ids.append(target.id)
                
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to import {config.get('target_name', 'unknown')}: {str(e)}")
        
        return {
            'imported_count': imported_count,
            'existing_count': existing_count,
            'failed_count': failed_count,
            'target_ids': target_ids,
            'errors': errors
        }
    
    def _map_device_type_to_os(self, device_type: str) -> str:
        """Map device type to OS type."""
        mapping = {
            'linux': 'linux',
            'windows': 'windows',
            'router': 'cisco_router',
            'switch': 'cisco_switch',
            'cisco_switch': 'cisco_switch',
            'cisco_router': 'cisco_router',
            'nginx': 'linux',
            'apache': 'linux',
            'server': 'linux',
            'workstation': 'linux',
            'desktop': 'linux'
        }
        return mapping.get(device_type, 'generic_device')
    
    def update_discovered_device_status(self, device_id: int, status: str) -> Optional[DiscoveredDevice]:
        """Update the status of a discovered device."""
        device = self.get_discovered_device(device_id)
        if not device:
            return None
        
        device.status = status
        self.db.commit()
        self.db.refresh(device)
        
        return device
    
    # Device Import
    
    def import_discovered_devices(
        self, 
        import_request: DeviceImportRequest, 
        user_id: Optional[int] = None
    ) -> DeviceImportResponse:
        """Import discovered devices as targets."""
        imported_count = 0
        failed_count = 0
        existing_count = 0
        target_ids = []
        errors = []
        
        for device_id in import_request.device_ids:
            try:
                device = self.get_discovered_device(device_id)
                if not device:
                    errors.append(f"Device {device_id} not found")
                    failed_count += 1
                    continue
                
                if device.status == 'imported':
                    errors.append(f"Device {device_id} already imported")
                    failed_count += 1
                    continue
                
                # Check if target already exists before creating
                existing_target = self.target_service._check_duplicate_active_ip(device.ip_address)
                
                # Create target from discovered device
                target_id = self._create_target_from_device(device, import_request, user_id)
                
                if target_id:
                    # Update device status
                    device.status = 'imported'
                    device.target_id = target_id
                    device.imported_at = datetime.utcnow()
                    device.imported_by = user_id
                    
                    target_ids.append(target_id)
                    
                    if existing_target:
                        existing_count += 1
                    else:
                        imported_count += 1
                else:
                    errors.append(f"Failed to create target for device {device_id}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error importing device {device_id}: {str(e)}")
                errors.append(f"Device {device_id}: {str(e)}")
                failed_count += 1
        
        self.db.commit()
        
        logger.info(f"Import completed: {imported_count} new targets, {existing_count} existing targets, {failed_count} failed")
        
        return DeviceImportResponse(
            imported_count=imported_count,
            existing_count=existing_count,
            failed_count=failed_count,
            target_ids=target_ids,
            errors=errors
        )
    
    def import_configured_devices(
        self, 
        import_request: 'BulkDeviceImportRequest', 
        user_id: Optional[int] = None
    ) -> 'DeviceImportResponse':
        """Import discovered devices as targets with user-provided configuration."""
        from app.schemas.discovery_schemas import BulkDeviceImportRequest, DeviceImportResponse
        
        imported_count = 0
        failed_count = 0
        existing_count = 0
        target_ids = []
        errors = []
        
        for device_config in import_request.device_configs:
            try:
                device = self.get_discovered_device(device_config.device_id)
                if not device:
                    errors.append(f"Device {device_config.device_id} not found")
                    failed_count += 1
                    continue
                
                if device.status == 'imported':
                    errors.append(f"Device {device_config.device_id} already imported")
                    failed_count += 1
                    continue
                
                # Check if target already exists before creating
                existing_target = self.target_service._check_duplicate_active_ip(device.ip_address)
                
                # Create target with user-provided configuration
                target_id = self._create_target_from_configured_device(device, device_config, user_id)
                
                if target_id:
                    # Update device status
                    device.status = 'imported'
                    device.target_id = target_id
                    device.imported_at = datetime.utcnow()
                    device.imported_by = user_id
                    
                    target_ids.append(target_id)
                    
                    if existing_target:
                        existing_count += 1
                    else:
                        imported_count += 1
                else:
                    errors.append(f"Failed to create target for device {device_config.device_id}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error importing configured device {device_config.device_id}: {str(e)}")
                errors.append(f"Device {device_config.device_id}: {str(e)}")
                failed_count += 1
        
        self.db.commit()
        
        logger.info(f"Configured import completed: {imported_count} new targets, {existing_count} existing targets, {failed_count} failed")
        
        return DeviceImportResponse(
            imported_count=imported_count,
            existing_count=existing_count,
            failed_count=failed_count,
            target_ids=target_ids,
            errors=errors
        )
    
    def _create_target_from_device(
        self, 
        device: DiscoveredDevice, 
        import_request: DeviceImportRequest,
        user_id: Optional[int] = None
    ) -> Optional[int]:
        """Create a target from a discovered device, or return existing target ID if already exists."""
        try:
            # Check if a target with this IP already exists
            existing_target = self.target_service._check_duplicate_active_ip(device.ip_address)
            if existing_target:
                logger.info(f"Target with IP {device.ip_address} already exists (ID: {existing_target.id}, Name: {existing_target.name}). Skipping creation.")
                return existing_target.id
            
            # Determine target name
            target_name = device.hostname or f"device-{device.ip_address.replace('.', '-')}"
            
            # Get primary communication method info
            primary_method = device.suggested_communication_methods[0] if device.suggested_communication_methods else 'ssh'
            
            # Create basic target using the expected signature
            target = self.target_service.create_target(
                name=target_name,
                os_type=device.device_type or 'generic_device',
                ip_address=device.ip_address,
                method_type=primary_method,
                username=import_request.default_credentials.get('username', 'admin') if import_request.default_credentials else 'admin',
                password=import_request.default_credentials.get('password') if import_request.default_credentials else None,
                description=f"Auto-imported from discovery job {device.discovery_job_id}",
                environment=import_request.default_environment
            )
            
            if not target:
                return None
            
            # The target service already created the primary communication method
            # We could add additional methods here if needed
            
            logger.info(f"Created new target from discovery: ID {target.id}, Name: {target.name}, IP: {device.ip_address}")
            return target.id
            
        except Exception as e:
            logger.error(f"Error creating target from device {device.id}: {str(e)}")
            return None
    
    def _create_target_from_configured_device(
        self, 
        device: DiscoveredDevice, 
        device_config: 'DeviceTargetConfig',
        user_id: Optional[int] = None
    ) -> Optional[int]:
        """Create a target from a discovered device with user-provided configuration."""
        from app.schemas.discovery_schemas import DeviceTargetConfig
        
        try:
            # Check if a target with this IP already exists
            existing_target = self.target_service._check_duplicate_active_ip(device.ip_address)
            if existing_target:
                logger.info(f"Target with IP {device.ip_address} already exists (ID: {existing_target.id}, Name: {existing_target.name}). Skipping creation.")
                return existing_target.id
            
            # Determine port - use user-provided port or default for the method
            port = device_config.port
            if not port:
                # Use default ports for common methods
                default_ports = {
                    'ssh': 22,
                    'winrm': 5985,
                    'snmp': 161,
                    'telnet': 23,
                    'http': 80,
                    'https': 443
                }
                port = default_ports.get(device_config.communication_method)
            
            # Create target using user-provided configuration
            target = self.target_service.create_target(
                name=device_config.target_name,
                os_type=device.device_type or 'generic_device',
                ip_address=device.ip_address,
                method_type=device_config.communication_method,
                username=device_config.username,
                password=device_config.password,
                ssh_key=device_config.ssh_key,
                ssh_passphrase=device_config.ssh_passphrase,
                description=device_config.description or f"Imported from discovery job {device.discovery_job_id}",
                environment=device_config.environment
            )
            
            if not target:
                return None
            
            logger.info(f"Created configured target from discovery: ID {target.id}, Name: {target.name}, IP: {device.ip_address}")
            return target.id
            
        except Exception as e:
            logger.error(f"Error creating configured target from device {device.id}: {str(e)}")
            return None
    
    def _create_communication_methods_for_device(
        self, 
        target_id: int, 
        device: DiscoveredDevice,
        default_credentials: Optional[Dict[str, str]] = None
    ):
        """Create communication methods for an imported device."""
        try:
            primary_method_created = False
            
            for method_type in device.suggested_communication_methods or []:
                # Determine port based on method type
                port = None
                if method_type == 'ssh' and 22 in device.open_ports:
                    port = 22
                elif method_type == 'winrm' and 5985 in device.open_ports:
                    port = 5985
                elif method_type == 'winrm' and 5986 in device.open_ports:
                    port = 5986
                elif method_type == 'snmp' and 161 in device.open_ports:
                    port = 161
                elif method_type == 'rest_api':
                    if 443 in device.open_ports:
                        port = 443
                    elif 80 in device.open_ports:
                        port = 80
                elif method_type == 'telnet' and 23 in device.open_ports:
                    port = 23
                elif method_type == 'smtp' and 25 in device.open_ports:
                    port = 25
                
                if port:
                    # Create communication method
                    method = self.target_service.create_communication_method(
                        target_id=target_id,
                        method_type=method_type,
                        host=device.ip_address,
                        port=port,
                        is_primary=not primary_method_created,
                        is_active=True,
                        priority=1 if not primary_method_created else 2
                    )
                    
                    if method and default_credentials:
                        # Create default credentials
                        username = default_credentials.get('username')
                        password = default_credentials.get('password')
                        
                        if username and password:
                            self.target_service.create_credential(
                                communication_method_id=method.id,
                                credential_type='password',
                                username=username,
                                password=password,
                                is_primary=True,
                                is_active=True
                            )
                    
                    primary_method_created = True
                    
        except Exception as e:
            logger.error(f"Error creating communication methods for target {target_id}: {str(e)}")
    
    # Templates
    
    def create_discovery_template(self, template_data: DiscoveryTemplateCreate, user_id: Optional[int] = None) -> DiscoveryTemplate:
        """Create a discovery template."""
        template = DiscoveryTemplate(
            name=template_data.name,
            description=template_data.description,
            network_ranges=template_data.network_ranges,
            port_ranges=template_data.port_ranges or [],
            common_ports=template_data.common_ports or [],
            timeout=template_data.timeout,
            max_concurrent=template_data.max_concurrent,
            snmp_communities=template_data.snmp_communities or ['public'],
            enable_snmp=template_data.enable_snmp,
            enable_service_detection=template_data.enable_service_detection,
            enable_hostname_resolution=template_data.enable_hostname_resolution,
            is_default=template_data.is_default,
            created_by=user_id
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"Created discovery template {template.id}: {template.name}")
        return template
    
    def get_discovery_template(self, template_id: int) -> Optional[DiscoveryTemplate]:
        """Get a discovery template by ID."""
        return self.db.query(DiscoveryTemplate).filter(DiscoveryTemplate.id == template_id).first()
    
    def list_discovery_templates(self, active_only: bool = True) -> List[DiscoveryTemplate]:
        """List discovery templates."""
        query = self.db.query(DiscoveryTemplate)
        
        if active_only:
            query = query.filter(DiscoveryTemplate.is_active == True)
        
        return query.order_by(DiscoveryTemplate.name).all()
    
    # Statistics
    
    def get_discovery_stats(self) -> DiscoveryStatsResponse:
        """Get discovery statistics."""
        total_jobs = self.db.query(DiscoveryJob).count()
        active_jobs = self.db.query(DiscoveryJob).filter(DiscoveryJob.status == 'running').count()
        
        total_devices = self.db.query(DiscoveredDevice).count()
        devices_imported = self.db.query(DiscoveredDevice).filter(DiscoveredDevice.status == 'imported').count()
        devices_pending = self.db.query(DiscoveredDevice).filter(DiscoveredDevice.status == 'discovered').count()
        
        # Device type counts
        from sqlalchemy import func
        device_type_query = self.db.query(
            DiscoveredDevice.device_type,
            func.count(DiscoveredDevice.id)
        ).group_by(DiscoveredDevice.device_type).all()
        
        device_type_counts = {device_type or 'unknown': count for device_type, count in device_type_query}
        
        # Recent jobs
        recent_jobs = self.list_discovery_jobs(limit=5)
        
        return DiscoveryStatsResponse(
            total_jobs=total_jobs,
            active_jobs=active_jobs,
            total_devices_discovered=total_devices,
            devices_imported=devices_imported,
            devices_pending=devices_pending,
            device_type_counts=device_type_counts,
            recent_jobs=[
                {
                    'id': job.id,
                    'name': job.name,
                    'status': job.status,
                    'progress': job.progress,
                    'devices_discovered': job.devices_discovered,
                    'created_at': job.created_at,
                    'completed_at': job.completed_at
                }
                for job in recent_jobs
            ]
        )
    
    # Quick Network Scan
    
    async def quick_network_scan(self, network_range: str, ports: Optional[List[int]] = None, timeout: float = 2.0) -> Dict[str, Any]:
        """Perform a quick network scan without saving to database."""
        import ipaddress
        import time
        
        start_time = time.time()
        
        # Create quick scan configuration
        config = DiscoveryConfig(
            network_ranges=[network_range],
            common_ports=ports or [22, 80, 443, 161],
            timeout=timeout,
            max_concurrent=50,
            enable_snmp=False,
            enable_service_detection=False,
            enable_hostname_resolution=False
        )
        
        # Calculate total IPs
        network = ipaddress.ip_network(network_range, strict=False)
        total_ips = network.num_addresses - 2  # Exclude network and broadcast
        
        # Run discovery
        discovered_devices = await self.network_service.discover_network(config)
        
        scan_duration = time.time() - start_time
        
        return {
            'network_range': network_range,
            'total_ips': total_ips,
            'responsive_ips': [device.ip_address for device in discovered_devices],
            'scan_duration': scan_duration,
            'devices_found': [
                {
                    'ip_address': device.ip_address,
                    'hostname': device.hostname,
                    'open_ports': device.open_ports,
                    'device_type': device.device_type,
                    'confidence_score': device.confidence_score,
                    'discovered_at': device.discovery_time
                }
                for device in discovered_devices
            ]
        }