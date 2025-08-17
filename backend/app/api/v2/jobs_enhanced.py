"""
Jobs API v2 Enhanced - Phases 1 & 2
Complete transformation with service layer, caching, and comprehensive models

PHASE 1 & 2 IMPROVEMENTS:
- ✅ Comprehensive Pydantic models with validation
- ✅ Service layer integration with business logic separation
- ✅ Redis caching for improved performance
- ✅ Structured JSON logging with contextual information
- ✅ Enhanced error handling with detailed responses
- ✅ Advanced job management and execution tracking
- ✅ Job safety and validation mechanisms
- ✅ Real-time job analytics and monitoring
- ✅ Comprehensive job lifecycle management
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator

# Import service layer
from app.services.jobs_management_service import JobsManagementService, JobsManagementError
from app.database.database import get_db
from app.core.security import verify_token
from app.core.logging import get_structured_logger, RequestLogger

# Configure structured logger
logger = get_structured_logger(__name__)

# Security scheme
security = HTTPBearer()

# PHASE 1: COMPREHENSIVE PYDANTIC MODELS

class JobActionCreateV2(BaseModel):
    """V2 Job action creation model"""
    action_order: Optional[int] = None
    action_type: str = Field(default="COMMAND", description="Action type")
    action_name: str = Field(..., description="Action name", min_length=1, max_length=255)
    action_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Action parameters")
    action_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Action configuration")


class JobCreateRequest(BaseModel):
    """V2 Enhanced request model for job creation - Frontend Compatible"""
    name: str = Field(..., description="Job name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Job description", max_length=1000)
    actions: List[JobActionCreateV2] = Field(..., description="Job actions", min_items=1)
    target_ids: List[int] = Field(..., description="Target IDs", min_items=1)
    scheduled_at: Optional[str] = Field(None, description="Scheduled execution time (ISO format)")
    
    # Optional v2 enhancements
    priority: int = Field(default=5, description="Job priority (1-10)", ge=1, le=10)
    timeout: Optional[int] = Field(None, description="Job timeout in seconds", ge=1)
    retry_count: int = Field(default=0, description="Number of retries", ge=0, le=10)
    
    @validator('name')
    def validate_name(cls, v):
        """Validate job name"""
        if not v.strip():
            raise ValueError('Job name cannot be empty')
        return v.strip()
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        """Validate and convert scheduled_at to datetime"""
        if v is None:
            return None
        try:
            # Parse ISO format datetime string
            from datetime import datetime
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('scheduled_at must be in ISO format (e.g., 2025-08-17T03:06:00.000Z)')
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Simple Job",
                "description": "A simple job example",
                "actions": [
                    {
                        "action_name": "Execute Command",
                        "action_type": "COMMAND",
                        "action_parameters": {
                            "command": "echo 'Hello World'"
                        }
                    }
                ],
                "target_ids": [1, 2, 3],
                "scheduled_at": "2025-08-17T03:06:00.000Z",
                "priority": 5,
                "timeout": 3600,
                "retry_count": 0
            }
        }


class JobResponse(BaseModel):
    """Enhanced response model for job information"""
    id: int = Field(..., description="Job ID")
    job_uuid: Optional[str] = Field(None, description="Permanent job UUID")
    job_serial: Optional[str] = Field(None, description="Human-readable job serial (e.g., J20250000001)")
    name: str = Field(..., description="Job name")
    job_type: str = Field(..., description="Job type")
    description: Optional[str] = Field(None, description="Job description")
    status: str = Field(..., description="Job status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: int = Field(..., description="Creator user ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Job parameters")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Job actions")
    scheduled_at: Optional[datetime] = Field(None, description="Job scheduled execution time")
    priority: int = Field(..., description="Job priority")
    timeout: Optional[int] = Field(None, description="Job timeout")
    retry_count: int = Field(..., description="Retry count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Job metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "name": "Network Discovery Job",
                "job_type": "discovery",
                "description": "Discover devices on the network",
                "status": "active",
                "created_at": "2025-01-01T10:30:00Z",
                "updated_at": "2025-01-01T11:00:00Z",
                "created_by": 1,
                "parameters": {
                    "network_range": "192.168.1.0/24"
                },
                "scheduled_at": "2025-01-01T02:00:00Z",
                "priority": 7,
                "timeout": 3600,
                "retry_count": 3,
                "metadata": {
                    "enhanced": True,
                    "execution_count": 15,
                    "last_execution": "2025-01-01T02:00:00Z"
                }
            }
        }


class JobsListResponse(BaseModel):
    """Enhanced response model for jobs list"""
    jobs: List[JobResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of jobs per page")
    total_pages: int = Field(..., description="Total number of pages")
    filters: Dict[str, Any] = Field(..., description="Applied filters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "jobs": [
                    {
                        "id": 123,
                        "name": "Network Discovery Job",
                        "job_type": "discovery",
                        "status": "active",
                        "created_at": "2025-01-01T10:30:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 50,
                "total_pages": 1,
                "filters": {
                    "job_type": None,
                    "status": None,
                    "user_id": None
                },
                "metadata": {
                    "cache_hit": False,
                    "query_time": 1640995800.0,
                    "requested_by": "admin"
                }
            }
        }


class JobExecutionRequest(BaseModel):
    """Enhanced request model for job execution"""
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Execution parameters")
    priority: Optional[int] = Field(None, description="Execution priority override", ge=1, le=10)
    timeout: Optional[int] = Field(None, description="Execution timeout override", ge=1)
    notify_on_completion: bool = Field(default=False, description="Send notification on completion")
    execution_context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "parameters": {
                    "network_range": "192.168.1.0/24",
                    "scan_ports": [22, 80, 443, 8080]
                },
                "priority": 8,
                "timeout": 1800,
                "notify_on_completion": True,
                "execution_context": {
                    "triggered_by": "manual",
                    "reason": "network_change_detected"
                }
            }
        }


class JobExecutionResponse(BaseModel):
    """Enhanced response model for job execution"""
    job_id: int = Field(..., description="Job ID")
    job_name: str = Field(..., description="Job name")
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Execution status")
    started_at: datetime = Field(..., description="Execution start time")
    executed_by: str = Field(..., description="Username who executed the job")
    parameters: Dict[str, Any] = Field(..., description="Execution parameters")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": 123,
                "job_name": "Network Discovery Job",
                "task_id": "celery-task-abc123",
                "status": "pending",
                "started_at": "2025-01-01T10:30:00Z",
                "executed_by": "admin",
                "parameters": {
                    "network_range": "192.168.1.0/24"
                },
                "estimated_duration": 1800
            }
        }


class JobStatisticsResponse(BaseModel):
    """Enhanced response model for job statistics"""
    total_jobs: int = Field(..., description="Total number of jobs")
    jobs_by_type: Dict[str, int] = Field(..., description="Jobs grouped by type")
    jobs_by_status: Dict[str, int] = Field(..., description="Jobs grouped by status")
    jobs_by_user: Dict[str, int] = Field(..., description="Jobs grouped by creator")
    recent_executions: List[Dict[str, Any]] = Field(..., description="Recent job executions")
    analytics: Dict[str, Any] = Field(default_factory=dict, description="Advanced analytics")
    performance: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Statistics metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_jobs": 150,
                "jobs_by_type": {
                    "discovery": 45,
                    "monitoring": 30,
                    "backup": 25
                },
                "jobs_by_status": {
                    "active": 120,
                    "paused": 20,
                    "disabled": 10
                },
                "jobs_by_user": {
                    "admin": 80,
                    "operator": 50,
                    "user": 20
                },
                "recent_executions": [],
                "analytics": {
                    "jobs_per_day": 12.5,
                    "average_execution_time": 450.0,
                    "success_rate": 95.5
                },
                "performance": {
                    "total_executions": 1500,
                    "failed_executions": 75,
                    "pending_executions": 5
                },
                "metadata": {
                    "last_updated": "2025-01-01T10:30:00Z",
                    "cache_ttl": 300
                }
            }
        }


class JobScheduleRequest(BaseModel):
    """Enhanced request model for job scheduling"""
    schedule_type: str = Field(..., description="Schedule type (cron, interval, once)")
    expression: str = Field(..., description="Schedule expression")
    timezone: str = Field(default="UTC", description="Timezone for schedule")
    enabled: bool = Field(default=True, description="Whether schedule is enabled")
    start_date: Optional[datetime] = Field(None, description="Schedule start date")
    end_date: Optional[datetime] = Field(None, description="Schedule end date")
    
    @validator('schedule_type')
    def validate_schedule_type(cls, v):
        """Validate schedule type"""
        allowed_types = ['cron', 'interval', 'once']
        if v not in allowed_types:
            raise ValueError(f'Schedule type must be one of: {", ".join(allowed_types)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "schedule_type": "cron",
                "expression": "0 2 * * *",
                "timezone": "UTC",
                "enabled": True,
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-12-31T23:59:59Z"
            }
        }


class JobErrorResponse(BaseModel):
    """Enhanced error response model for job management errors"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    job_id: Optional[int] = Field(None, description="Related job ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "job_creation_error",
                "message": "Job creation failed due to invalid parameters",
                "details": {
                    "validation_errors": ["Job name is required"]
                },
                "timestamp": "2025-01-01T10:30:00Z",
                "job_id": 123
            }
        }


