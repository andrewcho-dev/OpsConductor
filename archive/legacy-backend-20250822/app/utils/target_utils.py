"""
Target utility functions following the architecture plan.
CRITICAL: These functions must be used for ALL target data access.
"""
from typing import Optional, List, Dict, Any
from app.models.universal_target_models import UniversalTarget, TargetCommunicationMethod, TargetCredential


def getTargetIpAddress(target: UniversalTarget) -> Optional[str]:
    """
    Get primary IP address from target's communication methods.
    CRITICAL: IP addresses are ONLY stored in communication_methods[0].config.host
    
    Args:
        target: UniversalTarget instance with loaded communication_methods
        
    Returns:
        str: IP address or None if no primary method found
    """
    if not target.communication_methods:
        return None
    
    # Look for primary communication method first
    for method in target.communication_methods:
        if method.is_primary and method.is_active and method.config:
            return method.config.get('host')
    
    # If no primary method, get first active method
    for method in target.communication_methods:
        if method.is_active and method.config:
            return method.config.get('host')
    
    return None


def getTargetPrimaryCommunicationMethod(target: UniversalTarget) -> Optional[TargetCommunicationMethod]:
    """
    Get the primary communication method for a target.
    
    Args:
        target: UniversalTarget instance with loaded communication_methods
        
    Returns:
        TargetCommunicationMethod: Primary method or None if not found
    """
    if not target.communication_methods:
        return None
    
    # Look for primary communication method
    for method in target.communication_methods:
        if method.is_primary and method.is_active:
            return method
    
    # If no primary method, get first active method
    for method in target.communication_methods:
        if method.is_active:
            return method
    
    return None


def validateTargetCommunication(target: UniversalTarget) -> bool:
    """
    Ensure target has valid communication methods.
    CRITICAL: Every target must have communication methods.
    
    Args:
        target: UniversalTarget instance with loaded communication_methods
        
    Returns:
        bool: True if target has valid communication methods
    """
    if not target.communication_methods:
        return False
    
    # Check if at least one active communication method exists
    active_methods = [method for method in target.communication_methods if method.is_active]
    if not active_methods:
        return False
    
    # Check if at least one method has valid config with host
    for method in active_methods:
        if method.config and method.config.get('host'):
            return True
    
    return False


def getTargetSummary(target: UniversalTarget) -> Dict[str, Any]:
    """
    Get a summary of target information for display purposes.
    
    Args:
        target: UniversalTarget instance with loaded communication_methods
        
    Returns:
        dict: Summary information about the target
    """
    primary_method = getTargetPrimaryCommunicationMethod(target)
    ip_address = getTargetIpAddress(target)
    
    return {
        'id': target.id,
        'target_uuid': str(target.target_uuid) if target.target_uuid else None,
        'target_serial': target.target_serial,
        'name': target.name,
        'target_type': target.target_type,
        'os_type': target.os_type,
        'environment': target.environment,
        'status': target.status,
        'health_status': target.health_status,
        'ip_address': ip_address,
        'primary_method': primary_method.method_type if primary_method else None,
        'communication_methods_count': len(target.communication_methods) if target.communication_methods else 0,
        'is_valid': validateTargetCommunication(target),
        'created_at': target.created_at,
        'updated_at': target.updated_at
    }


def validateTargetCommunication(target: UniversalTarget) -> bool:
    """
    Validate if target has valid communication configuration.
    
    Args:
        target: UniversalTarget instance with loaded communication_methods
        
    Returns:
        bool: True if target has valid communication setup
    """
    if not target.communication_methods:
        return False
    
    # Check if there's at least one active communication method
    active_methods = [m for m in target.communication_methods if m.is_active]
    if not active_methods:
        return False
    
    # Check if there's a primary method
    primary_methods = [m for m in active_methods if m.is_primary]
    if not primary_methods:
        return False
    
    # Validate primary method has required configuration
    primary_method = primary_methods[0]
    if not primary_method.config or not primary_method.config.get('host'):
        return False
    
    return True


