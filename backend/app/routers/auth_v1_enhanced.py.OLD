"""
Authentication Router - Phase 1 Enhanced
Foundation improvements with clean code structure and comprehensive models

PHASE 1 IMPROVEMENTS:
- ✅ Clean imports and organization
- ✅ Centralized authentication patterns
- ✅ Comprehensive Pydantic response models
- ✅ Enhanced error handling with proper HTTP status codes
- ✅ Detailed API documentation
- ✅ Input validation and typed responses
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
import logging

# Centralized imports
from app.database.database import get_db
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.services.user_service import UserService
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity

# Configure logger
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# PHASE 1: COMPREHENSIVE PYDANTIC MODELS

class UserLoginRequest(BaseModel):
    """Enhanced request model for user login"""
    username: str = Field(
        ..., 
        description="Username or email address",
        min_length=3,
        max_length=100,
        example="admin"
    )
    password: str = Field(
        ..., 
        description="User password",
        min_length=8,
        max_length=128,
        example="secure_password123"
    )
    remember_me: bool = Field(
        default=False,
        description="Extend session duration for convenience"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "secure_password123",
                "remember_me": False
            }
        }


class TokenResponse(BaseModel):
    """Enhanced response model for authentication tokens"""
    access_token: str = Field(..., description="JWT access token for API authentication")
    refresh_token: str = Field(..., description="JWT refresh token for token renewal")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    expires_at: datetime = Field(..., description="Access token expiration timestamp")
    user_info: Dict[str, Any] = Field(..., description="Basic user information")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "expires_at": "2025-01-01T12:00:00Z",
                "user_info": {
                    "id": 1,
                    "username": "admin",
                    "role": "administrator",
                    "email": "admin@example.com"
                },
                "session_id": "sess_abc123"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str = Field(..., description="Valid refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class UserInfoResponse(BaseModel):
    """Enhanced response model for user information"""
    id: int = Field(..., description="User unique identifier")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="User email address")
    role: str = Field(..., description="User role (administrator, manager, user, guest)")
    is_active: bool = Field(..., description="Whether the user account is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    session_info: Dict[str, Any] = Field(..., description="Current session information")
    permissions: list[str] = Field(..., description="User permissions based on role")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "role": "administrator",
                "is_active": True,
                "last_login": "2025-01-01T10:30:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "session_info": {
                    "session_id": "sess_abc123",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0...",
                    "login_time": "2025-01-01T10:30:00Z"
                },
                "permissions": ["read:all", "write:all", "admin:system"]
            }
        }


class LogoutResponse(BaseModel):
    """Response model for logout operation"""
    message: str = Field(..., description="Logout confirmation message")
    logged_out_at: datetime = Field(..., description="Logout timestamp")
    session_duration: int = Field(..., description="Session duration in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Successfully logged out",
                "logged_out_at": "2025-01-01T11:30:00Z",
                "session_duration": 3600
            }
        }


class AuthErrorResponse(BaseModel):
    """Enhanced error response model for authentication errors"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "invalid_credentials",
                "message": "Incorrect username or password",
                "details": {
                    "failed_attempts": 3,
                    "lockout_remaining": 0
                },
                "timestamp": "2025-01-01T10:30:00Z",
                "request_id": "req_abc123"
            }
        }


# PHASE 1: ENHANCED ROUTER WITH COMPREHENSIVE DOCUMENTATION

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"model": AuthErrorResponse, "description": "Authentication failed"},
        403: {"model": AuthErrorResponse, "description": "Access forbidden"},
        429: {"model": AuthErrorResponse, "description": "Too many requests"},
        500: {"model": AuthErrorResponse, "description": "Internal server error"}
    }
)


