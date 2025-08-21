"""
Job Execution API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.schemas.job_schemas import (
    JobExecutionResponse, JobExecutionDetailResponse, JobExecutionResultResponse
)
from app.services.execution_service import JobExecutionService
from app.services.auth_service import get_current_user
from app.models.job_models import JobExecution, JobExecutionResult, ExecutionStatus
from app.tasks.job_tasks import cancel_job_execution, retry_failed_execution

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{execution_id}", response_model=JobExecutionDetailResponse)
async def get_execution(
    execution_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get execution details with results"""
    try:
        execution = db.query(JobExecution).filter(
            JobExecution.id == execution_id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Get execution results
        results = db.query(JobExecutionResult).filter(
            JobExecutionResult.execution_id == execution_id
        ).order_by(
            JobExecutionResult.target_name,
            JobExecutionResult.action_order
        ).all()
        
        # Build response
        execution_response = JobExecutionResponse(
            id=execution.id,
            uuid=execution.uuid,
            job_id=execution.job_id,
            execution_number=execution.execution_number,
            status=execution.status,
            triggered_by=execution.triggered_by,
            triggered_by_user=execution.triggered_by_user,
            scheduled_at=execution.scheduled_at,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            created_at=execution.created_at,
            total_targets=execution.total_targets,
            successful_targets=execution.successful_targets,
            failed_targets=execution.failed_targets,
            execution_time_seconds=execution.execution_time_seconds,
            error_message=execution.error_message,
            retry_count=execution.retry_count
        )
        
        result_responses = [
            JobExecutionResultResponse(
                id=result.id,
                execution_id=result.execution_id,
                target_id=result.target_id,
                target_name=result.target_name,
                action_id=result.action_id,
                action_order=result.action_order,
                action_name=result.action_name,
                action_type=result.action_type,
                status=result.status,
                started_at=result.started_at,
                completed_at=result.completed_at,
                execution_time_ms=result.execution_time_ms,
                output_text=result.output_text,
                error_text=result.error_text,
                exit_code=result.exit_code,
                command_executed=result.command_executed,
                connection_method=result.connection_method,
                connection_host=result.connection_host,
                retry_count=result.retry_count,
                is_retry=result.is_retry
            )
            for result in results
        ]
        
        job_info = {
            "id": execution.job.id,
            "name": execution.job.name,
            "description": execution.job.description,
            "job_type": execution.job.job_type.value,
            "created_by": execution.job.created_by
        }
        
        return JobExecutionDetailResponse(
            execution=execution_response,
            results=result_responses,
            job_info=job_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get execution")


@router.get("/{execution_id}/results", response_model=List[JobExecutionResultResponse])
async def get_execution_results(
    execution_id: int,
    target_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get execution results with optional filtering"""
    try:
        query = db.query(JobExecutionResult).filter(
            JobExecutionResult.execution_id == execution_id
        )
        
        if target_id:
            query = query.filter(JobExecutionResult.target_id == target_id)
        
        if status:
            query = query.filter(JobExecutionResult.status == status)
        
        results = query.order_by(
            JobExecutionResult.target_name,
            JobExecutionResult.action_order
        ).all()
        
        return [
            JobExecutionResultResponse(
                id=result.id,
                execution_id=result.execution_id,
                target_id=result.target_id,
                target_name=result.target_name,
                action_id=result.action_id,
                action_order=result.action_order,
                action_name=result.action_name,
                action_type=result.action_type,
                status=result.status,
                started_at=result.started_at,
                completed_at=result.completed_at,
                execution_time_ms=result.execution_time_ms,
                output_text=result.output_text,
                error_text=result.error_text,
                exit_code=result.exit_code,
                command_executed=result.command_executed,
                connection_method=result.connection_method,
                connection_host=result.connection_host,
                retry_count=result.retry_count,
                is_retry=result.is_retry
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Failed to get execution results for {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get execution results")


@router.post("/{execution_id}/cancel", response_model=dict)
async def cancel_execution(
    execution_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel running execution"""
    try:
        execution = db.query(JobExecution).filter(
            JobExecution.id == execution_id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        if execution.status != ExecutionStatus.RUNNING:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel execution with status: {execution.status}"
            )
        
        # Queue cancellation task
        task = cancel_job_execution.delay(execution_id)
        
        logger.info(f"Queued cancellation for execution {execution_id} by user {current_user['id']}")
        
        return {
            "execution_id": execution_id,
            "status": "cancellation_queued",
            "task_id": task.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel execution")


@router.post("/{execution_id}/retry", response_model=dict)
async def retry_execution(
    execution_id: int,
    target_ids: Optional[List[int]] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retry failed execution"""
    try:
        execution = db.query(JobExecution).filter(
            JobExecution.id == execution_id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        if execution.status != ExecutionStatus.FAILED:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot retry execution with status: {execution.status}"
            )
        
        # Queue retry task
        task = retry_failed_execution.delay(execution_id, target_ids)
        
        logger.info(f"Queued retry for execution {execution_id} by user {current_user['id']}")
        
        return {
            "original_execution_id": execution_id,
            "status": "retry_queued",
            "task_id": task.id,
            "retry_targets": target_ids or "all_failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retry execution")


@router.get("/{execution_id}/logs", response_model=dict)
async def get_execution_logs(
    execution_id: int,
    target_id: Optional[int] = Query(None),
    action_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get execution logs"""
    try:
        query = db.query(JobExecutionResult).filter(
            JobExecutionResult.execution_id == execution_id
        )
        
        if target_id:
            query = query.filter(JobExecutionResult.target_id == target_id)
        
        if action_id:
            query = query.filter(JobExecutionResult.action_id == action_id)
        
        results = query.order_by(
            JobExecutionResult.target_name,
            JobExecutionResult.action_order,
            JobExecutionResult.started_at
        ).all()
        
        logs = []
        for result in results:
            log_entry = {
                "target_id": result.target_id,
                "target_name": result.target_name,
                "action_id": result.action_id,
                "action_name": result.action_name,
                "action_order": result.action_order,
                "status": result.status.value,
                "started_at": result.started_at,
                "completed_at": result.completed_at,
                "execution_time_ms": result.execution_time_ms,
                "command_executed": result.command_executed,
                "output": result.output_text,
                "error": result.error_text,
                "exit_code": result.exit_code,
                "connection_method": result.connection_method,
                "connection_host": result.connection_host
            }
            logs.append(log_entry)
        
        return {
            "execution_id": execution_id,
            "log_count": len(logs),
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"Failed to get logs for execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get execution logs")