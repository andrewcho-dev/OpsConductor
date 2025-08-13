"""
User Domain Service - Contains business logic for user management.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.shared.exceptions.base import ValidationException, ConflictError, NotFoundError
from app.domains.user_management.repositories.user_repository import UserRepository
from app.models.user_models import User
from app.core.security import get_password_hash, verify_password
from app.shared.infrastructure.container import injectable


@injectable()
class UserDomainService:
    """Domain service for user business logic."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def create_user(
        self, 
        username: str, 
        email: str, 
        password: str, 
        role: str = "user"
    ) -> User:
        """Create a new user with validation."""
        # Validate input
        await self._validate_user_creation(username, email, role)
        
        # Check for conflicts
        if await self.user_repository.username_exists(username):
            raise ConflictError(f"Username '{username}' already exists")
        
        if await self.user_repository.email_exists(email):
            raise ConflictError(f"Email '{email}' already exists")
        
        # Create user data
        user_data = {
            "username": username,
            "email": email,
            "password_hash": get_password_hash(password),
            "role": role,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        return await self.user_repository.create(user_data)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        user = await self.user_repository.get_by_username(username)
        
        if not user:
            return None
        
        if not user.is_active:
            raise ValidationException("User account is deactivated")
        
        if not verify_password(password, user.password_hash):
            return None
        
        # Update last login
        await self.user_repository.update_last_login(user.id)
        
        return user
    
    async def update_user(
        self, 
        user_id: int, 
        update_data: Dict[str, Any]
    ) -> User:
        """Update user with validation."""
        user = await self.user_repository.get_by_id_or_raise(user_id)
        
        # Validate updates
        if "username" in update_data:
            if await self.user_repository.username_exists(update_data["username"], exclude_id=user_id):
                raise ConflictError(f"Username '{update_data['username']}' already exists")
        
        if "email" in update_data:
            if await self.user_repository.email_exists(update_data["email"], exclude_id=user_id):
                raise ConflictError(f"Email '{update_data['email']}' already exists")
        
        if "role" in update_data:
            self._validate_role(update_data["role"])
        
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        return await self.user_repository.update(user_id, update_data)
    
    async def change_password(self, user_id: int, current_password: str, new_password: str) -> User:
        """Change user password with current password verification."""
        user = await self.user_repository.get_by_id_or_raise(user_id)
        
        if not verify_password(current_password, user.password_hash):
            raise ValidationException("Current password is incorrect")
        
        self._validate_password(new_password)
        
        update_data = {
            "password_hash": get_password_hash(new_password),
            "updated_at": datetime.now(timezone.utc)
        }
        
        return await self.user_repository.update(user_id, update_data)
    
    async def deactivate_user(self, user_id: int) -> User:
        """Deactivate a user account."""
        return await self.user_repository.deactivate_user(user_id)
    
    async def activate_user(self, user_id: int) -> User:
        """Activate a user account."""
        return await self.user_repository.activate_user(user_id)
    
    async def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID."""
        return await self.user_repository.get_by_id_or_raise(user_id)
    
    async def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        role: Optional[str] = None,
        active_only: bool = False
    ) -> List[User]:
        """Get users with optional filtering."""
        if role:
            return await self.user_repository.get_by_role(role, skip, limit)
        elif active_only:
            return await self.user_repository.get_active_users(skip, limit)
        else:
            return await self.user_repository.get_all(skip, limit)
    
    async def _validate_user_creation(self, username: str, email: str, role: str) -> None:
        """Validate user creation data."""
        if not username or len(username.strip()) < 3:
            raise ValidationException("Username must be at least 3 characters long")
        
        if not email or "@" not in email:
            raise ValidationException("Valid email address is required")
        
        self._validate_role(role)
    
    def _validate_role(self, role: str) -> None:
        """Validate user role."""
        valid_roles = ["user", "administrator", "operator"]
        if role not in valid_roles:
            raise ValidationException(f"Role must be one of: {', '.join(valid_roles)}")
    
    def _validate_password(self, password: str) -> None:
        """Validate password strength."""
        if not password or len(password) < 8:
            raise ValidationException("Password must be at least 8 characters long")
        
        # Add more password validation rules as needed
        if not any(c.isupper() for c in password):
            raise ValidationException("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise ValidationException("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValidationException("Password must contain at least one digit")