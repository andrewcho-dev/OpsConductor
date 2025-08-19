from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from app.models.user_models import User, UserSession
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.core.audit_utils import log_audit_event_sync
from app.domains.audit.services.audit_service import AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user management operations."""

    @staticmethod
    def create_user(db: Session, user_data: UserCreate, current_user_id: Optional[int] = None) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User data to create
            current_user_id: ID of the user performing the action (for audit logging)
            
        Returns:
            Created user object
            
        Raises:
            ValueError: If username or email already exists
        """
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            role=user_data.role
        )
        
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Log audit event
            log_audit_event_sync(
                db=db,
                event_type=AuditEventType.USER_CREATED,
                user_id=current_user_id,
                resource_type="user",
                resource_id=str(db_user.id),
                action="create",
                details={
                    "username": db_user.username,
                    "email": db_user.email,
                    "role": db_user.role
                },
                severity=AuditSeverity.MEDIUM
            )
            
            return db_user
        except IntegrityError:
            db.rollback()
            raise ValueError("Username or email already exists")

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users with pagination."""
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate, current_user_id: Optional[int] = None) -> Optional[User]:
        """
        Update user information.
        
        Args:
            db: Database session
            user_id: ID of the user to update
            user_data: User data to update
            current_user_id: ID of the user performing the action (for audit logging)
            
        Returns:
            Updated user object or None if user not found
        """
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            return None

        # Store original values for audit logging
        original_values = {
            "username": db_user.username,
            "email": db_user.email,
            "role": db_user.role,
            "is_active": db_user.is_active
        }

        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        
        # Determine what fields were changed
        changed_fields = {}
        for field, original_value in original_values.items():
            if field in update_data and getattr(db_user, field) != original_value:
                changed_fields[field] = {
                    "from": original_value,
                    "to": getattr(db_user, field)
                }
        
        # Log audit event if fields were changed
        if changed_fields:
            log_audit_event_sync(
                db=db,
                event_type=AuditEventType.USER_UPDATED,
                user_id=current_user_id,
                resource_type="user",
                resource_id=str(user_id),
                action="update",
                details={
                    "username": db_user.username,
                    "changed_fields": changed_fields
                },
                severity=AuditSeverity.MEDIUM
            )
        
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: int, current_user_id: Optional[int] = None) -> bool:
        """
        Delete a user (soft delete by setting is_active to False).
        
        Args:
            db: Database session
            user_id: ID of the user to delete
            current_user_id: ID of the user performing the action (for audit logging)
            
        Returns:
            True if user was deleted, False if user not found
        """
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            return False

        # Store user info for audit logging
        user_info = {
            "username": db_user.username,
            "email": db_user.email,
            "role": db_user.role
        }

        db_user.is_active = False
        db.commit()
        
        # Log audit event
        log_audit_event_sync(
            db=db,
            event_type=AuditEventType.USER_DELETED,
            user_id=current_user_id,
            resource_type="user",
            resource_id=str(user_id),
            action="delete",
            details=user_info,
            severity=AuditSeverity.HIGH
        )
        
        return True

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Args:
            db: Database session
            username: Username to authenticate
            password: Password to verify
            ip_address: IP address of the client (for audit logging)
            user_agent: User agent of the client (for audit logging)
            
        Returns:
            User object if authentication successful, None otherwise
        """
        logger.debug(f"Attempting to authenticate user '{username}'")
        user = UserService.get_user_by_username(db, username)
        
        # Authentication failure - user not found
        if not user:
            logger.debug(f"User '{username}' not found")
            # Log failed login attempt
            log_audit_event_sync(
                db=db,
                event_type=AuditEventType.LOGIN_FAILED,
                user_id=None,
                resource_type="authentication",
                resource_id=username,
                action="login_attempt",
                details={
                    "username": username,
                    "reason": "user_not_found"
                },
                severity=AuditSeverity.MEDIUM,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return None
        
        # Authentication failure - user not active
        if not user.is_active:
            logger.debug(f"User '{username}' is not active")
            # Log failed login attempt
            log_audit_event_sync(
                db=db,
                event_type=AuditEventType.LOGIN_FAILED,
                user_id=user.id,
                resource_type="authentication",
                resource_id=username,
                action="login_attempt",
                details={
                    "username": username,
                    "reason": "account_disabled"
                },
                severity=AuditSeverity.HIGH,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return None
        
        logger.debug(f"User found, verifying password")
        
        # Authentication failure - invalid password
        if not verify_password(password, user.password_hash):
            logger.debug(f"Password verification failed for user '{username}'")
            # Log failed login attempt
            log_audit_event_sync(
                db=db,
                event_type=AuditEventType.LOGIN_FAILED,
                user_id=user.id,
                resource_type="authentication",
                resource_id=username,
                action="login_attempt",
                details={
                    "username": username,
                    "reason": "invalid_password"
                },
                severity=AuditSeverity.HIGH,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return None
        
        logger.debug(f"Authentication successful for user '{username}'")
        
        # Log successful login
        log_audit_event_sync(
            db=db,
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id=user.id,
            resource_type="authentication",
            resource_id=username,
            action="login",
            details={
                "username": username
            },
            severity=AuditSeverity.INFO,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return user

    @staticmethod
    def update_last_login(db: Session, user_id: int):
        """Update user's last login timestamp."""
        db_user = UserService.get_user_by_id(db, user_id)
        if db_user:
            db_user.last_login = datetime.utcnow()
            db.commit()

    @staticmethod
    def create_user_session(db: Session, user_id: int, ip_address: str = None, 
                          user_agent: str = None) -> UserSession:
        """
        Create a new user session.
        
        Args:
            db: Database session
            user_id: ID of the user for the session
            ip_address: IP address of the client
            user_agent: User agent of the client
            
        Returns:
            Created session object
        """
        session_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        db_session = UserSession(
            user_id=user_id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        # Get user info for audit logging
        user = UserService.get_user_by_id(db, user_id)
        username = user.username if user else f"user_{user_id}"
        
        # Log session creation
        log_audit_event_sync(
            db=db,
            event_type=AuditEventType.USER_LOGIN,
            user_id=user_id,
            resource_type="session",
            resource_id=str(db_session.id),
            action="create_session",
            details={
                "username": username,
                "session_token": session_token,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "expires_at": expires_at.isoformat()
            },
            severity=AuditSeverity.INFO,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return db_session

    @staticmethod
    def get_user_session(db: Session, session_token: str) -> Optional[UserSession]:
        """Get user session by token."""
        return db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.expires_at > datetime.utcnow()
        ).first()

    @staticmethod
    def update_session_activity(db: Session, session_id: int):
        """Update session last activity."""
        db_session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if db_session:
            db_session.last_activity = datetime.utcnow()
            db.commit()

    @staticmethod
    def delete_user_session(db: Session, session_token: str, ip_address: str = None, user_agent: str = None) -> bool:
        """
        Delete a user session.
        
        Args:
            db: Database session
            session_token: Token of the session to delete
            ip_address: IP address of the client (for audit logging)
            user_agent: User agent of the client (for audit logging)
            
        Returns:
            True if session was deleted, False if session not found
        """
        db_session = db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if db_session:
            user_id = db_session.user_id
            session_id = db_session.id
            
            # Get user info for audit logging
            user = UserService.get_user_by_id(db, user_id)
            username = user.username if user else f"user_{user_id}"
            
            db.delete(db_session)
            db.commit()
            
            # Log session deletion
            log_audit_event_sync(
                db=db,
                event_type=AuditEventType.USER_LOGOUT,
                user_id=user_id,
                resource_type="session",
                resource_id=str(session_id),
                action="delete_session",
                details={
                    "username": username,
                    "session_token": session_token
                },
                severity=AuditSeverity.INFO,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return True
        return False

    @staticmethod
    def cleanup_expired_sessions(db: Session):
        """
        Clean up expired user sessions.
        
        Args:
            db: Database session
        """
        expired_sessions = db.query(UserSession).filter(
            UserSession.expires_at <= datetime.utcnow()
        ).all()
        
        if not expired_sessions:
            return
            
        # Log batch session cleanup
        session_details = []
        for session in expired_sessions:
            session_details.append({
                "session_id": session.id,
                "user_id": session.user_id,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None
            })
            db.delete(session)
            
        db.commit()
        
        # Log audit event for session cleanup
        log_audit_event_sync(
            db=db,
            event_type=AuditEventType.SYSTEM_MAINTENANCE,
            user_id=None,  # System operation
            resource_type="session",
            resource_id="batch_cleanup",
            action="cleanup_expired_sessions",
            details={
                "expired_sessions_count": len(expired_sessions),
                "expired_sessions": session_details
            },
            severity=AuditSeverity.INFO
        )