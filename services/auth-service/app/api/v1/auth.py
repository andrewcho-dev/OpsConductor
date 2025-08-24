"""
Auth Service API Endpoints
Handles authentication - integrates with user-service for user data
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest, LoginResponse, TokenValidationRequest, TokenValidationResponse,
    LogoutRequest, SessionInfo
)

router = APIRouter()

# Global auth service instance
auth_service = AuthService()

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and create session
    Validates credentials with user-service
    """
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    return await auth_service.login(login_data, ip_address, user_agent, db)


@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(
    validation_data: TokenValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate JWT token
    Used by other services to verify authentication
    """
    return await auth_service.validate_token(validation_data.token, db)


@router.post("/logout")
async def logout(
    logout_data: LogoutRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Logout user and invalidate tokens
    """
    # Get token from Authorization header if not provided
    token = logout_data.token
    if not token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token required for logout"
        )
    
    success = await auth_service.logout(token, logout_data.all_sessions or False, db)
    
    if success:
        return {"message": "Logged out successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed"
        )


@router.get("/me")
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get current user information from token
    Used by shared JWT auth library
    """
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = auth_header.split(" ")[1]
    validation_result = await auth_service.validate_token(token, db)
    
    if not validation_result.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return validation_result.user


@router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get active sessions for current user
    """
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = auth_header.split(" ")[1]
    validation_result = await auth_service.validate_token(token, db)
    
    if not validation_result.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = validation_result.user["id"]
    sessions = await auth_service.get_user_sessions(user_id, db)
    
    return [SessionInfo(**session) for session in sessions]


@router.post("/refresh")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    TODO: Implement refresh token logic
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token functionality not yet implemented"
    )