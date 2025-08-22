"""
Universal Target Service
Handles business logic for target management following the architecture plan.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
import logging

from app.models.universal_target_models import UniversalTarget, TargetCommunicationMethod, TargetCredential
# SerialService removed - using database defaults
from app.utils.target_utils import (
    getTargetIpAddress, 
    getTargetPrimaryCommunicationMethod, 
    validateTargetCommunication,
    getTargetSummary,
    getDefaultCommunicationMethodConfig,
    validateMethodTypeForOS,
    generateMethodName
)
from app.utils.encryption_utils import encrypt_password_credentials, encrypt_ssh_key_credentials, decrypt_credentials
from app.utils.connection_test_utils import perform_connection_test
from app.core.audit_utils import log_audit_event_sync
from app.domains.audit.services.audit_service import AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class UniversalTargetService:
    """Service class for Universal Target operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _check_duplicate_active_ip(self, ip_address: str) -> Optional[UniversalTarget]:
        """
        Check if an IP address is already in use by an active target.
        
        Args:
            ip_address: IP address to check
            
        Returns:
            UniversalTarget: Existing target using this IP, or None if available
        """
        # Query all active targets with their communication methods
        active_targets = self.db.query(UniversalTarget)\
            .options(joinedload(UniversalTarget.communication_methods))\
            .filter(
                and_(
                    UniversalTarget.is_active == True,
                    UniversalTarget.status == 'active'
                )
            ).all()
        
        # Check each target's communication methods for the IP address
        for target in active_targets:
            for method in target.communication_methods:
                if method.is_active and method.config and method.config.get('host') == ip_address:
                    return target
        
        return None
    
    def create_target(
        self, 
        name: str, 
        os_type: str, 
        ip_address: str,
        method_type: str,
        username: str,
        password: str = None,
        ssh_key: str = None,
        ssh_passphrase: str = None,
        description: str = None,
        environment: str = "development",
        location: str = None,
        data_center: str = None,
        region: str = None,
        # SMTP-specific parameters
        encryption: str = None,
        server_type: str = None,
        domain: str = None,
        test_recipient: str = None,
        connection_security: str = None,
        # REST API-specific parameters
        protocol: str = None,
        base_path: str = None,
        verify_ssl: bool = None,
        # SNMP-specific parameters
        snmp_version: str = None,
        snmp_community: str = None,
        snmp_retries: int = None,
        # SNMPv3-specific parameters
        snmp_security_level: str = None,
        snmp_auth_protocol: str = None,
        snmp_privacy_protocol: str = None,
        # Database-specific parameters
        database: str = None,
        charset: str = None,
        ssl_mode: str = None,
        driver: str = None,
        encrypt: str = None,
        service_name: str = None,
        sid: str = None,
        database_path: str = None,
        auth_source: str = None,
        ssl: bool = None,
        verify_certs: bool = None
    ) -> UniversalTarget:
        """
        Create a new universal target with communication method and credentials.
        This is an atomic operation - target, communication method, and credentials are created together.
        
        Args:
            name: Unique target name
            os_type: Operating system type (linux, windows)
            ip_address: IP address for the target
            method_type: Communication method type (ssh, winrm)
            username: Username for authentication
            password: Password for authentication (for password auth)
            ssh_key: SSH private key content (for key auth)
            ssh_passphrase: SSH key passphrase (optional)
            description: Optional target description
            environment: Target environment
            location: Physical location
            data_center: Data center name
            region: Geographic region
            
        Returns:
            UniversalTarget: Created target with communication method and credentials
            
        Raises:
            ValueError: If validation fails or target name already exists
        """
        # Validate inputs
        if not validateMethodTypeForOS(method_type, os_type):
            raise ValueError(f"Communication method '{method_type}' is not valid for OS type '{os_type}'")
        
        # Check if IP address is already in use by an active target
        existing_ip_target = self._check_duplicate_active_ip(ip_address)
        if existing_ip_target:
            raise ValueError(f"IP address '{ip_address}' is already in use by active target '{existing_ip_target.name}'")
        
        # Validate credential inputs based on method type
        if method_type in ['ssh', 'winrm', 'telnet', 'mysql', 'postgresql', 'mssql', 'oracle', 'sqlite', 'mongodb', 'redis', 'elasticsearch']:
            # These methods require traditional authentication
            if method_type == 'ssh' and ssh_key and not password:
                credential_type = 'ssh_key'
            elif password and not ssh_key:
                credential_type = 'password'
            else:
                raise ValueError("SSH/WinRM/Telnet/Database methods require either password or SSH key for authentication")
        elif method_type == 'snmp':
            # SNMP uses community strings (stored as password)
            if not password:
                raise ValueError("SNMP method requires community string (provided as password)")
            credential_type = 'snmp_community'
        elif method_type == 'rest_api':
            # REST API can use various auth methods (API key, basic auth, etc.)
            if not password and not ssh_key:
                raise ValueError("REST API method requires authentication (API key as password or token as ssh_key)")
            credential_type = 'api_key' if password else 'api_token'
        elif method_type == 'smtp':
            # SMTP requires username/password for authentication
            if not password:
                raise ValueError("SMTP method requires password for authentication")
            credential_type = 'password'
        else:
            raise ValueError(f"Unknown method type: {method_type}")
        
        try:
            # Create the target (target_serial will be auto-generated by database)
            target = UniversalTarget(
                name=name,
                target_type="system",  # Simplified version only supports system targets
                description=description,
                os_type=os_type,
                environment=environment,
                location=location,
                data_center=data_center,
                region=region,
                status="active",
                health_status="unknown"
            )
            
            self.db.add(target)
            self.db.flush()  # Get the target ID
            
            # Create communication method
            method_config = getDefaultCommunicationMethodConfig(method_type, ip_address)
            
            # Add SMTP-specific configuration if provided
            if method_type == 'smtp':
                if encryption:
                    method_config['encryption'] = encryption
                if server_type:
                    method_config['server_type'] = server_type
                if domain:
                    method_config['domain'] = domain
                if test_recipient:
                    method_config['test_recipient'] = test_recipient
                if connection_security:
                    method_config['connection_security'] = connection_security
            
            # Add REST API-specific configuration if provided
            elif method_type == 'rest_api':
                if protocol:
                    method_config['protocol'] = protocol
                if base_path:
                    method_config['base_path'] = base_path
                if verify_ssl is not None:
                    method_config['verify_ssl'] = verify_ssl
            
            # Add SNMP-specific configuration if provided
            elif method_type == 'snmp':
                if snmp_version:
                    method_config['version'] = snmp_version
                if snmp_community:
                    method_config['community'] = snmp_community
                if snmp_retries is not None:
                    method_config['retries'] = snmp_retries
                # SNMPv3-specific configuration
                if snmp_security_level:
                    method_config['security_level'] = snmp_security_level
                if snmp_auth_protocol:
                    method_config['auth_protocol'] = snmp_auth_protocol
                if snmp_privacy_protocol:
                    method_config['privacy_protocol'] = snmp_privacy_protocol
            
            # Add database-specific configuration if provided
            elif method_type == 'mysql':
                if database:
                    method_config['database'] = database
                if charset:
                    method_config['charset'] = charset
                if ssl_mode:
                    method_config['ssl_mode'] = ssl_mode
            elif method_type == 'postgresql':
                if database:
                    method_config['database'] = database
                if ssl_mode:
                    method_config['ssl_mode'] = ssl_mode
            elif method_type == 'mssql':
                if database:
                    method_config['database'] = database
                if driver:
                    method_config['driver'] = driver
                if encrypt:
                    method_config['encrypt'] = encrypt
            elif method_type == 'oracle':
                if service_name:
                    method_config['service_name'] = service_name
                if sid:
                    method_config['sid'] = sid
            elif method_type == 'sqlite':
                if database_path:
                    method_config['database_path'] = database_path
            elif method_type == 'mongodb':
                if database:
                    method_config['database'] = database
                if auth_source:
                    method_config['auth_source'] = auth_source
            elif method_type == 'redis':
                if database is not None:
                    method_config['database'] = database
            elif method_type == 'elasticsearch':
                if ssl is not None:
                    method_config['ssl'] = ssl
                if verify_certs is not None:
                    method_config['verify_certs'] = verify_certs
            
            method_name = generateMethodName(method_type)
            
            communication_method = TargetCommunicationMethod(
                target_id=target.id,
                method_type=method_type,
                method_name=method_name,
                is_primary=True,  # First method is always primary
                is_active=True,
                priority=1,
                config=method_config
            )
            
            self.db.add(communication_method)
            self.db.flush()  # Get the communication method ID
            
            # Create credentials based on type
            if credential_type in ['password', 'snmp_community']:
                encrypted_creds = encrypt_password_credentials(username, password)
            elif credential_type == 'ssh_key':
                encrypted_creds = encrypt_ssh_key_credentials(username, ssh_key, ssh_passphrase)
            elif credential_type == 'api_key':
                # API key stored as password with username
                encrypted_creds = encrypt_password_credentials(username, password)
            elif credential_type == 'api_token':
                # API token stored as ssh_key field
                encrypted_creds = encrypt_ssh_key_credentials(username, ssh_key, None)
            else:
                raise ValueError(f"Unknown credential type: {credential_type}")
            
            credential = TargetCredential(
                communication_method_id=communication_method.id,
                credential_type=credential_type,
                credential_name=f"{username}_{credential_type}",
                is_primary=True,
                is_active=True,
                encrypted_credentials=encrypted_creds
            )
            
            self.db.add(credential)
            self.db.commit()
            
            # Log audit event for target creation
            log_audit_event_sync(
                db=self.db,
                event_type=AuditEventType.TARGET_CREATED,
                user_id=None,  # Will be set by the API endpoint
                resource_type="target",
                resource_id=str(target.id),
                action="create",
                details={
                    "target_name": target.name,
                    "target_type": target.target_type,
                    "os_type": target.os_type,
                    "environment": target.environment,
                    "method_type": method_type,
                    "ip_address": ip_address,
                    "username": username,
                    "credential_type": credential_type
                },
                severity=AuditSeverity.MEDIUM
            )
            
            # Return target with relationships loaded
            return self.get_target_by_id(target.id)
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to create target: {str(e)}")
    
    def get_all_targets(self) -> List[UniversalTarget]:
        """
        Get all active targets with their communication methods and credentials loaded.
        
        Returns:
            List[UniversalTarget]: List of all active targets
        """
        return self.db.query(UniversalTarget)\
            .options(
                joinedload(UniversalTarget.communication_methods)
                .joinedload(TargetCommunicationMethod.credentials)
            )\
            .filter(UniversalTarget.is_active == True)\
            .order_by(UniversalTarget.name)\
            .all()
    
    def get_target_by_id(self, target_id: int) -> Optional[UniversalTarget]:
        """
        Get a target by ID with relationships loaded.
        
        Args:
            target_id: Target ID
            
        Returns:
            UniversalTarget: Target if found, None otherwise
        """
        return self.db.query(UniversalTarget)\
            .options(
                joinedload(UniversalTarget.communication_methods)
                .joinedload(TargetCommunicationMethod.credentials)
            )\
            .filter(
                and_(
                    UniversalTarget.id == target_id,
                    UniversalTarget.is_active == True
                )
            )\
            .first()
    
    def get_target_by_uuid(self, target_uuid: str) -> Optional[UniversalTarget]:
        """
        Get a target by UUID (permanent identifier) with relationships loaded.
        
        Args:
            target_uuid: Target UUID
            
        Returns:
            UniversalTarget: Target if found, None otherwise
        """
        return self.db.query(UniversalTarget)\
            .options(
                joinedload(UniversalTarget.communication_methods)
                .joinedload(TargetCommunicationMethod.credentials)
            )\
            .filter(
                and_(
                    UniversalTarget.target_uuid == target_uuid,
                    UniversalTarget.is_active == True
                )
            )\
            .first()
    
    def get_target_by_serial(self, target_serial: str) -> Optional[UniversalTarget]:
        """
        Get a target by serial number (human-readable permanent identifier) with relationships loaded.
        
        Args:
            target_serial: Target serial number
            
        Returns:
            UniversalTarget: Target if found, None otherwise
        """
        return self.db.query(UniversalTarget)\
            .options(
                joinedload(UniversalTarget.communication_methods)
                .joinedload(TargetCommunicationMethod.credentials)
            )\
            .filter(
                and_(
                    UniversalTarget.target_serial == target_serial,
                    UniversalTarget.is_active == True
                )
            )\
            .first()
    
    def get_target_by_name(self, name: str) -> Optional[UniversalTarget]:
        """
        Get a target by name with relationships loaded.
        
        Args:
            name: Target name
            
        Returns:
            UniversalTarget: Target if found, None otherwise
        """
        return self.db.query(UniversalTarget)\
            .options(
                joinedload(UniversalTarget.communication_methods)
                .joinedload(TargetCommunicationMethod.credentials)
            )\
            .filter(
                and_(
                    UniversalTarget.name == name,
                    UniversalTarget.is_active == True
                )
            )\
            .first()
    
    def get_target_by_host(self, host: str) -> Optional[UniversalTarget]:
        """
        Get a target by host/IP address.
        
        Args:
            host: Host IP address or hostname
            
        Returns:
            UniversalTarget: Target if found, None otherwise
        """
        return self.db.query(UniversalTarget)\
            .join(TargetCommunicationMethod)\
            .filter(
                and_(
                    TargetCommunicationMethod.config.op('->')('host').astext == host,
                    UniversalTarget.is_active == True
                )
            )\
            .first()
    
    def update_target(
        self, 
        target_id: int, 
        name: str = None,
        description: str = None,
        os_type: str = None,
        environment: str = None,
        location: str = None,
        data_center: str = None,
        region: str = None,
        status: str = None
    ) -> Optional[UniversalTarget]:
        """
        Update target basic information (not communication methods).
        
        Args:
            target_id: Target ID to update
            name: New target name (must be unique)
            description: New description
            os_type: New operating system type
            environment: New environment
            location: New location
            data_center: New data center
            region: New region
            status: New status
            
        Returns:
            UniversalTarget: Updated target or None if not found
            
        Raises:
            ValueError: If validation fails
        """
        target = self.get_target_by_id(target_id)
        if not target:
            return None
        
        try:
            # Update name if provided
            if name:
                target.name = name
            
            # Update other fields if provided
            if description is not None:
                target.description = description
            if os_type:
                target.os_type = os_type
            if environment:
                target.environment = environment
            if location is not None:
                target.location = location
            if data_center is not None:
                target.data_center = data_center
            if region is not None:
                target.region = region
            if status:
                target.status = status
            
            self.db.commit()
            
            # Log audit event for target update
            log_audit_event_sync(
                db=self.db,
                event_type=AuditEventType.TARGET_UPDATED,
                user_id=None,  # Will be set by the API endpoint
                resource_type="target",
                resource_id=str(target_id),
                action="update",
                details={
                    "target_name": target.name,
                    "updated_fields": {
                        "name": name if name else None,
                        "description": description if description is not None else None,
                        "os_type": os_type if os_type else None,
                        "environment": environment if environment else None,
                        "location": location if location is not None else None,
                        "data_center": data_center if data_center is not None else None,
                        "region": region if region is not None else None,
                        "status": status if status else None
                    }
                },
                severity=AuditSeverity.MEDIUM
            )
            
            return self.get_target_by_id(target_id)
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to update target: {str(e)}")
    
    def delete_target(self, target_id: int) -> bool:
        """
        Soft delete a target (set is_active = False).
        
        Args:
            target_id: Target ID to delete
            
        Returns:
            bool: True if target was deleted, False if not found
        """
        target = self.get_target_by_id(target_id)
        if not target:
            return False
        
        try:
            # Store target info for audit logging before deletion
            target_info = {
                "target_name": target.name,
                "target_type": target.target_type,
                "os_type": target.os_type,
                "environment": target.environment
            }
            
            target.is_active = False
            self.db.commit()
            
            # Log audit event for target deletion
            log_audit_event_sync(
                db=self.db,
                event_type=AuditEventType.TARGET_DELETED,
                user_id=None,  # Will be set by the API endpoint
                resource_type="target",
                resource_id=str(target_id),
                action="delete",
                details=target_info,
                severity=AuditSeverity.HIGH
            )
            
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete target {target_id}: {str(e)}")
            return False
    
    def get_targets_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary information for all targets using utility functions.
        
        Returns:
            List[Dict]: List of target summaries
        """
        targets = self.get_all_targets()
        return [getTargetSummary(target) for target in targets]
    
    def test_target_connection(self, target_id: int) -> Dict[str, Any]:
        """
        Test connection to a target using the primary communication method.
        
        Args:
            target_id: Target ID to test
            
        Returns:
            dict: Connection test results
        """
        target = self.get_target_by_id(target_id)
        if not target:
            return {'success': False, 'message': 'Target not found'}
        
        if not validateTargetCommunication(target):
            return {'success': False, 'message': 'Invalid target communication configuration'}
        
        # Get primary communication method
        primary_method = getTargetPrimaryCommunicationMethod(target)
        if not primary_method:
            return {'success': False, 'message': 'No primary communication method found'}
        
        # Get primary credentials for the method
        primary_credential = None
        for credential in primary_method.credentials:
            if credential.is_primary and credential.is_active:
                primary_credential = credential
                break
        
        if not primary_credential:
            # If no primary credential, get first active credential
            for credential in primary_method.credentials:
                if credential.is_active:
                    primary_credential = credential
                    break
        
        if not primary_credential:
            return {'success': False, 'message': 'No active credentials found for target'}
        
        try:
            # Decrypt credentials
            credentials_data = decrypt_credentials(primary_credential.encrypted_credentials)
            
            # Perform the actual connection test
            result = perform_connection_test(target, primary_method, credentials_data)
            
            # Add additional context to the result
            result['ip_address'] = getTargetIpAddress(target)
            result['method_type'] = primary_method.method_type
            result['target_name'] = target.name
            
            # Log audit event for connection test
            event_type = AuditEventType.TARGET_CONNECTION_SUCCESS if result.get('success') else AuditEventType.TARGET_CONNECTION_FAILURE
            severity = AuditSeverity.INFO if result.get('success') else AuditSeverity.MEDIUM
            
            log_audit_event_sync(
                db=self.db,
                event_type=event_type,
                user_id=None,  # Will be set by the API endpoint
                resource_type="target",
                resource_id=str(target_id),
                action="connection_test",
                details={
                    "target_name": target.name,
                    "ip_address": result['ip_address'],
                    "method_type": result['method_type'],
                    "success": result.get('success', False),
                    "message": result.get('message', ''),
                    "latency_ms": result.get('latency_ms')
                },
                severity=severity
            )
            
            return result
            
        except Exception as e:
            result = {
                'success': False, 
                'message': f'Connection test failed: {str(e)}',
                'ip_address': getTargetIpAddress(target),
                'method_type': primary_method.method_type
            }
            
            # Log audit event for connection test failure
            log_audit_event_sync(
                db=self.db,
                event_type=AuditEventType.TARGET_CONNECTION_FAILURE,
                user_id=None,  # Will be set by the API endpoint
                resource_type="target",
                resource_id=str(target_id),
                action="connection_test",
                details={
                    "target_name": target.name,
                    "ip_address": result['ip_address'],
                    "method_type": result['method_type'],
                    "success": False,
                    "message": result['message'],
                    "error": str(e)
                },
                severity=AuditSeverity.MEDIUM
            )
            
            return result
    
    def update_target_comprehensive(
        self,
        target_id: int,
        name: str = None,
        description: str = None,
        os_type: str = None,
        environment: str = None,
        location: str = None,
        data_center: str = None,
        region: str = None,
        status: str = None,
        ip_address: str = None,
        communication_methods: List[Dict] = None,
        # Legacy single method support
        method_type: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        ssh_key: str = None,
        ssh_passphrase: str = None
    ) -> Optional[UniversalTarget]:
        """
        Comprehensive update of target including basic info, communication methods, and credentials.
        
        Args:
            target_id: Target ID to update
            Basic info fields: name, description, os_type, environment, location, data_center, region, status
            Communication method fields: ip_address, method_type, port
            Credential fields: username, password, ssh_key, ssh_passphrase
            
        Returns:
            UniversalTarget: Updated target or None if not found
            
        Raises:
            ValueError: If validation fails
        """
        from ..utils.encryption_utils import encrypt_password_credentials, encrypt_ssh_key_credentials
        from ..utils.target_utils import getDefaultCommunicationMethodConfig, generateMethodName
        
        target = self.get_target_by_id(target_id)
        if not target:
            return None
            
        try:
            # Update basic target information
            if name:
                target.name = name
            
            # Update other basic fields
            if description is not None:
                target.description = description
            if os_type:
                target.os_type = os_type
            if environment:
                target.environment = environment
            if location is not None:
                target.location = location
            if data_center is not None:
                target.data_center = data_center
            if region is not None:
                target.region = region
            if status:
                target.status = status
            
            # Handle multiple communication methods (NEW APPROACH)
            if communication_methods:
                print(f"Processing {len(communication_methods)} communication methods")
                
                # First, handle primary method changes
                current_primary = None
                new_primary = None
                
                for method_data in communication_methods:
                    if method_data.get('is_primary'):
                        new_primary = method_data
                        break
                
                # Find current primary method
                for method in target.communication_methods:
                    if method.is_primary:
                        current_primary = method
                        break
                
                # Update primary flags if changed
                if new_primary and current_primary:
                    method_id = new_primary.get('id')
                    if method_id and method_id != current_primary.id:
                        print(f"Changing primary method from {current_primary.id} to {method_id}")
                        
                        # Unset current primary
                        current_primary.is_primary = False
                        
                        # Set new primary
                        for method in target.communication_methods:
                            if method.id == method_id:
                                method.is_primary = True
                                print(f"Set method {method_id} as primary")
                                break
                
                # Handle method creation and updates
                for method_data in communication_methods:
                    method_id = method_data.get('id')
                    if method_id:
                        # Update existing method
                        for method in target.communication_methods:
                            if method.id == method_id:
                                # Update config if provided
                                if 'config' in method_data:
                                    method.config = method_data['config']
                                
                                # Update credentials if provided
                                if method_data.get('credentials'):
                                    # Handle credential updates
                                    pass  # TODO: Implement credential updates if needed
                                break
                    else:
                        # Create new method
                        print(f"Creating new communication method: {method_data['method_type']}")
                        
                        # Extract credentials from the method data
                        credentials = method_data.get('credentials', [])
                        username = None
                        password = None
                        ssh_key = None
                        ssh_passphrase = None
                        credential_type = 'password'
                        
                        if credentials and len(credentials) > 0:
                            cred = credentials[0]
                            credential_type = cred.get('credential_type', 'password')
                            encrypted_creds = cred.get('encrypted_credentials', {})
                            
                            if credential_type == 'password':
                                username = encrypted_creds.get('username')
                                password = encrypted_creds.get('password')
                            elif credential_type == 'ssh_key':
                                username = encrypted_creds.get('username')
                                ssh_key = encrypted_creds.get('ssh_key')
                                ssh_passphrase = encrypted_creds.get('ssh_passphrase')
                        
                        # Add the new communication method
                        new_method = self.add_communication_method(
                            target_id=target_id,
                            method_type=method_data['method_type'],
                            config=method_data['config'],
                            is_primary=method_data.get('is_primary', False),
                            is_active=method_data.get('is_active', True),
                            credential_type=credential_type,
                            username=username,
                            password=password,
                            ssh_key=ssh_key,
                            ssh_passphrase=ssh_passphrase
                        )
                        
                        if new_method:
                            print(f"Successfully created communication method: {new_method.id}")
                        else:
                            print(f"Failed to create communication method: {method_data['method_type']}")
            
            # Legacy single method support (for backward compatibility)
            elif any([ip_address, method_type, port]):
                primary_method = target.communication_methods[0] if target.communication_methods else None
                if not primary_method:
                    raise ValueError("No communication method found to update")
                
                # Check for duplicate IP address if IP is being changed
                if ip_address and primary_method.config.get('host') != ip_address:
                    existing_ip_target = self._check_duplicate_active_ip(ip_address)
                    if existing_ip_target and existing_ip_target.id != target_id:
                        raise ValueError(f"IP address '{ip_address}' is already in use by active target '{existing_ip_target.name}'")
                
                # Update method config
                current_config = primary_method.config or {}
                if ip_address:
                    current_config['host'] = ip_address
                if port:
                    current_config['port'] = port
                if method_type and method_type != primary_method.method_type:
                    # If method type changes, recreate config with defaults
                    current_config = getDefaultCommunicationMethodConfig(method_type, ip_address or current_config.get('host'))
                    primary_method.method_type = method_type
                    primary_method.method_name = generateMethodName(method_type)
                
                primary_method.config = current_config
            
            # Legacy credential updates
            if any([username, password, ssh_key]):
                # Filter out placeholder values and empty strings
                def is_real_credential_value(value):
                    if not value:
                        return False
                    # Check for placeholder values that frontend sends
                    placeholder_patterns = [
                        '[Current Username - Hidden for Security]',
                        '[Current Password - Hidden for Security]', 
                        '[Current SSH Key - Hidden for Security]',
                        '[Current SSH Key User]'
                    ]
                    return not any(pattern in str(value) for pattern in placeholder_patterns)
                
                real_username = username if is_real_credential_value(username) else None
                real_password = password if is_real_credential_value(password) else None
                real_ssh_key = ssh_key if is_real_credential_value(ssh_key) else None
                
                if any([real_password, real_ssh_key]):
                    # Only update credentials if we have new password or SSH key
                    primary_method = target.communication_methods[0] if target.communication_methods else None
                    if not primary_method:
                        raise ValueError("No communication method found to update credentials")
                    
                    primary_credential = primary_method.credentials[0] if primary_method.credentials else None
                    if not primary_credential:
                        raise ValueError("No credentials found to update")
                    
                    # Determine credential type and encrypt new credentials
                    if real_ssh_key:
                        credential_type = 'ssh_key'
                        encrypted_creds = encrypt_ssh_key_credentials(
                            real_username or 'root', 
                            real_ssh_key, 
                            ssh_passphrase
                        )
                        primary_credential.credential_type = credential_type
                        primary_credential.credential_name = f"{real_username or 'root'}_{credential_type}"
                        primary_credential.encrypted_credentials = encrypted_creds
                    elif real_password:
                        credential_type = 'password'
                        encrypted_creds = encrypt_password_credentials(
                            real_username or primary_credential.credential_name.split('_')[0], 
                            real_password
                        )
                        primary_credential.credential_type = credential_type
                        primary_credential.credential_name = f"{real_username or primary_credential.credential_name.split('_')[0]}_{credential_type}"
                        primary_credential.encrypted_credentials = encrypted_creds
            
            self.db.commit()
            return self.get_target_by_id(target_id)
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to update target comprehensively: {str(e)}")
    
    def add_communication_method(
        self,
        target_id: int,
        method_type: str,
        config: Dict[str, Any],
        is_primary: bool = False,
        is_active: bool = True,
        priority: int = 1,
        credential_type: str = "password",
        username: str = None,
        password: str = None,
        ssh_key: str = None,
        ssh_passphrase: str = None
    ) -> Optional[TargetCommunicationMethod]:
        """
        Add a new communication method to an existing target.
        
        Args:
            target_id: Target ID to add method to
            method_type: Communication method type (ssh, winrm)
            config: Method configuration including host IP
            is_primary: Whether this is the primary method
            is_active: Whether this method is active
            priority: Priority of this method
            credential_type: Type of credential (password, ssh_key)
            username: Username for authentication
            password: Password for authentication (for password auth)
            ssh_key: SSH private key content (for key auth)
            ssh_passphrase: SSH key passphrase (optional)
            
        Returns:
            TargetCommunicationMethod: Created communication method with credentials
            
        Raises:
            ValueError: If validation fails or target not found
        """
        try:
            # Get target to validate it exists
            target = self.get_target_by_id(target_id)
            if not target:
                raise ValueError(f"Target with ID {target_id} not found")
            
            # Validate method type for OS
            if not validateMethodTypeForOS(method_type, target.os_type):
                raise ValueError(f"Communication method '{method_type}' is not valid for OS type '{target.os_type}'")
            
            # If this is set as primary, unset other primary methods
            if is_primary:
                for existing_method in target.communication_methods:
                    if existing_method.is_primary:
                        existing_method.is_primary = False
            
            # Create communication method
            method_name = generateMethodName(method_type)
            
            communication_method = TargetCommunicationMethod(
                target_id=target_id,
                method_type=method_type,
                method_name=method_name,
                is_primary=is_primary,
                is_active=is_active,
                priority=priority,
                config=config
            )
            
            self.db.add(communication_method)
            self.db.flush()  # Get the communication method ID
            
            # Create credentials if provided
            if username:
                if credential_type == 'password' and password:
                    encrypted_creds = encrypt_password_credentials(username, password)
                elif credential_type == 'ssh_key' and ssh_key:
                    encrypted_creds = encrypt_ssh_key_credentials(username, ssh_key, ssh_passphrase)
                else:
                    raise ValueError(f"Missing credentials for {credential_type} authentication")
                
                credential = TargetCredential(
                    communication_method_id=communication_method.id,
                    credential_type=credential_type,
                    credential_name=f"{username}_{credential_type}",
                    is_primary=True,
                    is_active=True,
                    encrypted_credentials=encrypted_creds
                )
                
                self.db.add(credential)
            
            self.db.commit()
            
            # Return the created method with relationships loaded
            return self.db.query(TargetCommunicationMethod)\
                .options(joinedload(TargetCommunicationMethod.credentials))\
                .filter(TargetCommunicationMethod.id == communication_method.id)\
                .first()
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to add communication method: {str(e)}")
    
    def update_communication_method(
        self,
        target_id: int,
        method_id: int,
        method_type: str = None,
        config: Dict[str, Any] = None,
        is_primary: bool = None,
        is_active: bool = None,
        priority: int = None
    ) -> Optional[TargetCommunicationMethod]:
        """
        Update an existing communication method.
        
        Args:
            target_id: Target ID
            method_id: Communication method ID to update
            method_type: New method type (optional)
            config: New method configuration (optional)
            is_primary: New primary status (optional)
            is_active: New active status (optional)
            priority: New priority (optional)
            
        Returns:
            TargetCommunicationMethod: Updated communication method
            
        Raises:
            ValueError: If validation fails or method not found
        """
        try:
            # Get the communication method
            method = self.db.query(TargetCommunicationMethod)\
                .filter(
                    and_(
                        TargetCommunicationMethod.id == method_id,
                        TargetCommunicationMethod.target_id == target_id
                    )
                )\
                .first()
            
            if not method:
                raise ValueError(f"Communication method with ID {method_id} not found for target {target_id}")
            
            # Update fields if provided
            if method_type is not None:
                # Validate method type for OS
                target = self.get_target_by_id(target_id)
                if not validateMethodTypeForOS(method_type, target.os_type):
                    raise ValueError(f"Communication method '{method_type}' is not valid for OS type '{target.os_type}'")
                method.method_type = method_type
            
            if config is not None:
                method.config = config
            
            if is_primary is not None:
                if is_primary:
                    # Unset other primary methods for this target
                    target = self.get_target_by_id(target_id)
                    for existing_method in target.communication_methods:
                        if existing_method.id != method_id and existing_method.is_primary:
                            existing_method.is_primary = False
                method.is_primary = is_primary
            
            if is_active is not None:
                method.is_active = is_active
            
            if priority is not None:
                method.priority = priority
            
            self.db.commit()
            
            # Return the updated method with relationships loaded
            return self.db.query(TargetCommunicationMethod)\
                .options(joinedload(TargetCommunicationMethod.credentials))\
                .filter(TargetCommunicationMethod.id == method_id)\
                .first()
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to update communication method: {str(e)}")
    
    def delete_communication_method(
        self,
        target_id: int,
        method_id: int
    ) -> bool:
        """
        Delete a communication method.
        
        Args:
            target_id: Target ID
            method_id: Communication method ID to delete
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            ValueError: If method is primary or not found
        """
        try:
            # Get the communication method
            method = self.db.query(TargetCommunicationMethod)\
                .filter(
                    and_(
                        TargetCommunicationMethod.id == method_id,
                        TargetCommunicationMethod.target_id == target_id
                    )
                )\
                .first()
            
            if not method:
                return False
            
            # Don't allow deleting the primary method if it's the only method
            target = self.get_target_by_id(target_id)
            if method.is_primary and len(target.communication_methods) == 1:
                raise ValueError("Cannot delete the only communication method for a target")
            
            # If deleting primary method, set another method as primary
            if method.is_primary and len(target.communication_methods) > 1:
                for other_method in target.communication_methods:
                    if other_method.id != method_id and other_method.is_active:
                        other_method.is_primary = True
                        break
            
            # Delete the method (credentials will be deleted by cascade)
            self.db.delete(method)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to delete communication method: {str(e)}")
    
    def test_communication_method(self, target_id: int, method_id: int) -> Dict[str, Any]:
        """
        Test connection using a specific communication method.
        
        Args:
            target_id: Target ID
            method_id: Communication method ID to test
            
        Returns:
            dict: Connection test results for this specific method
        """
        try:
            # Get the target
            target = self.get_target_by_id(target_id)
            if not target:
                return {'success': False, 'message': 'Target not found'}
            
            # Get the specific communication method
            method = None
            for comm_method in target.communication_methods:
                if comm_method.id == method_id:
                    method = comm_method
                    break
            
            if not method:
                return {'success': False, 'message': f'Communication method with ID {method_id} not found. Available methods: {[m.id for m in target.communication_methods]}'}
            
            if not method.is_active:
                return {'success': False, 'message': 'Communication method is inactive'}
            
            # Get primary credential for this method
            primary_credential = None
            for credential in method.credentials:
                if credential.is_primary and credential.is_active:
                    primary_credential = credential
                    break
            
            if not primary_credential:
                # If no primary credential, get first active credential
                for credential in method.credentials:
                    if credential.is_active:
                        primary_credential = credential
                        break
            
            if not primary_credential:
                return {'success': False, 'message': 'No active credentials found for this method'}
            
            # Decrypt credentials
            try:
                decrypted_creds = decrypt_credentials(primary_credential.encrypted_credentials)
            except Exception as e:
                return {'success': False, 'message': f'Failed to decrypt credentials: {str(e)}'}
            
            # Perform connection test using this specific method and credentials
            test_result = perform_connection_test(
                target=target,
                method=method,
                credentials_data=decrypted_creds
            )
            
            return {
                'success': test_result.get('success', False),
                'message': test_result.get('message', 'Connection test completed'),
                'method_type': method.method_type,
                'method_id': method.id,
                'method_name': method.method_name,
                'host': method.config.get('host'),
                'port': method.config.get('port'),
                'credential_type': primary_credential.credential_type,
                'username': decrypted_creds.get('username', 'unknown'),
                'test_duration': test_result.get('duration', 0),
                'details': test_result.get('details', {}),
                'debug_info': f'Testing method ID {method.id} of type {method.method_type} for target {target.id}'
            }
            
        except Exception as e:
            return {
                'success': False, 
                'message': f'Connection test failed: {str(e)}',
                'method_id': method_id
            }