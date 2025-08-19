"""
Jobs API v3 - SIMPLIFIED
No serialization complexity, just clean IDs and execution tracking
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.services.job_service import JobService
from app.services.job_scheduling_service import JobSchedulingService
from app.models.job_models import JobStatus, ExecutionStatus, ActionType
from app.tasks.job_tasks import execute_job_task
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{os.getenv(\'API_BASE_URL\', \'/api/v3\')}/jobs", tags=["Jobs v3 - Simplified"])


# SIMPLIFIED MODELS
class ActionCreate(BaseModel):
    action_type: ActionType = Field(default=ActionType.COMMAND)
    action_name: str = Field(..., min_length=1, max_length=255)
    action_parameters: Dict[str, Any] = Field(default_factory=dict)


class JobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    actions: List[ActionCreate] = Field(..., min_items=1)
    target_ids: List[int] = Field(..., min_items=1)
    scheduled_at: Optional[datetime] = None


class JobUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    actions: Optional[List[ActionCreate]] = Field(None, min_items=1)
    target_ids: Optional[List[int]] = Field(None, min_items=1)
    scheduled_at: Optional[datetime] = None


class JobExecuteRequest(BaseModel):
    target_ids: Optional[List[int]] = None  # If None, use all job targets


class ActionResponse(BaseModel):
    id: int
    action_order: int
    action_name: str
    action_type: ActionType
    action_parameters: Dict[str, Any]


class TargetResponse(BaseModel):
    id: int
    name: str


class JobResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: JobStatus
    created_at: datetime
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    last_execution: Optional[Dict[str, Any]] = None
    actions: Optional[List[ActionResponse]] = None
    targets: Optional[List[TargetResponse]] = None
    schedule_config: Optional[Dict[str, Any]] = None


class ExecutionResponse(BaseModel):
    id: int
    job_id: int
    execution_number: int
    status: ExecutionStatus
    total_targets: int
    successful_targets: int
    failed_targets: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    duration_seconds: Optional[float] = None
    target_names: Optional[List[str]] = None


class ExecutionResultResponse(BaseModel):
    id: int
    execution_id: int
    target_id: int
    target_name: str
    action_name: str
    action_type: ActionType
    status: ExecutionStatus
    output_text: Optional[str]
    error_text: Optional[str]
    exit_code: Optional[int]
    execution_time_ms: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


# API ENDPOINTS

@router.post("/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job - SIMPLIFIED"""
    try:
        job_service = JobService(db)
        
        # Convert to internal format
        from app.schemas.job_schemas import JobCreate as InternalJobCreate, JobActionCreate
        
        internal_actions = [
            JobActionCreate(
                action_type=action.action_type,
                action_name=action.action_name,
                action_parameters=action.action_parameters
            )
            for action in job_data.actions
        ]
        
        internal_job_data = InternalJobCreate(
            name=job_data.name,
            description=job_data.description,
            actions=internal_actions,
            target_ids=job_data.target_ids,
            scheduled_at=job_data.scheduled_at
        )
        
        job = job_service.create_job(internal_job_data, current_user["id"])
        
        return JobResponse(
            id=job.id,
            name=job.name,
            description=job.description,
            status=job.status,
            created_at=job.created_at,
            scheduled_at=job.scheduled_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List jobs - SIMPLIFIED"""
    try:
        job_service = JobService(db)
        jobs = job_service.list_jobs(skip=skip, limit=limit)
        
        # Build response with last execution data
        job_responses = []
        for job in jobs:
            # Get the most recent execution for this job
            last_execution = None
            if job.executions:
                # Sort executions by started_at descending to get the most recent
                sorted_executions = sorted(job.executions, key=lambda e: e.started_at or e.created_at, reverse=True)
                if sorted_executions:
                    latest_exec = sorted_executions[0]
                    last_execution = {
                        "id": latest_exec.id,
                        "execution_number": latest_exec.execution_number,
                        "status": latest_exec.status.value if hasattr(latest_exec.status, 'value') else str(latest_exec.status),
                        "started_at": latest_exec.started_at,
                        "completed_at": latest_exec.completed_at,
                        "total_targets": latest_exec.total_targets,
                        "successful_targets": latest_exec.successful_targets,
                        "failed_targets": latest_exec.failed_targets
                    }
            
            job_responses.append(JobResponse(
                id=job.id,
                name=job.name,
                description=job.description,
                status=job.status,
                created_at=job.created_at,
                scheduled_at=job.scheduled_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                last_execution=last_execution
            ))
        
        return job_responses
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get job by ID - SIMPLIFIED"""
    try:
        job_service = JobService(db)
        job = job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get the most recent execution for this job
        last_execution = None
        if job.executions:
            # Sort executions by started_at descending to get the most recent
            sorted_executions = sorted(job.executions, key=lambda e: e.started_at or e.created_at, reverse=True)
            if sorted_executions:
                latest_exec = sorted_executions[0]
                last_execution = {
                    "id": latest_exec.id,
                    "execution_number": latest_exec.execution_number,
                    "status": latest_exec.status.value if hasattr(latest_exec.status, 'value') else str(latest_exec.status),
                    "started_at": latest_exec.started_at,
                    "completed_at": latest_exec.completed_at,
                    "total_targets": latest_exec.total_targets,
                    "successful_targets": latest_exec.successful_targets,
                    "failed_targets": latest_exec.failed_targets
                }
            
        # Get actions
        actions = [
            ActionResponse(
                id=action.id,
                action_order=action.action_order,
                action_name=action.action_name,
                action_type=action.action_type,
                action_parameters=action.action_parameters
            )
            for action in job.actions
        ]
        
        # Get targets
        targets = [
            TargetResponse(
                id=target.target.id,
                name=target.target.name
            )
            for target in job.targets
        ]
        
        # Get schedule configuration
        schedule_config = None
        try:
            scheduling_service = JobSchedulingService(db)
            schedules = scheduling_service.get_job_schedules(job.id)
            if schedules:
                # Get the most recent active schedule
                active_schedule = next((s for s in schedules if s.enabled), None)
                if active_schedule:
                    schedule_config = {
                        "scheduleType": active_schedule.schedule_type,
                        "enabled": active_schedule.enabled,
                        "executeAt": active_schedule.execute_at,
                        "recurringType": active_schedule.recurring_type,
                        "interval": active_schedule.interval,
                        "time": active_schedule.time,
                        "daysOfWeek": active_schedule.days_of_week,
                        "dayOfMonth": active_schedule.day_of_month,
                        "cronExpression": active_schedule.cron_expression,
                        "timezone": active_schedule.timezone,
                        "nextRun": active_schedule.next_run
                    }
        except Exception as e:
            logger.warning(f"Failed to get schedule config for job {job.id}: {str(e)}")
        
        return JobResponse(
            id=job.id,
            name=job.name,
            description=job.description,
            status=job.status,
            created_at=job.created_at,
            scheduled_at=job.scheduled_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            last_execution=last_execution,
            actions=actions,
            targets=targets,
            schedule_config=schedule_config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/execute", response_model=ExecutionResponse)
async def execute_job(
    job_id: int,
    execute_data: JobExecuteRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Execute a job - SIMPLIFIED"""
    try:
        job_service = JobService(db)
        
        # Convert to internal format
        from app.schemas.job_schemas import JobExecuteRequest as InternalExecuteRequest
        internal_execute_data = InternalExecuteRequest(target_ids=execute_data.target_ids)
        
        execution = job_service.execute_job(job_id, internal_execute_data)
        
        # Get target IDs for Celery task
        if execute_data.target_ids:
            target_ids = execute_data.target_ids
        else:
            job = job_service.get_job(job_id)
            target_ids = [jt.target_id for jt in job.targets]
        
        # Queue the execution task
        execute_job_task.delay(execution.id, target_ids)
        
        return ExecutionResponse(
            id=execution.id,
            job_id=execution.job_id,
            execution_number=execution.execution_number,
            status=execution.status,
            total_targets=execution.total_targets,
            successful_targets=execution.successful_targets,
            failed_targets=execution.failed_targets,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            created_at=execution.created_at
        )
        
    except Exception as e:
        logger.error(f"Failed to execute job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/executions", response_model=List[ExecutionResponse])
async def get_job_executions(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all executions for a job - SIMPLIFIED"""
    try:
        job_service = JobService(db)
        
        from app.models.job_models import JobExecution, JobExecutionResult
        from app.models.universal_target_models import UniversalTarget
        
        executions = db.query(JobExecution).filter(JobExecution.job_id == job_id).order_by(JobExecution.execution_number.desc()).all()
        
        execution_responses = []
        for execution in executions:
            # Calculate duration
            duration_seconds = None
            if execution.started_at and execution.completed_at:
                duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
            # Get target names for this execution
            target_names = []
            results = db.query(JobExecutionResult).filter(JobExecutionResult.execution_id == execution.id).all()
            unique_target_names = set()
            for result in results:
                if result.target_name:
                    unique_target_names.add(result.target_name)
            target_names = list(unique_target_names)
            
            execution_responses.append(ExecutionResponse(
                id=execution.id,
                job_id=execution.job_id,
                execution_number=execution.execution_number,
                status=execution.status,
                total_targets=execution.total_targets,
                successful_targets=execution.successful_targets,
                failed_targets=execution.failed_targets,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                created_at=execution.created_at,
                duration_seconds=duration_seconds,
                target_names=target_names
            ))
        
        return execution_responses
        
    except Exception as e:
        logger.error(f"Failed to get executions for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/executions/{execution_number}/results", response_model=List[ExecutionResultResponse])
async def get_execution_results(
    job_id: int,
    execution_number: int,
    target_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get execution results - SIMPLIFIED"""
    try:
        job_service = JobService(db)
        
        # Find the execution
        from app.models.job_models import JobExecution
        execution = db.query(JobExecution).filter(
            JobExecution.job_id == job_id,
            JobExecution.execution_number == execution_number
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Get results
        results = job_service.get_execution_results(execution.id, target_id)
        
        return [
            ExecutionResultResponse(
                id=result.id,
                execution_id=result.execution_id,
                target_id=result.target_id,
                target_name=result.target_name,
                action_name=result.action_name,
                action_type=result.action_type,
                status=result.status,
                output_text=result.output_text,
                error_text=result.error_text,
                exit_code=result.exit_code,
                execution_time_ms=result.execution_time_ms,
                started_at=result.started_at,
                completed_at=result.completed_at
            )
            for result in results
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/targets/{target_id}/results", response_model=List[ExecutionResultResponse])
async def get_target_results(
    target_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all results for a specific target - SIMPLIFIED"""
    try:
        job_service = JobService(db)
        
        results = job_service.get_target_results(target_id, limit)
        
        return [
            ExecutionResultResponse(
                id=result.id,
                execution_id=result.execution_id,
                target_id=result.target_id,
                target_name=result.target_name,
                action_name=result.action_name,
                action_type=result.action_type,
                status=result.status,
                output_text=result.output_text,
                error_text=result.error_text,
                exit_code=result.exit_code,
                execution_time_ms=result.execution_time_ms,
                started_at=result.started_at,
                completed_at=result.completed_at
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Failed to get target results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a job - SIMPLIFIED"""
    try:
        job_service = JobService(db)
        
        success = job_service.delete_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
            
        return {"message": "Job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a job - SIMPLIFIED"""
    try:
        job_service = JobService(db)
        
        # Get existing job
        existing_job = job_service.get_job(job_id)
        if not existing_job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update job fields
        update_data = {}
        if job_update.name is not None:
            update_data['name'] = job_update.name
        if job_update.description is not None:
            update_data['description'] = job_update.description
        if job_update.scheduled_at is not None:
            update_data['scheduled_at'] = job_update.scheduled_at
            # If a scheduled time is set, change status to scheduled
            update_data['status'] = JobStatus.SCHEDULED
            
        # Update basic fields
        if update_data:
            for field, value in update_data.items():
                setattr(existing_job, field, value)
            db.commit()
            db.refresh(existing_job)
        
        # Update actions if provided
        if job_update.actions is not None:
            # Delete existing actions
            for action in existing_job.actions:
                db.delete(action)
            
            # Create new actions
            for i, action_data in enumerate(job_update.actions):
                from app.models.job_models import JobAction
                action = JobAction(
                    job_id=job_id,
                    action_order=i + 1,
                    action_name=action_data.action_name,
                    action_type=action_data.action_type,
                    action_parameters=action_data.action_parameters
                )
                db.add(action)
        
        # Update targets if provided
        if job_update.target_ids is not None:
            # Delete existing targets
            for target in existing_job.targets:
                db.delete(target)
            
            # Create new targets
            for target_id in job_update.target_ids:
                from app.models.job_models import JobTarget
                job_target = JobTarget(
                    job_id=job_id,
                    target_id=target_id
                )
                db.add(job_target)
        
        db.commit()
        db.refresh(existing_job)
        
        # Get the most recent execution for this job
        last_execution = None
        if existing_job.executions:
            sorted_executions = sorted(existing_job.executions, key=lambda e: e.started_at or e.created_at, reverse=True)
            if sorted_executions:
                latest_exec = sorted_executions[0]
                last_execution = {
                    "id": latest_exec.id,
                    "execution_number": latest_exec.execution_number,
                    "status": latest_exec.status.value if hasattr(latest_exec.status, 'value') else str(latest_exec.status),
                    "started_at": latest_exec.started_at,
                    "completed_at": latest_exec.completed_at,
                    "total_targets": latest_exec.total_targets,
                    "successful_targets": latest_exec.successful_targets,
                    "failed_targets": latest_exec.failed_targets
                }
        
        # Get updated actions
        actions = [
            ActionResponse(
                id=action.id,
                action_order=action.action_order,
                action_name=action.action_name,
                action_type=action.action_type,
                action_parameters=action.action_parameters
            )
            for action in existing_job.actions
        ]
        
        # Get updated targets
        targets = [
            TargetResponse(
                id=target.target.id,
                name=target.target.name
            )
            for target in existing_job.targets
        ]
        
        return JobResponse(
            id=existing_job.id,
            name=existing_job.name,
            description=existing_job.description,
            status=existing_job.status,
            created_at=existing_job.created_at,
            scheduled_at=existing_job.scheduled_at,
            started_at=existing_job.started_at,
            completed_at=existing_job.completed_at,
            last_execution=last_execution,
            actions=actions,
            targets=targets
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/targets")
async def get_job_targets(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get job targets - for editing purposes"""
    try:
        
        # Get job with targets
        from app.models.job_models import Job
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Extract target IDs from job targets
        target_ids = [jt.target_id for jt in job.targets]
        
        return {"target_ids": target_ids}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job targets {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))