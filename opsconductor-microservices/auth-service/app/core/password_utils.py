"""
Password utilities for Auth Service
"""

import re
import logging
from typing import List, Tuple
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS
)


class PasswordManager:
    """Password management utilities"""
    
    def __init__(self):
        self.min_length = settings.PASSWORD_MIN_LENGTH
        self.require_uppercase = settings.PASSWORD_REQUIRE_UPPERCASE
        self.require_lowercase = settings.PASSWORD_REQUIRE_LOWERCASE
        self.require_numbers = settings.PASSWORD_REQUIRE_NUMBERS
        self.require_special = settings.PASSWORD_REQUIRE_SPECIAL
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        try:
            hashed = pwd_context.hash(password)
            logger.info("Password hashed successfully")
            return hashed
        except Exception as e:
            logger.error(f"Failed to hash password: {e}")
            raise
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            result = pwd_context.verify(plain_password, hashed_password)
            logger.info(f"Password verification: {'success' if result else 'failed'}")
            return result
        except Exception as e:
            logger.error(f"Failed to verify password: {e}")
            return False
    
    def needs_update(self, hashed_password: str) -> bool:
        """Check if password hash needs to be updated"""
        try:
            return pwd_context.needs_update(hashed_password)
        except Exception as e:
            logger.error(f"Failed to check if password needs update: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength based on configured requirements
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check minimum length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        # Check uppercase requirement
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check lowercase requirement
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check numbers requirement
        if self.require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        # Check special characters requirement
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak patterns
        weak_patterns = [
            (r'(.)\1{2,}', "Password cannot contain more than 2 consecutive identical characters"),
            (r'(012|123|234|345|456|567|678|789|890)', "Password cannot contain sequential numbers"),
            (r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', "Password cannot contain sequential letters"),
        ]
        
        for pattern, message in weak_patterns:
            if re.search(pattern, password.lower()):
                errors.append(message)
        
        # Check against common passwords (basic check)
        common_passwords = [
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "dragon", "master"
        ]
        
        if password.lower() in common_passwords:
            errors.append("Password is too common, please choose a more secure password")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("Password validation passed")
        else:
            logger.warning(f"Password validation failed: {len(errors)} errors")
        
        return is_valid, errors
    
    def generate_password_requirements_text(self) -> str:
        """Generate human-readable password requirements"""
        requirements = [f"At least {self.min_length} characters long"]
        
        if self.require_uppercase:
            requirements.append("At least one uppercase letter")
        
        if self.require_lowercase:
            requirements.append("At least one lowercase letter")
        
        if self.require_numbers:
            requirements.append("At least one number")
        
        if self.require_special:
            requirements.append("At least one special character (!@#$%^&*(),.?\":{}|<>)")
        
        requirements.extend([
            "No more than 2 consecutive identical characters",
            "No sequential numbers or letters",
            "Not a common password"
        ])
        
        return "Password must meet the following requirements:\n• " + "\n• ".join(requirements)


# Global password manager instance
password_manager = PasswordManager()