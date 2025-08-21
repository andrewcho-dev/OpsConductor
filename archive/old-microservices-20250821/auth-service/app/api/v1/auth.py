"""
Authentication API endpoints for Auth Service
"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import uuid4

from app.core.database import get_db
from app.core.events import publish_auth_event
from app.core.redis_client import session_manager
from app.core.jwt_utils import jwt_manager
from app.core.password_utils import password_manager
from app.schemas.auth import (
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    TokenRefreshRequest, TokenResponse, TokenValidationRequest, TokenValidationResponse,
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
    LogoutRequest, UserSessionsResponse, LoginHistoryResponse,
    PasswordStrengthResponse, AuthErrorResponse
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from opsconductor_shared.models.base import EventType

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get auth service instance"""
    return AuthService(db)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency to get user service instance"""
    return UserService(db)


def get_client_info(request: Request) -> Dict[str, str]:
    """Extract client information from request"""
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }


# =============================================================================
# Authentication Endpoints
# =============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """User login endpoint"""
    client_info = get_client_info(request)
    
    try:
        # Check if user is locked out
        if await session_manager.is_locked_out(login_data.email):
            await publish_auth_event(
                event_type=EventType.USER_LOGIN_FAILED,
                data={
                    "email": login_data.email,
                    "reason": "account_locked",
                    "ip_address": client_info["ip_address"],
                    "user_agent": client_info["user_agent"]
                }
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed login attempts"
            )
        
        # Attempt login
        login_result = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
            client_info=client_info
        )
        
        if not login_result["success"]:
            # Record failed attempt
            await session_manager.record_login_attempt(login_data.email, success=False)
            
            await publish_auth_event(
                event_type=EventType.USER_LOGIN_FAILED,
                data={
                    "email": login_data.email,
                    "reason": login_result["error"],
                    "ip_address": client_info["ip_address"],
                    "user_agent": client_info["user_agent"]
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=login_result["message"]
            )
        
        user = login_result["user"]
        
        # Create session
        session_id = str(uuid4())
        session_expires = timedelta(
            days=7 if login_data.remember_me else 0,
            minutes=0 if login_data.remember_me else 480  # 8 hours
        )
        
        # Set default admin role and permissions for now (temporary fix)
        # TODO: Implement proper service-to-service authentication
        roles = ["admin"]  # Grant admin role to all users temporarily
        permissions = ["targets:read", "targets:write", "targets:delete", "users:read", "users:write", "users:delete"]  # Grant all permissions temporarily
        
        # Create user data for token
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "role": "admin" if "admin" in roles else (roles[0] if roles else "user"),
            "roles": roles,
            "permissions": permissions
        }
        
        # Create session in Redis
        await session_manager.create_session(
            session_id=session_id,
            user_id=user.id,
            user_data=user_data,
            expires_in_minutes=int(session_expires.total_seconds() / 60)
        )
        
        # Create JWT tokens
        access_token = jwt_manager.create_access_token(
            user_id=user.id,
            user_data=user_data,
            session_id=session_id
        )
        
        refresh_token = jwt_manager.create_refresh_token(
            user_id=user.id,
            session_id=session_id,
            expires_delta=session_expires
        )
        
        # Store session in database
        await auth_service.create_user_session(
            user_id=user.id,
            session_id=session_id,
            refresh_token=refresh_token,
            client_info=client_info,
            expires_at=datetime.utcnow() + session_expires
        )
        
        # Record successful login
        await session_manager.record_login_attempt(login_data.email, success=True)
        
        # Update user last login
        await auth_service.update_user_last_login(user.id)
        
        # Publish login event
        correlation_id = uuid4()
        await publish_auth_event(
            event_type=EventType.USER_LOGIN,
            data={
                "user_id": user.id,
                "email": user.email,
                "ip_address": client_info["ip_address"],
                "user_agent": client_info["user_agent"],
                "login_method": "password"
            },
            correlation_id=correlation_id,
            user_id=user.id
        )
        
        return LoginResponse(
            user=user,
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=jwt_manager.access_token_expire_minutes * 60,
                session_id=session_id
            ),
            session_info={
                "session_id": session_id,
                "expires_at": (datetime.utcnow() + session_expires).isoformat(),
                "remember_me": login_data.remember_me
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed for {login_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to internal error"
        )


@router.post("/logout")
async def logout(
    logout_data: LogoutRequest = LogoutRequest(),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """User logout endpoint"""
    try:
        # Verify token to get session info
        token_payload = jwt_manager.verify_token(credentials.credentials)
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_id = int(token_payload.get("sub"))
        session_id = token_payload.get("session_id")
        
        if logout_data.all_sessions:
            # Logout from all sessions
            await session_manager.delete_user_sessions(user_id)
            await auth_service.deactivate_user_sessions(user_id)
            
            await publish_auth_event(
                event_type=EventType.USER_LOGOUT,
                data={
                    "user_id": user_id,
                    "logout_reason": "user_initiated_all_sessions"
                },
                user_id=user_id
            )
        else:
            # Logout from current session only
            await session_manager.delete_session(session_id)
            await auth_service.deactivate_user_session(session_id)
            
            await publish_auth_event(
                event_type=EventType.USER_LOGOUT,
                data={
                    "user_id": user_id,
                    "session_id": session_id,
                    "logout_reason": "user_initiated"
                },
                user_id=user_id
            )
        
        return {"success": True, "message": "Logged out successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed due to internal error"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        token_payload = jwt_manager.verify_token(refresh_data.refresh_token)
        if not token_payload or token_payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = int(token_payload.get("sub"))
        session_id = token_payload.get("session_id")
        
        # Verify session exists and is active
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found or expired"
            )
        
        # Verify session in database
        db_session = await auth_service.get_user_session(session_id)
        if not db_session or not db_session.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session is not active"
            )
        
        # Get updated user data
        user = await auth_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not active"
            )
        
        # Create new access token
        user_data = session_data.get("user_data", {})
        new_access_token = jwt_manager.create_access_token(
            user_id=user_id,
            user_data=user_data,
            session_id=session_id
        )
        
        # Publish token refresh event
        await publish_auth_event(
            event_type=EventType.TOKEN_REFRESHED,
            data={
                "user_id": user_id,
                "session_id": session_id
            },
            user_id=user_id
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_data.refresh_token,  # Keep same refresh token
            expires_in=jwt_manager.access_token_expire_minutes * 60,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed due to internal error"
        )


@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(
    validation_data: TokenValidationRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Validate access token (used by other services)"""
    try:
        # Verify token
        token_payload = jwt_manager.verify_token(validation_data.token)
        if not token_payload:
            return TokenValidationResponse(
                valid=False,
                error="Invalid or expired token"
            )
        
        user_id = int(token_payload.get("sub"))
        session_id = token_payload.get("session_id")
        
        # Verify session exists and is active
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            return TokenValidationResponse(
                valid=False,
                error="Session not found or expired"
            )
        
        # Verify user is still active
        user = await auth_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            return TokenValidationResponse(
                valid=False,
                error="User is not active"
            )
        
        # Debug logging to see what's in session_data
        user_data = session_data.get("user_data")
        logger.info(f"VALIDATION - Session data: {session_data}")
        logger.info(f"VALIDATION - User data: {user_data}")
        
        # Return validation success with user data
        return TokenValidationResponse(
            valid=True,
            user=user_data,
            session_id=session_id,
            expires_at=datetime.fromisoformat(session_data.get("expires_at"))
        )
        
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return TokenValidationResponse(
            valid=False,
            error="Token validation failed due to internal error"
        )


