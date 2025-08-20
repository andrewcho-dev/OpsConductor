"""
Configuration management API endpoints.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.config_service import ConfigService
from app.schemas.config import (
    ConfigurationResponse, ConfigurationCategoryResponse, ConfigurationBatchUpdate,
    ConfigurationBatchResponse, SessionConfigResponse, PasswordPolicyResponse,
    SecurityConfigResponse, AuditConfigResponse, UserManagementConfigResponse,
    CompleteConfigResponse
)
from app.core.auth_dependencies import get_current_user, require_admin

router = APIRouter(prefix="/config", tags=["configuration"])


@router.get("/", response_model=CompleteConfigResponse)
async def get_all_configuration(
    db: Session = Depends(get_db)
    # TODO: Re-enable authentication: current_user = Depends(get_current_user)
):
    """Get complete configuration (all categories)."""
    try:
        config_service = ConfigService(db)
        all_config = config_service.get_all_config()
        
        # Transform to structured response
        return CompleteConfigResponse(
            session=SessionConfigResponse(
                timeout_minutes=all_config.get("session", {}).get("session.timeout_minutes", {}).get("value", 30),
                warning_minutes=all_config.get("session", {}).get("session.warning_minutes", {}).get("value", 5),
                max_concurrent=all_config.get("session", {}).get("session.max_concurrent", {}).get("value", 3),
                idle_timeout_minutes=all_config.get("session", {}).get("session.idle_timeout_minutes", {}).get("value", 15),
                remember_me_days=all_config.get("session", {}).get("session.remember_me_days", {}).get("value", 30)
            ),
            password=PasswordPolicyResponse(
                min_length=all_config.get("password", {}).get("password.min_length", {}).get("value", 8),
                max_length=all_config.get("password", {}).get("password.max_length", {}).get("value", 128),
                require_uppercase=all_config.get("password", {}).get("password.require_uppercase", {}).get("value", True),
                require_lowercase=all_config.get("password", {}).get("password.require_lowercase", {}).get("value", True),
                require_numbers=all_config.get("password", {}).get("password.require_numbers", {}).get("value", True),
                require_special=all_config.get("password", {}).get("password.require_special", {}).get("value", True),
                special_chars=all_config.get("password", {}).get("password.special_chars", {}).get("value", "!@#$%^&*()_+-=[]{}|;:,.<>?"),
                expiry_days=all_config.get("password", {}).get("password.expiry_days", {}).get("value", 90),
                history_count=all_config.get("password", {}).get("password.history_count", {}).get("value", 5),
                min_age_hours=all_config.get("password", {}).get("password.min_age_hours", {}).get("value", 24)
            ),
            security=SecurityConfigResponse(
                max_failed_attempts=all_config.get("security", {}).get("security.max_failed_attempts", {}).get("value", 5),
                lockout_duration_minutes=all_config.get("security", {}).get("security.lockout_duration_minutes", {}).get("value", 30),
                progressive_lockout=all_config.get("security", {}).get("security.progressive_lockout", {}).get("value", True),
                require_email_verification=all_config.get("security", {}).get("security.require_email_verification", {}).get("value", True),
                force_password_change_first_login=all_config.get("security", {}).get("security.force_password_change_first_login", {}).get("value", True),
                enable_two_factor=all_config.get("security", {}).get("security.enable_two_factor", {}).get("value", False)
            ),
            audit=AuditConfigResponse(
                log_all_events=all_config.get("audit", {}).get("audit.log_all_events", {}).get("value", True),
                retention_days=all_config.get("audit", {}).get("audit.retention_days", {}).get("value", 365),
                log_failed_attempts=all_config.get("audit", {}).get("audit.log_failed_attempts", {}).get("value", True)
            ),
            users=UserManagementConfigResponse(
                default_role=all_config.get("users", {}).get("users.default_role", {}).get("value", "user"),
                allow_self_registration=all_config.get("users", {}).get("users.allow_self_registration", {}).get("value", False),
                require_admin_approval=all_config.get("users", {}).get("users.require_admin_approval", {}).get("value", True)
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving configuration: {str(e)}"
        )


@router.get("/session", response_model=SessionConfigResponse)
async def get_session_config(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get security configuration (admin only)."""
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


