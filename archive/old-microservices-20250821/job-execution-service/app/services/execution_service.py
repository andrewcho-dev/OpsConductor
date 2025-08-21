"""
Job Execution Service - Core Execution Logic
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.execution_models import JobExecution, JobExecutionResult
from opsconductor_shared.models.base import ExecutionStatus, EventType, ServiceType
from opsconductor_shared.events.publisher import EventPublisher
from opsconductor_shared.clients.base_client import BaseServiceClient
from app.core.config import settings
from app.utils.connection_manager import ConnectionManager
from app.utils.safety_checker import SafetyChecker

logger = logging.getLogger(__name__)


class ExecutionService:
    """Core job execution business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.event_publisher = EventPublisher(settings.rabbitmq_url)
        self.connection_manager = ConnectionManager()
        self.safety_checker = SafetyChecker()
        
        # External service clients
        self.job_management_client = BaseServiceClient(
            ServiceType.JOB_EXECUTION,
            settings.job_management_service_url
        )
        self.target_client = BaseServiceClient(
            ServiceType.JOB_EXECUTION,
            settings.target_service_url
        )
        
        # Execution configuration
        self.max_concurrent = settings.max_concurrent_targets
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def create_execution(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job execution"""
        try:
            job_id = execution_data["job_id"]
            job_uuid = execution_data["job_uuid"]
            
            # Get job details from job management service
            job_response = await self.job_management_client.get(f"/api/v1/jobs/{job_id}")
            if not job_response.success:
                raise ValueError(f"Failed to get job details: {job_response.message}")
            
            job_data = job_response.data
            
            # Determine target IDs
            target_ids = execution_data.get("target_ids")
            if not target_ids:
                # Use all job targets
                target_ids = [t["target_id"] for t in job_data.get("targets", [])]
            
            if not target_ids:
                raise ValueError("No targets specified for execution")
            
            # Get next execution number
            max_execution = self.db.query(JobExecution.execution_number).filter(
                JobExecution.job_id == job_id
            ).order_by(JobExecution.execution_number.desc()).first()
            
            execution_number = (max_execution[0] if max_execution else 0) + 1
            
            # Create execution record
            execution = JobExecution(
                job_id=job_id,
                job_uuid=job_uuid,
                execution_number=execution_number,
                status=ExecutionStatus.SCHEDULED.value,
                triggered_by="api",
                triggered_by_user=execution_data.get("executed_by"),
                execution_context=execution_data.get("execution_context"),
                scheduled_at=datetime.now(timezone.utc),
                total_targets=len(target_ids)
            )
            
            self.db.add(execution)
            self.db.commit()
            
            # Queue execution task
            from app.tasks.execution_tasks import execute_job_task
            execute_job_task.delay(execution.id, target_ids)
            
            # Publish event
            self.event_publisher.publish_event(
                event_type=EventType.EXECUTION_STARTED,
                service_name=ServiceType.JOB_EXECUTION,
                data={
                    "execution_id": execution.id,
                    "execution_uuid": str(execution.uuid),
                    "job_id": job_id,
                    "job_uuid": str(job_uuid),
                    "target_count": len(target_ids)
                },
                user_id=execution_data.get("executed_by")
            )
            
            logger.info(f"Created execution {execution.id} for job {job_id} on {len(target_ids)} targets")
            
            return {
                "execution_id": execution.id,
                "execution_uuid": str(execution.uuid),
                "job_id": job_id,
                "status": execution.status,
                "target_count": len(target_ids),
                "scheduled_at": execution.scheduled_at
            }
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create execution: {e}")
            raise
    
    async def execute_on_targets(self, execution: JobExecution, target_ids: List[int]) -> Dict[str, Any]:
        """Execute job on multiple targets concurrently"""
        logger.info(f"🚀 Starting execution {execution.id} on {len(target_ids)} targets")
        execution_start_time = time.time()
        
        try:
            # Update execution status
            execution.status = ExecutionStatus.RUNNING.value
            execution.started_at = datetime.now(timezone.utc)
            self.db.commit()
            
            # Get job details
            job_response = await self.job_management_client.get(f"/api/v1/jobs/{execution.job_id}")
            if not job_response.success:
                raise ValueError(f"Failed to get job details: {job_response.message}")
            
            job_data = job_response.data
            actions = job_data.get("actions", [])
            
            if not actions:
                raise ValueError(f"No actions found for job {execution.job_id}")
            
            # Get target details
            target_response = await self.target_client.post(
                "/api/v3/targets/batch",
                {"target_ids": target_ids}
            )
            
            if not target_response.success:
                raise ValueError(f"Failed to get target details: {target_response.message}")
            
            targets = target_response.data.get("targets", [])
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
                execution.status = ExecutionStatus.FAILED.value
            else:
                execution.status = ExecutionStatus.COMPLETED.value
            
            execution.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            
            # Publish completion event
            event_type = EventType.EXECUTION_COMPLETED if execution.status == ExecutionStatus.COMPLETED.value else EventType.EXECUTION_FAILED
            
            self.event_publisher.publish_event(
                event_type=event_type,
                service_name=ServiceType.JOB_EXECUTION,
                data={
                    "execution_id": execution.id,
                    "execution_uuid": str(execution.uuid),
                    "job_id": execution.job_id,
                    "job_uuid": str(execution.job_uuid),
                    "status": execution.status,
                    "total_targets": len(targets),
                    "successful_targets": successful_targets,
                    "failed_targets": failed_targets,
                    "execution_time": execution.execution_time_seconds
                },
                user_id=execution.triggered_by_user
            )
            
            logger.info(f"✅ Execution {execution.id} completed in {execution.execution_time_seconds:.2f}s: {successful_targets} success, {failed_targets} failed")
            
            return {
                "execution_id": execution.id,
                "status": execution.status,
                "total_targets": len(targets),
                "successful_targets": successful_targets,
                "failed_targets": failed_targets,
                "execution_time": execution.execution_time_seconds
            }
            
        except Exception as e:
            logger.error(f"Execution {execution.id} failed: {e}")
            execution.status = ExecutionStatus.FAILED.value
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            execution.execution_time_seconds = time.time() - execution_start_time
            self.db.commit()
            
            # Publish failure event
            self.event_publisher.publish_event(
                event_type=EventType.EXECUTION_FAILED,
                service_name=ServiceType.JOB_EXECUTION,
                data={
                    "execution_id": execution.id,
                    "execution_uuid": str(execution.uuid),
                    "job_id": execution.job_id,
                    "job_uuid": str(execution.job_uuid),
                    "error": str(e)
                },
                user_id=execution.triggered_by_user
            )
            
            raise
    
    async def _execute_on_target(
        self, 
        execution: JobExecution, 
        target: Dict[str, Any], 
        actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute job on a single target"""
        async with self.semaphore:  # Limit concurrent executions
            logger.info(f"🎯 Executing on target: {target['name']}")
            
            try:
                # Execute each action
                all_success = True
                for action in actions:
                    try:
                        result = await self._execute_action(execution, target, action)
                        if not result.get('success', False):
                            all_success = False
                            
                    except Exception as e:
                        logger.error(f"Action {action['action_name']} failed on {target['name']}: {e}")
                        self._create_failed_result(execution, target, action, str(e))
                        all_success = False
                
                return {"success": all_success, "target": target['name']}
                
            except Exception as e:
                logger.error(f"Target execution failed for {target['name']}: {e}")
                return {"success": False, "target": target['name'], "error": str(e)}
    
    async def _execute_action(
        self,
        execution: JobExecution,
        target: Dict[str, Any],
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single action on a target"""
        start_time = time.time()
        
        try:
            logger.info(f"🔧 Executing action '{action['action_name']}' on {target['name']}")
            
            # Safety check
            if settings.enable_safety_checks:
                safety_result = self.safety_checker.check_action_safety(action)
                if not safety_result["safe"]:
                    error_msg = f"Action blocked by safety check: {safety_result['reason']}"
                    logger.warning(error_msg)
                    self._create_failed_result(execution, target, action, error_msg)
                    return {"success": False, "error": error_msg}
            
            # Execute action using connection manager
            result = await self.connection_manager.execute_action(target, action)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Create execution result record
            self._create_execution_result(
                execution=execution,
                target=target,
                action=action,
                result=result,
                execution_time_ms=execution_time_ms
            )
            
            return result
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            logger.error(f"Action execution failed: {error_msg}")
            
            self._create_failed_result(execution, target, action, error_msg, execution_time_ms)
            return {"success": False, "error": error_msg}
    
    def _create_execution_result(
        self,
        execution: JobExecution,
        target: Dict[str, Any],
        action: Dict[str, Any],
        result: Dict[str, Any],
        execution_time_ms: int
    ):
        """Create execution result record"""
        execution_result = JobExecutionResult(
            execution_id=execution.id,
            target_id=target["id"],
            target_name=target["name"],
            action_id=action["id"],
            action_order=action["action_order"],
            action_name=action["action_name"],
            action_type=action["action_type"],
            status=ExecutionStatus.COMPLETED.value if result.get("success") else ExecutionStatus.FAILED.value,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            execution_time_ms=execution_time_ms,
            output_text=result.get("output"),
            error_text=result.get("error"),
            exit_code=result.get("exit_code"),
            command_executed=result.get("command"),
            connection_method=result.get("connection_method"),
            connection_host=target.get("host"),
            connection_port=target.get("port")
        )
        
        self.db.add(execution_result)
        self.db.commit()
    
    def _create_failed_result(
        self,
        execution: JobExecution,
        target: Dict[str, Any],
        action: Dict[str, Any],
        error_message: str,
        execution_time_ms: int = 0
    ):
        """Create failed execution result record"""
        execution_result = JobExecutionResult(
            execution_id=execution.id,
            target_id=target["id"],
            target_name=target["name"],
            action_id=action["id"],
            action_order=action["action_order"],
            action_name=action["action_name"],
            action_type=action["action_type"],
            status=ExecutionStatus.FAILED.value,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            execution_time_ms=execution_time_ms,
            error_text=error_message,
            connection_host=target.get("host"),
            connection_port=target.get("port")
        )
        
        self.db.add(execution_result)
        self.db.commit()
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'event_publisher'):
            self.event_publisher.close()