# =============================================================================
# Password Management
# =============================================================================

@router.post("/password/strength", response_model=PasswordStrengthResponse)
async def check_password_strength(password: str):
    """Check password strength"""
    try:
        is_strong, errors = password_manager.validate_password_strength(password)
        
        # Calculate simple strength score
        score = max(0, 100 - (len(errors) * 20))
        
        suggestions = []
        if not is_strong:
            suggestions = [
                "Use a mix of uppercase and lowercase letters",
                "Include numbers and special characters",
                "Avoid common words and patterns",
                "Make it at least 12 characters long for better security"
            ]
        
        return PasswordStrengthResponse(
            is_strong=is_strong,
            score=score,
            errors=errors,
            suggestions=suggestions,
            requirements=password_manager.generate_password_requirements_text()
        )
        
    except Exception as e:
        logger.error(f"Password strength check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password strength check failed"
        )


@router.post("/password/change")
async def change_password(
    password_data: PasswordChangeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password"""
    try:
        # Verify token
        token_payload = jwt_manager.verify_token(credentials.credentials)
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_id = int(token_payload.get("sub"))
        
        # Change password
        result = await auth_service.change_password(
            user_id=user_id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        # Publish password change event
        await publish_auth_event(
            event_type=EventType.PASSWORD_CHANGED,
            data={
                "user_id": user_id,
                "change_reason": "user_initiated"
            },
            user_id=user_id
        )
        
        return {"success": True, "message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed due to internal error"
        )


# =============================================================================
# Session Management
# =============================================================================

@router.get("/sessions", response_model=UserSessionsResponse)
async def get_user_sessions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user's active sessions"""
    try:
        # Verify token
        token_payload = jwt_manager.verify_token(credentials.credentials)
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_id = int(token_payload.get("sub"))
        
        # Get sessions from database
        sessions = await auth_service.get_user_sessions(user_id)
        
        return UserSessionsResponse(
            sessions=sessions,
            total_sessions=len(sessions),
            active_sessions=len([s for s in sessions if s.is_active])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user sessions failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user sessions"
        )


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Terminate a specific session"""
    try:
        # Verify token
        token_payload = jwt_manager.verify_token(credentials.credentials)
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_id = int(token_payload.get("sub"))
        
        # Verify session belongs to user
        session = await auth_service.get_user_session(session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Terminate session
        await session_manager.delete_session(session_id)
        await auth_service.deactivate_user_session(session_id)
        
        await publish_auth_event(
            event_type=EventType.SESSION_TERMINATED,
            data={
                "user_id": user_id,
                "session_id": session_id,
                "terminated_by": "user"
            },
            user_id=user_id
        )
        
        return {"success": True, "message": "Session terminated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session termination failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session termination failed"
        )