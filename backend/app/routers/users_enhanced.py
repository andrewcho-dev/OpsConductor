"""
Users Router - Phases 1 & 2 Enhanced
Complete transformation with service layer, caching, and comprehensive models

PHASE 1 & 2 IMPROVEMENTS:
- ✅ Comprehensive Pydantic models with validation
- ✅ Service layer integration with business logic separation
- ✅ Redis caching for improved performance
- ✅ Structured JSON logging with contextual information
- ✅ Enhanced error handling with detailed responses
- ✅ Advanced user search and filtering
- ✅ Role-based access control with permissions
- ✅ User activity tracking and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr

# Import service layer
from app.services.user_management_service import UserManagementService, UserManagementError
from app.database.database import get_db
from app.core.security import verify_token
from app.core.logging import get_structured_logger, RequestLogger

# Configure structured logger
logger = get_structured_logger(__name__)

# Security scheme
security = HTTPBearer()

# PHASE 1: COMPREHENSIVE PYDANTIC MODELS

class UserCreateRequest(BaseModel):
    """Enhanced request model for user creation"""
    username: str = Field(
        ..., 
        description="Unique username",
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_-]+$",
        example="john_doe"
    )
    email: EmailStr = Field(
        ..., 
        description="User email address",
        example="john.doe@example.com"
    )
    password: str = Field(
        ..., 
        description="User password",
        min_length=8,
        max_length=128,
        example="secure_password123"
    )
    role: str = Field(
        default="user",
        description="User role (administrator, manager, user, guest)",
        pattern="^(administrator|manager|user|guest)$",
        example="user"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the user account is active"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john.doe@example.com",
                "password": "secure_password123",
                "role": "user",
                "is_active": True
            }
        }


class UserUpdateRequest(BaseModel):
    """Enhanced request model for user updates"""
    email: Optional[EmailStr] = Field(
        None, 
        description="Updated email address",
        example="john.updated@example.com"
    )
    role: Optional[str] = Field(
        None,
        description="Updated user role",
        pattern="^(administrator|manager|user|guest)$",
        example="manager"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status"
    )
    password: Optional[str] = Field(
        None,
        description="Updated password",
        min_length=8,
        max_length=128
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.updated@example.com",
                "role": "manager",
                "is_active": True
            }
        }


class UserResponse(BaseModel):
    """Enhanced response model for user information"""
    id: int = Field(..., description="User unique identifier")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="User email address")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    permissions: List[str] = Field(..., description="User permissions based on role")
    profile: Dict[str, Any] = Field(..., description="User profile information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john.doe@example.com",
                "role": "user",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2025-01-01T10:30:00Z",
                "permissions": ["read:own", "write:own", "execute:jobs"],
                "profile": {
                    "preferences": {},
                    "settings": {},
                    "last_activity": "2025-01-01T10:30:00Z"
                }
            }
        }


class UserListResponse(BaseModel):
    """Enhanced response model for user list"""
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    skip: int = Field(..., description="Number of users skipped")
    limit: int = Field(..., description="Maximum number of users returned")
    filters: Dict[str, Any] = Field(..., description="Applied filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john.doe@example.com",
                        "role": "user",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "last_login": "2025-01-01T10:30:00Z",
                        "permissions": ["read:own", "write:own"],
                        "profile": {}
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 100,
                "filters": {
                    "search": None,
                    "role": None,
                    "is_active": None
                }
            }
        }


class UserSessionResponse(BaseModel):
    """Enhanced response model for user sessions"""
    session_id: str = Field(..., description="Session identifier")
    ip_address: str = Field(..., description="IP address of the session")
    user_agent: str = Field(..., description="User agent string")
    login_time: datetime = Field(..., description="Session login timestamp")
    is_active: bool = Field(..., description="Whether the session is active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_1_1640995200",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "login_time": "2025-01-01T10:30:00Z",
                "is_active": True
            }
        }


class UserDeleteResponse(BaseModel):
    """Enhanced response model for user deletion"""
    message: str = Field(..., description="Deletion confirmation message")
    deleted_user: Dict[str, Any] = Field(..., description="Information about deleted user")
    deleted_at: datetime = Field(..., description="Deletion timestamp")
    deleted_by: str = Field(..., description="Username who performed the deletion")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "User deleted successfully",
                "deleted_user": {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john.doe@example.com"
                },
                "deleted_at": "2025-01-01T11:30:00Z",
                "deleted_by": "admin"
            }
        }


class UserErrorResponse(BaseModel):
    """Enhanced error response model for user management errors"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "User creation failed due to validation errors",
                "details": {
                    "field_errors": "Username already exists"
                },
                "timestamp": "2025-01-01T10:30:00Z",
                "request_id": "user_req_abc123"
            }
        }


