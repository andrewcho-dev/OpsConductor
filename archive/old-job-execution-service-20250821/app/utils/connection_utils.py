"""
Connection utilities for SSH and WinRM
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import asyncssh
import aiofiles
from pathlib import Path

logger = logging.getLogger(__name__)


class SSHConnectionManager:
    """Manager for SSH connections and operations"""
    
    async def execute_command(
        self, 
        target: Dict[str, Any], 
        credentials: Dict[str, Any], 
        command: str, 
        timeout: int
    ) -> Dict[str, Any]:
        """Execute command via SSH"""
        try:
            connection_params = self._build_ssh_params(target, credentials)
            
            async with asyncssh.connect(**connection_params) as conn:
                logger.info(f"SSH connected to {target['name']} ({target.get('host')})")
                
                result = await asyncio.wait_for(
                    conn.run(command, check=False),
                    timeout=timeout
                )
                
                return {
                    "success": result.exit_status == 0,
                    "output": result.stdout,
                    "error": result.stderr,
                    "exit_code": result.exit_status,
                    "command": command,
                    "retriable": result.exit_status in [124, 125, 126, 127]  # Common retriable exit codes
                }
                
        except asyncio.TimeoutError:
            error_msg = f"Command timed out after {timeout} seconds"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": command,
                "retriable": True
            }
        except asyncssh.Error as e:
            error_msg = f"SSH error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": command,
                "retriable": self._is_ssh_error_retriable(str(e))
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": command,
                "retriable": False
            }
    
    async def execute_script(
        self, 
        target: Dict[str, Any], 
        credentials: Dict[str, Any], 
        script_content: str, 
        script_type: str, 
        timeout: int
    ) -> Dict[str, Any]:
        """Execute script via SSH"""
        try:
            connection_params = self._build_ssh_params(target, credentials)
            
            # Determine script interpreter
            if script_type.lower() == "bash":
                interpreter = "/bin/bash"
            elif script_type.lower() == "sh":
                interpreter = "/bin/sh"
            elif script_type.lower() == "python":
                interpreter = "/usr/bin/python3"
            else:
                interpreter = "/bin/bash"  # Default
            
            async with asyncssh.connect(**connection_params) as conn:
                logger.info(f"SSH connected to {target['name']} for script execution")
                
                # Execute script by piping to interpreter
                result = await asyncio.wait_for(
                    conn.run(f"echo {repr(script_content)} | {interpreter}", check=False),
                    timeout=timeout
                )
                
                return {
                    "success": result.exit_status == 0,
                    "output": result.stdout,
                    "error": result.stderr,
                    "exit_code": result.exit_status,
                    "command": f"{interpreter} script",
                    "retriable": result.exit_status in [124, 125, 126, 127]
                }
                
        except asyncio.TimeoutError:
            error_msg = f"Script timed out after {timeout} seconds"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": f"{script_type} script",
                "retriable": True
            }
        except Exception as e:
            error_msg = f"Script execution error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": f"{script_type} script",
                "retriable": False
            }
    
    async def upload_file(
        self, 
        target: Dict[str, Any], 
        credentials: Dict[str, Any], 
        local_path: str, 
        remote_path: str
    ) -> Dict[str, Any]:
        """Upload file via SFTP"""
        try:
            connection_params = self._build_ssh_params(target, credentials)
            
            async with asyncssh.connect(**connection_params) as conn:
                logger.info(f"Uploading {local_path} to {target['name']}:{remote_path}")
                
                async with conn.start_sftp_client() as sftp:
                    await sftp.put(local_path, remote_path)
                
                return {
                    "success": True,
                    "output": f"File uploaded successfully: {local_path} -> {remote_path}",
                    "command": f"upload {local_path} {remote_path}",
                    "retriable": False
                }
                
        except Exception as e:
            error_msg = f"File upload error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": f"upload {local_path} {remote_path}",
                "retriable": True
            }
    
    async def download_file(
        self, 
        target: Dict[str, Any], 
        credentials: Dict[str, Any], 
        remote_path: str, 
        local_path: str
    ) -> Dict[str, Any]:
        """Download file via SFTP"""
        try:
            connection_params = self._build_ssh_params(target, credentials)
            
            async with asyncssh.connect(**connection_params) as conn:
                logger.info(f"Downloading {target['name']}:{remote_path} to {local_path}")
                
                async with conn.start_sftp_client() as sftp:
                    await sftp.get(remote_path, local_path)
                
                return {
                    "success": True,
                    "output": f"File downloaded successfully: {remote_path} -> {local_path}",
                    "command": f"download {remote_path} {local_path}",
                    "retriable": False
                }
                
        except Exception as e:
            error_msg = f"File download error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": f"download {remote_path} {local_path}",
                "retriable": True
            }
    
    def _build_ssh_params(self, target: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Build SSH connection parameters"""
        params = {
            "host": target.get("host"),
            "port": target.get("port", 22),
            "username": credentials.get("username"),
            "known_hosts": None,  # Disable host key checking for now
        }
        
        # Authentication method
        if credentials.get("private_key"):
            params["client_keys"] = [credentials["private_key"]]
        elif credentials.get("password"):
            params["password"] = credentials["password"]
        else:
            raise ValueError("No valid authentication method found")
        
        return params
    
    def _is_ssh_error_retriable(self, error_message: str) -> bool:
        """Check if SSH error is retriable"""
        retriable_patterns = [
            "connection refused",
            "connection timed out",
            "network unreachable",
            "host unreachable",
            "authentication failed"  # Might be temporary
        ]
        
        error_lower = error_message.lower()
        return any(pattern in error_lower for pattern in retriable_patterns)