# PHASE 1 & 2: ENHANCED ROUTER WITH SERVICE LAYER INTEGRATION

router = APIRouter(
    prefix="/api/v2/jobs",
    tags=["Jobs Management Enhanced v2"],
    responses={
        401: {"model": JobErrorResponse, "description": "Authentication required"},
        403: {"model": JobErrorResponse, "description": "Insufficient permissions"},
        404: {"model": JobErrorResponse, "description": "Resource not found"},
        422: {"model": JobErrorResponse, "description": "Validation error"},
        500: {"model": JobErrorResponse, "description": "Internal server error"}
    }
)


# PHASE 2: ENHANCED DEPENDENCY FUNCTIONS

def get_current_user(credentials = Depends(security), 
                    db: Session = Depends(get_db)):
    """Get current authenticated user with enhanced error handling."""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            logger.warning("Invalid token in jobs management request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Invalid or expired token",
                    "timestamp": datetime.utcnow().isoformat()
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
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Internal error during authentication",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def require_job_permissions(current_user = Depends(get_current_user)):
    """Require job management permissions."""
    if current_user.role not in ["administrator", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_permissions",
                "message": "Insufficient permissions to manage jobs",
                "required_roles": ["administrator", "operator"],
                "user_role": current_user.role,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    return current_user


# PHASE 1 & 2: ENHANCED ENDPOINTS WITH SERVICE LAYER

@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Job",
    description="""
    Create a new job with comprehensive validation and tracking.
    
    **Phase 1 & 2 Features:**
    - ✅ Advanced job validation with type checking
    - ✅ Redis caching for job data
    - ✅ Comprehensive audit logging
    - ✅ Enhanced job metadata and tracking
    
    **Security:**
    - Role-based access control (administrator, operator)
    - Comprehensive audit trail
    - Input validation and sanitization
    """,
    responses={
        201: {"description": "Job created successfully", "model": JobResponse}
    }
)
async def create_job(
    job_data: JobCreateRequest,
    request: Request,
    current_user = Depends(require_job_permissions),
    db: Session = Depends(get_db)
) -> JobResponse:
    """Enhanced job creation with service layer and comprehensive validation"""
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_logger = RequestLogger(logger, f"create_job_{job_data.name}")
    request_logger.log_request_start("POST", "/api/v2/jobs/", current_user.username)
    
    try:
        # Initialize service layer
        jobs_mgmt_service = JobsManagementService(db)
        
        # Create job through service layer
        job_result = await jobs_mgmt_service.create_job(
            job_data=job_data.model_dump(),
            current_user_id=current_user.id,
            current_username=current_user.username,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        response = JobResponse(**job_result)
        
        request_logger.log_request_end(status.HTTP_201_CREATED, len(str(response)))
        
        logger.info(
            "Job creation successful via service layer",
            extra={
                "job_id": job_result["id"],
                "job_name": job_result["name"],
                "job_type": job_result["job_type"],
                "created_by": current_user.username
            }
        )
        
        return response
        
    except JobsManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Job creation failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "job_name": job_data.name,
                "created_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Job creation error via service layer",
            extra={
                "error": str(e),
                "job_name": job_data.name,
                "created_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while creating the job",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/",
    response_model=JobsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Jobs",
    description="""
    Get paginated list of jobs with advanced filtering and caching.
    
    **Phase 1 & 2 Features:**
    - ✅ Advanced pagination with comprehensive metadata
    - ✅ Multi-field filtering (job type, status, user)
    - ✅ Redis caching for improved performance
    - ✅ Enhanced job data with execution history
    
    **Performance:**
    - Redis caching with 5-minute TTL
    - Optimized database queries
    - Structured logging for monitoring
    """,
    responses={
        200: {"description": "Jobs retrieved successfully", "model": JobsListResponse}
    }
)
async def get_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Jobs per page"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    job_status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    sort_by: Optional[str] = Query("created_at", description="Sort by field (created_at, scheduled_at, name, status)"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc, desc)"),
    current_user = Depends(require_job_permissions),
    db: Session = Depends(get_db)
) -> JobsListResponse:
    """Enhanced jobs retrieval with service layer and advanced filtering"""
    
    request_logger = RequestLogger(logger, "get_jobs")
    request_logger.log_request_start("GET", "/api/v2/jobs/", current_user.username)
    
    try:
        # Initialize service layer
        jobs_mgmt_service = JobsManagementService(db)
        
        # Get jobs through service layer (with caching)
        jobs_result = await jobs_mgmt_service.get_jobs(
            page=page,
            limit=limit,
            user_id=user_id,
            job_type=job_type,
            status=job_status,
            sort_by=sort_by,
            sort_order=sort_order,
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        # Convert to response format
        job_responses = []
        for job_data in jobs_result["jobs"]:
            job_responses.append(JobResponse(**job_data))
        
        response = JobsListResponse(
            jobs=job_responses,
            total=jobs_result["total"],
            page=jobs_result["page"],
            limit=jobs_result["limit"],
            total_pages=jobs_result["total_pages"],
            filters=jobs_result["filters"],
            metadata=jobs_result["metadata"]
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Jobs retrieval successful via service layer",
            extra={
                "total_jobs": jobs_result["total"],
                "returned_jobs": len(job_responses),
                "filters_applied": bool(job_type or job_status or user_id),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except JobsManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Jobs retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Jobs retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving jobs",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Job by ID",
    description="""
    Get specific job by ID with comprehensive information.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching for job data
    - ✅ Enhanced job information with execution history
    - ✅ Comprehensive error handling
    """,
    responses={
        200: {"description": "Job retrieved successfully", "model": JobResponse}
    }
)
async def get_job_by_id(
    job_id: int,
    current_user = Depends(require_job_permissions),
    db: Session = Depends(get_db)
) -> JobResponse:
    """Enhanced job retrieval by ID with service layer and caching"""
    
    request_logger = RequestLogger(logger, f"get_job_{job_id}")
    request_logger.log_request_start("GET", f"/api/v2/jobs/{job_id}", current_user.username)
    
    try:
        # Initialize service layer
        jobs_mgmt_service = JobsManagementService(db)
        
        # Get job through service layer (with caching)
        job_result = await jobs_mgmt_service.get_job_by_id(
            job_id=job_id,
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = JobResponse(**job_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Job retrieval by ID successful via service layer",
            extra={
                "job_id": job_id,
                "job_name": job_result.get("name", "unknown"),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except JobsManagementError as e:
        request_logger.log_request_end(status.HTTP_404_NOT_FOUND if e.error_code == "job_not_found" else status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Job retrieval by ID failed via service layer",
            extra={
                "job_id": job_id,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        status_code = status.HTTP_404_NOT_FOUND if e.error_code == "job_not_found" else status.HTTP_500_INTERNAL_SERVER_ERROR
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Job retrieval by ID error via service layer",
            extra={
                "job_id": job_id,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving the job",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.post(
    "/{job_id}/execute",
    response_model=JobExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Job",
    description="""
    Execute a job with comprehensive tracking and validation.
    
    **Phase 1 & 2 Features:**
    - ✅ Advanced job execution validation
    - ✅ Real-time execution tracking
    - ✅ Comprehensive audit logging
    - ✅ Enhanced execution metadata
    """,
    responses={
        200: {"description": "Job execution initiated successfully", "model": JobExecutionResponse}
    }
)
async def execute_job(
    job_id: int,
    execution_data: JobExecutionRequest,
    request: Request,
    current_user = Depends(require_job_permissions),
    db: Session = Depends(get_db)
) -> JobExecutionResponse:
    """Enhanced job execution with service layer and comprehensive tracking"""
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_logger = RequestLogger(logger, f"execute_job_{job_id}")
    request_logger.log_request_start("POST", f"/api/v2/jobs/{job_id}/execute", current_user.username)
    
    try:
        # Initialize service layer
        jobs_mgmt_service = JobsManagementService(db)
        
        # Execute job through service layer
        execution_result = await jobs_mgmt_service.execute_job(
            job_id=job_id,
            execution_params=execution_data.model_dump(),
            current_user_id=current_user.id,
            current_username=current_user.username,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        response = JobExecutionResponse(**execution_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Job execution successful via service layer",
            extra={
                "job_id": job_id,
                "task_id": execution_result["task_id"],
                "executed_by": current_user.username
            }
        )
        
        return response
        
    except JobsManagementError as e:
        request_logger.log_request_end(status.HTTP_404_NOT_FOUND if e.error_code == "job_not_found" else status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Job execution failed via service layer",
            extra={
                "job_id": job_id,
                "error_code": e.error_code,
                "error_message": e.message,
                "executed_by": current_user.username
            }
        )
        
        status_code = status.HTTP_404_NOT_FOUND if e.error_code == "job_not_found" else status.HTTP_500_INTERNAL_SERVER_ERROR
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Job execution error via service layer",
            extra={
                "job_id": job_id,
                "error": str(e),
                "executed_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while executing the job",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/statistics",
    response_model=JobStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Job Statistics",
    description="""
    Get comprehensive job statistics with analytics and trends.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 5-minute TTL
    - ✅ Advanced analytics and performance metrics
    - ✅ Real-time job monitoring statistics
    - ✅ Enhanced statistics with execution history
    """,
    responses={
        200: {"description": "Job statistics retrieved successfully", "model": JobStatisticsResponse}
    }
)
async def get_job_statistics(
    current_user = Depends(require_job_permissions),
    db: Session = Depends(get_db)
) -> JobStatisticsResponse:
    """Enhanced job statistics with service layer and comprehensive analytics"""
    
    request_logger = RequestLogger(logger, "get_job_statistics")
    request_logger.log_request_start("GET", "/api/v2/jobs/statistics", current_user.username)
    
    try:
        # Initialize service layer
        jobs_mgmt_service = JobsManagementService(db)
        
        # Get statistics through service layer (with caching)
        stats_result = await jobs_mgmt_service.get_jobs_statistics(
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        response = JobStatisticsResponse(**stats_result)
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Job statistics retrieval successful via service layer",
            extra={
                "total_jobs": stats_result.get("total_jobs", 0),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except JobsManagementError as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.warning(
            "Job statistics retrieval failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Job statistics retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving job statistics",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


class JobUpdateRequest(BaseModel):
    """Request model for updating jobs"""
    name: Optional[str] = Field(None, description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    actions: Optional[List[JobActionCreateV2]] = Field(None, description="Job actions")
    target_ids: Optional[List[int]] = Field(None, description="Target system IDs")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled execution time")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Job priority (1-10)")
    timeout: Optional[int] = Field(None, ge=1, description="Job timeout in seconds")
    retry_count: Optional[int] = Field(None, ge=0, le=5, description="Number of retries")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Network Discovery Job",
                "description": "Updated description",
                "scheduled_at": "2025-01-01T02:00:00Z",
                "priority": 8
            }
        }


@router.put(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Job",
    description="""
    Update an existing job with new information.
    
    **Features:**
    - ✅ Partial updates (only provided fields are updated)
    - ✅ Enhanced job data with execution history
    - ✅ Comprehensive error handling
    - ✅ Audit logging for changes
    """,
    responses={
        200: {"description": "Job updated successfully", "model": JobResponse},
        404: {"description": "Job not found"},
        403: {"description": "Insufficient permissions"}
    }
)
async def update_job(
    job_id: int,
    job_update: JobUpdateRequest,
    current_user = Depends(require_job_permissions),
    db: Session = Depends(get_db)
) -> JobResponse:
    """Enhanced job update with service layer and comprehensive features"""
    
    request_logger = RequestLogger(logger, "update_job")
    request_logger.log_request_start("PUT", f"/api/v2/jobs/{job_id}", current_user.username)
    
    try:
        # Initialize service layer
        jobs_mgmt_service = JobsManagementService(db)
        
        # Update job through service layer
        updated_job = await jobs_mgmt_service.update_job(
            job_id=job_id,
            job_update_data=job_update.dict(exclude_unset=True),
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, 1)
        
        logger.info(
            "Job update successful",
            extra={
                "job_id": job_id,
                "updated_by": current_user.username,
                "fields_updated": list(job_update.dict(exclude_unset=True).keys())
            }
        )
        
        return updated_job
        
    except JobsManagementError as e:
        request_logger.log_request_end(status.HTTP_400_BAD_REQUEST, 0)
        
        logger.warning(
            "Job update failed via service layer",
            extra={
                "job_id": job_id,
                "error_code": e.error_code,
                "error_message": e.message,
                "updated_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Job update error via service layer",
            extra={
                "job_id": job_id,
                "error": str(e),
                "updated_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while updating the job",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Job",
    description="""
    Delete a job and all its associated data.
    
    **Features:**
    - ✅ Cascading deletion of related data
    - ✅ Comprehensive error handling
    - ✅ Audit logging for deletion
    - ✅ Soft delete option (preserves history)
    """,
    responses={
        200: {"description": "Job deleted successfully"},
        404: {"description": "Job not found"},
        403: {"description": "Insufficient permissions"}
    }
)
async def delete_job(
    job_id: int,
    soft_delete: bool = Query(False, description="Perform soft delete (preserve history)"),
    current_user = Depends(require_job_permissions),
    db: Session = Depends(get_db)
):
    """Enhanced job deletion with service layer and comprehensive features"""
    
    request_logger = RequestLogger(logger, "delete_job")
    request_logger.log_request_start("DELETE", f"/api/v2/jobs/{job_id}", current_user.username)
    
    try:
        # Initialize service layer
        jobs_mgmt_service = JobsManagementService(db)
        
        # Delete job through service layer
        result = await jobs_mgmt_service.delete_job(
            job_id=job_id,
            soft_delete=soft_delete,
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, 1)
        
        logger.info(
            "Job deletion successful",
            extra={
                "job_id": job_id,
                "soft_delete": soft_delete,
                "deleted_by": current_user.username
            }
        )
        
        return {
            "message": "Job deleted successfully",
            "job_id": job_id,
            "soft_delete": soft_delete,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except JobsManagementError as e:
        request_logger.log_request_end(status.HTTP_400_BAD_REQUEST, 0)
        
        logger.warning(
            "Job deletion failed via service layer",
            extra={
                "job_id": job_id,
                "error_code": e.error_code,
                "error_message": e.message,
                "deleted_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Job deletion error via service layer",
            extra={
                "job_id": job_id,
                "error": str(e),
                "deleted_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while deleting the job",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/{job_id}/targets",
    status_code=status.HTTP_200_OK,
    summary="Get Job Targets",
    description="""
    Get all targets associated with a specific job.
    
    **Features:**
    - ✅ Complete target information
    - ✅ Target connection status
    - ✅ Comprehensive error handling
    """,
    responses={
        200: {"description": "Job targets retrieved successfully"},
        404: {"description": "Job not found"}
    }
)
async def get_job_targets(
    job_id: int,
    current_user = Depends(require_job_permissions),
    db: Session = Depends(get_db)
):
    """Get targets associated with a job"""
    
    request_logger = RequestLogger(logger, "get_job_targets")
    request_logger.log_request_start("GET", f"/api/v2/jobs/{job_id}/targets", current_user.username)
    
    try:
        # Initialize service layer
        jobs_mgmt_service = JobsManagementService(db)
        
        # Get job targets through service layer
        targets = await jobs_mgmt_service.get_job_targets(
            job_id=job_id,
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(targets))
        
        return {
            "job_id": job_id,
            "targets": targets,
            "total": len(targets),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except JobsManagementError as e:
        request_logger.log_request_end(status.HTTP_404_NOT_FOUND, 0)
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.error_code,
                "message": e.message,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Job targets retrieval error",
            extra={
                "job_id": job_id,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving job targets",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/{job_id}/executions",
    status_code=status.HTTP_200_OK,
    summary="Get Job Execution History",
    description="""
    Get execution history for a specific job.
    
    **Features:**
    - ✅ Complete execution information with serial numbers
    - ✅ Execution status and timing details
    - ✅ Pagination support
    - ✅ Comprehensive error handling
    """,
    responses={
        200: {"description": "Job execution history retrieved successfully"},
        404: {"description": "Job not found"}
    }
)
async def get_job_executions(
    job_id: int,
    skip: int = Query(0, ge=0, description="Number of executions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of executions to return"),
    current_user = Depends(require_job_permissions),
    db: Session = Depends(get_db)
):
    """Get execution history for a job"""
    
    request_logger = RequestLogger(logger, "get_job_executions")
    request_logger.log_request_start("GET", f"/api/v2/jobs/{job_id}/executions", current_user.username)
    
    try:
        # Initialize service layer
        jobs_mgmt_service = JobsManagementService(db)
        
        # Get job executions through service layer
        executions_data = await jobs_mgmt_service.get_job_executions(
            job_id=job_id,
            skip=skip,
            limit=limit,
            current_user_id=current_user.id,
            current_username=current_user.username
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(executions_data.get('executions', [])))
        
        return executions_data
        
    except JobsManagementError as e:
        request_logger.log_request_end(status.HTTP_404_NOT_FOUND, 0)
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": e.error_code,
                "message": e.message,
                "timestamp": e.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Job executions retrieval error",
            extra={
                "job_id": job_id,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving job executions",
                "timestamp": datetime.utcnow().isoformat()
            }
        )