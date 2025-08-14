from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.database import get_db
from app.core.security import verify_token
from app.models.user_models import User
from app.services.job_service import JobService
from app.schemas.job_schemas import (
    JobCreate, JobResponse, JobListResponse, JobSchedule, JobExecuteRequest,
    JobExecutionResponse, JobWithExecutionsResponse, JobActionResultResponse
)
from app.services.user_service import UserService
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
from app.tasks.job_tasks import execute_job_task
import logging
from app.utils.target_utils import getTargetIpAddress

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def build_execution_response(execution):
    """Convert JobExecution ORM object to Pydantic model with target metadata."""
    # Convert execution to dict and handle UUID conversion
    execution_data = {
        "id": execution.id,
        "execution_uuid": str(execution.execution_uuid) if execution.execution_uuid else None,
        "execution_serial": execution.execution_serial,
        "execution_number": execution.execution_number,
        "status": execution.status,
        "scheduled_at": execution.scheduled_at,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "created_at": execution.created_at,
        "branches": []
    }
    
    # Process branches
    for branch in execution.branches:
        branch_data = {
            "id": branch.id,
            "branch_uuid": str(branch.branch_uuid) if branch.branch_uuid else None,
            "branch_serial": branch.branch_serial,
            "branch_id": branch.branch_id,
            "target_id": branch.target_id,
            "target_serial_ref": branch.target_serial_ref,
            "status": branch.status,
            "scheduled_at": branch.scheduled_at,
            "started_at": branch.started_at,
            "completed_at": branch.completed_at,
            "result_output": branch.result_output,
            "result_error": branch.result_error,
            "exit_code": branch.exit_code,
            "created_at": branch.created_at
        }
        
        # Add target metadata
        target = getattr(branch, 'target', None)
        if target:
            branch_data["target_name"] = target.name
            branch_data["os_type"] = target.os_type
            try:
                branch_data["ip_address"] = getTargetIpAddress(target)
            except Exception:
                branch_data["ip_address"] = None
        else:
            branch_data["target_name"] = None
            branch_data["os_type"] = None
            branch_data["ip_address"] = None
            
        execution_data["branches"].append(branch_data)
    
    return JobExecutionResponse(**execution_data)
security = HTTPBearer()



def get_current_user(
    credentials: HTTPBearer = Depends(security), 
    db: Session = Depends(get_db)
):
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("user_id")
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new job"""
    try:
        print(f"DEBUG: Received job_data: {job_data}")
        print(f"DEBUG: job_data.job_type: {job_data.job_type}")
        print(f"DEBUG: job_data.job_type type: {type(job_data.job_type)}")
        job_service = JobService(db)
        job = job_service.create_job(job_data, current_user.id)
        
        # Log job creation audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.JOB_CREATED,
            user_id=current_user.id,
            resource_type="job",
            resource_id=str(job.id),
            action="create_job",
            details={
                "job_name": job.name,
                "job_type": job.job_type,
                "description": job.description,
                "created_by": current_user.username
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Return job with actions
        return JobResponse.model_validate(job)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/", response_model=JobListResponse)
async def get_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of jobs"""
    try:
        job_service = JobService(db)
        
        # Convert status string to enum if provided
        job_status = None
        if status_filter:
            from app.models.job_models import JobStatus
            try:
                job_status = JobStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}"
                )
        
        # Use optimized method to get jobs with last execution in single query
        # Role-based filtering: admins see all jobs, regular users see only their own
        created_by_filter = None if current_user.role in ['admin', 'administrator'] else current_user.id
        
        jobs_with_executions = job_service.get_jobs_with_last_execution(
            skip=skip,
            limit=limit,
            status=job_status,
            created_by=created_by_filter
        )
        
        # Convert to response format
        job_list = []
        for job, last_execution in jobs_with_executions:
            last_execution_data = None
            if last_execution:
                last_execution_data = build_execution_response(last_execution)
            
            job_list.append({
                "id": job.id,
                "job_uuid": str(job.job_uuid) if job.job_uuid else None,
                "job_serial": job.job_serial,
                "name": job.name,
                "job_type": job.job_type,
                "status": job.status,
                "created_at": job.created_at,
                "scheduled_at": job.scheduled_at,  # Return UTC - frontend will handle display
                "last_execution": last_execution_data
            })
        
        return JobListResponse(
            jobs=job_list,
            total=len(job_list),
            page=skip // limit + 1,
            per_page=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get jobs: {str(e)}"
        )


