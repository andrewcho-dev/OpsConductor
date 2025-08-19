"""
Auth API v3 - Consolidated from routers/auth_session.py
All authentication endpoints in v3 structure
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.schemas.user_schemas import UserLogin
from app.services.user_service import UserService
from app.core.session_security import (
    create_user_session, 
    verify_session_token, 
    destroy_user_session,
    get_session_status,
    extend_user_session
)
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity

router = APIRouter(prefix=f"{os.getenv(\'API_BASE_URL\', \'/api/v3\')}/auth", tags=["Auth v3"])
security = HTTPBearer()


class SessionToken(BaseModel):
    """Session token response model."""
    access_token: str
    session_id: str
    token_type: str = "bearer"


class SessionStatus(BaseModel):
    """Session status response model."""
    valid: bool
    expired: bool
    time_remaining: int
    warning: bool
    warning_threshold: int


class ExtendSessionRequest(BaseModel):
    """Request to extend session."""
    session_id: str


class RefreshTokenRequest(BaseModel):
    """Request to refresh token."""
    refresh_token: str


@router.post("/login", response_model=SessionToken)
async def login_with_session(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """User login with session-based authentication."""
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Authenticate user
    user = UserService.authenticate_user(
        db, user_credentials.username, user_credentials.password
    )
    if not user:
        # Log failed login attempt
        await audit_service.log_event(
            event_type=AuditEventType.LOGIN_FAILED,
            user_id=None,
            resource_type="authentication",
            resource_id=user_credentials.username,
            action="login_attempt",
            details={
                "username": user_credentials.username,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "reason": "invalid_credentials"
            },
            severity=AuditSeverity.HIGH,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        await audit_service.log_event(
            event_type=AuditEventType.LOGIN_FAILED,
            user_id=user.id,
            resource_type="authentication",
            resource_id=user.username,
            action="login_attempt",
            details={
                "username": user.username,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "reason": "account_inactive"
            },
            severity=AuditSeverity.HIGH,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create session
    session_data = create_user_session(user.id, client_ip, user_agent)
    
    # Log successful login
    await audit_service.log_event(
        event_type=AuditEventType.LOGIN_SUCCESS,
        user_id=user.id,
        resource_type="authentication",
        resource_id=user.username,
        action="login_success",
        details={
            "username": user.username,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "session_id": session_data["session_id"]
        },
        severity=AuditSeverity.INFO,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return SessionToken(
        access_token=session_data["access_token"],
        session_id=session_data["session_id"],
        token_type="bearer"
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User logout - destroys session."""
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Get session ID from current user context
    session_id = current_user.get("session_id")
    
    if session_id:
        # Destroy session
        destroy_user_session(session_id)
        
        # Log logout
        await audit_service.log_event(
            event_type=AuditEventType.LOGOUT,
            user_id=current_user["id"],
            resource_type="authentication",
            resource_id=current_user["username"],
            action="logout",
            details={
                "username": current_user["username"],
                "client_ip": client_ip,
                "user_agent": user_agent,
                "session_id": session_id
            },
            severity=AuditSeverity.INFO,
            ip_address=client_ip,
            user_agent=user_agent
        )
    
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=SessionToken)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        # For session-based auth, we extend the session instead of refreshing tokens
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Verify the refresh token is actually a session token
        session_data = verify_session_token(refresh_request.refresh_token)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Extend the session
        extended_session = extend_user_session(session_data["session_id"], client_ip, user_agent)
        if not extended_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh session"
            )
        
        return SessionToken(
            access_token=extended_session["access_token"],
            session_id=extended_session["session_id"],
            token_type="bearer"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/session/status", response_model=SessionStatus)
async def get_session_status_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current session status."""
    session_id = current_user.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session"
        )
    
    status_info = get_session_status(session_id)
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found"
        )
    
    return SessionStatus(**status_info)


@router.post("/session/extend")
async def extend_session(
    extend_request: ExtendSessionRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Extend current session."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Verify the session belongs to the current user
    if extend_request.session_id != current_user.get("session_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot extend another user's session"
        )
    
    extended_session = extend_user_session(extend_request.session_id, client_ip, user_agent)
    if not extended_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to extend session"
        )
    
    return {"message": "Session extended successfully"}


@router.post("/session/activity")
async def log_session_activity(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Log user activity to extend session."""
    session_id = current_user.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session"
        )
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Extend the session based on activity
    extended_session = extend_user_session(session_id, client_ip, user_agent)
    if not extended_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to log activity"
        )
    
    return {"message": "Activity logged successfully"}


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current user information."""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user.get("email"),
        "role": current_user["role"],
        "is_active": current_user.get("is_active", True),
        "session_id": current_user.get("session_id")
    }