class WinRMConnectionManager:
    """Manager for WinRM connections and operations"""
    
    async def execute_command(
        self, 
        target: Dict[str, Any], 
        credentials: Dict[str, Any], 
        command: str, 
        timeout: int
    ) -> Dict[str, Any]:
        """Execute command via WinRM"""
        try:
            # Note: This is a simplified implementation
            # In production, you'd use a proper async WinRM library like pywinrm
            
            # For now, return a mock response
            logger.info(f"WinRM command execution on {target['name']}: {command}")
            
            # TODO: Implement actual WinRM execution
            return {
                "success": True,
                "output": f"Mock WinRM execution of: {command}",
                "error": "",
                "exit_code": 0,
                "command": command,
                "retriable": False
            }
            
        except Exception as e:
            error_msg = f"WinRM error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": command,
                "retriable": True
            }
    
    async def execute_script(
        self, 
        target: Dict[str, Any], 
        credentials: Dict[str, Any], 
        script_content: str, 
        script_type: str, 
        timeout: int
    ) -> Dict[str, Any]:
        """Execute script via WinRM"""
        try:
            logger.info(f"WinRM script execution on {target['name']}: {script_type}")
            
            # TODO: Implement actual WinRM script execution
            return {
                "success": True,
                "output": f"Mock WinRM {script_type} script execution",
                "error": "",
                "exit_code": 0,
                "command": f"{script_type} script",
                "retriable": False
            }
            
        except Exception as e:
            error_msg = f"WinRM script error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": f"{script_type} script",
                "retriable": True
            }
    
    async def upload_file(
        self, 
        target: Dict[str, Any], 
        credentials: Dict[str, Any], 
        local_path: str, 
        remote_path: str
    ) -> Dict[str, Any]:
        """Upload file via WinRM"""
        try:
            logger.info(f"WinRM file upload to {target['name']}: {local_path} -> {remote_path}")
            
            # TODO: Implement actual WinRM file upload
            return {
                "success": True,
                "output": f"Mock WinRM file upload: {local_path} -> {remote_path}",
                "command": f"upload {local_path} {remote_path}",
                "retriable": False
            }
            
        except Exception as e:
            error_msg = f"WinRM upload error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": f"upload {local_path} {remote_path}",
                "retriable": True
            }
    
    async def download_file(
        self, 
        target: Dict[str, Any], 
        credentials: Dict[str, Any], 
        remote_path: str, 
        local_path: str
    ) -> Dict[str, Any]:
        """Download file via WinRM"""
        try:
            logger.info(f"WinRM file download from {target['name']}: {remote_path} -> {local_path}")
            
            # TODO: Implement actual WinRM file download
            return {
                "success": True,
                "output": f"Mock WinRM file download: {remote_path} -> {local_path}",
                "command": f"download {remote_path} {local_path}",
                "retriable": False
            }
            
        except Exception as e:
            error_msg = f"WinRM download error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": f"download {remote_path} {local_path}",
                "retriable": True
            }