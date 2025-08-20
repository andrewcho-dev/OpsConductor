"""
User Service Business Logic
"""
import logging
import math
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.models.user import UserProfile, UserSettings, UserActivity
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserSettingsCreate, UserSettingsUpdate, UserSettingsResponse,
    UserActivityCreate, UserActivityResponse, UserActivityListResponse,
    UserStatsResponse, BulkUserAction, BulkUserActionResponse
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserService:
    """User service for managing user profiles and settings."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate, created_by: str) -> UserResponse:
        """Create a new user profile."""
        try:
            # Check if username already exists
            existing_user = self.db.query(UserProfile).filter(
                UserProfile.username == user_data.username
            ).first()
            if existing_user:
                raise ValueError(f"Username '{user_data.username}' already exists")
            
            # Check if email already exists
            existing_email = self.db.query(UserProfile).filter(
                UserProfile.email == user_data.email
            ).first()
            if existing_email:
                raise ValueError(f"Email '{user_data.email}' already exists")
            
            # Generate user_id (in real implementation, this would come from auth service)
            user_id = f"user-{user_data.username}-{int(datetime.now().timestamp())}"
            
            # Create user profile
            db_user = UserProfile(
                user_id=user_id,
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                role=user_data.role,
                permissions=user_data.permissions,
                is_active=user_data.is_active,
                created_by=created_by
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            # Create default settings
            self._create_default_settings(user_id)
            
            # Log activity
            self._log_activity(
                user_id=created_by,
                action="create_user",
                resource_type="user",
                resource_id=user_id,
                details={"username": user_data.username, "role": user_data.role}
            )
            
            logger.info(f"User created: {user_data.username} (ID: {user_id})")
            return UserResponse.from_orm(db_user)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by user_id."""
        user = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if user:
            return UserResponse.from_orm(user)
        return None
    
    def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """Get user by username."""
        user = self.db.query(UserProfile).filter(
            UserProfile.username == username
        ).first()
        
        if user:
            return UserResponse.from_orm(user)
        return None
    
    def get_users(
        self,
        skip: int = 0,
        limit: int = 25,
        search: Optional[str] = None,
        role: Optional[str] = None,
        active_only: bool = False,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> UserListResponse:
        """Get paginated list of users with filtering."""
        try:
            query = self.db.query(UserProfile)
            
            # Apply filters
            if search:
                search_filter = or_(
                    UserProfile.username.ilike(f"%{search}%"),
                    UserProfile.email.ilike(f"%{search}%"),
                    UserProfile.full_name.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            if role:
                query = query.filter(UserProfile.role == role)
            
            if active_only:
                query = query.filter(UserProfile.is_active == True)
            
            # Get total count
            total = query.count()
            
            # Apply sorting
            sort_column = getattr(UserProfile, sort_by, UserProfile.created_at)
            if sort_desc:
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
            
            # Apply pagination
            users = query.offset(skip).limit(limit).all()
            
            # Calculate pagination info
            pages = math.ceil(total / limit) if limit > 0 else 1
            page = (skip // limit) + 1 if limit > 0 else 1
            
            return UserListResponse(
                users=[UserResponse.from_orm(user) for user in users],
                total=total,
                page=page,
                size=limit,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise
    
    def update_user(
        self, 
        user_id: str, 
        user_data: UserUpdate, 
        updated_by: str
    ) -> Optional[UserResponse]:
        """Update user profile."""
        try:
            user = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not user:
                return None
            
            # Update fields
            update_data = user_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_by = updated_by
            
            self.db.commit()
            self.db.refresh(user)
            
            # Log activity
            self._log_activity(
                user_id=updated_by,
                action="update_user",
                resource_type="user",
                resource_id=user_id,
                details=update_data
            )
            
            logger.info(f"User updated: {user.username} (ID: {user_id})")
            return UserResponse.from_orm(user)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user: {e}")
            raise
    
    def delete_user(self, user_id: str, deleted_by: str) -> bool:
        """Delete user profile."""
        try:
            user = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not user:
                return False
            
            username = user.username
            
            # Delete related records
            self.db.query(UserSettings).filter(
                UserSettings.user_id == user_id
            ).delete()
            
            self.db.query(UserActivity).filter(
                UserActivity.user_id == user_id
            ).delete()
            
            # Delete user
            self.db.delete(user)
            self.db.commit()
            
            # Log activity
            self._log_activity(
                user_id=deleted_by,
                action="delete_user",
                resource_type="user",
                resource_id=user_id,
                details={"username": username}
            )
            
            logger.info(f"User deleted: {username} (ID: {user_id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user: {e}")
            raise
    
    def get_user_settings(self, user_id: str) -> Optional[UserSettingsResponse]:
        """Get user settings."""
        settings = self.db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()
        
        if settings:
            return UserSettingsResponse.from_orm(settings)
        return None
    
    def update_user_settings(
        self, 
        user_id: str, 
        settings_data: UserSettingsUpdate
    ) -> Optional[UserSettingsResponse]:
        """Update user settings."""
        try:
            settings = self.db.query(UserSettings).filter(
                UserSettings.user_id == user_id
            ).first()
            
            if not settings:
                # Create settings if they don't exist
                settings = UserSettings(user_id=user_id)
                self.db.add(settings)
            
            # Update fields
            update_data = settings_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(settings, field, value)
            
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"User settings updated for user: {user_id}")
            return UserSettingsResponse.from_orm(settings)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user settings: {e}")
            raise
    
    def get_user_stats(self) -> UserStatsResponse:
        """Get user statistics."""
        try:
            total_users = self.db.query(UserProfile).count()
            active_users = self.db.query(UserProfile).filter(
                UserProfile.is_active == True
            ).count()
            inactive_users = total_users - active_users
            admin_users = self.db.query(UserProfile).filter(
                UserProfile.role == "admin"
            ).count()
            regular_users = total_users - admin_users
            
            # Recent signups (last 7 days)
            from datetime import timedelta
            week_ago = datetime.now() - timedelta(days=7)
            recent_signups = self.db.query(UserProfile).filter(
                UserProfile.created_at >= week_ago
            ).count()
            
            return UserStatsResponse(
                total_users=total_users,
                active_users=active_users,
                inactive_users=inactive_users,
                admin_users=admin_users,
                regular_users=regular_users,
                recent_signups=recent_signups
            )
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            raise
    
    def bulk_user_action(
        self, 
        action_data: BulkUserAction, 
        performed_by: str
    ) -> BulkUserActionResponse:
        """Perform bulk action on users."""
        try:
            success_count = 0
            failed_count = 0
            failed_users = []
            
            for user_id in action_data.user_ids:
                try:
                    user = self.db.query(UserProfile).filter(
                        UserProfile.user_id == user_id
                    ).first()
                    
                    if not user:
                        failed_count += 1
                        failed_users.append(user_id)
                        continue
                    
                    if action_data.action == "activate":
                        user.is_active = True
                    elif action_data.action == "deactivate":
                        user.is_active = False
                    elif action_data.action == "delete":
                        self.db.delete(user)
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing user {user_id}: {e}")
                    failed_count += 1
                    failed_users.append(user_id)
            
            self.db.commit()
            
            # Log activity
            self._log_activity(
                user_id=performed_by,
                action=f"bulk_{action_data.action}",
                resource_type="user",
                resource_id="bulk",
                details={
                    "user_count": len(action_data.user_ids),
                    "success_count": success_count,
                    "failed_count": failed_count
                }
            )
            
            return BulkUserActionResponse(
                success_count=success_count,
                failed_count=failed_count,
                failed_users=failed_users,
                message=f"Bulk {action_data.action} completed: {success_count} successful, {failed_count} failed"
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error performing bulk action: {e}")
            raise
    
    def _create_default_settings(self, user_id: str):
        """Create default settings for a user."""
        try:
            settings = UserSettings(
                user_id=user_id,
                preferences={"dashboard_layout": "default", "items_per_page": 25},
                timezone="UTC",
                theme="light",
                language="en",
                notifications_enabled=True
            )
            self.db.add(settings)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating default settings for user {user_id}: {e}")
    
    def _log_activity(
        self,
        user_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log user activity."""
        try:
            activity = UserActivity(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(activity)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging activity: {e}")