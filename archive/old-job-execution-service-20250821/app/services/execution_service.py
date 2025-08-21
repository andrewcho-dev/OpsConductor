"""
Job Execution Service
Handles the actual execution of jobs on targets
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.job_models import (
    Job, JobExecution, JobExecutionResult, JobAction,
    ExecutionStatus, ActionType
)
from app.services.external_services import target_service
from app.core.config import settings
from app.utils.connection_utils import SSHConnectionManager, WinRMConnectionManager
from app.utils.safety_utils import SafetyChecker

logger = logging.getLogger(__name__)


class JobExecutionService:
    """Service for executing jobs on targets"""
    
    def __init__(self, db: Session):
        self.db = db
        self.max_concurrent = settings.max_concurrent_targets
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.connection_timeout = settings.connection_timeout
        self.command_timeout = settings.command_timeout
        self.enable_retry = settings.enable_retry
        self.max_retries = settings.max_retries
        self.retry_backoff_base = settings.retry_backoff_base
        self.safety_checker = SafetyChecker()
    
    async def execute_job_on_targets(
        self, 
        execution: JobExecution, 
        target_ids: List[int]
    ) -> Dict[str, Any]:
        """Execute a job on multiple targets concurrently"""
        logger.info(f"🚀 Starting execution {execution.id} on {len(target_ids)} targets")
        execution_start_time = time.time()
        
        try:
            # Update execution status
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.now(timezone.utc)
            self.db.commit()
            
            # Get job and actions
            job = execution.job
            actions = sorted(job.actions, key=lambda a: a.action_order)
            
            if not actions:
                raise ValueError(f"No actions found for job {job.id}")
            
            # Get target details
            targets = await target_service.get_targets(target_ids)
            if len(targets) != len(target_ids):
                found_ids = {t["id"] for t in targets}
                missing_ids = set(target_ids) - found_ids
                raise ValueError(f"Targets not found: {missing_ids}")
            
            # Create tasks for each target
            tasks = []
            for target in targets:
                task = asyncio.create_task(
                    self._execute_on_target(execution, target, actions)
                )
                tasks.append(task)
            
            # Execute all targets concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_targets = 0
            failed_targets = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Target {targets[i]['name']} failed: {str(result)}")
                    failed_targets += 1
                else:
                    if result.get('success', False):
                        successful_targets += 1
                    else:
                        failed_targets += 1
            
            # Update execution summary
            execution.successful_targets = successful_targets
            execution.failed_targets = failed_targets
            execution.execution_time_seconds = time.time() - execution_start_time
            
            if failed_targets > 0:
                execution.status = ExecutionStatus.FAILED
            else:
                execution.status = ExecutionStatus.COMPLETED
            
            execution.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"✅ Execution {execution.id} completed in {execution.execution_time_seconds:.2f}s: {successful_targets} success, {failed_targets} failed")
            
            return {
                "execution_id": execution.id,
                "total_targets": len(targets),
                "successful_targets": successful_targets,
                "failed_targets": failed_targets,
                "execution_time": execution.execution_time_seconds
            }
            
        except Exception as e:
            logger.error(f"Execution {execution.id} failed: {e}")
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            execution.execution_time_seconds = time.time() - execution_start_time
            self.db.commit()
            raise
    
    async def _execute_on_target(
        self, 
        execution: JobExecution, 
        target: Dict[str, Any], 
        actions: List[JobAction]
    ) -> Dict[str, Any]:
        """Execute job on a single target"""
        async with self.semaphore:  # Limit concurrent executions
            logger.info(f"🎯 Executing on target: {target['name']}")
            
            try:
                # Get target credentials
                credentials = await target_service.get_target_credentials(target["id"])
                if not credentials:
                    raise ValueError(f"No credentials found for target {target['name']}")
                
                # Determine connection method
                connection_method = self._get_connection_method(target, credentials)
                
                # Execute each action
                all_success = True
                for action in actions:
                    try:
                        if self.enable_retry:
                            result = await self._execute_action_with_retry(
                                execution, target, action, connection_method, credentials
                            )
                        else:
                            result = await self._execute_action(
                                execution, target, action, connection_method, credentials
                            )
                        
                        if not result.get('success', False):
                            all_success = False
                            
                    except Exception as e:
                        logger.error(f"Action {action.action_name} failed on {target['name']}: {e}")
                        self._create_failed_result(execution, target, action, str(e))
                        all_success = False
                
                return {"success": all_success, "target": target['name']}
                
            except Exception as e:
                logger.error(f"Target execution failed for {target['name']}: {e}")
                return {"success": False, "target": target['name'], "error": str(e)}
    
    async def _execute_action_with_retry(
        self,
        execution: JobExecution,
        target: Dict[str, Any],
        action: JobAction,
        connection_method: str,
        credentials: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Execute action with retry logic"""
        try:
            result = await self._execute_action(
                execution, target, action, connection_method, credentials
            )
            
            # If successful or retries disabled, return result
            if result.get('success', False) or not self.enable_retry:
                return result
            
            # Check if error is retriable
            if not result.get('retriable', False):
                logger.info(f"⚠️ Error is not retriable for action '{action.action_name}' on {target['name']}")
                return result
            
            # If we've reached max retries, return failed result
            if retry_count >= self.max_retries:
                logger.warning(f"⚠️ Max retries ({self.max_retries}) reached for action '{action.action_name}' on {target['name']}")
                result['retries_exhausted'] = True
                return result
            
            # Calculate backoff time
            backoff_seconds = self.retry_backoff_base ** retry_count
            logger.info(f"🔄 Retrying action '{action.action_name}' on {target['name']} in {backoff_seconds:.2f}s (attempt {retry_count + 1}/{self.max_retries})")
            
            # Wait for backoff period
            await asyncio.sleep(backoff_seconds)
            
            # Retry the action
            return await self._execute_action_with_retry(
                execution, target, action, connection_method, credentials, retry_count + 1
            )
            
        except Exception as e:
            logger.error(f"❌ Retry mechanism failed: {e}")
            return {"success": False, "error": f"Retry mechanism failed: {e}"}
    
    async def _execute_action(
        self,
        execution: JobExecution,
        target: Dict[str, Any],
        action: JobAction,
        connection_method: str,
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single action on a target"""
        start_time = time.time()
        
        try:
            logger.info(f"🔧 Executing action '{action.action_name}' on {target['name']}")
            
            # Safety check
            if settings.enable_safety_checks:
                safety_result = self.safety_checker.check_action_safety(action)
                if not safety_result["safe"]:
                    error_msg = f"Action blocked by safety check: {safety_result['reason']}"
                    logger.warning(error_msg)
                    self._create_failed_result(execution, target, action, error_msg)
                    return {"success": False, "error": error_msg, "retriable": False}
            
            # Execute based on action type and connection method
            if action.action_type == ActionType.COMMAND:
                result = await self._execute_command(
                    target, action, connection_method, credentials
                )
            elif action.action_type == ActionType.SCRIPT:
                result = await self._execute_script(
                    target, action, connection_method, credentials
                )
            elif action.action_type == ActionType.FILE_TRANSFER:
                result = await self._execute_file_transfer(
                    target, action, connection_method, credentials
                )
            else:
                raise ValueError(f"Unsupported action type: {action.action_type}")
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Create execution result record
            self._create_execution_result(
                execution=execution,
                target=target,
                action=action,
                result=result,
                execution_time_ms=execution_time_ms,
                connection_method=connection_method
            )
            
            return result
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            logger.error(f"Action execution failed: {error_msg}")
            
            self._create_failed_result(
                execution, target, action, error_msg, execution_time_ms
            )
            
            return {
                "success": False, 
                "error": error_msg, 
                "retriable": self._is_retriable_error(error_msg)
            }
    
    async def _execute_command(
        self,
        target: Dict[str, Any],
        action: JobAction,
        connection_method: str,
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute command action"""
        command = action.action_parameters.get("command")
        if not command:
            raise ValueError("No command specified in action parameters")
        
        if connection_method == "ssh":
            manager = SSHConnectionManager()
            return await manager.execute_command(target, credentials, command, self.command_timeout)
        elif connection_method == "winrm":
            manager = WinRMConnectionManager()
            return await manager.execute_command(target, credentials, command, self.command_timeout)
        else:
            raise ValueError(f"Unsupported connection method: {connection_method}")
    
    async def _execute_script(
        self,
        target: Dict[str, Any],
        action: JobAction,
        connection_method: str,
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute script action"""
        script_content = action.action_parameters.get("script_content")
        script_type = action.action_parameters.get("script_type", "bash")
        
        if not script_content:
            raise ValueError("No script content specified in action parameters")
        
        if connection_method == "ssh":
            manager = SSHConnectionManager()
            return await manager.execute_script(target, credentials, script_content, script_type, self.command_timeout)
        elif connection_method == "winrm":
            manager = WinRMConnectionManager()
            return await manager.execute_script(target, credentials, script_content, script_type, self.command_timeout)
        else:
            raise ValueError(f"Unsupported connection method: {connection_method}")
    
    async def _execute_file_transfer(
        self,
        target: Dict[str, Any],
        action: JobAction,
        connection_method: str,
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute file transfer action"""
        operation = action.action_parameters.get("operation")  # upload or download
        local_path = action.action_parameters.get("local_path")
        remote_path = action.action_parameters.get("remote_path")
        
        if not all([operation, local_path, remote_path]):
            raise ValueError("File transfer requires operation, local_path, and remote_path")
        
        if connection_method == "ssh":
            manager = SSHConnectionManager()
            if operation == "upload":
                return await manager.upload_file(target, credentials, local_path, remote_path)
            else:
                return await manager.download_file(target, credentials, remote_path, local_path)
        elif connection_method == "winrm":
            manager = WinRMConnectionManager()
            if operation == "upload":
                return await manager.upload_file(target, credentials, local_path, remote_path)
            else:
                return await manager.download_file(target, credentials, remote_path, local_path)
        else:
            raise ValueError(f"Unsupported connection method: {connection_method}")
    
    def _get_connection_method(self, target: Dict[str, Any], credentials: Dict[str, Any]) -> str:
        """Determine the best connection method for target"""
        target_type = target.get("type", "").lower()
        
        if target_type in ["windows", "win"]:
            return "winrm"
        else:
            return "ssh"
    
    def _create_execution_result(
        self,
        execution: JobExecution,
        target: Dict[str, Any],
        action: JobAction,
        result: Dict[str, Any],
        execution_time_ms: int,
        connection_method: str
    ):
        """Create execution result record"""
        execution_result = JobExecutionResult(
            execution_id=execution.id,
            target_id=target["id"],
            target_name=target["name"],
            action_id=action.id,
            action_order=action.action_order,
            action_name=action.action_name,
            action_type=action.action_type,
            status=ExecutionStatus.COMPLETED if result.get("success") else ExecutionStatus.FAILED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            execution_time_ms=execution_time_ms,
            output_text=result.get("output"),
            error_text=result.get("error"),
            exit_code=result.get("exit_code"),
            command_executed=result.get("command"),
            connection_method=connection_method,
            connection_host=target.get("host"),
            connection_port=target.get("port")
        )
        
        self.db.add(execution_result)
        self.db.commit()
    
    def _create_failed_result(
        self,
        execution: JobExecution,
        target: Dict[str, Any],
        action: JobAction,
        error_message: str,
        execution_time_ms: int = 0
    ):
        """Create failed execution result record"""
        execution_result = JobExecutionResult(
            execution_id=execution.id,
            target_id=target["id"],
            target_name=target["name"],
            action_id=action.id,
            action_order=action.action_order,
            action_name=action.action_name,
            action_type=action.action_type,
            status=ExecutionStatus.FAILED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            execution_time_ms=execution_time_ms,
            error_text=error_message,
            connection_host=target.get("host"),
            connection_port=target.get("port")
        )
        
        self.db.add(execution_result)
        self.db.commit()
    
    def _is_retriable_error(self, error_message: str) -> bool:
        """Determine if an error is retriable"""
        retriable_patterns = [
            "connection timeout",
            "connection refused",
            "network unreachable",
            "temporary failure",
            "service unavailable"
        ]
        
        error_lower = error_message.lower()
        return any(pattern in error_lower for pattern in retriable_patterns)