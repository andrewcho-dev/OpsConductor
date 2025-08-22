"""
Safety Checker for command validation and security
"""

import logging
import re
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class SafetyChecker:
    """Validates commands for safety and security before execution"""
    
    def __init__(self):
        self.dangerous_commands = settings.dangerous_commands
        self.dangerous_patterns = [
            r'rm\s+-rf\s+/',  # Delete root directory
            r'del\s+/[fs]\s+/[sq]',  # Windows delete commands
            r'format\s+[cd]:', # Format drives
            r'shutdown|reboot|halt|poweroff',  # System shutdown commands
            r'mkfs\.',  # Format filesystem
            r'dd\s+.*of=/dev/',  # Dangerous dd commands
            r'chmod\s+777\s+/',  # Dangerous permissions
            r'passwd\s+root',  # Change root password
            r'sudo\s+su\s+-',  # Privilege escalation
        ]
    
    def check_command_safety(self, command: str, target_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Check if a command is safe to execute
        
        Args:
            command: The command to check
            target_config: Target system configuration
            
        Returns:
            Dict with safety check results
        """
        try:
            logger.debug(f"Checking command safety: {command}")
            
            safety_result = {
                'command': command,
                'is_safe': True,
                'risk_level': 'low',
                'warnings': [],
                'blocked_reasons': []
            }
            
            # Check against dangerous command list
            for dangerous_cmd in self.dangerous_commands:
                if dangerous_cmd.lower() in command.lower():
                    safety_result['is_safe'] = False
                    safety_result['risk_level'] = 'critical'
                    safety_result['blocked_reasons'].append(f"Contains dangerous command: {dangerous_cmd}")
            
            # Check against dangerous patterns
            for pattern in self.dangerous_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    safety_result['is_safe'] = False
                    safety_result['risk_level'] = 'critical'
                    safety_result['blocked_reasons'].append(f"Matches dangerous pattern: {pattern}")
            
            # Check for potential risks (warnings, not blocks)
            risk_patterns = [
                r'sudo',  # Privilege escalation
                r'su\s+',  # User switching
                r'crontab',  # Cron modifications
                r'iptables',  # Firewall changes
                r'systemctl\s+(stop|disable)',  # Service management
                r'service\s+.*\s+stop',  # Service stopping
            ]
            
            for pattern in risk_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    if safety_result['risk_level'] == 'low':
                        safety_result['risk_level'] = 'medium'
                    safety_result['warnings'].append(f"Contains potentially risky operation: {pattern}")
            
            # Environment-specific checks
            if target_config:
                environment = target_config.get('environment', '').lower()
                if environment == 'production':
                    production_risks = [
                        r'restart',
                        r'kill\s+-9',
                        r'pkill',
                        r'service.*stop'
                    ]
                    
                    for pattern in production_risks:
                        if re.search(pattern, command, re.IGNORECASE):
                            safety_result['warnings'].append(f"High-risk operation in production: {pattern}")
                            if safety_result['risk_level'] in ['low', 'medium']:
                                safety_result['risk_level'] = 'high'
            
            logger.info(f"Command safety check: {safety_result['risk_level']} risk, safe: {safety_result['is_safe']}")
            return safety_result
            
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return {
                'command': command,
                'is_safe': False,
                'risk_level': 'critical',
                'warnings': [],
                'blocked_reasons': [f"Safety check error: {str(e)}"]
            }
    
    def is_command_allowed(self, command: str, target_config: Dict[str, Any] = None) -> bool:
        """
        Simple boolean check if command is allowed
        
        Args:
            command: The command to check
            target_config: Target system configuration
            
        Returns:
            True if command is safe, False if blocked
        """
        if not settings.enable_safety_checks:
            return True
            
        safety_result = self.check_command_safety(command, target_config)
        return safety_result['is_safe']
    
    def get_safety_recommendations(self, command: str) -> List[str]:
        """
        Get safety recommendations for a command
        
        Args:
            command: The command to analyze
            
        Returns:
            List of safety recommendations
        """
        recommendations = []
        
        safety_result = self.check_command_safety(command)
        
        if not safety_result['is_safe']:
            recommendations.append("⛔ This command has been blocked due to safety concerns")
            
        if safety_result['warnings']:
            recommendations.append("⚠️  This command contains potentially risky operations")
            
        if 'sudo' in command.lower():
            recommendations.append("💡 Consider running without sudo if possible")
            
        if any(pattern in command.lower() for pattern in ['restart', 'stop', 'kill']):
            recommendations.append("🔄 Consider scheduling this during maintenance windows")
            
        if not recommendations:
            recommendations.append("✅ Command appears safe to execute")
            
        return recommendations