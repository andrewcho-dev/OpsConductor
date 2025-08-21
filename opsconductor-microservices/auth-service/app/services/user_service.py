"""
User Service for Auth Service - Handles user management within auth context
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.auth import User, EmailVerificationToken, PasswordResetToken
from app.schemas.auth import UserResponse, RegisterRequest
from app.core.password_utils import password_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user operations within auth context"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_user(
        self,
        user_data: RegisterRequest,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                or_(
                    User.email == user_data.email,
                    User.username == user_data.username
                )
            ).first()
            
            if existing_user:
                if existing_user.email == user_data.email:
                    return {
                        "success": False,
                        "error": "email_exists",
                        "message": "User with this email already exists"
                    }
                else:
                    return {
                        "success": False,
                        "error": "username_exists",
                        "message": "User with this username already exists"
                    }
            
            # Validate password strength
            is_strong, errors = password_manager.validate_password_strength(user_data.password)
            if not is_strong:
                return {
                    "success": False,
                    "error": "weak_password",
                    "message": "Password does not meet requirements",
                    "details": errors
                }
            
            # Hash password
            password_hash = password_manager.hash_password(user_data.password)
            
            # Create user
            user = User(
                email=user_data.email,
                username=user_data.username,
                password_hash=password_hash,
                is_active=True,
                is_verified=False  # Requires email verification
            )
            
            self.db.add(user)
            self.db.flush()  # Get the user ID
            
            # Create email verification token
            verification_token = await self._create_email_verification_token(user.id, user.email)
            
            self.db.commit()
            
            logger.info(f"User created: {user.id} ({user.email})")
            
            return {
                "success": True,
                "user": UserResponse.from_orm(user),
                "verification_token": verification_token,
                "message": "User created successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return self.db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            raise
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            return self.db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            raise
    
    async def update_user(
        self,
        user_id: int,
        update_data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> Optional[UserResponse]:
        """Update user information"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Update allowed fields
            allowed_fields = ['email', 'username', 'is_active', 'is_verified']
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"User updated: {user_id}")
            return UserResponse.from_orm(user)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"User deactivated: {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            raise
    
    async def verify_email(self, token: str) -> Dict[str, Any]:
        """Verify user email with token"""
        try:
            # Hash token for lookup
            token_hash = password_manager.hash_password(token)
            
            # Find verification token
            verification = self.db.query(EmailVerificationToken).filter(
                and_(
                    EmailVerificationToken.token_hash == token_hash,
                    EmailVerificationToken.is_used == False,
                    EmailVerificationToken.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not verification:
                return {
                    "success": False,
                    "error": "invalid_token",
                    "message": "Invalid or expired verification token"
                }
            
            # Get user
            user = self.db.query(User).filter(User.id == verification.user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "user_not_found",
                    "message": "User not found"
                }
            
            # Verify email
            user.is_verified = True
            user.updated_at = datetime.utcnow()
            
            # Mark token as used
            verification.is_used = True
            verification.used_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Email verified for user {user.id}")
            
            return {
                "success": True,
                "user": UserResponse.from_orm(user),
                "message": "Email verified successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to verify email: {e}")
            raise
    
    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """Request password reset for user"""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                # Don't reveal if user exists or not
                return {
                    "success": True,
                    "message": "If the email exists, a reset link has been sent"
                }
            
            # Create password reset token
            reset_token = await self._create_password_reset_token(user.id, user.email)
            
            self.db.commit()
            
            logger.info(f"Password reset requested for user {user.id}")
            
            return {
                "success": True,
                "reset_token": reset_token,  # In production, this would be sent via email
                "message": "Password reset token created"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to request password reset for {email}: {e}")
            raise
    
    async def reset_password(
        self,
        token: str,
        new_password: str
    ) -> Dict[str, Any]:
        """Reset password using token"""
        try:
            # Hash token for lookup
            token_hash = password_manager.hash_password(token)
            
            # Find reset token
            reset_token = self.db.query(PasswordResetToken).filter(
                and_(
                    PasswordResetToken.token_hash == token_hash,
                    PasswordResetToken.is_used == False,
                    PasswordResetToken.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not reset_token:
                return {
                    "success": False,
                    "error": "invalid_token",
                    "message": "Invalid or expired reset token"
                }
            
            # Validate new password strength
            is_strong, errors = password_manager.validate_password_strength(new_password)
            if not is_strong:
                return {
                    "success": False,
                    "error": "weak_password",
                    "message": "Password does not meet requirements",
                    "details": errors
                }
            
            # Get user
            user = self.db.query(User).filter(User.id == reset_token.user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "user_not_found",
                    "message": "User not found"
                }
            
            # Check if new password is different from current
            if password_manager.verify_password(new_password, user.password_hash):
                return {
                    "success": False,
                    "error": "same_password",
                    "message": "New password must be different from current password"
                }
            
            # Update password
            user.password_hash = password_manager.hash_password(new_password)
            user.password_changed_at = datetime.utcnow()
            user.failed_login_attempts = 0  # Reset failed attempts
            user.is_locked = False  # Unlock if locked
            user.locked_until = None
            user.updated_at = datetime.utcnow()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.used_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Password reset for user {user.id}")
            
            return {
                "success": True,
                "message": "Password reset successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to reset password: {e}")
            raise
    
    # Helper methods
    
    async def _create_email_verification_token(
        self,
        user_id: int,
        email: str
    ) -> str:
        """Create email verification token"""
        import secrets
        
        # Generate token
        token = secrets.token_urlsafe(32)
        token_hash = password_manager.hash_password(token)
        
        # Create verification record
        verification = EmailVerificationToken(
            token_hash=token_hash,
            user_id=user_id,
            email=email,
            expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        )
        
        self.db.add(verification)
        
        return token
    
    async def _create_password_reset_token(
        self,
        user_id: int,
        email: str
    ) -> str:
        """Create password reset token"""
        import secrets
        
        # Generate token
        token = secrets.token_urlsafe(32)
        token_hash = password_manager.hash_password(token)
        
        # Create reset record
        reset_token = PasswordResetToken(
            token_hash=token_hash,
            user_id=user_id,
            email=email,
            expires_at=datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        )
        
        self.db.add(reset_token)
        
        return token
    
    async def cleanup_expired_tokens(self) -> Dict[str, int]:
        """Clean up expired tokens"""
        try:
            # Clean up expired email verification tokens
            expired_verification = self.db.query(EmailVerificationToken).filter(
                and_(
                    EmailVerificationToken.expires_at < datetime.utcnow(),
                    EmailVerificationToken.is_used == False
                )
            ).count()
            
            self.db.query(EmailVerificationToken).filter(
                EmailVerificationToken.expires_at < datetime.utcnow()
            ).delete()
            
            # Clean up expired password reset tokens
            expired_reset = self.db.query(PasswordResetToken).filter(
                and_(
                    PasswordResetToken.expires_at < datetime.utcnow(),
                    PasswordResetToken.is_used == False
                )
            ).count()
            
            self.db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at < datetime.utcnow()
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {expired_verification} verification tokens and {expired_reset} reset tokens")
            
            return {
                "verification_tokens": expired_verification,
                "reset_tokens": expired_reset
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup expired tokens: {e}")
            raise