@router.get("/{job_id}", response_model=JobWithExecutionsResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific job with its executions"""
    try:
        job_service = JobService(db)
        job = job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Check if user has access to this job
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get executions
        executions = job_service.get_job_executions(job_id)
        
        return JobWithExecutionsResponse(
            job=JobResponse.model_validate(job),  # Return UTC - frontend will handle display
            executions=[build_execution_response(execution) for execution in executions]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job: {str(e)}"
        )


@router.post("/{job_id}/schedule", response_model=JobResponse)
async def schedule_job(
    job_id: int,
    schedule_data: JobSchedule,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schedule a job for execution"""
    try:
        job_service = JobService(db)
        job = job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Check if user has access to this job
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        job = job_service.schedule_job(job_id, schedule_data)
        return JobResponse.model_validate(job)  # Return UTC - frontend will handle display
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to schedule job: {str(e)}"
        )


@router.post("/{job_id}/execute", response_model=JobExecutionResponse)
async def execute_job(
    job_id: int,
    execute_data: JobExecuteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute a job immediately"""
    try:
        job_service = JobService(db)
        job = job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Check if user has access to this job
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Create execution
        execution = job_service.execute_job(job_id, execute_data)
        
        # DEBUG: log received execute_data and selected target_ids
        logger.info(f"ExecuteJob API called: job_id={job_id}, execute_data={execute_data}")
        # Get targets for execution
        target_ids = execute_data.target_ids if execute_data.target_ids else []
        if not target_ids:
            # Get targets associated with this job
            target_ids = job_service.get_job_target_ids(job_id)
        
        # Queue Celery task for job execution
        task = execute_job_task.delay(execution.id, target_ids)
        logger.info(f"Celery task queued: execution_id={execution.id}, task_id={task.id}, targets={target_ids}")
        
        # Log job execution audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.JOB_EXECUTED,
            user_id=current_user.id,
            resource_type="job",
            resource_id=str(job_id),
            action="execute_job",
            details={
                "job_name": job.name,
                "execution_id": execution.id,
                "execution_uuid": str(execution.execution_uuid) if execution.execution_uuid else None,
                "target_count": len(target_ids),
                "target_ids": target_ids,
                "executed_by": current_user.username,
                "task_id": task.id
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return build_execution_response(execution)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to execute job: {str(e)}"
        )


@router.get("/{job_id}/executions/{execution_id}", response_model=JobExecutionResponse)
async def get_job_execution(
    job_id: int,
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific job execution"""
    try:
        job_service = JobService(db)
        
        # Verify job exists and user has access
        job = job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get execution
        execution = job_service.get_job_execution(execution_id)
        if not execution or execution.job_id != job_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found"
            )
        
        return build_execution_response(execution)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution: {str(e)}"
        )


@router.get("/{job_id}/executions", response_model=List[JobExecutionResponse])
async def get_job_executions(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all executions for a job"""
    try:
        job_service = JobService(db)
        
        # Verify job exists and user has access
        job = job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get executions
        executions = job_service.get_job_executions(job_id)
        return [build_execution_response(execution) for execution in executions]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get executions: {str(e)}"
        )


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing job"""
    try:
        job_service = JobService(db)
        
        # Verify job exists and user has access
        job = job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update job
        updated_job = job_service.update_job(job_id, job_data)
        
        # Log job update audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.JOB_UPDATED,
            user_id=current_user.id,
            resource_type="job",
            resource_id=str(job_id),
            action="update_job",
            details={
                "job_name": updated_job.name,
                "job_type": updated_job.job_type,
                "updated_fields": {
                    "name": job_data.name,
                    "description": job_data.description,
                    "job_type": job_data.job_type,
                    "command": job_data.command
                },
                "updated_by": current_user.username
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return JobResponse.model_validate(updated_job)
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Exception in update_job: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update job: {str(e)}"
        )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a job"""
    try:
        job_service = JobService(db)
        
        # Verify job exists and user has access
        job = job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Delete job
        success = job_service.delete_job(job_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete job {job_id}"
            )
        
        # Log job deletion audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.JOB_DELETED,
            user_id=current_user.id,
            resource_type="job",
            resource_id=str(job_id),
            action="delete_job",
            details={
                "job_name": job.name,
                "job_type": job.job_type,
                "command": job.command,
                "deleted_by": current_user.username
            },
            severity=AuditSeverity.HIGH,  # Job deletion is high severity
            ip_address=client_ip,
            user_agent=user_agent
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )


@router.get("/{job_id}/targets", response_model=List[int])
async def get_job_targets(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get target IDs associated with a job"""
    try:
        job_service = JobService(db)
        
        # Verify job exists and user has access
        job = job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get target IDs for this job
        target_ids = job_service.get_job_target_ids(job_id)
        return target_ids
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job targets: {str(e)}"
        )


