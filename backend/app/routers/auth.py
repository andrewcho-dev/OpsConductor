from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.database import get_db
from app.schemas.user_schemas import UserLogin, Token, TokenData
from app.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """User login endpoint."""
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Authenticate user
    user = UserService.authenticate_user(
        db, user_credentials.username, user_credentials.password
    )
    if not user:
        # Check for potential brute force attack (multiple failed attempts from same IP)
        from app.shared.infrastructure.cache import cache_service
        await cache_service.initialize()
        
        failed_attempts_key = f"failed_login_attempts:{client_ip}"
        failed_attempts = await cache_service.get(failed_attempts_key) or 0
        failed_attempts += 1
        await cache_service.set(failed_attempts_key, failed_attempts, ttl=3600)  # 1 hour TTL
        
        # Determine severity based on failed attempts
        if failed_attempts >= 10:
            severity = AuditSeverity.CRITICAL  # Potential brute force attack
            action = "potential_brute_force_attack"
        elif failed_attempts >= 5:
            severity = AuditSeverity.HIGH
            action = "multiple_failed_logins"
        else:
            severity = AuditSeverity.HIGH
            action = "failed_login"
        
        # Log failed login attempt
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
                "potential_brute_force": failed_attempts >= 10
            },
            severity=severity,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    UserService.update_last_login(db, user.id)

    # Create user session
    UserService.create_user_session(
        db, user.id, 
        ip_address=client_ip,
        user_agent=user_agent
    )

    # Log successful login
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
            "user_agent": user_agent
        },
        severity=AuditSeverity.LOW,
        ip_address=client_ip,
        user_agent=user_agent
    )

    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPBearer = Depends(security),
    db: Session = Depends(get_db)
):
    """User logout endpoint."""
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("user_id")
    username = payload.get("sub")
    
    # Log logout event
    await audit_service.log_event(
        event_type=AuditEventType.USER_LOGOUT,
        user_id=user_id,
        resource_type="user",
        resource_id=str(user_id) if user_id else "unknown",
        action="logout",
        details={
            "username": username,
            "ip_address": client_ip,
            "user_agent": user_agent
        },
        severity=AuditSeverity.LOW,
        ip_address=client_ip,
        user_agent=user_agent
    )

    # In a real implementation, you might want to blacklist the token
    # For now, we'll just return success
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPBearer = Depends(security),
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    username = payload.get("sub")
    user_id = payload.get("user_id")
    role = payload.get("role")

    if not username or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Verify user still exists and is active
    user = UserService.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username, "user_id": user_id, "role": role},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": username, "user_id": user_id, "role": role}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.get("/me")
async def get_current_user_info(
    credentials: HTTPBearer = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user information."""
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

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "last_login": user.last_login
    } 