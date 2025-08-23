"""
User Service - Business logic for user management operations
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc

from app.models.user import User, UserProfile, UserActivityLog, Role, UserRole
from app.schemas.user import (
    UserCreateRequest, UserUpdateRequest, UserResponse, 
    UserListResponse, UserStatsResponse, UserActivityLogResponse
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_user(
        self,
        user_data: UserCreateRequest,
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
            
            # Create user
            user = User(
                email=user_data.email,
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                display_name=user_data.display_name,
                phone=user_data.phone,
                department=user_data.department,
                job_title=user_data.job_title,
                organization=user_data.organization,
                timezone=user_data.timezone,
                language=user_data.language,
                theme=user_data.theme,
                is_active=True,
                is_verified=not settings.REQUIRE_EMAIL_VERIFICATION
            )
            
            self.db.add(user)
            self.db.flush()  # Get the user ID
            
            # Create user profile
            profile = UserProfile(user_id=user.id)
            self.db.add(profile)
            
            # Assign role (simple foreign key - one role per user)
            if user_data.role_id:
                # Verify role exists and is active
                role = self.db.query(Role).filter(
                    and_(Role.id == user_data.role_id, Role.is_active == True)
                ).first()
                if role:
                    user.role_id = user_data.role_id
            else:
                # Assign default role
                default_role = self.db.query(Role).filter(
                    Role.name == settings.DEFAULT_USER_ROLE
                ).first()
                if default_role:
                    user.role_id = default_role.id
            
            # Get assigned role name for logging
            assigned_role = None
            if user.role_id:
                role = self.db.query(Role).filter(Role.id == user.role_id).first()
                if role:
                    assigned_role = role.name
            
            # Log user creation activity
            activity_log = UserActivityLog(
                user_id=user.id,
                activity_type="user_created",
                activity_description=f"User account created by {'system' if not created_by else f'user {created_by}'}",
                activity_metadata={
                    "created_by": created_by,
                    "role_assigned": assigned_role,
                    "send_welcome_email": user_data.send_welcome_email
                }
            )
            self.db.add(activity_log)
            
            self.db.commit()
            
            logger.info(f"User created: {user.id} ({user.email})")
            
            return {
                "success": True,
                "user": await self._get_user_response(user),
                "message": "User created successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Get user by ID"""
        try:
            user = self.db.query(User).options(
                joinedload(User.profile)
            ).filter(User.id == user_id).first()
            
            if user:
                return await self._get_user_response(user)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Get user by email"""
        try:
            user = self.db.query(User).options(
                joinedload(User.profile)
            ).filter(User.email == email).first()
            
            if user:
                return await self._get_user_response(user)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            raise
    
    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """Get user by username"""
        try:
            user = self.db.query(User).options(
                joinedload(User.profile)
            ).filter(User.username == username).first()
            
            if user:
                return await self._get_user_response(user)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            raise
    
    async def update_user(
        self,
        user_id: int,
        update_data: UserUpdateRequest,
        updated_by: Optional[int] = None
    ) -> Optional[UserResponse]:
        """Update user information"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Track changes for activity log
            changes = {}
            
            # Update allowed fields
            update_fields = [
                'email', 'username', 'first_name', 'last_name', 'display_name',
                'phone', 'department', 'job_title', 'organization', 'timezone',
                'language', 'theme', 'is_active', 'is_verified', 'metadata', 'tags'
            ]
            
            for field in update_fields:
                new_value = getattr(update_data, field, None)
                if new_value is not None:
                    old_value = getattr(user, field)
                    if old_value != new_value:
                        changes[field] = {"old": old_value, "new": new_value}
                        setattr(user, field, new_value)
            
            user.updated_at = datetime.utcnow()
            
            # Log activity if there were changes
            if changes:
                activity_log = UserActivityLog(
                    user_id=user.id,
                    activity_type="user_updated",
                    activity_description=f"User information updated by {'system' if not updated_by else f'user {updated_by}'}",
                    metadata={
                        "updated_by": updated_by,
                        "changes": changes
                    }
                )
                self.db.add(activity_log)
            
            self.db.commit()
            
            logger.info(f"User updated: {user_id}")
            return await self._get_user_response(user)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    async def delete_user(self, user_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a user (deactivate)"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Soft delete by deactivating
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            # Log activity
            activity_log = UserActivityLog(
                user_id=user.id,
                activity_type="user_deleted",
                activity_description=f"User account deactivated by {'system' if not deleted_by else f'user {deleted_by}'}",
                metadata={
                    "deleted_by": deleted_by,
                    "deletion_type": "soft_delete"
                }
            )
            self.db.add(activity_log)
            
            self.db.commit()
            
            logger.info(f"User soft deleted: {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise
    
    async def list_users(
        self,
        page: int = 1,
        page_size: int = None,
        search: Optional[str] = None,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        department: Optional[str] = None,
        organization: Optional[str] = None
    ) -> UserListResponse:
        """List users with filtering and pagination"""
        try:
            page_size = page_size or settings.DEFAULT_PAGE_SIZE
            page_size = min(page_size, settings.MAX_PAGE_SIZE)
            
            query = self.db.query(User).options(
                joinedload(User.profile)
            )
            
            # Apply filters
            if search:
                search_filter = or_(
                    User.email.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%"),
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%"),
                    User.display_name.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            if role_id is not None:
                # Filter by role_id directly
                query = query.filter(User.role_id == role_id)
            
            if is_active is not None:
                query = query.filter(User.is_active == is_active)
            
            if is_verified is not None:
                query = query.filter(User.is_verified == is_verified)
            
            if department:
                query = query.filter(User.department.ilike(f"%{department}%"))
            
            if organization:
                query = query.filter(User.organization.ilike(f"%{organization}%"))
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            users = query.offset(offset).limit(page_size).all()
            
            # Convert to response objects
            user_responses = []
            for user in users:
                user_responses.append(await self._get_user_response(user))
            
            total_pages = (total + page_size - 1) // page_size
            
            return UserListResponse(
                users=user_responses,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise
    
    async def assign_role(
        self,
        user_id: int,
        role_id: int
    ) -> bool:
        """Assign a single role to a user (simplified)"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Verify role exists and is active
            role = self.db.query(Role).filter(
                and_(Role.id == role_id, Role.is_active == True)
            ).first()
            
            if not role:
                return False  # Role not found or inactive
            
            # Store old role for logging
            old_role_name = None
            if user.role_id:
                old_role = self.db.query(Role).filter(Role.id == user.role_id).first()
                if old_role:
                    old_role_name = old_role.name
            
            # Assign new role
            user.role_id = role_id
            
            # Log activity
            activity_log = UserActivityLog(
                user_id=user.id,
                activity_type="role_assigned",
                activity_description=f"Role changed from {old_role_name or 'None'} to {role.name}",
                activity_metadata={
                    "old_role": old_role_name,
                    "new_role": role.name
                }
            )
            self.db.add(activity_log)
            
            self.db.commit()
            
            logger.info(f"Role assigned to user {user_id}: {role.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to assign role to user {user_id}: {e}")
            raise
    
    async def remove_role(
        self,
        user_id: int,
        removed_by: Optional[int] = None
    ) -> bool:
        """Remove role from a user (set to None)"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Get current role for logging
            old_role_name = None
            if user.role_id:
                old_role = self.db.query(Role).filter(Role.id == user.role_id).first()
                if old_role:
                    old_role_name = old_role.name
            
            # Remove role
            user.role_id = None
            
            # Log activity
            if old_role_name:
                activity_log = UserActivityLog(
                    user_id=user.id,
                    activity_type="role_removed",
                    activity_description=f"Role {old_role_name} removed by {'system' if not removed_by else f'user {removed_by}'}",
                    activity_metadata={
                        "removed_by": removed_by,
                        "role_removed": old_role_name
                    }
                )
                self.db.add(activity_log)
            
            self.db.commit()
            
            logger.info(f"Role removed from user {user_id}: {old_role_name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to remove role from user {user_id}: {e}")
            raise
    
    async def get_user_activity_logs(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 50,
        activity_type: Optional[str] = None
    ) -> List[UserActivityLogResponse]:
        """Get user activity logs"""
        try:
            query = self.db.query(UserActivityLog).filter(
                UserActivityLog.user_id == user_id
            )
            
            if activity_type:
                query = query.filter(UserActivityLog.activity_type == activity_type)
            
            # Apply pagination
            offset = (page - 1) * page_size
            logs = query.order_by(desc(UserActivityLog.created_at)).offset(offset).limit(page_size).all()
            
            return [UserActivityLogResponse.from_orm(log) for log in logs]
            
        except Exception as e:
            logger.error(f"Failed to get activity logs for user {user_id}: {e}")
            raise
    
    async def get_user_stats(self) -> UserStatsResponse:
        """Get user statistics"""
        try:
            # Basic counts
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            verified_users = self.db.query(User).filter(User.is_verified == True).count()
            # superusers = 0  # No longer tracking superusers
            
            # Time-based counts
            today = datetime.utcnow().date()
            users_created_today = self.db.query(User).filter(
                func.date(User.created_at) == today
            ).count()
            
            # Most common roles
            role_stats = self.db.query(
                Role.name,
                func.count(User.id).label('user_count')
            ).join(User.roles).group_by(Role.name).order_by(
                desc('user_count')
            ).limit(5).all()
            
            most_common_roles = [
                {"role": role, "count": count} 
                for role, count in role_stats
            ]
            
            # Most active users (by activity logs)
            active_user_stats = self.db.query(
                User.id,
                User.email,
                User.display_name,
                func.count(UserActivityLog.id).label('activity_count')
            ).join(UserActivityLog).group_by(
                User.id, User.email, User.display_name
            ).order_by(desc('activity_count')).limit(5).all()
            
            most_active_users = [
                {
                    "user_id": user_id,
                    "email": email,
                    "display_name": display_name,
                    "activity_count": count
                }
                for user_id, email, display_name, count in active_user_stats
            ]
            
            return UserStatsResponse(
                total_users=total_users,
                active_users=active_users,
                verified_users=verified_users,
                superusers=superusers,
                users_created_today=users_created_today,
                users_created_this_week=0,  # TODO: Implement
                users_created_this_month=0,  # TODO: Implement
                most_common_roles=most_common_roles,
                most_active_users=most_active_users
            )
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            raise
    
    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user credentials"""
        try:
            # Find user by username or email
            user = self.db.query(User).filter(
                or_(
                    User.username == username,
                    User.email == username
                )
            ).first()
            
            if not user:
                return {
                    "success": False,
                    "message": "User not found"
                }
            
            if not user.is_active:
                return {
                    "success": False,
                    "message": "User account is inactive"
                }
            
            # Verify password hash
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            if not user.password_hash:
                return {
                    "success": False,
                    "message": "No password set for user"
                }
            
            # Verify password
            if not pwd_context.verify(password, user.password_hash):
                return {
                    "success": False,
                    "message": "Invalid password"
                }
            
            # Get user's role
            role_name = "user"  # default role
            user_role_query = self.db.query(UserRole, Role).join(
                Role, UserRole.role_id == Role.id
            ).filter(UserRole.user_id == user.id).first()
            
            if user_role_query:
                user_role, role = user_role_query
                role_name = role.name
            
            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "display_name": user.display_name,
                    "role": role_name
                },
                "message": "Authentication successful"
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {
                "success": False,
                "message": "Authentication error"
            }
    
    # Helper methods
    
    async def _get_user_response(self, user: User) -> UserResponse:
        """Convert User model to UserResponse"""
        from app.schemas.user import UserProfileResponse, RoleResponse, PermissionResponse
        
        # Convert profile
        profile_response = None
        if user.profile:
            profile_response = UserProfileResponse.from_orm(user.profile)
        
        # Convert role and permissions (simplified - single role)
        role_response = None
        permissions = []
        
        if user.role and user.role.is_active:
            permission_responses = []
            for permission in user.role.permissions:
                if permission.is_active:
                    permission_responses.append(PermissionResponse.from_orm(permission))
                    permissions.append(permission.name)
            
            role_response = RoleResponse.from_orm(user.role)
            role_response.permissions = permission_responses
        
        # Create user response
        user_response = UserResponse.from_orm(user)
        user_response.role = role_response  # Single role instead of roles list
        user_response.profile = profile_response
        user_response.permissions = permissions
        user_response.full_name = user.full_name
        
        return user_response