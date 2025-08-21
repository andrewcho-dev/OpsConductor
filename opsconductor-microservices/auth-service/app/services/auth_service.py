"""
Auth Service - Business logic for authentication operations
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.auth import User, UserSession, LoginHistory, PasswordHistory
from app.schemas.auth import UserResponse, SessionInfo, LoginHistoryEntry
from app.core.password_utils import password_manager

logger = logging.getLogger(__name__)


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        client_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        try:
            # Get user by email
            user = self.db.query(User).filter(User.email == email).first()
            
            # Record login attempt
            login_history = LoginHistory(
                user_id=user.id if user else None,
                email=email,
                success=False,  # Will be updated if successful
                ip_address=client_info.get("ip_address"),
                user_agent=client_info.get("user_agent")
            )
            
            if not user:
                login_history.failure_reason = "user_not_found"
                self.db.add(login_history)
                self.db.commit()
                return {
                    "success": False,
                    "error": "invalid_credentials",
                    "message": "Invalid email or password"
                }
            
            # Check if user is active
            if not user.is_active:
                login_history.failure_reason = "user_inactive"
                self.db.add(login_history)
                self.db.commit()
                return {
                    "success": False,
                    "error": "user_inactive",
                    "message": "User account is inactive"
                }
            
            # Check if user is locked
            if user.is_locked:
                if user.locked_until and user.locked_until > datetime.utcnow():
                    login_history.failure_reason = "user_locked"
                    self.db.add(login_history)
                    self.db.commit()
                    return {
                        "success": False,
                        "error": "user_locked",
                        "message": f"User account is locked until {user.locked_until}"
                    }
                else:
                    # Unlock user if lock period has expired
                    user.is_locked = False
                    user.locked_until = None
                    user.failed_login_attempts = 0
            
            # Verify password
            if not password_manager.verify_password(password, user.password_hash):
                # Increment failed attempts
                user.failed_login_attempts += 1
                
                # Lock user if too many failed attempts
                from app.core.config import settings
                if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                    user.is_locked = True
                    user.locked_until = datetime.utcnow() + timedelta(
                        minutes=settings.LOCKOUT_DURATION_MINUTES
                    )
                
                login_history.failure_reason = "invalid_password"
                self.db.add(login_history)
                self.db.commit()
                
                return {
                    "success": False,
                    "error": "invalid_credentials",
                    "message": "Invalid email or password"
                }
            
            # Check if password needs update
            if password_manager.needs_update(user.password_hash):
                # This could trigger a password update flow
                logger.info(f"Password hash needs update for user {user.id}")
            
            # Successful authentication
            user.failed_login_attempts = 0
            user.last_login_at = datetime.utcnow()
            
            login_history.success = True
            login_history.user_id = user.id
            
            self.db.add(login_history)
            self.db.commit()
            
            return {
                "success": True,
                "user": UserResponse.from_orm(user),
                "message": "Authentication successful"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Authentication failed for {email}: {e}")
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
    
    async def create_user_session(
        self,
        user_id: int,
        session_id: str,
        refresh_token: str,
        client_info: Dict[str, str],
        expires_at: datetime
    ) -> UserSession:
        """Create a new user session"""
        try:
            # Hash refresh token for storage
            refresh_token_hash = password_manager.hash_password(refresh_token)
            
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                refresh_token_hash=refresh_token_hash,
                ip_address=client_info.get("ip_address"),
                user_agent=client_info.get("user_agent"),
                expires_at=expires_at
            )
            
            self.db.add(session)
            self.db.commit()
            
            logger.info(f"Session created for user {user_id}: {session_id}")
            return session
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create session for user {user_id}: {e}")
            raise
    
    async def get_user_session(self, session_id: str) -> Optional[UserSession]:
        """Get user session by session ID"""
        try:
            return self.db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise
    
    async def get_user_sessions(self, user_id: int) -> List[SessionInfo]:
        """Get all sessions for a user"""
        try:
            sessions = self.db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).order_by(UserSession.created_at.desc()).all()
            
            session_infos = []
            for session in sessions:
                session_info = SessionInfo(
                    session_id=session.session_id,
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    is_active=session.is_active and session.expires_at > datetime.utcnow(),
                    expires_at=session.expires_at,
                    last_activity=session.last_activity,
                    created_at=session.created_at
                )
                session_infos.append(session_info)
            
            return session_infos
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            raise
    
    async def deactivate_user_session(self, session_id: str) -> bool:
        """Deactivate a specific user session"""
        try:
            session = self.db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if session:
                session.is_active = False
                self.db.commit()
                logger.info(f"Session deactivated: {session_id}")
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to deactivate session {session_id}: {e}")
            raise
    
    async def deactivate_user_sessions(self, user_id: int) -> int:
        """Deactivate all sessions for a user"""
        try:
            updated_count = self.db.query(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            ).update({"is_active": False})
            
            self.db.commit()
            logger.info(f"Deactivated {updated_count} sessions for user {user_id}")
            return updated_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to deactivate sessions for user {user_id}: {e}")
            raise
    
    async def update_user_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login_at = datetime.utcnow()
                self.db.commit()
                return True
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update last login for user {user_id}: {e}")
            raise
    
    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """Change user password"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "user_not_found",
                    "message": "User not found"
                }
            
            # Verify current password
            if not password_manager.verify_password(current_password, user.password_hash):
                return {
                    "success": False,
                    "error": "invalid_current_password",
                    "message": "Current password is incorrect"
                }
            
            # Validate new password strength
            is_strong, errors = password_manager.validate_password_strength(new_password)
            if not is_strong:
                return {
                    "success": False,
                    "error": "weak_password",
                    "message": "New password does not meet requirements",
                    "details": errors
                }
            
            # Check if new password is different from current
            if password_manager.verify_password(new_password, user.password_hash):
                return {
                    "success": False,
                    "error": "same_password",
                    "message": "New password must be different from current password"
                }
            
            # Store old password in history
            password_history = PasswordHistory(
                user_id=user_id,
                password_hash=user.password_hash,
                changed_by=user_id,
                change_reason="user_change"
            )
            self.db.add(password_history)
            
            # Update password
            user.password_hash = password_manager.hash_password(new_password)
            user.password_changed_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Password changed for user {user_id}")
            return {
                "success": True,
                "message": "Password changed successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to change password for user {user_id}: {e}")
            raise
    
    async def get_login_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[LoginHistoryEntry]:
        """Get login history for a user"""
        try:
            history = self.db.query(LoginHistory).filter(
                LoginHistory.user_id == user_id
            ).order_by(
                LoginHistory.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return [LoginHistoryEntry.from_orm(entry) for entry in history]
            
        except Exception as e:
            logger.error(f"Failed to get login history for user {user_id}: {e}")
            raise
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            expired_count = self.db.query(UserSession).filter(
                and_(
                    UserSession.expires_at < datetime.utcnow(),
                    UserSession.is_active == True
                )
            ).update({"is_active": False})
            
            self.db.commit()
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions")
            
            return expired_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup expired sessions: {e}")
            raise
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user authentication statistics"""
        try:
            # Get total login attempts
            total_logins = self.db.query(LoginHistory).filter(
                LoginHistory.user_id == user_id
            ).count()
            
            # Get successful logins
            successful_logins = self.db.query(LoginHistory).filter(
                and_(
                    LoginHistory.user_id == user_id,
                    LoginHistory.success == True
                )
            ).count()
            
            # Get failed attempts
            failed_attempts = total_logins - successful_logins
            
            # Get active sessions
            active_sessions = self.db.query(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            ).count()
            
            # Get last login
            last_login = self.db.query(LoginHistory).filter(
                and_(
                    LoginHistory.user_id == user_id,
                    LoginHistory.success == True
                )
            ).order_by(LoginHistory.created_at.desc()).first()
            
            return {
                "total_logins": total_logins,
                "successful_logins": successful_logins,
                "failed_attempts": failed_attempts,
                "active_sessions": active_sessions,
                "last_login": last_login.created_at if last_login else None,
                "last_login_ip": last_login.ip_address if last_login else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats for user {user_id}: {e}")
            raise