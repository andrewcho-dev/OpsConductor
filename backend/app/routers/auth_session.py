"""
Session-based authentication router.
Replaces JWT token expiration with activity-based sessions.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.database import get_db
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
from pydantic import BaseModel

router = APIRouter()
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
                "reason": "account_disabled"
            },
            severity=AuditSeverity.HIGH,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create session-based token
    user_data = {
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "client_ip": client_ip,
        "user_agent": user_agent
    }
    
    session_info = await create_user_session(user.id, user_data)
    
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
            "session_id": session_info["session_id"]
        },
        severity=AuditSeverity.INFO,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return SessionToken(**session_info)


# Dependency to get current user from session token
async def get_current_user_session(
    credentials: HTTPBearer = Depends(security)
) -> Dict[str, Any]:
    """Get current user from session token."""
    token = credentials.credentials
    user_info = await verify_session_token(token)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info


@router.post("/logout")
async def logout_session(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
    db: Session = Depends(get_db)
):
    """Logout and destroy session."""
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    
    session_id = current_user.get("session_id")
    user_id = current_user.get("user_id")
    
    # Destroy session
    await destroy_user_session(session_id)
    
    # Log logout
    await audit_service.log_event(
        event_type=AuditEventType.LOGOUT,
        user_id=user_id,
        resource_type="authentication",
        resource_id=str(user_id),
        action="logout",
        details={
            "client_ip": client_ip,
            "session_id": session_id
        },
        severity=AuditSeverity.INFO,
        ip_address=client_ip
    )
    
    return {"message": "Successfully logged out"}


@router.get("/session/status", response_model=SessionStatus)
async def get_session_status_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user_session)
):
    """Get current session status."""
    session_id = current_user.get("session_id")
    status_info = await get_session_status(session_id)
    return SessionStatus(**status_info)


@router.post("/session/extend")
async def extend_session_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user_session)
):
    """Extend current session (reset timeout)."""
    session_id = current_user.get("session_id")
    success = await extend_user_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to extend session"
        )
    
    return {"message": "Session extended successfully"}


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user_session),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    user_id = current_user.get("user_id")
    user = UserService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "session_info": {
            "session_id": current_user.get("session_id"),
            "last_activity": current_user.get("last_activity")
        }
    }

