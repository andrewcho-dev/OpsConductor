from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.models.user_models import User, UserSession
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.config import settings


class UserService:
    """Service class for user management operations."""

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user."""
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
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            return None

        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete a user (soft delete by setting is_active to False)."""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            return False

        db_user.is_active = False
        db.commit()
        return True

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        print(f"DEBUG: Attempting to authenticate user '{username}'")
        user = UserService.get_user_by_username(db, username)
        if not user:
            print(f"DEBUG: User '{username}' not found")
            return None
        if not user.is_active:
            print(f"DEBUG: User '{username}' is not active")
            return None
        print(f"DEBUG: User found, verifying password")
        if not verify_password(password, user.password_hash):
            print(f"DEBUG: Password verification failed for user '{username}'")
            return None
        print(f"DEBUG: Authentication successful for user '{username}'")
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
        """Create a new user session."""
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
    def delete_user_session(db: Session, session_token: str) -> bool:
        """Delete a user session."""
        db_session = db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        if db_session:
            db.delete(db_session)
            db.commit()
            return True
        return False

    @staticmethod
    def cleanup_expired_sessions(db: Session):
        """Clean up expired user sessions."""
        expired_sessions = db.query(UserSession).filter(
            UserSession.expires_at <= datetime.utcnow()
        ).all()
        
        for session in expired_sessions:
            db.delete(session)
        db.commit() 