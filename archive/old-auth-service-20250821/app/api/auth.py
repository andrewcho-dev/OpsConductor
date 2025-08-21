from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.database import get_db
from app.schemas.auth import (
    UserLogin, TokenResponse, TokenRequest, TokenValidationResponse,
    SessionStatus, UserInfo
)
from app.services.auth_service import AuthService
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """User login with session-based authentication."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Authenticate user
    user = AuthService.authenticate_user(
        db, user_credentials.username, user_credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

    
    # Create session
    session_data = await AuthService.create_user_session(
        db, user, client_ip, user_agent
    )
    
    # Create user info
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        role=user.role,
        last_login=user.last_login
    )
    
    return TokenResponse(
        access_token=session_data["access_token"],
        session_id=session_data["session_id"],
        token_type="bearer",
        expires_in=settings.SESSION_TIMEOUT_MINUTES * 60,
        user=user_info
    )


@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(token_request: TokenRequest):
    """Validate a JWT token and return user information."""
    return await AuthService.validate_token(token_request.token)


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """User logout - destroys session."""
    # Validate token to get session ID
    validation_result = await AuthService.validate_token(credentials.credentials)
    
    if not validation_result.valid or not validation_result.session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Destroy session
    await AuthService.destroy_session(validation_result.session_id)
    
    return {"message": "Successfully logged out"}


@router.get("/session/status", response_model=SessionStatus)
async def get_session_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current session status."""
    # Validate token to get session ID
    validation_result = await AuthService.validate_token(credentials.credentials)
    
    if not validation_result.valid or not validation_result.session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    status_info = await AuthService.get_session_status(validation_result.session_id)
    return SessionStatus(**status_info)


@router.post("/session/extend")
async def extend_session(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Extend current session."""
    # Validate token to get session ID
    validation_result = await AuthService.validate_token(credentials.credentials)
    
    if not validation_result.valid or not validation_result.session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    extended = await AuthService.extend_session(validation_result.session_id)
    if not extended:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to extend session"
        )
    
    return {"message": "Session extended successfully"}


