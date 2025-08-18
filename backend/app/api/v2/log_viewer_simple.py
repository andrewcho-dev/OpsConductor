"""
Simple Log Viewer API v2 - Working Version
Provides basic job execution log viewing without complex queries
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.core.security import verify_token
from app.core.logging import get_structured_logger
from app.models.job_models import (
    Job, JobExecution, JobExecutionResult, ExecutionStatus
)

# Configure structured logger
logger = get_structured_logger(__name__)

# Security scheme
security = HTTPBearer()

# Router
router = APIRouter(prefix="/api/v2/log-viewer", tags=["Log Viewer Simple"])

# PYDANTIC MODELS

class ActionResultResponse(BaseModel):
    """Action result response model - matching original format"""
    id: int
    action_serial: str = ""
    action_name: str
    action_type: str = "command"
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time_ms: Optional[int] = None
    result_output: Optional[str] = None
    result_error: Optional[str] = None
    exit_code: Optional[int] = None
    command_executed: Optional[str] = None
    
    # Context information
    job_serial: str = ""
    job_name: str
    execution_serial: str = ""
    branch_serial: str = ""
    target_serial: str = ""
    target_name: str
    target_type: str = "device"

class LogViewerSearchResponse(BaseModel):
    """Log viewer search response - matching original format"""
    results: List[ActionResultResponse]
    total_count: int
    page: int
    limit: int
    has_more: bool

class LogStatsResponse(BaseModel):
    """Log statistics response"""
    success: bool
    stats: Dict[str, Any]

# DEPENDENCY FUNCTIONS

def get_current_user(credentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return payload
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# ENDPOINTS

@router.get(
    "/search",
    response_model=LogViewerSearchResponse,
    summary="Search Execution Logs",
    description="Search and filter job execution logs with pagination"
)
async def search_execution_logs(
    limit: int = Query(50, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    status: str = Query("all", description="Filter by status (all, completed, failed, running)"),
    pattern: Optional[str] = Query(None, description="Search pattern"),
    execution_id: Optional[int] = Query(None, description="Filter by execution ID"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    execution_number: Optional[int] = Query(None, description="Filter by execution number"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search execution logs with basic filtering"""
    try:
        logger.info(f"Searching logs: limit={limit}, offset={offset}, status={status}, pattern={pattern}, execution_id={execution_id}, job_id={job_id}, execution_number={execution_number}")
        
        # Build base query
        query = db.query(JobExecutionResult).join(
            JobExecution, JobExecutionResult.execution_id == JobExecution.id
        ).join(
            Job, JobExecution.job_id == Job.id
        )
        
        # Apply execution ID filter
        if execution_id:
            query = query.filter(JobExecutionResult.execution_id == execution_id)
        
        # Apply job ID filter
        if job_id:
            query = query.filter(Job.id == job_id)
        
        # Apply execution number filter (combined with job_id)
        if execution_number is not None and job_id:
            query = query.filter(JobExecution.execution_number == execution_number)
        
        # Apply status filter
        if status != "all":
            query = query.filter(JobExecutionResult.status == status)
        
        # Apply pattern search (only if no specific filters are used)
        if pattern and not (job_id and execution_number):
            query = query.filter(
                JobExecutionResult.action_name.ilike(f"%{pattern}%")
            )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        results = query.order_by(
            desc(JobExecutionResult.started_at),
            desc(JobExecutionResult.id)
        ).offset(offset).limit(limit).all()
        
        # Convert to response format matching original
        action_results = []
        for result in results:
            action_results.append(ActionResultResponse(
                id=result.id,
                action_serial=f"action_{result.id}",
                action_name=result.action_name,
                action_type="command",
                status=result.status.value if hasattr(result.status, 'value') else str(result.status),
                started_at=result.started_at.isoformat() if result.started_at else None,
                completed_at=result.completed_at.isoformat() if result.completed_at else None,
                execution_time_ms=result.execution_time_ms,
                result_output=result.output_text,
                result_error=result.error_text,
                exit_code=result.exit_code,
                command_executed=result.command_executed,
                job_serial=f"job_{result.execution.job.id}",
                job_name=result.execution.job.name,
                execution_serial=f"exec_{result.execution_id}",
                branch_serial=f"branch_{result.id}",
                target_serial=f"target_{result.target_id}",
                target_name=result.target_name,
                target_type="device"
            ))
        
        return LogViewerSearchResponse(
            results=action_results,
            total_count=total_count,
            page=offset // limit + 1,
            limit=limit,
            has_more=(offset + limit) < total_count
        )
        
    except Exception as e:
        logger.error(f"Log search failed: {str(e)}")
        return LogViewerSearchResponse(
            results=[],
            total_count=0,
            page=1,
            limit=limit,
            has_more=False
        )

@router.get(
    "/stats",
    response_model=LogStatsResponse,
    summary="Get Log Statistics",
    description="Get basic statistics about job execution logs"
)
async def get_log_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get basic log statistics"""
    try:
        logger.info("Getting log statistics")
        
        # Get basic counts
        total_executions = db.query(JobExecutionResult).count()
        completed_executions = db.query(JobExecutionResult).filter(
            JobExecutionResult.status == ExecutionStatus.COMPLETED
        ).count()
        failed_executions = db.query(JobExecutionResult).filter(
            JobExecutionResult.status == ExecutionStatus.FAILED
        ).count()
        running_executions = db.query(JobExecutionResult).filter(
            JobExecutionResult.status == ExecutionStatus.RUNNING
        ).count()
        
        stats = {
            "total_executions": total_executions,
            "completed_executions": completed_executions,
            "failed_executions": failed_executions,
            "running_executions": running_executions,
            "success_rate": (completed_executions / total_executions * 100) if total_executions > 0 else 0
        }
        
        return LogStatsResponse(
            success=True,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Log stats failed: {str(e)}")
        return LogStatsResponse(
            success=False,
            stats={"error": str(e)}
        )