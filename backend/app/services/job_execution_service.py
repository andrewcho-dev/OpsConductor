import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from app.models.job_models import (
    JobExecution, JobExecutionResult, ExecutionStatus, ActionType
)
from app.models.universal_target_models import UniversalTarget
from app.services.job_service import JobService
from app.utils.target_utils import getTargetIpAddress
from app.utils.connection_test_utils import test_ssh_connection, test_winrm_connection, execute_ssh_command, execute_winrm_command
from app.core.config import settings

logger = logging.getLogger(__name__)


class JobExecutionService:
    def __init__(self, job_service: JobService, max_concurrent=None):
        self.job_service = job_service
        self.max_concurrent = max_concurrent or settings.MAX_CONCURRENT_TARGETS
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.connection_timeout = settings.CONNECTION_TIMEOUT
        self.command_timeout = settings.COMMAND_TIMEOUT

    async def execute_job_on_targets(
        self,
        execution: JobExecution,
        targets: List[UniversalTarget]
    ) -> Dict[str, Any]:
        """Execute a job on multiple targets concurrently - SIMPLIFIED"""
        logger.info(f"🚀 Starting execution {execution.id} on {len(targets)} targets")
        execution_start_time = time.time()

        # Update execution status
        self.job_service.update_execution_status(execution.id, ExecutionStatus.RUNNING)

        # Create tasks for each target
        tasks = []
        for target in targets:
            task = asyncio.create_task(self._execute_on_target(execution, target))
            tasks.append(task)

        # Execute all targets concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_targets = 0
        failed_targets = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Target {targets[i].name} failed: {str(result)}")
                failed_targets += 1
            else:
                if result.get('success', False):
                    successful_targets += 1
                else:
                    failed_targets += 1

        # Update execution summary
        execution.successful_targets = successful_targets
        execution.failed_targets = failed_targets
        
        if failed_targets > 0:
            execution.status = ExecutionStatus.FAILED
        else:
            execution.status = ExecutionStatus.COMPLETED
            
        execution.completed_at = datetime.now(timezone.utc)
        self.job_service.db.commit()

        execution_time = time.time() - execution_start_time
        logger.info(f"✅ Execution {execution.id} completed in {execution_time:.2f}s: {successful_targets} success, {failed_targets} failed")

        return {
            "execution_id": execution.id,
            "total_targets": len(targets),
            "successful_targets": successful_targets,
            "failed_targets": failed_targets,
            "execution_time": execution_time
        }

    async def _execute_on_target(self, execution: JobExecution, target: UniversalTarget) -> Dict[str, Any]:
        """Execute job on a single target - SIMPLIFIED"""
        logger.info(f"🎯 Executing on target: {target.name}")
        
        try:
            # Get job actions
            job = execution.job
            actions = sorted(job.actions, key=lambda a: a.action_order)
            
            if not actions:
                raise ValueError(f"No actions found for job {job.id}")

            # Get communication method
            comm_method = self._get_primary_communication_method(target)
            if not comm_method:
                raise ValueError(f"No communication method found for target {target.name}")

            # Execute each action
            all_success = True
            for action in actions:
                try:
                    result = await self._execute_action(execution, target, action, comm_method)
                    if not result.get('success', False):
                        all_success = False
                except Exception as e:
                    logger.error(f"Action {action.action_name} failed on {target.name}: {str(e)}")
                    # Create failed result record
                    self.job_service.create_execution_result(
                        execution_id=execution.id,
                        target_id=target.id,
                        target_name=target.name,
                        action_id=action.id,
                        action_order=action.action_order,
                        action_name=action.action_name,
                        action_type=action.action_type,
                        status=ExecutionStatus.FAILED,
                        error_text=str(e)
                    )
                    all_success = False

            return {"success": all_success, "target": target.name}

        except Exception as e:
            logger.error(f"Target execution failed for {target.name}: {str(e)}")
            return {"success": False, "target": target.name, "error": str(e)}

    async def _execute_action(
        self, 
        execution: JobExecution, 
        target: UniversalTarget, 
        action, 
        comm_method
    ) -> Dict[str, Any]:
        """Execute a single action on a target - SIMPLIFIED"""
        start_time = time.time()
        
        try:
            logger.info(f"🔧 Executing action '{action.action_name}' on {target.name}")

            # Execute based on communication method
            if comm_method.method_type == "ssh":
                result = await self._execute_ssh_action(target, action, comm_method)
            elif comm_method.method_type == "winrm":
                result = await self._execute_winrm_action(target, action, comm_method)
            else:
                raise ValueError(f"Unsupported communication method: {comm_method.method_type}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Check if output capture is enabled for this action
            capture_output = action.action_parameters.get('captureOutput', True)  # Default to True for backward compatibility
            
            # Get credentials for connection info
            credentials = self._get_credentials(comm_method)
            
            # Prepare output text with connection info
            output_text = ""
            if capture_output:
                # Add connection status to output
                connection_info = f"🔗 Connection: {comm_method.method_type.upper()} to {getTargetIpAddress(target)}:{comm_method.config.get('port', 'default')}\n"
                connection_info += f"👤 Username: {credentials.get('username', 'unknown')}\n"
                connection_info += f"✅ Status: {'CONNECTED' if result['success'] else 'FAILED'}\n"
                connection_info += "=" * 50 + "\n"
                
                if result['success']:
                    output_text = connection_info + result.get('output', '')
                else:
                    output_text = connection_info + f"❌ Connection Error: {result.get('error', 'Unknown error')}"
            
            # Create result record
            self.job_service.create_execution_result(
                execution_id=execution.id,
                target_id=target.id,
                target_name=target.name,
                action_id=action.id,
                action_order=action.action_order,
                action_name=action.action_name,
                action_type=action.action_type,
                status=ExecutionStatus.COMPLETED if result['success'] else ExecutionStatus.FAILED,
                output_text=output_text if capture_output else None,
                error_text=result.get('error', '') if capture_output else None,
                exit_code=result.get('exit_code', 0),
                command_executed=result.get('command', ''),
                execution_time_ms=execution_time_ms
            )

            logger.info(f"✅ Action '{action.action_name}' completed on {target.name} in {execution_time_ms}ms")
            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"❌ Action '{action.action_name}' failed on {target.name}: {str(e)}")
            
            # Create failed result record
            self.job_service.create_execution_result(
                execution_id=execution.id,
                target_id=target.id,
                target_name=target.name,
                action_id=action.id,
                action_order=action.action_order,
                action_name=action.action_name,
                action_type=action.action_type,
                status=ExecutionStatus.FAILED,
                error_text=str(e),
                execution_time_ms=execution_time_ms
            )
            
            return {"success": False, "error": str(e)}

    async def _execute_ssh_action(self, target: UniversalTarget, action, comm_method) -> Dict[str, Any]:
        """Execute action via SSH using existing connection utilities"""
        try:
            logger.info(f"🔍 DEBUG: comm_method type: {type(comm_method)}")
            logger.info(f"🔍 DEBUG: comm_method attributes: {dir(comm_method)}")
            logger.info(f"🔍 DEBUG: comm_method.config type: {type(getattr(comm_method, 'config', 'NOT_FOUND'))}")
            
            if action.action_type != ActionType.COMMAND:
                raise ValueError(f"Unsupported SSH action type: {action.action_type}")

            command = action.action_parameters.get('command', '')
            if not command:
                raise ValueError("No command specified in action parameters")

            # Get target connection details
            host = getTargetIpAddress(target)
            port = comm_method.config.get('port', 22)
            
            # Get credentials
            credentials = self._get_credentials(comm_method)
            
            # Log connection attempt
            logger.info(f"🔗 CONNECTING to {host}:{port} via SSH")
            logger.info(f"👤 Using credentials: username='{credentials.get('username', 'NONE')}'")
            logger.info(f"💻 Executing command: '{command}'")
            
            # Execute the actual command
            result = execute_ssh_command(host, port, credentials, command, timeout=self.command_timeout)
            
            # Log connection result
            if result.get('success'):
                logger.info(f"✅ SSH CONNECTION SUCCESSFUL to {host}:{port}")
                logger.info(f"📤 Command output: {len(result.get('output', ''))} characters")
            else:
                logger.error(f"❌ SSH CONNECTION FAILED to {host}:{port}")
                logger.error(f"🚫 Error: {result.get('error', 'Unknown error')}")
                logger.error(f"🔢 Exit code: {result.get('exit_code', 'Unknown')}")
                
            logger.info(f"🔍 Full SSH result: {result}")
            
            return {
                'success': result.get('success', False),
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'command': command,
                'exit_code': result.get('exit_code', 1)
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command if 'command' in locals() else '',
                'exit_code': 1
            }

    async def _execute_winrm_action(self, target: UniversalTarget, action, comm_method) -> Dict[str, Any]:
        """Execute action via WinRM using existing connection utilities"""
        try:
            if action.action_type != ActionType.COMMAND:
                raise ValueError(f"Unsupported WinRM action type: {action.action_type}")

            command = action.action_parameters.get('command', '')
            if not command:
                raise ValueError("No command specified in action parameters")

            # Get target connection details
            host = getTargetIpAddress(target)
            port = comm_method.config.get('port', 5985)
            
            # Get credentials
            credentials = self._get_credentials(comm_method)
            
            # Log connection attempt
            logger.info(f"🔗 CONNECTING to {host}:{port} via WinRM")
            logger.info(f"👤 Using credentials: username='{credentials.get('username', 'NONE')}'")
            logger.info(f"💻 Executing command: '{command}'")
            
            result = execute_winrm_command(host, port, credentials, command, timeout=self.command_timeout)
            
            # Log connection result
            if result.get('success'):
                logger.info(f"✅ WinRM CONNECTION SUCCESSFUL to {host}:{port}")
                logger.info(f"📤 Command output: {len(result.get('output', ''))} characters")
            else:
                logger.error(f"❌ WinRM CONNECTION FAILED to {host}:{port}")
                logger.error(f"🚫 Error: {result.get('error', 'Unknown error')}")
                logger.error(f"🔢 Exit code: {result.get('exit_code', 'Unknown')}")
                
            logger.info(f"🔍 Full WinRM result: {result}")
            
            return {
                'success': result.get('success', False),
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'command': command,
                'exit_code': result.get('exit_code', 1)
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command if 'command' in locals() else '',
                'exit_code': 1
            }

    def _get_primary_communication_method(self, target: UniversalTarget):
        """Get primary communication method for target"""
        if hasattr(target, 'communication_methods') and target.communication_methods:
            # Find primary method or first active method
            for method in target.communication_methods:
                if method.is_primary and method.is_active:
                    return method
            # Fallback to first active method
            for method in target.communication_methods:
                if method.is_active:
                    return method
        return None

    def _get_credentials(self, comm_method) -> Dict[str, Any]:
        """Get credentials for communication method"""
        credentials = {}
        
        logger.info(f"🔐 RETRIEVING CREDENTIALS for communication method")
        
        if hasattr(comm_method, 'credentials') and comm_method.credentials:
            logger.info(f"🔑 Found {len(comm_method.credentials)} credential(s)")
            
            for cred in comm_method.credentials:
                logger.info(f"🔍 Processing credential type: {cred.credential_type}")
                
                if cred.credential_type == 'password' and cred.encrypted_credentials:
                    # The credentials are encrypted - need to decrypt them
                    try:
                        from app.utils.encryption_utils import CredentialEncryption
                        encryptor = CredentialEncryption()
                        cred_data = encryptor.decrypt_credentials(cred.encrypted_credentials)
                        
                        if isinstance(cred_data, dict):
                            credentials['username'] = cred_data.get('username', 'admin')
                            credentials['password'] = cred_data.get('password', '')
                            logger.info(f"✅ CREDENTIALS DECRYPTED successfully - username: '{credentials['username']}'")
                        else:
                            # If decryption fails, use fallback
                            credentials = {'username': 'admin', 'password': 'password123'}
                            logger.error(f"❌ CREDENTIAL DECRYPTION FAILED - using fallback credentials")
                    except Exception as e:
                        logger.error(f"❌ CREDENTIAL DECRYPTION ERROR: {str(e)}")
                        logger.error(f"🔄 Using fallback credentials: admin/password123")
                        credentials = {'username': 'admin', 'password': 'password123'}
                elif cred.credential_type == 'ssh_key' and cred.encrypted_credentials:
                    try:
                        from app.utils.encryption_utils import decrypt_credentials
                        cred_data = decrypt_credentials(cred.encrypted_credentials)
                        if isinstance(cred_data, dict):
                            credentials['username'] = cred_data.get('username', 'admin')
                            credentials['private_key'] = cred_data.get('private_key', '')
                            if cred_data.get('passphrase'):
                                credentials['passphrase'] = cred_data.get('passphrase')
                        else:
                            credentials = {'username': 'admin', 'password': 'password123'}
                    except Exception as e:
                        logger.warning(f"Failed to decrypt SSH key credentials: {str(e)}")
                        credentials = {'username': 'admin', 'password': 'password123'}
        
        else:
            logger.warning(f"⚠️  NO CREDENTIALS found for communication method")
        
        # Fallback credentials for testing
        if not credentials:
            logger.error(f"❌ NO VALID CREDENTIALS - using default fallback")
            credentials = {
                'username': 'admin',
                'password': 'password123'  # Default test credentials
            }
        
        logger.info(f"🔐 FINAL CREDENTIALS: username='{credentials.get('username', 'NONE')}'")
        return credentials