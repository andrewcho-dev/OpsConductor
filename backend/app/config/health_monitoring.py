"""
Health Monitoring Configuration
Configurable settings for target health monitoring system.
"""
from typing import Dict, Any
import os

# Default health check intervals (in seconds)
DEFAULT_HEALTH_CHECK_INTERVALS = {
    'production': {
        'healthy': 300,      # 5 minutes
        'warning': 180,      # 3 minutes  
        'critical': 60,      # 1 minute
        'unknown': 300       # 5 minutes
    },
    'staging': {
        'healthy': 600,      # 10 minutes
        'warning': 300,      # 5 minutes
        'critical': 180,     # 3 minutes
        'unknown': 600       # 10 minutes
    },
    'development': {
        'healthy': 1800,     # 30 minutes
        'warning': 900,      # 15 minutes
        'critical': 300,     # 5 minutes
        'unknown': 1800      # 30 minutes
    },
    'testing': {
        'healthy': 900,      # 15 minutes
        'warning': 600,      # 10 minutes
        'critical': 300,     # 5 minutes
        'unknown': 900       # 15 minutes
    }
}

# Health check timeout settings
HEALTH_CHECK_TIMEOUTS = {
    'ssh': 15,        # SSH connection timeout (seconds)
    'winrm': 20,      # WinRM connection timeout (seconds)
    'snmp': 10,       # SNMP connection timeout (seconds)
    'telnet': 15,     # Telnet connection timeout (seconds)
    'rest_api': 30,   # REST API request timeout (seconds)
    'smtp': 20,       # SMTP connection timeout (seconds)
    'default': 15     # Default timeout
}

# Health status thresholds
HEALTH_THRESHOLDS = {
    'response_time_warning': 5.0,    # Seconds - above this is warning
    'response_time_critical': 10.0,  # Seconds - above this is critical
    'consecutive_failures_warning': 2,   # Failures before warning
    'consecutive_failures_critical': 3,  # Failures before critical
    'recovery_success_count': 2      # Successes needed to recover from critical
}

# Global health monitoring settings
HEALTH_MONITORING_SETTINGS = {
    'enabled': os.getenv('HEALTH_MONITORING_ENABLED', 'true').lower() == 'true',
    'batch_size': int(os.getenv('HEALTH_CHECK_BATCH_SIZE', '10')),  # Targets per batch
    'max_concurrent_checks': int(os.getenv('HEALTH_MAX_CONCURRENT', '5')),
    'retry_failed_checks': os.getenv('HEALTH_RETRY_FAILED', 'true').lower() == 'true',
    'log_all_checks': os.getenv('HEALTH_LOG_ALL_CHECKS', 'false').lower() == 'true',
    'alert_on_status_change': os.getenv('HEALTH_ALERT_CHANGES', 'true').lower() == 'true'
}


def get_health_check_interval(environment: str, health_status: str) -> int:
    """
    Get the health check interval for a target based on environment and current health status.
    
    Args:
        environment: Target environment (production, staging, development, testing)
        health_status: Current health status (healthy, warning, critical, unknown)
        
    Returns:
        int: Check interval in seconds
    """
    env_config = DEFAULT_HEALTH_CHECK_INTERVALS.get(environment.lower(), 
                                                   DEFAULT_HEALTH_CHECK_INTERVALS['development'])
    return env_config.get(health_status.lower(), env_config['unknown'])


def get_health_check_timeout(method_type: str) -> int:
    """
    Get the connection timeout for a specific communication method type.
    
    Args:
        method_type: Communication method type (ssh, winrm)
        
    Returns:
        int: Timeout in seconds
    """
    return HEALTH_CHECK_TIMEOUTS.get(method_type.lower(), HEALTH_CHECK_TIMEOUTS['default'])


def should_escalate_to_warning(consecutive_failures: int, response_time: float = None) -> bool:
    """
    Determine if target should be marked as warning status.
    
    Args:
        consecutive_failures: Number of consecutive failed checks
        response_time: Latest response time in seconds (if successful)
        
    Returns:
        bool: True if should escalate to warning
    """
    if consecutive_failures >= HEALTH_THRESHOLDS['consecutive_failures_warning']:
        return True
    
    if response_time and response_time > HEALTH_THRESHOLDS['response_time_warning']:
        return True
        
    return False


def should_escalate_to_critical(consecutive_failures: int, response_time: float = None) -> bool:
    """
    Determine if target should be marked as critical status.
    
    Args:
        consecutive_failures: Number of consecutive failed checks
        response_time: Latest response time in seconds (if successful)
        
    Returns:
        bool: True if should escalate to critical
    """
    if consecutive_failures >= HEALTH_THRESHOLDS['consecutive_failures_critical']:
        return True
    
    if response_time and response_time > HEALTH_THRESHOLDS['response_time_critical']:
        return True
        
    return False


def should_recover_to_healthy(consecutive_successes: int, response_time: float) -> bool:
    """
    Determine if target should recover to healthy status.
    
    Args:
        consecutive_successes: Number of consecutive successful checks
        response_time: Latest response time in seconds
        
    Returns:
        bool: True if should recover to healthy
    """
    return (consecutive_successes >= HEALTH_THRESHOLDS['recovery_success_count'] and 
            response_time <= HEALTH_THRESHOLDS['response_time_warning'])