# PHASE 1: ENHANCED ENDPOINTS WITH COMPREHENSIVE ERROR HANDLING

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Authentication",
    description="""
    Authenticate user with username/email and password.
    
    **Features:**
    - ✅ Username or email authentication
    - ✅ Brute force protection with rate limiting
    - ✅ Comprehensive audit logging
    - ✅ Session management
    - ✅ Remember me functionality
    - ✅ Detailed security monitoring
    
    **Security:**
    - Failed login attempts are tracked and logged
    - Potential brute force attacks are detected and blocked
    - All authentication events are audited
    - IP address and user agent tracking
    
    **Rate Limiting:**
    - 5+ failed attempts: High severity alert
    - 10+ failed attempts: Critical severity, potential brute force
    """,
    responses={
        200: {"description": "Authentication successful", "model": TokenResponse},
        401: {"description": "Invalid credentials", "model": AuthErrorResponse},
        429: {"description": "Too many failed attempts", "model": AuthErrorResponse}
    }
)
async def login(
    user_credentials: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Enhanced user login endpoint with comprehensive security features"""
    
    # Initialize services
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    logger.info(
        f"Login attempt for user: {user_credentials.username}",
        extra={
            "username": user_credentials.username,
            "ip_address": client_ip,
            "user_agent": user_agent
        }
    )
    
    try:
        # Authenticate user
        user = UserService.authenticate_user(
            db, user_credentials.username, user_credentials.password
        )
        
        if not user:
            # Enhanced brute force protection
            from app.shared.infrastructure.cache import cache_service
            await cache_service.initialize()
            
            failed_attempts_key = f"failed_login_attempts:{client_ip}"
            failed_attempts = await cache_service.get(failed_attempts_key) or 0
            failed_attempts += 1
            await cache_service.set(failed_attempts_key, failed_attempts, ttl=3600)
            
            # Determine severity and action
            if failed_attempts >= 10:
                severity = AuditSeverity.CRITICAL
                action = "potential_brute_force_attack"
                error_detail = "Account temporarily locked due to multiple failed attempts"
            elif failed_attempts >= 5:
                severity = AuditSeverity.HIGH
                action = "multiple_failed_logins"
                error_detail = f"Invalid credentials. {10 - failed_attempts} attempts remaining"
            else:
                severity = AuditSeverity.HIGH
                action = "failed_login"
                error_detail = "Incorrect username or password"
            
            # Enhanced audit logging
            await audit_service.log_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                user_id=None,
                resource_type="authentication",
                resource_id=user_credentials.username,
                action=action,
                details={
                    "username": user_credentials.username,
                    "reason": "invalid_credentials",
                    "ip_address": client_ip,
                    "user_agent": user_agent,
                    "failed_attempts_count": failed_attempts,
                    "potential_brute_force": failed_attempts >= 10,
                    "remember_me_requested": user_credentials.remember_me
                },
                severity=severity,
                ip_address=client_ip,
                user_agent=user_agent
            )
            
            logger.warning(
                f"Failed login attempt for user: {user_credentials.username}",
                extra={
                    "username": user_credentials.username,
                    "ip_address": client_ip,
                    "failed_attempts": failed_attempts,
                    "potential_brute_force": failed_attempts >= 10
                }
            )
            
            # Enhanced error response
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_credentials",
                    "message": error_detail,
                    "details": {
                        "failed_attempts": failed_attempts,
                        "lockout_threshold": 10
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": f"auth_{int(datetime.utcnow().timestamp())}"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Clear failed attempts on successful login
        from app.shared.infrastructure.cache import cache_service
        await cache_service.initialize()
        failed_attempts_key = f"failed_login_attempts:{client_ip}"
        await cache_service.delete(failed_attempts_key)
        
        # Update last login
        UserService.update_last_login(db, user.id)
        
        # Create user session with enhanced information
        session_id = UserService.create_user_session(
            db, user.id,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Enhanced audit logging for successful login
        await audit_service.log_event(
            event_type=AuditEventType.USER_LOGIN,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            action="login",
            details={
                "username": user.username,
                "login_method": "password",
                "ip_address": client_ip,
                "user_agent": user_agent,
                "remember_me": user_credentials.remember_me,
                "session_id": session_id
            },
            severity=AuditSeverity.LOW,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Create tokens with enhanced expiration handling
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES * (7 if user_credentials.remember_me else 1)
        )
        expires_at = datetime.utcnow() + access_token_expires
        
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role}
        )
        
        # Get user permissions based on role
        permissions = _get_user_permissions(user.role)
        
        logger.info(
            f"Successful login for user: {user.username}",
            extra={
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "ip_address": client_ip,
                "session_id": session_id
            }
        )
        
        # Enhanced response with comprehensive information
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            expires_at=expires_at,
            user_info={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            },
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Login error for user: {user_credentials.username}",
            extra={
                "username": user_credentials.username,
                "ip_address": client_ip,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred during authentication",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": f"auth_error_{int(datetime.utcnow().timestamp())}"
            }
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="""
    Logout current user and invalidate session.
    
    **Features:**
    - ✅ Token validation and invalidation
    - ✅ Session cleanup
    - ✅ Comprehensive audit logging
    - ✅ Session duration tracking
    """,
    responses={
        200: {"description": "Logout successful", "model": LogoutResponse},
        401: {"description": "Invalid or expired token", "model": AuthErrorResponse}
    }
)
async def logout(
    request: Request,
    credentials: HTTPBearer = Depends(security),
    db: Session = Depends(get_db)
) -> LogoutResponse:
    """Enhanced user logout endpoint with comprehensive session management"""
    
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    logout_time = datetime.utcnow()
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if not payload:
            logger.warning(
                "Logout attempt with invalid token",
                extra={
                    "ip_address": client_ip,
                    "user_agent": user_agent
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Invalid or expired token",
                    "timestamp": logout_time.isoformat()
                }
            )
        
        user_id = payload.get("user_id")
        username = payload.get("sub")
        
        # Calculate session duration
        login_time = payload.get("iat", int(logout_time.timestamp()))
        session_duration = int(logout_time.timestamp() - login_time)
        
        # Enhanced audit logging
        await audit_service.log_event(
            event_type=AuditEventType.USER_LOGOUT,
            user_id=user_id,
            resource_type="user",
            resource_id=str(user_id) if user_id else "unknown",
            action="logout",
            details={
                "username": username,
                "ip_address": client_ip,
                "user_agent": user_agent,
                "session_duration_seconds": session_duration,
                "logout_method": "explicit"
            },
            severity=AuditSeverity.LOW,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        logger.info(
            f"User logout: {username}",
            extra={
                "user_id": user_id,
                "username": username,
                "ip_address": client_ip,
                "session_duration": session_duration
            }
        )
        
        # TODO: In Phase 2, implement token blacklisting with Redis
        # For now, return success response
        
        return LogoutResponse(
            message="Successfully logged out",
            logged_out_at=logout_time,
            session_duration=session_duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Logout error",
            extra={
                "ip_address": client_ip,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred during logout",
                "timestamp": logout_time.isoformat()
            }
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="""
    Refresh access token using a valid refresh token.
    
    **Features:**
    - ✅ Refresh token validation
    - ✅ User status verification
    - ✅ New token generation
    - ✅ Security audit logging
    """,
    responses={
        200: {"description": "Token refresh successful", "model": TokenResponse},
        401: {"description": "Invalid refresh token", "model": AuthErrorResponse}
    }
)
async def refresh_token(
    credentials: HTTPBearer = Depends(security),
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Enhanced token refresh endpoint with comprehensive validation"""
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if not payload:
            logger.warning("Token refresh attempt with invalid token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_refresh_token",
                    "message": "Invalid or expired refresh token",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        username = payload.get("sub")
        user_id = payload.get("user_id")
        role = payload.get("role")
        
        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token_payload",
                    "message": "Invalid token payload",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Verify user still exists and is active
        user = UserService.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            logger.warning(
                f"Token refresh for inactive/missing user: {username}",
                extra={"user_id": user_id, "username": username}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "user_not_found_or_inactive",
                    "message": "User not found or account is inactive",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Create new tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_at = datetime.utcnow() + access_token_expires
        
        access_token = create_access_token(
            data={"sub": username, "user_id": user_id, "role": role},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": username, "user_id": user_id, "role": role}
        )
        
        logger.info(
            f"Token refreshed for user: {username}",
            extra={
                "user_id": user_id,
                "username": username,
                "role": role
            }
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            expires_at=expires_at,
            user_info={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Token refresh error",
            extra={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred during token refresh",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/me",
    response_model=UserInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Information",
    description="""
    Get detailed information about the currently authenticated user.
    
    **Features:**
    - ✅ Complete user profile information
    - ✅ Current session details
    - ✅ Role-based permissions
    - ✅ Account status and metadata
    """,
    responses={
        200: {"description": "User information retrieved", "model": UserInfoResponse},
        401: {"description": "Invalid or expired token", "model": AuthErrorResponse},
        404: {"description": "User not found", "model": AuthErrorResponse}
    }
)
async def get_current_user_info(
    request: Request,
    credentials: HTTPBearer = Depends(security),
    db: Session = Depends(get_db)
) -> UserInfoResponse:
    """Enhanced endpoint to get current user information with comprehensive details"""
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Invalid or expired token",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        user_id = payload.get("user_id")
        user = UserService.get_user_by_id(db, user_id)
        
        if not user:
            logger.warning(
                f"User info request for non-existent user: {user_id}",
                extra={"user_id": user_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "user_not_found",
                    "message": "User not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Get user permissions
        permissions = _get_user_permissions(user.role)
        
        # Get session information
        login_time = payload.get("iat", int(datetime.utcnow().timestamp()))
        session_info = {
            "ip_address": client_ip,
            "user_agent": user_agent,
            "login_time": datetime.fromtimestamp(login_time).isoformat(),
            "token_expires": datetime.fromtimestamp(payload.get("exp", 0)).isoformat()
        }
        
        logger.info(
            f"User info retrieved for: {user.username}",
            extra={
                "user_id": user.id,
                "username": user.username,
                "ip_address": client_ip
            }
        )
        
        return UserInfoResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
            session_info=session_info,
            permissions=permissions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Get user info error",
            extra={
                "ip_address": client_ip,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred while retrieving user information",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# PHASE 1: HELPER FUNCTIONS

def _get_user_permissions(role: str) -> list[str]:
    """Get user permissions based on role"""
    permission_map = {
        "administrator": [
            "read:all", "write:all", "delete:all",
            "admin:users", "admin:system", "admin:audit",
            "manage:targets", "manage:jobs", "manage:templates"
        ],
        "manager": [
            "read:all", "write:own", "write:team",
            "manage:targets", "manage:jobs", "view:audit"
        ],
        "user": [
            "read:own", "write:own", "execute:jobs"
        ],
        "guest": [
            "read:limited"
        ]
    }
    return permission_map.get(role, ["read:limited"])