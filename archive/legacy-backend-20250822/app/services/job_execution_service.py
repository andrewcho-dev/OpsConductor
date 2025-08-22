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
        
        # Retry configuration
        self.enable_retry = settings.ENABLE_RETRY
        self.max_retries = settings.MAX_RETRIES
        self.retry_backoff_base = settings.RETRY_BACKOFF_BASE

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
        """
        Execute job on a single target with retry support.
        
        Args:
            execution: The job execution record
            target: The target to execute on
            
        Returns:
            dict: Execution result with success status
        """
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

            # Execute each action with retry support
            all_success = True
            for action in actions:
                try:
                    # Use retry logic if enabled
                    if self.enable_retry:
                        result = await self._execute_action_with_retry(execution, target, action, comm_method)
                    else:
                        result = await self._execute_action(execution, target, action, comm_method)
                        
                    if not result.get('success', False):
                        all_success = False
                        
                        # Log retry information if available
                        if result.get('retries_exhausted'):
                            logger.warning(f"⚠️ All retries exhausted for action '{action.action_name}' on {target.name}")
                            
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
                        error_text=f"Unhandled exception: {str(e)}"
                    )
                    all_success = False

            return {"success": all_success, "target": target.name}

        except Exception as e:
            logger.error(f"Target execution failed for {target.name}: {str(e)}")
            return {"success": False, "target": target.name, "error": str(e)}

    async def _execute_action_with_retry(
        self, 
        execution: JobExecution, 
        target: UniversalTarget, 
        action, 
        comm_method,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Execute a single action with retry logic.
        
        Args:
            execution: The job execution record
            target: The target to execute on
            action: The action to execute
            comm_method: The communication method to use
            retry_count: Current retry attempt (0 for first attempt)
            
        Returns:
            dict: Execution result with success status and output/error information
        """
        try:
            # Execute the action
            result = await self._execute_action(execution, target, action, comm_method)
            
            # If successful or retries disabled, return the result
            if result.get('success', False) or not self.enable_retry:
                return result
                
            # Check if the error is retriable
            if not result.get('retriable', False):
                logger.info(f"⚠️ Error is not retriable for action '{action.action_name}' on {target.name}")
                return result
                
            # If we've reached max retries, return the failed result
            if retry_count >= self.max_retries:
                logger.warning(f"⚠️ Max retries ({self.max_retries}) reached for action '{action.action_name}' on {target.name}")
                result['retries_exhausted'] = True
                
                # Create a final execution result with retry information
                error_msg = result.get('error', 'Unknown error')
                self.job_service.create_execution_result(
                    execution_id=execution.id,
                    target_id=target.id,
                    target_name=target.name,
                    action_id=action.id,
                    action_order=action.action_order,
                    action_name=action.action_name,
                    action_type=action.action_type,
                    status=ExecutionStatus.FAILED,
                    error_text=f"Failed after {self.max_retries} retries: {error_msg}",
                    command_executed=result.get('command', 'N/A')
                )
                
                return result
                
            # Calculate backoff time using exponential backoff
            backoff_seconds = self.retry_backoff_base ** retry_count
            logger.info(f"🔄 Retrying action '{action.action_name}' on {target.name} in {backoff_seconds:.2f}s (attempt {retry_count + 1}/{self.max_retries})")
            
            # Record the retry attempt
            try:
                self.job_service.record_retry_attempt(
                    execution_id=execution.id,
                    target_id=target.id,
                    action_id=action.id,
                    attempt_number=retry_count + 1,
                    error_message=result.get('error', 'Unknown error')
                )
            except Exception as record_error:
                logger.error(f"Failed to record retry attempt: {str(record_error)}")
            
            # Wait for backoff period
            await asyncio.sleep(backoff_seconds)
            
            # Retry the action
            return await self._execute_action_with_retry(
                execution=execution,
                target=target,
                action=action,
                comm_method=comm_method,
                retry_count=retry_count + 1
            )
            
        except Exception as e:
            logger.error(f"❌ Retry mechanism failed: {str(e)}")
            
            # Create a failure record for the retry mechanism itself
            self.job_service.create_execution_result(
                execution_id=execution.id,
                target_id=target.id,
                target_name=target.name,
                action_id=action.id,
                action_order=action.action_order,
                action_name=f"{action.action_name} (Retry Mechanism)",
                action_type=action.action_type,
                status=ExecutionStatus.FAILED,
                error_text=f"Retry mechanism failed: {str(e)}",
                command_executed="N/A - Retry mechanism failure"
            )
            
            return {"success": False, "error": f"Retry mechanism failed: {str(e)}"}
    
    async def _execute_action(
        self, 
        execution: JobExecution, 
        target: UniversalTarget, 
        action, 
        comm_method
    ) -> Dict[str, Any]:
        """
        Execute a single action on a target with improved error handling.
        
        Args:
            execution: The job execution record
            target: The target to execute on
            action: The action to execute
            comm_method: The communication method to use
            
        Returns:
            dict: Execution result with success status and output/error information
        """
        start_time = time.time()
        credentials = None
        
        try:
            logger.info(f"🔧 Executing action '{action.action_name}' on {target.name}")
            
            # Get credentials first - fail early if credentials are not available
            try:
                credentials = self._get_credentials(comm_method)
                logger.info(f"✅ Retrieved credentials for {target.name} using {comm_method.method_type}")
            except ValueError as cred_error:
                # Handle credential errors specifically
                error_msg = f"Credential error for {target.name}: {str(cred_error)}"
                logger.error(f"🔑 {error_msg}")
                
                # Create a specific credential error result
                execution_time_ms = int((time.time() - start_time) * 1000)
                self.job_service.create_execution_result(
                    execution_id=execution.id,
                    target_id=target.id,
                    target_name=target.name,
                    action_id=action.id,
                    action_order=action.action_order,
                    action_name=action.action_name,
                    action_type=action.action_type,
                    status=ExecutionStatus.FAILED,
                    error_text=f"Authentication error: {error_msg}",
                    execution_time_ms=execution_time_ms,
                    command_executed="N/A - Authentication failed"
                )
                return {"success": False, "error": error_msg, "auth_failure": True, "retriable": False}

            # Execute based on communication method
            if comm_method.method_type == "ssh":
                result = await self._execute_ssh_action(target, action, comm_method, credentials)
            elif comm_method.method_type == "winrm":
                result = await self._execute_winrm_action(target, action, comm_method, credentials)
            else:
                raise ValueError(f"Unsupported communication method: {comm_method.method_type}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Check if output capture is enabled for this action
            capture_output = action.action_parameters.get('captureOutput', True)  # Default to True for backward compatibility
            
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
            
            # Determine if this error is retriable
            retriable = False
            if not result.get('success', False):
                error_text = result.get('error', '').lower()
                # Connection timeouts, network errors are retriable
                retriable = any(term in error_text for term in [
                    'timeout', 'connection refused', 'network', 'unreachable', 
                    'temporary failure', 'reset by peer', 'broken pipe'
                ])
                result['retriable'] = retriable
            
            # Create result record only if this is not a retry or it's the final attempt
            if not self.enable_retry or not retriable:
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
            
            # Determine if this error is retriable
            error_text = str(e).lower()
            retriable = any(term in error_text for term in [
                'timeout', 'connection refused', 'network', 'unreachable', 
                'temporary failure', 'reset by peer', 'broken pipe'
            ])
            
            # Create failed result record with detailed error information
            error_category = "Authentication error" if "credential" in error_text else "Execution error"
            error_message = f"{error_category}: {str(e)}"
            
            # Create result record only if this is not a retry or it's the final attempt
            if not self.enable_retry or not retriable:
                self.job_service.create_execution_result(
                    execution_id=execution.id,
                    target_id=target.id,
                    target_name=target.name,
                    action_id=action.id,
                    action_order=action.action_order,
                    action_name=action.action_name,
                    action_type=action.action_type,
                    status=ExecutionStatus.FAILED,
                    error_text=error_message,
                    execution_time_ms=execution_time_ms,
                    command_executed=action.action_parameters.get('command', 'N/A') if hasattr(action, 'action_parameters') else 'N/A'
                )
            
            return {"success": False, "error": error_message, "retriable": retriable}

    async def _execute_ssh_action(self, target: UniversalTarget, action, comm_method, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute action via SSH using existing connection utilities.
        
        Args:
            target: The target to execute on
            action: The action to execute
            comm_method: The communication method to use
            credentials: The credentials to use for authentication
            
        Returns:
            dict: Execution result with success status and output/error information
        """
        try:
            if action.action_type != ActionType.COMMAND:
                raise ValueError(f"Unsupported SSH action type: {action.action_type}")

            command = action.action_parameters.get('command', '')
            if not command:
                raise ValueError("No command specified in action parameters")

            # Get target connection details
            host = getTargetIpAddress(target)
            if not host:
                raise ValueError(f"Could not determine IP address for target {target.name}")
                
            port = comm_method.config.get('port', 22)
            
            # Log connection attempt
            logger.info(f"🔗 Connecting to {host}:{port} via SSH")
            logger.info(f"👤 Using credentials: username='{credentials.get('username', 'NONE')}'")
            logger.info(f"💻 Executing command: '{command}'")
            
            # Execute the actual command
            result = execute_ssh_command(host, port, credentials, command, timeout=self.command_timeout)
            
            # Log connection result
            if result.get('success'):
                logger.info(f"✅ SSH connection successful to {host}:{port}")
                logger.info(f"📤 Command output: {len(result.get('output', ''))} characters")
            else:
                logger.error(f"❌ SSH connection failed to {host}:{port}")
                logger.error(f"🚫 Error: {result.get('error', 'Unknown error')}")
                logger.error(f"🔢 Exit code: {result.get('exit_code', 'Unknown')}")
            
            return {
                'success': result.get('success', False),
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'command': command,
                'exit_code': result.get('exit_code', 1)
            }
                
        except Exception as e:
            logger.error(f"❌ SSH action execution error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'command': command if 'command' in locals() else '',
                'exit_code': 1
            }

    async def _execute_winrm_action(self, target: UniversalTarget, action, comm_method, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute action via WinRM using existing connection utilities.
        
        Args:
            target: The target to execute on
            action: The action to execute
            comm_method: The communication method to use
            credentials: The credentials to use for authentication
            
        Returns:
            dict: Execution result with success status and output/error information
        """
        try:
            if action.action_type != ActionType.COMMAND:
                raise ValueError(f"Unsupported WinRM action type: {action.action_type}")

            command = action.action_parameters.get('command', '')
            if not command:
                raise ValueError("No command specified in action parameters")

            # Get target connection details
            host = getTargetIpAddress(target)
            if not host:
                raise ValueError(f"Could not determine IP address for target {target.name}")
                
            port = comm_method.config.get('port', 5985)
            
            # Log connection attempt
            logger.info(f"🔗 Connecting to {host}:{port} via WinRM")
            logger.info(f"👤 Using credentials: username='{credentials.get('username', 'NONE')}'")
            logger.info(f"💻 Executing command: '{command}'")
            
            # Validate credentials for WinRM
            if not credentials.get('username') or not credentials.get('password'):
                raise ValueError("WinRM requires both username and password")
            
            result = execute_winrm_command(host, port, credentials, command, timeout=self.command_timeout)
            
            # Log connection result
            if result.get('success'):
                logger.info(f"✅ WinRM connection successful to {host}:{port}")
                logger.info(f"📤 Command output: {len(result.get('output', ''))} characters")
            else:
                logger.error(f"❌ WinRM connection failed to {host}:{port}")
                logger.error(f"🚫 Error: {result.get('error', 'Unknown error')}")
                logger.error(f"🔢 Exit code: {result.get('exit_code', 'Unknown')}")
            
            return {
                'success': result.get('success', False),
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'command': command,
                'exit_code': result.get('exit_code', 1)
            }
                
        except Exception as e:
            logger.error(f"❌ WinRM action execution error: {str(e)}")
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
        """
        Get credentials for communication method with secure handling.
        
        This method retrieves and decrypts credentials for a communication method.
        It implements secure credential handling with proper error reporting.
        
        Args:
            comm_method: The communication method object containing credential information
            
        Returns:
            dict: Credential information or empty dict if credentials cannot be retrieved
            
        Raises:
            ValueError: If credentials are required but not available
        """
        credentials = {}
        
        logger.info(f"🔐 Retrieving credentials for communication method")
        
        # Check if communication method has credentials
        if not hasattr(comm_method, 'credentials') or not comm_method.credentials:
            logger.error(f"⚠️ No credentials found for communication method")
            raise ValueError("No credentials available for target communication method")
        
        logger.info(f"🔑 Found {len(comm_method.credentials)} credential(s)")
        
        # Process credentials based on type
        for cred in comm_method.credentials:
            logger.info(f"🔍 Processing credential type: {cred.credential_type}")
            
            # Skip if no encrypted credentials
            if not cred.encrypted_credentials:
                logger.warning(f"⚠️ Empty encrypted credentials for {cred.credential_type}")
                continue
                
            try:
                # Use the global credential encryption instance
                from app.utils.encryption_utils import decrypt_credentials
                cred_data = decrypt_credentials(cred.encrypted_credentials)
                
                if not isinstance(cred_data, dict):
                    logger.error(f"❌ Invalid credential format after decryption")
                    continue
                
                # Process based on credential type
                if cred.credential_type == 'password':
                    if 'username' not in cred_data or 'password' not in cred_data:
                        logger.error(f"❌ Missing username or password in decrypted credentials")
                        continue
                        
                    credentials['username'] = cred_data['username']
                    credentials['password'] = cred_data['password']
                    credentials['type'] = 'password'
                    logger.info(f"✅ Password credentials decrypted successfully for user: '{credentials['username']}'")
                    break  # Use first valid credential
                    
                elif cred.credential_type == 'ssh_key':
                    if 'username' not in cred_data or 'private_key' not in cred_data:
                        logger.error(f"❌ Missing username or private_key in decrypted credentials")
                        continue
                        
                    credentials['username'] = cred_data['username']
                    credentials['private_key'] = cred_data['private_key']
                    credentials['type'] = 'ssh_key'
                    
                    if 'passphrase' in cred_data:
                        credentials['passphrase'] = cred_data['passphrase']
                        
                    logger.info(f"✅ SSH key credentials decrypted successfully for user: '{credentials['username']}'")
                    break  # Use first valid credential
                    
                else:
                    logger.warning(f"⚠️ Unsupported credential type: {cred.credential_type}")
                    
            except Exception as e:
                logger.error(f"❌ Credential decryption error: {str(e)}")
                # Continue to try other credentials instead of using fallback
        
        # Check if we have valid credentials
        if not credentials:
            error_msg = "Failed to retrieve valid credentials for target communication"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        return credentials