def getDefaultCommunicationMethodConfig(method_type: str, ip_address: str) -> Dict[str, Any]:
    """
    Get default configuration for a communication method type.
    
    Args:
        method_type: Type of communication method (ssh, winrm, snmp, telnet, rest_api, smtp, mysql, postgresql, mssql, oracle, sqlite, mongodb, redis, elasticsearch)
        ip_address: IP address of the target
        
    Returns:
        dict: Default configuration for the method type
    """
    if method_type == 'ssh':
        return {
            'host': ip_address,
            'port': 22,
            'timeout': 30,
            'key_algorithm': 'rsa'
        }
    elif method_type == 'winrm':
        return {
            'host': ip_address,
            'port': 5985,
            'timeout': 30,
            'transport': 'plaintext',
            'auth': 'basic'
        }
    elif method_type == 'snmp':
        return {
            'host': ip_address,
            'port': 161,
            'timeout': 10,
            'version': '2c',
            'community': 'public',
            'retries': 3
        }
    elif method_type == 'telnet':
        return {
            'host': ip_address,
            'port': 23,
            'timeout': 30,
            'encoding': 'utf-8',
            'newline': '\r\n'
        }
    elif method_type == 'rest_api':
        return {
            'host': ip_address,
            'port': 80,
            'protocol': 'http',
            'base_path': '/',
            'timeout': 30,
            'verify_ssl': True
        }
    elif method_type == 'smtp':
        return {
            'host': ip_address,
            'port': 587,
            'timeout': 30,
            'use_tls': True,
            'use_ssl': False,
            'auth_required': True,
            'encryption': 'starttls',  # starttls, ssl, none
            'server_type': 'smtp',     # smtp, exchange, gmail, outlook
            'domain': '',              # email domain for testing
            'test_recipient': '',      # test email address
            'connection_security': 'auto'  # auto, ssl, starttls, none
        }
    # Database configurations
    elif method_type == 'mysql':
        return {
            'host': ip_address,
            'port': 3306,
            'timeout': 30,
            'database': '',
            'charset': 'utf8mb4',
            'ssl_mode': 'disabled',  # disabled, preferred, required, verify_identity
            'connection_pool_size': 5
        }
    elif method_type == 'postgresql':
        return {
            'host': ip_address,
            'port': 5432,
            'timeout': 30,
            'database': 'postgres',
            'ssl_mode': 'prefer',  # disable, allow, prefer, require, verify-ca, verify-full
            'connection_pool_size': 5
        }
    elif method_type == 'mssql':
        return {
            'host': ip_address,
            'port': 1433,
            'timeout': 30,
            'database': 'master',
            'driver': 'ODBC Driver 17 for SQL Server',
            'encrypt': 'yes',  # yes, no
            'trust_server_certificate': 'no',  # yes, no
            'connection_pool_size': 5
        }
    elif method_type == 'oracle':
        return {
            'host': ip_address,
            'port': 1521,
            'timeout': 30,
            'service_name': '',  # Oracle service name
            'sid': '',           # Oracle SID (alternative to service_name)
            'connection_pool_size': 5
        }
    elif method_type == 'sqlite':
        return {
            'host': ip_address,  # Will be used as file path
            'port': 0,           # Not used for SQLite
            'timeout': 30,
            'database_path': '',  # Full path to SQLite database file
            'journal_mode': 'WAL',  # DELETE, TRUNCATE, PERSIST, MEMORY, WAL, OFF
            'synchronous': 'NORMAL'  # OFF, NORMAL, FULL, EXTRA
        }
    elif method_type == 'mongodb':
        return {
            'host': ip_address,
            'port': 27017,
            'timeout': 30,
            'database': 'admin',
            'auth_source': 'admin',
            'replica_set': '',  # Replica set name (optional)
            'ssl': False,
            'connection_pool_size': 10
        }
    elif method_type == 'redis':
        return {
            'host': ip_address,
            'port': 6379,
            'timeout': 30,
            'database': 0,  # Redis database number (0-15)
            'ssl': False,
            'connection_pool_size': 10,
            'max_connections': 50
        }
    elif method_type == 'elasticsearch':
        return {
            'host': ip_address,
            'port': 9200,
            'timeout': 30,
            'ssl': False,
            'verify_certs': True,
            'index_prefix': '',  # Optional index prefix
            'connection_pool_size': 10
        }
    else:
        return {
            'host': ip_address,
            'port': 22
        }


def validateMethodTypeForOS(method_type: str, os_type: str) -> bool:
    """
    Validate if a communication method type is appropriate for an OS type.
    
    Args:
        method_type: Communication method type (ssh, winrm, snmp, telnet, rest_api, smtp, mysql, postgresql, mssql, oracle, sqlite, mongodb, redis, elasticsearch)
        os_type: Operating system type (linux, windows)
        
    Returns:
        bool: True if method type is valid for OS type
    """
    # All supported communication methods
    valid_methods = [
        'ssh', 'winrm', 'snmp', 'telnet', 'rest_api', 'smtp',
        'mysql', 'postgresql', 'mssql', 'oracle', 'sqlite', 
        'mongodb', 'redis', 'elasticsearch'
    ]
    
    # Allow any valid method with any OS - let users decide what works for their environment
    return method_type in valid_methods


def generateMethodName(method_type: str) -> str:
    """
    Generate a unique method name for a communication method.
    Format: method_type_timestamp
    
    Args:
        method_type: Type of communication method
        
    Returns:
        str: Generated method name
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{method_type}_{timestamp}"