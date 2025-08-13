"""
Health Monitoring Service
Handles target health checks and status updates.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.universal_target_models import UniversalTarget, TargetCommunicationMethod
from app.utils.connection_test_utils import test_ssh_connection, test_winrm_connection
from app.utils.encryption_utils import decrypt_credentials
from app.config.health_monitoring import (
    get_health_check_interval,
    get_health_check_timeout,
    should_escalate_to_warning,
    should_escalate_to_critical,
    should_recover_to_healthy,
    HEALTH_MONITORING_SETTINGS
)

logger = logging.getLogger(__name__)


class HealthMonitoringService:
    """Service for monitoring target health and updating status."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_target_health(self, target: UniversalTarget) -> Dict[str, Any]:
        """
        Check the health of a single target using its primary communication method.
        
        Args:
            target: UniversalTarget instance with loaded communication methods
            
        Returns:
            dict: Health check result with status, response_time, and details
        """
        if not HEALTH_MONITORING_SETTINGS['enabled']:
            return {'success': False, 'message': 'Health monitoring disabled'}
        
        # Get primary communication method
        primary_method = self._get_primary_communication_method(target)
        if not primary_method:
            return {
                'success': False,
                'message': 'No primary communication method found',
                'health_status': 'critical'
            }
        
        # Get timeout for this method type
        timeout = get_health_check_timeout(primary_method.method_type)
        
        try:
            # Get primary credential for this method
            primary_credential = None
            if primary_method.credentials:
                # Look for primary credential first
                for cred in primary_method.credentials:
                    if cred.is_primary and cred.is_active:
                        primary_credential = cred
                        break
                
                # If no primary, get first active credential
                if not primary_credential:
                    for cred in primary_method.credentials:
                        if cred.is_active:
                            primary_credential = cred
                            break
            
            if not primary_credential:
                return {
                    'success': False,
                    'message': 'No active credentials found for communication method',
                    'health_status': 'critical'
                }
            
            # Decrypt credentials
            decrypted_creds = decrypt_credentials(primary_credential.encrypted_credentials)
            
            # Perform health check based on method type
            start_time = time.time()
            
            if primary_method.method_type == 'ssh':
                result = self._check_ssh_health(primary_method, decrypted_creds, timeout)
            elif primary_method.method_type == 'winrm':
                result = self._check_winrm_health(primary_method, decrypted_creds, timeout)
            elif primary_method.method_type == 'snmp':
                result = self._check_snmp_health(primary_method, decrypted_creds, timeout)
            elif primary_method.method_type == 'telnet':
                result = self._check_telnet_health(primary_method, decrypted_creds, timeout)
            elif primary_method.method_type == 'rest_api':
                result = self._check_rest_api_health(primary_method, decrypted_creds, timeout)
            elif primary_method.method_type == 'smtp':
                result = self._check_smtp_health(primary_method, decrypted_creds, timeout)
            else:
                return {
                    'success': False,
                    'message': f'Unsupported method type: {primary_method.method_type}',
                    'health_status': 'unknown'
                }
            
            response_time = time.time() - start_time
            result['response_time'] = response_time
            
            # Determine health status based on result and response time
            if result['success']:
                if response_time <= 5.0:
                    result['health_status'] = 'healthy'
                elif response_time <= 10.0:
                    result['health_status'] = 'warning'
                else:
                    result['health_status'] = 'critical'
            else:
                result['health_status'] = 'critical'
            
            return result
            
        except Exception as e:
            logger.error(f"Health check failed for target {target.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Health check error: {str(e)}',
                'health_status': 'critical',
                'response_time': None
            }
    
    def _check_ssh_health(self, method: TargetCommunicationMethod, credentials: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Check SSH connectivity for health monitoring."""
        host = method.config.get('host')
        port = method.config.get('port', 22)
        
        if not host:
            return {'success': False, 'message': 'No host configured'}
        
        # Use the connection test utility
        result = test_ssh_connection(host, port, credentials, timeout)
        
        if HEALTH_MONITORING_SETTINGS['log_all_checks']:
            logger.info(f"SSH health check for {host}:{port} - {'SUCCESS' if result['success'] else 'FAILED'}")
        
        return result
    
    def _check_winrm_health(self, method: TargetCommunicationMethod, credentials: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Check WinRM connectivity for health monitoring."""
        host = method.config.get('host')
        port = method.config.get('port', 5985)
        
        if not host:
            return {'success': False, 'message': 'No host configured'}
        
        # Use the connection test utility
        result = test_winrm_connection(host, port, credentials, timeout)
        
        if HEALTH_MONITORING_SETTINGS['log_all_checks']:
            logger.info(f"WinRM health check for {host}:{port} - {'SUCCESS' if result['success'] else 'FAILED'}")
        
        return result
    
    def _check_snmp_health(self, method: TargetCommunicationMethod, credentials: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Check SNMP connectivity for health monitoring."""
        host = method.config.get('host')
        port = method.config.get('port', 161)
        
        if not host:
            return {'success': False, 'message': 'No host configured'}
        
        try:
            # Simple socket connection test for SNMP port
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return {'success': True, 'message': f'SNMP port {port} is reachable on {host}'}
            else:
                return {'success': False, 'message': f'SNMP port {port} is not reachable on {host}'}
                
        except Exception as e:
            return {'success': False, 'message': f'SNMP health check failed: {str(e)}'}
    
    def _check_telnet_health(self, method: TargetCommunicationMethod, credentials: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Check Telnet connectivity for health monitoring."""
        host = method.config.get('host')
        port = method.config.get('port', 23)
        
        if not host:
            return {'success': False, 'message': 'No host configured'}
        
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return {'success': True, 'message': f'Telnet connection successful to {host}:{port}'}
            else:
                return {'success': False, 'message': f'Telnet connection failed to {host}:{port}'}
                
        except Exception as e:
            return {'success': False, 'message': f'Telnet health check failed: {str(e)}'}
    
    def _check_rest_api_health(self, method: TargetCommunicationMethod, credentials: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Check REST API connectivity for health monitoring."""
        host = method.config.get('host')
        port = method.config.get('port', 80)
        protocol = method.config.get('protocol', 'http')
        base_path = method.config.get('base_path', '/')
        
        if not host:
            return {'success': False, 'message': 'No host configured'}
        
        try:
            import requests
            url = f"{protocol}://{host}:{port}{base_path}"
            
            # Simple GET request to check if API is responding
            response = requests.get(url, timeout=timeout, verify=method.config.get('verify_ssl', True))
            
            if response.status_code < 500:  # Any response under 500 means the API is responding
                return {'success': True, 'message': f'REST API responding at {url} (status: {response.status_code})'}
            else:
                return {'success': False, 'message': f'REST API error at {url} (status: {response.status_code})'}
                
        except Exception as e:
            return {'success': False, 'message': f'REST API health check failed: {str(e)}'}
    
    def _check_smtp_health(self, method: TargetCommunicationMethod, credentials: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Check SMTP connectivity for health monitoring - CONNECTIVITY ONLY, NO EMAILS SENT."""
        host = method.config.get('host')
        port = method.config.get('port', 587)
        
        if not host:
            return {'success': False, 'message': 'No host configured'}
        
        # Use the dedicated health-only SMTP function that never sends emails
        from app.utils.connection_test_utils import test_smtp_health_only
        
        # FORCE NO EMAIL SENDING - Remove test_recipient from config for health checks
        health_config = method.config.copy() if method.config else {}
        health_config.pop('test_recipient', None)  # Remove test_recipient to prevent email sending
        
        result = test_smtp_health_only(host, port, credentials, health_config, timeout)
        
        if HEALTH_MONITORING_SETTINGS['log_all_checks']:
            logger.info(f"SMTP health check for {host}:{port} - {'SUCCESS' if result['success'] else 'FAILED'} (connectivity only)")
        
        return result
    
    def _get_primary_communication_method(self, target: UniversalTarget) -> Optional[TargetCommunicationMethod]:
        """Get the primary communication method for a target."""
        if not target.communication_methods:
            return None
        
        # Look for primary method first
        for method in target.communication_methods:
            if method.is_primary and method.is_active:
                return method
        
        # If no primary, get first active method
        for method in target.communication_methods:
            if method.is_active:
                return method
        
        return None
    
    def update_target_health_status(self, target_id: int, health_result: Dict[str, Any]) -> bool:
        """
        Update target health status based on health check result.
        
        Args:
            target_id: Target ID to update
            health_result: Result from check_target_health()
            
        Returns:
            bool: True if status was updated
        """
        try:
            target = self.db.query(UniversalTarget).filter(UniversalTarget.id == target_id).first()
            if not target:
                logger.error(f"Target {target_id} not found for health update")
                return False
            
            old_status = target.health_status
            new_status = health_result.get('health_status', 'unknown')
            
            # Update health status
            target.health_status = new_status
            target.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log status changes
            if old_status != new_status:
                logger.info(f"Target {target.name} ({target_id}) health status changed: {old_status} -> {new_status}")
                
                if HEALTH_MONITORING_SETTINGS['alert_on_status_change']:
                    self._log_health_status_change(target, old_status, new_status, health_result)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update health status for target {target_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def _log_health_status_change(self, target: UniversalTarget, old_status: str, new_status: str, health_result: Dict[str, Any]):
        """Log health status changes for monitoring/alerting."""
        message = health_result.get('message', 'No details')
        response_time = health_result.get('response_time')
        
        log_entry = {
            'target_id': target.id,
            'target_name': target.name,
            'old_status': old_status,
            'new_status': new_status,
            'message': message,
            'response_time': response_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if new_status == 'critical':
            logger.warning(f"🔴 TARGET CRITICAL: {target.name} - {message}")
        elif new_status == 'warning':
            logger.warning(f"🟡 TARGET WARNING: {target.name} - {message}")
        elif new_status == 'healthy' and old_status in ['warning', 'critical']:
            logger.info(f"🟢 TARGET RECOVERED: {target.name} - {message}")
    
    def get_targets_for_health_check(self, batch_size: int = None) -> List[UniversalTarget]:
        """
        Get targets that need health checks based on their last check time and intervals.
        
        Args:
            batch_size: Maximum number of targets to return
            
        Returns:
            List of targets that need health checks
        """
        if batch_size is None:
            batch_size = HEALTH_MONITORING_SETTINGS['batch_size']
        
        # Get active targets that need health checks
        # For now, we'll check all active targets - in future we can add last_health_check timestamp
        targets = (
            self.db.query(UniversalTarget)
            .filter(
                and_(
                    UniversalTarget.is_active == True,
                    UniversalTarget.status == 'active'
                )
            )
            .limit(batch_size)
            .all()
        )
        
        return targets
    
    def run_health_check_batch(self, batch_size: int = None) -> Dict[str, Any]:
        """
        Run health checks on a batch of targets.
        
        Args:
            batch_size: Number of targets to check in this batch
            
        Returns:
            dict: Summary of health check results
        """
        if not HEALTH_MONITORING_SETTINGS['enabled']:
            return {'status': 'disabled', 'message': 'Health monitoring is disabled'}
        
        targets = self.get_targets_for_health_check(batch_size)
        
        if not targets:
            return {'status': 'no_targets', 'message': 'No targets need health checks'}
        
        results = {
            'checked': 0,
            'healthy': 0,
            'warning': 0,
            'critical': 0,
            'unknown': 0,
            'errors': 0,
            'status_changes': 0
        }
        
        logger.info(f"🏥 Starting health check batch for {len(targets)} targets")
        
        for target in targets:
            try:
                # Check target health
                health_result = self.check_target_health(target)
                
                # Update status in database
                old_status = target.health_status
                status_updated = self.update_target_health_status(target.id, health_result)
                
                if status_updated:
                    results['checked'] += 1
                    new_status = health_result.get('health_status', 'unknown')
                    results[new_status] += 1
                    
                    if old_status != new_status:
                        results['status_changes'] += 1
                else:
                    results['errors'] += 1
                    
            except Exception as e:
                logger.error(f"Error checking health for target {target.id}: {str(e)}")
                results['errors'] += 1
        
        logger.info(f"✅ Health check batch completed: {results}")
        return results