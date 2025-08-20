from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import logging

from app.models.user import User
from app.schemas.auth import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user management operations."""

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User data to create
            
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
    def get_users(db: Session, skip: int = 0, limit: int = 100, search: str = None, 
                 role: str = None, active_only: bool = None) -> List[User]:
        """
        Get list of users with pagination and filtering options.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search string for username or email
            role: Filter by role
            active_only: If True, only return active users
            
        Returns:
            List of users matching the criteria
        """
        query = db.query(User)
        
        # Apply filters if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.username.ilike(search_term)) | 
                (User.email.ilike(search_term))
            )
            
        if role:
            query = query.filter(User.role == role)
            
        if active_only:
            query = query.filter(User.is_active == True)
            
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Update user information.
        
        Args:
            db: Database session
            user_id: ID of the user to update
            user_data: User data to update
            
        Returns:
            Updated user object or None if user not found
        """
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
        """
        Delete a user (soft delete by setting is_active to False).
        
        Args:
            db: Database session
            user_id: ID of the user to delete
            
        Returns:
            True if user was deleted, False if user not found
        """
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            return False

        db_user.is_active = False
        db.commit()
        return True

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        return verify_password(plain_password, hashed_password)

    @staticmethod
    def update_password(db: Session, user_id: int, new_password: str) -> bool:
        """
        Update user password.
        
        Args:
            db: Database session
            user_id: ID of the user to update
            new_password: New plain text password
            
        Returns:
            True if password was updated, False if user not found
        """
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            return False

        db_user.password_hash = get_password_hash(new_password)
        db.commit()
        db.refresh(db_user)
        return True