@router.get("/audit", response_model=AuditConfigResponse)
async def get_audit_config(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get audit configuration (admin only)."""
    try:
        config_service = ConfigService(db)
        audit_config = config_service.get_config_by_category("audit")
        
        return AuditConfigResponse(
            log_all_events=audit_config.get("audit.log_all_events", {}).get("value", True),
            retention_days=audit_config.get("audit.retention_days", {}).get("value", 365),
            log_failed_attempts=audit_config.get("audit.log_failed_attempts", {}).get("value", True)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit configuration: {str(e)}"
        )


@router.get("/users", response_model=UserManagementConfigResponse)
async def get_user_management_config(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get user management configuration (admin only)."""
    try:
        config_service = ConfigService(db)
        users_config = config_service.get_config_by_category("users")
        
        return UserManagementConfigResponse(
            default_role=users_config.get("users.default_role", {}).get("value", "user"),
            allow_self_registration=users_config.get("users.allow_self_registration", {}).get("value", False),
            require_admin_approval=users_config.get("users.require_admin_approval", {}).get("value", True)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user management configuration: {str(e)}"
        )


@router.put("/batch", response_model=ConfigurationBatchResponse)
async def update_configuration_batch(
    updates: ConfigurationBatchUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Update multiple configuration values (admin only)."""
    try:
        config_service = ConfigService(db)
        results = config_service.update_config_batch(updates.updates, updated_by=current_user.id)
        
        successful = [key for key, success in results.items() if success]
        failed = {key: "Configuration not found or invalid" for key, success in results.items() if not success}
        
        return ConfigurationBatchResponse(
            successful=successful,
            failed=failed
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating configuration: {str(e)}"
        )


@router.put("/session", response_model=SessionConfigResponse)
async def update_session_config(
    config: SessionConfigResponse,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Update session configuration (admin only)."""
    try:
        config_service = ConfigService(db)
        updates = {
            "session.timeout_minutes": config.timeout_minutes,
            "session.warning_minutes": config.warning_minutes,
            "session.max_concurrent": config.max_concurrent,
            "session.idle_timeout_minutes": config.idle_timeout_minutes,
            "session.remember_me_days": config.remember_me_days
        }
        
        config_service.update_config_batch(updates, updated_by=current_user.id)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating session configuration: {str(e)}"
        )


@router.put("/password", response_model=PasswordPolicyResponse)
async def update_password_policy(
    policy: PasswordPolicyResponse,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Update password policy (admin only)."""
    try:
        config_service = ConfigService(db)
        updates = {
            "password.min_length": policy.min_length,
            "password.max_length": policy.max_length,
            "password.require_uppercase": policy.require_uppercase,
            "password.require_lowercase": policy.require_lowercase,
            "password.require_numbers": policy.require_numbers,
            "password.require_special": policy.require_special,
            "password.special_chars": policy.special_chars,
            "password.expiry_days": policy.expiry_days,
            "password.history_count": policy.history_count,
            "password.min_age_hours": policy.min_age_hours
        }
        
        config_service.update_config_batch(updates, updated_by=current_user.id)
        return policy
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating password policy: {str(e)}"
        )


@router.put("/security", response_model=SecurityConfigResponse)
async def update_security_config(
    config: SecurityConfigResponse,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Update security configuration (admin only)."""
    try:
        config_service = ConfigService(db)
        updates = {
            "security.max_failed_attempts": config.max_failed_attempts,
            "security.lockout_duration_minutes": config.lockout_duration_minutes,
            "security.progressive_lockout": config.progressive_lockout,
            "security.require_email_verification": config.require_email_verification,
            "security.force_password_change_first_login": config.force_password_change_first_login,
            "security.enable_two_factor": config.enable_two_factor
        }
        
        config_service.update_config_batch(updates, updated_by=current_user.id)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating security configuration: {str(e)}"
        )


@router.put("/audit", response_model=AuditConfigResponse)
async def update_audit_config(
    config: AuditConfigResponse,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Update audit configuration (admin only)."""
    try:
        config_service = ConfigService(db)
        updates = {
            "audit.log_all_events": config.log_all_events,
            "audit.retention_days": config.retention_days,
            "audit.log_failed_attempts": config.log_failed_attempts
        }
        
        config_service.update_config_batch(updates, updated_by=current_user.id)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating audit configuration: {str(e)}"
        )


@router.put("/users", response_model=UserManagementConfigResponse)
async def update_user_management_config(
    config: UserManagementConfigResponse,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Update user management configuration (admin only)."""
    try:
        config_service = ConfigService(db)
        updates = {
            "users.default_role": config.default_role,
            "users.allow_self_registration": config.allow_self_registration,
            "users.require_admin_approval": config.require_admin_approval
        }
        
        config_service.update_config_batch(updates, updated_by=current_user.id)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user management configuration: {str(e)}"
        )


@router.post("/initialize", status_code=status.HTTP_204_NO_CONTENT)
async def initialize_default_config(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Initialize default configuration values (admin only)."""
    try:
        config_service = ConfigService(db)
        config_service.initialize_default_config()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing configuration: {str(e)}"
        )