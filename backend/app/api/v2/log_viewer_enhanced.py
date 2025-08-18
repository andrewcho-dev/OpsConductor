"""
Log Viewer API v2 Enhanced - Job Execution Logs and Results
Provides comprehensive job execution monitoring and log analysis

FEATURES:
- ✅ Hierarchical job execution data (Job → Execution → Branch → Action)
- ✅ Advanced search and filtering capabilities
- ✅ Performance statistics and analytics
- ✅ Real-time execution monitoring
- ✅ Comprehensive action result details
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func, text
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.core.security import verify_token
from app.core.logging import get_structured_logger, RequestLogger
from app.models.job_models import (
    Job, JobExecution, JobExecutionBranch, JobActionResult, 
    JobExecutionLog, ExecutionStatus, LogLevel, LogPhase
)
from app.models.universal_target_models import UniversalTarget

# Configure structured logger
logger = get_structured_logger(__name__)

# Security scheme
security = HTTPBearer()

# Router
router = APIRouter(prefix="/api/v2/log-viewer", tags=["Log Viewer"])

# PYDANTIC MODELS

class ActionResultResponse(BaseModel):
    """Action result response model"""
    id: int
    action_serial: str
    action_name: str
    action_type: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time_ms: Optional[int]
    result_output: Optional[str]
    result_error: Optional[str]
    exit_code: Optional[int]
    command_executed: Optional[str]
    
    # Context information
    job_serial: str
    job_name: str
    execution_serial: str
    branch_serial: str
    target_serial: str
    target_name: str
    target_type: str

    class Config:
        from_attributes = True


class LogViewerSearchResponse(BaseModel):
    """Log viewer search response"""
    results: List[ActionResultResponse]
    total_count: int
    page: int
    limit: int
    has_more: bool

    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "total_count": 150,
                "page": 1,
                "limit": 100,
                "has_more": True
            }
        }


class LogViewerStatsResponse(BaseModel):
    """Log viewer statistics response"""
    stats: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "stats": {
                    "total_jobs": 25,
                    "total_executions": 45,
                    "total_actions": 180,
                    "completed_actions": 165,
                    "failed_actions": 12,
                    "running_actions": 3,
                    "success_rate": 91.7,
                    "avg_execution_time": 2.5,
                    "last_24h_executions": 15
                }
            }
        }


# HELPER FUNCTIONS

def get_current_user(credentials = Depends(security), 
                    db: Session = Depends(get_db)):
    """Get current authenticated user with enhanced error handling."""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            logger.warning("Invalid token in log viewer request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Invalid or expired token",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        user_id = payload.get("user_id")
        from app.services.user_service import UserService
        user = UserService.get_user_by_id(db, user_id)
        
        if not user:
            logger.warning(f"User not found for token: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "user_not_found",
                    "message": "User not found",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error in log viewer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "authentication_failed",
                "message": "Authentication failed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


def require_log_viewer_permissions(current_user = Depends(get_current_user)):
    """Require log viewer permissions"""
    if current_user.role not in ["administrator", "operator", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_permissions",
                "message": "Insufficient permissions to view logs",
                "required_roles": ["administrator", "operator", "viewer"],
                "user_role": current_user.role,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    return current_user


def build_search_query(db: Session, pattern: Optional[str] = None, status_filter: str = "all"):
    """Build search query for action results"""
    
    # Base query with all necessary joins
    query = db.query(JobActionResult).join(
        JobExecutionBranch, JobActionResult.branch_id == JobExecutionBranch.id
    ).join(
        JobExecution, JobExecutionBranch.job_execution_id == JobExecution.id
    ).join(
        Job, JobExecution.job_id == Job.id
    ).join(
        UniversalTarget, JobExecutionBranch.target_id == UniversalTarget.id
    )
    
    # Apply status filter
    if status_filter != "all":
        query = query.filter(JobActionResult.status == status_filter)
    
    # Apply pattern search
    if pattern and pattern.strip():
        pattern = pattern.strip()
        
        # Check if it's a serial pattern search
        if any(char in pattern for char in ['J', '.', '*']):
            # Serial pattern search
            if '*' in pattern:
                # Wildcard search
                like_pattern = pattern.replace('*', '%')
                query = query.filter(
                    or_(
                        JobActionResult.action_serial.like(like_pattern),
                        Job.job_serial.like(like_pattern),
                        JobExecution.execution_serial.like(like_pattern),
                        JobExecutionBranch.branch_serial.like(like_pattern)
                    )
                )
            else:
                # Exact or prefix search
                query = query.filter(
                    or_(
                        JobActionResult.action_serial.like(f"{pattern}%"),
                        Job.job_serial.like(f"{pattern}%"),
                        JobExecution.execution_serial.like(f"{pattern}%"),
                        JobExecutionBranch.branch_serial.like(f"{pattern}%"),
                        UniversalTarget.target_serial.like(f"{pattern}%")
                    )
                )
        else:
            # Text search in names and content
            query = query.filter(
                or_(
                    Job.name.ilike(f"%{pattern}%"),
                    JobActionResult.action_name.ilike(f"%{pattern}%"),
                    UniversalTarget.name.ilike(f"%{pattern}%"),
                    JobActionResult.result_output.ilike(f"%{pattern}%"),
                    JobActionResult.command_executed.ilike(f"%{pattern}%")
                )
            )
    
    return query


# API ENDPOINTS

@router.get(
    "/search",
    response_model=LogViewerSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Job Execution Logs",
    description="""
    Search and retrieve job execution logs with advanced filtering.
    
    **Features:**
    - ✅ Hierarchical job execution data
    - ✅ Serial pattern matching (J20250000001, *.0001, etc.)
    - ✅ Text search in job names, actions, outputs
    - ✅ Status filtering
    - ✅ Pagination support
    
    **Search Patterns:**
    - `J20250000001` - Specific job
    - `J20250000001.0001` - Specific execution
    - `J20250000001.0001.0001` - Specific branch
    - `J20250000001.0001.0001.0001` - Specific action
    - `J2025*` - All 2025 jobs
    - `*.0001` - All first executions
    - `setup` - Text search in names/content
    """,
    responses={
        200: {"description": "Search results retrieved successfully"}
    }
)
async def search_execution_logs(
    pattern: Optional[str] = Query(None, description="Search pattern (serial or text)"),
    status: str = Query("all", description="Status filter"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Results offset"),
    current_user = Depends(require_log_viewer_permissions),
    db: Session = Depends(get_db)
) -> LogViewerSearchResponse:
    """Search job execution logs with advanced filtering"""
    
    request_logger = RequestLogger(logger, "search_execution_logs")
    request_logger.log_request_start("GET", "/api/v2/log-viewer/search", current_user.username)
    
    try:
        # Build search query
        query = build_search_query(db, pattern, status)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        results = query.order_by(
            desc(JobActionResult.started_at),
            desc(JobActionResult.id)
        ).offset(offset).limit(limit).all()
        
        # Transform results to response format
        action_results = []
        for result in results:
            # Get related data
            branch = result.branch
            execution = branch.execution
            job = execution.job
            target = branch.target
            
            action_result = ActionResultResponse(
                id=result.id,
                action_serial=result.action_serial,
                action_name=result.action_name,
                action_type=result.action_type,
                status=result.status,
                started_at=result.started_at,
                completed_at=result.completed_at,
                execution_time_ms=result.execution_time_ms,
                result_output=result.result_output,
                result_error=result.result_error,
                exit_code=result.exit_code,
                command_executed=result.command_executed,
                
                # Context information
                job_serial=job.job_serial,
                job_name=job.name,
                execution_serial=execution.execution_serial,
                branch_serial=branch.branch_serial,
                target_serial=target.target_serial,
                target_name=target.name,
                target_type=target.target_type
            )
            action_results.append(action_result)
        
        response = LogViewerSearchResponse(
            results=action_results,
            total_count=total_count,
            page=(offset // limit) + 1,
            limit=limit,
            has_more=(offset + limit) < total_count
        )
        
        request_logger.log_request_end(200, 0.0)
        
        logger.info(
            "Log viewer search completed",
            extra={
                "pattern": pattern,
                "status_filter": status,
                "results_count": len(action_results),
                "total_count": total_count,
                "user": current_user.username
            }
        )
        
        return response
        
    except Exception as e:
        request_logger.log_request_end(500, 0.0)
        logger.error(f"Log viewer search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=LogViewerStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Log Viewer Statistics",
    description="""
    Get comprehensive statistics for job execution logs.
    
    **Features:**
    - ✅ Overall execution statistics
    - ✅ Success/failure rates
    - ✅ Performance metrics
    - ✅ Recent activity summary
    """,
    responses={
        200: {"description": "Statistics retrieved successfully"}
    }
)
async def get_log_viewer_stats(
    pattern: Optional[str] = Query(None, description="Filter stats by search pattern"),
    current_user = Depends(require_log_viewer_permissions),
    db: Session = Depends(get_db)
) -> LogViewerStatsResponse:
    """Get comprehensive log viewer statistics"""
    
    request_logger = RequestLogger(logger, "get_log_viewer_stats")
    request_logger.log_request_start("GET", "/api/v2/log-viewer/stats", current_user.username)
    
    try:
        # Build base query for stats
        base_query = build_search_query(db, pattern, "all")
        
        # Get basic counts
        total_actions = base_query.count()
        completed_actions = base_query.filter(JobActionResult.status == 'completed').count()
        failed_actions = base_query.filter(JobActionResult.status == 'failed').count()
        running_actions = base_query.filter(JobActionResult.status == 'running').count()
        
        # Get unique job and execution counts
        job_count = db.query(Job.id).join(
            JobExecution, Job.id == JobExecution.job_id
        ).join(
            JobExecutionBranch, JobExecution.id == JobExecutionBranch.job_execution_id
        ).join(
            JobActionResult, JobExecutionBranch.id == JobActionResult.branch_id
        ).distinct().count()
        
        execution_count = db.query(JobExecution.id).join(
            JobExecutionBranch, JobExecution.id == JobExecutionBranch.job_execution_id
        ).join(
            JobActionResult, JobExecutionBranch.id == JobActionResult.branch_id
        ).distinct().count()
        
        # Calculate success rate
        success_rate = (completed_actions / total_actions * 100) if total_actions > 0 else 0
        
        # Get average execution time
        avg_time_result = db.query(
            func.avg(JobActionResult.execution_time_ms)
        ).filter(
            JobActionResult.execution_time_ms.isnot(None)
        ).scalar()
        avg_execution_time = (avg_time_result / 1000) if avg_time_result else 0  # Convert to seconds
        
        # Get last 24h executions
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        last_24h_executions = base_query.filter(
            JobActionResult.started_at >= yesterday
        ).count()
        
        stats = {
            "total_jobs": job_count,
            "total_executions": execution_count,
            "total_actions": total_actions,
            "completed_actions": completed_actions,
            "failed_actions": failed_actions,
            "running_actions": running_actions,
            "success_rate": round(success_rate, 1),
            "avg_execution_time": round(avg_execution_time, 2),
            "last_24h_executions": last_24h_executions
        }
        
        response = LogViewerStatsResponse(stats=stats)
        
        request_logger.log_request_end(200, 0.0)
        
        logger.info(
            "Log viewer stats retrieved",
            extra={
                "pattern": pattern,
                "stats": stats,
                "user": current_user.username
            }
        )
        
        return response
        
    except Exception as e:
        request_logger.log_request_end(500, 0.0)
        logger.error(f"Log viewer stats failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats retrieval failed: {str(e)}"
        )


@router.get(
    "/action/{action_id}",
    response_model=ActionResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Action Details",
    description="""
    Get detailed information for a specific action result.
    
    **Features:**
    - ✅ Complete action execution details
    - ✅ Command output and error information
    - ✅ Execution context and metadata
    """,
    responses={
        200: {"description": "Action details retrieved successfully"},
        404: {"description": "Action not found"}
    }
)
async def get_action_details(
    action_id: int,
    current_user = Depends(require_log_viewer_permissions),
    db: Session = Depends(get_db)
) -> ActionResultResponse:
    """Get detailed information for a specific action"""
    
    request_logger = RequestLogger(logger, f"get_action_details_{action_id}")
    request_logger.log_request_start("GET", f"/api/v2/log-viewer/action/{action_id}", current_user.username)
    
    try:
        # Query action with all related data
        action = db.query(JobActionResult).options(
            joinedload(JobActionResult.branch).joinedload(JobExecutionBranch.execution).joinedload(JobExecution.job),
            joinedload(JobActionResult.branch).joinedload(JobExecutionBranch.target)
        ).filter(JobActionResult.id == action_id).first()
        
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action with ID {action_id} not found"
            )
        
        # Get related data
        branch = action.branch
        execution = branch.execution
        job = execution.job
        target = branch.target
        
        response = ActionResultResponse(
            id=action.id,
            action_serial=action.action_serial,
            action_name=action.action_name,
            action_type=action.action_type,
            status=action.status,
            started_at=action.started_at,
            completed_at=action.completed_at,
            execution_time_ms=action.execution_time_ms,
            result_output=action.result_output,
            result_error=action.result_error,
            exit_code=action.exit_code,
            command_executed=action.command_executed,
            
            # Context information
            job_serial=job.job_serial,
            job_name=job.name,
            execution_serial=execution.execution_serial,
            branch_serial=branch.branch_serial,
            target_serial=target.serial,
            target_name=target.name,
            target_type=target.target_type
        )
        
        request_logger.log_request_end(200, 0.0)
        
        logger.info(
            "Action details retrieved",
            extra={
                "action_id": action_id,
                "action_serial": action.action_serial,
                "user": current_user.username
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        request_logger.log_request_end(500, 0.0)
        logger.error(f"Get action details failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve action details: {str(e)}"
        )