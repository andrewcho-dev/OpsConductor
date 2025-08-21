"""
Safety utilities for job execution
"""

import re
import logging
from typing import Dict, Any, List
from app.models.job_models import JobAction, ActionType
from app.core.config import settings

logger = logging.getLogger(__name__)


class SafetyChecker:
    """Safety checker for job actions"""
    
    def __init__(self):
        self.dangerous_commands = settings.dangerous_commands
        self.dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r'del\s+/[fs]\s+/[sq]\s+c:\\',
            r'format\s+c:',
            r'shutdown\s+',
            r'reboot\s*$',
            r'halt\s*$',
            r'poweroff\s*$',
            r'init\s+0',
            r'init\s+6',
            r'systemctl\s+poweroff',
            r'systemctl\s+reboot',
            r'dd\s+if=/dev/zero\s+of=/',
            r'mkfs\.',
            r'fdisk\s+',
            r'parted\s+',
            r'wipefs\s+',
        ]
    
    def check_action_safety(self, action: JobAction) -> Dict[str, Any]:
        """Check if an action is safe to execute"""
        try:
            if action.action_type == ActionType.COMMAND:
                return self._check_command_safety(action)
            elif action.action_type == ActionType.SCRIPT:
                return self._check_script_safety(action)
            elif action.action_type == ActionType.FILE_TRANSFER:
                return self._check_file_transfer_safety(action)
            else:
                return {"safe": True, "reason": None}
                
        except Exception as e:
            logger.error(f"Safety check error: {e}")
            return {"safe": False, "reason": f"Safety check failed: {e}"}
    
    def _check_command_safety(self, action: JobAction) -> Dict[str, Any]:
        """Check command safety"""
        command = action.action_parameters.get("command", "")
        
        # Check against dangerous command list
        for dangerous_cmd in self.dangerous_commands:
            if dangerous_cmd.lower() in command.lower():
                return {
                    "safe": False,
                    "reason": f"Command contains dangerous pattern: {dangerous_cmd}"
                }
        
        # Check against dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return {
                    "safe": False,
                    "reason": f"Command matches dangerous pattern: {pattern}"
                }
        
        # Check for potentially dangerous operations
        dangerous_indicators = [
            "sudo rm",
            "sudo dd",
            "sudo mkfs",
            "sudo fdisk",
            "sudo parted",
            "sudo wipefs",
            "> /dev/",
            "| dd",
            "&& rm",
            "; rm",
            "$(rm",
            "`rm",
        ]
        
        for indicator in dangerous_indicators:
            if indicator in command.lower():
                return {
                    "safe": False,
                    "reason": f"Command contains potentially dangerous operation: {indicator}"
                }
        
        return {"safe": True, "reason": None}
    
    def _check_script_safety(self, action: JobAction) -> Dict[str, Any]:
        """Check script safety"""
        script_content = action.action_parameters.get("script_content", "")
        
        # Check script content for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, script_content, re.IGNORECASE):
                return {
                    "safe": False,
                    "reason": f"Script contains dangerous pattern: {pattern}"
                }
        
        # Check for dangerous script operations
        dangerous_script_patterns = [
            r'exec\s*\(',
            r'eval\s*\(',
            r'system\s*\(',
            r'os\.system',
            r'subprocess\.',
            r'shell=True',
            r'import\s+os',
            r'from\s+os\s+import',
            r'__import__',
        ]
        
        for pattern in dangerous_script_patterns:
            if re.search(pattern, script_content, re.IGNORECASE):
                return {
                    "safe": False,
                    "reason": f"Script contains potentially dangerous operation: {pattern}"
                }
        
        return {"safe": True, "reason": None}
    
    def _check_file_transfer_safety(self, action: JobAction) -> Dict[str, Any]:
        """Check file transfer safety"""
        operation = action.action_parameters.get("operation", "")
        local_path = action.action_parameters.get("local_path", "")
        remote_path = action.action_parameters.get("remote_path", "")
        
        # Check for dangerous paths
        dangerous_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "/etc/sudoers",
            "/boot/",
            "/sys/",
            "/proc/",
            "/dev/",
            "C:\\Windows\\System32\\",
            "C:\\Windows\\Boot\\",
            "C:\\Program Files\\",
        ]
        
        paths_to_check = [local_path, remote_path]
        
        for path in paths_to_check:
            for dangerous_path in dangerous_paths:
                if dangerous_path.lower() in path.lower():
                    return {
                        "safe": False,
                        "reason": f"File transfer involves dangerous path: {dangerous_path}"
                    }
        
        # Check for executable file uploads
        if operation == "upload":
            executable_extensions = [".exe", ".bat", ".cmd", ".ps1", ".sh", ".py", ".pl"]
            for ext in executable_extensions:
                if local_path.lower().endswith(ext):
                    return {
                        "safe": False,
                        "reason": f"Uploading executable file: {ext}"
                    }
        
        return {"safe": True, "reason": None}
    
    def get_safety_recommendations(self, action: JobAction) -> List[str]:
        """Get safety recommendations for an action"""
        recommendations = []
        
        if action.action_type == ActionType.COMMAND:
            command = action.action_parameters.get("command", "")
            
            if "sudo" in command.lower():
                recommendations.append("Consider running without sudo if possible")
            
            if any(op in command.lower() for op in ["rm", "del", "delete"]):
                recommendations.append("Double-check file paths before deletion")
            
            if any(op in command.lower() for op in ["format", "mkfs", "fdisk"]):
                recommendations.append("Verify disk operations on correct devices")
        
        elif action.action_type == ActionType.SCRIPT:
            recommendations.append("Review script content for unintended side effects")
            recommendations.append("Test script in non-production environment first")
        
        elif action.action_type == ActionType.FILE_TRANSFER:
            operation = action.action_parameters.get("operation", "")
            if operation == "upload":
                recommendations.append("Verify file permissions after upload")
                recommendations.append("Scan uploaded files for malware")
        
        return recommendations