# PHASE 1 & 2: ENHANCED ROUTER WITH SERVICE LAYER INTEGRATION

router = APIRouter(
    prefix="/users",
    tags=["User Management"],
    responses={
        401: {"model": UserErrorResponse, "description": "Authentication required"},
        403: {"model": UserErrorResponse, "description": "Insufficient permissions"},
        404: {"model": UserErrorResponse, "description": "User not found"},
        422: {"model": UserErrorResponse, "description": "Validation error"},
        500: {"model": UserErrorResponse, "description": "Internal server error"}
    }
)


# PHASE 2: ENHANCED DEPENDENCY FUNCTIONS

def get_current_user(credentials: HTTPBearer = Depends(security), 
                    db: Session = Depends(get_db)):
    """Get current authenticated user with enhanced error handling."""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            logger.warning("Invalid token in user management request")
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


def require_admin_role(current_user = Depends(get_current_user)):
    """Require administrator role for access with enhanced error handling."""
    if current_user.role != "administrator":
        logger.warning(
            f"Access denied for user {current_user.username} with role {current_user.role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_permissions",
                "message": "Administrator access required",
                "details": {
                    "required_role": "administrator",
                    "current_role": current_user.role
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    return current_user


# PHASE 1 & 2: ENHANCED ENDPOINTS WITH SERVICE LAYER

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New User",
    description="""
    Create a new user account with comprehensive validation and audit logging.
    
    **Phase 1 & 2 Features:**
    - ✅ Comprehensive input validation with Pydantic models
    - ✅ Service layer integration for business logic separation
    - ✅ Enhanced audit logging with detailed context
    - ✅ Cache invalidation for user lists
    - ✅ User activity tracking
    - ✅ Role-based permission assignment
    
    **Security:**
    - Administrator role required
    - Comprehensive audit trail
    - Input validation and sanitization
    - Password strength requirements
    
    **Performance:**
    - Cache invalidation for optimal performance
    - Structured logging for monitoring
    """,
    responses={
        201: {"description": "User created successfully", "model": UserResponse},
        400: {"description": "Validation error", "model": UserErrorResponse},
        403: {"description": "Administrator access required", "model": UserErrorResponse}
    }
)
async def create_user(
    user_data: UserCreateRequest,
    request: Request,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Enhanced user creation with service layer and comprehensive features"""
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_logger = RequestLogger(logger, f"create_user_{user_data.username}")
    request_logger.log_request_start("POST", "/users", current_user.username)
    
    try:
        # Initialize service layer
        user_mgmt_service = UserManagementService(db)
        
        # Convert request to service format
        from app.schemas.user_schemas import UserCreate
        user_create_data = UserCreate(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role,
            is_active=user_data.is_active
        )
        
        # Create user through service layer
        created_user = await user_mgmt_service.create_user(
            user_data=user_create_data,
            current_user_id=current_user.id,
            current_username=current_user.username,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        response = UserResponse(
            id=created_user["id"],
            username=created_user["username"],
            email=created_user["email"],
            role=created_user["role"],
            is_active=created_user["is_active"],
            created_at=created_user["created_at"],
            last_login=created_user["last_login"],
            permissions=created_user.get("permissions", []),
            profile=created_user.get("profile", {})
        )
        
        request_logger.log_request_end(status.HTTP_201_CREATED, len(str(response)))
        
        logger.info(
            "User creation successful via service layer",
            extra={
                "created_user_id": created_user["id"],
                "created_username": created_user["username"],
                "created_by": current_user.username
            }
        )
        
        return response
        
    except UserManagementError as e:
        request_logger.log_request_end(status.HTTP_400_BAD_REQUEST, 0)
        
        logger.warning(
            "User creation failed via service layer",
            extra={
                "username": user_data.username,
                "error_code": e.error_code,
                "error_message": e.message,
                "created_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat(),
                "request_id": f"user_create_{int(datetime.utcnow().timestamp())}"
            }
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "User creation error via service layer",
            extra={
                "username": user_data.username,
                "error": str(e),
                "created_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred during user creation",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": f"user_error_{int(datetime.utcnow().timestamp())}"
            }
        )


@router.get(
    "/",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Users List",
    description="""
    Get paginated list of users with advanced filtering and search capabilities.
    
    **Phase 1 & 2 Features:**
    - ✅ Advanced pagination with skip/limit
    - ✅ Search functionality across username and email
    - ✅ Role-based filtering
    - ✅ Active status filtering
    - ✅ Redis caching for improved performance
    - ✅ Comprehensive response with metadata
    
    **Performance:**
    - Redis caching with 15-minute TTL
    - Optimized database queries
    - Structured logging for monitoring
    """,
    responses={
        200: {"description": "Users retrieved successfully", "model": UserListResponse},
        403: {"description": "Administrator access required", "model": UserErrorResponse}
    }
)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    search: Optional[str] = Query(None, description="Search term for username or email"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
) -> UserListResponse:
    """Enhanced user list retrieval with service layer and advanced filtering"""
    
    request_logger = RequestLogger(logger, "get_users")
    request_logger.log_request_start("GET", "/users", current_user.username)
    
    try:
        # Initialize service layer
        user_mgmt_service = UserManagementService(db)
        
        # Get users through service layer (with caching)
        users_result = await user_mgmt_service.get_users(
            skip=skip,
            limit=limit,
            search=search,
            role=role,
            is_active=is_active
        )
        
        # Convert to response format
        user_responses = []
        for user_data in users_result["users"]:
            user_responses.append(UserResponse(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"],
                is_active=user_data["is_active"],
                created_at=user_data["created_at"],
                last_login=user_data["last_login"],
                permissions=user_data.get("permissions", []),
                profile=user_data.get("profile", {})
            ))
        
        response = UserListResponse(
            users=user_responses,
            total=users_result["total"],
            skip=users_result["skip"],
            limit=users_result["limit"],
            filters=users_result["filters"]
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Users list retrieval successful via service layer",
            extra={
                "total_users": users_result["total"],
                "returned_users": len(user_responses),
                "filters_applied": bool(search or role or is_active is not None),
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Users list retrieval error via service layer",
            extra={
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving users",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User by ID",
    description="""
    Get detailed user information by ID with caching and comprehensive data.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis caching with 30-minute TTL
    - ✅ Comprehensive user information including permissions
    - ✅ User profile data and preferences
    - ✅ Enhanced error handling
    """,
    responses={
        200: {"description": "User retrieved successfully", "model": UserResponse},
        404: {"description": "User not found", "model": UserErrorResponse},
        403: {"description": "Administrator access required", "model": UserErrorResponse}
    }
)
async def get_user(
    user_id: int,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Enhanced user retrieval by ID with service layer and caching"""
    
    request_logger = RequestLogger(logger, f"get_user_{user_id}")
    request_logger.log_request_start("GET", f"/users/{user_id}", current_user.username)
    
    try:
        # Initialize service layer
        user_mgmt_service = UserManagementService(db)
        
        # Get user through service layer (with caching)
        user_data = await user_mgmt_service.get_user_by_id(user_id)
        
        response = UserResponse(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            role=user_data["role"],
            is_active=user_data["is_active"],
            created_at=user_data["created_at"],
            last_login=user_data["last_login"],
            permissions=user_data["permissions"],
            profile=user_data["profile"]
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "User retrieval successful via service layer",
            extra={
                "user_id": user_id,
                "username": user_data["username"],
                "requested_by": current_user.username
            }
        )
        
        return response
        
    except UserManagementError as e:
        status_code = status.HTTP_404_NOT_FOUND if e.error_code == "user_not_found" else status.HTTP_500_INTERNAL_SERVER_ERROR
        request_logger.log_request_end(status_code, 0)
        
        logger.warning(
            "User retrieval failed via service layer",
            extra={
                "user_id": user_id,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
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
            "User retrieval error via service layer",
            extra={
                "user_id": user_id,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving user",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User",
    description="""
    Update user information with change tracking and comprehensive audit logging.
    
    **Phase 1 & 2 Features:**
    - ✅ Change tracking and audit logging
    - ✅ Cache invalidation for updated data
    - ✅ Role change detection with permission logging
    - ✅ User activity tracking
    - ✅ Comprehensive validation
    """,
    responses={
        200: {"description": "User updated successfully", "model": UserResponse},
        404: {"description": "User not found", "model": UserErrorResponse},
        400: {"description": "Validation error", "model": UserErrorResponse},
        403: {"description": "Administrator access required", "model": UserErrorResponse}
    }
)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    request: Request,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Enhanced user update with service layer and comprehensive change tracking"""
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_logger = RequestLogger(logger, f"update_user_{user_id}")
    request_logger.log_request_start("PUT", f"/users/{user_id}", current_user.username)
    
    try:
        # Initialize service layer
        user_mgmt_service = UserManagementService(db)
        
        # Convert request to service format
        from app.schemas.user_schemas import UserUpdate
        user_update_data = UserUpdate(
            email=user_data.email,
            role=user_data.role,
            is_active=user_data.is_active,
            password=user_data.password
        )
        
        # Update user through service layer
        updated_user = await user_mgmt_service.update_user(
            user_id=user_id,
            user_data=user_update_data,
            current_user_id=current_user.id,
            current_username=current_user.username,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        response = UserResponse(
            id=updated_user["id"],
            username=updated_user["username"],
            email=updated_user["email"],
            role=updated_user["role"],
            is_active=updated_user["is_active"],
            created_at=updated_user["created_at"],
            last_login=updated_user["last_login"],
            permissions=updated_user.get("permissions", []),
            profile=updated_user.get("profile", {})
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "User update successful via service layer",
            extra={
                "user_id": user_id,
                "updated_username": updated_user["username"],
                "changes": updated_user.get("changes_applied", {}),
                "updated_by": current_user.username
            }
        )
        
        return response
        
    except UserManagementError as e:
        status_code = status.HTTP_404_NOT_FOUND if e.error_code == "user_not_found" else status.HTTP_400_BAD_REQUEST
        request_logger.log_request_end(status_code, 0)
        
        logger.warning(
            "User update failed via service layer",
            extra={
                "user_id": user_id,
                "error_code": e.error_code,
                "error_message": e.message,
                "updated_by": current_user.username
            }
        )
        
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
            "User update error via service layer",
            extra={
                "user_id": user_id,
                "error": str(e),
                "updated_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred during user update",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.delete(
    "/{user_id}",
    response_model=UserDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete User",
    description="""
    Delete user account with comprehensive audit logging and cache cleanup.
    
    **Phase 1 & 2 Features:**
    - ✅ Soft delete with comprehensive audit trail
    - ✅ Cache invalidation for deleted user
    - ✅ User activity tracking
    - ✅ Detailed deletion information
    """,
    responses={
        200: {"description": "User deleted successfully", "model": UserDeleteResponse},
        404: {"description": "User not found", "model": UserErrorResponse},
        403: {"description": "Administrator access required", "model": UserErrorResponse}
    }
)
async def delete_user(
    user_id: int,
    request: Request,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
) -> UserDeleteResponse:
    """Enhanced user deletion with service layer and comprehensive audit logging"""
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_logger = RequestLogger(logger, f"delete_user_{user_id}")
    request_logger.log_request_start("DELETE", f"/users/{user_id}", current_user.username)
    
    try:
        # Initialize service layer
        user_mgmt_service = UserManagementService(db)
        
        # Delete user through service layer
        deletion_result = await user_mgmt_service.delete_user(
            user_id=user_id,
            current_user_id=current_user.id,
            current_username=current_user.username,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        response = UserDeleteResponse(
            message=deletion_result["message"],
            deleted_user=deletion_result["deleted_user"],
            deleted_at=deletion_result["deleted_at"],
            deleted_by=deletion_result["deleted_by"]
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "User deletion successful via service layer",
            extra={
                "deleted_user_id": user_id,
                "deleted_username": deletion_result["deleted_user"]["username"],
                "deleted_by": current_user.username
            }
        )
        
        return response
        
    except UserManagementError as e:
        status_code = status.HTTP_404_NOT_FOUND if e.error_code == "user_not_found" else status.HTTP_500_INTERNAL_SERVER_ERROR
        request_logger.log_request_end(status_code, 0)
        
        logger.warning(
            "User deletion failed via service layer",
            extra={
                "user_id": user_id,
                "error_code": e.error_code,
                "error_message": e.message,
                "deleted_by": current_user.username
            }
        )
        
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
            "User deletion error via service layer",
            extra={
                "user_id": user_id,
                "error": str(e),
                "deleted_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred during user deletion",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/{user_id}/sessions",
    response_model=List[UserSessionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get User Sessions",
    description="""
    Get active sessions for a specific user with caching.
    
    **Phase 1 & 2 Features:**
    - ✅ Redis-based session retrieval
    - ✅ Session activity tracking
    - ✅ Comprehensive session information
    """,
    responses={
        200: {"description": "User sessions retrieved successfully", "model": List[UserSessionResponse]},
        404: {"description": "User not found", "model": UserErrorResponse},
        403: {"description": "Administrator access required", "model": UserErrorResponse}
    }
)
async def get_user_sessions(
    user_id: int,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
) -> List[UserSessionResponse]:
    """Enhanced user sessions retrieval with service layer and caching"""
    
    request_logger = RequestLogger(logger, f"get_user_sessions_{user_id}")
    request_logger.log_request_start("GET", f"/users/{user_id}/sessions", current_user.username)
    
    try:
        # Initialize service layer
        user_mgmt_service = UserManagementService(db)
        
        # Get user sessions through service layer (with caching)
        sessions = await user_mgmt_service.get_user_sessions(user_id)
        
        # Convert to response format
        session_responses = []
        for session_data in sessions:
            session_responses.append(UserSessionResponse(
                session_id=session_data["session_id"],
                ip_address=session_data["ip_address"],
                user_agent=session_data["user_agent"],
                login_time=datetime.fromisoformat(session_data["login_time"].replace('Z', '+00:00')),
                is_active=session_data["is_active"]
            ))
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(session_responses)))
        
        logger.info(
            "User sessions retrieval successful via service layer",
            extra={
                "user_id": user_id,
                "session_count": len(session_responses),
                "requested_by": current_user.username
            }
        )
        
        return session_responses
        
    except UserManagementError as e:
        status_code = status.HTTP_404_NOT_FOUND if e.error_code == "user_not_found" else status.HTTP_500_INTERNAL_SERVER_ERROR
        request_logger.log_request_end(status_code, 0)
        
        logger.warning(
            "User sessions retrieval failed via service layer",
            extra={
                "user_id": user_id,
                "error_code": e.error_code,
                "error_message": e.message,
                "requested_by": current_user.username
            }
        )
        
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
            "User sessions retrieval error via service layer",
            extra={
                "user_id": user_id,
                "error": str(e),
                "requested_by": current_user.username
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving user sessions",
                "timestamp": datetime.utcnow().isoformat()
            }
        )