# UUID-based endpoints for permanent references
@router.get("/uuid/{job_uuid}", response_model=JobResponse)
async def get_job_by_uuid(
    job_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get job by UUID (permanent identifier)"""
    try:
        job_service = JobService(db)
        job = job_service.get_job_by_uuid(job_uuid)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with UUID {job_uuid} not found"
            )
        
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return JobResponse.model_validate(job)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job by UUID: {str(e)}"
        )


@router.get("/serial/{job_serial}", response_model=JobResponse)
async def get_job_by_serial(
    job_serial: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get job by serial number (human-readable permanent identifier)"""
    try:
        job_service = JobService(db)
        job = job_service.get_job_by_serial(job_serial)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with serial {job_serial} not found"
            )
        
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return JobResponse.model_validate(job)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job by serial: {str(e)}"
        )


@router.get("/{job_id}/executions/{execution_id}/action-results", response_model=List[JobActionResultResponse])
async def get_execution_action_results(
    job_id: int,
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get individual action results for a job execution"""
    try:
        job_service = JobService(db)
        
        # Verify job exists and user has access
        job = job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Verify execution belongs to this job
        execution = job_service.get_job_execution(execution_id)
        if not execution or execution.job_id != job_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found for job {job_id}"
            )
        
        # Get action results
        action_results = job_service.get_execution_action_results(execution_id)
        
        return [JobActionResultResponse.model_validate(result) for result in action_results]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get action results: {str(e)}"
        )


@router.get("/executions/{execution_serial}/branches")
async def get_execution_branches_by_serial(
    execution_serial: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all target result branches for an execution using the serialization system"""
    try:
        job_service = JobService(db)
        
        # Get execution by serial
        execution = job_service.get_execution_by_serial(execution_serial)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution with serial {execution_serial} not found"
            )
        
        # Check access to the job
        job = job_service.get_job(execution.job_id)
        if job.created_by != current_user.id and current_user.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get branches with target info and action results
        branches_data = []
        for branch in execution.branches:
            # Get action results for this branch
            action_results = []
            for action_result in branch.action_results:
                action_data = {
                    "id": action_result.id,
                    "action_name": action_result.action_name,
                    "action_type": action_result.action_type,
                    "status": action_result.status,
                    "started_at": action_result.started_at,
                    "completed_at": action_result.completed_at,
                    "execution_time_ms": action_result.execution_time_ms,
                    "result_output": action_result.result_output,
                    "result_error": action_result.result_error,
                    "exit_code": action_result.exit_code,
                    "command_executed": action_result.command_executed,
                    "action_order": action_result.action_order
                }
                action_results.append(action_data)
            
            branch_data = {
                "id": branch.id,
                "branch_uuid": str(branch.branch_uuid) if branch.branch_uuid else None,
                "branch_serial": branch.branch_serial,
                "branch_id": branch.branch_id,
                "target_id": branch.target_id,
                "target_serial_ref": branch.target_serial_ref,
                "status": branch.status,
                "started_at": branch.started_at,
                "completed_at": branch.completed_at,
                "result_output": branch.result_output,
                "result_error": branch.result_error,
                "exit_code": branch.exit_code,
                "action_results": action_results,
                "target": {
                    "id": branch.target.id,
                    "name": branch.target.name,
                    "ip_address": getTargetIpAddress(branch.target),
                    "target_serial": branch.target.target_serial
                } if branch.target else None
            }
            branches_data.append(branch_data)
        
        return {"branches": branches_data}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution branches: {str(e)}"
        )
