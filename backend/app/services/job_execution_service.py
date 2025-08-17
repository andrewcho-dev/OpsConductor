import asyncio
import paramiko
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from app.models.job_models import (
    JobExecution, JobExecutionBranch, ExecutionStatus, LogPhase, LogLevel, LogCategory
)
from app.models.universal_target_models import UniversalTarget
from app.services.job_service import JobService
from app.utils.target_utils import getTargetIpAddress
from app.core.config import settings


logger = logging.getLogger(__name__)


class JobExecutionService:
    def __init__(self, job_service: JobService, max_concurrent=None):
        self.job_service = job_service
        self.max_concurrent = max_concurrent or settings.MAX_CONCURRENT_TARGETS
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.connection_pool = {}  # Reuse SSH connections
        self.connection_timeout = settings.CONNECTION_TIMEOUT
        self.command_timeout = settings.COMMAND_TIMEOUT

    async def execute_job_on_targets(
        self,
        execution: JobExecution,
        targets: List[UniversalTarget]
    ) -> Dict[str, Any]:
        """Execute a job on multiple targets concurrently"""
        logger.info(f"Starting execution {execution.id} on {len(targets)} targets")
        execution_start_time = time.time()

        # Create tasks for each target with concurrency control
        tasks = []
        total_targets = len(targets)
        completed_targets = 0
        
        async def execute_with_progress(target):
            nonlocal completed_targets
            async with self.semaphore:
                start_time = time.time()
                try:
                    result = await self._execute_with_retry(execution, target)
                    execution_time = time.time() - start_time
                    completed_targets += 1
                    logger.info(f"Progress: {completed_targets}/{total_targets} targets completed "
                              f"(Target: {target.name}, Time: {execution_time:.2f}s)")
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    completed_targets += 1
                    logger.error(f"Target {target.name} failed after {execution_time:.2f}s: {str(e)}")
                    raise
        
        for target in targets:
            task = asyncio.create_task(execute_with_progress(target))
            tasks.append(task)

        # Execute all targets with concurrency control
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results with detailed error tracking and performance metrics
        successful_targets = 0
        failed_targets = 0
        error_summary = {}
        execution_times = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                target_name = targets[i].name
                error_type = type(result).__name__
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
                logger.error(f"Target {target_name} failed: {str(result)}")
                failed_targets += 1
            else:
                successful_targets += 1
                # Extract execution time from result if available
                if isinstance(result, dict) and 'execution_time' in result:
                    execution_times.append(result['execution_time'])
        
        # Calculate performance metrics
        total_execution_time = time.time() - execution_start_time
        avg_target_time = sum(execution_times) / len(execution_times) if execution_times else 0
        min_target_time = min(execution_times) if execution_times else 0
        max_target_time = max(execution_times) if execution_times else 0
        
        # Log execution summary with performance metrics
        logger.info(f"Execution {execution.id} completed: "
                   f"{successful_targets} successful, {failed_targets} failed")
        logger.info(f"Performance: Total={total_execution_time:.2f}s, "
                   f"Avg={avg_target_time:.2f}s, Min={min_target_time:.2f}s, "
                   f"Max={max_target_time:.2f}s")
        if error_summary:
            logger.info(f"Error summary: {error_summary}")

        # Update execution status
        if failed_targets == 0:
            await self._update_execution_complete(execution.id, ExecutionStatus.COMPLETED)
        elif successful_targets == 0:
            await self._update_execution_complete(execution.id, ExecutionStatus.FAILED)
        else:
            await self._update_execution_complete(execution.id, ExecutionStatus.FAILED)

        return {
            "execution_id": execution.id,
            "total_targets": len(targets),
            "successful_targets": successful_targets,
            "failed_targets": failed_targets
        }

    async def _execute_with_retry(
        self,
        execution: JobExecution,
        target: UniversalTarget
    ) -> Dict[str, Any]:
        """Execute on target with optional retry logic"""
        if settings.ENABLE_RETRY:
            return await self._execute_with_retry_logic(execution, target)
        else:
            return await self._execute_on_target(execution, target)

    async def _execute_with_retry_logic(
        self,
        execution: JobExecution,
        target: UniversalTarget
    ) -> Dict[str, Any]:
        """Execute on target with retry logic (stub for future implementation)"""
        max_retries = settings.MAX_RETRIES
        backoff_base = settings.RETRY_BACKOFF_BASE
        
        for attempt in range(max_retries):
            try:
                return await self._execute_on_target(execution, target)
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed, re-raise the exception
                    raise
                
                # Calculate backoff delay
                delay = backoff_base ** attempt
                logger.warning(f"Target {target.name} failed (attempt {attempt + 1}/{max_retries}), "
                             f"retrying in {delay:.1f}s: {str(e)}")
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        raise Exception(f"All {max_retries} attempts failed for target {target.name}")

    async def _execute_on_target(
        self,
        execution: JobExecution,
        target: UniversalTarget
    ) -> Dict[str, Any]:
        """Execute job on a single target"""
        branch = None
        start_time = time.time()
        try:
            # Find the branch for this target
            branch = self._get_branch_for_target(execution.id, target.id)
            if not branch:
                raise ValueError(f"No branch found for target {target.id}")

            # Log target selection
            await self._log_execution_event(
                execution.id, branch.id, LogPhase.TARGET_SELECTION,
                LogLevel.INFO, LogCategory.SYSTEM,
                f"Selected target: {target.name}"
            )

            # Get primary communication method first (this loads communication_methods)
            comm_method = self._get_primary_communication_method(target)
            if not comm_method:
                raise ValueError(f"No communication method found for target {target.name}")

            # Get target IP address (now that communication_methods are loaded)
            ip_address = getTargetIpAddress(target)
            if not ip_address:
                raise ValueError(f"No IP address found for target {target.name}")

            # Execute based on communication method
            if comm_method.method_type == "ssh":
                result = await self._execute_ssh_command(
                    target, comm_method, execution, branch
                )
            elif comm_method.method_type == "winrm":
                result = await self._execute_winrm_command(
                    target, comm_method, execution, branch
                )
            else:
                raise ValueError(f"Unsupported communication method: {comm_method.method_type}")

            # Update branch with results
            await self._update_branch_results(branch.id, result)

            # Add execution time to result for performance tracking
            if isinstance(result, dict):
                result['execution_time'] = time.time() - start_time

            return result

        except Exception as e:
            logger.error(f"Execution failed on target {target.name}: {str(e)}")
            
            if branch:
                await self._update_branch_error(branch.id, str(e))
                await self._log_execution_event(
                    execution.id, branch.id, LogPhase.ACTION_EXECUTION,
                    LogLevel.ERROR, LogCategory.COMMAND_EXECUTION,
                    f"Execution failed: {str(e)}"
                )

            raise

    async def _execute_ssh_command(
        self,
        target: UniversalTarget,
        comm_method: Any,
        execution: JobExecution,
        branch: JobExecutionBranch
    ) -> Dict[str, Any]:
        """Execute command via SSH"""
        ip_address = getTargetIpAddress(target)
        
        # Log authentication phase
        await self._log_execution_event(
            execution.id, branch.id, LogPhase.AUTHENTICATION,
            LogLevel.INFO, LogCategory.AUTHENTICATION,
            f"Authenticating to {ip_address}"
        )

        # Get credentials
        credentials = self._get_credentials_for_method(comm_method.id)
        if not credentials:
            raise ValueError("No credentials found for SSH connection")

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect to target
            ssh.connect(
                hostname=ip_address,
                port=comm_method.config.get("port", 22),
                username=credentials.get("username"),
                password=credentials.get("password"),
                key_filename=credentials.get("key_file"),
                timeout=30
            )

            # Log communication established
            await self._log_execution_event(
                execution.id, branch.id, LogPhase.COMMUNICATION,
                LogLevel.INFO, LogCategory.COMMUNICATION,
                f"SSH connection established to {ip_address}"
            )

            # Get job actions
            actions = execution.job.actions
            if not actions:
                raise ValueError("No actions found for job")

            # Execute each action
            results = []
            for i, action in enumerate(actions, 1):
                result = await self._execute_ssh_action(ssh, action, execution, branch, i)
                results.append(result)

            # Close connection
            ssh.close()

            # Return combined results
            return {
                "success": True,
                "results": results,
                "target_name": target.name,
                "ip_address": ip_address
            }

        except Exception as e:
            if ssh:
                ssh.close()
            raise

    async def _execute_ssh_action(
        self,
        ssh: paramiko.SSHClient,
        action: Any,
        execution: JobExecution,
        branch: JobExecutionBranch,
        action_order: int
    ) -> Dict[str, Any]:
        """Execute a single action via SSH"""
        command = action.action_parameters.get("command", "")
        started_at = datetime.now(timezone.utc)
        
        # Log action execution
        await self._log_execution_event(
            execution.id, branch.id, LogPhase.ACTION_EXECUTION,
            LogLevel.INFO, LogCategory.COMMAND_EXECUTION,
            f"Executing action {action_order}: {command[:50]}..."
        )

        try:
            # Execute command
            stdin, stdout, stderr = ssh.exec_command(command, timeout=300)
            
            # Get output
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            completed_at = datetime.now(timezone.utc)
            execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)

            return {
                "action_id": action.id,
                "action_order": action_order,
                "action_name": action.action_name,
                "action_type": action.action_type.value,
                "command": command,
                "output": output,
                "error": error,
                "exit_code": exit_code,
                "success": exit_code == 0,
                "started_at": started_at,
                "completed_at": completed_at,
                "execution_time_ms": execution_time_ms
            }

        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)
            
            return {
                "action_id": action.id,
                "action_order": action_order,
                "action_name": action.action_name,
                "action_type": action.action_type.value,
                "command": command,
                "output": "",
                "error": str(e),
                "exit_code": -1,
                "success": False,
                "started_at": started_at,
                "completed_at": completed_at,
                "execution_time_ms": execution_time_ms
            }

    async def _execute_winrm_command(
        self,
        target: UniversalTarget,
        comm_method: Any,
        execution: JobExecution,
        branch: JobExecutionBranch
    ) -> Dict[str, Any]:
        """Execute command via WinRM"""
        try:
            import winrm
            logger.info("WinRM import successful")
        except ImportError as e:
            logger.error(f"WinRM import failed: {str(e)}")
            return {
                "results": [{
                    "action_name": "WinRM Command",
                    "output": f"WinRM library not available: {str(e)}",
                    "error": None,
                    "exit_code": -1
                }]
            }
        
        logger.info(f"Starting WinRM execution for target {target.name}")
        ip_address = getTargetIpAddress(target)
        logger.info(f"Target IP address: {ip_address}")
        
        # Log authentication phase
        await self._log_execution_event(
            execution.id, branch.id, LogPhase.AUTHENTICATION,
            LogLevel.INFO, LogCategory.AUTHENTICATION,
            f"Authenticating to {ip_address} via WinRM"
        )

        # Get credentials
        credentials = self._get_credentials_for_method(comm_method.id)
        if not credentials:
            raise ValueError("No credentials found for WinRM connection")

        # Get job actions to execute
        from app.models.job_models import JobAction
        job_actions = self.job_service.db.query(JobAction).filter(
            JobAction.job_id == execution.job_id
        ).all()

        results = []
        
        try:
            # Create WinRM session
            session = winrm.Session(
                f"http://{ip_address}:{comm_method.config.get('port', 5985)}/wsman",
                auth=(credentials.get('username'), credentials.get('password')),
                transport='plaintext',
                server_cert_validation='ignore'
            )

            # Log communication established
            await self._log_execution_event(
                execution.id, branch.id, LogPhase.COMMUNICATION,
                LogLevel.INFO, LogCategory.COMMUNICATION,
                f"WinRM connection established to {ip_address}"
            )

            # Execute each action
            for i, action in enumerate(job_actions, 1):
                if action.action_type == "command":
                    command = action.action_parameters.get("command", "")
                    started_at = datetime.now(timezone.utc)
                    
                    # Log command execution
                    await self._log_execution_event(
                        execution.id, branch.id, LogPhase.ACTION_EXECUTION,
                        LogLevel.INFO, LogCategory.COMMAND_EXECUTION,
                        f"Executing action {i}: {command}"
                    )
                    
                    # Execute command via WinRM
                    response = session.run_cmd(command)
                    completed_at = datetime.now(timezone.utc)
                    execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)
                    
                    results.append({
                        "action_id": action.id,
                        "action_order": i,
                        "action_name": action.action_name,
                        "action_type": action.action_type.value,
                        "command": command,
                        "output": response.std_out.decode('utf-8', errors='ignore') if response.std_out else "",
                        "error": response.std_err.decode('utf-8', errors='ignore') if response.std_err else "",
                        "exit_code": response.status_code,
                        "success": response.status_code == 0,
                        "started_at": started_at,
                        "completed_at": completed_at,
                        "execution_time_ms": execution_time_ms
                    })
                    
                    # Log command completion
                    await self._log_execution_event(
                        execution.id, branch.id, LogPhase.COMPLETION,
                        LogLevel.INFO, LogCategory.COMMAND_EXECUTION,
                        f"Command completed with exit code: {response.status_code}"
                    )

        except Exception as e:
            logger.error(f"WinRM execution failed: {str(e)}")
            # Return error result
            results.append({
                "action_name": "WinRM Command",
                "output": "",
                "error": f"WinRM execution failed: {str(e)}",
                "exit_code": -1
            })

        return {"results": results}

    def _get_branch_for_target(
        self,
        execution_id: int,
        target_id: int
    ) -> Optional[JobExecutionBranch]:
        """Get the execution branch for a specific target"""
        return self.job_service.db.query(JobExecutionBranch).filter(
            JobExecutionBranch.job_execution_id == execution_id,
            JobExecutionBranch.target_id == target_id
        ).first()

    def _get_primary_communication_method(self, target: UniversalTarget) -> Optional[Any]:
        """Get the primary communication method for a target"""
        from app.models.universal_target_models import TargetCommunicationMethod
        # Load communication methods for the target
        target.communication_methods = self.job_service.db.query(TargetCommunicationMethod).filter(
            TargetCommunicationMethod.target_id == target.id,
            TargetCommunicationMethod.is_active == True
        ).all()
        
        # Return primary method
        for method in target.communication_methods:
            if method.is_primary:
                return method
        
        # If no primary, return first active method
        return target.communication_methods[0] if target.communication_methods else None

    def _get_credentials_for_method(self, method_id: int) -> Optional[Dict[str, Any]]:
        """Get credentials for a communication method"""
        from app.models.universal_target_models import TargetCredential
        from app.utils.encryption_utils import decrypt_credentials
        
        credential = self.job_service.db.query(TargetCredential).filter(
            TargetCredential.communication_method_id == method_id,
            TargetCredential.is_primary == True
        ).first()
        
        if credential:
            try:
                # Decrypt the credentials
                decrypted = decrypt_credentials(credential.encrypted_credentials)
                return decrypted
            except Exception as e:
                logger.error(f"Failed to decrypt credentials: {str(e)}")
                return None
        return None

    async def _update_branch_results(
        self,
        branch_id: int,
        result: Dict[str, Any]
    ):
        """Update branch with individual action results"""
        from app.models.job_models import JobActionResult, ExecutionStatus, JobExecutionBranch
        from app.services.serial_service import SerialService
        
        # Get branch serial for action serial generation
        branch = self.job_service.db.query(JobExecutionBranch).filter(
            JobExecutionBranch.id == branch_id
        ).first()
        
        if not branch or not branch.branch_serial:
            logger.error(f"Branch {branch_id} not found or missing branch_serial")
            return
        
        # Store individual action results
        action_results = result.get("results", [])
        overall_success = True
        overall_exit_code = 0
        
        for action_result in action_results:
            # Generate action serial
            action_serial = SerialService.generate_action_serial(
                self.job_service.db, 
                branch.branch_serial
            )
            
            # Create individual action result record
            action_result_record = JobActionResult(
                branch_id=branch_id,
                action_id=action_result.get("action_id", 0),  # Will be set properly in execution
                action_serial=action_serial,
                action_order=action_result.get("action_order", 1),
                action_name=action_result.get("action_name", "Unknown Action"),
                action_type=action_result.get("action_type", "command"),
                status=ExecutionStatus.COMPLETED if action_result.get("success", False) else ExecutionStatus.FAILED,
                started_at=action_result.get("started_at"),
                completed_at=action_result.get("completed_at"),
                execution_time_ms=action_result.get("execution_time_ms"),
                result_output=action_result.get("output"),
                result_error=action_result.get("error"),
                exit_code=action_result.get("exit_code", 0),
                command_executed=action_result.get("command")
            )
            
            self.job_service.db.add(action_result_record)
            
            # Track overall status
            if action_result.get("exit_code", 0) != 0:
                overall_success = False
                overall_exit_code = action_result.get("exit_code", -1)
        
        # Create summary for branch (for backward compatibility)
        summary_output = f"Executed {len(action_results)} actions. See individual action results for details."
        summary_error = None
        
        if not overall_success:
            failed_actions = [ar for ar in action_results if ar.get("exit_code", 0) != 0]
            summary_error = f"{len(failed_actions)} of {len(action_results)} actions failed."

        # Update branch with summary
        self.job_service.update_branch_status(
            branch_id=branch_id,
            status=ExecutionStatus.COMPLETED if overall_success else ExecutionStatus.FAILED,
            result_output=summary_output,
            result_error=summary_error,
            exit_code=overall_exit_code,
            completed_at=datetime.now(timezone.utc)
        )
        
        # Commit the action results
        self.job_service.db.commit()

    async def _update_branch_error(
        self,
        branch_id: int,
        error_message: str
    ):
        """Update branch with error results"""
        self.job_service.update_branch_status(
            branch_id=branch_id,
            status=ExecutionStatus.FAILED,
            result_error=error_message,
            exit_code=-1,
            completed_at=datetime.now(timezone.utc)
        )

    async def _update_execution_complete(
        self,
        execution_id: int,
        status: ExecutionStatus
    ):
        """Update execution as complete and update job status"""
        # Update execution status (this also updates job status automatically)
        execution = self.job_service.update_execution_status(
            execution_id=execution_id,
            status=status,
            completed_at=datetime.now(timezone.utc)
        )
        
        if execution and execution.job:
            job_status = "completed" if status == ExecutionStatus.COMPLETED else "failed"
            logger.info(f"Updated job {execution.job.id} status to {job_status}")

    async def _log_execution_event(
        self,
        execution_id: int,
        branch_id: int,
        phase: LogPhase,
        level: LogLevel,
        category: LogCategory,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log execution events"""
        self.job_service._log_job_event(
            job_id=0,  # Will be set by the service
            execution_id=execution_id,
            branch_id=branch_id,
            phase=phase,
            level=level,
            category=category,
            message=message,
            details=details
        )
