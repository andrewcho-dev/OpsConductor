"""
Discovery Tasks - Network Discovery and Target Management
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.celery_app import app
from app.core.config import settings

# Try to import from shared libs, fall back to local implementations
try:
    from opsconductor_shared.clients.base_client import BaseServiceClient
    from opsconductor_shared.models.base import ServiceType
except ImportError:
    from app.shared.fallback_models import BaseServiceClient, ServiceType

logger = logging.getLogger(__name__)


@app.task(queue='system')
def auto_discovery_scan(network_ranges: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Perform automatic network discovery scan
    
    Args:
        network_ranges: Optional list of network ranges to scan
        
    Returns:
        Dict with discovery results
    """
    try:
        logger.info("Starting auto-discovery network scan")
        
        # BaseServiceClient and ServiceType already imported at module level
        
        # Get target discovery service client
        discovery_client = BaseServiceClient(
            ServiceType.TARGET_DISCOVERY,
            settings.target_discovery_service_url
        )
        
        # Get configured network ranges if none provided
        if not network_ranges:
            network_ranges = settings.auto_discovery_networks or ['192.168.1.0/24']
        
        discovered_targets = []
        total_scanned = 0
        
        for network_range in network_ranges:
            try:
                logger.info(f"Scanning network range: {network_range}")
                
                # Call discovery service
                scan_result = discovery_client.post('/api/discovery/scan', {
                    'network_range': network_range,
                    'scan_type': 'auto',
                    'ports': [22, 3389, 80, 443, 5985, 5986],  # Common management ports
                    'timeout': 30
                })
                
                if scan_result.get('status') == 'success':
                    targets = scan_result.get('targets', [])
                    discovered_targets.extend(targets)
                    total_scanned += scan_result.get('hosts_scanned', 0)
                    
                    logger.info(f"Found {len(targets)} targets in {network_range}")
                else:
                    logger.warning(f"Discovery scan failed for {network_range}: {scan_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Failed to scan network {network_range}: {e}")
                continue
        
        # Filter new targets (not already in database)
        from app.database.database import get_db
        
        db = next(get_db())
        
        try:
            # Get targets service client to check existing targets
            targets_client = BaseServiceClient(
                ServiceType.TARGET_MANAGEMENT,
                settings.targets_service_url
            )
            
            existing_targets_resp = targets_client.get('/api/targets')
            existing_ips = set()
            
            if existing_targets_resp.get('status') == 'success':
                existing_targets = existing_targets_resp.get('targets', [])
                existing_ips = {target.get('ip_address') for target in existing_targets}
            
            # Filter out existing targets
            new_targets = [
                target for target in discovered_targets
                if target.get('ip_address') not in existing_ips
            ]
            
            return {
                'status': 'success',
                'networks_scanned': network_ranges,
                'hosts_scanned': total_scanned,
                'targets_discovered': len(discovered_targets),
                'new_targets': len(new_targets),
                'targets': new_targets,
                'scanned_at': datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Auto-discovery scan failed: {exc}")
        raise exc


@app.task(queue='system')
def validate_discovered_targets(target_ids: List[int]) -> Dict[str, Any]:
    """
    Validate connectivity to discovered targets
    
    Args:
        target_ids: List of target IDs to validate
        
    Returns:
        Dict with validation results
    """
    try:
        logger.info(f"Validating {len(target_ids)} discovered targets")
        
        # BaseServiceClient and ServiceType already imported at module level
        
        # Get targets service client
        targets_client = BaseServiceClient(
            ServiceType.TARGET_MANAGEMENT,
            settings.targets_service_url
        )
        
        validated_targets = []
        failed_validations = []
        
        for target_id in target_ids:
            try:
                logger.debug(f"Validating target {target_id}")
                
                # Test connectivity
                validation_result = targets_client.post(f'/api/targets/{target_id}/test-connection', {
                    'timeout': 30,
                    'include_ports': True
                })
                
                if validation_result.get('status') == 'success':
                    validated_targets.append({
                        'target_id': target_id,
                        'connectivity': validation_result.get('connectivity'),
                        'available_ports': validation_result.get('available_ports', []),
                        'os_detection': validation_result.get('os_detection'),
                        'validated_at': datetime.now(timezone.utc).isoformat()
                    })
                else:
                    failed_validations.append({
                        'target_id': target_id,
                        'error': validation_result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to validate target {target_id}: {e}")
                failed_validations.append({
                    'target_id': target_id,
                    'error': str(e)
                })
                continue
        
        return {
            'status': 'success',
            'validated_count': len(validated_targets),
            'failed_count': len(failed_validations),
            'validated_targets': validated_targets,
            'failed_validations': failed_validations,
            'validated_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Target validation failed: {exc}")
        raise exc


@app.task(queue='system')
def update_target_inventory(scan_deep: bool = False) -> Dict[str, Any]:
    """
    Update inventory information for existing targets
    
    Args:
        scan_deep: Whether to perform deep inventory scan
        
    Returns:
        Dict with inventory update results
    """
    try:
        logger.info(f"Updating target inventory (deep={scan_deep})")
        
        # BaseServiceClient and ServiceType already imported at module level
        
        # Get targets service client
        targets_client = BaseServiceClient(
            ServiceType.TARGET_MANAGEMENT,
            settings.targets_service_url
        )
        
        # Get all active targets
        targets_resp = targets_client.get('/api/targets', params={
            'status': 'active',
            'limit': 1000
        })
        
        if targets_resp.get('status') != 'success':
            raise Exception(f"Failed to get targets: {targets_resp.get('error')}")
        
        targets = targets_resp.get('targets', [])
        updated_count = 0
        failed_count = 0
        
        for target in targets:
            try:
                target_id = target.get('id')
                logger.debug(f"Updating inventory for target {target_id}")
                
                # Collect inventory data
                inventory_data = {
                    'collect_hardware': True,
                    'collect_software': True,
                    'collect_services': True,
                    'collect_network': scan_deep,
                    'collect_performance': scan_deep
                }
                
                # Update target inventory
                update_result = targets_client.post(
                    f'/api/targets/{target_id}/collect-inventory',
                    inventory_data
                )
                
                if update_result.get('status') == 'success':
                    updated_count += 1
                    logger.debug(f"Updated inventory for target {target_id}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to update inventory for target {target_id}: {update_result.get('error')}")
                    
            except Exception as e:
                logger.warning(f"Failed to process target {target.get('id')}: {e}")
                failed_count += 1
                continue
        
        return {
            'status': 'success',
            'targets_processed': len(targets),
            'updated_count': updated_count,
            'failed_count': failed_count,
            'scan_type': 'deep' if scan_deep else 'standard',
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Target inventory update failed: {exc}")
        raise exc


@app.task(queue='system')
def cleanup_stale_discoveries(days_old: int = 7) -> Dict[str, Any]:
    """
    Clean up old discovery scan results
    
    Args:
        days_old: Remove discovery data older than this many days
        
    Returns:
        Dict with cleanup results
    """
    try:
        logger.info(f"Cleaning up discovery data older than {days_old} days")
        
        # BaseServiceClient and ServiceType already imported at module level
        from datetime import timedelta
        
        # Get target discovery service client
        discovery_client = BaseServiceClient(
            ServiceType.TARGET_DISCOVERY,
            settings.target_discovery_service_url
        )
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        # Clean up old scan results
        cleanup_result = discovery_client.delete('/api/discovery/cleanup', params={
            'cutoff_date': cutoff_date.isoformat(),
            'keep_successful': True  # Keep successful discoveries that led to targets
        })
        
        if cleanup_result.get('status') == 'success':
            return {
                'status': 'success',
                'records_deleted': cleanup_result.get('records_deleted', 0),
                'cutoff_date': cutoff_date.isoformat(),
                'cleaned_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            raise Exception(f"Discovery cleanup failed: {cleanup_result.get('error')}")
        
    except Exception as exc:
        logger.error(f"Discovery cleanup failed: {exc}")
        raise exc