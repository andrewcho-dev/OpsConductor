"""
User Repository implementation for User Management domain.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.shared.infrastructure.repository import BaseRepository
from app.shared.exceptions.base import DatabaseError, NotFoundError
from app.models.user_models import User
from app.shared.infrastructure.container import injectable


@injectable()
class UserRepository(BaseRepository[User]):
    """Repository for User entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            return self.db.query(User).filter(User.username == username).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get user by username: {str(e)}")
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            return self.db.query(User).filter(User.email == email).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get user by email: {str(e)}")
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users."""
        try:
            return self.db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get active users: {str(e)}")
    
    async def get_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role."""
        try:
            return self.db.query(User).filter(User.role == role).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get users by role: {str(e)}")
    
    async def username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """Check if username exists (optionally excluding a specific user ID)."""
        try:
            query = self.db.query(User).filter(User.username == username)
            if exclude_id:
                query = query.filter(User.id != exclude_id)
            return query.first() is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to check username existence: {str(e)}")
    
    async def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email exists (optionally excluding a specific user ID)."""
        try:
            query = self.db.query(User).filter(User.email == email)
            if exclude_id:
                query = query.filter(User.id != exclude_id)
            return query.first() is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to check email existence: {str(e)}")
    
    async def update_last_login(self, user_id: int) -> User:
        """Update user's last login timestamp."""
        try:
            from datetime import datetime, timezone
            user = await self.get_by_id_or_raise(user_id)
            user.last_login = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update last login: {str(e)}")
    
    async def deactivate_user(self, user_id: int) -> User:
        """Deactivate a user."""
        try:
            user = await self.get_by_id_or_raise(user_id)
            user.is_active = False
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to deactivate user: {str(e)}")
    
    async def activate_user(self, user_id: int) -> User:
        """Activate a user."""
        try:
            user = await self.get_by_id_or_raise(user_id)
            user.is_active = True
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to activate user: {str(e)}")