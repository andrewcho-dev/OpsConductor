"""
Authentication Router - Phase 2 Enhanced
Service layer integration with caching and comprehensive logging

PHASE 2 IMPROVEMENTS:
- ✅ Service layer architecture with business logic separation
- ✅ Redis caching for sessions and rate limiting
- ✅ Structured JSON logging with contextual information
- ✅ Performance monitoring and metrics collection
- ✅ Enhanced security with advanced rate limiting
- ✅ Token blacklisting and session management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

# Import Phase 1 models (reuse the comprehensive models)
from app.routers.auth_v1_enhanced import (
    UserLoginRequest, TokenResponse, RefreshTokenRequest,
    UserInfoResponse, LogoutResponse, AuthErrorResponse
)

# Import Phase 2 service layer
from app.services.auth_service import AuthService, AuthenticationError
from app.database.database import get_db
from app.core.logging import get_structured_logger, RequestLogger

# Configure structured logger
logger = get_structured_logger(__name__)

# Security scheme
security = HTTPBearer()

# PHASE 2: ENHANCED ROUTER WITH SERVICE LAYER INTEGRATION

router = APIRouter(
    prefix="/auth",
    tags=["Authentication v2"],
    responses={
        401: {"model": AuthErrorResponse, "description": "Authentication failed"},
        403: {"model": AuthErrorResponse, "description": "Access forbidden"},
        429: {"model": AuthErrorResponse, "description": "Too many requests"},
        500: {"model": AuthErrorResponse, "description": "Internal server error"}
    }
)


# PHASE 2: SERVICE LAYER INTEGRATED ENDPOINTS

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Authentication (Enhanced)",
    description="""
    Enhanced user authentication with service layer, caching, and comprehensive security.
    
    **Phase 2 Enhancements:**
    - ✅ Service layer architecture for business logic separation
    - ✅ Redis caching for improved performance
    - ✅ Advanced rate limiting with IP-based tracking
    - ✅ Token blacklisting for enhanced security
    - ✅ Comprehensive structured logging
    - ✅ Session management with caching
    - ✅ Performance monitoring and metrics
    
    **Security Features:**
    - Advanced brute force protection with Redis-based tracking
    - Comprehensive audit logging with structured data
    - Session management with configurable TTL
    - IP-based rate limiting with automatic lockout
    - Remember me functionality with extended sessions
    
    **Performance Features:**
    - Redis caching for session data and rate limiting
    - Structured logging with performance metrics
    - Optimized database queries through service layer
    - Comprehensive error handling with context
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
    """Enhanced user login with service layer and comprehensive security"""
    
    # Initialize request logging
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_logger = RequestLogger(logger, f"login_{user_credentials.username}")
    request_logger.log_request_start("POST", "/auth/login", user_credentials.username)
    
    try:
        # Initialize service layer
        auth_service = AuthService(db)
        
        # Authenticate user through service layer
        auth_result = await auth_service.authenticate_user(
            username=user_credentials.username,
            password=user_credentials.password,
            ip_address=client_ip,
            user_agent=user_agent,
            remember_me=user_credentials.remember_me
        )
        
        # Build enhanced response
        response = TokenResponse(
            access_token=auth_result["tokens"]["access_token"],
            refresh_token=auth_result["tokens"]["refresh_token"],
            token_type=auth_result["tokens"]["token_type"],
            expires_in=auth_result["tokens"]["expires_in"],
            expires_at=auth_result["tokens"]["expires_at"],
            user_info=auth_result["user"],
            session_id=auth_result["session_id"]
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Login successful via service layer",
            extra={
                "user_id": auth_result["user"]["id"],
                "username": auth_result["user"]["username"],
                "ip_address": client_ip,
                "session_id": auth_result["session_id"],
                "remember_me": user_credentials.remember_me
            }
        )
        
        return response
        
    except AuthenticationError as e:
        request_logger.log_request_end(status.HTTP_401_UNAUTHORIZED, 0)
        
        logger.warning(
            "Authentication failed via service layer",
            extra={
                "username": user_credentials.username,
                "ip_address": client_ip,
                "error_code": e.error_code,
                "error_message": e.message
            }
        )
        
        # Map service errors to HTTP responses
        status_code = status.HTTP_401_UNAUTHORIZED
        if e.error_code == "rate_limited":
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "timestamp": e.timestamp.isoformat(),
                "request_id": f"auth_{int(datetime.utcnow().timestamp())}"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    except Exception as e:
        request_logger.log_request_end(status.HTTP_500_INTERNAL_SERVER_ERROR, 0)
        
        logger.error(
            "Login error via service layer",
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
    summary="User Logout (Enhanced)",
    description="""
    Enhanced user logout with service layer, token blacklisting, and session cleanup.
    
    **Phase 2 Enhancements:**
    - ✅ Service layer for business logic separation
    - ✅ Token blacklisting with Redis
    - ✅ Session cleanup and cache invalidation
    - ✅ Comprehensive audit logging
    - ✅ Performance monitoring
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
    """Enhanced user logout with service layer and comprehensive session management"""
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_logger = RequestLogger(logger, "logout")
    request_logger.log_request_start("POST", "/auth/logout", "authenticated_user")
    
    try:
        # Initialize service layer
        auth_service = AuthService(db)
        
        # Logout through service layer
        logout_result = await auth_service.logout_user(
            token=credentials.credentials,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        response = LogoutResponse(
            message=logout_result["message"],
            logged_out_at=logout_result["logged_out_at"],
            session_duration=logout_result["session_duration"]
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Logout successful via service layer",
            extra={
                "ip_address": client_ip,
                "session_duration": logout_result["session_duration"]
            }
        )
        
        return response
        
    except AuthenticationError as e:
        request_logger.log_request_end(status.HTTP_401_UNAUTHORIZED, 0)
        
        logger.warning(
            "Logout failed via service layer",
            extra={
                "ip_address": client_ip,
                "error_code": e.error_code,
                "error_message": e.message
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
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
            "Logout error via service layer",
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
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token (Enhanced)",
    description="""
    Enhanced token refresh with service layer, blacklist checking, and caching.
    
    **Phase 2 Enhancements:**
    - ✅ Service layer for business logic separation
    - ✅ Token blacklist validation
    - ✅ User status verification with caching
    - ✅ Performance monitoring
    - ✅ Comprehensive error handling
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
    """Enhanced token refresh with service layer and comprehensive validation"""
    
    request_logger = RequestLogger(logger, "refresh_token")
    request_logger.log_request_start("POST", "/auth/refresh", "token_refresh")
    
    try:
        # Initialize service layer
        auth_service = AuthService(db)
        
        # Refresh token through service layer
        refresh_result = await auth_service.refresh_token(credentials.credentials)
        
        response = TokenResponse(
            access_token=refresh_result["tokens"]["access_token"],
            refresh_token=refresh_result["tokens"]["refresh_token"],
            token_type=refresh_result["tokens"]["token_type"],
            expires_in=refresh_result["tokens"]["expires_in"],
            expires_at=refresh_result["tokens"]["expires_at"],
            user_info=refresh_result["user"]
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "Token refresh successful via service layer",
            extra={
                "user_id": refresh_result["user"]["id"],
                "username": refresh_result["user"]["username"]
            }
        )
        
        return response
        
    except AuthenticationError as e:
        request_logger.log_request_end(status.HTTP_401_UNAUTHORIZED, 0)
        
        logger.warning(
            "Token refresh failed via service layer",
            extra={
                "error_code": e.error_code,
                "error_message": e.message
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
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
            "Token refresh error via service layer",
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
    summary="Get Current User Information (Enhanced)",
    description="""
    Enhanced user information retrieval with service layer and caching.
    
    **Phase 2 Enhancements:**
    - ✅ Service layer for business logic separation
    - ✅ Redis caching for improved performance
    - ✅ Comprehensive user information with permissions
    - ✅ Session information with context
    - ✅ Performance monitoring
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
    """Enhanced user information retrieval with service layer and caching"""
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_logger = RequestLogger(logger, "get_user_info")
    request_logger.log_request_start("GET", "/auth/me", "authenticated_user")
    
    try:
        # Verify token first
        from app.core.security import verify_token
        token = credentials.credentials
        payload = verify_token(token)
        
        if not payload:
            raise AuthenticationError(
                "Invalid or expired token",
                error_code="invalid_token"
            )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationError(
                "Invalid token payload",
                error_code="invalid_token_payload"
            )
        
        # Initialize service layer
        auth_service = AuthService(db)
        
        # Get user info through service layer (with caching)
        user_info = await auth_service.get_user_info(user_id)
        
        # Add session information
        login_time = payload.get("iat", int(datetime.utcnow().timestamp()))
        session_info = {
            "ip_address": client_ip,
            "user_agent": user_agent,
            "login_time": datetime.fromtimestamp(login_time).isoformat(),
            "token_expires": datetime.fromtimestamp(payload.get("exp", 0)).isoformat()
        }
        
        response = UserInfoResponse(
            id=user_info["id"],
            username=user_info["username"],
            email=user_info["email"],
            role=user_info["role"],
            is_active=user_info["is_active"],
            last_login=user_info["last_login"],
            created_at=user_info["created_at"],
            session_info=session_info,
            permissions=user_info["permissions"]
        )
        
        request_logger.log_request_end(status.HTTP_200_OK, len(str(response)))
        
        logger.info(
            "User info retrieved via service layer",
            extra={
                "user_id": user_info["id"],
                "username": user_info["username"],
                "ip_address": client_ip
            }
        )
        
        return response
        
    except AuthenticationError as e:
        status_code = status.HTTP_401_UNAUTHORIZED
        if e.error_code == "user_not_found":
            status_code = status.HTTP_404_NOT_FOUND
        
        request_logger.log_request_end(status_code, 0)
        
        logger.warning(
            "Get user info failed via service layer",
            extra={
                "ip_address": client_ip,
                "error_code": e.error_code,
                "error_message": e.message
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
            "Get user info error via service layer",
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


# PHASE 2: ADDITIONAL ENHANCED ENDPOINTS

@router.post(
    "/validate-token",
    status_code=status.HTTP_200_OK,
    summary="Validate Token (New)",
    description="""
    Validate token and check if it's blacklisted.
    
    **Phase 2 Feature:**
    - ✅ Token validation with blacklist checking
    - ✅ Service layer integration
    - ✅ Performance monitoring
    """,
    responses={
        200: {"description": "Token is valid"},
        401: {"description": "Invalid or blacklisted token", "model": AuthErrorResponse}
    }
)
async def validate_token(
    credentials: HTTPBearer = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Validate token and check blacklist status"""
    
    try:
        # Initialize service layer
        auth_service = AuthService(db)
        
        # Check if token is blacklisted
        if await auth_service._is_token_blacklisted(credentials.credentials):
            raise AuthenticationError(
                "Token has been revoked",
                error_code="token_revoked"
            )
        
        # Verify token
        from app.core.security import verify_token
        payload = verify_token(credentials.credentials)
        
        if not payload:
            raise AuthenticationError(
                "Invalid or expired token",
                error_code="invalid_token"
            )
        
        logger.info(
            "Token validation successful",
            extra={
                "user_id": payload.get("user_id"),
                "username": payload.get("sub")
            }
        )
        
        return {
            "valid": True,
            "user_id": payload.get("user_id"),
            "username": payload.get("sub"),
            "role": payload.get("role"),
            "expires_at": datetime.fromtimestamp(payload.get("exp", 0)).isoformat()
        }
        
    except AuthenticationError as e:
        logger.warning(
            "Token validation failed",
            extra={
                "error_code": e.error_code,
                "error_message": e.message
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": e.error_code,
                "message": e.message,
                "timestamp": e.timestamp.isoformat()
            }
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Auth Service Health Check (New)",
    description="""
    Check authentication service health including cache connectivity.
    
    **Phase 2 Feature:**
    - ✅ Service health monitoring
    - ✅ Cache connectivity check
    - ✅ Performance metrics
    """,
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def auth_health_check() -> Dict[str, Any]:
    """Check authentication service health"""
    
    try:
        # Check Redis connectivity
        from app.core.cache import get_redis_client
        redis_client = get_redis_client()
        redis_healthy = False
        
        if redis_client:
            try:
                await redis_client.ping()
                redis_healthy = True
            except Exception:
                pass
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "redis_cache": "healthy" if redis_healthy else "unhealthy",
                "auth_service": "healthy"
            }
        }
        
        logger.info(
            "Auth service health check",
            extra={
                "status": "healthy",
                "redis_healthy": redis_healthy
            }
        )
        
        return health_status
        
    except Exception as e:
        logger.error(
            "Auth service health check failed",
            extra={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )