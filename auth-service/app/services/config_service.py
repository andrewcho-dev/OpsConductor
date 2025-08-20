"""
Configuration service for managing authentication and security settings.
"""
import json
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.user import AuthConfiguration
from app.database.database import get_db


class ConfigService:
    """Service for managing authentication configuration."""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        # Session Management
        "session.timeout_minutes": {
            "value": "30",
            "type": "integer",
            "category": "session",
            "description": "Session timeout in minutes"
        },
        "session.warning_minutes": {
            "value": "5",
            "type": "integer", 
            "category": "session",
            "description": "Minutes before session timeout to show warning"
        },
        "session.max_concurrent": {
            "value": "3",
            "type": "integer",
            "category": "session",
            "description": "Maximum concurrent sessions per user"
        },
        "session.idle_timeout_minutes": {
            "value": "15",
            "type": "integer",
            "category": "session",
            "description": "Idle timeout in minutes"
        },
        "session.remember_me_days": {
            "value": "30",
            "type": "integer",
            "category": "session",
            "description": "Remember me duration in days"
        },
        
        # Password Policies
        "password.min_length": {
            "value": "8",
            "type": "integer",
            "category": "password",
            "description": "Minimum password length"
        },
        "password.max_length": {
            "value": "128",
            "type": "integer",
            "category": "password",
            "description": "Maximum password length"
        },
        "password.require_uppercase": {
            "value": "true",
            "type": "boolean",
            "category": "password",
            "description": "Require at least one uppercase letter"
        },
        "password.require_lowercase": {
            "value": "true",
            "type": "boolean",
            "category": "password",
            "description": "Require at least one lowercase letter"
        },
        "password.require_numbers": {
            "value": "true",
            "type": "boolean",
            "category": "password",
            "description": "Require at least one number"
        },
        "password.require_special": {
            "value": "true",
            "type": "boolean",
            "category": "password",
            "description": "Require at least one special character"
        },
        "password.special_chars": {
            "value": "!@#$%^&*()_+-=[]{}|;:,.<>?",
            "type": "string",
            "category": "password",
            "description": "Allowed special characters"
        },
        "password.expiry_days": {
            "value": "90",
            "type": "integer",
            "category": "password",
            "description": "Password expiry in days (0 = never expires)"
        },
        "password.history_count": {
            "value": "5",
            "type": "integer",
            "category": "password",
            "description": "Number of previous passwords to remember"
        },
        "password.min_age_hours": {
            "value": "24",
            "type": "integer",
            "category": "password",
            "description": "Minimum hours before password can be changed again"
        },
        
        # Account Security
        "security.max_failed_attempts": {
            "value": "5",
            "type": "integer",
            "category": "security",
            "description": "Maximum failed login attempts before lockout"
        },
        "security.lockout_duration_minutes": {
            "value": "30",
            "type": "integer",
            "category": "security",
            "description": "Account lockout duration in minutes"
        },
        "security.progressive_lockout": {
            "value": "true",
            "type": "boolean",
            "category": "security",
            "description": "Enable progressive lockout (longer lockouts for repeated failures)"
        },
        "security.require_email_verification": {
            "value": "true",
            "type": "boolean",
            "category": "security",
            "description": "Require email verification for new accounts"
        },
        "security.force_password_change_first_login": {
            "value": "true",
            "type": "boolean",
            "category": "security",
            "description": "Force password change on first login"
        },
        "security.enable_two_factor": {
            "value": "false",
            "type": "boolean",
            "category": "security",
            "description": "Enable two-factor authentication"
        },
        
        # Audit and Compliance
        "audit.log_all_events": {
            "value": "true",
            "type": "boolean",
            "category": "audit",
            "description": "Log all authentication events"
        },
        "audit.retention_days": {
            "value": "365",
            "type": "integer",
            "category": "audit",
            "description": "Audit log retention period in days"
        },
        "audit.log_failed_attempts": {
            "value": "true",
            "type": "boolean",
            "category": "audit",
            "description": "Log failed login attempts"
        },
        
        # User Management
        "users.default_role": {
            "value": "user",
            "type": "string",
            "category": "users",
            "description": "Default role for new users"
        },
        "users.allow_self_registration": {
            "value": "false",
            "type": "boolean",
            "category": "users",
            "description": "Allow users to self-register"
        },
        "users.require_admin_approval": {
            "value": "true",
            "type": "boolean",
            "category": "users",
            "description": "Require admin approval for new accounts"
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def initialize_default_config(self) -> None:
        """Initialize database with default configuration values."""
        for key, config in self.DEFAULT_CONFIG.items():
            existing = self.db.query(AuthConfiguration).filter(
                AuthConfiguration.config_key == key
            ).first()
            
            if not existing:
                config_item = AuthConfiguration(
                    config_key=key,
                    config_value=config["value"],
                    config_type=config["type"],
                    category=config["category"],
                    description=config["description"]
                )
                self.db.add(config_item)
        
        self.db.commit()
    
    def get_config(self, key: str) -> Optional[Any]:
        """Get a configuration value by key."""
        config = self.db.query(AuthConfiguration).filter(
            AuthConfiguration.config_key == key
        ).first()
        
        if not config:
            return None
        
        return self._convert_value(config.config_value, config.config_type)
    
    def get_config_by_category(self, category: str) -> Dict[str, Any]:
        """Get all configuration values for a category."""
        configs = self.db.query(AuthConfiguration).filter(
            AuthConfiguration.category == category
        ).all()
        
        result = {}
        for config in configs:
            result[config.config_key] = {
                "value": self._convert_value(config.config_value, config.config_type),
                "type": config.config_type,
                "description": config.description,
                "updated_at": config.updated_at
            }
        
        return result
    
    def get_all_config(self) -> Dict[str, Dict[str, Any]]:
        """Get all configuration values grouped by category."""
        configs = self.db.query(AuthConfiguration).all()
        
        result = {}
        for config in configs:
            if config.category not in result:
                result[config.category] = {}
            
            result[config.category][config.config_key] = {
                "value": self._convert_value(config.config_value, config.config_type),
                "type": config.config_type,
                "description": config.description,
                "updated_at": config.updated_at
            }
        
        return result
    
    def set_config(self, key: str, value: Any, updated_by: Optional[int] = None) -> bool:
        """Set a configuration value."""
        config = self.db.query(AuthConfiguration).filter(
            AuthConfiguration.config_key == key
        ).first()
        
        if not config:
            return False
        
        config.config_value = self._serialize_value(value, config.config_type)
        config.updated_by = updated_by
        
        self.db.commit()
        return True
    
    def update_config_batch(self, updates: Dict[str, Any], updated_by: Optional[int] = None) -> Dict[str, bool]:
        """Update multiple configuration values."""
        results = {}
        
        for key, value in updates.items():
            results[key] = self.set_config(key, value, updated_by)
        
        return results
    
    def _convert_value(self, value: str, config_type: str) -> Any:
        """Convert string value to appropriate type."""
        if config_type == "boolean":
            return value.lower() in ("true", "1", "yes", "on")
        elif config_type == "integer":
            try:
                return int(value)
            except ValueError:
                return 0
        elif config_type == "json":
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        else:  # string
            return value
    
    def _serialize_value(self, value: Any, config_type: str) -> str:
        """Serialize value to string for storage."""
        if config_type == "boolean":
            return "true" if value else "false"
        elif config_type == "json":
            return json.dumps(value)
        else:
            return str(value)
    
    # Convenience methods for common configurations
    def get_session_timeout(self) -> int:
        """Get session timeout in minutes."""
        return self.get_config("session.timeout_minutes") or 30
    
    def get_session_warning(self) -> int:
        """Get session warning time in minutes."""
        return self.get_config("session.warning_minutes") or 5
    
    def get_max_concurrent_sessions(self) -> int:
        """Get maximum concurrent sessions per user."""
        return self.get_config("session.max_concurrent") or 3
    
    def get_password_policy(self) -> Dict[str, Any]:
        """Get complete password policy configuration."""
        return self.get_config_by_category("password")
    
    def get_security_settings(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self.get_config_by_category("security")
    
    def is_password_expired(self, password_changed_at) -> bool:
        """Check if password is expired based on policy."""
        expiry_days = self.get_config("password.expiry_days") or 0
        if expiry_days == 0:
            return False
        
        from datetime import datetime, timedelta
        expiry_date = password_changed_at + timedelta(days=expiry_days)
        return datetime.utcnow() > expiry_date
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password against current policy."""
        policy = self.get_password_policy()
        errors = []
        
        min_length = policy.get("password.min_length", {}).get("value", 8)
        max_length = policy.get("password.max_length", {}).get("value", 128)
        
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long")
        
        if len(password) > max_length:
            errors.append(f"Password must be no more than {max_length} characters long")
        
        if policy.get("password.require_uppercase", {}).get("value", True):
            if not any(c.isupper() for c in password):
                errors.append("Password must contain at least one uppercase letter")
        
        if policy.get("password.require_lowercase", {}).get("value", True):
            if not any(c.islower() for c in password):
                errors.append("Password must contain at least one lowercase letter")
        
        if policy.get("password.require_numbers", {}).get("value", True):
            if not any(c.isdigit() for c in password):
                errors.append("Password must contain at least one number")
        
        if policy.get("password.require_special", {}).get("value", True):
            special_chars = policy.get("password.special_chars", {}).get("value", "!@#$%^&*()_+-=[]{}|;:,.<>?")
            if not any(c in special_chars for c in password):
                errors.append(f"Password must contain at least one special character: {special_chars}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


def get_config_service(db: Session = None) -> ConfigService:
    """Get configuration service instance."""
    if db is None:
        db = next(get_db())
    return ConfigService(db)