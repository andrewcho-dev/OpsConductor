"""
Configuration management API endpoints - AUTHENTICATION ONLY!
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.config_service import ConfigService
from app.schemas.config import (
    SessionConfigResponse, PasswordPolicyResponse, SecurityConfigResponse
)
from app.core.auth_dependencies import get_current_user, require_admin

router = APIRouter(prefix="/config", tags=["configuration"])


@router.get("/session", response_model=SessionConfigResponse)
async def get_session_config(
    db: Session = Depends(get_db)
):
    """Get session management configuration."""
    try:
        config_service = ConfigService(db)
        session_config = config_service.get_config_by_category("session")
        
        return SessionConfigResponse(
            timeout_minutes=session_config.get("session.timeout_minutes", {}).get("value", 30),
            warning_minutes=session_config.get("session.warning_minutes", {}).get("value", 5),
            max_concurrent=session_config.get("session.max_concurrent", {}).get("value", 3),
            idle_timeout_minutes=session_config.get("session.idle_timeout_minutes", {}).get("value", 15),
            remember_me_days=session_config.get("session.remember_me_days", {}).get("value", 30)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session configuration: {str(e)}"
        )


@router.get("/password", response_model=PasswordPolicyResponse)
async def get_password_policy(
    db: Session = Depends(get_db)
):
    """Get password policy configuration."""
    try:
        config_service = ConfigService(db)
        password_config = config_service.get_config_by_category("password")
        
        return PasswordPolicyResponse(
            min_length=password_config.get("password.min_length", {}).get("value", 8),
            max_length=password_config.get("password.max_length", {}).get("value", 128),
            require_uppercase=password_config.get("password.require_uppercase", {}).get("value", True),
            require_lowercase=password_config.get("password.require_lowercase", {}).get("value", True),
            require_numbers=password_config.get("password.require_numbers", {}).get("value", True),
            require_special=password_config.get("password.require_special", {}).get("value", True),
            special_chars=password_config.get("password.special_chars", {}).get("value", "!@#$%^&*()_+-=[]{}|;:,.<>?"),
            expiry_days=password_config.get("password.expiry_days", {}).get("value", 90),
            history_count=password_config.get("password.history_count", {}).get("value", 5),
            min_age_hours=password_config.get("password.min_age_hours", {}).get("value", 24)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving password policy: {str(e)}"
        )


@router.get("/security", response_model=SecurityConfigResponse)
async def get_security_config(
    db: Session = Depends(get_db)
):
    """Get security configuration."""
    try:
        config_service = ConfigService(db)
        security_config = config_service.get_config_by_category("security")
        
        return SecurityConfigResponse(
            max_failed_attempts=security_config.get("security.max_failed_attempts", {}).get("value", 5),
            lockout_duration_minutes=security_config.get("security.lockout_duration_minutes", {}).get("value", 30),
            progressive_lockout=security_config.get("security.progressive_lockout", {}).get("value", True),
            require_email_verification=security_config.get("security.require_email_verification", {}).get("value", True),
            force_password_change_first_login=security_config.get("security.force_password_change_first_login", {}).get("value", True),
            enable_two_factor=security_config.get("security.enable_two_factor", {}).get("value", False)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving security configuration: {str(e)}"
        )